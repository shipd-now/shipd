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

After a session completes, the runner SHALL grade the scratch repository
with structural assertions over both storage locations the workflow
sanctions: exactly one change directory SHALL exist across the scratch
root's `.shipd/planned/` and one level of `.worktrees/*/.shipd/planned/`
combined; the host repo's `spec_lint.py` SHALL exit 0 for that change
with `--root` pointing at the tree the change lives in (the scratch root,
or the containing worktree); and the produced `plan.md` SHALL carry
`Status: ready`. A run SHALL pass only if all assertions hold, and a
failing assertion SHALL name the locations inspected.

#### Scenario: Root change still passes
- **WHEN** a session leaves one lint-clean `ready` change under the
  scratch root's `.shipd/planned/`
- **THEN** the run is graded as passed

#### Scenario: Worktree change passes
- **WHEN** a session follows the worktree convention, leaving its only
  change under `<scratch>/.worktrees/<change>/.shipd/planned/` lint-clean at
  `Status: ready`
- **THEN** the run is graded as passed

#### Scenario: Structural violations fail the run
- **WHEN** the session produced no change anywhere, more than one change
  across the locations combined, a lint failure, or a plan not promoted
  to `ready`
- **THEN** the run is graded as failed and the failing assertion names
  the inspected locations

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
