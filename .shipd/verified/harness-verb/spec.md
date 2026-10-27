# harness-verb

### Requirement: Generation actions
id: harness-add-remove

The `shipd harness` verb SHALL provide `add` and `remove` actions taking one or
more harness ids or `--all`, a `--root DIR` selecting repo surfaces, and
`--user` selecting user-global surfaces. `add` SHALL write one generated file
per command into the registry-declared path, including command-specific
directories declared through `{command}` in `user_dir`, and SHALL render each
body with the harness's declared features.

For a harness declaring `file-references`, `add` SHALL write fallback references
under the mode's reference root. A `conventions-file` harness SHALL instead
write one conventions file and report its wiring step. Every generated file
SHALL carry the ownership marker. Foreign targets SHALL be refused unless
`--force`; unchanged reruns SHALL preserve bytes and modification times.

For a harness whose registry entry carries an `agent` member, `add` SHALL also
write one agent file per `AGENT_ROLES` member at the entry's agent repo or user
path, and `remove` SHALL delete those agent files with the command files. An
agent file SHALL carry the ownership marker and SHALL obey the same
foreign-target and `--force` rules as a command file; a harness whose `agent`
member is `None` SHALL gain no agent file. `shipd install` SHALL write the agent
files for every selected harness that carries an agent surface.

Where the registry declares legacy user patterns, successful user-mode `add` and
`remove` SHALL delete legacy files only when they carry shipd's ownership
marker. A foreign legacy file SHALL remain unchanged and SHALL NOT block writing
or removing the current surface. `remove` SHALL delete only eligible generated
files and directories it empties. Unsupported surfaces SHALL be skipped
successfully, and all actions SHALL remain offline.

#### Scenario: Add generates owned files for a repo-level harness
- **WHEN** `shipd harness add cursor --root <tmp>` runs in a temp repo
- **THEN** `.cursor/commands/` holds one owned `shipd-<command>.md` per body
  template, and an unchanged rerun changes no bytes

#### Scenario: AGY repo mode writes Agent Skills packages
- **WHEN** `shipd harness add agy --root <tmp>` runs
- **THEN** each command is written under `.agents/skills/shipd-<command>/SKILL.md`
  with `name` and `description` frontmatter

#### Scenario: File-references harnesses get reference files
- **WHEN** `shipd harness add cursor --root <tmp>` runs
- **THEN** fallback references exist under `<content-dir>/harness/references/`
  and generated bodies name that root

#### Scenario: User mode writes the user-global surface
- **WHEN** `shipd harness add codex --user` runs with an isolated `HOME`
- **THEN** generated files land under `~/.codex/prompts/` and nothing is written
  under the working directory

#### Scenario: AGY user mode writes Agent Skills packages
- **WHEN** `shipd harness add agy --user` runs with an isolated `HOME`
- **THEN** each command is written under `~/.gemini/config/skills/shipd-<command>/SKILL.md`

#### Scenario: AGY add migrates owned legacy files
- **GIVEN** marker-owned AGY files exist under `~/.gemini/antigravity-cli/skills/`
- **WHEN** `shipd harness add agy --user` runs
- **THEN** current Agent Skills packages are written and the marker-owned legacy
  files are deleted

#### Scenario: AGY migration preserves foreign legacy files
- **GIVEN** an unmarked file exists at an AGY legacy path
- **WHEN** `shipd harness add agy --user` runs
- **THEN** current Agent Skills packages are written and the foreign legacy file
  remains byte-identical

#### Scenario: Aider gets exactly one conventions file
- **WHEN** `shipd harness add aider --root <tmp>` runs
- **THEN** exactly one owned `shipd-conventions.md` is written and the report
  names the `.aider.conf.yml` wiring step

#### Scenario: A modeless harness is skipped, not failed
- **WHEN** `shipd harness add aider --user` runs with an isolated `HOME`
- **THEN** the action exits 0, reports aider as skipped, and writes no file

#### Scenario: Foreign files are refused without force
- **WHEN** a current target exists without the marker and `add` runs without
  `--force`
- **THEN** one `Error:` line names the target, the action exits nonzero, and the
  file remains unchanged

#### Scenario: Remove deletes only owned files
- **WHEN** `shipd harness remove cursor --root <tmp>` runs after add with an
  unmarked neighbor
- **THEN** generated files are gone, the unmarked neighbor remains, and emptied
  directories are pruned

#### Scenario: AGY remove cleans current and legacy owned files
- **GIVEN** current AGY packages and marker-owned legacy files exist in user mode
- **WHEN** `shipd harness remove agy --user` runs
- **THEN** both generated surfaces are removed while unmarked legacy files remain

