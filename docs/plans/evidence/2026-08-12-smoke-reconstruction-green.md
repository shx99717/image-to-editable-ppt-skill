# Smoke reconstruction harness — GREEN evidence

**Date:** 2026-08-12  
**Branch:** `feature/host-aware-image-backend-lean`

## Checklist

- [x] Fixture at `tests/smoke-reconstruction/fixtures/coffee-extraction.pptx` (3 slides; see `2026-08-12-smoke-reconstruction-fixture.md`)
- [x] `verify_run.py` + unit tests green (lock, page-count both axes, missing final, OpenClaw reject, CLI `--expect-backend-id`, page_request mismatch, wrong backend-id expect)
- [x] Six prompts + README present
- [x] `runs/.gitkeep` + `runs/.gitignore` (ignore `*` except keepfiles)
- [x] Root `.gitignore` un-ignores fixture PPTX under `tests/smoke-reconstruction/fixtures/`
- [x] Prompts encode fork sync, pins, interactive A+B behavior, verify command; all six prompts use `--job-dir` for prepare
- [x] No commit made (awaiting user OK)
- [x] Did not port generative T-matrix / `validation.passed` requirement

## Prompt files

- `tests/smoke-reconstruction/README.md`
- `tests/smoke-reconstruction/RUN_PROMPT_cursor.md`
- `tests/smoke-reconstruction/RUN_PROMPT_cursor_codex-gpt-image.md`
- `tests/smoke-reconstruction/RUN_PROMPT_cursor_interactive.md`
- `tests/smoke-reconstruction/RUN_PROMPT_claude.md`
- `tests/smoke-reconstruction/RUN_PROMPT_codex.md`
- `tests/smoke-reconstruction/RUN_PROMPT.md`

## Unit test command (fresh evidence)

```text
PYTHONPATH=skills/image-to-editable-ppt/cli python -m unittest \
  tests.test_smoke_reconstruction_verify tests.test_script_inventory -v
```

Result: **13 tests OK** (9 verifier + 4 inventory).

Also: `python tests/smoke-reconstruction/verify_run.py --help` exits 0.

## Note

Live multi-host E2E image generation is deferred to human paste runs of the RUN_PROMPT_* files.
