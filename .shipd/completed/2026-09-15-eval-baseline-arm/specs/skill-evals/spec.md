## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Pass-rate reporting and exit code
id: pass-rate-reporting
base: 055ba08cbae5

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
