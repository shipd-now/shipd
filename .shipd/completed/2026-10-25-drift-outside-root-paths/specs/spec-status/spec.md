## MODIFIED Requirements

### Requirement: Drift verb
id: drift-verb
base: 34a7fcc2d321

The status CLI SHALL provide `drift [change] [--base <ref>] [--json]`,
measuring from local git alone whether a planned change still matches the
code it was gated against, without writing anything. The verb SHALL take
the plan's `Planned-at` stamp as the measuring point and, when the plan
carries none, the last commit that touched its `plan.md`; it SHALL resolve
the base ref (default `main`) once, anchoring every git call on the root
hosting the change. It SHALL extract cited paths (path-shaped backticked
tokens, a trailing `:<line>[-<line>]` citation stripped, `artefacts/`
references, the version-bump exempt paths, and any path that is absolute
or whose normalized form escapes the hosting root through `..` dropped) and
cited symbols
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

#### Scenario: A path outside the repository never fails the run
- **GIVEN** a stamped plan citing `src/engine.py`, `../scripts`,
  `../../docs/x/doc.md`, and an absolute path outside the repository, and a
  later commit editing `src/engine.py`
- **WHEN** `drift <change>` runs
- **THEN** a `file-drift src/engine.py 1 (<sha>)` line prints, no line names
  any of the outside paths, no `Error:` line prints, and the exit code is 4

#### Scenario: JSON is one object
- **WHEN** `drift <change> --json` runs on a drifted change
- **THEN** stdout parses as one object whose `findings` carry a
  `file-drift` entry with `path` and `commits`, and the exit code is 4

#### Scenario: The verb never writes
- **WHEN** `drift <change>` runs with any mix of findings
- **THEN** no file under the content directory or the change directory is
  modified
