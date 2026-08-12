# PaddleOCR Per-Page PNG Upload — Implementation Plan

> **For the implementing agent:** Follow this plan task-by-task. Complete each step, verify it works, then move to the next.

**Goal:** Make PaddleOCR text-hints always upload each page’s `source.png` (never a multi-page PDF), and raise the client upload POST timeout to 300 seconds, so large decks stay under the API 50 MB local-upload limit and avoid client write timeouts.

**Architecture:** Change only the OCR submit path in the skill-local `editppt` CLI. `paddle_pages()` loops per page directory and calls `submit_and_fetch` on that page’s `source.png`. `submit_and_fetch` keeps job-polling `--timeout` separate from a fixed **300s** upload POST timeout. Partial page failures fall back to `builtin-ink` for that page only.

**Tech Stack:** Python 3, `requests`, existing `unittest` suite under `tests/`.

---

## SELF-CONTAINED HANDOFF NOTE

This plan is **SELF-CONTAINED**. The executor needs no prior chat session or memory file and must not ask the user to re-explain context. All decisions live here. Companion execute prompt: `docs/plans/2026-08-13-paddleocr-per-page-upload-PROMPT-execute.md`.

**Repo root:** `d:/git/image-to-editable-ppt-skill`  
**Branch (continue):** `feature/host-aware-image-backend-lean`  
**Task ID (if user later asks to commit):** `SQ5GEN-195`

---

## Section 0: Full Context

### 0.1 Why / background

During a Cursor smoke reconstruction (`GenerateImage` hard-pin), `editppt prepare` / `editppt run hints` fell back to `builtin-ink` with:

```text
text-hints: PaddleOCR failed (('Connection aborted.', TimeoutError('The write operation timed out'))); falling back to built-in detector
```

Investigation showed:

| Check | Result |
|-------|--------|
| Token in `~/.editppt/config.yaml` | Present / works |
| DNS/TLS to `paddleocr.aistudio-app.com` | OK |
| Synthesized OCR PDF for 3 coffee pages | **~14.16 MB** |
| POST that PDF with `timeout=60` | Fail @ ~60s — write timeout (no HTTP error body) |
| POST single `page_001/source.png` (~1.37 MB) | **OK @ ~34s**, `jobId` returned |
| PaddleOCR local upload limit (docs) | **50 MB** |

So the API is fine. The failure is uploading one fat multi-page file. A 10-page synth PDF can approach/exceed 50 MB even when per-page PNGs would be fine.

**Root cause in code:** For non-PDF inputs, `paddle_pages()` builds a temp PDF via `synthesize_pdf()` and uploads it in **one** job. For PDF inputs it uploads the **original PDF** in one job. Module docstring already claimed image/PPTX submit each `source.png`, but the implementation did not.

### 0.2 Confirmed decisions (do not re-litigate)

1. **Always per-page `source.png` upload** for **all** prepare input types: image(s), PDF, PPT/PPTX. Do **not** upload the original PDF. Do **not** synthesize a multi-page PDF for OCR.
2. **Upload POST timeout = 300 seconds** (user chose 300, not 600). Job **polling** timeout remains the existing CLI `--timeout` (default 300) — separate concern.
3. **Approach:** Simple rewrite of `paddle_pages` + bump POST timeout in `submit_and_fetch`. No parallel uploads. No size-gated hybrid.
4. **Partial failure:** If one page’s OCR call fails, log it and omit that page from the OCR results map so `main()` falls back to `builtin-ink` **for that page only**. Do not wipe successful pages just because one failed.
5. **All-pages failure must raise:** If `paddle_pages` ends with an **empty** results dict (every page failed or was skipped), **raise** `RuntimeError` summarizing the failure so `main()`’s existing `except` path runs (`text-hints: PaddleOCR failed (...); falling back to built-in detector`) and the summary log does **not** claim `backend=paddleocr-vl` when nothing was OCR’d. Partial success → return the non-empty dict, do not raise.
6. **Keep `synthesize_pdf()`** in the tree for the existing unit test (`SynthesizePdfTest`); it must **not** be called from the OCR path anymore. Update its docstring to say it is a helper/test utility, not the OCR submit path.
7. **Scope this plan:** Code + unit tests + doc string / `cli-helper` sync in the fork. **Out of scope:** resuming the parked smoke run; commit/push unless the user explicitly asks; collection install scripts; changing image-backend selection.
8. **Rejected:** Timeout-only fix keeping batch PDF; per-page PNG→PDF conversion; parallel OCR; redesigning OCR vs LLM vision.
9. **Plan review amendment (2026-08-13):** Items 5 (all-fail raise), Task 1 patch-import note, and live-CLI sync note were added after critical review. Second pass: move `UPLOAD_TIMEOUT` assert to Task 3; accept double-log on total failure; Task 4 remains the only required doc fix (`cli-helper.md` batch wording).

