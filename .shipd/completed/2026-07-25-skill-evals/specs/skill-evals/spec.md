# skill-evals — delta

## ADDED Requirements

### Requirement: Eval case layout and discovery
id: eval-case-layout

The system SHALL define an eval case as a directory under `evals/cases/<name>/`
containing `prompt.md` (the user request given to the headless session) and
`fixture/` (a minimal repository tree with an `am/` layout), and the runner
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
the fixture (copy to a temp directory, overwrite `am/README.md` with the host
repo's copy, initialize a git repo with an initial commit) and SHALL run a
headless Claude Code session with the scratch directory as working directory,
loading the host repo's plugin sources via `--plugin-dir`. The session SHALL
run with `--permission-mode bypassPermissions`, `--output-format json`, and a
timeout, and the runner SHALL save the session transcript into the scratch
directory. If the session times out or the CLI exits non-zero, then the runner
SHALL record that run as failed rather than aborting the whole eval.

#### Scenario: Session runs against the working tree's plugin
- **WHEN** a case run starts
- **THEN** the `claude` invocation includes `--plugin-dir` pointing at the host
  repo's `plugins/am`, so the session executes the skill sources currently
  under edit, not the cached plugin snapshot

#### Scenario: Fixture is isolated from the host repo
- **WHEN** a case run starts
- **THEN** the session's working directory is a fresh temp copy of the fixture
  with its own git history, and the host repository is not the session cwd

#### Scenario: A crashed session fails only its own run
- **WHEN** the CLI exits non-zero or exceeds the timeout during one run
- **THEN** that run is recorded as failed and the runner proceeds to the
  remaining runs and cases

### Requirement: Deterministic structural grading
id: deterministic-grading

After a session completes, the runner SHALL grade the scratch repository with
structural assertions: exactly one change directory exists under
`am/planned/`, the host repo's `spec_lint.py` exits 0 for that change with
`--root` pointing at the scratch directory, and the produced `plan.md` carries
`Status: ready`. A run SHALL pass only if all assertions hold.

#### Scenario: Lint-clean ready plan passes
- **WHEN** a session leaves one change under `am/planned/` that lints clean
  and whose `plan.md` says `Status: ready`
- **THEN** the run is graded as passed

#### Scenario: Structural violations fail the run
- **WHEN** the session produced no change, more than one change, a lint
  failure, or a plan not promoted to `ready`
- **THEN** the run is graded as failed and the failing assertion is named in
  the runner output

### Requirement: Pass-rate reporting and exit code
id: pass-rate-reporting

The runner SHALL support `--runs N` (default 1) to repeat each case N times,
SHALL print a per-case pass-rate summary, and SHALL exit non-zero if any
case's pass-rate is below 1.0.

#### Scenario: Repeated runs report a pass-rate
- **WHEN** `evals/run.py --runs 3` executes a case that passes twice and fails
  once
- **THEN** the summary reports the case at 2/3 and the runner exits non-zero

#### Scenario: All-green run exits zero
- **WHEN** every run of every executed case passes
- **THEN** the runner exits 0
