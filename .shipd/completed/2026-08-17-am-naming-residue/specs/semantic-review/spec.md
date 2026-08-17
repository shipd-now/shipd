## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: c9b45f9faf7e

The system SHALL provide `review_gate.py post <pr> --from <json|->` which,
given a `/s:review --json` object, publishes it to the named pull request
via `gh`: it SHALL upsert a single summary comment identified by the hidden
marker `<!-- shipd-semantic-review -->` (editing the existing marker comment
in place on re-runs), SHALL post inline comments only for findings whose
`location` anchors to a RIGHT-side commentable line of the PR diff (folding
unanchorable findings into the summary, and retrying once with no inline
comments if the review POST is rejected), and SHALL set a commit status with
context `semantic-review` on the PR's head SHA. The summary-comment
upsert lookup SHALL also recognize the legacy marker
`<!-- am-semantic-review -->`, while every write SHALL emit only the current
marker, so a PR whose summary predates the rename is edited in place rather
than duplicated (`reply`, `autoreply`, and `resolve` identify gate threads
by their gate-authored root comment, which needs no marker matching). The verb SHALL accept
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

#### Scenario: Legacy-marker summary is updated, not duplicated
- **WHEN** `post` runs against a PR whose existing summary comment carries
  the legacy `<!-- am-semantic-review -->` marker
- **THEN** that comment is edited in place, the edited body opens with the
  current `<!-- shipd-semantic-review -->` marker, and exactly one gate
  summary comment exists afterward

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
