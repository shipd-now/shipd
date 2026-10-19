## ADDED Requirements

### Requirement: Review events from other reviewers never cancel the gate
id: gate-review-event-concurrency

The review-gate workflow template SHALL key its concurrency group on the pull request number, and SHALL append a suffix carrying the review id when the event is `pull_request_review` and the reviewer is not `copilot-pull-request-reviewer[bot]`. Runs for `pull_request` events and for Copilot's own review events SHALL share the unsuffixed group with `cancel-in-progress: true`, so a new push still supersedes a running review. A review by any other reviewer SHALL therefore never cancel a running review of the pull request.

#### Scenario: Another reviewer's review runs in its own group
- **WHEN** the template's concurrency group line is read
- **THEN** it appends `-review-` and the review id only for a `pull_request_review` event whose reviewer login is not `copilot-pull-request-reviewer[bot]`

#### Scenario: Pushes still supersede each other
- **WHEN** the template's concurrency block is read
- **THEN** the group is keyed on the pull request number and `cancel-in-progress` is `true`
