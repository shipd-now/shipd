## ADDED Requirements

### Requirement: Doctor wiki-store check
id: doctor-wiki-check

The `doctor` verb SHALL include a report-only `wiki` check, printed directly
after the `schema` check, naming the wiki store the working directory
resolves: when a workspace chain exists, the detail SHALL name the nearest
member's store path and whether it is present or absent; when no workspace is
discoverable but the resolved content directory exists, the detail SHALL name
the repo-local fallback store path, whether it is present or absent, and that
`wiki-init` scaffolds an absent one; when neither exists, the detail SHALL
state that no store is resolvable, naming the missing workspace and content
directory. The check SHALL always report `ok` — it informs which store
resolved and never gates the preflight — and SHALL mutate nothing.

#### Scenario: Bare repo reports the fallback store
- **WHEN** `shipd doctor` runs in a repo with a content directory and no
  workspace
- **THEN** the output carries an `ok wiki — …` line naming
  `<root>/<content-dir>/wiki` as the repo-local fallback store

#### Scenario: Workspace repo reports the chain store
- **WHEN** `shipd doctor` runs in a repo under a workspace
- **THEN** the `ok wiki — …` line names the nearest workspace member's store
  path

#### Scenario: The check never fails the preflight
- **WHEN** `shipd doctor` runs where no store is resolvable at all
- **THEN** the `wiki` line still reports `ok`, naming what is missing, and
  the check contributes nothing to the exit code
