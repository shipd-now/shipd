# harness-registry

### Requirement: Registry data
id: registry-data

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/harness_registry.py` declaring `FEATURES` —
exactly the vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks` — `AGENT_DIALECTS` — exactly the vocabulary `yaml` —
`AGENT_ROLES` — exactly `sub-agent`, `oracle`, `validator` — and `HARNESSES`,
fifteen harness entries (`claude-code`, `cursor`, `github-copilot`, `windsurf`,
`aider`, `codex`, `cline`, `roocode`, `continue`, `antigravity`, `agy`,
`devin`, `oh-my-pi`, `opencode`, `pi`) each carrying a unique kebab-case `id`,
display `name`, `repo_pattern`, `user_dir`, supported `dialect`, `frontmatter`
tuple, `features` tuple that is a subset of `FEATURES`, and an `agent` member.

An entry's `agent` member SHALL be `None`, or a dict carrying exactly
`repo_pattern`, `user_dir`, `dialect`, `frontmatter`, and `extra`. A non-`None`
`agent` member SHALL be present if and only if the entry declares `subagents`;
its `dialect` SHALL be a member of `AGENT_DIALECTS`; its non-`None`
`repo_pattern` SHALL contain an `{agent}` placeholder; its `frontmatter` SHALL
be an ordered tuple drawn from `("name", "description")` with no duplicates;
and its `extra` SHALL be a tuple of `(field, scalar)` string pairs emitted
verbatim after the frontmatter fields. The `claude-code`, `opencode`, `agy`,
and `oh-my-pi` entries SHALL carry the agent target their harness documents.

For every dialect other than `conventions-file`, a non-`None` `repo_pattern`
SHALL contain a `{command}` placeholder; a `conventions-file` pattern SHALL be a
literal path. A `user_dir` MAY contain `{command}` when each command requires
its own directory. The `aider` entry's pattern SHALL remain
`shipd-conventions.md`. The module SHALL expose `get(id)`, ordered `ids()`, and
`agent_surface(id)` accessors, the last returning the entry's `agent` member or
`None`.

The module SHALL declare data-driven legacy user patterns for generated
surfaces that moved. AGY's legacy pattern SHALL identify
`~/.gemini/antigravity-cli/skills/shipd-{command}.md`.

#### Scenario: Every entry is structurally valid
- **WHEN** the test suite iterates `HARNESSES`
- **THEN** every entry satisfies the registry's id, key, dialect, frontmatter,
  path-placeholder, feature-vocabulary, and agent-field invariants

#### Scenario: Known entries carry their researched paths
- **WHEN** `get` is called for `cursor`, `github-copilot`, and `codex`
- **THEN** cursor's repo pattern is `.cursor/commands/shipd-{command}.md`,
  GitHub Copilot's ends with `.prompt.md`, and Codex has no repo pattern and a
  user directory under `~/.codex/prompts`

#### Scenario: AGY CLI carries its researched skill surfaces
- **WHEN** `get("agy")` is read
- **THEN** its name is `Antigravity CLI`, its repo pattern is
  `.agents/skills/shipd-{command}/SKILL.md`, its user directory is
  `~/.gemini/config/skills/shipd-{command}/`, its dialect is `yaml` with
  frontmatter `("name", "description")`, and its features are exactly
  `subagents`, `file-references`, and `background-tasks`

#### Scenario: AGY CLI and Antigravity remain separate entries
- **WHEN** `ids()` is read
- **THEN** it contains both `antigravity` and `agy`, and their repo patterns
  differ

#### Scenario: OpenCode carries its researched paths
- **WHEN** `get("opencode")` is read
- **THEN** its repo pattern is `.opencode/commands/shipd-{command}.md`, its user
  directory is `~/.config/opencode/commands/`, its dialect is `yaml` with
  frontmatter `("description",)`, and its features are exactly `subagents` and
  `file-references`

#### Scenario: Pi carries its researched paths
- **WHEN** `get("pi")` is read
- **THEN** its repo pattern is `.pi/prompts/shipd-{command}.md`, its user
  directory is `~/.pi/agent/prompts/`, its dialect is `yaml` with frontmatter
  `("description", "argument-hint")`, and its only feature is
  `file-references`

#### Scenario: Pi and oh-my-pi are separate entries
- **WHEN** `ids()` is read
- **THEN** it contains both `oh-my-pi` and `pi`, with repo patterns
  `.omp/commands/shipd-{command}.md` and `.pi/prompts/shipd-{command}.md`
  respectively

#### Scenario: Claude Code declares the full feature set
- **WHEN** `get("claude-code")` is read
- **THEN** its features equal the complete `FEATURES` vocabulary, while aider
  declares none