#### Scenario: Add writes the agent files beside the commands
- **WHEN** `shipd harness add claude-code --user` runs with an isolated `HOME`
- **THEN** `~/.claude/agents/` holds one owned `shipd-<role>.md` per
  `AGENT_ROLES` member, each carrying the ownership marker, and
  `shipd harness add cursor --user` writes no agent file

#### Scenario: Remove deletes the agent files
- **WHEN** `shipd harness remove claude-code --user` runs after add
- **THEN** the agent files are gone along with the command files

#### Scenario: A foreign agent file is refused without force
- **GIVEN** an unmarked file sits at a harness's agent path
- **WHEN** `shipd harness add <harness> --user` runs without `--force`
- **THEN** one `Error:` line names the agent path, the action exits nonzero, and
  the file remains unchanged

### Requirement: Installation state report
id: harness-status

The `shipd harness` verb SHALL provide a read-only `status` action taking
optional harness ids (default: all), `--root DIR`, `--user`, and `--json`,
reporting per harness and surface one of `installed` (every expected file
present and byte-identical to a fresh render), `stale` (present but differing),
`foreign` (a target exists without the ownership marker), `absent`, or
`skipped` (no surface in this mode, or a plugin-provided surface per
requirement `harness-plugin-provided` with no owned file left). The
expected and present counts SHALL include the harness's agent files when its
entry carries an `agent` member, so a harness is `installed` only when its
command and agent files are both byte-current. Where a plugin-provided
surface still holds owned command or agent files, the state SHALL be `stale`
with a detail naming the plugin and `shipd harness add <id> --user` as the
step that retires them. The action SHALL create or modify no files.

#### Scenario: Status reflects the lifecycle
- **WHEN** `status` runs before an `add`, after it, and after one generated file
  is edited in place
- **THEN** the harness reports `absent`, then `installed`, then `stale`, and the
  temp root's contents are unchanged by every `status` run

#### Scenario: JSON status is machine-readable
- **WHEN** `shipd harness status --root <tmp> --json` runs
- **THEN** stdout parses as one JSON document keyed by harness id

#### Scenario: Status counts the agent files
- **WHEN** `status` runs for `claude-code` after `add` writes its agent files,
  then after one agent file is deleted
- **THEN** the harness reports `installed`, then `stale` naming the missing
  agent file

#### Scenario: Status reports a plugin-provided surface
- **GIVEN** an isolated `HOME` with `s@shipd` installed at user scope and
  enabled
- **WHEN** `shipd harness status claude-code --user --json` runs with owned
  claude-code files present, then again with none
- **THEN** it reports `stale` with a detail naming `s@shipd` and
  `shipd harness add claude-code --user`, then `skipped` with a detail
  naming `s@shipd`

### Requirement: Dialect rendering
id: dialect-rendering

The generation SHALL render each harness's files per its registry dialect:
`yaml` emits `---`-delimited frontmatter carrying exactly the entry's
declared `frontmatter` fields with the fixed value table (`name`/`id`/
`title`: `shipd-<command>`; `description`: the body template's declared
description; `category`/`tags`: `shipd`; `invokable`: `true`;
`argument-hint`: `[input]`; an undeclared-value field is omitted), values
escaped for YAML; `markdown-headers` emits a `# shipd-<command>` heading and
the description line instead of frontmatter. In both dialects the rendered
body follows, and the file extension comes from the surface pattern. The
`conventions-file` dialect SHALL render the single conventions file from
the `plugins/s/harness/bodies/_conventions.md` template, substituting
`{preamble}` with `_preamble.md`'s content and `{command_index}` with one
line per body-template command carrying its `shipd-<command>` name and
declared description, emitting the ownership marker first; the rendered
file SHALL carry no unresolved placeholder.

#### Scenario: YAML dialect carries the declared fields
- **WHEN** cursor's `shipd-plan` file is generated
- **THEN** its frontmatter contains exactly `name`, `id`, `category`, and
  `description` with `name: shipd-plan`, and the github-copilot variant of
  the same command carries only `description`

#### Scenario: Markdown-headers dialect carries no frontmatter
- **WHEN** cline's `shipd-plan` file is generated
- **THEN** it contains no `---` frontmatter block and begins with
  `# shipd-plan` followed by the description

#### Scenario: The conventions file indexes every command
- **WHEN** aider's conventions file is generated
- **THEN** it names `shipd-<command>` with its description for every
  body-template command, contains the preamble's engine-scripts snippet,
  and carries no `{preamble}` or `{command_index}` text

### Requirement: Agent rendering
id: agent-rendering

The generation SHALL render each harness's agent files from the neutral agent
source under `plugins/s/harness/agents/`, one file per `AGENT_ROLES` member, for
every harness whose registry entry carries an `agent` member. The rendered file
SHALL be the entry's agent dialect's frontmatter block, then the ownership
marker, then the source's body.

