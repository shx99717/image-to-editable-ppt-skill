# Smoke Reconstruction Harness — Implementation Plan

> **For the implementing agent:** Follow this plan task-by-task. Complete each step, verify it works, then move to the next.

**Goal:** Add a codex-ppt-style smoke harness under `tests/smoke-reconstruction/` for `image-to-editable-ppt`: stable coffee PPTX fixture, six paste-ready host prompts, and a minimal `verify_run.py` that checks run artifacts, backend lock, and page-count parity with the fixture.

**Architecture:** Mirror the *shape* of `d:/git/codex-ppt-skill/tests/smoke-deck` (README + host-pinned RUN_PROMPT_*.md + verifier + runs/). Do **not** port generative-deck T1–T7 logic. Verifier is Minimal-A for reconstruction: manifests, `image_backend.tool_name` lock, final `.pptx` exists, and page counts match the fixture (page_jobs **and** final slides).

**Tech Stack:** Python 3 stdlib (+ existing editppt deps if already importable), unittest, Markdown prompts.

---

## SELF-CONTAINED HANDOFF NOTE

This plan is **SELF-CONTAINED**. The executor needs no prior chat session or memory file and must not ask the user to re-explain context. All decisions live here. Companion execute prompt: `docs/plans/2026-08-12-smoke-reconstruction-PROMPT-execute.md`.

**Reference for prompt *shape* only (do not copy generative checks):**  
`d:/git/codex-ppt-skill/tests/smoke-deck/RUN_PROMPT_cursor.md` and siblings.

---

## Section 0: Full Context

### 0.1 Why

The fork just gained host-aware image backend selection (`builtin-imagegen` + allowlisted `tool_name`). Operators need the same multi-host smoke workflow they use for `codex-ppt`: paste a prompt per IDE, run the skill, verify. The coffee PPTX used as input will be wiped from the codex-ppt runs tree soon — copy it into this repo first.

### 0.2 Confirmed decisions (do not re-litigate)

1. **Approach:** Mirror layout + thin native verifier (not prompts-only; not heavy `verify_deck.py` port).
2. **Folder name:** `tests/smoke-reconstruction/` (not `smoke-deck`).
3. **Fixture source (copy once):**  
   `D:/git/codex-ppt-skill/tests/smoke-deck/runs/20260810-1654-claude/coffee-extraction/coffee-extraction.pptx`  
   → `tests/smoke-reconstruction/fixtures/coffee-extraction.pptx`  
   (Known: **3 slides**, ~4.3 MB.)
4. **Six prompts:**
   - `RUN_PROMPT_cursor.md` — hard-pin `GenerateImage`
   - `RUN_PROMPT_cursor_codex-gpt-image.md` — hard-pin `codex-gpt-image`
   - `RUN_PROMPT_cursor_interactive.md` — probe → menu → wait → lock **and** pause for other user decisions (OCR token, failures, etc.)
   - `RUN_PROMPT_claude.md` — hard-pin `codex-gpt-image`; no invented Claude native tool
   - `RUN_PROMPT_codex.md` — hard-pin `image_gen.imagegen`
   - `RUN_PROMPT.md` — self-detect host; recommend prefer-order; still wait to lock
5. **Verifier Minimal-A BASELINE (exit code):**
   - `deck_manifest.json`, `page_jobs.json` exist
   - `image_backend.backend_id` + `tool_name` present
   - If `--expect-tool-name` given: exact match; else allowlisted specific tool OR documented CLI mode
   - Each `pages/page_*/page_request.json` copies the same `image_backend`
   - Final `.pptx` exists (`deck_manifest.output` or `final/*.pptx`)
   - **Page count:** `len(page_jobs.pages)` **and** slide count of final `.pptx` **==** slide count of fixture PPTX
   - Reject OpenClaw `image_generate` / invented Claude-native names
6. **Out of verifier v1:** per-page `validation.json.passed`, OCR/visual quality, TARGET progress tier.
7. **Prompt guardrails:** fork↔install sync; edits only in fork; no commit/push without explicit user OK; systematic debug + TDD for script bugs.
8. **Lock mapping (prepare flags):**

