# Cursor — smoke reconstruction (interactive backend lock)

Paste the fenced block below **verbatim** into a fresh Cursor agent chat.
This variant exercises **probe → menu → wait → lock** and pauses for other
user decisions (OCR token, page failures). Do not hard-pin a backend.

Canonical skill source: `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`  
Installed skill: `~/.cursor/skills/image-to-editable-ppt`

---

```
You are running the image-to-editable-ppt smoke-reconstruction on CURSOR only
in INTERACTIVE backend-selection mode. Do not switch hosts. Do not commit or
push unless I explicitly say so.

## Host pins

| Item | Value |
|------|-------|
| Environment | Cursor |
| --host | cursor |
| Installed skill | ~/.cursor/skills/image-to-editable-ppt |
| Locked tool / backend | (user chooses after menu — wait) |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules

1. Sync fork → `~/.cursor/skills/image-to-editable-ppt` before work and after
   every fix; verify match.
2. Edits only in the fork.
3. No commits / push without my explicit OK.
4. On failure: systematic debugging + TDD; re-sync; re-run.
5. Prefer order when recommending: GenerateImage → codex-gpt-image →
   editppt image CLI/API. Never prefer OpenClaw / image_generate.

## Procedure

### A. Preflight sync
cd d:/git/image-to-editable-ppt-skill; sync fork → install path.

### B. Backend selection (MUST wait)
1. Prose-check Cursor `GenerateImage` availability in this session.
2. Run: python <skill-root>/scripts/probe_image_backends.py
3. Present an annotated menu of **available** options only; recommend one.
4. **WAIT** for me to lock a specific label. Do not prepare until I lock.
5. Record the lock in the run summary (tool_name or CLI).

Map lock → prepare flags:
| Lock | Flags |
|------|-------|
| GenerateImage | --image-backend builtin-imagegen --tool-name GenerateImage |
| image_gen.imagegen | --image-backend builtin-imagegen |
| codex-gpt-image | --image-backend builtin-imagegen --tool-name codex-gpt-image |
| CLI/API | --image-backend editppt-image-cli |

### C. Other decision pauses
Before/during the run, also pause when SKILL.md requires it, including:
- PaddleOCR token offer when prepare/doctor reports no token
- Network/OCR approval failures needing explicit user choice
- Page failure / retry decisions
Do not auto-skip these waits.

### D. Prepare + rebuild
Suggest:
`tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-cursor-interactive/coffee-extraction`

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  <locked flags> --job-dir <run_dir>

Then follow SKILL.md next/dispatch/record/finalize.

### E. Verify (exact expect flag required)
Host/bridge lock:
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host cursor --expect-tool-name <GenerateImage|image_gen.imagegen|codex-gpt-image>

CLI lock:
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host cursor --expect-backend-id editppt-image-cli

Do NOT call verify with neither expect flag (ambiguous). Do not invent a fake
tool_name for CLI.

### F. Report
Paste verifier output and the recorded lock; stop at exit 0.
```