#### Scenario: Unknown id returns None
- **WHEN** `get("no-such-harness")` is called
- **THEN** it returns `None` and `ids()` does not contain that id

#### Scenario: Every subagents harness carries an agent target
- **WHEN** the test suite iterates `HARNESSES`
- **THEN** an entry's `agent` member is non-`None` exactly when its `features`
  declare `subagents`, and every non-`None` member satisfies the agent-field
  invariants

#### Scenario: Known agent surfaces carry their researched paths
- **WHEN** `agent_surface` is called for `claude-code`, `opencode`, `agy`, and
  `oh-my-pi`
- **THEN** their agent repo patterns are `.claude/agents/shipd-{agent}.md`,
  `.opencode/agents/shipd-{agent}.md`, `.agents/agents/shipd-{agent}.md`, and
  `.omp/agents/shipd-{agent}.md`, their user directories are
  `~/.claude/agents/`, `~/.config/opencode/agents/`,
  `~/.gemini/config/agents/`, and `~/.omp/agent/agents/`, and their frontmatter
  and extra fields are the ones their harness documents

### Requirement: Harness read verbs
id: harness-read-verbs

The `shipd` binary SHALL provide a read-only `harness` verb whose bare and `list` forms print one line per registry entry, whose `show <id>` form prints every field of one entry, and whose `--json` form emits the corresponding machine-readable document. Unknown ids SHALL produce one `Error:` line and a nonzero exit. The read actions SHALL create or modify no files.

#### Scenario: List names every harness
- **WHEN** `shipd harness` runs
- **THEN** stdout contains all fifteen registry ids, including `agy`, and the exit code is 0

#### Scenario: Show prints one entry's data
- **WHEN** `shipd harness show cursor` runs
- **THEN** stdout contains `.cursor/commands/shipd-{command}.md` and the entry's dialect

#### Scenario: Show prints the AGY CLI entry
- **WHEN** `shipd harness show agy` runs
- **THEN** stdout contains `.agents/skills/shipd-{command}.md`, `~/.gemini/antigravity-cli/skills/`, and the entry's dialect and features

#### Scenario: JSON is machine-readable
- **WHEN** `shipd harness --json` runs
- **THEN** stdout parses as JSON with fifteen entries whose ids match `ids()`

#### Scenario: Unknown id is a single-line error
- **WHEN** `shipd harness show no-such-harness` runs
- **THEN** stderr carries a single line beginning `Error: ` and the exit code is nonzero

#### Scenario: The read actions write nothing
- **WHEN** `shipd harness`, `shipd harness show cursor`, and `shipd harness show agy` run in a temporary directory
- **THEN** the directory's contents are unchanged

### Requirement: Neutral agent source
id: registry-agent-source

The plugin SHALL ship a neutral agent-definition source under
`plugins/s/harness/agents/`, one file per `AGENT_ROLES` member
(`sub-agent.md`, `oracle.md`, `validator.md`), each opening with a
`<!-- description: <one line> -->` marker followed by that role's
system-prompt prose, and carrying no harness-specific frontmatter. Each file's
prose SHALL be the plugin's existing agent prose for that role, re-homed
verbatim rather than rewritten.

#### Scenario: One source file per role
- **WHEN** the test suite reads `plugins/s/harness/agents/`
- **THEN** it holds exactly one file per `AGENT_ROLES` member, each opening
  with a non-empty `<!-- description: ... -->` marker

#### Scenario: The source matches the plugin agent prose
- **WHEN** a role's source file and the plugin's `plugins/s/agents/<role>.md`
  are read
- **THEN** the source's body after the description marker equals the plugin
  agent's body after its frontmatter

### Requirement: Agent surface documentation
id: agent-surface-docs

The documentation SHALL describe the harness agent surface.
`docs/customise.md`'s harness section SHALL name the agent files a harness
receives beside its commands and link to the reference.
`docs/harness-agents-reference.md` SHALL record, for each harness that declares
`subagents`, its agent files' repository and user-global locations and the
frontmatter those files carry, the `shipd-<role>` agent ids, and the steps to
add a harness.

#### Scenario: The reference records each harness's agent surface
- **WHEN** `docs/harness-agents-reference.md` is read
- **THEN** it names `claude-code`, `opencode`, `agy`, and `oh-my-pi` with each
  one's agent repository and user-global location and frontmatter, and states
  the `shipd-sub-agent`, `shipd-oracle`, and `shipd-validator` ids

#### Scenario: Customise points at the reference
- **WHEN** `docs/customise.md`'s harness section is read
- **THEN** it names the agent files written beside the commands and links to
  `harness-agents-reference.md`
