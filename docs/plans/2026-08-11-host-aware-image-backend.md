# Host-Aware Image Backend Selection — Lean Implementation Plan

> **For the implementing agent:** Follow this plan task-by-task. Complete each step, verify it works, then move to the next.

**Goal:** Let the user **pick and lock** a specific image backend for an `image-to-editable-ppt` run on Codex / Cursor / Claude Code — same success pattern as the `codex-ppt` fork — without renovating the skill.

**Architecture:** Docs-first menu + lock (mirror `codex-ppt` `docs/backend-selection.md`). Thin probe for bridges/CLI. Minimal CLI change: keep existing `backend_id` values (`builtin-imagegen`, `editppt-image-cli`, `openai-compatible-api`) and allow a **specific** `tool_name` on the preferred path (`image_gen.imagegen` | `GenerateImage` | `codex-gpt-image`). Workers execute the locked `tool_name`. CLI/API fallback unchanged.

**Tech Stack:** Python `editppt` CLI, unittest, skill docs under `skills/image-to-editable-ppt/`.

**Supersedes:** the earlier heavier draft of this same filename that renamed `builtin-imagegen` → `host-image-tool` and mandated a full en/zh/ko site rewrite. That scope is **rejected** for v1.

---

## SELF-CONTAINED HANDOFF NOTE

This plan is **SELF-CONTAINED**. The executor needs no prior chat session or memory file and must not ask the user to re-explain context. All decisions live here. Companion execute prompt: `docs/plans/2026-08-11-host-aware-image-backend-PROMPT-execute.md`.

**Reference success story (read for shape, do not copy blindly):**  
`d:/git/codex-ppt-skill/skills/codex-ppt/docs/backend-selection.md` and `scripts/probe_image_backends.py`.

---

## Section 0: Full Context

### 0.1 Why

Today’s parent policy is Codex-shaped only: “if `image_gen.imagegen` callable → `--image-backend builtin-imagegen`.” Cursor `GenerateImage` and `codex-gpt-image` are invisible. User wants a real **pick-a-backend** gate, not a skill rewrite.

`editppt` already locks `image_backend` at prepare and copies it into page requests. Reuse that. Do not invent a parallel system.

### 0.2 Confirmed decisions (do not re-litigate)

1. **User goal only:** probe → annotated menu → user locks one backend → run uses that lock.
2. **Learn from `codex-ppt`:** docs + thin probe + specific label lock + small validation — **not** a taxonomy renovation.
3. **Do NOT rename** `builtin-imagegen` → `host-image-tool` in v1. Keep on-disk `backend_id` values stable.
4. **Cursor preference:** `GenerateImage` → `codex-gpt-image` (if installed) → `editppt image` CLI/API.
5. **Codex preference:** `image_gen.imagegen` → CLI/API.
6. **Claude Code:** no native image tool; prefer `codex-gpt-image` if installed → CLI/API.
7. **CLI/API fallback already exists** (`editppt image` → Codex OAuth → OpenAI-compatible API) — keep it.
8. **GenerateImage edit-with-refs:** best-effort; on `fallback_policy.on` → CLI. Do not redesign edit pipeline.
9. **No OpenClaw / `image_generate`** as a preferred backend.
10. **No pre-finalize review gate, no OCR/i18n redesign.**
11. **Public docs:** small FAQ/install touch that Cursor/`GenerateImage`/`codex-gpt-image` exist — **defer** full README + all-language site rewrite unless a one-line inconsistency is trivial to fix in the same files you already edit.
12. **No commits** unless the user explicitly asks.
13. **Rejected for v1:** `host-image-tool` rename + legacy alias migration of the whole test suite; plugin registry; full en/zh/ko marketing rewrite as a required task.

### 0.3 How locking maps onto existing CLI (authoritative)

