#!/usr/bin/env python3
"""Unit tests for probe_image_backends.py."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/image-to-editable-ppt/scripts"
SKILL_ROOT = ROOT / "skills/image-to-editable-ppt"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from probe_image_backends import build_report, main, probe_candidates


class ProbeImageBackendsTests(unittest.TestCase):
    def test_cli_always_listed_with_available_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cands = probe_candidates(home, SKILL_ROOT, honor_codex_home_env=False)
            cli = next(c for c in cands if c["id"] == "editppt-image-cli")
            self.assertTrue(cli["available"])
            self.assertEqual(cli["label"], "editppt image CLI/API")
            self.assertFalse(any(c["id"] == "codex-gpt-image" for c in cands))

    def test_finds_codex_gpt_image_under_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            skill = home / ".cursor" / "skills" / "codex-gpt-image"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# bridge\n", encoding="utf-8")
            cands = probe_candidates(home, SKILL_ROOT, honor_codex_home_env=False)
            bridge = next(c for c in cands if c["id"] == "codex-gpt-image")
            self.assertTrue(bridge["available"])
            self.assertEqual(bridge["label"], "codex-gpt-image")

    def test_empty_bridge_dir_without_skill_md_not_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            skill = home / ".cursor" / "skills" / "codex-gpt-image"
            skill.mkdir(parents=True)
            cands = probe_candidates(home, SKILL_ROOT, honor_codex_home_env=False)
            self.assertFalse(any(c["id"] == "codex-gpt-image" for c in cands))

    def test_home_override_ignores_codex_home_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_codex = root / "codex_home" / "skills" / "codex-gpt-image"
            fake_codex.mkdir(parents=True)
            (fake_codex / "SKILL.md").write_text("# bridge\n", encoding="utf-8")
            empty_home = root / "empty_home"
            empty_home.mkdir()
            previous = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = str(root / "codex_home")
            try:
                leaked = probe_candidates(empty_home, SKILL_ROOT, honor_codex_home_env=True)
                self.assertTrue(any(c["id"] == "codex-gpt-image" for c in leaked))
                isolated = probe_candidates(empty_home, SKILL_ROOT, honor_codex_home_env=False)
                self.assertFalse(any(c["id"] == "codex-gpt-image" for c in isolated))
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPTS / "probe_image_backends.py"),
                        "--home",
                        str(empty_home),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    env={**os.environ},
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                data = json.loads(proc.stdout)
                self.assertFalse(
                    any(c["id"] == "codex-gpt-image" for c in data["candidates"])
                )
            finally:
                if previous is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = previous

    def test_cli_json_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "probe_image_backends.py"), "--home", tmp],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(proc.stdout)
            self.assertIn("candidates", data)
            self.assertIn("preference_hints", data)
            self.assertIn("lock_mapping", data)
            self.assertIn("Claude Code", data["host_native_note"])
            self.assertIn("image_generate", data["host_native_note"])

    def test_build_report_claude_preference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_report(Path(tmp), SKILL_ROOT, honor_codex_home_env=False)
            self.assertEqual(
                report["preference_hints"]["claude-code"],
                ["codex-gpt-image", "editppt image CLI/API"],
            )

    def test_chinese_home_path_does_not_crash_on_non_cjk_console(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "咖啡萃取的三个变量"
            skill = home / ".cursor" / "skills" / "codex-gpt-image"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# bridge\n", encoding="utf-8")

            buffer = io.BytesIO()
            cp1252_stdout = io.TextIOWrapper(buffer, encoding="cp1252", errors="strict")
            old_argv, old_stdout = sys.argv, sys.stdout
            try:
                sys.argv = ["probe_image_backends.py", "--home", str(home)]
                sys.stdout = cp1252_stdout
                exit_code = main()
            finally:
                cp1252_stdout.flush()
                sys.stdout = old_stdout
                sys.argv = old_argv

        self.assertEqual(exit_code, 0)
        buffer.seek(0)
        output = buffer.getvalue().decode("utf-8")
        self.assertIn("咖啡萃取的三个变量", output)


if __name__ == "__main__":
    unittest.main()
