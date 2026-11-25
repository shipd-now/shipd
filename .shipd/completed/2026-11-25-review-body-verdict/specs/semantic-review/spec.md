## MODIFIED Requirements

### Requirement: Branded review submission body
id: gate-review-submission-body
base: e51e824e4f5f

`review_gate.py post` SHALL submit its pull request review with a body that
opens with the speaker heading `### ☕ shipd · semantic-review · reviewer (for
@<login>)`, where `<login>` is read once per post from `gh api user`. The next
line SHALL be the verdict line: the verdict in bold, `**❌ Fix required**` or
`**✅ Ship it**`, taken from the words the summary comment's findings header
uses; then ` — ` and the finding counts the commit status description carries
after its verdict word, such as `1 high, 1 low` or `no findings`; then
` · commit ` and the first seven characters of the reviewed head in
backticks. The line after it SHALL be one plain sentence pointing at the
summary comment. The body SHALL no longer read `Semantic review — see the
summary comment for the full report.`. If the login read fails, the heading
SHALL drop the `(for @<login>)` segment and the post SHALL proceed. Where
`--room-agent` is passed, the body SHALL stay the heading and the full
summary, which already states the verdict. The review event follows the
`gate-review-event` requirement; inline comments, summary comment, and commit
status SHALL be unchanged.

#### Scenario: Submission body carries the heading
- **WHEN** the poster submits a review with inline comments and `gh api user`
  returns login `mikkel`
- **THEN** the submitted body's first line is
  `### ☕ shipd · semantic-review · reviewer (for @mikkel)` and the old
  sentence is absent

#### Scenario: A failed login read still submits
- **WHEN** `gh api user` fails during `post`
- **THEN** the review is still submitted, its heading is
  `### ☕ shipd · semantic-review · reviewer`, and the event is `COMMENT` because the acting login is unknown

#### Scenario: A failing review states its verdict
- **WHEN** `post` publishes a `changes-requested` verdict with one high and
  one low finding on head `064b2ee1c0ffee`
- **THEN** the submitted body's second line is
  ``**❌ Fix required** — 1 high, 1 low · commit `064b2ee` `` and its third
  line is the pointer sentence

#### Scenario: A passing review states its verdict
- **WHEN** `post` publishes a `pass` verdict with no findings on head
  `dbc5a97a171186`
- **THEN** the submitted body's second line is
  ``**✅ Ship it** — no findings · commit `dbc5a97` ``

#### Scenario: A room reviewer keeps the full summary
- **WHEN** `post --room-agent reviewer-b` submits a review
- **THEN** the body is the heading and the full summary, it contains
  `## Findings:`, and it carries no separate verdict line