| User picks | `editppt prepare` / `run backend` | Stored contract (conceptual) |
|------------|-----------------------------------|------------------------------|
| Cursor `GenerateImage` | `--image-backend builtin-imagegen --tool-name GenerateImage` | `backend_id=builtin-imagegen`, `tool_name=tool_call=GenerateImage`, same fallback_policy as today |
| Codex `image_gen.imagegen` | `--image-backend builtin-imagegen` (default tool) or `--tool-name image_gen.imagegen` | `backend_id=builtin-imagegen`, `tool_name=image_gen.imagegen` (today’s behavior) |
| `codex-gpt-image` | `--image-backend builtin-imagegen --tool-name codex-gpt-image` | Same preferred-host contract bucket; **real** choice is `tool_name`; fallback_policy still → `editppt image` |
| CLI only | `--image-backend editppt-image-cli` | unchanged — do **not** fake CLI as `builtin-imagegen` |

**Note:** Keeping `backend_id=builtin-imagegen` for host/bridge picks is a **compat bucket** (avoids renaming). The user-visible lock is always the specific `tool_name`. Document that clearly in SKILL/schema so agents do not treat “builtin” as Codex-only.

**Important:** Today `configure_image_backend.py` **forbids** overriding `tool_name` for `builtin-imagegen`. That hard-lock is what must loosen — allow an allowlist override, defaulting to `image_gen.imagegen` when omitted.

**v1 choice (locked):** allowlist-on-`builtin-imagegen` only. Do **not** add a new `--mode codex-gpt-image` / new `backend_id` in this plan.

### 0.4 Project rules

- Repo: `d:/git/image-to-editable-ppt-skill`
- Honor `AGENTS.md` ownership: parent policy in `SKILL.md`; field contracts in `references/manifest-schema.md`; worker short reminder in `prompts/page-worker.md`; command examples in `references/cli-helper.md`.
- Prefer TDD for CLI/configure/import changes.
- Work on a feature branch; do not mix unrelated dirty README badge edits unless user says so.

### 0.5 Non-goals (explicit)

- Renaming backend ids
- Reworking page-decision-tree / finalize / OCR
- Making doctor detect IDE-native tools (impossible from CLI — same as `codex-ppt`)
- Live multi-host E2E image generation in CI

---

### Task 0: Branch + baseline

```bash
cd d:/git/image-to-editable-ppt-skill
git status -sb
git checkout -b feature/host-aware-image-backend-lean
PYTHONPATH=skills/image-to-editable-ppt/cli python -m unittest tests.test_multi_agent_backend -v
```

Write a one-line baseline note to `docs/plans/evidence/2026-08-12-host-backend-lean-baseline.md`.

---

### Task 1: RED — minimal contract tests

**Files:** `tests/test_multi_agent_backend.py` (add cases; do **not** mass-rewrite existing `builtin-imagegen` assertions)

Add failing tests:

1. `run backend --mode builtin-imagegen --tool-name GenerateImage` stores `tool_name=GenerateImage` (and `tool_call=GenerateImage`), keeps `backend_id=builtin-imagegen`, keeps fallback_policy shape.
2. `run backend --mode builtin-imagegen` with no tool-name still stores `image_gen.imagegen` (compat).
3. `run backend --mode builtin-imagegen --tool-name NotARealTool` fails.
4. `run backend --mode builtin-imagegen --tool-name codex-gpt-image` stores that tool_name (allowlist-only; no dedicated mode).
5. Import under `builtin-imagegen` + `tool_name=GenerateImage`: `--backend GenerateImage` succeeds; `--backend builtin-imagegen` fails (legacy alias only for Codex default tool); `--backend codex-oauth` without `--fallback-reason` fails; with reason succeeds.
6. Default/legacy: when contract tool is `image_gen.imagegen` (or omitted default), `--backend builtin-imagegen` still accepted as producer alias (keep old tests green).

Run tests → expect new ones RED. Evidence: `docs/plans/evidence/2026-08-12-host-backend-lean-red.md`.

---

### Task 2: GREEN — configure + prepare wiring (smallest change)

**Files:**
- `skills/image-to-editable-ppt/cli/editppt/runtime/configure_image_backend.py`
- `skills/image-to-editable-ppt/cli/editppt/runtime/main.py`

**Rules:**

1. For `backend_id=builtin-imagegen`:
   - Default `tool_name=tool_call=image_gen.imagegen` when `--tool-name` omitted (today).
   - Allow `--tool-name` in allowlist: `image_gen.imagegen`, `GenerateImage`, `codex-gpt-image`.
   - Reject anything else.
   - Keep fallback_command / fallback_order / fallback_policy identical to today.
   - Set `input_context_policy` host-neutral when tool is `GenerateImage` (inspect with host view/vision tool; do not hard-require Codex `view_image` string only). Codex default may keep existing wording.
