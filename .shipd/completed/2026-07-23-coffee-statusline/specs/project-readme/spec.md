## MODIFIED Requirements

### Requirement: README documents the spec engine and status pipeline
id: readme-documents-spec-engine
base: e02feb24d5ff

The `README.md` SHALL document the homegrown spec system: the `am/spec/`
layout (master library, in-flight changes, archive) and the full-ceremony
change artifacts; the five-status lifecycle (`draft`, `ready`, `active`,
`complete`, `verified`) with one-line stage meanings, its pipeline ownership,
and the guarded `set-status` transitions with `--force` override; the ☕
statusline (rendered line format, spec selection via `spec_status.py use`,
and its `.claude/settings.json` registration); and the build telemetry
(report table, `~/.shipd/config.json`, `builds.jsonl`). It SHALL link to
`am/spec/README.md` as the grammar authority rather than restating the
requirement/delta grammar.

#### Scenario: Lifecycle is explained
- **WHEN** a reader reaches the spec-engine documentation
- **THEN** the five statuses appear in pipeline order with a one-line meaning
  each, and guarded transitions with `--force` override are described

#### Scenario: Statusline is explained
- **WHEN** a reader reaches the statusline documentation
- **THEN** it shows the `☕ <name> · <status> · <done>/<total>` line format
  and how to select the current spec

#### Scenario: Grammar is linked, not restated
- **WHEN** the reader wants the requirement/delta grammar
- **THEN** the README points to `am/spec/README.md` instead of duplicating it
