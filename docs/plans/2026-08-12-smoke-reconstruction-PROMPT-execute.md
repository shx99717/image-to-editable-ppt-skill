# Execute prompt — smoke reconstruction harness

Paste the fenced block below into a **fresh** agent session in `d:/git/image-to-editable-ppt-skill`.

---

```
Execute the implementation plan at `docs/plans/2026-08-12-smoke-reconstruction.md` in this repository (`d:/git/image-to-editable-ppt-skill`).

The plan is fully SELF-CONTAINED (handoff mode). It carries every decision you need.
You do NOT need any prior chat session or memory file — start fresh and rely on the plan.

Please:
1. Read the entire plan first (especially Section 0 and Verification Summary).
2. Execute task-by-task (`executing-plans` if available). Verify after each task.
3. Satisfy the plan's Verification Summary.
4. Hard guardrails:
   - Goal is ONLY: smoke-reconstruction harness (fixture copy, verify_run.py, unit tests, README, 6 prompts).
   - Copy fixture from the exact codex-ppt path named in the plan (3-slide coffee PPTX).
   - Folder name: tests/smoke-reconstruction/ (not smoke-deck).
   - Verifier Minimal-A + page-count match (page_jobs AND final pptx vs fixture). Do NOT require validation.passed.
   - Do NOT port generative T1–T7 / verify_deck.py logic.
   - Cursor interactive = probe → menu → wait → lock AND pause for other user decisions.
   - Six prompts: cursor GenerateImage, cursor codex-gpt-image, cursor interactive, claude, codex, plus generic RUN_PROMPT.md.
   - Live multi-host E2E image generation is NOT required to finish — unit-test the verifier.
   - Do NOT commit unless I explicitly ask.
   - Do not re-litigate Section 0.2.
5. When green, report results and offer a code review.

If genuinely blocked, ask via the question channel; otherwise proceed autonomously.
```
