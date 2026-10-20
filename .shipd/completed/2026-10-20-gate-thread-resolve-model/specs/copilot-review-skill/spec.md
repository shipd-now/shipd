## ADDED Requirements

### Requirement: Gate resolves its own superseded review threads
id: gate-resolves-superseded-threads

When the review-gate workflow's CLI reviewer path is about to submit an `APPROVE` or `REQUEST_CHANGES` review for a grounded head, the posting step SHALL first resolve every unresolved review thread on the pull request whose first comment was authored by the gate's own identity (`github-actions[bot]`, reported by GraphQL as "github-actions") on a commit other than the reviewed head. It SHALL do so through GraphQL (`reviewThreads` and `resolveReviewThread`) with the workflow token, in the posting step only. It SHALL NOT resolve a thread another author opened, a thread anchored on the reviewed head, or any thread when the review is a `COMMENT`, the review is ungrounded, or the run is on the poll or review-event path. If the thread query, the selection, or a resolve fails, then the step SHALL print a warning and SHALL leave the posted status, the review event, and its own exit code unchanged.

#### Scenario: A decision review resolves the gate's earlier threads
- **WHEN** the CLI path submits `REQUEST_CHANGES` or `APPROVE` and the pull request has an unresolved thread the gate opened on an earlier commit
- **THEN** that thread is resolved before the review is posted

#### Scenario: Other threads are left alone
- **WHEN** the CLI path submits a decision review and the pull request also has a thread by another author, an already resolved gate thread, and a gate thread on the reviewed head
- **THEN** none of those three is resolved

#### Scenario: A comment review resolves nothing
- **WHEN** the CLI path submits a `COMMENT` review, the review is ungrounded, or the run takes the poll path
- **THEN** no review-thread query or resolve is made

#### Scenario: A failed resolve only warns
- **WHEN** the thread query or a resolve fails
- **THEN** the run prints a warning, still posts its status and its review, and exits as it would have

### Requirement: Gate review model is configurable and named
id: gate-review-model

The review-gate workflow template SHALL read an optional repository variable `SHIPD_REVIEW_MODEL` through `${{ vars.SHIPD_REVIEW_MODEL }}` in the step `env:` of both the CLI step and the posting step. Where the variable is non-empty, the CLI step SHALL pass `--model` with its value to the Copilot CLI; where it is empty or unset, the CLI SHALL receive no `--model` flag. The posting step SHALL add a line to a grounded review body's footer, directly below the "Reviewed N files" stat line: "Model: " followed by the variable's value, or "Model: Copilot CLI default" when it is empty. The stat line itself SHALL stay identical to `review_gate.py`'s `review_footer`. A body whose diff could not be read, or an ungrounded review, SHALL carry no model line.

#### Scenario: A set variable selects and names the model
- **WHEN** `SHIPD_REVIEW_MODEL` is "gpt-5.4" and the CLI path posts a grounded review
- **THEN** the CLI is invoked with `--model gpt-5.4` and the posted body carries "Model: gpt-5.4" directly below the stat line

#### Scenario: An unset variable keeps the CLI default and says so
- **WHEN** `SHIPD_REVIEW_MODEL` is unset and the CLI path posts a grounded review
- **THEN** the CLI is invoked without `--model` and the posted body carries "Model: Copilot CLI default"

#### Scenario: Both steps bind the variable from vars
- **WHEN** the template's CLI step and posting step are read
- **THEN** each binds `SHIPD_REVIEW_MODEL: ${{ vars.SHIPD_REVIEW_MODEL }}` in its own `env:`
