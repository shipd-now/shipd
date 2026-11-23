## MODIFIED Requirements

### Requirement: Fix skill registration
id: fix-skill-registration
base: 26725fe22574

The plugin SHALL register `/s:fix` like its sibling commands:
`plugins/s/harness/bodies/fix.md` SHALL exist as the distilled command body,
opening with a `<!-- description: -->` marker, so the harness bodies and
skills id sets stay equal; `docs/cheatsheet.md`'s command table and the `AGENTS.md`
skill enumeration SHALL list `/s:fix`; and
`plugins/s/.claude-plugin/plugin.json` SHALL declare version `0.6.148` or later so the
plugin cache snapshot refreshes.

#### Scenario: Body and skill ids stay equal
- **WHEN** the harness test suites under `plugins/s/skills/build/tests/` run
- **THEN** the bodies/skills id-set equality test passes with `fix` present
  in both sets

#### Scenario: The listings name the skill
- **WHEN** `docs/cheatsheet.md` and `AGENTS.md` are read
- **THEN** each lists `/s:fix` among the plugin's commands

#### Scenario: The snapshot version advances
- **WHEN** `plugins/s/.claude-plugin/plugin.json` is read
- **THEN** its `version` is `0.6.148` or later
