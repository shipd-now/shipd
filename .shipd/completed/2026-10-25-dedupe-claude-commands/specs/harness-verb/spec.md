## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Installation state report
id: harness-status
base: 6e06e167a7b0

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
