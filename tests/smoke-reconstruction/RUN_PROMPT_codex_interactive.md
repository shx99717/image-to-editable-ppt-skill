# Codex — smoke reconstruction (interactive backend lock)

Paste the fenced block below **verbatim** into a fresh Codex agent chat.
This variant exercises **probe → menu → wait → lock** and pauses for other
user decisions (OCR token, page failures). Do not hard-pin a backend.

Canonical skill source: `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`  
Installed skill: `~/.codex/skills/image-to-editable-ppt`

For Cursor interactive, use
[`RUN_PROMPT_cursor_interactive.md`](RUN_PROMPT_cursor_interactive.md).
For Codex hard-pin (`image_gen.imagegen`), use
[`RUN_PROMPT_codex.md`](RUN_PROMPT_codex.md).

---

```
You are running the image-to-editable-ppt smoke-reconstruction on CODEX only
in INTERACTIVE backend-selection mode. Do not switch hosts. Do not invent a
Cursor-only tool (GenerateImage) as available here. Do not commit or push
unless I explicitly say so.

## Host pins

| Item | Value |
|------|-------|
| Environment | Codex |
| --host | codex |
| Installed skill | ~/.codex/skills/image-to-editable-ppt |
| Locked tool / backend | (user chooses after menu — wait) |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules

1. Sync fork → `~/.codex/skills/image-to-editable-ppt` before work and after
   every fix (exclude `__pycache__` / `*.pyc`). Verify match
   (especially `SKILL.md`, `scripts/probe_image_backends.py`,
   `cli/editppt/runtime/configure_image_backend.py`,
   `cli/editppt/runtime/deck_text_hints.py`,
   `cli/editppt/runtime/paddle_text_hints.py`).
2. Edits only in the fork. Never fix-only the installed copy.
3. No commits / push / amend unless I explicitly authorize it.
4. On failure: systematic debugging; TDD for script bugs; re-sync; re-run.
5. Prefer order when recommending: `image_gen.imagegen` →
   `editppt image` CLI/API. Optionally mention `codex-gpt-image` if the
   probe shows the bridge available, but do not prefer OpenClaw /
   `image_generate`. Never claim Cursor `GenerateImage` is callable in Codex.

## Procedure

### A. Preflight sync
cd d:/git/image-to-editable-ppt-skill and sync as above.
If `editppt` is missing or may be stale after a skill sync:
  python -m pip install --user -e skills/image-to-editable-ppt/cli
Confirm Codex `image_gen.imagegen` is callable in this session (prose-check).
Stop only if the whole smoke cannot proceed — do not silently switch hosts.

### B. Backend selection (MUST wait)
1. Prose-check Codex native `image_gen.imagegen` availability in this session.
2. Run: python <skill-root>/scripts/probe_image_backends.py
3. Present an annotated menu of **available** options only; recommend one
   (prefer `image_gen.imagegen` when available).
4. **WAIT** for me to lock a specific label. Do not prepare until I lock.
5. Record the lock in the run summary (tool_name or CLI).

Map lock → prepare flags:
| Lock | Flags |
|------|-------|
| image_gen.imagegen | --image-backend builtin-imagegen |
| codex-gpt-image | --image-backend builtin-imagegen --tool-name codex-gpt-image |
| CLI/API | --image-backend editppt-image-cli |

(Do not offer GenerateImage on Codex. Omitting --tool-name with
builtin-imagegen defaults to image_gen.imagegen.)

### C. Other decision pauses
Before/during the run, also pause when SKILL.md requires it, including:
- PaddleOCR token offer when prepare/doctor reports no token
- Network/OCR approval failures needing explicit user choice
- Page failure / retry decisions
Do not auto-skip these waits.
Note: OCR uploads are per-page `source.png` (not a synthesized multi-page PDF).

### D. Prepare + rebuild
Suggest:
`tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-codex-interactive/coffee-extraction`

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  <locked flags> --job-dir <run_dir>

Then follow SKILL.md next/dispatch/record/finalize.
Workers must call the locked tool first, then `editppt image import` with
`--backend` matching that lock (`image_gen.imagegen`, `codex-gpt-image`, or
CLI producer as required by the contract).

### E. Verify (exact expect flag required)
Host/bridge lock:
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host codex --expect-tool-name <image_gen.imagegen|codex-gpt-image>

CLI lock:
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host codex --expect-backend-id editppt-image-cli

Do NOT call verify with neither expect flag (ambiguous). Do not invent a fake
tool_name for CLI. Do not use --host cursor.

### F. Report
Paste verifier output and the recorded lock; stop at exit 0.
Wrong backend = failure even if a .pptx exists.
```
