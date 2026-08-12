# Cursor — smoke reconstruction (`codex-gpt-image` hard-pin)

Paste the fenced block below **verbatim** into a fresh Cursor agent chat.
Pinned to **Cursor** with backend locked to **`codex-gpt-image`**.

For Cursor + `GenerateImage`, use [`RUN_PROMPT_cursor.md`](RUN_PROMPT_cursor.md).

Canonical skill source: `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`  
Installed skill: `~/.cursor/skills/image-to-editable-ppt`

---

```
You are running the image-to-editable-ppt smoke-reconstruction on CURSOR only,
with image backend HARD-PINNED to `codex-gpt-image`. Do not switch hosts. Do not
use `GenerateImage` or CLI for this variant. Do not commit or push unless I
explicitly say so.

## Host pins

| Item | Value |
|------|-------|
| Environment | Cursor |
| --host | cursor |
| Installed skill | ~/.cursor/skills/image-to-editable-ppt |
| Locked tool_name | codex-gpt-image |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules

1. Sync fork → `~/.cursor/skills/image-to-editable-ppt` (exclude `__pycache__` /
   `*.pyc`). Verify match after every fix.
2. Edits only in `d:/git/image-to-editable-ppt-skill`.
3. No commits / push without my explicit OK.
4. On failure: systematic debugging + TDD for script bugs; re-sync; re-run.
5. Require the `codex-gpt-image` bridge skill to be installed/callable. Stop if
   missing — do not fall back to GenerateImage in this variant.

## Procedure

### A. Preflight sync
Sync fork → install path. Confirm `codex-gpt-image` is callable.

### B. Prepare with lock
Suggest:
`tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-cursor-codex-gpt-image/coffee-extraction`

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  --image-backend builtin-imagegen --tool-name codex-gpt-image \
  --job-dir <run_dir>

### C. Rebuild / record / finalize
Follow SKILL.md next/dispatch/record/finalize. Import with
`--backend codex-gpt-image`.

### D. Verify
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host cursor --expect-tool-name codex-gpt-image

### E. Report
Paste verifier output; stop at exit 0. Wrong backend = failure.
```
