## ADDED Requirements

### Requirement: Provisional ledger entries block promotion
id: provisional-entry-check

Alongside its deterministic context checks, the gate SHALL treat every
`## Questions and answers` entry in `plan.md` whose `**Answered by:**` field
holds `PLANNER` as a finding naming the entry, because a provisional default
still awaits a human answer. A plan carrying such an entry SHALL be rejected
like any other finding, and the check SHALL stay deterministic and
repository-local.

#### Scenario: Provisional ledger entry is a finding
- **GIVEN** a plan whose `### Q2:` ledger entry carries
  `**Answered by:** PLANNER`
- **WHEN** the gate runs
- **THEN** the change is rejected and the findings name entry `Q2` as a
  provisional entry awaiting a human answer

#### Scenario: Settled ledger entries pass
- **GIVEN** a plan whose ledger entries carry only `**Answered by:** ORACLE`
  or `**Answered by:** USER`
- **WHEN** the gate runs
- **THEN** no provisional-entry finding is produced
