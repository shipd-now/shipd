# harness-registry

### Requirement: Registry data
id: registry-data

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/harness_registry.py` declaring `FEATURES` —
exactly the vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks` — `AGENT_DIALECTS` — exactly the vocabulary `yaml` —
`AGENT_ROLES` — exactly `sub-agent`, `validator` — and `HARNESSES`,
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
(`sub-agent.md`, `validator.md`, `teacher.md`), each opening with a
`<!-- description: <one line> -->` marker followed by that role's
system-prompt prose, and carrying no harness-specific frontmatter. Each file's
prose SHALL be the plugin's existing agent prose for that role, re-homed
verbatim rather than rewritten. `AGENT_ROLES` SHALL equal
`("sub-agent", "validator", "teacher")`, so the generator renders a
`shipd-teacher` agent file for every harness that carries an `agent` member.

#### Scenario: One source file per role
- **WHEN** the test suite reads `plugins/s/harness/agents/`
- **THEN** it holds exactly one file per `AGENT_ROLES` member, each opening
  with a non-empty `<!-- description: ... -->` marker

#### Scenario: The source matches the plugin agent prose
- **WHEN** a role's source file and the plugin's `plugins/s/agents/<role>.md`
  are read
- **THEN** the source's body after the description marker equals the plugin
  agent's body after its frontmatter

#### Scenario: The teacher role is generated beside the others
- **WHEN** a harness declaring `subagents` is added for the user
- **THEN** its agent location receives `shipd-teacher` alongside
  `shipd-sub-agent` and `shipd-validator`

### Requirement: Agent surface documentation
id: agent-surface-docs

The documentation SHALL describe the harness agent surface.
`docs/harnesses.md` SHALL state in one sentence that a harness declaring
`subagents` receives agent files beside its commands, and SHALL link to the
reference from its `## Reference` section.
`docs/harness-agents-reference.md` SHALL be the nested reference of
`docs/harnesses.md`. It SHALL open with a link back to that main page. It
SHALL record, for each harness that declares `subagents`, its agent files'
repository and user-global locations and the frontmatter those files carry,
the `shipd-<role>` agent ids, and the steps to add a harness. It SHALL keep
how `shipd harness status` counts the agent files, and SHALL state the
plugin-provided skip in one sentence that links `harnesses.md`.

#### Scenario: The reference records each harness's agent surface
- **WHEN** `docs/harness-agents-reference.md` is read
- **THEN** it names `claude-code`, `opencode`, `agy`, and `oh-my-pi` with each
  one's agent repository and user-global location and frontmatter, and states
  the `shipd-sub-agent` and `shipd-validator` ids, and names no `shipd-oracle` agent

#### Scenario: The main page points at the reference
- **WHEN** `docs/harnesses.md` is read
- **THEN** it states that a harness declaring `subagents` receives agent
  files beside its commands, and links to `harness-agents-reference.md`

#### Scenario: The reference links back to its main page
- **WHEN** the opening paragraph of `docs/harness-agents-reference.md` is read
- **THEN** it holds a resolving link to `harnesses.md` and no link that names
  `customise.md` as the owner of the registry

#### Scenario: The reference passes the lint
- **WHEN** `docs_lint.py` runs over `docs/harness-agents-reference.md`
- **THEN** it exits 0 with the file marked `reference`

### Requirement: Plugin-provided surfaces
id: registry-plugin-provided

The registry module SHALL declare a data map `PLUGIN_PROVIDED` from a
harness id to the Claude Code plugin id that already provides that
harness's user-global surface, holding exactly `{"claude-code": "s@shipd"}`.
Every key SHALL be a registry id.

#### Scenario: Claude Code is provided by the shipd plugin
- **WHEN** the test suite reads `harness_registry.PLUGIN_PROVIDED`
- **THEN** it equals `{"claude-code": "s@shipd"}` and every key is in `ids()`

### Requirement: Harnesses user documentation
id: harness-user-docs

The repository SHALL provide `docs/harnesses.md`, titled "Harnesses", as the
main page for the `shipd harness` verb family. The page SHALL conform to the
shipd documentation standard with `<!-- doc-type: how-to -->` as its first
line and a total line count within the how-to cap.

The page SHALL follow the main-page shape: opening paragraphs saying what a
harness is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL state:

- that a harness is a coding agent surface, and that the harness registry
  lets each registered harness drive the same `shipd` CLI from its own
  command palette;
- that one shared body per command is rendered per harness against the
  features its registry entry declares (`subagents`, `question-dialogs`,
  `file-references`, `background-tasks`), so a generated file never mentions
  a feature its harness lacks;
- that placement, file naming, and the frontmatter dialect follow each
  harness's own convention;
- the run as numbered steps: list the registry with `shipd harness`, inspect
  one entry with `shipd harness show <id>`, generate the commands with
  `shipd harness add <id>...`, and check them with `shipd harness status`;
- that every generated file carries the ownership marker, that re-running
  `add` is idempotent and serves as the upgrade path, that `add` refuses a
  target file without the marker unless `--force` is passed, and that
  `remove` deletes only marker-carrying files;
- that a harness with no surface for the selected mode is reported as
  skipped and does not fail the run;
- that `shipd harness add aider` writes one `shipd-conventions.md` file,
  wired in through `read: shipd-conventions.md` in `.aider.conf.yml`;
- that with the `s@shipd` plugin installed at user scope and enabled,
  `shipd install` and `shipd harness add claude-code --user` write no Claude
  Code command or agent files and retire the copies shipd wrote earlier;
- in one sentence, that `shipd install` runs the user-global half for the
  harnesses a person picks.

The `## Reference` section SHALL hold a table of the five verbs `list`,
`show`, `add`, `remove`, and `status`, a table of the flags `--all`,
`--root`, `--user`, `--force`, and `--json`, and a link to
`harness-agents-reference.md` for the agent files. The page SHALL link
`customise.md`, SHALL carry no mermaid fence, and SHALL carry no table of
every registered harness. Every command on the page SHALL be a `shipd` verb
or a `/s:` skill.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/harnesses.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the feature scaling and the safety rules
- **WHEN** `docs/harnesses.md` is inspected
- **THEN** it names the four features, the ownership marker, the idempotent
  `add`, the `--force` refusal, and the marker-only `remove`

#### Scenario: Reference tables match the CLI
- **WHEN** the verbs and flags in the `## Reference` tables are compared with
  the output of `shipd harness --help`
- **THEN** every verb and flag in the tables appears in that output

#### Scenario: Page nests the agents reference
- **WHEN** the `## Reference` section is read
- **THEN** it holds a resolving link to `harness-agents-reference.md`, and
  the page states no agent file location and no agent frontmatter

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/harnesses.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  the file holds no mermaid fence, and every relative link resolves
