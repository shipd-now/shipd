## MODIFIED Requirements

### Requirement: Required-check protection verb
id: required-check-protect
base: 5b5effd453c0

`review_gate.py protect` SHALL read the default branch's protection,
union `semantic-review` into the required status check contexts, set
`required_conversation_resolution` to true, and write back preserving
`strict` and every other protection field; `protect --remove` SHALL
remove the context and clear the conversation-resolution requirement the
same way. If the protection read reports the branch as not protected (the
404 an unprotected branch returns), then `protect` SHALL create the
protection instead of failing: a write whose required status checks are
`strict` false and contexts `["semantic-review"]`, with conversation
resolution required and every other protection field null or absent.
Any other protection-read failure SHALL still fail the verb. Both
directions SHALL be idempotent — already in the desired
state means no write and exit zero — and the verb SHALL print the
resulting contexts and conversation-resolution state.

#### Scenario: Protect adds the check and the resolution requirement
- **GIVEN** required contexts `["ci"]` and conversation resolution off
- **WHEN** `protect` runs
- **THEN** contexts become `ci` and `semantic-review`, conversation
  resolution is required, and `strict` is preserved

#### Scenario: Remove restores the prior gate
- **WHEN** `protect --remove` runs on a protected branch
- **THEN** `semantic-review` leaves the contexts and conversation
  resolution is no longer required

#### Scenario: Unprotected branch gains minimal protection
- **GIVEN** a default branch whose protection read returns the
  not-protected 404
- **WHEN** `protect` runs
- **THEN** protection is created requiring `semantic-review` with `strict`
  false and conversation resolution required, and the verb prints the
  resulting state

#### Scenario: Other read failures still fail
- **WHEN** the protection read fails for any reason other than the
  not-protected 404
- **THEN** the verb fails naming the read error, and no write is performed
