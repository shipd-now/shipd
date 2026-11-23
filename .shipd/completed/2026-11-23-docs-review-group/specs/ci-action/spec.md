## MODIFIED Requirements

### Requirement: Consumer CI documentation
id: ci-usage-docs
base: 32f7039de88e
Dropped: README carries the workflow snippet

`docs/copilot-review.md` SHALL document the consumer workflow for the lint
action, as the last step of its `## How to run it` section under the heading
`### 7. Lint your specs in CI`: what the action lints (the master library,
then every in-flight change under the resolved `planned/` directory, a
finding failing the step), a copyable workflow snippet with a checkout step
followed by `uses: shipd-now/shipd@<ref>`, a note preferring a pinned ref,
and one sentence naming the `path` input's default with a link to the
reference.

`docs/copilot-review-reference.md` SHALL hold a `## The spec lint action`
section covering the `path` input (default `.`, a subdirectory example, the
content directory resolved from `.shipd-config.json`) and the runner
requirement (`python3` on the PATH, nothing installed or downloaded).

This requirement SHALL place no rule on `README.md`.

#### Scenario: Main page carries the workflow snippet
- **WHEN** a reader reaches `### 7. Lint your specs in CI` in
  `docs/copilot-review.md`
- **THEN** a copyable workflow snippet shows checkout plus the `uses:` step,
  the prose prefers a pinned ref, and one sentence names the `path` input's
  default

#### Scenario: Reference carries the input and the runner requirement
- **WHEN** `## The spec lint action` in `docs/copilot-review-reference.md`
  is read
- **THEN** it names the `path` input with its default and the `python3`
  runner requirement
