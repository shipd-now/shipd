## MODIFIED Requirements

### Requirement: Headless skill session per run
id: headless-skill-run
base: 501333871214

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
  host repo's `plugins/am`, so the session executes the skill sources
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
