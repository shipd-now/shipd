## ADDED Requirements

### Requirement: Review event follows the status and never self-approves
id: gate-review-event

`review_gate.py post` SHALL submit its pull request review with an event
chosen from the `semantic-review` status state it sets: `APPROVE` when the
state is `success` and `REQUEST_CHANGES` when it is `failure`, under every
disposition scope. It SHALL submit exactly one such review per post, with a
body only and no inline comments when no finding anchors. When the acting
login (read once from `gh api user`) equals the pull request's author
(`gh pr view --json author`, compared case-insensitively), or either login
cannot be read, it SHALL NOT attempt an approval or change request: it SHALL
submit a `COMMENT` review only when findings anchor, and print one line naming
the login and saying GitHub rejects self-approval. If a decision review is
rejected, the poster SHALL retry it once with no inline comments and the same
event, and if that is rejected too, submit a body-only `COMMENT` review and
print a line saying the decision was not recorded. The result object SHALL
carry the `review_event` actually submitted, or `None`.

#### Scenario: A clean pass approves without findings
- **WHEN** `post` publishes a `pass` verdict with no findings and the acting
  login differs from the pull request author
- **THEN** one review is submitted with event `APPROVE`, no inline comments

#### Scenario: A failing verdict requests changes
- **WHEN** `post` publishes a `changes-requested` verdict with an anchored
  finding under disposition `all`
- **THEN** one review is submitted with event `REQUEST_CHANGES` carrying the
  inline comment

#### Scenario: The event follows the status under high-only
- **WHEN** `post` runs with `--disposition high-only` over a
  `changes-requested` verdict carrying only medium findings
- **THEN** the status is `success` and the review event is `APPROVE`

#### Scenario: The author never approves
- **WHEN** the acting login equals the pull request author
- **THEN** no `APPROVE` or `REQUEST_CHANGES` is submitted, findings that
  anchor go out as a `COMMENT` review, and one explanatory line is printed

#### Scenario: An unreadable login falls back to a comment
- **WHEN** `gh api user` or the author read fails
- **THEN** the review is submitted as `COMMENT` or not at all, never as a
  decision

#### Scenario: A rejected decision retries then degrades
- **WHEN** an `APPROVE` review is rejected twice
- **THEN** a body-only `COMMENT` review is submitted and the output says the
  decision was not recorded

### Requirement: Approval change ships docs, tests, and a version bump
id: gate-approvals-docs-version

The change SHALL replace the test pinning `COMMENT` with tests of the
`gate-review-event` scenarios through the `FakeGh` seam, update the poster's
caller docs (`review/references/posting.md` and
`docs/semantic-review-reference.md`) to describe the event and the author rule,
and advance the plugin version in `plugins/s/.claude-plugin/plugin.json` by
one patch above the value `main` carries.

#### Scenario: Review suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/review/tests`
  runs with no network
- **THEN** it reports `OK`

#### Scenario: Version guard passes
- **WHEN** `version_guard.py --base main --head HEAD` runs on the change
- **THEN** it exits `0`
