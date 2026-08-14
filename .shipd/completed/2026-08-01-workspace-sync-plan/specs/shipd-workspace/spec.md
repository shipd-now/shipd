## ADDED Requirements

### Requirement: Sync materialization planning
id: sync-materialization-planning

The engine SHALL compute a deterministic per-member materialization plan
from the workspace manifest, the resolved configuration, and local disk
state, using only local git probes and never the network. For a member
whose destination exists as a git work tree the plan SHALL record action
`none`, adding a drift note when the destination's origin URL differs from
the manifest `url`; an existing non-git destination SHALL be recorded as
occupied with a drift note and never modified. For an absent member the
plan SHALL choose the cheapest rung: a work-tree candidate clone (an
immediate child of a `clone_sources` directory whose origin URL equals the
manifest `url`, first match in list order) yields action `worktree`; a bare
candidate yields action `reference-clone`; no candidate with a `url` yields
action `clone`; no `url` yields action `unmaterializable` with a reason.
Actions carrying a rung SHALL include an advisory command string; the
planner SHALL never execute one. The plan SHALL also compare the marked
member-repos gitignore block against the manifest's member paths and record
the missing or stale lines.

#### Scenario: Absent member with a local work-tree candidate
- **GIVEN** a manifest entry with a `url` and a `clone_sources` directory
  containing a clone whose origin equals that url
- **WHEN** the plan is computed
- **THEN** the member's action is `worktree` naming that candidate as the
  source with an advisory `git worktree add` command

#### Scenario: Absent member with no candidate falls to clone
- **GIVEN** a manifest entry with a `url` and no matching local candidate
- **WHEN** the plan is computed
- **THEN** the member's action is `clone` carrying the manifest url

#### Scenario: Present member with a mismatched origin drifts
- **GIVEN** a member present on disk whose origin URL differs from the
  manifest `url`
- **WHEN** the plan is computed
- **THEN** the action is `none` and the record carries a drift note naming
  both URLs, and nothing on disk is modified

#### Scenario: Absent member without a url is unmaterializable
- **GIVEN** a path-only manifest entry that is absent on disk
- **WHEN** the plan is computed
- **THEN** the member's action is `unmaterializable` with a reason naming
  the missing url

#### Scenario: Gitignore block gaps are reported
- **GIVEN** a workspace whose marked member block lacks a manifest member
  path
- **WHEN** the plan is computed
- **THEN** the gitignore record lists that path as missing