### 0.3 Audience & assumptions

- Executor works in `d:/git/image-to-editable-ppt-skill`.
- `editppt` is installed editable from `skills/image-to-editable-ppt/cli` (or run tests with `PYTHONPATH` into `cli/editppt/runtime` as existing tests do).
- Live PaddleOCR network calls are **not** required for plan completion — unit tests must mock `submit_and_fetch` / network.
- Optional live smoke resume is a **later** human/session step after this plan is green.

### 0.4 Project rules / conventions

- No commits / push / amend unless the user explicitly asks.
- Do not run collection `Install-to-*.ps1` / `Uninstall-to-*.ps1`.
- Edit the **fork** skill under `skills/image-to-editable-ppt/`. After code is green, optionally sync to `~/.cursor/skills/image-to-editable-ppt` only if verifying install path — prefer documenting the sync command rather than requiring it for acceptance.
- Prefer TDD: RED test → implement → GREEN.
- Conventional Commits later: `[SQ5GEN-195] fix: ...` if asked to commit.

### 0.5 Formats & reference material

**PaddleOCR job URL (unchanged):** `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`

**`submit_and_fetch` contract (unchanged return shape):** returns `list[dict]` of prunedResult pages. For a single PNG upload, the list length must be **1**.

**`build_page_hints(page_dir, pruned)`:** already turns one prunedResult into `text_hints` payload with `backend: paddleocr-vl`.

**`main()` fallback (keep):** `hints = results.get(page_dir) or builtin_page(page_dir)`.

See **Appendix A** for current `paddle_pages` / `submit_and_fetch` snippets to replace.

---

### Task 1: RED — unit tests for per-page PNG OCR path

**Files:**
- Modify: `tests/test_page_hints.py`
- (Implementation not yet): `skills/image-to-editable-ppt/cli/editppt/runtime/deck_text_hints.py`
- (Implementation not yet): `skills/image-to-editable-ppt/cli/editppt/runtime/paddle_text_hints.py`

**Step 1: Add failing tests**

Follow the same import style as the rest of `tests/test_page_hints.py` (runtime on `sys.path` under `skills/image-to-editable-ppt/cli/editppt/runtime`). Patch **`submit_and_fetch` where `paddle_pages` looks it up** — typically:

```python
from unittest.mock import patch
# after path setup used by this test module:
with patch("paddle_text_hints.submit_and_fetch", side_effect=fake_submit):
    ...
```

If the implementation does `from paddle_text_hints import submit_and_fetch` inside `paddle_pages`, patch `paddle_text_hints.submit_and_fetch` **before** the call (same pattern as other deferred imports in this codebase). Assert call args use each page’s `source.png`.

Add a new test class that:

1. Creates a temp run with two page dirs, each with a tiny `source.png`.
2. Mocks `submit_and_fetch` to:
   - Assert the uploaded path’s name is `source.png` (or equals that page’s `source.png`).
   - Return a minimal one-element prunedResult list (can reuse shapes from existing OCR tests in this file).
3. Calls `paddle_pages(run_dir, deck, page_dirs, token="dummy", timeout=300)`.
4. Asserts:
   - `submit_and_fetch` was called **exactly twice** (once per page).
   - **Never** called with a `.pdf` path.
   - Returned mapping has both page dirs.
5. Add a second test: when `submit_and_fetch` raises on page 2 only, page 1 is still present in results and page 2 is absent (partial success).
6. Add a third test: when `submit_and_fetch` raises on **every** page, `paddle_pages` **raises** `RuntimeError` (all-fail raise — Section 0.2 item 5).

Minimal pruned stub example:

```python
pruned = {
    "width": 100,
    "height": 100,
    "parsing_res_list": [
        {"block_label": "text", "block_content": "Hello", "block_bbox": [10, 10, 50, 30]}
    ],
}
```

**Step 2: Run tests — expect RED**

```bash
cd d:/git/image-to-editable-ppt-skill
python -m unittest tests.test_page_hints -v
```

Expected: new per-page tests **FAIL** (still one-shot PDF / wrong call pattern) or fail on partial-success behavior not yet implemented.

**Step 3: Do not implement production code in this task** — stop after RED evidence.

---

