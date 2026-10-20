## ADDED Requirements

### Requirement: Copilot report points stale files at update
id: copilot-report-update-hint

Where the bare `copilot` verb reports a managed gate file or a room wake file as `stale`, the line's detail SHALL name `shipd copilot update` as the refresh, and SHALL NOT name `shipd copilot add` or `shipd copilot add --room` as the refresh. The stale states themselves, the other states' details, and the report's closing lines SHALL stay unchanged.

#### Scenario: A stale gate file names update
- **WHEN** the bare report runs on a gate install whose workflow marker names `v0.0.1`
- **THEN** the workflow's line is `stale`, contains `0.0.1` and `shipd copilot update`, and contains no "copilot add` refreshes"

#### Scenario: A stale wake set names update
- **WHEN** the bare report runs on a wake set whose bundled `room.py` has drifted
- **THEN** each stale wake line names `shipd copilot update` and none contains `add --room`

#### Scenario: Copilot suite passes
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/build/tests -p test_copilot_verb.py` runs
- **THEN** it reports `OK`
