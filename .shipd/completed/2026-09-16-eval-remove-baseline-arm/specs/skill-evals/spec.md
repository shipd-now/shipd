## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Arm selection
id: arm-selection
base: a9ef34c116cd
Reason: The baseline arm measures nothing, because assembly injects the shipd grammar authority into every fixture and a plugin-less session used it to author a complete change.
Migration: `--arm` is removed and every run loads the plugin as the treatment arm did; no case, grader, or fixture changes, and `--runs` is unaffected.

### Requirement: Derived baseline prompt
id: derived-baseline-prompt
base: 5ec250640e55
Reason: The derivation exists only to give the removed baseline arm a prompt at parity with the treatment arm's.
Migration: `baseline_prompt` is removed and every run sends the case's `prompt.md` unmodified, including its `/s:` token.

### Requirement: Baseline arm requires a behavior-graded case
id: baseline-requires-behavior
base: ed9e75c7b9bb
Reason: The refusals guard an arm that no longer exists, their only purpose being to stop an invocation that could carry no information.
Migration: `_arm_refusal` and the refused-run bookkeeping are removed, so a structural case runs normally as it did before the arm existed.

### Requirement: Handoff cases accept both arms
id: handoff-accepts-arms
base: 38d3aa0e4cc2
Reason: The requirement exists only to say a handoff case is exempt from the baseline-arm refusal, and its scenario invokes a `--arm both` flag this change removes, so merging without it would leave the master documenting a flag no code provides.
Migration: Nothing replaces it; with no arms left there is no refusal to be exempt from, and every case runs the single arm that remains.

## MODIFIED Requirements

### Requirement: Pass-rate reporting and exit code
id: pass-rate-reporting
base: 3e09b50a9206
Dropped: Both arms are reported separately
Dropped: A failing baseline does not fail the harness
Dropped: A refused run exits non-zero

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

### Requirement: Handoff grading for a wrong-specification case
id: handoff-grading
base: 5882112adbef

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

The `.shipd` segment in the new-file check above is a literal name match, not
a resolution of a fixture's configured content directory (the `dir` key a
`.shipd-config.json` may set to something other than `.shipd`). A fixture
that configures a different content-directory name therefore gets no
new-file protection for a newly added specification file under that
directory — only for `src/`, which is unaffected by this configuration. The
modified-or-deleted rule is unaffected by this gap: an existing spec file's
edit or deletion is still caught regardless of the content directory's name,
since that comparison walks the whole snapshot rather than matching a
literal path segment.

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
