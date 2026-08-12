# Claude Code — smoke reconstruction (`codex-gpt-image` hard-pin)

Paste the fenced block below **verbatim** into a fresh Claude Code chat.
Pinned to **Claude Code** with backend locked to **`codex-gpt-image`**.
Claude has **no** native image tool — do not invent one.

Canonical skill source: `d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt`  
Installed skill: `~/.claude/skills/image-to-editable-ppt`

---

```
You are running the image-to-editable-ppt smoke-reconstruction on CLAUDE CODE
only, with image backend HARD-PINNED to `codex-gpt-image`. Do not switch hosts.
Do not invent a Claude-native image tool. Do not use OpenClaw `image_generate`.
Do not commit or push unless I explicitly say so.

## Host pins

| Item | Value |
|------|-------|
| Environment | Claude Code |
| --host | claude-code |
| Installed skill | ~/.claude/skills/image-to-editable-ppt |
| Locked tool_name | codex-gpt-image |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules

1. Sync fork → `~/.claude/skills/image-to-editable-ppt` (exclude `__pycache__` /
   `*.pyc`). Verify match after every fix.
2. Edits only in the fork.
3. No commits / push without my explicit OK.
4. On failure: systematic debugging + TDD; re-sync; re-run.
5. Never invent `ClaudeImage`, `generate_image`, or similar native names.

## Procedure

### A. Preflight sync
Sync fork → install. Confirm `codex-gpt-image` bridge is callable. Stop if not.

### B. Prepare with lock
Suggest:
`tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-claude/coffee-extraction`

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  --image-backend builtin-imagegen --tool-name codex-gpt-image \
  --job-dir <run_dir>

### C. Rebuild / record / finalize
Follow SKILL.md. Import with `--backend codex-gpt-image`.

### D. Verify
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host claude-code --expect-tool-name codex-gpt-image

### E. Report
Paste verifier output; stop at exit 0.
```
