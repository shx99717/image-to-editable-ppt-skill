# Backend Selection

Read this before `editppt prepare` (or before `editppt run backend` if prepare already locked the wrong tool).

## Facts

- **Claude Code has no native image generation** (vision only). Do not invent a Claude Code native option.
- **Do not** present OpenClaw / `image_generate` as a preferred backend for this skill.
- Host-native tools that *do* exist: Codex `image_gen.imagegen`, Cursor `GenerateImage`.
- Bridge: `codex-gpt-image` (when installed under `~/.claude/skills`, `~/.cursor/skills`, or `~/.codex/skills`).
- CLI/API fallback: `editppt image` (Codex OAuth → OpenAI-compatible API). Already supported; keep it.

## Compat note

On-disk `backend_id` stays `builtin-imagegen` for host/bridge locks (compat bucket). The user-visible lock is always the specific `tool_name`. Do not treat “builtin” as Codex-only.

## Hybrid probe

1. **Prose-check host-native tools** in the current runtime (Codex `image_gen.imagegen`, Cursor `GenerateImage` only). The probe script cannot see IDE tools.
2. Run the probe for bridges/CLI signals:

```bash
python <skill-root>/scripts/probe_image_backends.py
```

3. Build the menu from:
   - prose-detected host-native tools (when actually callable), plus
   - probe `candidates` with `"available": true` only.
4. Do not list unavailable CLI/bridge entries as choosable defaults.

## Preference order by host

| Host | Prefer first | Then | Else |
|------|--------------|------|------|
| Cursor | `GenerateImage` (native) | `codex-gpt-image` if installed | `editppt image` CLI/API |
| Codex | `image_gen.imagegen` (native) | `editppt image` CLI/API | — |
| Claude Code | `codex-gpt-image` if installed | `editppt image` CLI/API | — (no native) |

## Menu requirements

Present only available options, annotate briefly, recommend one, and **wait** for the user to lock a **specific** label before prepare.

```text
Host: Cursor. Probe + prose check found:
  A) GenerateImage (native, recommended)
  B) codex-gpt-image (installed bridge)
  C) editppt image CLI/API
I recommend A. Which backend should we lock for this run?
```

## Lock mapping (exact flags)

| User picks | Prepare / backend flags |
|------------|-------------------------|
| Cursor `GenerateImage` | `--image-backend builtin-imagegen --tool-name GenerateImage` |
| Codex `image_gen.imagegen` | `--image-backend builtin-imagegen` (default tool) |
| `codex-gpt-image` | `--image-backend builtin-imagegen --tool-name codex-gpt-image` |
| CLI only | `--image-backend editppt-image-cli` (do **not** fake CLI as builtin) |

If prepare already used the wrong tool, correct with `editppt run backend <run> --mode builtin-imagegen --tool-name <locked>` (or `--mode editppt-image-cli`).

## Forbidden locks

- Generic “built-in image tool”
- OpenClaw / `image_generate`
- Invented Claude Code native names
- New `backend_id` values such as `host-image-tool`

## Workers

Page reconstructors execute the locked `page_request.json.image_backend.tool_name` first; CLI fallback only for a matching `fallback_policy.on` event. Import with `--backend` equal to that specific producer (`GenerateImage`, `image_gen.imagegen`, or `codex-gpt-image`). Legacy `--backend builtin-imagegen` is an alias of `image_gen.imagegen` only.