### Task 2: GREEN — rewrite `paddle_pages` to per-page PNG

**Files:**
- Modify: `skills/image-to-editable-ppt/cli/editppt/runtime/deck_text_hints.py`

**Step 1: Replace `paddle_pages` body**

Target behavior (illustrative — match style of surrounding file):

```python
def paddle_pages(run_dir: Path, deck: dict, page_dirs: list[Path], token: str, timeout: int) -> dict[Path, dict]:
    """Fetch OCR results by uploading each page's source.png as its own job."""
    from paddle_text_hints import DEFAULT_MODEL, build_page_hints, submit_and_fetch

    results: dict[Path, dict] = {}
    for page_dir in page_dirs:
        source = page_dir / "source.png"
        if not source.exists():
            print(f"text-hints: {page_dir.name}: missing source.png; skipping OCR", file=sys.stderr)
            continue
        try:
            pages = submit_and_fetch(source, token, DEFAULT_MODEL, timeout)
            if len(pages) != 1:
                raise RuntimeError(
                    f"OCR returned {len(pages)} pages for single image {source}"
                )
            results[page_dir] = build_page_hints(page_dir, pages[0])
        except Exception as exc:
            print(
                f"text-hints: {page_dir.name}: PaddleOCR failed ({exc}); "
                f"will fall back to built-in detector for this page",
                file=sys.stderr,
            )
    if not results:
        raise RuntimeError("PaddleOCR failed for all pages")
    return results
```

Notes:

- `run_dir` / `deck` may become unused — keep parameters for call-site compatibility (`main()` still passes them) or prefix with `_` if linters demand it. Do **not** break the `main()` call signature without updating all callers.
- Remove use of `tempfile` / `synthesize_pdf` from this function.
- Update the **module docstring** (lines 8–13 area) to state clearly: with a token, **every** input type OCRs each `source.png` in its own job.

**Step 2: Update `synthesize_pdf` docstring**

State it is retained for tests / optional bundling utility and is **not** used by the PaddleOCR hints path.

**Step 3: Re-run unit tests**

```bash
python -m unittest tests.test_page_hints -v
```

Expected: new per-page tests PASS; existing `SynthesizePdfTest` still PASS.

---

### Task 3: GREEN — upload POST timeout 300s

**Files:**
- Modify: `skills/image-to-editable-ppt/cli/editppt/runtime/paddle_text_hints.py`

**Step 1: Introduce a named constant and use it on POST**

Near top of file (with other constants):

```python
UPLOAD_TIMEOUT = 300  # seconds — client timeout for job submit POST (upload + HTTP response)
```

In `submit_and_fetch`, change:

```python
timeout=60,  # on requests.post
```

to:

```python
timeout=UPLOAD_TIMEOUT,
```

Keep `requests.get` poll/result timeouts as they are (60) unless you have a clear reason — **out of scope** to change poll HTTP timeouts. The function argument `timeout` remains the **job polling** deadline (`time.time() - started > timeout`).

**Step 2: Assert constant from test**

Add (or keep) in `tests/test_page_hints.py`:

```python
def test_upload_timeout_is_300(self) -> None:
    from paddle_text_hints import UPLOAD_TIMEOUT
    self.assertEqual(300, UPLOAD_TIMEOUT)
```

Also:

```bash
python -c "import sys; sys.path.insert(0, r'skills/image-to-editable-ppt/cli/editppt/runtime'); from paddle_text_hints import UPLOAD_TIMEOUT; assert UPLOAD_TIMEOUT == 300"
```

**Step 3: Full hints test module green**

```bash
python -m unittest tests.test_page_hints -v
```

Expected: all PASS.

**Note (acceptable noise):** On total OCR failure, per-page stderr lines plus `main()`’s `PaddleOCR failed (...); falling back...` may both print. Do **not** spend scope silencing that unless it confuses tests.

---

### Task 4: Docs sync

**Files:**
- Modify: `skills/image-to-editable-ppt/references/cli-helper.md` (around the `editppt page hints` purpose paragraph that currently says PDF inputs are OCR’d in one batch job)
- Modify: module docstring in `deck_text_hints.py` if not fully done in Task 2

**Step 1: Replace batch-PDF wording**

Old idea to remove: “PDF inputs are OCR’d in one batch job…”

New idea: When a PaddleOCR token is available, `prepare` / `run hints` upload each page’s `source.png` as its own OCR job (all input types). Without a token, the built-in offline detector runs per page.

**Step 2: Skim for other “one batch” / “synth PDF” claims** under `skills/image-to-editable-ppt/` and fix any that contradict Section 0.2. Do **not** rewrite unrelated SKILL policy.