The frontmatter SHALL carry exactly the entry's declared agent `frontmatter`
fields, in order — `name` rendered as `shipd-<role>`, `description` as the
source's declared description — followed by each `extra` field emitted verbatim,
every value escaped for YAML. The render SHALL resolve the surface paths from
the entry's agent `repo_pattern` and `user_dir`, and `render_agent` and every
agent path helper SHALL resolve to `None` for a harness whose `agent` member is
`None`.

#### Scenario: The claude-code agent renders with its declared fields
- **WHEN** `claude-code`'s `sub-agent` agent is rendered
- **THEN** the file opens with a `---` block carrying `name: shipd-sub-agent`
  and the source's description, then the ownership marker, then the source body

#### Scenario: Extra fields render verbatim
- **WHEN** `opencode`'s `sub-agent` agent and `agy`'s `validator` agent are
  rendered
- **THEN** opencode's frontmatter carries `mode: subagent` and agy's carries
  `subagent: true`, each after the fields its entry declares

#### Scenario: The render pins the plugin agent prose
- **WHEN** the neutral source is rendered for `claude-code` and compared with
  `plugins/s/agents/<role>.md`
- **THEN** the rendered description and body equal the plugin agent's
  description and body, for every `AGENT_ROLES` member

#### Scenario: Agent surface paths come from the registry
- **WHEN** `claude-code`'s and `oh-my-pi`'s agent surfaces are resolved
- **THEN** their repo-relative paths are `.claude/agents/shipd-sub-agent.md` and
  `.omp/agents/shipd-sub-agent.md`, and their user paths sit under
  `~/.claude/agents/` and `~/.omp/agent/agents/`

#### Scenario: A harness with no agent surface renders nothing
- **WHEN** `cursor`'s agent surface is rendered and its paths resolved
- **THEN** each resolves to `None`

#### Scenario: A source file without a description marker is refused
- **WHEN** a role's source file lacks its opening `<!-- description: ... -->`
  marker
- **THEN** reading it raises a `ValueError` naming the file

### Requirement: Plugin-provided user surface is skipped and retired
id: harness-plugin-provided

The generator SHALL treat a harness's user-global surface as plugin-provided
when the mode is user mode, the harness id is a key of the registry's
`PLUGIN_PROVIDED`, and the named plugin is installed: the Claude Code file
`~/.claude/plugins/installed_plugins.json` lists the plugin id with an
entry whose `scope` is `user`, and `~/.claude/settings.json` sets
`enabledPlugins[<plugin id>]` to `true`. If either file is missing,
unreadable, or malformed, then the plugin SHALL count as not installed.

While a surface is plugin-provided, `add` SHALL write none of that
harness's command or agent files and none of the reference files on its
behalf, SHALL report `skipped <id> (provided by the <plugin id> plugin)`,
and SHALL delete each of its command and agent paths that carries the
ownership marker, reporting each as `retired`, then prune the directories
it empties. A file at those paths without the marker SHALL remain
unchanged and SHALL NOT block the action. Repo mode and every other
harness SHALL be unaffected.

#### Scenario: Add skips claude-code when the plugin is installed
- **GIVEN** an isolated `HOME` whose Claude Code files show `s@shipd`
  installed at user scope and enabled
- **WHEN** `shipd harness add claude-code --user` runs
- **THEN** it exits 0, stdout names `provided by the s@shipd plugin`, and
  no file exists under `~/.claude/commands/shipd/` or `~/.claude/agents/`

#### Scenario: Add retires owned duplicates and keeps foreign files
- **GIVEN** the plugin is installed as above, a prior add left owned files
  under `~/.claude/commands/shipd/` and `~/.claude/agents/`, and an
  unmarked `~/.claude/commands/shipd/plan.md` replaces the owned one
- **WHEN** `shipd harness add claude-code --user` runs
- **THEN** it exits 0, every owned file is gone and reported `retired`,
  `~/.claude/agents/` is pruned, and the unmarked `plan.md` is
  byte-identical

#### Scenario: A project-scope or disabled install does not count
- **GIVEN** `installed_plugins.json` lists `s@shipd` only at `project`
  scope, or `enabledPlugins["s@shipd"]` is `false`, or
  `installed_plugins.json` is not valid JSON
- **WHEN** `shipd harness add claude-code --user` runs
- **THEN** the command files are written under `~/.claude/commands/shipd/`

#### Scenario: Repo mode still writes with the plugin installed
- **GIVEN** the plugin is installed as above
- **WHEN** `shipd harness add claude-code --root <tmp>` runs
- **THEN** `<tmp>/.claude/commands/shipd/` holds one owned file per command
