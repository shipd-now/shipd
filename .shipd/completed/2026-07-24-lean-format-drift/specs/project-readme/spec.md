# project-readme — delta

## MODIFIED Requirements

### Requirement: README displays the auto:mikk banner
id: readme-displays-the-auto-mikk-banner
base: 96300590a31e

The `README.md` at the repository root SHALL open with an ASCII-art header that
renders the project name **auto:mikk**. The banner SHALL be enclosed in a fenced
code block so it renders as monospaced preformatted text on GitHub and in
terminals.

#### Scenario: Banner is the first content
- **WHEN** a reader opens `README.md`
- **THEN** the first rendered block is the fenced ASCII-art header spelling
  `auto:mikk` (uppercase block styling permitted)

#### Scenario: Banner is preformatted
- **WHEN** the README is viewed on GitHub
- **THEN** the banner is inside a fenced code block and its columns stay aligned

### Requirement: README documents the spec engine and status pipeline
id: readme-documents-spec-engine
base: 97ce4b80b5ce

The `README.md` SHALL document the homegrown spec system: the `am/spec/`
layout (master library, in-flight changes, archive) and the lean change
artifacts (`plan.md`, `tasks.md`, delta specs); the five-status lifecycle
(`draft`, `ready`, `active`, `complete`, `verified`) with one-line stage
meanings, its pipeline ownership,
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
