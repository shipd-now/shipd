## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Per-case grader selection
id: case-grader-selection
base: c922501e9a82

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
