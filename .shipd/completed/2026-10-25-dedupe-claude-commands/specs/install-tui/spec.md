## ADDED Requirements

### Requirement: Plugin-provided harness is reported, not generated
id: install-plugin-provided

Where a confirmed selection includes a harness whose user surface the
installed Claude Code plugin provides (requirement
`harness-plugin-provided`), the install SHALL write none of that harness's
command or agent files, SHALL retire its marker-owned ones, and SHALL
report it with a `provided` line naming the plugin instead of `installed`.

#### Scenario: Claude Code with the plugin installed is reported as provided
- **GIVEN** an isolated `HOME` whose Claude Code files show `s@shipd`
  installed at user scope and enabled, and one marker-owned file under
  `~/.claude/commands/shipd/`
- **WHEN** `install_selection(("claude-code",), out)` runs
- **THEN** it returns `None`, `out` carries a line with `provided`,
  `claude-code`, and `s@shipd`, and `~/.claude/commands/shipd/` and
  `~/.claude/agents/` hold no shipd file

#### Scenario: Claude Code without the plugin is still installed
- **WHEN** `install_selection(("claude-code",), out)` runs in an isolated
  `HOME` with no Claude Code plugin files
- **THEN** the command files exist under `~/.claude/commands/shipd/` and
  `out` reports `claude-code` as `installed`
