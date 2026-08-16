## MODIFIED Requirements

### Requirement: Remedy safety boundaries
id: doctor-remedy-boundaries
base: 5de9ef63d5a8

The skill's remedy table SHALL be: a `textual` warning →
`python3 -m pip install "textual>=8.2.8,<9"` (the range mirrored from
`requirements.txt`); a `pydantic` finding — the `warn` and the escalated
`fail` alike → `python3 -m pip install "pydantic>=2.12,<3"` (the range
likewise mirrored from `requirements.txt`); a stale `snapshot` warning →
`claude plugin update s@shipd` with the restart-to-apply note; a
`statusline` warning → `shipd statusline install` (the binary resolved
exactly as the preflight resolved it); a missing `gh` or `git` → the
platform-appropriate install command, stated before it runs. An unauthenticated `gh` SHALL be handed to the user as
`! gh auth login` and never run by the skill; a failing `python` version
check and a failing `config` check SHALL be report-only — the skill SHALL
never install an interpreter and never edit a `.shipd-config.json`. A
failing `pipeline` check SHALL likewise be report-only — the skill SHALL
never edit a `.shipd-config.json` to repair a declared pipeline — with the
pydantic row's remedy standing as the fix when the pipeline failure's
detail names missing pydantic. The skill SHALL recognize `pipeline` among
the parsed check names. The `shipd doctor` CLI verb itself SHALL remain
unmodified by this capability.

#### Scenario: Interactive auth is handed off
- **WHEN** the findings include an unauthenticated `gh`
- **THEN** the skill instructs the user to run `! gh auth login` and does
  not execute it

#### Scenario: Config failures are never auto-edited
- **WHEN** the findings include a `config` failure naming a malformed file
- **THEN** the skill reports the file and error with no edit performed and
  proposes no remedy command for it

#### Scenario: Pydantic remedy runs only on consent
- **WHEN** the findings include a `warn pydantic` or escalated
  `fail pydantic` line and the user consents to its remedy
- **THEN** the skill runs `python3 -m pip install "pydantic>=2.12,<3"`, then
  re-runs the preflight and reports the before/after states

#### Scenario: Statusline remedy runs only on consent
- **WHEN** the findings include a `warn statusline` line and the user
  consents to its remedy
- **THEN** the skill runs `shipd statusline install`, then re-runs the
  preflight and reports the before/after states

#### Scenario: Malformed pipeline is report-only
- **WHEN** the findings include a `fail pipeline` line whose detail names
  malformed entries or an unknown preset
- **THEN** the skill reports the resolver's error with no edit performed
  and proposes no remedy command for it

#### Scenario: Pydantic-caused pipeline failure routes to the pydantic remedy
- **WHEN** the findings include a `fail pipeline` line whose detail names
  missing pydantic alongside a `fail pydantic` line
- **THEN** the only remedy offered for the pair is the pydantic install
  command, and no config edit is proposed
