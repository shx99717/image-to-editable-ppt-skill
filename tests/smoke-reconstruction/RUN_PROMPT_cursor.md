# Cursor — smoke reconstruction (`GenerateImage` hard-pin)

Paste the fenced block below **verbatim** into a fresh Cursor agent chat.
Pinned to **Cursor** with backend locked to **`GenerateImage`**.

For Cursor + `codex-gpt-image`, use
[`RUN_PROMPT_cursor_codex-gpt-image.md`](RUN_PROMPT_cursor_codex-gpt-image.md).
For probe/menu/wait, use
[`RUN_PROMPT_cursor_interactive.md`](RUN_PROMPT_cursor_interactive.md).

Canonical skill source: `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`  
Installed skill: `~/.cursor/skills/image-to-editable-ppt`

---

```
You are running the image-to-editable-ppt smoke-reconstruction on CURSOR only,
with image backend HARD-PINNED to `GenerateImage`. Do not switch hosts. Do not
use `codex-gpt-image` or CLI for this variant. Do not commit or push unless I
explicitly say so.

## Host pins

| Item | Value |
|------|-------|
| Environment | Cursor |
| --host | cursor |
| Installed skill | ~/.cursor/skills/image-to-editable-ppt |
| Locked tool_name | GenerateImage |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules

1. Sync fork skill → install path before work and after every fix:
   copy `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`
   → `~/.cursor/skills/image-to-editable-ppt`
   (replace destination; exclude `__pycache__` / `*.pyc`). Verify match
   (especially `SKILL.md`, `scripts/probe_image_backends.py`,
   `cli/editppt/runtime/configure_image_backend.py`).
2. Edits only in the fork repo. Never fix-only the installed copy.
3. No commits / push / amend unless I explicitly authorize it.
4. On failure: systematic debugging; TDD for script bugs; re-sync; re-run.

## Procedure

### A. Preflight sync
cd d:/git/image-to-editable-ppt-skill and sync as above. Confirm Cursor
`GenerateImage` is callable. Stop if unavailable — do not silently switch.

### B. Prepare with lock
Suggest run dir:
`tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-cursor-generateimage/coffee-extraction`
(or ask me). From fork root, prepare the fixture with:

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  --image-backend builtin-imagegen --tool-name GenerateImage \
  --job-dir <run_dir>

(Use `--job-dir` for an explicit run folder per `cli-helper.md`. The contract
must land `tool_name=GenerateImage` in `deck_manifest.json`.)

### C. Rebuild / record / finalize
Follow SKILL.md: `editppt run next` → dispatch/local rebuild → record →
finalize. Workers must call locked `GenerateImage`, then `editppt image import`
with `--backend GenerateImage`.

### D. Verify
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host cursor --expect-tool-name GenerateImage

### E. Report
Paste verifier output. Stop when exit 0. Wrong backend = failure even if a
.pptx exists.
```
