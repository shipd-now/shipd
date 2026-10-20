## MODIFIED Requirements

### Requirement: Gate resolves its own superseded review threads
id: gate-resolves-superseded-threads
base: b096c4a39f01

When the review-gate workflow's CLI reviewer path has posted an `APPROVE` or `REQUEST_CHANGES` review for a grounded head, the workflow SHALL resolve every unresolved review thread on the pull request whose first comment was authored by the gate's own identity (`github-actions[bot]`, reported by GraphQL as "github-actions") on a commit other than the reviewed head, reading at most the first 100 threads. It SHALL do so through GraphQL (`reviewThreads` and `resolveReviewThread`) in a separate job, "resolve-threads", that needs the "gate" job and whose job-level permissions are "contents: write" and "pull-requests: write"; the "gate" job SHALL keep the workflow-level "contents: read", "statuses: write", and "pull-requests: write". The posting step SHALL signal that job through the "gate" job outputs "resolve_threads" and "head_sha" only after the decision review posted successfully, and the job SHALL run only on a "pull_request" event whose "gate" job succeeded with "resolve_threads" equal to "true" and "head_sha" equal to the event's head. The "resolve-threads" job SHALL bind no secret and check out nothing. It SHALL NOT resolve a thread another author opened, a thread anchored on the reviewed head, or any thread when the review is a `COMMENT`, the decision was refused and posted as a `COMMENT`, the review is ungrounded, or the run is on the poll or review-event path. If the thread query, the selection, or a resolve fails, then the job SHALL print a warning and exit 0, and the posted status and review SHALL be unchanged.

#### Scenario: A decision review resolves the gate's earlier threads
- **WHEN** the CLI path submits `REQUEST_CHANGES` or `APPROVE` and the pull request has an unresolved thread the gate opened on an earlier commit
- **THEN** that thread is resolved after the review is posted

#### Scenario: Other threads are left alone
- **WHEN** the CLI path submits a decision review and the pull request also has a thread by another author, an already resolved gate thread, and a gate thread on the reviewed head
- **THEN** none of those three is resolved

#### Scenario: A comment review resolves nothing
- **WHEN** the CLI path submits a `COMMENT` review, the review is ungrounded, or the run takes the poll path
- **THEN** no review-thread query or resolve is made

#### Scenario: A refused decision resolves nothing
- **WHEN** GitHub refuses the decision and the CLI path falls back to the body-only `COMMENT`
- **THEN** the "gate" job sets no "resolve_threads" output and no review-thread query is made

#### Scenario: A failed resolve only warns
- **WHEN** the thread query or a resolve fails
- **THEN** the run prints a warning, still posts its status and its review, and every job exits 0

#### Scenario: Only the resolve job holds contents write
- **WHEN** the template is read
- **THEN** the workflow-level permissions carry "contents: read", the "resolve-threads" job declares "needs: gate" and job-level "contents: write" and "pull-requests: write", its guard requires a "pull_request" event, "resolve_threads" equal to "true", and "head_sha" equal to the event's head, and it carries no "secrets." reference and no checkout