| Lock | Flags |
|------|-------|
| `GenerateImage` | `--image-backend builtin-imagegen --tool-name GenerateImage` |
| `image_gen.imagegen` | `--image-backend builtin-imagegen` |
| `codex-gpt-image` | `--image-backend builtin-imagegen --tool-name codex-gpt-image` |
| CLI | `--image-backend editppt-image-cli` |

9. **Rejected:** TARGET T-matrix port; requiring validation.passed in BASELINE; renaming folder to smoke-deck.

### 0.3 Audience & assumptions

- Executor works in `d:/git/image-to-editable-ppt-skill`.
- Prefer continuing on `feature/host-aware-image-backend-lean` if it already has the backend work; otherwise create `feature/smoke-reconstruction` from current branch tip.
- Host-aware backend code may already be staged/committed on the branch — smoke harness assumes that contract exists (`tool_name` allowlist). If missing, stop and tell the user (do not re-implement backend selection in this plan).
- Live multi-host E2E image generation is **not** required to finish this plan — unit-test the verifier with fake run dirs; prompts are authored for humans to paste later.

### 0.4 Project rules

- No commits unless user explicitly asks.
- Do not run collection install/uninstall scripts.
- Keep ASCII/path notes Windows-friendly (this team works on Windows).
- `runs/` outputs should be gitignored except `.gitkeep`.

### 0.5 Non-goals

- Running the full coffee reconstruction live in CI
- Porting codex-ppt speech/multilingual/T5 image-width checks
- Changing skill runtime beyond what smoke docs reference

---

### Task 0: Branch + confirm backend contract present

**Steps:**

```bash
cd d:/git/image-to-editable-ppt-skill
git status -sb
git branch --show-current
rg -n "GenerateImage|BUILTIN_TOOL_ALLOWLIST|probe_image_backends" skills/image-to-editable-ppt tests
```

Expected: allowlist / probe already exist from host-backend lean work. If not, **STOP** and report.

If not already on a feature branch, create `feature/smoke-reconstruction`.

---

### Task 1: Scaffold dirs + copy fixture

**Create:**
- `tests/smoke-reconstruction/fixtures/`
- `tests/smoke-reconstruction/runs/.gitkeep`
- Update root or local `.gitignore` so `tests/smoke-reconstruction/runs/**` is ignored except `.gitkeep`

**Copy (verify source first):**

```bash
SRC="D:/git/codex-ppt-skill/tests/smoke-deck/runs/20260810-1654-claude/coffee-extraction/coffee-extraction.pptx"
# If missing, STOP and ask the user for an alternate path (do not silently invent another deck).
test -f "$SRC" || { echo "MISSING fixture source: $SRC"; exit 1; }
mkdir -p tests/smoke-reconstruction/fixtures tests/smoke-reconstruction/runs
cp "$SRC" tests/smoke-reconstruction/fixtures/coffee-extraction.pptx
```

**Note:** The ~4.3 MB binary fixture is intentional so the input survives wipe of the codex-ppt runs tree; include it when the user later asks to commit.

**Verify:** file exists; slide count == 3 (use ZipFile count of `ppt/slides/slide*.xml`). Write one-line note to `docs/plans/evidence/2026-08-12-smoke-reconstruction-fixture.md`.

---

### Task 2: RED — verifier unit tests

**Create:** `tests/test_smoke_reconstruction_verify.py`

Add failing tests against `tests/smoke-reconstruction/verify_run.py` helpers (importable):

1. Fake run with matching page count + expected tool_name → pass
2. Wrong `--expect-tool-name` → fail
3. Final pptx slide count ≠ fixture → fail
4. `page_jobs` page count ≠ fixture → fail
5. Missing final pptx → fail
6. `tool_name=image_generate` → fail
7. CLI lock: `backend_id=editppt-image-cli` with `--expect-backend-id editppt-image-cli` → pass

Build tiny fake PPTX in tempfile with N slides via ZipFile minimal OOXML **or** copy fixture and claim wrong expected count for mismatch cases.

