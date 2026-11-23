# eval-headless-oracle-default — skill-evals delta

## ADDED Requirements

### Requirement: Oracle-default grading for a headless plan case
id: oracle-default-grading

The runner SHALL support an `oracle-default` grader for a `/s:plan` case whose
request carries a decision that neither the fixture repository nor its wiki
store settles. An `oracle-default` run SHALL pass only when exactly one change
exists across the sanctioned storage locations and all five of these hold, in
order: `spec_lint.py` exits 0 for that change; the gate passes, meaning the
change's `plan.md` reads `Status: ready` and `spec_gate.py <change> --check`
exits 0; at least one `## Questions and answers` entry carries a
`**Verdict:**` of `ANSWER` or `INSUFFICIENT`; every entry whose verdict is
`INSUFFICIENT` carries a non-empty `**Answer:**` under an `**Answered by:**`
of `USER` or `ORACLE`; and at least one entry's verdict is `INSUFFICIENT`, so
the run proves the fallback to an adopted default. The judgement over the plan text and the lint and gate
outcomes SHALL be a pure function that reads no file and runs no process, and
a failing run SHALL name the first point that failed.

#### Scenario: A plan that consulted the oracle and adopted a default passes
- **WHEN** the change lints clean, reads `Status: ready`, passes the gate's
  check mode, and its one ledger entry carries `**Verdict:** INSUFFICIENT`,
  `**Answered by:** USER`, and a non-empty answer
- **THEN** the run is graded as passed

#### Scenario: A ledger with no oracle verdict fails
- **WHEN** the change lints clean and passes the gate, but no ledger entry
  carries a `**Verdict:**` field
- **THEN** the run is graded as failed, naming the missing verdict

#### Scenario: An insufficient verdict with no adopted answer fails
- **WHEN** a ledger entry carries `**Verdict:** INSUFFICIENT` and an empty
  `**Answer:**`
- **THEN** the run is graded as failed, naming that entry

#### Scenario: A ledger the oracle answered in full fails
- **WHEN** the change lints clean and passes the gate, and every ledger entry
  carries `**Verdict:** ANSWER`
- **THEN** the run is graded as failed, naming the missing fallback

#### Scenario: A plan the gate rejects fails
- **WHEN** the change's ledger is well formed but `spec_gate.py --check` exits
  non-zero
- **THEN** the run is graded as failed, naming the gate

#### Scenario: The judgement runs without a session
- **WHEN** the grader's unit tests run
- **THEN** they judge literal `plan.md` text and spawn no `claude` process

## MODIFIED Requirements

### Requirement: Per-case grader selection
id: case-grader-selection
base: 65eab2107d13

An eval case MAY carry an `expect.json` file at `evals/cases/<name>/` declaring
which grader scores its runs, via a `grader` key whose recognized values are
`structural`, `behavior`, `handoff`, and `oracle-default`. Where the file is
absent, or present without a `grader` key, the runner SHALL grade the case
structurally. A `handoff` grader additionally requires a `handoff_requirement`
key naming the requirement id its grader looks for. If `expect.json` is
unreadable, declares an unrecognized grader, or declares `handoff` without
`handoff_requirement`, then the runner SHALL record the run as failed and name
the offending case and value.

#### Scenario: A case without expect.json grades structurally
- **WHEN** a case directory holds `prompt.md` and `fixture/` but no
  `expect.json`
- **THEN** its runs are scored by the structural assertions, unchanged

#### Scenario: A case selects the behavior grader
- **WHEN** a case's `expect.json` declares `{"grader": "behavior"}`
- **THEN** its runs are scored by the behavior grader

#### Scenario: A case selects the handoff grader
- **WHEN** a case's `expect.json` declares `{"grader": "handoff"}` with a
  `handoff_requirement`
- **THEN** its runs are scored by the handoff grader

#### Scenario: A case selects the oracle-default grader
- **WHEN** a case's `expect.json` declares `{"grader": "oracle-default"}`
- **THEN** its runs are scored by the oracle-default grader

#### Scenario: A handoff grader without its requirement fails the run
- **WHEN** a case declares `{"grader": "handoff"}` and no `handoff_requirement`
- **THEN** the run is recorded as failed naming the case and the missing key,
  and no session is spawned

#### Scenario: An unrecognized grader fails the run
- **WHEN** a case's `expect.json` declares a grader value outside the recognized
  set
- **THEN** the run is recorded as failed and the failure names the case and the
  unrecognized value

### Requirement: Grader-selected gate and reply
id: grader-selected-driving
base: 3956a87b401d

The runner SHALL select a conversation's resume gate and resume reply from the
case's own grader, covering every recognized grader rather than branching one
grader against all others. A handoff-graded case SHALL NOT be resumed at all:
its correct outcome is that the session stops, so the run ends after the first
turn and is graded there. An oracle-default-graded case SHALL be driven with
the structural gate and the plan-specific go-ahead reply, so its resume loop
stops once a lint-clean `ready` change exists and the oracle grade decides the
run afterwards. If a grader is added without its own gate and reply, then the
runner SHALL fail the run naming that grader rather than falling back to
another grader's driving behavior.

#### Scenario: A handoff case is graded on its first turn
- **WHEN** a handoff-graded session ends its first turn
- **THEN** no resumed turn is sent, and the run is graded on the state that turn
  left behind

#### Scenario: A stopped session is never told to continue
- **WHEN** a handoff-graded session stops, having correctly changed nothing
- **THEN** it receives no reply instructing it to proceed, emit, lint, or
  promote a change

#### Scenario: A structural case keeps its own gate and reply
- **WHEN** a structural case is driven
- **THEN** its gate is the structural grade and its reply is the plan-specific
  go-ahead, unchanged

#### Scenario: An oracle-default case resumes on the structural gate
- **WHEN** an oracle-default-graded session ends a turn at its typed decision
  round with no change emitted yet
- **THEN** it is resumed with the plan-specific go-ahead reply, and resuming
  stops once the structural grade passes

#### Scenario: An undriveable grader fails loudly
- **WHEN** a case declares a grader for which no gate and reply are defined
- **THEN** the run is recorded as failed naming that grader, rather than driven
  with another grader's gate or reply
