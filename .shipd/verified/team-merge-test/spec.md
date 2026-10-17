# team-merge-test

### Requirement: Driver is confined and stops on missing prerequisites
id: merge-proof-driver

The proof driver SHALL refuse any repository other than `mikkel-bergmann/unkannybanny`, SHALL take the reviewer identity only from the environment and never print it, and SHALL exit 3 naming each missing prerequisite when `preflight` finds one.

#### Scenario: Other repository refused
- **WHEN** the driver runs with `--repo mikkel-bergmann/shipd`
- **THEN** it exits 2 before any `gh` call

#### Scenario: Missing second account stops the run
- **WHEN** the reviewer variables are unset or the reviewer login is not a write collaborator
- **THEN** `preflight` prints `missing <name>` lines and exits 3

#### Scenario: Token never recorded
- **WHEN** any output or evidence line would contain the reviewer token value
- **THEN** the value is replaced by `[redacted]`

### Requirement: Run proves each rule from GitHub server facts
id: merge-proof-scenarios

The driver SHALL prove, on one throwaway pull request and from recorded GitHub responses, that one approval cannot merge, that a push dismisses approvals, that the author's approval is refused, that auto-merge lands with two non-author approvals on the latest head, and that doctor reports no drift.

#### Scenario: One approval blocks
- **WHEN** only the github-actions[bot] approval exists and checks are green
- **THEN** the merge call returns 405 and the evidence records `ok: true`

#### Scenario: Push dismisses
- **WHEN** the author pushes after both approvals
- **THEN** the reviewer's review reads DISMISSED and the merge call returns 405

#### Scenario: Auto-merge lands
- **WHEN** both non-author approvals cover the head sha, checks are green, and threads are resolved
- **THEN** the pull request reaches MERGED without a manual merge call

### Requirement: Proof is documented and recorded
id: merge-proof-docs

The change SHALL ship a how-to under `docs/` that passes `docs_lint.py` and a retro evidence record rendered from the driver's evidence file.

#### Scenario: Doc lints clean
- **WHEN** `docs_lint.py docs/team-merge-test.md` runs
- **THEN** it exits 0
