# agy-cli-antigravity
Status: verified

## Idea

Add AGY CLI as a first-class shipd harness adapter alongside the existing Antigravity workflow adapter.

### Motivation

The harness registry can generate shipd commands for fourteen coding harnesses, but it has no entry for the `agy` CLI, so AGY CLI users cannot install shipd as workspace or global slash-command skills.

### Details

- Add an `agy` registry entry using AGY CLI's documented skill locations and frontmatter.
- Pin the adapter's researched paths and feature declarations in registry tests.
- Update the documented registry count and advance the plugin version.

Affected capabilities: `harness-registry` and `project-readme` (modified). Impact: `plugins/s/skills/build/scripts/harness_registry.py`, `plugins/s/skills/build/tests/test_harness_registry.py`, `README.md`, and `plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No replacement or migration of the existing `antigravity` adapter, which targets a separate workflow surface.
- No AGY-specific branch in generation, installation, or command bodies.
- No native AGY plugin bundle or custom agent definitions; this change generates slash-command skills through the existing harness engine.
- No `question-dialogs` declaration without a documented AGY native question-dialog tool.

## Implementation

- Add `agy` immediately after `antigravity` in `HARNESSES`, keeping the related products adjacent while preserving the registry's existing insertion-order contract. Use display name `Antigravity CLI` to distinguish it from the existing `Antigravity` entry.
- Use `repo_pattern` `.agents/skills/shipd-{command}.md` and `user_dir` `~/.gemini/antigravity-cli/skills/`. These are the current workspace and global skill paths documented at https://www.antigravity.google/docs/cli/plugins/; each markdown skill becomes a slash command named from its filename.
- Use the existing `yaml` dialect with frontmatter `("name", "description")`, matching AGY's documented skill example. Rejected: the old Antigravity workflow shape (`.agent/workflows/` with description-only metadata), because it does not represent AGY CLI's skill contract.
- Declare `("subagents", "file-references", "background-tasks")`, in the registry vocabulary's canonical order. AGY CLI documents asynchronous subagents and background tasks at https://www.antigravity.google/docs/cli/subagents/; generated skill instructions can read shipd's fallback references. Omit `question-dialogs` because no native question-dialog surface was established.
- Keep the change data-only: `harness_generate.py`, `harness_bodies.py`, and `install_tui.py` already iterate registry entries. Generic generation and install tests provide regression coverage; a focused registry test pins AGY's fields.
- Update the registry's spelled-out count from fourteen to fifteen in the `harness-registry` capability and `README.md`, and advance `plugins/s/.claude-plugin/plugin.json` from `0.6.223` to `0.6.224` because the change edits `plugins/s/`.

Runtime premises observed before planning: `agy --help`, `agy agent --help`, and `agy plugin --help` exited 0 and exposed the installed CLI's agent and plugin surfaces; `plugins/s/bin/shipd harness` exited 0 with fourteen entries and no `agy`, while `shipd harness show antigravity` reported the distinct repo-only `.agent/workflows/` adapter.

Risk: AGY CLI is evolving and may move its skill directories. The focused researched-path test makes a future vendor path change an explicit registry-and-spec update rather than silent generation into a stale location.
