## ADDED Requirements

### Requirement: Per-case grader selection
id: case-grader-selection

An eval case MAY carry an `expect.json` file at `evals/cases/<name>/` declaring
which grader scores its runs, via a `grader` key whose recognized values are
`structural` and `behavior`. Where the file is absent, or present without a
`grader` key, the runner SHALL grade the case structurally. If `expect.json` is
unreadable or declares an unrecognized grader, then the runner SHALL record the
run as failed and name the offending case and value.

#### Scenario: A case without expect.json grades structurally
- **WHEN** a case directory holds `prompt.md` and `fixture/` but no
  `expect.json`
- **THEN** its runs are scored by the structural assertions, unchanged

#### Scenario: A case selects the behavior grader
- **WHEN** a case's `expect.json` declares `{"grader": "behavior"}`
- **THEN** its runs are scored by the behavior grader instead of the structural
  assertions

#### Scenario: An unrecognized grader fails the run
- **WHEN** a case's `expect.json` declares a grader value that is neither
  `structural` nor `behavior`
- **THEN** the run is recorded as failed and the failure names the case and the
  unrecognized value

### Requirement: Behavior grading against a held-out oracle
id: behavior-grading

A behavior-graded case SHALL keep its oracle out of the fixture, in a
`verify/` directory at `evals/cases/<name>/`, which the runner copies into the
scratch repository only after the session has ended. Before copying, the runner
SHALL restore the case's shipped `fixture/tests/` tree over the scratch copy, so
a session's edits to a shipped test cannot affect the grade. The runner SHALL
then run `python3 -m unittest discover -s tests` with the scratch root as
working directory, and the run SHALL pass only if that command exits 0. The
grader SHALL NOT assert that the session added a test of its own.

#### Scenario: A correct fix passes
- **WHEN** the session repairs the seeded bug and the restored suite plus the
  held-out test all pass
- **THEN** the run is graded as passed

#### Scenario: An unfixed bug fails
- **WHEN** the session ends without repairing the seeded bug
- **THEN** the held-out test fails, the discover command exits non-zero, and the
  run is graded as failed

#### Scenario: Collateral breakage fails the run
- **WHEN** the session repairs the seeded bug but breaks a test the fixture
  shipped green
- **THEN** the discover command exits non-zero and the run is graded as failed

#### Scenario: Weakening a shipped test cannot rescue a run
- **WHEN** the session edits or deletes a test the fixture shipped and leaves
  the seeded bug in place
- **THEN** the restore reverts that edit before grading and the run is graded as
  failed

#### Scenario: No assertion is made about an added test
- **WHEN** the session repairs the seeded bug without adding a regression test
  of its own
- **THEN** the run is graded as passed

### Requirement: Behavior fixture sanity check
id: behavior-fixture-sanity

When assembling the scratch repository for a behavior-graded case, the runner
SHALL verify the fixture is correctly seeded: the shipped suite SHALL exit 0
before the session runs, and the suite SHALL exit non-zero once the case's
`verify/` tree is copied in. If either check does not hold, then the runner
SHALL record the run as failed, naming which check failed, and SHALL NOT spawn a
session.

#### Scenario: An unseeded fixture fails before the session
- **WHEN** a behavior case's held-out test already passes against the fixture's
  original code
- **THEN** the run is recorded as failed naming the sanity check, and no session
  is spawned

#### Scenario: A fixture shipping a red suite fails before the session
- **WHEN** a behavior case's own shipped suite does not exit 0 against the
  fixture's original code
- **THEN** the run is recorded as failed naming the sanity check, and no session
  is spawned

### Requirement: Grader-aware conversation driving
id: grader-aware-driving

While driving a behavior-graded case, the runner SHALL gate its resume loop on
that case's own grader and SHALL send a resume reply appropriate to the skill
under test, never the plan-specific reply that instructs a session to complete
an emission, lint, and promotion to `ready`. The behavior gate SHALL evaluate a
throwaway copy of the scratch repository, so the held-out `verify/` tree is
never copied into the working tree the session is still operating in.

#### Scenario: A behavior case is not gated on the structural grade
- **WHEN** a behavior-graded session has repaired the seeded bug on its first
  turn
- **THEN** the resume loop stops without spending further turns, rather than
  exhausting the resume cap against a structural condition the session can
  never satisfy

#### Scenario: The resume reply suits the skill under test
- **WHEN** a behavior-graded session is resumed
- **THEN** the reply sent carries no instruction to emit a change, lint it, or
  promote it to `ready`

#### Scenario: The gate never leaks the held-out oracle
- **WHEN** the resume gate evaluates a behavior-graded run mid-conversation
- **THEN** the scratch repository the session works in contains no file from
  the case's `verify/` tree

### Requirement: Eval tests run in CI
id: evals-ci-discovery

The eval harness's own unit tests SHALL be written against the Python standard
library's `unittest`, with no third-party test dependency, and the repository's
CI workflow (`.github/workflows/ci.yml`) SHALL carry a step running
`python3 -m unittest discover -s evals/tests`. If any eval harness unit test
fails, then that step SHALL fail with a non-zero exit.

#### Scenario: CI discovers the eval harness tests
- **WHEN** the CI workflow runs
- **THEN** a step runs `python3 -m unittest discover -s evals/tests` and its
  failure fails the job

#### Scenario: The suite needs nothing installed
- **WHEN** `python3 -m unittest discover -s evals/tests` runs on a checkout with
  no third-party packages installed
- **THEN** the suite executes without an import error

## MODIFIED Requirements

### Requirement: Deterministic structural grading
id: deterministic-grading
base: 1fad5369f8de

Structural grading SHALL be the default grader, applied to every case that does
not select another (see the case-grader-selection requirement). After a session
completes, the structural grader SHALL grade the scratch repository with
assertions over both storage locations the workflow sanctions: exactly one
change directory SHALL exist across the scratch root's `.shipd/planned/` and one
level of `.worktrees/*/.shipd/planned/` combined; the host repo's
`spec_lint.py` SHALL exit 0 for that change with `--root` pointing at the tree
the change lives in (the scratch root, or the containing worktree); and the
produced `plan.md` SHALL carry `Status: ready`. A run SHALL pass only if all
assertions hold, and a failing assertion SHALL name the locations inspected.

#### Scenario: Root change still passes
- **WHEN** a session leaves one lint-clean `ready` change under the scratch
  root's `.shipd/planned/`
- **THEN** the run is graded as passed

#### Scenario: Worktree change passes
- **WHEN** a session follows the worktree convention, leaving its only change
  under `<scratch>/.worktrees/<change>/.shipd/planned/` lint-clean at
  `Status: ready`
- **THEN** the run is graded as passed

#### Scenario: Structural violations fail the run
- **WHEN** the session produced no change anywhere, more than one change across
  the locations combined, a lint failure, or a plan not promoted to `ready`
- **THEN** the run is graded as failed and the failing assertion names the
  inspected locations

#### Scenario: The existing plan cases are unaffected
- **WHEN** a case carrying no `expect.json` runs
- **THEN** it is graded by these assertions exactly as before
