## ADDED Requirements

### Requirement: Ruleset findings are report-only in the skill
id: doctor-ruleset-lines

The `/s:doctor` skill SHALL recognize `merge-rules` and `actions-approve`
among the parsed check names and SHALL propose no `gh api` remedy of its own
for them: a `warn merge-rules` finding is relayed with `shipd gate rules`
output and applied only through `/s:gate`'s consent-gated `shipd gate rules
apply`, and a `warn actions-approve` finding is relayed as an admin setting
`/s:gate` offers. A `protection` warning whose detail names a ruleset SHALL
be report-only: the classic protection PUT and contexts POST SHALL NOT be
offered for it.

#### Scenario: Ruleset protection warning offers no classic remedy
- **WHEN** the doctor output carries a `warn protection` line naming a ruleset
- **THEN** the skill proposes neither the protection PUT nor the contexts POST

#### Scenario: Merge-rules drift is routed to the gate
- **WHEN** the doctor output carries a `warn merge-rules` line
- **THEN** the skill proposes no `gh api` write and points to `/s:gate`
