## ADDED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster

The system SHALL provide `review_gate.py post <pr> --from <json|->` which,
given a `/s:review --json` object, publishes it to the named pull request
via `gh`: it SHALL upsert a single summary comment identified by the hidden
marker `<!-- am-semantic-review -->` (editing the existing marker comment in
place on re-runs), SHALL post inline comments only for findings whose
`location` anchors to a RIGHT-side commentable line of the PR diff (folding
unanchorable findings into the summary, and retrying once with no inline
comments if the review POST is rejected), and SHALL set a commit status with
context `semantic-review` on the PR's head SHA — state `success` iff the
verdict is `pass`, else `failure`, with the summary comment as target URL.
The script SHALL be stdlib-only and perform no analysis of its own.

#### Scenario: Pass verdict posts green
- **WHEN** `post` runs with a JSON whose verdict is `pass` and no prior
  marker comment exists
- **THEN** a summary comment carrying the marker is created and the
  `semantic-review` status on the head SHA is `success`

#### Scenario: Re-post updates instead of stacking
- **WHEN** `post` runs twice against the same PR
- **THEN** the second run edits the existing marker comment and exactly one
  marker comment exists afterward

#### Scenario: Red verdict anchors findings inline
- **WHEN** `post` runs with verdict `changes-requested`, one finding whose
  `path:LINE` is in the PR diff and one whose is not
- **THEN** the in-diff finding becomes an inline comment, the other appears
  in the summary, and the status state is `failure`

### Requirement: Required-check protection verb
id: required-check-protect

The system SHALL provide `review_gate.py protect [--remove]` which adds (or
with `--remove`, removes) the `semantic-review` context in the default
branch's required status check contexts via `gh`, preserving all other
contexts and protection settings unchanged. Running `protect` when the
context is already present SHALL make no change and exit zero.

#### Scenario: Protect adds alongside ci
- **WHEN** `protect` runs against protection requiring only `ci`
- **THEN** the required contexts become `ci` and `semantic-review`, and a
  second run changes nothing

#### Scenario: Remove restores the prior gate
- **WHEN** `protect --remove` runs against contexts `ci` and
  `semantic-review`
- **THEN** only `semantic-review` is removed and `ci` remains required

### Requirement: Skill post-to-PR flow
id: skill-post-flow

Where the user or a driving session explicitly requests posting, the
`/s:review` skill SHALL review the PR's branch against its base using
merge-base semantics, emit the machine JSON, and publish it through
`review_gate.py post`, reporting the resulting status state and summary
comment URL. The skill SHALL NOT post to any PR without an explicit request.

#### Scenario: Explicit request posts the verdict
- **WHEN** the user asks the skill to review and post to a PR
- **THEN** the skill runs the review, invokes the poster, and reports the
  posted status state and comment URL

#### Scenario: No silent posting
- **WHEN** the skill runs without a posting request
- **THEN** no `gh` write occurs and the review stays local

### Requirement: Poster test coverage in ci
id: gate-test-coverage

The `review_gate.py` script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that injects a fake `gh` command seam,
performs no network access, and covers marker upsert versus create, inline
anchor computation from patch text, status state mapping, the no-inline
fallback, and protect add/remove idempotency; the suite SHALL be discovered
by the existing `ci` review-tests step.

#### Scenario: ci discovers the poster suite
- **WHEN** the ci workflow's review test step runs
- **THEN** the poster tests run via unittest discovery with no network
  access and pass
