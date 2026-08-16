# ci-action

### Requirement: Composite lint action
id: composite-lint-action

The repository SHALL carry a root `action.yml` defining a composite GitHub
Action with a `path` input defaulting to `.`, whose steps — using the
runner's `python3` and no third-party action steps — run the engine's
`spec_lint.py` from the action's own checkout (`github.action_path`)
against the consumer directory named by `path`: first the master-library
lint (`--root <path>`), then one lint per change directory under the
consumer's resolved `planned/` directory. A lint finding SHALL fail the
action with a nonzero exit; a clean consumer repository SHALL pass. The
action SHALL perform no caching and no downloads.

#### Scenario: Manifest declares the composite contract
- **WHEN** `action.yml` is inspected
- **THEN** it declares `using: composite`, a `path` input defaulting to
  `.`, and steps invoking `spec_lint.py` via the action-path variable, with
  no `uses:` step and no cache step

#### Scenario: Encoded command passes a valid repo
- **WHEN** the manifest's lint command runs, variables substituted, against
  a fixture repository with a valid library and a valid planned change
- **THEN** it exits 0

#### Scenario: Encoded command fails an invalid change
- **WHEN** the same substituted commands run against a fixture whose
  planned change has a structural error
- **THEN** the run exits nonzero

### Requirement: Consumer CI documentation
id: ci-usage-docs

The repository `README.md` SHALL document the consumer workflow for the
lint action: a checkout step followed by `uses: shipd-now/shipd@<ref>`,
with a note preferring a pinned ref, and the runner requirement (python3
present).

#### Scenario: README carries the workflow snippet
- **WHEN** a reader reaches the README's CI section
- **THEN** a copyable workflow snippet shows checkout plus the `uses:` step
  and names the `path` input's default
