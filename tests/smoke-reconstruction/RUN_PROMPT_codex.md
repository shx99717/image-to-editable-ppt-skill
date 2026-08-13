# Codex — smoke reconstruction (`image_gen.imagegen` hard-pin)

Paste the fenced block below **verbatim** into a fresh Codex agent chat.
Pinned to **Codex** with backend locked to **`image_gen.imagegen`**.

Canonical skill source: `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`  
Installed skill: `~/.codex/skills/image-to-editable-ppt`

---

```
You are running the image-to-editable-ppt smoke-reconstruction on CODEX only,
with image backend HARD-PINNED to `image_gen.imagegen`. Do not switch hosts.
Do not use GenerateImage or invent alternate hosts. Do not commit or push
unless I explicitly say so.

## Host pins

| Item | Value |
|------|-------|
| Environment | Codex |
| --host | codex |
| Installed skill | ~/.codex/skills/image-to-editable-ppt |
| Locked tool_name | image_gen.imagegen |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules

1. Sync fork → `~/.codex/skills/image-to-editable-ppt` (exclude `__pycache__` /
   `*.pyc`). Verify match after every fix.
2. Edits only in the fork.
3. No commits / push without my explicit OK.
4. On failure: systematic debugging + TDD; re-sync; re-run.

## Procedure

### A. Preflight sync
Sync fork → install. Confirm Codex `image_gen.imagegen` is callable.

### B. Prepare with lock
Suggest:
`tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-codex/coffee-extraction`

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  --image-backend builtin-imagegen \
  --job-dir <run_dir>

(Default tool_name is `image_gen.imagegen` when --tool-name is omitted.)

### C. Rebuild / record / finalize
Follow SKILL.md. Import with `--backend image_gen.imagegen` (legacy
`builtin-imagegen` alias only when contract tool_name is image_gen.imagegen).

### D. Verify
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host codex --expect-tool-name image_gen.imagegen

### E. Report
Paste verifier output; stop at exit 0. Wrong backend = failure.
```
