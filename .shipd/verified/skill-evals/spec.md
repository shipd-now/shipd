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

The runner SHALL support `--runs N` (default 1) to repeat each case N times and
SHALL print a per-case pass-rate summary. Where more than one arm ran, the
summary SHALL report each arm's pass rate on its own labelled row for every
case. The runner SHALL exit non-zero if any case's **treatment** pass-rate is
below 1.0, and the pass rate of a baseline arm that actually ran SHALL NOT
affect the exit code — a failing baseline is the expected result of a working
comparison, not a regression in the harness. A refused run is not such a
result: it exits non-zero, because nothing was measured.

#### Scenario: Repeated runs report a pass-rate
- **WHEN** `evals/run.py --runs 3` executes a case that passes twice and fails
  once
- **THEN** the summary reports the case at 2/3 and the runner exits non-zero

#### Scenario: All-green run exits zero
- **WHEN** every run of every executed case passes
- **THEN** the runner exits 0

#### Scenario: Both arms are reported separately
- **WHEN** a case runs under `--arm both`
- **THEN** the summary carries one labelled pass-rate row per arm for that case

#### Scenario: A failing baseline does not fail the harness
- **WHEN** a case runs under `--arm both` with every treatment run passing and
  every baseline run failing
- **THEN** both rates are reported and the runner exits 0

#### Scenario: A refused run exits non-zero
- **WHEN** a baseline arm is refused, because the case grades structurally or
  its prompt carries no skill token
- **THEN** the runner exits non-zero, even though no treatment arm ran

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

### Requirement: Arm selection
id: arm-selection

The runner SHALL accept `--arm` with the values `treatment`, `baseline`, and
`both`, defaulting to `treatment`. Where the arm is `treatment`, a run SHALL
load the host repo's plugin exactly as it does today. Where the arm is
`baseline`, a run SHALL omit `--plugin-dir` from the session invocation and
SHALL change nothing else about it — the same fixture, content directory,
permission mode, timeout, resume cap, and grader. Where the arm is `both`, the
runner SHALL execute `--runs N` runs of each arm for every selected case.

#### Scenario: The default arm is unchanged behavior
- **WHEN** `evals/run.py` runs with no `--arm` flag
- **THEN** every session loads the plugin via `--plugin-dir`, exactly as before

#### Scenario: The baseline arm omits only the plugin
- **WHEN** a run executes under `--arm baseline`
- **THEN** the session command carries no `--plugin-dir` argument, and its
  working directory, permission mode, and timeout are those the treatment arm
  would have used

#### Scenario: Both arms run under the combined arm
- **WHEN** `evals/run.py --case fix-report-drift --runs 3 --arm both` is invoked
- **THEN** three treatment runs and three baseline runs are executed for that
  case

### Requirement: Derived baseline prompt
id: derived-baseline-prompt

The runner SHALL derive a baseline run's prompt from the case's own
`prompt.md` by removing a leading `/s:<skill>` token from its first line and
using the remainder verbatim, so both arms receive identical wording. The
runner SHALL NOT read any separately authored baseline prompt file. If a case's
`prompt.md` carries no leading `/s:<skill>` token, then a baseline run of that
case SHALL be recorded as failed, naming the case, SHALL NOT spawn a session,
and SHALL exit non-zero — a refusal means nothing was measured, which is a
usage error rather than a baseline result.

#### Scenario: The skill token is stripped and the rest kept verbatim
- **WHEN** a case's `prompt.md` begins `/s:fix The report CLI prints its rows
  in the wrong order.`
- **THEN** the baseline prompt is `The report CLI prints its rows in the wrong
  order.` followed by the remainder of the file unchanged

#### Scenario: A prompt without a skill token fails the baseline run
- **WHEN** a baseline run is requested for a case whose `prompt.md` opens with
  no `/s:` token
- **THEN** the run is recorded as failed naming the case, and no session is
  spawned

#### Scenario: The treatment prompt is untouched
- **WHEN** a treatment run executes
- **THEN** the prompt sent is the case's `prompt.md` content unmodified,
  including its `/s:` token

### Requirement: Baseline arm requires a behavior-graded case
id: baseline-requires-behavior

If a `baseline` or `both` arm is requested for a case whose grader is
`structural`, then the runner SHALL record the run as failed, naming the case
and its grader, SHALL NOT spawn a session, and SHALL exit non-zero — a refusal
means nothing was measured, which is a usage error rather than a baseline
result. Structural grading asserts
artifacts that only the plugin's skills produce, so a baseline arm could never
pass and the comparison would carry no information.

#### Scenario: A structural case refuses the baseline arm
- **WHEN** `evals/run.py --case plan-csv-export --arm baseline` is invoked
- **THEN** the run is recorded as failed naming the case and its structural
  grader, and no session is spawned

#### Scenario: The combined arm is refused whole on a structural case
- **WHEN** `evals/run.py --case plan-csv-export --arm both` is invoked
- **THEN** the invocation is refused before either arm executes, so no session
  spawns for the treatment arm either, and the runner exits non-zero

#### Scenario: A behavior case accepts the baseline arm
- **WHEN** `evals/run.py --case fix-report-drift --arm baseline` is invoked
- **THEN** the run proceeds and is graded by the behavior grader

### Requirement: Handoff grading for a wrong-specification case
id: handoff-grading

The runner SHALL support a `handoff` grader for a case whose correct outcome is
that no code changes. Immediately after assembling the scratch repository and
before any session runs, the runner SHALL snapshot the scratch `src/` tree and
the scratch content directory. A handoff-graded run SHALL pass only when all
four of these hold: the scratch `src/` matches that pre-session snapshot; the
scratch content directory matches that pre-session snapshot; the shipped suite
exits 0; and the session's final result text contains the requirement id the
case declares as `handoff_requirement`. The comparison SHALL be against the
pre-session snapshot rather than the case's `fixture/`, because assembly
legitimately injects files the fixture does not ship — the grader asks what the
session changed, never how the scratch differs from the fixture. The grader
SHALL NOT assert that the session named any particular skill, command, or
hand-off destination.

#### Scenario: A correct hand-off passes through the real assembly path
- **WHEN** a scratch repository assembled by the runner's own assembly step is
  left with `src/` and the content directory untouched, the shipped suite green,
  and the declared requirement id named in the session's final text
- **THEN** the run is graded as passed, and no file the assembly step itself
  injected is counted as a session change

#### Scenario: Patching the code fails the run
- **WHEN** a session edits `src/report.py` to widen the column
- **THEN** the run is graded as failed, naming `src/report.py` as the changed
  path

#### Scenario: Editing the specification fails the run
- **WHEN** a session edits the content directory's `report-output` spec to
  correct the documented width
- **THEN** the run is graded as failed, naming that spec's path as the changed
  path, and not some other file of the content directory

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

### Requirement: Handoff cases accept both arms
id: handoff-accepts-arms

A handoff-graded case SHALL accept the `baseline` and `both` arms, since its
grader asserts an outcome either arm can reach. The runner SHALL refuse a
baseline-bearing arm for a `structural` case only.

#### Scenario: A handoff case runs under the combined arm
- **WHEN** `evals/run.py --case fix-spec-wrong --arm both` is invoked
- **THEN** both arms execute and neither is refused for its grader
