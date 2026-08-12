# image-to-editable-ppt smoke reconstruction

A small, repeatable end-to-end smoke harness for the **reconstruction** skill
(`image-to-editable-ppt`), modeled on the *shape* of `codex-ppt` smoke-deck —
not a port of its generative T-matrix.

Use it after host-backend / skill changes to confirm:

- a coffee PPTX fixture can be prepared and rebuilt into an editable `.pptx`
- the run locks the expected image backend (`tool_name` or CLI `backend_id`)
- page count in `page_jobs` **and** the final deck matches the fixture

## Fixture

| Item | Value |
|------|-------|
| Path | `fixtures/coffee-extraction.pptx` |
| Slides | **3** |
| Source | Copied from `codex-ppt-skill` run `tests/smoke-deck/runs/20260810-1654-claude/coffee-extraction/coffee-extraction.pptx` |

## Quick start

1. Pick a prompt below and paste it into a fresh agent chat on that host.
2. Let the agent sync the fork skill → install path, run the skill, then verify.
3. Confirm `verify_run.py` exits 0.

| Prompt | Host | Backend lock |
|--------|------|--------------|
| [`RUN_PROMPT_cursor.md`](RUN_PROMPT_cursor.md) | Cursor | hard-pin `GenerateImage` |
| [`RUN_PROMPT_cursor_codex-gpt-image.md`](RUN_PROMPT_cursor_codex-gpt-image.md) | Cursor | hard-pin `codex-gpt-image` |
| [`RUN_PROMPT_cursor_interactive.md`](RUN_PROMPT_cursor_interactive.md) | Cursor | probe → menu → wait → lock (+ other pauses) |
| [`RUN_PROMPT_claude.md`](RUN_PROMPT_claude.md) | Claude Code | hard-pin `codex-gpt-image` (no invented native) |
| [`RUN_PROMPT_codex.md`](RUN_PROMPT_codex.md) | Codex | hard-pin `image_gen.imagegen` |
| [`RUN_PROMPT.md`](RUN_PROMPT.md) | any | self-detect host; still wait to lock |

## Verifier (`verify_run.py`)

Minimal-A BASELINE (exit 0 only if all pass):

- `deck_manifest.json` + `page_jobs.json` exist
- `image_backend.backend_id` + `tool_name` present
- `--expect-tool-name` exact match **or** `--expect-backend-id` (CLI) **or** allowlisted tool / CLI
- each `pages/page_*/page_request.json` copies the same `image_backend`
- final `.pptx` exists (`deck_manifest.output` or `final/*.pptx`)
- `len(page_jobs.pages)` **and** final slide count **==** fixture slide count
- rejects OpenClaw `image_generate` / invented Claude-native names

**Not checked in v1:** `validation.json.passed`, OCR/visual quality, TARGET progress tiers.

```bash
python tests/smoke-reconstruction/verify_run.py \
  tests/smoke-reconstruction/runs/<stamp>-<host>/coffee-extraction \
  --host cursor --expect-tool-name GenerateImage
```

For interactive/generic runs that locked CLI:

```bash
python tests/smoke-reconstruction/verify_run.py <run_dir> \
  --host <host> --expect-backend-id editppt-image-cli
```

## Output layout

```
tests/smoke-reconstruction/runs/<YYYYMMDD-HHMM>-<host>[-variant]/coffee-extraction/
```

`runs/` is gitignored except `.gitkeep`. Unit tests live at
`tests/test_smoke_reconstruction_verify.py` (fake run dirs; no live image gen required).
