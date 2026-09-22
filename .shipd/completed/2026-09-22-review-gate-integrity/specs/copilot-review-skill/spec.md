## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: 6de924624ca8

The plugin SHALL carry a review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` that posts a terminal
`semantic-review` commit status for every reviewed head, reads the verdict
by scanning the review text backwards for the last line equal to a verdict
marker, honours the repository's `SHIPD_GATE_FAIL_OPEN` setting for a
marker-less review, and keeps the reviewer's credential and the repository
credential in separate steps so the reviewing agent holds no credential able
to post a status, comment, or push.

The backwards scan SHALL compare whole lines for equality and SHALL examine
at most the last 200 lines, so a marker quoted mid-sentence or inside the
reviewer transcript's own tool-call log is never read as a verdict and a
maximal body cannot make the scan walk the whole text. Taking the last
non-empty line instead fell open whenever the Copilot CLI streamed its
session narration after the report: the gate then posted `success` carrying
a description saying no verdict was parsed, reporting a pass over a review
it had not read. One residual window remains and SHALL be documented in the
workflow: a bare marker standing alone on its own line inside trailing
narration is still read as the verdict.

Where the workflow installs difftastic for the review engine, it SHALL
request a pinned release version rather than the unversioned
`releases/latest/download/` asset name, and SHALL fail the step when the
download itself fails. Difftastic stopped publishing the unversioned asset
after 0.65.0, so the unpinned fetch 404s and kills the job before the
reviewer starts, leaving `semantic-review` pending forever on a repository
that requires it.

The reviewer's instructions SHALL be pinned by overwriting the reviewed
checkout's own `.github/skills/code-review/SKILL.md` with the base ref's
copy, so the Copilot CLI's skill discovery finds the pinned contract without
being asked to prefer it. Materializing that copy elsewhere and instructing
the reviewer to read it leaves the pinning advisory: the CLI discovers the
workspace copy on its own, so a change editing the review rules could still
be reviewed under the rules it is asking for. The reviewer step SHALL also
pass `--add-dir` for the directory holding the findings file it must write,
which `--allow-all-tools` alone does not bring inside its sandbox.

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
workflow itself verifies against the diff it computed. That diff SHALL cover
every file the pull request changed, the workflow paginating the changed-files
read rather than taking a single page of it: a short read is indistinguishable
downstream from a finding that named a path the pull request never touched, so
a truncated diff silently withholds the anchoring a finding was computed for
instead of reporting that it could not be placed. A finding naming a path
or range outside that diff, and every finding whose severity is `low`, SHALL be
folded into the body as prose rather than anchored — an inline comment opens a
review thread, and a repository requiring conversation resolution would
otherwise let a `low` finding block a merge the rubric says it never blocks.
Where an anchored finding also carries a replacement, its inline comment SHALL
include that replacement as a committable `suggestion` block.

#### Scenario: The changed-files read is paginated
- **WHEN** the posting step's changed-files read is inspected
- **THEN** it carries the option that fetches every page, so the diff map is
  not capped at a single page's worth of files

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

#### Scenario: Template carries the marker, triggers, permissions, and concurrency
- **WHEN** the installed workflow template is read
- **THEN** it carries the version marker comment, triggers on `pull_request`
  and `pull_request_review`, declares `contents: read`, `statuses: write` and
  `pull-requests: write`, and runs under a per-pull-request concurrency group
  that cancels a superseded run

#### Scenario: Reviewer instructions come from the base ref
- **WHEN** the CLI reviewer prepares its prompt
- **THEN** the reviewer skill is materialized from the base ref, a base that
  cannot be resolved fails the step, and the head's copy is used only where the
  file is confirmed absent at the base

#### Scenario: The CLI install is pinned
- **WHEN** the provisioning step installs the reviewer CLI
- **THEN** it installs an exact pinned version rather than a floating tag

#### Scenario: The posting step's environment is credential-isolated
- **WHEN** the posting step runs after the reviewer step
- **THEN** it invokes its tools by absolute path, re-binds the strictness
  setting from repository variables in its own step environment, and reads the
  review text from a workspace file rather than an inherited variable

#### Scenario: The classified text is never piped nor env-passed
- **WHEN** the workflow classifies a review body on the CLI or poll path
- **THEN** the body reaches the classifier as a file read rather than a pipe,
  and the verdict is extracted by bounded in-shell string comparison

#### Scenario: Marker verdicts map to terminal status states
- **WHEN** a review's last non-empty line is the fix-required marker, and
  separately the ship-it marker
- **THEN** the `semantic-review` status is `failure` for the first and
  `success` for the second

#### Scenario: Strict mode posts no status but still posts the comment
- **WHEN** the fail-open setting is explicitly `false` and a reviewer run
  produces no verdict marker
- **THEN** no `semantic-review` status is posted while the CLI path still posts
  its review comment

#### Scenario: Pull-request events post pending first
- **WHEN** the workflow runs on a `pull_request` event
- **THEN** a `pending` `semantic-review` status is posted before the reviewer
  runs

#### Scenario: The review-event bridge guards reviewer and head commit
- **WHEN** the workflow runs on a `pull_request_review` event
- **THEN** it acts only where the review's author is the configured reviewer
  and its commit is the pull request's current head

#### Scenario: The CLI fail-open description names its source
- **WHEN** the gate's own CLI review produces no verdict marker and the
  fail-open setting is anything other than `false`, so the fail-open default
  stands
- **THEN** the posted `success` description names the CLI review as what
  produced no marker, distinguishing it from the other paths' shared wording

#### Scenario: A marker above trailing narration is still the verdict
- **GIVEN** a review body whose verdict marker is followed by the reviewer's
  own narration about writing its findings file
- **WHEN** the workflow classifies the reviewed text
- **THEN** the marker is read as the verdict, not treated as absent

#### Scenario: A quoted marker is not a verdict
- **GIVEN** a review body quoting a verdict marker mid-sentence and inside a
  transcript tool-call line, with no marker alone on its own line
- **WHEN** the workflow classifies the reviewed text
- **THEN** no verdict is parsed

#### Scenario: The difftastic download is pinned and guarded
- **WHEN** the workflow's difftastic install step is inspected
- **THEN** it requests a pinned release version rather than
  `releases/latest/download/`, and a failed download fails the step

#### Scenario: Skill discovery finds the pinned contract
- **WHEN** the reviewer step runs on a pull request that edits
  `.github/skills/code-review/SKILL.md`
- **THEN** the checkout's copy of that path holds the base ref's content, so
  the reviewed change cannot govern its own review

#### Scenario: The findings directory is inside the reviewer's sandbox
- **WHEN** the reviewer invocation is inspected
- **THEN** it passes `--add-dir` for the directory holding the findings file
