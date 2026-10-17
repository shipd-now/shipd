## ADDED Requirements

### Requirement: Merge rules consent row
id: gate-rules-consent

The `/s:gate` skill's single batched consent selection SHALL carry a merge
rules step running `shipd gate rules apply`, whose option states in plain
words that it creates or updates one repository ruleset named `shipd merge
rules` from the `merge` configuration, requiring the configured approvals and
status checks before a pull request merges. The skill SHALL first run bare
`shipd gate rules` and show its output as the preview, SHALL run the step only
on a consent answer naming it, SHALL report a 403 as that step's failure with
the manual hint without blocking other consented steps, and SHALL NOT run it
in the `update` flow. The closing report SHALL state that the rules are
enforced by GitHub only once the ruleset exists.

#### Scenario: The consent round offers the step
- **WHEN** the batched selection is presented
- **THEN** it carries an option naming `shipd gate rules apply` and the
  ruleset it writes

#### Scenario: Declining writes nothing
- **WHEN** the user consents to other steps but not this one
- **THEN** `shipd gate rules apply` is not run

#### Scenario: Update flow never applies rules
- **WHEN** `/s:gate update` runs
- **THEN** no ruleset call is made
