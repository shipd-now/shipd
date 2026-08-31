## MODIFIED Requirements

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs
base: 717918f5d687

The root `README.md`'s autonomous-pipeline overview SHALL mention that
entries may carry typed per-stage options validated strictly (unknown keys
and wrong types rejected) by the engine's stdlib-only schema module,
requiring no third-party package, linking the format authority for the full grammar. `docs/quickstart.md`
SHALL list the `shipd doctor` checks as shipped and SHALL carry a
one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset.

#### Scenario: Root README names the options layer
- **WHEN** a reader finishes the README's autonomous-pipeline paragraph
- **THEN** it names typed per-stage options and strict validation and
  points at the format authority for the grammar

#### Scenario: Quickstart doctor list matches the shipped checks
- **WHEN** a reader compares quickstart's doctor check list against a
  `shipd doctor` run
- **THEN** every check the verb reports — `python`, `git`, `config`, `gh`,
  `textual`, `snapshot` — appears in the list

#### Scenario: Quickstart mentions the eco opt-in
- **WHEN** a reader searches quickstart for the cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in
