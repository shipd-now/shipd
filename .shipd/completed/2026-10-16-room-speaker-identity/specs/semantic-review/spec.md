## ADDED Requirements

### Requirement: Branded review submission body
id: gate-review-submission-body

`review_gate.py post` SHALL submit its pull request review with a body that
opens with the speaker heading `### ☕ shipd · semantic-review · reviewer (for
@<login>)`, where `<login>` is read once per post from `gh api user`, followed
on the next line by one plain sentence pointing at the summary comment. The
body SHALL no longer read `Semantic review — see the summary comment for the
full report.`. If the login read fails, the heading SHALL drop the `(for @<login>)`
segment and the post SHALL proceed. The review event, inline comments, summary
comment, and commit status SHALL be unchanged.

#### Scenario: Submission body carries the heading
- **WHEN** the poster submits a review with inline comments and `gh api user`
  returns login `mikkel`
- **THEN** the submitted body's first line is
  `### ☕ shipd · semantic-review · reviewer (for @mikkel)` and the old
  sentence is absent

#### Scenario: A failed login read still submits
- **WHEN** `gh api user` fails during `post`
- **THEN** the review is still submitted, its heading is
  `### ☕ shipd · semantic-review · reviewer`, and the event is `COMMENT`
