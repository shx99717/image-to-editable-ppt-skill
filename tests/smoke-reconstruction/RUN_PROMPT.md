# Portable run prompt — smoke reconstruction

Copy-paste into a fresh Codex, Claude Code, or Cursor session. Self-detects
host, recommends prefer-order, still **waits** for you to lock the backend,
then reconstructs the coffee fixture and verifies Minimal-A.

Host-pinned variants (recommended when chasing bugs one host at a time):

| Host | Prompt |
|------|--------|
| Cursor `GenerateImage` | [`RUN_PROMPT_cursor.md`](RUN_PROMPT_cursor.md) |
| Cursor `codex-gpt-image` | [`RUN_PROMPT_cursor_codex-gpt-image.md`](RUN_PROMPT_cursor_codex-gpt-image.md) |
| Cursor interactive | [`RUN_PROMPT_cursor_interactive.md`](RUN_PROMPT_cursor_interactive.md) |
| Claude Code | [`RUN_PROMPT_claude.md`](RUN_PROMPT_claude.md) |
| Codex | [`RUN_PROMPT_codex.md`](RUN_PROMPT_codex.md) |
| Codex interactive | [`RUN_PROMPT_codex_interactive.md`](RUN_PROMPT_codex_interactive.md) |

---

```
Use the image-to-editable-ppt skill to run its smoke-reconstruction end to end,
then report the verifier result. Do not commit or push unless I explicitly say so.

## Setup

1. Locate the fork repo (expected d:/git/image-to-editable-ppt-skill). Paths
   below are relative to its root.
2. Detect environment and set --host / install path:

   | Environment | --host      | Installed skill |
   |-------------|-------------|-----------------|
   | Codex CLI   | codex       | ~/.codex/skills/image-to-editable-ppt |
   | Claude Code | claude-code | ~/.claude/skills/image-to-editable-ppt |
   | Cursor      | cursor      | ~/.cursor/skills/image-to-editable-ppt |

3. Sync fork skills/image-to-editable-ppt → that install path (exclude
   __pycache__ / *.pyc). Verify match.
4. Suggest output:
   tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-<host>/coffee-extraction
   Ask me to confirm <run_dir>.

## Backend selection (MUST wait)

Prefer order by host:
| Host | Prefer first | Then | Else |
|------|--------------|------|------|
| Cursor | GenerateImage | codex-gpt-image | editppt image CLI/API |
| Codex | image_gen.imagegen | CLI/API | — |
| Claude Code | codex-gpt-image | CLI/API | (no native — do not invent) |

1. Prose-check host-native tools (Codex image_gen.imagegen, Cursor GenerateImage
   only).
2. Run python <skill-root>/scripts/probe_image_backends.py
3. Annotated menu of available options; recommend one.
4. WAIT for my lock. Record it.
5. Also pause for OCR token / other SKILL.md user decisions before dispatch.

Lock → flags:
| Lock | Flags |
|------|-------|
| GenerateImage | --image-backend builtin-imagegen --tool-name GenerateImage |
| image_gen.imagegen | --image-backend builtin-imagegen |
| codex-gpt-image | --image-backend builtin-imagegen --tool-name codex-gpt-image |
| CLI/API | --image-backend editppt-image-cli |

Never prefer OpenClaw / image_generate.

## Reconstruct

editppt prepare tests/smoke-reconstruction/fixtures/coffee-extraction.pptx \
  <locked flags> --job-dir <run_dir>

Then follow SKILL.md: run next → dispatch/local rebuild → record → finalize.

## Verify (exact expect flag required)

Host/bridge:
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host <detected> --expect-tool-name <exact-locked-tool>

CLI:
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host <detected> --expect-backend-id editppt-image-cli

Do not verify with neither expect flag. Paste output; stop at exit 0.
```
