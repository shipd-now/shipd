# headless-reference — context-gate delta

## ADDED Requirements

### Requirement: Assumption ledger entries must be complete
id: assumption-entry-check

Alongside its other checks, the gate SHALL treat every `## Questions and
answers` entry in `plan.md` whose `**Answered by:**` field holds `ASSUMPTION`
as a finding naming the entry when it carries no `**Verdict:**` field, or when
its `**Answer:**` is empty — also when it is empty once a leading
`Proceeding on the recommendation:` is removed. A wrapped answer on
continuation lines SHALL count as non-empty. A well-formed `ASSUMPTION` entry
SHALL NOT be provisional and SHALL pass. The existing `PLANNER` finding SHALL
stay unchanged, and the check SHALL stay deterministic and repository-local.

#### Scenario: A well-formed assumption passes
- **GIVEN** a plan whose ledger entry carries `**Verdict:** INSUFFICIENT`,
  `**Answered by:** ASSUMPTION`, and a non-empty `**Answer:**`
- **WHEN** the gate runs
- **THEN** no ledger finding is produced

#### Scenario: An assumption with no verdict is a finding
- **GIVEN** an `ASSUMPTION` entry `### Q2:` with no `**Verdict:**` field
- **WHEN** the gate runs
- **THEN** the change is rejected and the findings name entry `Q2`

#### Scenario: An assumption with an empty answer is a finding
- **GIVEN** an `ASSUMPTION` entry whose `**Answer:**` is empty, or reads only
  `Proceeding on the recommendation:`
- **WHEN** the gate runs
- **THEN** the change is rejected and the findings name that entry

#### Scenario: A planner entry is still provisional
- **GIVEN** an entry carrying `**Answered by:** PLANNER`
- **WHEN** the gate runs
- **THEN** the findings name it as provisional, as before

### Requirement: Ledger questions may quote a placeholder marker
id: ledger-question-placeholder-exemption

The placeholder check of `context-sufficiency-checks` SHALL NOT fire on a
marker that sits inside the `**Question:**` field of a `## Questions and
answers` entry, because a question may legitimately quote the word. The field
runs from its line to the next ledger field, heading, or blank line, so a
wrapped question counts. The check SHALL keep firing on a marker in any other
field of a ledger entry and anywhere else in `plan.md`, the delta specs, or
`tasks.md`.

#### Scenario: A marker quoted in a ledger question passes
- **WHEN** a ledger entry's `**Question:**` line quotes a placeholder marker
  and no other marker appears
- **THEN** the gate produces no placeholder finding

#### Scenario: A marker on a wrapped question line passes
- **WHEN** a placeholder marker sits on a continuation line of a
  `**Question:**` field
- **THEN** the gate produces no placeholder finding

#### Scenario: A marker in a ledger answer is still a finding
- **WHEN** a ledger entry's `**Answer:**` line carries a placeholder marker
- **THEN** the findings name the placeholder

#### Scenario: A marker outside the ledger is still a finding
- **WHEN** a placeholder marker appears in the plan's `## Implementation`
- **THEN** the findings name the placeholder
