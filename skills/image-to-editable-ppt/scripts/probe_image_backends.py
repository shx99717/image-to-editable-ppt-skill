#!/usr/bin/env python3
"""Probe non-host-native image backend signals for image-to-editable-ppt (JSON stdout).

Does NOT detect IDE-native tools. The agent must prose-check Codex `image_gen.imagegen`
and Cursor `GenerateImage`. Claude Code has no native image tool.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _codex_home(home: Path, *, honor_env: bool = True) -> Path:
    if honor_env:
        override = os.environ.get("CODEX_HOME")
        if override:
            return Path(override).expanduser()
    return home / ".codex"


def probe_candidates(
    home: Path,
    skill_root: Path,
    *,
    honor_codex_home_env: bool = True,
) -> list[dict]:
    candidates: list[dict] = []
    skill_bases = [
        home / ".claude" / "skills" / "codex-gpt-image",
        home / ".cursor" / "skills" / "codex-gpt-image",
        _codex_home(home, honor_env=honor_codex_home_env) / "skills" / "codex-gpt-image",
    ]
    for base in skill_bases:
        if (base / "SKILL.md").is_file():
            candidates.append(
                {
                    "id": "codex-gpt-image",
                    "label": "codex-gpt-image",
                    "kind": "bridge-skill",
                    "path": str(base),
                    "available": True,
                    "reference_image": True,
                    "auth": "Codex/ChatGPT OAuth via bridge",
                }
            )
            break

    cli = skill_root / "cli" / "editppt" / "runtime" / "image_gen.py"
    candidates.append(
        {
            "id": "editppt-image-cli",
            "label": "editppt image CLI/API",
            "kind": "cli-api-fallback",
            "path": str(cli),
            "available": cli.is_file(),
            "reference_image": True,
            "auth": "Codex OAuth then OPENAI_API_KEY / ~/.editppt config (no secrets printed)",
        }
    )
    return candidates


def build_report(
    home: Path,
    skill_root: Path,
    *,
    honor_codex_home_env: bool = True,
) -> dict:
    return {
        "host_native_note": (
            "This script does NOT detect IDE-native tools. Agent must prose-check "
            "Codex image_gen.imagegen and Cursor GenerateImage. Claude Code has NO native image tool. "
            "Do not present OpenClaw image_generate as a supported backend."
        ),
        "preference_hints": {
            "cursor": ["GenerateImage (prose)", "codex-gpt-image", "editppt image CLI/API"],
            "codex": ["image_gen.imagegen (prose)", "editppt image CLI/API"],
            "claude-code": ["codex-gpt-image", "editppt image CLI/API"],
        },
        "lock_mapping": {
            "GenerateImage": "editppt prepare --image-backend builtin-imagegen --tool-name GenerateImage",
            "image_gen.imagegen": "editppt prepare --image-backend builtin-imagegen",
            "codex-gpt-image": "editppt prepare --image-backend builtin-imagegen --tool-name codex-gpt-image",
            "editppt image CLI/API": "editppt prepare --image-backend editppt-image-cli",
        },
        "candidates": probe_candidates(
            home,
            skill_root,
            honor_codex_home_env=honor_codex_home_env,
        ),
    }


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        help="Override home directory for skill-dir probes (tests). Ignores CODEX_HOME.",
    )
    args = parser.parse_args()
    home_override = bool(args.home)
    home = Path(args.home).expanduser() if args.home else Path.home()
    skill_root = Path(__file__).resolve().parents[1]
    report = build_report(
        home,
        skill_root,
        honor_codex_home_env=not home_override,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
