# skill-evals

### Requirement: Eval case layout and discovery
id: eval-case-layout

The system SHALL define an eval case as a directory under `evals/cases/<name>/`
containing `prompt.md` (the user request given to the headless session) and
`fixture/` (a minimal repository tree with a `.shipd/` layout), and the runner
SHALL discover all cases automatically from that directory. When invoked with
`--case <name>`, the runner SHALL run only the named case.

#### Scenario: Cases are discovered from the cases directory
- **WHEN** `evals/run.py` is invoked with no case filter
- **THEN** every directory under `evals/cases/` containing `prompt.md` and
  `fixture/` is executed as one eval case

#### Scenario: A single case can be selected
- **WHEN** `evals/run.py --case plan-csv-export` is invoked
- **THEN** only the `plan-csv-export` case runs

### Requirement: Headless skill session per run
id: headless-skill-run

When executing a case, the runner SHALL assemble an isolated scratch copy of
the fixture (copy to a temp directory, overwrite `.shipd/README.md` with the
host repo's copy, initialize a git repo with an initial commit) and SHALL
drive a headless Claude Code session as a bounded conversation with the
scratch directory as working directory, loading the host repo's plugin
sources via `--plugin-dir`. The initial turn SHALL send the case prompt;
afterwards, while the structural grade has not passed and a configurable
resume cap (default 4) is not exhausted, the runner SHALL resume the same
session — `--resume` with the `session_id` parsed from the previous turn's
JSON transcript — with a fixed generic reply that proceeds and takes the
session's own recommended option on any open question or decision. Every
turn SHALL run with `--permission-mode bypassPermissions`,
`--output-format json`, and a timeout, and the runner SHALL save each
turn's transcript into the scratch directory. If any turn times out or the
CLI exits non-zero, then the runner SHALL record that run as failed rather
than aborting the whole eval; if a transcript yields no session id, the
runner SHALL stop resuming and let the final grade decide the run.

#### Scenario: Session runs against the working tree's plugin
- **WHEN** a case run starts
- **THEN** the `claude` invocation includes `--plugin-dir` pointing at the
  host repo's `plugins/s`, so the session executes the skill sources
  currently under edit, not the cached plugin snapshot

#### Scenario: Fixture is isolated from the host repo
- **WHEN** a case run starts
- **THEN** the session's working directory is a fresh temp copy of the
  fixture with its own git history, and the host repository is not the
  session cwd

#### Scenario: Checkpoint stop is driven through by resuming
- **WHEN** the initial turn ends at the plan skill's findings checkpoint
  with no change yet under `.shipd/planned/`
- **THEN** the runner resumes the same session with the generic proceed
  reply and re-grades after the resumed turn

#### Scenario: Resume cap bounds the conversation
- **WHEN** the resume cap is exhausted without the grade passing
- **THEN** the run is recorded as failed with the structural grading
  failure, and no further turns are spawned

#### Scenario: A crashed session fails only its own run
- **WHEN** the CLI exits non-zero or exceeds the timeout during any turn of
  one run
- **THEN** that run is recorded as failed and the runner proceeds to the
  remaining runs and cases

### Requirement: Deterministic structural grading
id: deterministic-grading

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

### Requirement: Pass-rate reporting and exit code
id: pass-rate-reporting

The runner SHALL support `--runs N` (default 1) to repeat each case N times,
SHALL print a per-case pass-rate summary carrying one row per case and no arm
label, and SHALL exit non-zero if any case's pass-rate is below 1.0.

#### Scenario: Repeated runs report a pass-rate
- **WHEN** `evals/run.py --runs 3` executes a case that passes twice and fails
  once
- **THEN** the summary reports the case at 2/3 and the runner exits non-zero

#### Scenario: All-green run exits zero
- **WHEN** every run of every executed case passes
- **THEN** the runner exits 0

#### Scenario: One row per case
- **WHEN** the summary is printed
- **THEN** each executed case contributes exactly one pass-rate row, carrying no
  arm label

### Requirement: Per-case grader selection
id: case-grader-selection

An eval case MAY carry an `expect.json` file at `evals/cases/<name>/` declaring
which grader scores its runs, via a `grader` key whose recognized values are
`structural`, `behavior`, and `handoff`. Where the file is absent, or present
without a `grader` key, the runner SHALL grade the case structurally. A
`handoff` grader additionally requires a `handoff_requirement` key naming the
requirement id its grader looks for. If `expect.json` is unreadable, declares an
unrecognized grader, or declares `handoff` without `handoff_requirement`, then
the runner SHALL record the run as failed and name the offending case and value.

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

#### Scenario: A handoff grader without its requirement fails the run
- **WHEN** a case declares `{"grader": "handoff"}` and no `handoff_requirement`
- **THEN** the run is recorded as failed naming the case and the missing key,
  and no session is spawned

#### Scenario: An unrecognized grader fails the run
- **WHEN** a case's `expect.json` declares a grader value outside the recognized
  set
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

### Requirement: Handoff grading for a wrong-specification case
id: handoff-grading

The runner SHALL support a `handoff` grader for a case whose correct outcome is
that no code changes. Immediately after assembling the scratch repository and
before any session runs, the runner SHALL snapshot the scratch tree. A
handoff-graded run SHALL pass only when all four of these hold: no file present
in that snapshot was modified or deleted; no file absent from it has appeared
under `src/`, or under any `.shipd/verified/` or `.shipd/planned/` directory
anywhere in the scratch, including inside a worktree; the shipped suite exits 0;
and the session's final result text contains the requirement id the case
declares as `handoff_requirement`. A new file created anywhere else SHALL NOT
fail the run, because assembly and the engine's own tooling legitimately create
files no session authored. The grader SHALL NOT assert that the session named
any particular skill, command, or hand-off destination.

#### Scenario: A correct hand-off passes through the real assembly path
- **WHEN** a scratch repository assembled by the runner's own assembly step is
  left with no snapshotted file modified, no authored file added, the shipped
  suite green, and the declared requirement id named in the session's final text
- **THEN** the run is graded as passed

#### Scenario: Engine scaffolding does not fail a run
- **WHEN** a session leaves the snapshotted files intact but tooling has created
  new entries outside `src/` and the content directory's `verified/` and
  `planned/` directories
- **THEN** the run is graded as passed, and no such entry is reported as a change

#### Scenario: Patching the code fails the run
- **WHEN** a session edits `src/report.py` to widen the column
- **THEN** the run is graded as failed, naming `src/report.py`

#### Scenario: Adding a module fails the run
- **WHEN** a session leaves `src/report.py` intact but adds a new file under
  `src/`
- **THEN** the run is graded as failed, naming that new file

#### Scenario: Editing the specification fails the run
- **WHEN** a session edits the content directory's `report-output` spec
- **THEN** the run is graded as failed, naming that spec's path

#### Scenario: Authoring a planned change fails the run, in a worktree too
- **WHEN** a session leaves the code and the documented behavior intact but
  writes a planned change under a `.shipd/planned/` directory, whether at the
  scratch root or inside a worktree it created
- **THEN** the run is graded as failed, naming a path under that directory

#### Scenario: Weakening a shipped test fails the run
- **WHEN** a session rewrites a test the fixture shipped
- **THEN** the run is graded as failed, because that file was present in the
  snapshot and has been modified

#### Scenario: Silence fails the run
- **WHEN** a session changes nothing and its final text does not name the
  declared requirement id
- **THEN** the run is graded as failed, naming the missing requirement id

#### Scenario: Naming the destination skill is not required
- **WHEN** a session hands off correctly, names the declared requirement id, and
  never mentions `/s:plan`
- **THEN** the run is graded as passed

### Requirement: Handoff fixture sanity check
id: handoff-fixture-sanity

When assembling the scratch repository for a handoff-graded case, the runner
SHALL verify the shipped suite exits 0 before the session runs, since the code
is expected to implement its documented contract faithfully. If it does not,
then the runner SHALL record the run as failed, naming the check, and SHALL NOT
spawn a session.

#### Scenario: A red shipped suite fails before the session
- **WHEN** a handoff case's shipped suite does not exit 0 against the fixture's
  original code
- **THEN** the run is recorded as failed naming the sanity check, and no session
  is spawned

### Requirement: Grader-selected gate and reply
id: grader-selected-driving

The runner SHALL select a conversation's resume gate and resume reply from the
case's own grader, covering every recognized grader rather than branching one
grader against all others. A handoff-graded case SHALL NOT be resumed at all:
its correct outcome is that the session stops, so the run ends after the first
turn and is graded there. If a grader is added without its own gate and reply,
then the runner SHALL fail the run naming that grader rather than falling back
to another grader's driving behavior.

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

#### Scenario: An undriveable grader fails loudly
- **WHEN** a case declares a grader for which no gate and reply are defined
- **THEN** the run is recorded as failed naming that grader, rather than driven
  with another grader's gate or reply
