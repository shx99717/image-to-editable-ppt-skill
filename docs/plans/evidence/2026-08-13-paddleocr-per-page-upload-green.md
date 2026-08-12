# Evidence: PaddleOCR per-page PNG upload — GREEN

**Date:** 2026-08-13  
**Plan:** `docs/plans/2026-08-13-paddleocr-per-page-upload.md`  
**Repo:** `d:/git/image-to-editable-ppt-skill`  
**Branch:** `feature/host-aware-image-backend-lean`

## What changed

1. **`paddle_pages`** (`skills/image-to-editable-ppt/cli/editppt/runtime/deck_text_hints.py`): uploads each page’s `source.png` as its own OCR job; no original PDF / synth PDF on the OCR path. Partial failures keep successful pages; empty results raise `RuntimeError("PaddleOCR failed for all pages")`.
2. **`UPLOAD_TIMEOUT = 300`** used for `requests.post` in `submit_and_fetch` (`paddle_text_hints.py`). Job polling still uses the `timeout` argument / `--timeout`.
3. **`synthesize_pdf`** retained for unit tests; docstring notes it is not used by OCR.
4. **`cli-helper.md`**: removed “PDF inputs are OCR’d in one batch job” wording; documents per-page `source.png` uploads for all input types.
5. **Tests:** `PaddlePagesPerPageTest` (3 cases) + `UploadTimeoutTest`.

## Verification

```bash
cd d:/git/image-to-editable-ppt-skill
python -m unittest tests.test_page_hints -v
```

**Verification:** `python -m unittest tests.test_page_hints -v` → **16 OK** (was 15; +`test_submit_post_uses_upload_timeout`)

## Review follow-ups applied (Minor-1, Minor-2)

- POST wiring assert via mocked `requests.post`
- `submit_and_fetch` docstring narrowed (per-page PNG deck contract)

## Non-goals (as planned)

- Did **not** resume parked smoke run
- Did **not** commit / push
- Live `editppt` editable reinstall / skill sync left for operator before live `run hints`
