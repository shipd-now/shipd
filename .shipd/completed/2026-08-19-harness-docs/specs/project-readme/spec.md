## ADDED Requirements

### Requirement: Harness mode documentation
id: harness-mode-docs

The `README.md` SHALL document the harness mode inside its installation
documentation: the interactive install finish (`shipd install`) — the
animated wordmark, the harness multi-select over the registry's twelve
harnesses, the selection record at `~/.shipd/harnesses.json`, user-global
command generation for harnesses declaring a user-global directory, the
headless degradation that prints a note and writes nothing, and re-running
`shipd install` to reopen the selection — and, in an explicitly labeled
harness-mode subsection, the repo-level `shipd harness add`/`remove` actions
(the ownership marker, idempotent refresh, refusal of unmarked files without
`--force`, `--user` for the user-global surfaces, and harnesses without a
surface reported as skipped), the feature-scaling model (the declared feature
vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks`; one shared body per command rendered per harness so a
generated file never mentions a feature its harness did not declare; the
`shipd-` command-id prefix), and `shipd harness` / `shipd harness show <id>`
as the inspection verbs. The README's CLI verb list SHALL include the
`harness` verb. The harness documentation SHALL carry the brand note: the
animated wordmark is confined to the install surface and ☕ remains the
brand mark. `docs/quickstart.md`'s install step SHALL mention the harness
selection step and its headless degradation, and the quickstart SHALL name
`shipd harness add` as the way to install the generated commands into a
repository.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the interactive `shipd install` finish is described with the
  harness multi-select, the `~/.shipd/harnesses.json` selection record, the
  headless write-nothing degradation, and re-running `shipd install` to
  reopen the selection

#### Scenario: Repo-level installation is documented
- **WHEN** a reader reaches the README's harness-mode subsection
- **THEN** `shipd harness add` and `remove` appear with the ownership
  marker, the idempotent re-run, `--force` for unmarked files, and `--user`
  for the user-global surfaces

#### Scenario: Feature scaling is explained
- **WHEN** a reader reaches the feature-scaling explanation
- **THEN** the four declared features are named and the text states that a
  generated file never mentions a feature its harness did not declare

#### Scenario: CLI list gains the harness verb
- **WHEN** a reader reads the README's CLI verb list
- **THEN** it includes a `harness` row consistent with the verb's registry
  list/show behavior

#### Scenario: Brand note is stated
- **WHEN** a reader reaches the harness documentation's brand note
- **THEN** it states the animated wordmark appears only on the install
  surface and that ☕ remains the brand mark

#### Scenario: Quickstart carries the mode
- **WHEN** a reader follows `docs/quickstart.md`'s install step
- **THEN** the harness selection step and its headless degradation are
  mentioned, and `shipd harness add` is named for repo-level installs
