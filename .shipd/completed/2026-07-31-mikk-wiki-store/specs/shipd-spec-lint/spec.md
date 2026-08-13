## ADDED Requirements

### Requirement: Wiki lint mode
id: wiki-lint-mode

The linter SHALL provide a `--wiki` mode that validates the workspace wiki
store against the shipd-wiki grammar: layout file presence (`schema.md`,
`index.md`, `log.md`, `queue.md`), reserved page slugs, wikilink resolution
outside fenced code blocks, bidirectional index coverage, log header format,
and queue block fields. When no workspace is discoverable from the lint root,
the mode SHALL exit non-zero explaining that `--wiki` requires a workspace,
mirroring the `--workspace` mode's behavior. Findings and exit codes SHALL
follow the linter's existing gating contract.

#### Scenario: Clean store passes
- **WHEN** `spec_lint.py --wiki` runs against a store satisfying the grammar
- **THEN** it prints an OK line and exits zero

#### Scenario: Violations gate
- **WHEN** the store contains a dead wikilink and an unindexed page
- **THEN** the mode prints one finding per violation and exits non-zero

#### Scenario: No workspace
- **WHEN** `--wiki` runs where no workspace is discoverable
- **THEN** it exits non-zero naming the missing workspace
