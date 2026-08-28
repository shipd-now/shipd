## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: 0fad52498042

The plugin SHALL carry a review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` that posts a terminal
`semantic-review` commit status for every reviewed head, reads the verdict
from the review text's last non-empty line by exact equality, honours the
repository's `SHIPD_GATE_FAIL_OPEN` setting for a marker-less review, and
keeps the reviewer's credential and the repository credential in separate
steps so the reviewing agent holds no credential able to post a status,
comment, or push.

If the reviewer produced no output at all — the gate's own reviewer writing no
review body, or the poll reaching its bound with no review of the head — then
the workflow SHALL leave the `semantic-review` status `pending` and SHALL exit
non-zero, and its message SHALL name the reviewer step's log as where the cause
is reported. Nothing was judged, so no verdict is invented; the job's exit code
is what distinguishes a reviewer that broke from one that is merely slow.
Exiting zero on those paths reported a passing run over a review that never
happened and left the pull request blocked on a status that would never arrive.
`SHIPD_GATE_FAIL_OPEN` SHALL NOT be consulted on those paths: it governs a
review that ran and carried no verdict marker, which is a different condition
from one that never ran. Where instead the poll observes that the pull
request's head has moved on, the workflow SHALL exit zero, because that run is
not stalled — the newer push's run owns the gate.

Where the gate's own reviewer produced the review, the workflow SHALL publish
it as a pull-request review rather than as an issue comment, submitting the
event `COMMENT`, carrying the review body and one anchored inline comment per
finding whose severity is `high` or `medium` and whose path and line range the
workflow itself verifies against the diff it computed. A finding naming a path
or range outside that diff, and every finding whose severity is `low`, SHALL be
folded into the body as prose rather than anchored — an inline comment opens a
review thread, and a repository requiring conversation resolution would
otherwise let a `low` finding block a merge the rubric says it never blocks.
Where an anchored finding also carries a replacement, its inline comment SHALL
include that replacement as a committable `suggestion` block.

#### Scenario: A reviewer that produced nothing fails the job
- **WHEN** the gate's own reviewer writes no review body
- **THEN** the `semantic-review` status is left `pending`, the job exits
  non-zero, and its message names the reviewer step's log

#### Scenario: A poll that found no review fails the job
- **WHEN** the poll reaches its bound without finding a review of the head
- **THEN** the `semantic-review` status is left `pending` and the job exits
  non-zero

#### Scenario: A moved head is a handoff, not a failure
- **WHEN** the poll observes that the pull request's head has moved on
- **THEN** the job exits zero, posting nothing further

#### Scenario: The gate's own review is posted as a review
- **WHEN** the workflow's own reviewer produces a review body for a pull
  request
- **THEN** it is published through the pull-request reviews API with the event
  `COMMENT`, not as an issue comment

#### Scenario: A verified high or medium finding is anchored
- **WHEN** a `high` or `medium` finding's path and line range are present in
  the diff the workflow computed
- **THEN** it is posted as an inline comment on that range

#### Scenario: A low finding is never anchored
- **WHEN** a `low` finding's path and line range are present in that diff
- **THEN** no inline comment is posted for it and it is folded into the review
  body as prose

#### Scenario: An unverifiable finding is not anchored
- **WHEN** a finding names a path or line range absent from that diff
- **THEN** it is folded into the review body as prose and no inline comment is
  posted for it

#### Scenario: A confident replacement becomes committable
- **WHEN** an anchored finding carries a replacement
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: The credentials stay separated
- **WHEN** the template's steps are read
- **THEN** the reviewer step binds only the reviewer token and the posting
  step binds only the workflow token