2. **Critical:** `cmd_prepare` currently passes `tool_name=None` into `cmd_backend` — forward `prepare --tool-name` through.
3. Add `prepare --tool-name` optional flag.
4. **Do not** introduce `host-image-tool` as a `backend_id`.
5. **Do not** add a new `backend_id` / `--mode` for the bridge — allowlist-on-`builtin-imagegen` only.
6. If `--tool-name` is passed with `--mode editppt-image-cli` or `openai-compatible-api`, **reject** it (tool_name only applies to the preferred-host `builtin-imagegen` bucket).

Re-run Task 1 configure tests → GREEN.

---

### Task 3: GREEN — import provenance (minimal)

**Files:** `skills/image-to-editable-ppt/cli/editppt/runtime/record_imagegen_result.py`

1. Expand `--backend` choices to include specific producers: `GenerateImage`, `image_gen.imagegen`, `codex-gpt-image`, plus existing `builtin-imagegen|codex-oauth|openai-compatible-api|unknown`.
2. For preferred `builtin-imagegen`:
   - Actual producer **equal to contract `tool_name`** → OK without fallback-reason.
   - Legacy `--backend builtin-imagegen` → treat as alias of `image_gen.imagegen` **only** when contract `tool_name` is `image_gen.imagegen` (default). Do **not** accept it when contract tool is `GenerateImage` or `codex-gpt-image`.
   - CLI producers (`codex-oauth`, `openai-compatible-api`) still require `--fallback-reason` under preferred builtin contract (today’s rule).
3. Only rewrite error strings that would be wrong for the new labels; do not drive a large message refactor.

Re-run Task 1 import tests → GREEN. Keep existing suite green.

---

### Task 4: Thin probe script (copy spirit from `codex-ppt`)

**Create:** `skills/image-to-editable-ppt/scripts/probe_image_backends.py`  
**Test:** `tests/test_probe_image_backends.py` (small)

Behavior (JSON stdout), modeled on `codex-ppt`’s probe:

- Note: script does **not** detect IDE-native tools.
- Prefer hints table: cursor / codex / claude-code (same order as §0.2).
- Candidates: `codex-gpt-image` if `SKILL.md` exists under `~/.{cursor,claude,codex}/skills/codex-gpt-image`; CLI readiness hints without printing secrets.
- `--home` override for tests (ignore ambient machine homes when set).
- Force UTF-8 stdout on Windows (lesson from `codex-ppt` encoding crash).

---

### Task 5: Parent + schema + worker docs (docs-first, like `codex-ppt`)

**Modify:**
- `skills/image-to-editable-ppt/SKILL.md` — replace “Image Backend Selection” subsection with probe → menu → wait → lock → prepare flags. Include host preference table. Point at probe script. Explicitly: Claude has no native tool; no OpenClaw preferred backend.
- `skills/image-to-editable-ppt/references/manifest-schema.md` — document that `builtin-imagegen` may carry specific `tool_name` values from the allowlist; import may record those specific producers.
- `skills/image-to-editable-ppt/prompts/page-worker.md` — one hard-rule line: execute locked `image_backend.tool_name` first (not hard-coded `image_gen.imagegen` only); fallback per contract.
- `skills/image-to-editable-ppt/references/cli-helper.md` — examples for `--tool-name GenerateImage` / `codex-gpt-image`.

Optional: add `skills/image-to-editable-ppt/references/backend-selection.md` if `SKILL.md` would get too long — then SKILL keeps a short pointer (matches `codex-ppt` split). Prefer this if the SKILL subsection exceeds ~40 lines.

**Menu shape (require in docs), copied from success story:**

```text
Host: Cursor. Probe + prose check found:
  A) GenerateImage (native, recommended)
  B) codex-gpt-image (installed bridge)
  C) editppt image CLI/API
I recommend A. Which backend should we lock for this run?
```

Wait for the user **before prepare** (or run `editppt run backend` to correct if prepare already used the wrong tool). Map menu choices to §0.3 flags exactly. If the user picks CLI, use `--image-backend editppt-image-cli` (not builtin + a fake tool name).

