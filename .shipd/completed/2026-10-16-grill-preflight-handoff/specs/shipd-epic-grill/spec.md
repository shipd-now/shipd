## MODIFIED Requirements

### Requirement: Amend, gate, and hand off
id: epic-grill-amend-gate
base: 85fcbec50a05

For each answer, the skill SHALL edit the affected installed artifacts in
place to match it and SHALL rewrite the entry's `**Answered by:**` to `USER`
with the user's resolution as its `**Answer:**`. Where an answer binds every
member, the skill SHALL flag it for `/s:epic <epic> amend` and SHALL NOT
edit the epic. If any answer chose an option other than the adopted default,
then before gating the skill SHALL re-run the consistency pass on the member
holding each overturned entry and on every member that entry's
`**Relied on by:**` field names, or on every selected member when an
overturned entry carries no such field. The re-check SHALL fix in place what
the plans and repository settle and SHALL ask any conflict only a human can
settle in one further round before gating. The skill SHALL then run
`spec_gate.py <member>` on every selected member. If the gate exits 2, then
the skill SHALL resolve the findings the repository answers, ask the human
about the rest, and re-gate. The skill SHALL NOT set a member's status by
any other path. After the last gate the skill SHALL run
`autopilot.py <epic> --preflight` once from the repository root and SHALL
relay every `warn` and `fail` line and the closing `preflight:` line
verbatim. The skill SHALL end with a why-first summary per member and a
`## Summary` heading with one sentence that states the preflight verdict.
When the preflight exits 0, the skill SHALL print `/s:autopilot <epic>` on
its own line; when it exits non-zero, the skill SHALL list every `fail` line
it printed (or its error text when it printed no rubric line), SHALL name
the preflight command to re-run after the remedies, and SHALL NOT print the
hand-off. A `warn` line SHALL NOT block the hand-off. The skill SHALL NOT
build.

#### Scenario: Overridden default amends the plan
- **WHEN** the user picks a non-default option for a member's `Q1`
- **THEN** that member's plan states the chosen option, its ledger entry
  reads `**Answered by:** USER`, and its gate passes

#### Scenario: Overturned default re-checks its dependents
- **WHEN** the user overturns member `a`'s `Q2`, whose entry carries
  `**Relied on by:** b`
- **THEN** the skill re-runs the consistency pass on `a` and `b` before
  gating either

#### Scenario: Accepted defaults skip the re-check
- **WHEN** the user accepts every adopted default
- **THEN** the skill gates every member without a second consistency pass

#### Scenario: Members reach ready only after the round
- **WHEN** the grill is interrupted before the final round
- **THEN** every planned member is left at `draft`

#### Scenario: Green preflight hands off
- **GIVEN** every selected member gated to `ready`
- **WHEN** `autopilot.py <epic> --preflight` exits 0 with every line `ok`
- **THEN** the Ending relays `preflight: ok` and prints `/s:autopilot
  <epic>` on its own line

#### Scenario: Warnings do not block the hand-off
- **WHEN** the preflight exits 0 carrying a `warn drift —` line
- **THEN** the Ending relays that line and still prints `/s:autopilot
  <epic>`

#### Scenario: A failing rubric lists its lines instead
- **WHEN** the preflight exits 1 with a `fail members —` line naming an
  unplanned member
- **THEN** the Ending lists that `fail` line, names the preflight command
  to re-run, and prints no `/s:autopilot` line

#### Scenario: A rubric-less error is red
- **WHEN** the preflight exits non-zero printing no `ok|warn|fail` line
- **THEN** the Ending relays the error text in place of the `fail` lines
  and prints no `/s:autopilot` line
