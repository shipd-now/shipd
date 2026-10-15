## ADDED Requirements

### Requirement: Drift verb
id: drift-verb

The status CLI SHALL provide `drift [change] [--base <ref>] [--json]`,
measuring from local git alone whether a planned change still matches the
code it was gated against, without writing anything. The verb SHALL take
the plan's `Planned-at` stamp as the measuring point and, when the plan
carries none, the last commit that touched its `plan.md`; it SHALL resolve
the base ref (default `main`) once, anchoring every git call on the root
hosting the change. It SHALL extract cited paths (path-shaped backticked
tokens, a trailing `:<line>[-<line>]` citation stripped, `artefacts/`
references and the version-bump exempt paths dropped) and cited symbols
(backticked identifiers, dotted names, and `--flags` that are not
path-shaped) from `plan.md`, `tasks.md`, and every delta spec, and report
three finding kinds: `file-drift <path> <n> (<sha>, ...)` for each cited
path with at least one commit in `<stamp>..<base>`; `symbol-gone <name>`
for each cited symbol `git grep` finds at the stamp and not at the base;
and `stale-base <capability>/<id> (expected <a>, actual <b>)`, computed
through the same primitives `check-base` uses. Text output SHALL print a
keyed header (`change:`, `root:`, `planned-at: <sha> (stamp|plan-commit)`,
`base: <ref> <sha>`), the finding lines, then a summary line; `--json`
SHALL emit one object with `change`, `root`, `planned_at`, `stamp_source`,
`base` (`ref`, `sha`), and `findings` (each with `kind` and its fields).
The verb SHALL exit 0 when clean and 4 when at least one finding exists. If
the base ref is unresolvable, the change has no plan, the stamp sha is
absent from the repository, or the plan has neither a stamp nor a commit,
then the verb SHALL exit 1 with an `Error:` line naming the cause and the
remedy. The verb SHALL NOT compare `Gated-hash`, SHALL NOT read file
timestamps, and SHALL NOT run a model or touch the network.

#### Scenario: A commit touching a cited file is file drift
- **GIVEN** a stamped plan citing `src/engine.py` and a later commit on
  `main` editing that file
- **WHEN** `drift <change>` runs
- **THEN** a `file-drift src/engine.py 1 (<sha>)` line prints and the exit
  code is 4

#### Scenario: A symbol removed since the stamp is gone
- **GIVEN** a plan citing `old_helper` and `kept`, where a commit after the
  stamp deleted `old_helper` from the tree and left `kept`
- **WHEN** `drift <change>` runs
- **THEN** `symbol-gone old_helper` prints, no line names `kept`, and the
  exit code is 4

#### Scenario: A symbol the plan introduces is never gone
- **GIVEN** a plan citing `new_verb`, absent from the tree at the stamp and
  at the base
- **WHEN** `drift <change>` runs
- **THEN** no `symbol-gone` line prints

#### Scenario: No commit since the stamp is clean
- **GIVEN** a stamped plan whose cited files have no commit in
  `<stamp>..main`
- **WHEN** `drift <change>` runs
- **THEN** the summary reads `drift: clean (no findings).` and the exit code
  is 0

#### Scenario: The version-bump file is exempt
- **GIVEN** a plan citing `plugins/s/.claude-plugin/plugin.json` and a
  commit after the stamp touching only that file
- **WHEN** `drift <change>` runs
- **THEN** no `file-drift` line prints and the exit code is 0

#### Scenario: Stale base rides along
- **GIVEN** a plan whose MODIFIED entry's `base:` no longer matches the
  master requirement's content hash
- **WHEN** `drift <change>` runs
- **THEN** a `stale-base <capability>/<id> (expected ..., actual ...)` line
  prints with the hashes `check-base` reports

#### Scenario: An unstamped plan falls back to its last commit
- **GIVEN** a committed plan with no `Planned-at` line
- **WHEN** `drift <change>` runs
- **THEN** the header reads `planned-at: <sha of the plan's last commit>
  (plan-commit)` and drift is measured from that commit

#### Scenario: An unmeasurable plan is an error, not a finding
- **GIVEN** a plan with no `Planned-at` line that no commit has touched
- **WHEN** `drift <change>` runs
- **THEN** stderr carries an `Error:` line naming the missing stamp and
  `spec_gate.py <change>`, and the exit code is 1

#### Scenario: JSON is one object
- **WHEN** `drift <change> --json` runs on a drifted change
- **THEN** stdout parses as one object whose `findings` carry a
  `file-drift` entry with `path` and `commits`, and the exit code is 4

#### Scenario: The verb never writes
- **WHEN** `drift <change>` runs with any mix of findings
- **THEN** no file under the content directory or the change directory is
  modified

### Requirement: Drift over an epic
id: drift-epic-mode

`drift --epic <slug> [--base <ref>] [--json]` SHALL resolve the epic across
the invocation root and its worktrees (the epic surfaces' hosting-root
probe), walk every `## Changes` stub member in table order, and measure
each member whose state is a plan status from the root hosting that
member's plan, exactly as the single-change form does. A member whose state
is `unplanned` or `archived`, or whose plan cannot be measured (no stamp
and no commit, or a stamp sha absent from the repository), SHALL be
reported as skipped with that reason — `skipped: <slug> (<reason>)` in text,
an entry of the JSON `skipped` array — and SHALL count as no finding. Text
output SHALL print one single-change block per measured member separated by
a blank line, then the skipped lines, then the summary; `--json` SHALL emit
one object with `epic`, `base`, `members` (the single-change objects), and
`skipped` (`member`, `reason`). The verb SHALL exit 4 when any member has a
finding and 0 otherwise; giving both a change and `--epic` SHALL be a usage
error (exit 2), and an epic found nowhere SHALL exit 1.

#### Scenario: Members are measured from their hosting roots
- **GIVEN** an epic with one drifted member planned under the invocation
  root, one clean member planned only under `.worktrees/<name>/`, and one
  unplanned member
- **WHEN** `drift --epic <slug>` runs from the invocation root
- **THEN** two member blocks print with their `root:` lines naming the
  hosting roots, `skipped: <member> (unplanned)` prints, and the exit code
  is 4

#### Scenario: A skipped member is not a finding
- **GIVEN** an epic whose only planned member has no stamp and an
  uncommitted `plan.md`
- **WHEN** `drift --epic <slug>` runs
- **THEN** `skipped: <member> (no-stamp)` prints, the summary reports clean,
  and the exit code is 0

#### Scenario: Epic JSON carries members and skipped
- **WHEN** `drift --epic <slug> --json` runs
- **THEN** stdout parses as one object with `epic`, `base`, a `members`
  array of single-change objects, and a `skipped` array

#### Scenario: Both forms at once is a usage error
- **WHEN** `drift <change> --epic <slug>` runs
- **THEN** usage is printed on stderr and the exit code is 2