Run:

```bash
PYTHONPATH=skills/image-to-editable-ppt/cli python -m unittest tests.test_smoke_reconstruction_verify -v
```

Expect RED (module missing). Evidence: `docs/plans/evidence/2026-08-12-smoke-reconstruction-red.md`.

---

### Task 3: GREEN — `verify_run.py`

**Create:** `tests/smoke-reconstruction/verify_run.py`

**CLI:**

```text
python tests/smoke-reconstruction/verify_run.py <run_dir> --host {cursor,claude-code,codex}
  [--expect-tool-name NAME]
  [--expect-backend-id ID]   # use editppt-image-cli when user locked CLI (no host tool_name)
  [--fixture PATH]   # default: tests/smoke-reconstruction/fixtures/coffee-extraction.pptx
```

**Behavior:**
- Print `[PASS]` / `[FAIL]` lines; exit 0 only if all BASELINE checks pass
- Lock check: if `--expect-tool-name` set, `image_backend.tool_name` must match; elif `--expect-backend-id` set, `image_backend.backend_id` must match (for CLI locks); else allowlisted tool_name OR `backend_id=editppt-image-cli`
- Exactly one of expect-tool-name / expect-backend-id should be used on interactive/generic runs (prompts enforce this)
- `--host claude-code`: fail invented Claude-native tool names (anything outside allowlist / editppt-image-cli)
- Slide count helper: ZipFile `ppt/slides/slide*.xml` count (no hard Pillow dependency)
- Resolve final pptx from `deck_manifest["output"]` relative to run dir, else first `final/*.pptx`

Re-run Task 2 tests → GREEN. Add one unit case: CLI lock with `--expect-backend-id editppt-image-cli` passes.

Optional micro unit: `python tests/smoke-reconstruction/verify_run.py --help` exits 0.

---

### Task 4: README

**Create:** `tests/smoke-reconstruction/README.md`

Cover:
- Purpose (regression smoke for reconstruction + backend lock)
- Fixture source attribution (copied from codex-ppt run path; 3 pages)
- Quick start: pick a RUN_PROMPT_*, paste into host, then verify_run.py
- Table of the six prompts
- What verifier checks / does not check
- Output layout under `runs/`

---

### Task 5: Host-pinned prompts (hard-pin)

**Create** (each with intro + fenced paste block, modeled on codex-ppt):

1. `RUN_PROMPT_cursor.md` — Cursor, lock GenerateImage only  
2. `RUN_PROMPT_cursor_codex-gpt-image.md` — Cursor, lock codex-gpt-image only  
3. `RUN_PROMPT_claude.md` — Claude Code, lock codex-gpt-image; forbid native invention  
4. `RUN_PROMPT_codex.md` — Codex, lock image_gen.imagegen  

**Each fenced block MUST include:**
- Host pins table (environment, install path, locked tool, fork root, skill source)
- Fork sync command to the correct `~/.…/skills/image-to-editable-ppt`
- No commit/push without OK
- Input path: `tests/smoke-reconstruction/fixtures/coffee-extraction.pptx`
- Output under `tests/smoke-reconstruction/runs/<stamp>-<host>[-variant]/coffee-extraction/`
- Procedure: preflight sync → prepare with exact flags → dispatch/rebuild/record/finalize per SKILL → verify_run.py with `--expect-tool-name <pin>`
- Pass bar: verifier exit 0; wrong backend = failure

**Do not** require live generation to complete this task — authoring only.

---

### Task 6: Interactive + generic prompts

**Create:**
- `RUN_PROMPT_cursor_interactive.md` — must require probe (`scripts/probe_image_backends.py`) + prose host check + annotated menu + **wait for user lock** + pause for OCR token / other decisions before prepare; then use locked flags.
- `RUN_PROMPT.md` — self-detect Cursor/Claude/Codex; recommend prefer-order from Appendix A; still wait to lock; then same workflow.

**Hard requirement for interactive + generic:** After the user locks a label, the agent must **record that lock in the run summary** and pass it to verify:

- Host/bridge lock → `--expect-tool-name <GenerateImage|image_gen.imagegen|codex-gpt-image>`
- CLI lock → `--expect-backend-id editppt-image-cli` (do **not** invent a fake tool_name)

```bash
python tests/smoke-reconstruction/verify_run.py <run_dir> --host <host> --expect-tool-name <exact-locked-tool>
# or, for CLI:
python tests/smoke-reconstruction/verify_run.py <run_dir> --host <host> --expect-backend-id editppt-image-cli
```

Do not call verify with neither expect flag on interactive/generic runs (ambiguous pass). Hard-pin prompts always pass their pinned `--expect-tool-name`.
---

### Task 7: Gitignore + inventory sanity

- Ensure `tests/smoke-reconstruction/runs/*` ignored except `.gitkeep`
- If `tests/test_script_inventory.py` forbids unexpected paths, do **not** break it (smoke lives under `tests/`, not skill `scripts/`)
- Run:

```bash
PYTHONPATH=skills/image-to-editable-ppt/cli python -m unittest tests.test_smoke_reconstruction_verify tests.test_script_inventory -v
```

---

### Task 8: Verification summary evidence

Write `docs/plans/evidence/2026-08-12-smoke-reconstruction-green.md` listing:
- Fixture copied + 3-slide confirm
- Unit tests green
- Prompt file list present
- Note: live E2E deferred to human paste runs

**Do not commit** unless user asks.

---

## Verification Summary

- [ ] Fixture at `tests/smoke-reconstruction/fixtures/coffee-extraction.pptx` (3 slides)
- [ ] `verify_run.py` + unit tests green (lock, page-count both axes, missing final, OpenClaw reject)
- [ ] Six RUN_PROMPT_*.md + README
- [ ] `runs/.gitkeep` + runs ignored
- [ ] Prompts encode fork sync, pins, interactive A+B behavior, verify command
- [ ] No commit without explicit OK
- [ ] Did not port generative T-matrix / validation.passed requirement

---

## Appendix A — Host prefer order (for generic / interactive prompts)

| Host | Prefer first | Then | Else |
|------|--------------|------|------|
| Cursor | `GenerateImage` | `codex-gpt-image` | `editppt image` CLI/API |
| Codex | `image_gen.imagegen` | CLI/API | — |
| Claude Code | `codex-gpt-image` | CLI/API | (no native) |

## Appendix B — Example verify commands

```bash
# Hard-pin Cursor GenerateImage run
python tests/smoke-reconstruction/verify_run.py \
  tests/smoke-reconstruction/runs/20260812-1200-cursor-generateimage/coffee-extraction \
  --host cursor --expect-tool-name GenerateImage

# Interactive (user locked codex-gpt-image)
python tests/smoke-reconstruction/verify_run.py <run_dir> --host cursor --expect-tool-name codex-gpt-image
```

## Appendix C — Prompt skeleton (embed; adapt per host)

Each hard-pin prompt’s fenced block should start like:

```
You are running the image-to-editable-ppt smoke-reconstruction on <HOST> only,
with image backend HARD-PINNED to `<TOOL>`. Do not switch hosts. Do not commit
or push unless I explicitly say so.

## Host pins
| Item | Value |
|------|-------|
| Environment | <HOST> |
| Installed skill | ~/.…/skills/image-to-editable-ppt |
| Locked tool_name | <TOOL> |
| Fork repo | d:/git/image-to-editable-ppt-skill |
| Fixture | tests/smoke-reconstruction/fixtures/coffee-extraction.pptx |

## Rules
1. Sync fork skill → install path; verify match.
2. Edits only in the fork.
3. No commits without explicit OK.
4. On failure: systematic debugging; TDD for script bugs; re-sync; re-run.

## Procedure
A. Preflight sync
B. prepare with lock flags for <TOOL>
C. run next / dispatch / record / finalize per SKILL.md
D. verify_run.py --host … --expect-tool-name <TOOL>
E. Paste verifier output; stop when exit 0
```

Interactive variant replaces B with probe + menu + wait + other decision pauses.