---

### Task 5: Verification evidence + optional install sync note

**Files:**
- Create: `docs/plans/evidence/2026-08-13-paddleocr-per-page-upload-green.md`

**Step 1: Run final verification**

```bash
cd d:/git/image-to-editable-ppt-skill
python -m unittest tests.test_page_hints -v
```

Capture summary (counts / OK).

**Step 2: Write evidence file** with:

- What changed (per-page PNG, UPLOAD_TIMEOUT=300)
- Test command + result
- Explicit non-goals completed (no smoke resume, no commit unless asked)

**Step 3 (optional for acceptance; required before any live CLI check):**  
Unit tests against fork sources do **not** update an already-installed `editppt` egg/scripts entrypoint. Before any live `editppt run hints` / prepare verification:

```bash
python -m pip install --user -e "d:/git/image-to-editable-ppt-skill/skills/image-to-editable-ppt/cli"
# and/or sync skill tree → ~/.cursor/skills/image-to-editable-ppt (exclude __pycache__ / *.pyc)
```

Not required solely to mark this plan’s unittest acceptance green.

---

## Acceptance / Verification Summary

Executor is done when **all** are true:

- [ ] `paddle_pages` uploads only `source.png`, once per page; no OCR path calls `synthesize_pdf` or original PDF
- [ ] Empty OCR results → `paddle_pages` raises; partial success returns non-empty dict without raising
- [ ] `UPLOAD_TIMEOUT == 300` used for `requests.post` in `submit_and_fetch`
- [ ] Job polling still uses the `timeout` argument / `--timeout`
- [ ] Partial page OCR failure does not drop successful pages
- [ ] `python -m unittest tests.test_page_hints -v` passes
- [ ] `cli-helper.md` no longer claims PDF one-batch OCR
- [ ] Evidence file written under `docs/plans/evidence/`
- [ ] No commit/push unless user explicitly requested
- [ ] (If live CLI checked) editable reinstall and/or skill sync performed

---

## Appendix A — Current code to replace (embedded)

### A.1 Current `paddle_pages` (batch / synth) — `deck_text_hints.py`

```python
def paddle_pages(run_dir: Path, deck: dict, page_dirs: list[Path], token: str, timeout: int) -> dict[Path, dict]:
    """Fetch OCR results for all pages in ONE job; returns {page_dir: hints}."""
    import tempfile

    from paddle_text_hints import DEFAULT_MODEL, build_page_hints, submit_and_fetch

    original = None
    if str(deck.get("input_type", "")) == "pdf":
        input_dir = run_dir / "input"
        candidates = sorted(input_dir.glob("*.pdf")) if input_dir.exists() else []
        original = candidates[0] if candidates else None

    synthesized = None
    try:
        if original is None:
            handle = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            handle.close()
            synthesized = Path(handle.name)
            synthesize_pdf(page_dirs, synthesized)
            original = synthesized
        pages = submit_and_fetch(original, token, DEFAULT_MODEL, timeout)
    finally:
        if synthesized is not None:
            synthesized.unlink(missing_ok=True)
    if len(pages) != len(page_dirs):
        raise RuntimeError(f"OCR returned {len(pages)} pages for {len(page_dirs)} page dirs")
    return {page_dir: build_page_hints(page_dir, pruned) for page_dir, pruned in zip(page_dirs, pages)}
```

### A.2 Current upload timeout — `paddle_text_hints.py` inside `submit_and_fetch`

```python
        response = requests.post(
            JOB_URL,
            headers=headers,
            data={"model": model, "optionalPayload": json.dumps(optional)},
            files={"file": handle},
            timeout=60,  # REPLACE with UPLOAD_TIMEOUT (300)
        )
```

### A.3 `cli-helper.md` sentence to fix

Under `editppt page hints` purpose (~line 207): remove “PDF inputs are OCR’d in one batch job…” and replace with per-page `source.png` wording from Task 4.

---

## Appendix B — Parked smoke (DO NOT run in this plan)

Run dir left from earlier session (resume later, outside this plan):

`tests/smoke-reconstruction/runs/20260812-1726-cursor-generateimage/coffee-extraction`

Already locked: `image_backend.tool_name=GenerateImage`. Hints currently `builtin-ink`. After this fix lands in a future session: re-sync skill if needed → `editppt run hints <run_dir>` → expect `paddleocr-vl` → continue dispatch/record/finalize → `verify_run.py --host cursor --expect-tool-name GenerateImage`.
