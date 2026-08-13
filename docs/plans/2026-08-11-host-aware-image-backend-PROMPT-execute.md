# Execute prompt — host-aware image backend (lean)

Paste the fenced block below into a **fresh** agent session in `d:/git/image-to-editable-ppt-skill`.

---

```
Execute the implementation plan at `docs/plans/2026-08-11-host-aware-image-backend.md` in this repository (`d:/git/image-to-editable-ppt-skill`).

The plan is fully SELF-CONTAINED (lean v1, revised 2026-08-12). It carries every decision you need.
You do NOT need any prior chat session or memory file — start fresh and rely on the plan.

Please:
1. Read the entire plan first (especially Section 0 and the Non-goals).
2. Execute task-by-task (`executing-plans` if available). Verify after each task.
3. Satisfy the plan's Verification Summary.
4. Hard guardrails:
   - Goal is ONLY: user can pick/lock an image backend (probe → menu → lock).
   - Learn from codex-ppt backend-selection.md pattern; do NOT renovate the skill.
   - Do NOT rename builtin-imagegen → host-image-tool (or any backend_id rename).
   - Do NOT do a full en/zh/ko README/site rewrite (small FAQ/install touch only).
   - Do NOT claim Claude Code has a native image tool.
   - Do NOT add OpenClaw / image_generate as a preferred backend.
   - Do NOT implement review-gate or OCR/i18n work.
   - Keep editppt image CLI/API fallback.
   - Wire cmd_prepare to forward --tool-name (today hardcodes None).
   - Allowlisted tool_name on builtin-imagegen ONLY: image_gen.imagegen | GenerateImage | codex-gpt-image.
   - Do NOT add a new backend_id/mode for the bridge; builtin-imagegen is the compat bucket, tool_name is the real lock.
   - Import --backend builtin-imagegen aliases Codex default tool only — not GenerateImage/codex-gpt-image runs.
   - Cursor order: GenerateImage → codex-gpt-image → CLI/API.
   - Do NOT commit unless I explicitly ask.
   - Do not re-litigate Section 0.2.
5. When green, report results and offer a code review.

If genuinely blocked, ask via the question channel; otherwise proceed autonomously.
```
