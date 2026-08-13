## MODIFIED Requirements

### Requirement: Deterministic structural grading
id: deterministic-grading
base: 595cc84cae2b

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
