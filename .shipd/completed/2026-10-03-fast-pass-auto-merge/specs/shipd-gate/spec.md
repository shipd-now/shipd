## ADDED Requirements

### Requirement: Fast-pass consent row
id: gate-fast-pass-consent

The `/s:gate` skill's single batched consent selection SHALL carry a fast-pass
step alongside the ones it already offers, running
`gh variable set SHIPD_FAST_PASS --body true`. Its option SHALL state the
mutation it performs and, in plain words, that a pull request carrying a
completed shipd change whose every delta scenario the review verified then
merges without a human. The step SHALL be omitted, with a note, wherever the
auto-merge option is omitted — a repository that never arms auto-merge cannot
fast-pass — and SHALL run only on a consent answer naming it. The skill's
closing `shipd doctor` report SHALL relay the `fast-pass` line beside the
`protection`, `automerge`, and `copilot-secret` lines, so what was enabled is
read back from the preflight rather than asserted.

Where the user declines the fast-pass step, the skill SHALL state that reviewed
pull requests still wait for a human merge. The update flow SHALL NOT touch the
variable: it remains a repository setting, and the refresh flow sets none.

#### Scenario: The consent round offers the fast-pass step
- **WHEN** the batched selection is presented in a repository whose resolved
  `pr-mode` is not `draft`
- **THEN** it carries a fast-pass option naming
  `gh variable set SHIPD_FAST_PASS --body true` and what it permits

#### Scenario: Draft pr-mode omits the fast-pass step
- **WHEN** the layered configuration resolves `pr-mode: draft`
- **THEN** the selection carries neither the auto-merge option nor the
  fast-pass option, and the skill notes why

#### Scenario: Declining the step is reported
- **WHEN** the user consents to other steps but not the fast-pass step
- **THEN** no variable is set and the closing report states that reviewed pull
  requests still wait for a human merge

#### Scenario: The closing report reads the line back
- **WHEN** the skill closes by running `shipd doctor`
- **THEN** it relays the `fast-pass` line with the `protection`, `automerge`,
  and `copilot-secret` lines

#### Scenario: The update flow sets no variable
- **WHEN** `/s:gate update` completes on any path
- **THEN** no `SHIPD_FAST_PASS` write has been performed
