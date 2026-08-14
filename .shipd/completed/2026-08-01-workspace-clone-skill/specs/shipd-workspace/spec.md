## MODIFIED Requirements

### Requirement: Workspace setup skill
id: workspace-setup-skill
base: f5b4aa8a2240

An `/s:workspace` skill SHALL provide, selected by argument: `init` — guided
workspace creation that, when a workspace root is already discoverable,
reports that root and stops; otherwise asks the user in a single question
round to choose the target root (the repository's parent directory offered
as the recommended default, the repository root as the alternative) and
whether to seed the root as a portable git workspace (plain init the
recommended default), then drives the status CLI's `workspace-init` verb —
with `--git` when seeding was chosen — reporting the created root; `show` —
the workspace roster via the status CLI's `workspace-show` verb, reading
only; `clone <url> [dest]` — bootstrap a job workspace from its repository
URL; and `sync` — materialize the workspace's members by executing the
engine's plan. The skill SHALL NOT write the workspace declaration or the
gitignore member block by hand — both go through the CLI verbs.

#### Scenario: Init on an existing workspace reports and stops
- **WHEN** the skill's `init` verb runs where a workspace root is discoverable
- **THEN** the skill reports that root, creates nothing, and stops

#### Scenario: Init creates through the CLI verb
- **WHEN** the user confirms a target root during `init` where no workspace is
  discoverable
- **THEN** the skill runs `workspace-init` against that root and reports the
  root the verb printed

#### Scenario: Init seeds git when the portable option is chosen
- **WHEN** the user chooses git seeding in the `init` round
- **THEN** the skill runs `workspace-init <path> --git` and reports the
  created root

#### Scenario: Show reports the roster
- **WHEN** the skill's `show` verb runs in a discoverable workspace
- **THEN** the workspace root, projects, and initiatives are reported and
  nothing is changed

## ADDED Requirements

### Requirement: Workspace clone and sync flows
id: workspace-clone-sync-flows

The `/s:workspace` skill SHALL be the only workspace surface that runs
networked git; the engine verbs it drives stay network-free. When invoked
as `clone <url> [dest]`, the skill SHALL run `git clone` against the URL,
then run the sync flow from inside the created root and report the roster;
if a workspace root resolves from the destination's parent, then the skill
SHALL proceed and report a note naming the enclosing workspace root,
refusing only when the destination's immediate parent directory itself
declares `workspace` in its own `.shipd-config.json`. When invoked as `sync`,
the skill SHALL obtain the plan via the status CLI's `workspace-sync
--json` and execute each member record by its action — running the record's
advisory command for `worktree`, `reference-clone`, and `clone` actions,
and reporting `drift:` notes and `unmaterializable` reasons without
modifying anything — asking no confirmation question. If a member's command
fails, then the skill SHALL report the failure against that member and
continue with the remaining members. After executing, the skill SHALL
recompute the plan with `--write-gitignore` to reconcile the marked member
block and confirm convergence, then report the roster via `workspace-show`.
If no workspace is discoverable when `sync` runs, then the skill SHALL
report the CLI's error verbatim and point at `init` or `clone`.

#### Scenario: Clone bootstraps and hands into sync
- **WHEN** `clone <url>` runs
- **THEN** the repository is cloned with real git, the sync flow runs inside
  the created root, and the roster is reported

#### Scenario: Nested clone destination proceeds with a note
- **GIVEN** a destination whose enclosing workspace root is an ancestor but
  not the immediate parent
- **WHEN** `clone <url> <dest>` runs
- **THEN** the clone proceeds and the report names the enclosing workspace
  root

#### Scenario: Sync executes the ladder actions
- **GIVEN** a plan whose records carry `worktree` and `clone` actions with
  advisory commands
- **WHEN** `sync` runs
- **THEN** each record's command is executed as printed and the members are
  git work trees on disk afterwards

#### Scenario: Drift is reported, never repaired
- **GIVEN** a plan record with action `none` carrying a `drift:` note
- **WHEN** `sync` runs
- **THEN** the note is reported and that member is not modified

#### Scenario: A failed member does not abort the run
- **GIVEN** a plan whose first member's advisory command fails
- **WHEN** `sync` runs
- **THEN** the failure is reported against that member and the remaining
  members are still executed

#### Scenario: Sync converges and reconciles the ignore block
- **WHEN** `sync` finishes executing a plan
- **THEN** the plan is recomputed with `--write-gitignore`, the marked
  member block matches the manifest, and the roster is reported