---

### Task 6: Small public doc touch (not a full i18n renovation)

Update **only** the backend FAQ / install paragraphs that currently say the builtin is only `image_gen.imagegen` and omit Cursor:

- `docs/faq.md` + `docs/en/faq.md` + `docs/ko/faq.md` (AGENTS.md requires language sync **for files you change**)
- Same for `docs/installation.md` (+ en/ko) **if** you edit the Chinese one

Do **not** require rewriting all READMEs / workflow pages unless they contain a directly false “only image_gen.imagegen” claim in a sentence you already touch. YAGNI.

---

### Task 7: Prompt-builder string asserts

If tests assert worker prompts always contain `image_gen.imagegen`, update them to expect the **locked** `tool_name` from the page request.

---

### Task 8: Verify

```bash
cd d:/git/image-to-editable-ppt-skill
PYTHONPATH=skills/image-to-editable-ppt/cli python -m unittest discover -s tests -v
python skills/image-to-editable-ppt/scripts/probe_image_backends.py
```

Evidence: `docs/plans/evidence/2026-08-12-host-backend-lean-green.md`.

**Do not commit** unless user asks. Offer code review.

---

### Task 9: Loophole closure (light)

```bash
rg -n "if so, pass --image-backend builtin-imagegen|image_gen\.imagegen whenever it is callable|built-in \`image_gen\.imagegen\`|builtin image_gen\.imagegen" skills/image-to-editable-ppt
```

Also re-read the SKILL **Entry Contract** authorization bullet that names only `image_gen.imagegen` — widen wording to “locked host/bridge/CLI image backend” without removing the authorization intent.

Fix remaining parent instructions that skip the menu / assume Codex-only builtin. Leave historical examples that still show the Codex default path when clearly labeled as default.

---

## Verification Summary

- [ ] Feature branch used
- [ ] User-facing flow: probe + menu + lock specific backend (docs)
- [ ] `builtin-imagegen` + `--tool-name GenerateImage|image_gen.imagegen|codex-gpt-image` works; default unchanged
- [ ] `cmd_prepare` forwards `--tool-name`
- [ ] Import accepts specific producers; CLI still needs fallback-reason under preferred builtin
- [ ] Thin probe script + unit tests
- [ ] Worker uses locked `tool_name`
- [ ] No `host-image-tool` rename
- [ ] No full README/site renovation
- [ ] Existing `tests.test_multi_agent_backend` not mass-broken
- [ ] No commit without explicit user OK

---

## Appendix A — Preference table

| Host | Prefer first | Then | Else |
|------|----------------|------|------|
| Cursor | `GenerateImage` | `codex-gpt-image` if installed | `editppt image` CLI/API |
| Codex | `image_gen.imagegen` | `editppt image` CLI/API | — |
| Claude Code | `codex-gpt-image` if installed | `editppt image` CLI/API | (no native) |

---

## Appendix B — What we deliberately stole from `codex-ppt`

- Hybrid probe (prose host tools + script for bridges/CLI)
- Menu of **available** options only; recommend one; **wait**
- Specific labels only (no generic “built-in image tool”)
- Thin `probe_image_backends.py` with `--home` and UTF-8 stdout
- Prefer order table by host

## Appendix C — What we deliberately did **not** copy

- Smoke-deck / T6 progress targets (different product)
- `_backend_family` landmine surgery beyond what import/configure need
- Broad multi-goal fork (review gate, multilingual)

---

## Appendix D — Key file anchors

- `skills/image-to-editable-ppt/SKILL.md` § Image Backend Selection
- `cli/editppt/runtime/configure_image_backend.py` (today forbids tool_name override on builtin)
- `cli/editppt/runtime/main.py` `cmd_prepare` → `cmd_backend(... tool_name=None)` ← must fix
- `cli/editppt/runtime/record_imagegen_result.py`
- `references/manifest-schema.md` `image_backend` block
- `prompts/page-worker.md` image backend paragraph
- `tests/test_multi_agent_backend.py`
- Success reference: `d:/git/codex-ppt-skill/skills/codex-ppt/docs/backend-selection.md`
