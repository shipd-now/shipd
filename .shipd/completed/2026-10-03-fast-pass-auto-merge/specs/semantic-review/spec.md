## ADDED Requirements

### Requirement: Fast-pass eligibility and poster arming
id: fast-pass-eligibility

Where a change is in scope, the `/s:review --json` object SHALL carry a
`change` member holding the resolved `slug`, the `location` (`planned` or
`completed`), and the `dir` reported by `semdiff change`, and SHALL omit that
member entirely where no change is in scope — the same presence rule
`spec_coverage` follows. Both documented payload surfaces —
`plugins/s/skills/review/references/json-output.md` and
`plugins/s/harness/references/review.md` — SHALL state that member, and a test
SHALL assert the two surfaces agree so one cannot drift behind the other.

`review_gate.py` SHALL expose a pure eligibility predicate deciding whether a
review object fast-passes. A review is eligible only where **all** of these
hold: the repository variable `SHIPD_FAST_PASS` reads exactly `true`; the
review's `change.location` is `completed`; the review's `verdict` is `pass`;
and `spec_coverage` is non-empty with every entry's `state` equal to `met`. The
predicate SHALL read `verdict` and never the disposition-mapped status state,
because `status_state` returns `success` unconditionally under the `none`
disposition scope and ignores medium findings under `high-only`, so a status
posted under either scope says nothing about whether findings remain open.

While a review is eligible, `review_gate.py post` SHALL arm auto-merge on the
pull request with `gh pr merge --auto --squash --delete-branch` through its
existing injectable `gh` runner, after the commit status is set, and SHALL
record in the summary comment that the fast-pass was armed. If a review is not
eligible, then `post` SHALL arm nothing and SHALL record which condition was
unmet, so a pull request that waits for a human says why. The variable SHALL be
read as `gh variable get SHIPD_FAST_PASS` through the same runner, and a
non-zero exit SHALL be treated as the fast-pass being off. If the arming call
fails, then `post` SHALL report the failure and SHALL still exit on the status
it already posted — a refused merge arming never costs the verdict.

#### Scenario: A verified completed change arms the merge
- **GIVEN** `SHIPD_FAST_PASS` reads `true`
- **WHEN** `post` consumes a review whose `change.location` is `completed`,
  whose verdict is `pass`, and whose every `spec_coverage` state is `met`
- **THEN** `gh pr merge --auto --squash --delete-branch` is run on that pull
  request and the summary comment records the fast-pass

#### Scenario: A can't-tell scenario arms nothing
- **WHEN** `post` consumes an otherwise eligible review carrying one
  `spec_coverage` entry whose state is `cant-tell`
- **THEN** no merge arming is run and the summary comment names the unmet
  condition

#### Scenario: The none disposition cannot fast-pass a failing verdict
- **GIVEN** `SHIPD_FAST_PASS` reads `true` and the acting disposition is `none`
- **WHEN** `post` consumes a review whose verdict is `changes-requested`
- **THEN** the commit status is `success` under that scope and no merge arming
  is run

#### Scenario: A planned-only change arms nothing
- **WHEN** `post` consumes an otherwise eligible review whose
  `change.location` is `planned`
- **THEN** no merge arming is run

#### Scenario: An absent variable is off
- **WHEN** `gh variable get SHIPD_FAST_PASS` exits non-zero
- **THEN** the predicate reports the review ineligible and no merge arming is
  run

#### Scenario: A review with no change in scope omits the member
- **WHEN** a `--json` review runs with no change in scope
- **THEN** the object carries no `change` member and no merge arming is run

#### Scenario: Both payload surfaces carry the change member
- **WHEN** `plugins/s/skills/review/references/json-output.md` and
  `plugins/s/harness/references/review.md` are compared
- **THEN** both document the `change` member with the same keys

#### Scenario: A refused arming keeps the verdict
- **WHEN** the merge arming call exits non-zero after the status was posted
- **THEN** `post` reports the arming failure and the posted status stands
