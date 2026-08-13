"""Unit tests for smoke-reconstruction verify_run.py (Minimal-A)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = REPO_ROOT / "tests" / "smoke-reconstruction"
VERIFY_PATH = SMOKE_DIR / "verify_run.py"
FIXTURE = SMOKE_DIR / "fixtures" / "coffee-extraction.pptx"

sys.path.insert(0, str(SMOKE_DIR))


def _minimal_pptx(path: Path, slide_count: int) -> None:
    """Write a tiny OOXML pptx with N slide XML parts (no real drawing ML)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        for i in range(1, slide_count + 1):
            zf.writestr(f"ppt/slides/slide{i}.xml", f"<sld>{i}</sld>")


def _write_run(
    root: Path,
    *,
    page_count: int,
    final_slides: int,
    backend_id: str = "builtin-imagegen",
    tool_name: str = "GenerateImage",
    include_final: bool = True,
    output_rel: str = "final/origin_edited.pptx",
) -> Path:
    """Build a fake reconstruction run directory."""
    run_dir = root / "coffee-extraction"
    run_dir.mkdir(parents=True)
    backend = {
        "backend_id": backend_id,
        "tool_name": tool_name,
        "tool_call": tool_name,
    }
    pages = []
    for i in range(1, page_count + 1):
        page_id = f"page_{i:03d}"
        page_dir = run_dir / "pages" / page_id
        page_dir.mkdir(parents=True)
        req = {
            "page_id": page_id,
            "image_backend": dict(backend),
        }
        (page_dir / "page_request.json").write_text(
            json.dumps(req, indent=2), encoding="utf-8"
        )
        pages.append(
            {
                "page_id": page_id,
                "status": "completed",
                "page_dir": f"pages/{page_id}",
                "page_request": f"pages/{page_id}/page_request.json",
            }
        )

    deck = {
        "schema_version": 1,
        "run_id": "smoke-test",
        "image_backend": dict(backend),
        "pages": [{"page_id": p["page_id"]} for p in pages],
        "output": output_rel,
    }
    (run_dir / "deck_manifest.json").write_text(
        json.dumps(deck, indent=2), encoding="utf-8"
    )
    (run_dir / "page_jobs.json").write_text(
        json.dumps(
            {"schema_version": 1, "run_id": "smoke-test", "pages": pages},
            indent=2,
        ),
        encoding="utf-8",
    )
    if include_final:
        final_path = run_dir / output_rel
        _minimal_pptx(final_path, final_slides)
    return run_dir


class SmokeReconstructionVerifyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # RED until Task 3 lands verify_run.py — ImportError/FileNotFound is expected.
        if not VERIFY_PATH.is_file():
            raise FileNotFoundError(f"missing verifier: {VERIFY_PATH}")
        import verify_run as vr  # type: ignore

        cls.vr = vr

    def test_matching_page_count_and_tool_name_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(Path(tmp), page_count=3, final_slides=3)
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_tool_name="GenerateImage",
                fixture_path=fixture,
            )
            self.assertEqual(0, code, "\n".join(lines))
            self.assertTrue(any(line.startswith("[PASS]") for line in lines))

    def test_wrong_expect_tool_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(Path(tmp), page_count=3, final_slides=3)
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_tool_name="codex-gpt-image",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            self.assertTrue(any("[FAIL]" in line for line in lines))

    def test_final_pptx_slide_count_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(Path(tmp), page_count=3, final_slides=2)
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_tool_name="GenerateImage",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            self.assertTrue(any("slide" in line.lower() for line in lines))

    def test_page_jobs_count_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(Path(tmp), page_count=2, final_slides=3)
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_tool_name="GenerateImage",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            joined = "\n".join(lines).lower()
            self.assertTrue("page_jobs" in joined or "page count" in joined)

    def test_missing_final_pptx_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(
                Path(tmp), page_count=3, final_slides=3, include_final=False
            )
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_tool_name="GenerateImage",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            self.assertTrue(any("final" in line.lower() or "pptx" in line.lower() for line in lines))

    def test_openclaw_image_generate_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(
                Path(tmp),
                page_count=3,
                final_slides=3,
                tool_name="image_generate",
            )
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="claude-code",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            self.assertTrue(any("[FAIL]" in line for line in lines))

    def test_cli_lock_with_expect_backend_id_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(
                Path(tmp),
                page_count=3,
                final_slides=3,
                backend_id="editppt-image-cli",
                tool_name="editppt image",
            )
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_backend_id="editppt-image-cli",
                fixture_path=fixture,
            )
            self.assertEqual(0, code, "\n".join(lines))

    def test_page_request_image_backend_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(Path(tmp), page_count=3, final_slides=3)
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            req_path = run_dir / "pages" / "page_002" / "page_request.json"
            req = json.loads(req_path.read_text(encoding="utf-8"))
            req["image_backend"]["tool_name"] = "codex-gpt-image"
            req_path.write_text(json.dumps(req, indent=2), encoding="utf-8")
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_tool_name="GenerateImage",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            self.assertTrue(
                any("does not match" in line for line in lines),
                "\n".join(lines),
            )

    def test_wrong_expect_backend_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _write_run(
                Path(tmp),
                page_count=3,
                final_slides=3,
                backend_id="editppt-image-cli",
                tool_name="editppt image",
            )
            fixture = Path(tmp) / "fixture.pptx"
            _minimal_pptx(fixture, 3)
            code, lines = self.vr.verify_run(
                run_dir,
                host="cursor",
                expect_backend_id="builtin-imagegen",
                fixture_path=fixture,
            )
            self.assertNotEqual(0, code)
            self.assertTrue(any("[FAIL]" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
