## MODIFIED Requirements

### Requirement: Harness mode documentation
id: harness-mode-docs
base: f85ddfb0d300

The `README.md` SHALL document harness mode inside its installation documentation: the interactive `shipd install` finish, animated wordmark, harness multi-select over the registry's fifteen harnesses, `~/.shipd/harnesses.json` selection record, user-global generation, closing read-only `shipd doctor` preflight, headless degradation, and re-run path. Its explicitly labeled harness-mode subsection SHALL cover repo-level `shipd harness add` and `remove`, ownership and overwrite safety, `--user`, skipped unsupported surfaces, the four-feature scaling model, `shipd-` command names, and registry inspection verbs. The CLI verb list SHALL include `harness`; the brand note and `docs/getting-started.md` harness guidance SHALL remain present.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the fifteen-harness multi-select, selection record, headless write-nothing degradation, and re-run path are described

#### Scenario: The closing preflight is documented
- **WHEN** a reader finishes the README's install finish paragraph
- **THEN** it states that a confirmed finish runs the read-only `shipd doctor` preflight and that headless and aborted paths do not

#### Scenario: Repo-level installation is documented
- **WHEN** a reader reaches the README's harness-mode subsection
- **THEN** `shipd harness add` and `remove` appear with ownership, idempotence, `--force`, and `--user` behavior

#### Scenario: Feature scaling is explained
- **WHEN** a reader reaches the feature-scaling explanation
- **THEN** all four declared features are named and generated files are described as omitting undeclared features

#### Scenario: CLI list gains the harness verb
- **WHEN** a reader reads the README's CLI verb list
- **THEN** it includes a `harness` row consistent with registry list and show behavior

#### Scenario: Brand note is stated
- **WHEN** a reader reaches the harness documentation's brand note
- **THEN** it confines the animated wordmark to installation and retains ☕ as the brand mark

#### Scenario: Getting started carries the mode
- **WHEN** a reader follows `docs/getting-started.md`'s install step
- **THEN** harness selection, headless degradation, and repo-level `shipd harness add` are named
