## MODIFIED Requirements

### Requirement: Review event follows the status and never self-approves
id: gate-review-event
base: 3b1454b236e9

`review_gate.py post` SHALL submit its pull request review with an event
chosen from the `semantic-review` status state it sets: `APPROVE` when the
state is `success` and `REQUEST_CHANGES` when it is `failure`, under every
disposition scope. It SHALL submit exactly one such review per post, with a
body only and no inline comments when no finding anchors. When the acting
login (read once from `gh api user`) equals the pull request's author
(`gh pr view --json author`, compared case-insensitively), or either login
cannot be read, it SHALL NOT attempt an approval or change request: it SHALL
submit exactly one `COMMENT` review, with a body only when no finding
anchors, so that every post leaves a review that states its verdict. When the
login is the author's, it SHALL print one line naming the login and saying
GitHub rejects self-approval. If a decision review is
rejected, the poster SHALL retry it once with no inline comments and the same
event, and if that is rejected too, submit a body-only `COMMENT` review and
print a line saying the decision was not recorded. If a `COMMENT` review with
inline comments is rejected, the poster SHALL retry it once with no inline
comments. The result object SHALL carry the `review_event` actually
submitted, or `None`.

`docs/semantic-review-reference.md` and the review skill's
`references/posting.md` SHALL state that the author's account, or an
unreadable login, submits one `COMMENT` review on every post, and neither
SHALL say such a review is submitted only when findings anchor. The reference
doc SHALL name the verdict line the review body carries.

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

#### Scenario: The author's clean pass still posts a review
- **WHEN** `post` publishes a `pass` verdict with no findings and the acting
  login equals the pull request author
- **THEN** one `COMMENT` review is submitted with a body and no inline
  comments, and the result's `review_event` is `COMMENT`

#### Scenario: An unreadable login falls back to a comment
- **WHEN** `gh api user` or the author read fails
- **THEN** the review is submitted as `COMMENT`, never as a decision

#### Scenario: A rejected decision retries then degrades
- **WHEN** an `APPROVE` review is rejected twice
- **THEN** a body-only `COMMENT` review is submitted and the output says the
  decision was not recorded

#### Scenario: The docs state the new rule
- **WHEN** `docs/semantic-review-reference.md` and
  `plugins/s/skills/review/references/posting.md` are read
- **THEN** neither contains "only when findings anchor", each says a
  `COMMENT` review is submitted on every post from the author's account, and
  `docs_lint.py docs/semantic-review-reference.md` exits `0`
