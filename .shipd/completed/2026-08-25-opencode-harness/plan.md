# opencode-harness
Status: verified

## Idea

Add OpenCode as the thirteenth harness in the registry so `shipd harness add
opencode` and the `shipd install` multi-select generate shipd command files
for OpenCode.

### Motivation

The harness registry drives shipd's command-file generation for twelve
harnesses, but OpenCode — which supports the same project/user markdown
command model — is not among them, so OpenCode users cannot install the
shipd commands.

### Details

- Append an `opencode` entry to `HARNESSES` in
  `plugins/s/skills/build/scripts/harness_registry.py`: `repo_pattern`
  `.opencode/commands/shipd-{command}.md`, `user_dir`
  `~/.config/opencode/commands/`, dialect `yaml`, frontmatter
  `("description",)`, features `("subagents", "file-references")`.
- Update the `harness-registry` spec's twelve-entry counts and id
  enumeration; pin OpenCode's researched paths in a scenario.
- Update `README.md`'s "registry's twelve harnesses" wording and the
  `project-readme` spec to thirteen.
- Bump the plugin version.

Affected capabilities: `harness-registry` (modified), `project-readme`
(modified). Impact: `harness_registry.py`,
`tests/test_harness_registry.py`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No new dialect and no new feature-vocabulary entry — OpenCode reuses the
  existing `yaml` dialect and the declared feature set.
- No changes to `harness_generate.py`, `harness_bodies.py`, or the
  copilot/gate surfaces.
- No OpenCode agent files (`.opencode/agent/`) — command files only,
  matching every other harness.

## Implementation

- **Data-only addition.** The registry is designed so "a vendor that moves
  its command directory is a one-entry edit" (`harness_registry.py` module
  docstring); the generation engine reads paths, dialect, and features from
  the entry alone. Rejected: any OpenCode-specific generation branch — the
  `yaml` dialect already renders it.
- **Paths from the official docs**, verified 2026-08-25 against
  `opencode.ai/docs/commands`: project commands live at
  `.opencode/commands/<name>.md`, global commands at
  `~/.config/opencode/commands/`, and the filename becomes the `/name`
  command. Hence `repo_pattern` `.opencode/commands/shipd-{command}.md` and
  `user_dir` `~/.config/opencode/commands/`.
- **Frontmatter is `("description",)` only.** OpenCode's other fields
  (`agent`, `model`, `subtask`) override user configuration shipd should
  not set, and `FIXED_FRONTMATTER` in `harness_generate.py` carries no
  values for them, so declaring them would only render omissions. Rejected:
  declaring `agent` — there is no sensible fixed value.
- **Features are `subagents` + `file-references`.** The docs confirm
  `@file` references and agent/subtask subagent invocation; OpenCode has no
  question-dialog tool and no background-task surface, so those gates
  render their else branches. Same two-feature shape as `oh-my-pi`.
- **Entry appended after `oh-my-pi`.** The registry is insertion-ordered,
  not alphabetical; `ids()` order and the spec's id enumeration follow the
  entry order.
- **Counts stay spelled out.** The registry spec spells "twelve"; the
  deltas re-spell "thirteen" in the same style rather than switching to
  digits.
- **Runnable premise.** `plugins/s/bin/shipd harness` was run before
  planning: it printed the twelve entry lines and exited 0, so the
  data-driven list/show/add surfaces need no code change for a new entry.

Risk: OpenCode has moved its command directory before (historically
`.opencode/command/`, singular); the researched-paths scenario pins the
currently documented path so a future vendor move is a deliberate one-entry
edit with a spec update, not silent drift.
