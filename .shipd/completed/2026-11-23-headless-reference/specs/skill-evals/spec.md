# headless-reference — skill-evals delta

## MODIFIED Requirements

### Requirement: Oracle-default grading for a headless plan case
id: oracle-default-grading
base: 3e9fa066f47f

The runner SHALL support an `oracle-default` grader for a `/s:plan` case whose
request carries a decision that neither the fixture repository nor its wiki
store settles. An `oracle-default` run SHALL pass only when exactly one change
exists across the sanctioned storage locations and all five of these hold, in
order: `spec_lint.py` exits 0 for that change; the gate passes, meaning the
change's `plan.md` reads `Status: ready` and `spec_gate.py <change> --check`
exits 0; at least one `## Questions and answers` entry carries a
`**Verdict:**` of `ANSWER` or `INSUFFICIENT`; every entry whose verdict is
`INSUFFICIENT` carries a non-empty `**Answer:**` under an `**Answered by:**`
of `ASSUMPTION`, since the oracle gave no answer there and a session's own
default is not a person's answer, so `ORACLE`, `PLANNER`, and `USER` all fail; and at least one entry's verdict is `INSUFFICIENT`, so
the run proves the fallback to an adopted default. The judgement over the plan text and the lint and gate
outcomes SHALL be a pure function that reads no file and runs no process, and
a failing run SHALL name the first point that failed.

#### Scenario: A plan that consulted the oracle and adopted a default passes
- **WHEN** the change lints clean, reads `Status: ready`, passes the gate's
  check mode, and its one ledger entry carries `**Verdict:** INSUFFICIENT`,
  `**Answered by:** ASSUMPTION`, and a non-empty answer
- **THEN** the run is graded as passed

#### Scenario: A ledger with no oracle verdict fails
- **WHEN** the change lints clean and passes the gate, but no ledger entry
  carries a `**Verdict:**` field
- **THEN** the run is graded as failed, naming the missing verdict

#### Scenario: An insufficient verdict with no adopted answer fails
- **WHEN** a ledger entry carries `**Verdict:** INSUFFICIENT` and an empty
  `**Answer:**`
- **THEN** the run is graded as failed, naming that entry

#### Scenario: An insufficient verdict credited to the oracle fails
- **WHEN** a ledger entry carries `**Verdict:** INSUFFICIENT` and
  `**Answered by:** ORACLE`
- **THEN** the run is graded as failed, naming that entry

#### Scenario: A ledger the oracle answered in full fails
- **WHEN** the change lints clean and passes the gate, and every ledger entry
  carries `**Verdict:** ANSWER`
- **THEN** the run is graded as failed, naming the missing fallback

#### Scenario: A plan the gate rejects fails
- **WHEN** the change's ledger is well formed but `spec_gate.py --check` exits
  non-zero
- **THEN** the run is graded as failed, naming the gate

#### Scenario: The go-ahead reply names the headless contract
- **WHEN** the plan-specific go-ahead reply is inspected
- **THEN** it states that no human is available and names the absolute path
  of `headless.md`

#### Scenario: The judgement runs without a session
- **WHEN** the grader's unit tests run
- **THEN** they judge literal `plan.md` text and spawn no `claude` process

#### Scenario: An insufficient verdict credited to the user fails
- **WHEN** a ledger entry carries `**Verdict:** INSUFFICIENT` and
  `**Answered by:** USER`
- **THEN** the run is graded as failed, naming that entry and expecting
  `ASSUMPTION`
