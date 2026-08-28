## MODIFIED Requirements

### Requirement: Required-check protection verb
id: required-check-protect
base: 19ab4617677f

`review_gate.py protect` SHALL read the default branch's protection,
union `semantic-review` into the required status checks, set
`required_conversation_resolution` to true, and write back preserving
`strict` and every other protection field; `protect --remove` SHALL
remove the check and clear the conversation-resolution requirement the
same way.

The write SHALL express the required status checks as `checks`, carrying one
entry per context with an explicit `app_id` of null, rather than as the legacy
`contexts` field. A null `app_id` states that any source may report the check,
which is what lets a status posted by a person — a review produced by hand when
the configured reviewer could not run — satisfy the requirement. Writing
`contexts` leaves that to GitHub's own translation, so the same outcome held
only by accident and said nothing about the intent; a branch whose check is
pinned to one app silently ignores every status from any other source.

If the protection read reports the branch as not protected (the
404 an unprotected branch returns), then `protect` SHALL create the
protection instead of failing: a write whose required status checks are
`strict` false and one `semantic-review` check with a null `app_id`, with
conversation resolution required and every other protection field null or
absent. Any other protection-read failure SHALL still fail the verb. Both
directions SHALL be idempotent — already in the desired
state means no write and exit zero — and the verb SHALL print the
resulting contexts and conversation-resolution state.

#### Scenario: The write names any app as the reporting source
- **WHEN** `protect` builds its protection write
- **THEN** the body carries a `checks` list whose `semantic-review` entry has
  an `app_id` of null, and carries no legacy `contexts` field

#### Scenario: Protect adds the check and the resolution requirement
- **GIVEN** required contexts `["ci"]` and conversation resolution off
- **WHEN** `protect` runs
- **THEN** the required checks become `ci` and `semantic-review`, conversation
  resolution is required, and `strict` is preserved

#### Scenario: Remove restores the prior gate
- **WHEN** `protect --remove` runs on a protected branch
- **THEN** `semantic-review` leaves the required checks and conversation
  resolution is no longer required

#### Scenario: Unprotected branch gains minimal protection
- **GIVEN** a default branch whose protection read returns the
  not-protected 404
- **WHEN** `protect` runs
- **THEN** protection is created requiring `semantic-review` with `strict`
  false and a null `app_id`, conversation resolution required, and the verb
  prints the resulting state

#### Scenario: Other read failures still fail
- **WHEN** the protection read fails for any reason other than the
  not-protected 404
- **THEN** the verb fails naming the read error, and no write is performed
