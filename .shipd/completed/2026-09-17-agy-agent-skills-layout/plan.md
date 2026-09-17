# agy-agent-skills-layout
Status: verified

## Idea

Correct AGY harness generation to emit discoverable Agent Skills packages and remove shipd-owned files from the broken `0.6.224` layout.

### Motivation

Version `0.6.224` writes flat markdown files under `~/.gemini/antigravity-cli/skills/`, but AGY discovers directory packages containing `SKILL.md` under its customization roots. The installed commands therefore do not appear in AGY.

### Details

- Correct AGY's workspace and global registry paths to nested Agent Skills packages.
- Extend generic user-path resolution to support a `{command}` placeholder in `user_dir`.
- Remove marker-owned files from AGY's obsolete `0.6.224` global path during add and remove operations.
- Add focused path, generation, migration, and safety tests; advance the plugin version.

Affected capabilities: `harness-registry` and `harness-verb` (modified). Impact: `plugins/s/skills/build/scripts/harness_registry.py`, `plugins/s/skills/build/scripts/harness_generate.py`, their focused tests, and `plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No change to the separate `antigravity` IDE adapter.
- No change to command bodies, AGY feature declarations, or the four-feature vocabulary.
- No deletion of unmarked files in the obsolete directory.
- No AGY plugin bundle; shipd continues to use native Agent Skills.

## Implementation

- Set AGY's `repo_pattern` to `.agents/skills/shipd-{command}/SKILL.md` and `user_dir` to `~/.gemini/config/skills/shipd-{command}/`. AGY's installed built-in customization guide defines `skills/<skill_name>/SKILL.md`, workspace roots under `.agents/`, and the global root at `~/.gemini/config/`.
- Teach `user_path()` to format `{command}` in `user_dir` before joining the filename derived from `repo_pattern`. Entries without a placeholder retain byte-for-byte path behavior. Rejected: an AGY-only `user_path()` branch, because the registry should remain the source of path differences.
- Add a data-driven `LEGACY_USER_PATTERNS` registry mapping for AGY's broken `~/.gemini/antigravity-cli/skills/shipd-{command}.md` output. Generation and removal resolve those patterns generically.
- After a successful user-mode `add`, delete only legacy files carrying shipd's ownership marker. `remove agy --user` also deletes marker-owned legacy files. Leave foreign legacy files untouched without blocking correct-path add or removal.
- Keep status based on the corrected expected surface. Legacy files alone do not make AGY appear installed.
- Pin the corrected AGY fields in `test_harness_registry.py`. In `test_harness_generate.py`, cover nested repo/global output, unchanged paths for another harness, migration cleanup, foreign legacy-file preservation, and removal cleanup.
- Advance the plugin version from `0.6.224` to `0.6.225`.

Risk: generic placeholder support could alter existing user paths. Tests pin an existing harness path and the full generation suite guards every registry entry.
