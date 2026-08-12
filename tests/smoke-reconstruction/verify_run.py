#!/usr/bin/env python3
"""Minimal-A verifier for image-to-editable-ppt smoke-reconstruction runs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from zipfile import ZipFile

ALLOWLISTED_TOOLS = frozenset(
    {"GenerateImage", "image_gen.imagegen", "codex-gpt-image"}
)
CLI_BACKEND_ID = "editppt-image-cli"
DEFAULT_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "coffee-extraction.pptx"
)
SLIDE_RE = re.compile(r"^ppt/slides/slide\d+\.xml$")


def pptx_slide_count(path: Path) -> int:
    with ZipFile(path) as zf:
        return sum(1 for name in zf.namelist() if SLIDE_RE.match(name))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_final_pptx(run_dir: Path, deck: dict[str, Any]) -> Path | None:
    output = deck.get("output")
    if isinstance(output, str) and output.strip():
        candidate = (run_dir / output).resolve()
        if candidate.is_file():
            return candidate
    final_dir = run_dir / "final"
    if final_dir.is_dir():
        pptx_files = sorted(final_dir.glob("*.pptx"))
        if pptx_files:
            return pptx_files[0]
    return None


def _same_backend(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        a.get("backend_id") == b.get("backend_id")
        and a.get("tool_name") == b.get("tool_name")
    )


def verify_run(
    run_dir: Path,
    *,
    host: str,
    expect_tool_name: str | None = None,
    expect_backend_id: str | None = None,
    fixture_path: Path | None = None,
) -> tuple[int, list[str]]:
    """Return (exit_code, report_lines). Exit 0 only when all BASELINE checks pass."""
    lines: list[str] = []
    failures = 0

    def ok(msg: str) -> None:
        lines.append(f"[PASS] {msg}")

    def fail(msg: str) -> None:
        nonlocal failures
        failures += 1
        lines.append(f"[FAIL] {msg}")

    run_dir = run_dir.resolve()
    fixture = (fixture_path or DEFAULT_FIXTURE).resolve()

    if expect_tool_name and expect_backend_id:
        fail("pass exactly one of --expect-tool-name or --expect-backend-id, not both")
        return 1, lines

    if not run_dir.is_dir():
        fail(f"run_dir is not a directory: {run_dir}")
        return 1, lines

    deck_path = run_dir / "deck_manifest.json"
    jobs_path = run_dir / "page_jobs.json"
    if not deck_path.is_file():
        fail("deck_manifest.json missing")
        return 1, lines
    if not jobs_path.is_file():
        fail("page_jobs.json missing")
        return 1, lines
    ok("deck_manifest.json and page_jobs.json exist")

    if not fixture.is_file():
        fail(f"fixture missing: {fixture}")
        return 1, lines

    try:
        deck = _load_json(deck_path)
        jobs = _load_json(jobs_path)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"manifest JSON unreadable: {exc}")
        return 1, lines

    backend = deck.get("image_backend")
    if not isinstance(backend, dict):
        fail("deck_manifest.image_backend missing or not an object")
        return 1, lines

    backend_id = backend.get("backend_id")
    tool_name = backend.get("tool_name")
    if not backend_id:
        fail("image_backend.backend_id missing")
    else:
        ok(f"image_backend.backend_id={backend_id}")
    if tool_name is None or tool_name == "":
        fail("image_backend.tool_name missing")
    else:
        ok(f"image_backend.tool_name={tool_name}")

    # Lock / allowlist checks
    if expect_tool_name is not None:
        if tool_name != expect_tool_name:
            fail(
                f"expected tool_name={expect_tool_name!r}, got {tool_name!r}"
            )
        else:
            ok(f"tool_name matches --expect-tool-name={expect_tool_name}")
    elif expect_backend_id is not None:
        if backend_id != expect_backend_id:
            fail(
                f"expected backend_id={expect_backend_id!r}, got {backend_id!r}"
            )
        else:
            ok(f"backend_id matches --expect-backend-id={expect_backend_id}")
    else:
        if backend_id == CLI_BACKEND_ID:
            ok("backend_id=editppt-image-cli accepted (no expect flag)")
        elif tool_name in ALLOWLISTED_TOOLS:
            ok(f"tool_name {tool_name!r} is allowlisted")
        else:
            fail(
                f"tool_name {tool_name!r} not allowlisted and not CLI "
                f"(allowlist: {sorted(ALLOWLISTED_TOOLS)})"
            )

    # Invented-native / OpenClaw rejection (any host; Claude has no native tool)
    if tool_name not in ALLOWLISTED_TOOLS and backend_id != CLI_BACKEND_ID:
        fail(
            f"rejected non-allowlisted tool_name={tool_name!r} "
            f"(host={host}; no invented Claude-native / OpenClaw tools)"
        )

    # Per-page image_backend copy
    pages = jobs.get("pages")
    if not isinstance(pages, list):
        fail("page_jobs.pages missing or not a list")
        pages = []
    for page in pages:
        if not isinstance(page, dict):
            fail("page_jobs.pages entry is not an object")
            continue
        rel = page.get("page_request") or (
            f"{page.get('page_dir')}/page_request.json"
            if page.get("page_dir")
            else None
        )
        if not rel:
            fail(f"page {page.get('page_id')} missing page_request path")
            continue
        req_path = run_dir / rel
        if not req_path.is_file():
            fail(f"page_request missing: {rel}")
            continue
        try:
            req = _load_json(req_path)
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"page_request unreadable ({rel}): {exc}")
            continue
        page_backend = req.get("image_backend")
        if not isinstance(page_backend, dict):
            fail(f"{rel}: image_backend missing")
        elif not _same_backend(backend, page_backend):
            fail(f"{rel}: image_backend does not match deck_manifest")
        else:
            ok(f"{rel}: image_backend matches deck")

    # Final pptx
    final_pptx = _resolve_final_pptx(run_dir, deck)
    if final_pptx is None:
        fail("final .pptx missing (deck_manifest.output or final/*.pptx)")
    else:
        ok(f"final pptx present: {final_pptx.relative_to(run_dir)}")

    # Page counts vs fixture
    try:
        fixture_slides = pptx_slide_count(fixture)
    except OSError as exc:
        fail(f"fixture unreadable: {exc}")
        return 1, lines

    job_count = len(pages) if isinstance(pages, list) else -1
    if job_count != fixture_slides:
        fail(
            f"page_jobs page count {job_count} != fixture slides {fixture_slides}"
        )
    else:
        ok(f"page_jobs page count matches fixture ({fixture_slides})")

    if final_pptx is not None:
        try:
            final_slides = pptx_slide_count(final_pptx)
        except OSError as exc:
            fail(f"final pptx unreadable: {exc}")
            final_slides = -1
        if final_slides != fixture_slides:
            fail(
                f"final pptx slide count {final_slides} != fixture slides {fixture_slides}"
            )
        else:
            ok(f"final pptx slide count matches fixture ({fixture_slides})")

    return (0 if failures == 0 else 1), lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Minimal-A verifier for smoke-reconstruction runs."
    )
    parser.add_argument("run_dir", type=Path, help="Path to a coffee-extraction run dir")
    parser.add_argument(
        "--host",
        required=True,
        choices=("cursor", "claude-code", "codex"),
        help="Host label for this smoke run",
    )
    parser.add_argument(
        "--expect-tool-name",
        default=None,
        help="Require deck image_backend.tool_name to match (host/bridge locks)",
    )
    parser.add_argument(
        "--expect-backend-id",
        default=None,
        help="Require deck image_backend.backend_id to match (e.g. editppt-image-cli)",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Input fixture PPTX used for slide-count parity (default: coffee fixture)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    code, lines = verify_run(
        args.run_dir,
        host=args.host,
        expect_tool_name=args.expect_tool_name,
        expect_backend_id=args.expect_backend_id,
        fixture_path=args.fixture,
    )
    for line in lines:
        print(line)
    if code == 0:
        print("[PASS] smoke-reconstruction Minimal-A baseline")
    else:
        print("[FAIL] smoke-reconstruction Minimal-A baseline")
    return code


if __name__ == "__main__":
    sys.exit(main())
