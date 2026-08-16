## ADDED Requirements

### Requirement: Auto-disposition reply verb
id: auto-disposition-verb

`review_gate.py autoreply <pr> --disposition <scope>` SHALL, through the
same injectable `gh` seam as the poster, post a canonical policy reply
onto gate-authored, unresolved finding threads that carry no reply yet,
where `<scope>` is `high-only` or `none`: under `high-only` it SHALL
reply only to threads whose root comment's severity — parsed from the
gate's own inline-body format, whose leading severity marker SHALL be
shared as one constant with the body renderer — is `medium` or `low`,
leaving `high` and unparseable roots untouched and reporting them; under
`none` it SHALL reply to every such thread without consulting severity.
The default reply body SHALL name the acting disposition scope and MAY be
overridden with `--body <text>`. The verb SHALL print `replied=<n>`,
SHALL skip threads already carrying a reply so re-runs are idempotent,
SHALL never touch human-authored threads, and SHALL exit zero on a
successful pass.

#### Scenario: High-only replies below the threshold
- **GIVEN** unreplied gate-authored threads rooted at one high, one
  medium, and one low finding comment
- **WHEN** `autoreply <pr> --disposition high-only` runs
- **THEN** the medium and low threads each gain a reply naming the
  policy, the high thread is untouched, and `replied=2` prints

#### Scenario: None replies to everything
- **WHEN** `autoreply <pr> --disposition none` runs over three unreplied
  gate-authored threads of mixed severity
- **THEN** all three threads gain the policy reply and `replied=3` prints

#### Scenario: Re-run is idempotent
- **GIVEN** a thread already carrying an autoreply
- **WHEN** `autoreply <pr> --disposition none` runs again
- **THEN** that thread gains no second reply and `replied=0` prints

#### Scenario: Unparseable root is left for judgment
- **GIVEN** a gate-authored thread whose root body does not start with
  the gate's severity marker
- **WHEN** `autoreply <pr> --disposition high-only` runs
- **THEN** the thread is untouched and reported as unparsed

## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: cf53b6a5b153

The system SHALL provide `review_gate.py post <pr> --from <json|->` which,
given a `/s:review --json` object, publishes it to the named pull request
via `gh`: it SHALL upsert a single summary comment identified by the hidden
marker `<!-- am-semantic-review -->` (editing the existing marker comment in
place on re-runs), SHALL post inline comments only for findings whose
`location` anchors to a RIGHT-side commentable line of the PR diff (folding
unanchorable findings into the summary, and retrying once with no inline
comments if the review POST is rejected), and SHALL set a commit status with
context `semantic-review` on the PR's head SHA. The verb SHALL accept
`--disposition <scope>` (`all`, `high-only`, or `none`, default `all`) and
SHALL map the status state by scope: under `all`, `success` iff the verdict
is `pass`; under `high-only`, `success` iff no finding has severity `high`;
under `none`, always `success` — the findings JSON and rendered verdict
stay severity-honest in every scope. When the scope is not `all`, the
summary comment SHALL carry a `Disposition: <scope>` line and the status
description SHALL name the scope. The verb SHALL also accept
`--model <tier>` and, when given, SHALL record it verbatim as a
`Model: <tier>` line in the summary comment without resolving symbolic
tiers. The script SHALL be stdlib-only and perform no analysis of its own.

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

#### Scenario: High-only greens over mediums
- **WHEN** `post --disposition high-only` runs with verdict
  `changes-requested` from one medium and one low finding and no high
- **THEN** the status state is `success`, its description names the
  scope, and the summary carries the findings and a
  `Disposition: high-only` line

#### Scenario: High-only stays red on a high
- **WHEN** `post --disposition high-only` runs with a JSON carrying a
  high finding
- **THEN** the status state is `failure`

#### Scenario: None is always green and stays honest
- **WHEN** `post --disposition none --model tier-below` runs with a JSON
  carrying a high finding
- **THEN** the status state is `success` and the summary comment carries
  the finding, a `Disposition: none` line, and a `Model: tier-below` line

### Requirement: Skill post-to-PR flow
id: skill-post-flow
base: 86c84ad6549a

Where the user explicitly asks for a review to be posted, the `/s:review`
skill SHALL run the review, emit the machine verdict, and publish it via
the poster, passing through the disposition scope and model tier when the
invoker supplied them (defaults: scope `all`, no tier). The skill SHALL
then disposition findings by scope. Under `all`, the flow SHALL run the
full loop over every posted finding regardless of severity: implement the
suggestion (edit, commit, push) when it is correct, otherwise reply on the
finding's thread with the concrete reason via the gate's reply verb —
never leaving a finding with neither. Under `high-only`, the flow SHALL
implement (or push back with a reasoned reply) only the high-severity
findings, re-reviewing and re-posting after any push, and SHALL then run
the gate's autoreply verb so the remaining threads carry disposition
evidence. Under `none`, the flow SHALL perform no per-finding judgment and
SHALL run the autoreply verb over every gate thread. Every scope SHALL
finish by running the gate's resolve verb and reporting the posted status
state, the summary comment URL, the acting scope when it is not `all`, and
the unresolved count, which SHALL be zero on a completed disposition. The
skill SHALL document that applying the model tier is the spawning driver's
concern, and SHALL NOT resolve the pipeline configuration or post as a
side effect of a plain review request.

#### Scenario: Sensible suggestion is implemented before merge
- **GIVEN** a posted low finding whose fix is correct under scope `all`
- **WHEN** the disposition loop reaches it
- **THEN** the fix is committed and pushed rather than left as advice

#### Scenario: Disagreement is answered, not ignored
- **WHEN** the session judges a posted finding not worth implementing
  under scope `all`
- **THEN** the finding's thread gains a reasoned reply and is then
  resolved

#### Scenario: Flow ends with zero unresolved
- **WHEN** the posting flow completes in any scope
- **THEN** the report includes `unresolved=0` from the resolve verb

#### Scenario: High-only spends judgment only on highs
- **GIVEN** an invocation passing disposition `high-only` and a posted
  review with one high and two medium findings
- **WHEN** the posting flow runs
- **THEN** the high finding is implemented or answered with a reasoned
  reply, the medium threads are covered by the autoreply verb instead of
  individual judgment, and the flow ends with resolve reporting zero
  unresolved

#### Scenario: None costs no disposition judgment
- **GIVEN** an invocation passing disposition `none`
- **WHEN** the posting flow runs
- **THEN** the review is posted, the autoreply verb covers every gate
  thread, resolve reports zero unresolved, and no finding receives an
  individually authored disposition

### Requirement: Poster test coverage in ci
id: gate-test-coverage
base: f5194d863057

The `review_gate.py` script SHALL be covered by a unittest suite under
`plugins/s/skills/review/tests/` that injects a fake `gh` command seam,
performs no network access, and covers marker upsert versus create, inline
anchor computation from patch text, status state mapping including the
per-disposition-scope mapping and provenance lines, the no-inline
fallback, protect add/remove idempotency, and the autoreply verb's
severity selection, idempotent re-run, and round-trip between the inline
body renderer and the severity parser; the suite SHALL be discovered by
the existing `ci` review-tests step.

#### Scenario: ci discovers the poster suite
- **WHEN** the ci workflow's review test step runs
- **THEN** the poster tests run via unittest discovery with no network
  access and pass
