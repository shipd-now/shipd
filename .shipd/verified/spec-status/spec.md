# spec-status

### Requirement: Plan status header
id: proposal-status-header

Every change's `plan.md` SHALL begin with a `# <change-name>` title on line
1, where `<change-name>` equals the change's directory slug, and SHALL
carry a `Status: <status>` line as the first non-blank line after the
title. `<status>` SHALL be exactly one of `draft`, `ready`, `active`,
`complete`, `verified`, `rejected`.

#### Scenario: Header shape
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` starts with `# dark-mode-toggle` followed by a
  line `Status: draft` before any other content

#### Scenario: Only the six statuses are valid
- **WHEN** a `Status:` line carries any value other than draft, ready,
  active, complete, verified, or rejected
- **THEN** tooling treats the status as invalid

### Requirement: Status lifecycle stages
id: status-lifecycle-stages

The six statuses SHALL denote pipeline stages with these semantics:
`draft` — the spec is being authored and may be incomplete; `ready` — the
spec is lint-clean and approved but no task has been worked on; `active` —
at least one task is done or in progress; `complete` — every task is done;
`verified` — the completed work has been checked against the spec;
`rejected` — the context-sufficiency gate found the plan lacking context
to build against the codebase, and it is parked for human enrichment.
`rejected` SHALL be entered by the gate (from `draft` or `ready`) and
exited by a human transition back to `draft` or `ready` after enrichment.

#### Scenario: Stages reflect task state
- **WHEN** a change's `tasks.md` shows some but not all tasks done
- **THEN** the change's pipeline stage is `active`

#### Scenario: Verified means checked, not merely done
- **WHEN** all tasks are done but verification has not been performed
- **THEN** the stage is `complete`, and it becomes `verified` only once
  the work has been verified against the spec

#### Scenario: Rejected means parked for enrichment
- **WHEN** the gate rejects a plan and a human later enriches it
- **THEN** the plan sits at `rejected` in between, and returns to the
  pipeline via `draft` or `ready`

### Requirement: Pipeline-owned transitions with manual override
id: pipeline-owned-transitions

The planning and build flows SHALL drive status transitions automatically via
the guarded `set-status` verb: planning emits `draft` and promotes to `ready`
at the approval gate; the build flow sets `active` when execution starts,
`complete` when the task checklist shows nothing pending or in progress, and
`verified` when verification passes. Explicit manual overrides SHALL remain
possible through `set-status --force`, gated on user consent when driven
through the interactive skill.

#### Scenario: Approval promotes draft to ready
- **WHEN** an authored change passes lint and the user approves the plan
- **THEN** the pipeline sets its status to `ready` without manual editing and
  without `--force`

#### Scenario: Manual override is allowed
- **WHEN** a user explicitly sets a change's status with `--force`
- **THEN** the status line is updated to that value regardless of derived
  state

### Requirement: Status CLI
id: status-cli

A stdlib-Python CLI SHALL provide: `show [change]` printing the change's
status and task progress; `status [change]` printing the bare status value
(`?` when missing or invalid); `validate [change]` checking the change's
structural validity and exiting non-zero with the errors when invalid;
`set-status <status> [change]` writing a validated status value into the
`plan.md` header (inserting the header if absent) subject to the
transition guards; and `sync [change]` re-deriving the status from
`tasks.md` — mapping all-done to `complete`, any-done-or-in-progress to
`active`, and none-started to `ready` — while never changing a status of
`draft`, `verified`, or `rejected`. No unguarded setter SHALL exist. Where
`[change]` is omitted, the CLI SHALL default to the currently selected
spec and SHALL exit non-zero with an error when none is selected — except
`show`, which SHALL instead print the workspace board report (see the
Workspace board report requirement) when no name is given and no spec is
selected; `status` SHALL keep the error in that case. When the
given name matches no change but an epic of that slug exists — discovered
by probing the invocation root first, then each `.worktrees/<name>`
directory under it in sorted name order, resolving each candidate's
content directory independently and skipping unreadable candidates —
`status` SHALL print the epic's status value and `show` SHALL print the
epic's board-shaped report — identical to `epic-show`'s output; a name
matching neither a change nor an epic in any candidate SHALL keep
printing `?` from `status`.

#### Scenario: Sync derives active
- **GIVEN** a change with status `ready`
- **WHEN** `sync` runs after one task is marked done
- **THEN** the plan's status line becomes `active`

#### Scenario: Sync never touches draft, verified, or rejected
- **WHEN** `sync` runs on a change whose status is `draft`, `verified`,
  or `rejected`
- **THEN** the status line is left unchanged

#### Scenario: Set-status validates the value
- **WHEN** `set-status` is invoked with a value outside the six statuses
- **THEN** the CLI writes nothing and exits non-zero with an error

#### Scenario: Status falls back to an epic
- **GIVEN** an epic slug with no change of the same name
- **WHEN** `status <slug>` runs
- **THEN** the epic's status value is printed and the exit code is 0

#### Scenario: Show falls back to the epic report
- **GIVEN** an epic slug with no change of the same name
- **WHEN** `show <slug>` runs
- **THEN** the output is the same board-shaped report `epic-show <slug>`
  prints

#### Scenario: Status falls back to a worktree-hosted epic
- **GIVEN** an epic whose `epic.md` exists only under a
  `.worktrees/<name>` content directory
- **WHEN** `status <slug>` runs from the invocation root
- **THEN** that epic's status value is printed and the exit code is 0

#### Scenario: A name that is neither change nor epic stays a question mark
- **WHEN** `status <name>` runs for a name matching no change and no epic
  in the invocation root or any worktree
- **THEN** `?` is printed

#### Scenario: Bare status without a selection still errors
- **GIVEN** no spec selected
- **WHEN** `status` runs with no argument
- **THEN** the CLI exits non-zero with the no-selection error

### Requirement: Transition guards
id: transition-guards

`set-status` SHALL enforce guards derived from the target status before
writing: targeting `draft` or `rejected` requires nothing; targeting
`ready` or `active` requires the change to pass structural validation;
targeting `complete` or `verified` additionally requires a finished
checklist — `tasks.md` present with at least one checkbox and nothing
pending or in progress. A refused transition SHALL write nothing, print a
reason line beginning `Refused: ` to stderr (with concrete task counts or
the validation errors), and exit with code 3, distinct from general
errors. A `--force` flag SHALL bypass the guards but SHALL NOT bypass
status-value validation.

#### Scenario: Complete refused while tickets are open
- **GIVEN** a change with 7 of 10 tasks done
- **WHEN** `set-status complete` runs without `--force`
- **THEN** nothing is written, stderr starts `Refused: `, and the exit
  code is 3

#### Scenario: Rejected needs no structural validity
- **WHEN** `set-status rejected` runs on a change whose delta specs fail
  structural validation
- **THEN** the status line is written to `rejected` and the exit code is 0

#### Scenario: Force never accepts an invalid value
- **WHEN** `set-status done --force` runs
- **THEN** nothing is written and the CLI errors with exit code 1

### Requirement: Interactive status skill
id: interactive-status-skill

A `shipd:status` skill SHALL expose four commands over the status CLI —
`status` (report the selected or named change's status), `validate` (report
structural validity or the errors), `set-status <status>` (guarded
transition), and `pipeline` (report the effective autonomous pipeline).
When invoked with no argument, the skill SHALL run `show`
alone and relay its output — the selected change's one-liner when a
selection exists, else the CLI's workspace board report — never surfacing
the bare `status` verb's no-selection error as the answer. When the
`status` command's argument names an epic rather than
a change, the skill SHALL relay the CLI's board-shaped epic report and point
epic transitions at the epic verbs rather than `set-status`. When
`set-status` is refused by a guard (exit code 3), the skill
SHALL surface the refusal reason and ask the user whether to override,
re-running with `--force` only after explicit consent; it SHALL never pass
`--force` uninvited, and on decline SHALL leave the status unchanged. The
`pipeline` command SHALL run `pipeline-show` and relay its output verbatim;
with a preset-name argument it SHALL instead run `pipeline-show --expand
<preset>` and relay that output, so an unknown preset relays the CLI's
error listing the known preset names.

#### Scenario: Refusal asks before forcing
- **WHEN** the skill's `set-status complete` is refused because tickets are
  open
- **THEN** the skill shows the reason, asks the user, and only re-runs with
  `--force` if the user chooses to override

#### Scenario: Decline leaves the status untouched
- **WHEN** the user declines the override question
- **THEN** the proposal's status line is unchanged and the skill reports the
  refusal

#### Scenario: An epic argument reports the epic
- **WHEN** the skill's `status` command is invoked with an epic's slug
- **THEN** the skill relays the board-shaped epic report instead of a
  change status

#### Scenario: A bare invocation reports the workspace
- **GIVEN** no spec selected
- **WHEN** the skill is invoked with no argument
- **THEN** the skill relays the CLI's workspace board report rather than
  the no-selection error

#### Scenario: The pipeline command relays the resolved pipeline
- **WHEN** the skill is invoked as `/s:status pipeline`
- **THEN** it runs the CLI's `pipeline-show` and relays the printed
  pipeline and provenance verbatim

#### Scenario: A preset argument expands the preset
- **WHEN** the skill is invoked as `/s:status pipeline eco`
- **THEN** it runs `pipeline-show --expand eco` and relays the printed
  entry list, and an unknown preset name relays the CLI's known-preset
  listing

### Requirement: Metadata-preserving status writes
id: metadata-preserving-status-writes

The status CLI's `set-status` and `sync` verbs SHALL rewrite only the
`Status:` line, preserving any header metadata lines byte-for-byte, and the
`show` verb SHALL print the plan's recognized metadata lines when present.

#### Scenario: Set-status keeps metadata intact
- **GIVEN** a plan whose header carries `Theme: reliability` after `Status:`
- **WHEN** `set-status ready` runs on the change
- **THEN** the `Status:` line becomes `ready` and the `Theme:` line is
  unchanged

#### Scenario: Show displays metadata
- **WHEN** `show` runs on a change whose plan carries `Profile: lite` and
  `Theme: reliability`
- **THEN** the output includes the profile and theme alongside the status and
  task progress

### Requirement: Epic status verbs
id: epic-status-verbs

The status CLI SHALL provide `epic-show <slug>` printing the epic's
board-shaped report; `epic-sync <slug>` re-deriving the epic's status from
member states; and `epic-set-status <status> <slug>` writing a validated
epic status (`draft`, `ready`, `active`, `complete`), refusing `ready`
unless the epic lints clean, with refusals printing a `Refused: ` reason
and exiting 3. `epic-show` SHALL resolve the epic across the universes the
engine's shared universe-discovery seam yields (shipd-workspace
workspace-universe-discovery), in seam order — the invocation root's own
universe first, then each declared project universe in slug order — probing
each universe's root first, then each of its `.worktrees/<name>` directories
in sorted name order, resolving each candidate's content directory
independently and skipping unreadable candidates; the first hosting
universe SHALL win, and the epic's file and status SHALL be read from the
hosting root. The mutating verbs (`epic-sync`, `epic-set-status`) SHALL
keep resolving the invocation root only. The board-shaped report SHALL
print, in order: the `<slug>: <status>` line and the epic's header metadata
lines (unchanged from before this report existed); when the epic resolved
from a worktree of its owning universe, a `worktree: <name>` line directly
after the metadata lines; when the epic resolved from a declared project
universe, a `project: <slug>` line directly after (after any `worktree:`
line); a `shipped <n>/<m>` line where `n` is the count of members whose
derived state is `archived` and `m` the count of all stub members; a blank
line; then the four board lanes in board order — `UNPLANNED`, `READY`,
`BUILDING`, `SHIPPED` — each printed as a `<LANE> (<count>)` header even
when its count is 0, followed by one indented line per member in that lane
carrying the member's slug, its derived state, its stub-table risk rating
as `risk <value>` (`?` when the row carries none), and a `[worktree]`
marker when its state was derived from a worktree rather than the owning
universe's root. A member's lane SHALL be derived from its state alone —
`archived`→`shipped`, `ready`→`ready`, `unplanned`→`unplanned`, every other
state→`building`, rendered as the uppercase lane headers — and that
projection SHALL be a single shared function the dashboard's flow-lane
mapping also consumes, so the report and the board cannot drift. A member's
state SHALL be derived by probing the epic's owning universe's candidate
roots in order — that universe's root first, then each of its
`.worktrees/<name>` directories in sorted name order — resolving each
candidate's content directory independently and skipping any candidate
whose configuration is unreadable. For each candidate in turn, the state
SHALL be `archived` when a matching `completed/*-<slug>/` exists there,
else that candidate's plan status when `planned/<slug>/` exists there; the
first candidate that yields a state wins. When no candidate yields one, the
state SHALL be `unplanned`. `epic-sync` SHALL derive: all members
archived → `complete`; any member archived or with plan status `active`,
`complete`, or `verified` → `active`; otherwise `ready` — and SHALL never
change an epic whose status is `draft`.

#### Scenario: Members are grouped into board lanes
- **GIVEN** an epic whose stub table lists one member with a matching
  `completed/*-<slug>/` and one member planned nowhere
- **WHEN** `epic-show` runs
- **THEN** the archived member is listed under `SHIPPED (1)` and the other
  under `UNPLANNED (1)`

#### Scenario: Empty lanes still print their header
- **GIVEN** an epic none of whose members is `ready`
- **WHEN** `epic-show` runs
- **THEN** the report contains a `READY (0)` header with no member lines
  under it

#### Scenario: The shipped progress line counts archived members
- **GIVEN** an epic with two archived members among seven
- **WHEN** `epic-show` runs
- **THEN** the report contains `shipped 2/7`

#### Scenario: A worktree-hosted member is marked
- **GIVEN** a member whose state derives from `.worktrees/<member>/` rather
  than the invocation root
- **WHEN** `epic-show` runs
- **THEN** that member's line carries `[worktree]`

#### Scenario: A member planned in its own worktree is not unplanned
- **GIVEN** a repository whose epic lists a member with no change under the
  invocation root's `planned/`, but with a `ready` change under
  `.worktrees/<member>/`'s planned directory
- **WHEN** `epic-show` runs from the invocation root
- **THEN** that member's derived state is `ready`, not `unplanned`

#### Scenario: The invocation root wins over a worktree
- **GIVEN** a member with a change under the invocation root's `planned/` and a
  different plan status for the same slug under a worktree
- **WHEN** the member's state is derived
- **THEN** the invocation root's status is the one reported

#### Scenario: An unreadable worktree config does not break derivation
- **GIVEN** a worktree whose content-directory configuration cannot be read
- **WHEN** a member's state is derived from the invocation root
- **THEN** that worktree is skipped and derivation completes without raising

#### Scenario: Epic-show resolves a worktree-hosted epic
- **GIVEN** an epic whose `epic.md` exists only under a
  `.worktrees/<name>` content directory
- **WHEN** `epic-show <slug>` runs from the invocation root
- **THEN** the report prints with the epic's status on the first line and a
  `worktree: <name>` line after the metadata lines

#### Scenario: Epic-show resolves a project-hosted epic at workspace level
- **GIVEN** a workspace root whose declared project repo hosts the epic
- **WHEN** `epic-show <slug>` runs from the workspace root
- **THEN** the report prints with a `project: <slug>` line after the
  metadata lines and its member states derived from that project repo

#### Scenario: The invocation root's universe wins over a project's
- **GIVEN** the same epic slug hosted under the invocation root and under a
  declared project repo
- **WHEN** `epic-show <slug>` runs from the workspace root
- **THEN** the invocation root's epic is the one reported, with no
  `project:` line

#### Scenario: Mutating verbs stay invocation-root-only
- **GIVEN** an epic hosted only under a worktree
- **WHEN** `epic-set-status ready <slug>` runs from the invocation root
- **THEN** the CLI exits non-zero with the epic-not-found error and writes
  nothing

#### Scenario: Mutating verbs never reach a project universe
- **GIVEN** an epic hosted only under a declared project repo
- **WHEN** `epic-sync <slug>` runs from the workspace root
- **THEN** the CLI exits non-zero with the epic-not-found error and writes
  nothing

#### Scenario: Sync derives active from one started member
- **GIVEN** a `ready` epic whose stub table lists two members, one of which
  is an `active` change under `.shipd/planned/`
- **WHEN** `epic-sync` runs
- **THEN** the epic's status line becomes `active`

#### Scenario: Sync derives complete when all members are archived
- **GIVEN** an epic whose every stub slug matches an `.shipd/completed/*-<slug>/`
  directory
- **WHEN** `epic-sync` runs
- **THEN** the epic's status line becomes `complete`

#### Scenario: Sync never touches a draft epic
- **WHEN** `epic-sync` runs on an epic whose status is `draft`
- **THEN** the status line is left unchanged

### Requirement: Initiative status verbs
id: initiative-status-verbs

The status CLI SHALL provide `initiative-show <slug>` printing a brief's
status, metadata, requirement progress (`done/total`), and each requirement
line; `initiative-sync <slug>` re-deriving the status from the requirement
checkboxes — `achieved` when at least one requirement exists and all are
ticked, `open` otherwise, never changing a `dropped` brief; and
`initiative-set-status <status> <slug>` writing a validated status from
`open`, `achieved`, `dropped`. All three SHALL resolve the workspace from
the repository root and SHALL exit non-zero with a clear error when no
workspace is discoverable.

#### Scenario: Show reports requirement progress
- **GIVEN** a brief with three requirements, one ticked
- **WHEN** `initiative-show` runs
- **THEN** the output includes the status and a `1/3` progress count

#### Scenario: Sync derives achieved
- **GIVEN** an `open` brief whose every requirement checkbox is ticked
- **WHEN** `initiative-sync` runs
- **THEN** the brief's status line becomes `achieved`

#### Scenario: Sync never touches dropped
- **WHEN** `initiative-sync` runs on a `dropped` brief with all requirements
  ticked
- **THEN** the status line is left unchanged

#### Scenario: Verbs require a workspace
- **WHEN** `initiative-show` runs in a checkout with no discoverable
  workspace
- **THEN** the CLI exits non-zero saying no workspace was found

#### Scenario: Set-status validates the value
- **WHEN** `initiative-set-status pending` runs
- **THEN** nothing is written and the CLI errors non-zero

### Requirement: Workspace status verbs
id: workspace-status-verbs

The status CLI SHALL provide `workspace-show` printing the workspace root,
the declared `focus` project when the resolved registry carries one, each
declared project with its repos (annotated when a path is not a directory on
this machine, and annotated `[url]` when the entry carries a clone URL) and
whether its `context.md` exists, each initiative with its status and project
scope, and a note that the current repository falls under the implicit
default project when it resolves to no declared project; and `project-show
<slug>` printing one declared project's repos (annotated the same way), its
`context.md` presence, and the initiatives scoped to it. Both verbs SHALL read
the registry resolved from the workspace chain, and where that registry comes
from a chain member other than the workspace root, `workspace-show` SHALL print
that member's root as the registry's provenance. An undeclared slug SHALL be a
non-zero error naming the declared slugs. Both verbs SHALL resolve repo paths
uniformly from string and object entry shapes, SHALL resolve the workspace from
the repository root, and SHALL exit non-zero with a clear error when no
workspace is discoverable.

#### Scenario: Workspace overview lists projects and initiatives
- **GIVEN** a workspace declaring project `alpha` (one repo present, one
  absent, no context.md) and an initiative `mvp-readiness` scoped
  `Project: alpha`
- **WHEN** `workspace-show` runs
- **THEN** the output lists `alpha` with both repos (one annotated absent),
  `context: no`, and `mvp-readiness` with its status and `alpha` scope

#### Scenario: Focus and clone URLs surface in the overview
- **GIVEN** a registry declaring `focus: "alpha"` and an alpha repo entry
  carrying a `url`
- **WHEN** `workspace-show` runs
- **THEN** the output names `alpha` as the focus and annotates that repo
  line `[url]`

#### Scenario: Inherited registry names its provenance
- **GIVEN** nested workspaces where only the outer one declares `projects`
- **WHEN** `workspace-show` runs from a repo under the inner workspace
- **THEN** the outer workspace's projects are listed and the output names the
  outer root as the registry's provenance

#### Scenario: Project view shows scoped initiatives
- **WHEN** `project-show alpha` runs in that workspace
- **THEN** the output lists alpha's repos, its context presence, and
  `mvp-readiness` among its scoped initiatives

#### Scenario: Unknown project slug errors
- **GIVEN** the registry declares only `alpha`
- **WHEN** `project-show beta` runs
- **THEN** the CLI exits non-zero naming the declared slugs

#### Scenario: Verbs require a workspace
- **WHEN** `workspace-show` runs in a checkout with no discoverable
  workspace
- **THEN** the CLI exits non-zero saying no workspace was found

### Requirement: Main-checkout epic write warning
id: main-checkout-epic-write-warning

When `epic-sync` or `epic-set-status` actually modifies an epic file and the
repository root's `.git` is a directory (a main checkout rather than a
linked worktree), the CLI SHALL print a one-line warning to stderr naming
the modified file and stating that a protected-main workflow must ship the
change via a worktree PR. The warning SHALL NOT change exit codes or block
the write, SHALL NOT appear when the same write happens in a linked
worktree (`.git` is a file), and SHALL NOT appear when a sync derives no
status change and writes nothing.

#### Scenario: Main-checkout write warns
- **GIVEN** a repo fixture whose root `.git` is a directory
- **WHEN** `epic-set-status active` rewrites an epic's status line
- **THEN** stderr carries the one-line warning naming the epic file and the
  exit code is zero

#### Scenario: Worktree write stays silent
- **GIVEN** a repo fixture whose root `.git` is a file
- **WHEN** `epic-set-status active` rewrites an epic's status line
- **THEN** no warning is emitted

#### Scenario: No-op sync stays silent
- **GIVEN** a main-checkout fixture whose epic already carries its derived
  status
- **WHEN** `epic-sync` runs
- **THEN** nothing is written and no warning is emitted

### Requirement: Workspace init verb
id: workspace-init-verb

The status CLI SHALL provide `workspace-init <path>` which initializes a
workspace at the given directory through the engine's workspace
initialization — declaring `workspace` in `<path>/.shipd-config.json` — and
prints the created workspace root on success. The verb SHALL accept a `--git`
flag requesting the engine's git option (git-init when the target is not
already inside a work tree, plus the seeded member-repos `.gitignore` block),
and a `--nested` flag requesting the engine's nested option, which permits
creating the workspace beneath an enclosing one and reports the enclosing root
it nests under. If initialization refuses or errors (a workspace already
discoverable from the target without `--nested`, a target that itself already
declares `workspace`, or a missing target directory), then the CLI SHALL exit
non-zero with that error. Unlike the other workspace verbs, `workspace-init`
SHALL NOT require a discoverable workspace to run.

#### Scenario: Init verb creates and prints the root
- **GIVEN** an existing directory with no discoverable workspace
- **WHEN** `workspace-init <path>` runs against it
- **THEN** `.shipd-config.json` declares `workspace` there, the created root is
  printed, and the exit code is zero

#### Scenario: Init verb refuses under an existing workspace
- **WHEN** `workspace-init <path>` runs where a workspace root is already
  discoverable from `<path>`
- **THEN** the CLI exits non-zero with an error naming the existing root

#### Scenario: Nested flag creates the nested workspace
- **WHEN** `workspace-init <path> --nested` runs where a workspace root is
  already discoverable from `<path>`
- **THEN** `<path>/.shipd-config.json` declares `workspace`, the enclosing root
  is reported, and the exit code is zero

#### Scenario: Git flag produces a git-ready root
- **GIVEN** an existing directory with no discoverable workspace and no git
  work tree
- **WHEN** `workspace-init <path> --git` runs
- **THEN** the created root is a git repository whose `.gitignore` carries
  the marked member-repos block, and the exit code is zero

### Requirement: Config-show verb
id: config-show-verb

The status CLI SHALL provide `config-show` printing the resolved layered
configuration: each effective top-level key with the path of the layer that
supplied it (or `default`), the resolved content directory name, and the
workspace root when one is discoverable (or a note that none is). Where the
resolved configuration declares `store_root`, the verb SHALL additionally
print the resolved absolute external content directory path, so a
mis-declared store is inspectable at a glance. Where the resolved workspace
chain carries more than one member, the verb SHALL additionally print the
whole chain in nearest-first order. The verb SHALL NOT require a
discoverable workspace and SHALL exit zero on a default-only resolution.

#### Scenario: Provenance is printed per key
- **GIVEN** the repo layer declares `valid_themes` and the workspace layer
  declares `workspace`
- **WHEN** `config-show` runs
- **THEN** each key is listed with the config file path that supplied it

#### Scenario: Nested chain is printed
- **GIVEN** nested workspaces enclosing the repository
- **WHEN** `config-show` runs
- **THEN** the workspace root is the nearest one and the chain lists both
  roots, nearest first

#### Scenario: Defaults-only still succeeds
- **WHEN** `config-show` runs where no `.shipd-config.json` exists in any layer
- **THEN** the content directory prints as `.shipd`, keys show `default`, and
  the exit code is zero

#### Scenario: External store path is printed
- **GIVEN** a resolved configuration declaring `store_root`
- **WHEN** `config-show` runs
- **THEN** the output includes the resolved absolute external content
  directory path

### Requirement: Epic initiative header verb
id: epic-set-initiative-verb

The status CLI SHALL provide `epic-set-initiative <epic> <initiative>`
writing `Initiative: <initiative>` into the epic's header metadata block,
replacing any existing `Initiative:` line and preserving all other header
and body content. An unknown epic SHALL be a non-zero error. The verb SHALL
validate the value is a kebab-case slug and SHALL leave status derivation
untouched.

#### Scenario: Initiative line is written metadata-preservingly
- **GIVEN** an epic whose header carries `Theme: reliability` and no
  `Initiative:` line
- **WHEN** `epic-set-initiative reporting-overhaul mvp-readiness` runs
- **THEN** the header carries both `Theme: reliability` and
  `Initiative: mvp-readiness` and the body is unchanged

#### Scenario: Existing initiative is replaced, never duplicated
- **WHEN** the verb runs on an epic already carrying an `Initiative:` line
- **THEN** exactly one `Initiative:` line remains, holding the new value

### Requirement: Pipeline-show verb
id: pipeline-show-verb

The status CLI SHALL provide `pipeline-show` printing the effective
autonomous pipeline: one line per resolved entry stating its form (stage,
skipped, tool-bound, replaced, or custom) and any bindings with their
fallbacks, plus the provenance of the `autonomous-pipeline` key — the
supplying config file path, `preset:<name>` with the supplying path for a
preset-resolved pipeline, or `[default]` when no layer declares it. Where a
resolved entry carries declared per-stage options, the verb SHALL append
them to that entry's line as `key=value` pairs (booleans rendered
`true`/`false`, `autopilot` sub-keys rendered `autopilot.<key>=<value>`);
an entry with no declared options SHALL render exactly as it does without
options. On a pipeline that fails validation the verb SHALL print every
validation error and exit non-zero. The verb SHALL NOT require a
discoverable workspace or a selected change, and a defaults-only resolution
SHALL exit zero. The verb SHALL additionally accept `--expand <preset>`,
printing the named preset's entry list as indented JSON — the exact value a
config may declare as a custom list — without resolving the repo's own
pipeline; expanding any preset SHALL require no third-party package, and an
unknown preset SHALL exit non-zero listing the known preset names.

The verb SHALL additionally accept `--json` as its machine contract: when
resolving the repo's pipeline it SHALL emit exactly one JSON object on
stdout and nothing else, with `source` holding the raw provenance value
(`default`, the supplying config file path, or `preset:<name>
(<config-path>)`) and `entries` holding the resolved entries as the
validated dicts, carrying exactly the keys each entry declared; when
combined with `--expand <preset>` it SHALL emit the same entry-list JSON
array the flagless expand prints. Without the flag, the text output SHALL
stay byte-identical to its pre-flag behavior, and error handling (stderr
`Error:` lines, exit codes) SHALL be unchanged in both modes.

#### Scenario: Default pipeline prints with default provenance
- **WHEN** `pipeline-show` runs where no layer declares the key
- **THEN** all six registry stages print in canonical order marked
  `[default]` and the exit code is zero

#### Scenario: Declared pipeline prints entries and provenance
- **GIVEN** a repo config declaring a pipeline with a skipped gate and a
  replaced review carrying `"fallback": "builtin"`
- **WHEN** `pipeline-show` runs
- **THEN** the output shows the gate as skipped, the review as replaced
  with its fallback, and names the repo's config file

#### Scenario: Invalid pipeline errors with findings
- **WHEN** `pipeline-show` runs against a declared entry with an unknown
  stage name
- **THEN** the validation error is printed naming the entry and the exit
  code is non-zero

#### Scenario: Preset pipeline prints options and preset provenance
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}`
- **WHEN** `pipeline-show` runs
- **THEN** the source line names `preset:eco` with the repo config path,
  the build line carries `validator=false`,
  `subagent_model=tier-two-below`, and `telemetry=false`, the gate line
  carries `autopilot.attempts=1`, and the review line carries
  `model=tier-below` and `disposition=high-only`

#### Scenario: Expand prints a fork-ready entry list
- **WHEN** `pipeline-show --expand eco` runs
- **THEN** the output is indented JSON parsing to the eco preset's entry
  list, valid as a declared `autonomous-pipeline` list, and the exit code
  is zero

#### Scenario: Expanding default needs no third-party package
- **WHEN** `pipeline-show --expand default` runs
- **THEN** the output is JSON parsing to the six bare registry stages in
  canonical order and the exit code is zero

#### Scenario: Expanding an unknown preset errors
- **WHEN** `pipeline-show --expand turbo` runs
- **THEN** the verb exits non-zero naming `turbo` and listing the known
  presets `basic`, `default`, and `eco`

#### Scenario: Resolved pipeline is machine-readable
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}`
- **WHEN** `pipeline-show --json` runs
- **THEN** stdout parses as one JSON object whose `source` names
  `preset:eco` with the repo config path and whose `entries` hold the
  validated entry dicts, the build entry carrying `subagent_model`
  `tier-two-below`, `validator` false, and `telemetry` false

#### Scenario: Default resolution is machine-readable
- **GIVEN** no layer declares the key
- **WHEN** `pipeline-show --json` runs
- **THEN** stdout parses as one JSON object with `source` `default` and
  `entries` holding the six bare registry stages in canonical order, and
  the exit code is zero

#### Scenario: Expand with the JSON flag keeps the array contract
- **WHEN** `pipeline-show --expand default --json` runs
- **THEN** stdout parses as the same JSON entry-list array the flagless
  expand prints

#### Scenario: Text mode is unchanged without the flag
- **WHEN** `pipeline-show` runs without `--json`
- **THEN** the output is byte-identical to the pre-flag text rendering

#### Scenario: Invalid pipeline errors identically under the flag
- **WHEN** `pipeline-show --json` runs against a declared entry with an
  unknown stage name
- **THEN** the verb prints the validation error to stderr and exits
  non-zero exactly as the flagless form does

### Requirement: Wiki status verbs
id: wiki-status-verbs

The status CLI SHALL provide wiki verbs operating on the workspace store:
`wiki-init` SHALL scaffold the store layout (seeding `schema.md` with the
grammar conventions, empty `index.md` and `queue.md`, a first dated `log.md`
entry, and empty `sources/` and `wiki/` directories) in the nearest workspace
and SHALL refuse when that wiki directory already exists; `wiki-show` SHALL
print the store root, page count, index-coverage health, pending-question
count, and the last log entry; the `cat` verb SHALL accept a `wiki` kind
resolving `<slug>` across the workspace chain — a page slug to `wiki/<slug>.md`
in the nearest chain store holding it, the reserved slugs `index` and `queue`
to every chain store's file of that name in nearest-first order, and the
reserved slugs `log` and `schema` to the nearest store's file only. Where a
file printed by `cat wiki` comes from an inherited chain store rather than
the nearest one, the verb SHALL annotate that file's separator line with the
inherited store's workspace root, so a reader never derives provenance by
comparing a root-relative separator against an absolute store path; a file
from the nearest store SHALL carry no annotation. And
`wiki-queue-add <q-slug>` SHALL append a queue block built from `--question`,
`--options`, `--recommendation`, and optional `--origin` values with a
current-date `Asked:` line and `Answer: pending` **to the nearest workspace's
store, scaffolding that store when it does not exist**, restoring the prior
`queue.md` and exiting non-zero when the slug already exists in that store or
the resulting queue is invalid. `wiki-show` SHALL additionally print a `chain:`
line listing the inherited chain stores that exist, nearest first, or `chain:
none` when the store has no inherited member; where the nearest workspace holds
no store but a chain member does, `wiki-show` SHALL report the nearest store as
absent, print the `chain:` line, and exit zero, exiting non-zero only when no
chain member holds a store; and a `base:` line reporting the
resolved `wiki_base` store: `base: <path> (present)` when the resolved base
directory exists, `base: <path> (absent)` when it is declared but missing, and
`base: none` when the key is undeclared or resolves to any chain store's
directory; if the declared `wiki_base` value is malformed, then `wiki-show`
SHALL exit non-zero with an error naming `wiki_base`.

`wiki-init`, `wiki-show`, and the `cat wiki` verb SHALL each accept a
`--personal` flag: when set, the verb SHALL resolve the personal memory store at
`<memory_dir>/wiki` (default `~/.shipd-memory/wiki`) by fixed path, bypassing
workspace discovery and the chain, and operate on it instead of the workspace
store. Under `--personal`, `wiki-show` SHALL report `chain: none` and `base:
none` (a personal store participates in no chain or base layering).

#### Scenario: Scaffold once
- **WHEN** `wiki-init` runs in a workspace with no wiki, then runs again
- **THEN** the first run creates the seeded layout and the second exits
  non-zero naming the existing store

#### Scenario: Queue append is guarded
- **WHEN** `wiki-queue-add stale-cache --question … --options …
  --recommendation …` runs twice
- **THEN** the first run appends a `## q-stale-cache` block with
  `Answer: pending` and the second exits non-zero leaving `queue.md` unchanged

#### Scenario: Queue append scaffolds the nearest store
- **GIVEN** nested workspaces where only the outer one holds a wiki store
- **WHEN** `wiki-queue-add stale-cache …` runs from a repo under the inner
  workspace
- **THEN** the inner workspace's store is scaffolded, the block lands in its
  `queue.md`, and the outer store is unchanged

#### Scenario: Mediated page read
- **WHEN** `cat wiki <slug>` names an existing page
- **THEN** the page's content prints with the engine's file separator, and an
  unknown slug exits non-zero

#### Scenario: Inherited page reads through the chain
- **GIVEN** nested workspaces where only the outer store holds
  `wiki/conventions.md`
- **WHEN** `cat wiki conventions` runs from a repo under the inner workspace
- **THEN** the outer store's page prints with its own path as the separator

#### Scenario: An inherited read is annotated with its provenance
- **GIVEN** nested workspaces where only the outer store holds
  `wiki/conventions.md`
- **WHEN** `cat wiki conventions` runs from a repo under the inner workspace
- **THEN** the separator line carries the outer workspace's root as that file's
  provenance, while the same read against a page held by the nearest store
  carries no such annotation

#### Scenario: Index aggregates across the chain
- **GIVEN** nested workspaces whose stores both hold `index.md`
- **WHEN** `cat wiki index` runs from a repo under the inner workspace
- **THEN** both files print, nearest first, each behind its own separator

#### Scenario: Absent nearest store still reports the chain
- **GIVEN** nested workspaces where only the outer one holds a wiki store
- **WHEN** `wiki-show` runs from a repo under the inner workspace
- **THEN** the nearest store is reported absent, the `chain:` line names the
  outer store, and the exit code is zero

#### Scenario: Chain line reports inherited stores
- **GIVEN** nested workspaces whose stores both exist
- **WHEN** `wiki-show` runs from a repo under the inner workspace
- **THEN** the output carries a `chain:` line naming the outer store

#### Scenario: Declared base is reported with presence
- **GIVEN** a workspace whose config declares `wiki_base` pointing at an
  existing base store directory outside its chain
- **WHEN** `wiki-show` runs
- **THEN** the output carries `base: <expanded-path> (present)`, and
  `(absent)` instead when the directory does not exist

#### Scenario: No base reports none
- **WHEN** `wiki-show` runs where no layer declares `wiki_base`, or where the
  key resolves to a chain store's own directory
- **THEN** the output carries `base: none`

#### Scenario: Personal flag targets the memory store
- **WHEN** `wiki-init --personal` runs, then `wiki-show --personal`
- **THEN** the store is scaffolded at `<memory_dir>/wiki` (default
  `~/.shipd-memory/wiki`) without workspace discovery, and `wiki-show --personal`
  reports that store's health with `chain: none` and `base: none`

### Requirement: Locate verb
id: locate-verb

The status CLI SHALL provide `locate [change]` searching for an installed
change across the universes the engine's shared universe-discovery seam
yields (shipd-workspace workspace-universe-discovery), in seam order — the
invocation root's own universe first, then each declared project universe
in slug order — probing, within each universe, that universe's resolved
`planned/` directory and then each `.worktrees/<name>` directory under it
in sorted name order, resolving the content directory independently for
every candidate root. Where `change` is omitted, the verb SHALL default to
the currently selected spec and SHALL exit non-zero with an error when none
is selected. For each match it SHALL print a keyed block — `change:`,
`root:` (absolute path), `dir:` (the change directory relative to that
root), `status:` (the plan's status value, `?` when missing or invalid),
and, for a match from a declared project universe only, `project:` (the
owning project's slug) — with blocks separated by a blank line and the
invocation root's own match always first. When at least one match exists
the verb SHALL exit 0; when none exists it SHALL print an error naming the
probed locations and exit non-zero. The verb SHALL NOT invoke git, a
model, or the network.

#### Scenario: Local change is located
- **GIVEN** a change installed under the invocation root's `planned/`
- **WHEN** `locate <change>` runs
- **THEN** one block prints with the root, dir, and status, and the exit code
  is 0

#### Scenario: Worktree change is located
- **GIVEN** a change installed only under a worktree's own planned directory
- **WHEN** `locate <change>` runs from the main checkout
- **THEN** the printed `root:` names the worktree directory and `status:`
  carries that plan's status value

#### Scenario: Local match precedes worktree matches
- **GIVEN** the change exists in both the invocation root and a worktree
- **WHEN** `locate <change>` runs
- **THEN** the invocation root's block prints first, followed by the
  worktree's block

#### Scenario: A project-hosted change is located at workspace level
- **GIVEN** a workspace root whose declared project repo holds the change
  under its `planned/`
- **WHEN** `locate <change>` runs from the workspace root
- **THEN** the match block names that repo as `root:` and carries a
  `project: <slug>` line

#### Scenario: Universe order governs the block order
- **GIVEN** the change exists under the invocation root and under a declared
  project repo
- **WHEN** `locate <change>` runs from the workspace root
- **THEN** the invocation root's block prints first and the project block
  after it

#### Scenario: Unknown change exits non-zero
- **WHEN** `locate no-such-change` runs and no candidate root contains it
- **THEN** an error names the probed locations and the exit code is non-zero

#### Scenario: Omitted argument falls back to the current selection
- **GIVEN** a change selected via `use`
- **WHEN** `locate` runs with no argument
- **THEN** the verb locates that selected change exactly as if its name had
  been given explicitly

#### Scenario: No argument and no selection errors
- **WHEN** `locate` runs with no argument and no change is currently selected
- **THEN** the CLI exits non-zero with an error stating no change was given
  and none is selected

### Requirement: Workspace sync verb
id: workspace-sync-verb

The status CLI SHALL provide `workspace-sync` printing the engine's
materialization plan as one keyed block per member (`member:`, `path:`,
`state:`, `action:`, plus `source:`, `url:`, `command:`, and `drift:` when
applicable) followed by a `gitignore:` section, and SHALL support `--json`
emitting one JSON object per record with a `kind` field
(`member`/`gitignore`). A computed plan SHALL exit zero regardless of drift
or unmaterializable entries. With `--write-gitignore` the verb SHALL
additionally rewrite only the marked member-repos block to match the
manifest's member paths, idempotently; without the flag it SHALL write
nothing. The verb SHALL require a discoverable workspace and SHALL exit
non-zero printing the findings when the registry fails validation.

#### Scenario: Plan prints and exits zero
- **GIVEN** a workspace whose manifest has one present member and one
  absent member with a url
- **WHEN** `workspace-sync` runs
- **THEN** two keyed member blocks and a gitignore section print and the
  exit code is zero

#### Scenario: JSON mode emits parseable records
- **WHEN** `workspace-sync --json` runs in that workspace
- **THEN** every output line parses as a JSON object carrying a `kind`
  field

#### Scenario: Gitignore write is opt-in and scoped
- **GIVEN** a marked member block missing a manifest path
- **WHEN** `workspace-sync` runs without and then with `--write-gitignore`
- **THEN** the first run leaves `.gitignore` unchanged and the second
  rewrites only the marked block to include the path, leaving content
  outside the markers untouched

#### Scenario: Invalid registry gates the verb
- **WHEN** `workspace-sync` runs where the registry declares a malformed
  project entry
- **THEN** the CLI exits non-zero printing the validation findings

#### Scenario: No workspace errors
- **WHEN** `workspace-sync` runs with no discoverable workspace
- **THEN** the CLI exits non-zero saying no workspace was found

### Requirement: Check-base verb
id: check-base-verb

The status CLI SHALL provide `check-base [change]` comparing the change's
delta specs against the current master library without writing anything,
reporting one finding line per mismatched entry: `stale-base` when a
MODIFIED/REMOVED entry's `base:` hash differs from the master requirement's
current content hash (computed with the same content-hash function the merge
engine uses, and reporting the expected and actual hashes); `missing-master`
when a MODIFIED/REMOVED entry's id — or the capability's master spec itself —
does not exist; and `id-collision` when an ADDED entry's id already exists in
the master. The verb SHALL print a summary line after the findings, SHALL
exit 0 when no finding exists, and SHALL exit 4 when at least one finding
exists — distinct from general errors and guard refusals. Where `[change]` is
omitted, the verb SHALL default to the currently selected change and SHALL
exit non-zero with an error when none is selected. The verb SHALL NOT invoke
git, a model, or the network.

#### Scenario: Clean change exits zero
- **GIVEN** a planned change whose MODIFIED entries all carry `base:` hashes
  matching the current masters and whose ADDED ids are all new
- **WHEN** `check-base <change>` runs
- **THEN** the summary reports clean, no finding lines print, and the exit
  code is 0

#### Scenario: Stale base is reported
- **GIVEN** a planned change with a MODIFIED entry whose `base:` hash no
  longer matches the master requirement's content hash
- **WHEN** `check-base <change>` runs
- **THEN** a `stale-base` line prints naming the capability, the id, and the
  expected and actual hashes, and the exit code is 4

#### Scenario: Added id collision is reported
- **GIVEN** a planned change with an ADDED entry whose id already exists in
  that capability's master spec
- **WHEN** `check-base <change>` runs
- **THEN** an `id-collision` line prints naming the capability and id, and
  the exit code is 4

#### Scenario: Missing master is reported
- **GIVEN** a planned change with a MODIFIED entry whose id exists in no
  master requirement
- **WHEN** `check-base <change>` runs
- **THEN** a `missing-master` line prints naming the capability and id, and
  the exit code is 4

#### Scenario: The verb never writes
- **WHEN** `check-base <change>` runs with any mix of findings
- **THEN** no file under the content directory or the change directory is
  modified

### Requirement: Wiki page removal verb
id: wiki-remove-verb

The status CLI SHALL provide a `wiki-remove <slug>` verb that resolves the store
(the workspace store by default, or the personal memory store under
`--personal`), deletes `wiki/<slug>.md`, removes the page's `index.md` catalog
entry, and appends a `## [YYYY-MM-DD] remove | <slug>` entry to `log.md`. If the
slug is reserved (`index`, `log`, `queue`, `schema`, `sources`), the page does
not exist, or the resulting store fails the whole-store wiki lint — for example
the removal would leave a dead `[[slug]]` wikilink in another page — then the
verb SHALL restore the affected files byte-for-byte, exit non-zero, and name the
reason (naming the linking page for a stranded wikilink). On a clean removal
inside a git work tree, the verb SHALL auto-commit exactly the touched files
with subject `shipd-wiki: remove <slug>`, following the wiki auto-commit semantics
(no commit attempted outside git; a failed commit never fails the removal).

#### Scenario: Successful removal updates page, index, and log
- **WHEN** `wiki-remove some-page` runs where `wiki/some-page.md` exists, is
  indexed, and no other page links to it
- **THEN** the page file and its index entry are gone, `log.md` gains a dated
  `remove | some-page` entry, and in a git work tree a commit scoped to the
  touched files exists with subject `shipd-wiki: remove some-page`

#### Scenario: Inbound wikilink blocks removal
- **WHEN** `wiki-remove some-page` runs while another page contains
  `[[some-page]]`
- **THEN** the verb exits non-zero naming the linking page and the store is
  restored byte-for-byte

#### Scenario: Missing page refused
- **WHEN** `wiki-remove no-such-page` runs and `wiki/no-such-page.md` does not
  exist
- **THEN** the verb exits non-zero naming the missing page and writes nothing

#### Scenario: Reserved slug refused
- **WHEN** `wiki-remove index` runs
- **THEN** the verb exits non-zero citing the reserved slug and writes nothing

#### Scenario: Personal store removal
- **WHEN** `wiki-remove some-page --personal` runs on the personal memory store
- **THEN** it resolves `<memory_dir>/wiki` by fixed path and removes the page
  there, leaving the workspace store untouched

#### Scenario: Non-git store removal succeeds without a commit
- **WHEN** a valid removal runs on a store that is not inside a git work tree
- **THEN** the removal installs, the exit code is zero, and no commit is
  attempted

### Requirement: Workspace board report
id: workspace-board-report

When `show` runs with no name given and no spec selected, the status CLI
SHALL print a workspace board report derived from the spec tree alone, in
order: a `N specs · N epics · N initiatives` totals line — members summed
across every epic, the epic count, and the distinct `Initiative:` slugs
across epic files, matching the board header's totals; a `shipped <n>/<m>`
line over every rendered row (epic members plus standalone changes), `n`
counting those whose lane is `shipped`; a blank line; then the four board
lanes in board order — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each
printed as a `<LANE> (<count>)` header even when its count is 0.

The report SHALL obtain its universes through the engine's shared
universe-discovery seam (shipd-workspace workspace-universe-discovery),
never a private reimplementation: the invocation root's own universe always
— its epics discovered by probing the invocation root first, then each
`.worktrees/<name>` directory under it in sorted name order, resolving each
candidate's content directory independently, skipping unreadable
candidates, the invocation root winning a slug hosted in both — plus, for a
workspace-level invocation, one universe per declared project repo the seam
yields, each aggregated exactly as an invocation root is (its own epics,
worktrees, member-state derivation, and standalone-change discovery, all
relative to that repo). When the seam yields no project universes, the
report SHALL cover only the invocation root's universe and its output SHALL
be byte-identical to the single-universe rendering. Epic slugs SHALL NOT be
deduplicated across universes; totals sum across every universe and
`initiatives` counts distinct slugs across universes.

In the non-shipped lanes each member SHALL print as one indented row
carrying its epic's slug (or `standalone` for a change planned outside any
epic), the member slug, its derived state, `risk <value>` (`?` when absent),
a `[worktree]` marker when its state was derived from a worktree of its
owning universe, and — for a row from a project universe — a `[<project>]`
marker after the worktree marker position. The `SHIPPED` lane SHALL print
rollup rows counted per epic per owning project — `<epic-slug> (<n>)` for
invocation-root rows, `<epic-slug> [<project>] (<n>)` for project rows, plus
`standalone` rollups last within each universe's grouping — never flat
member rows. Rows SHALL collect epics first (the invocation root's, then
each project universe's in slug order), then standalone changes in the same
universe order. Lanes SHALL derive from the shared state→lane projection,
and standalone changes SHALL be discovered by the same single implementation
the dashboard's board aggregation consumes, per universe with that
universe's own member-slug exclusion set. An unreadable epic file SHALL be
skipped, never raised.

#### Scenario: Bare show reports the workspace
- **GIVEN** a repository with epics and no spec selected
- **WHEN** `show` runs with no argument
- **THEN** the totals line, the `shipped <n>/<m>` line, and all four lane
  headers with counts are printed, and the exit code is 0

#### Scenario: Non-shipped rows carry their epic context
- **GIVEN** an epic `e1` with an unplanned member `m1`
- **WHEN** the workspace report prints
- **THEN** `m1`'s row sits under `UNPLANNED` and carries `e1`, `m1`, the
  state `unplanned`, and its risk

#### Scenario: Shipped lane rolls up per epic
- **GIVEN** two epics each with archived members
- **WHEN** the workspace report prints
- **THEN** the `SHIPPED` lane holds one `<epic-slug> (<n>)` row per epic
  and no flat member rows

#### Scenario: A standalone change folds in
- **GIVEN** a change planned under `planned/` whose plan carries no `Epic:`
  header and whose slug appears in no epic
- **WHEN** the workspace report prints
- **THEN** it appears as a row under its lane with the epic column
  `standalone`

#### Scenario: A worktree-authored epic counts in the report
- **GIVEN** an epic whose `epic.md` exists only under a
  `.worktrees/<name>` content directory
- **WHEN** the workspace report prints from the invocation root
- **THEN** the epic count includes it, its members are summed into the
  totals, and its member rows render under their lanes

#### Scenario: Declared project epics aggregate at workspace level
- **GIVEN** a workspace root whose registry declares a project whose repo
  directory holds an epic with members
- **WHEN** `show` runs bare from the workspace root
- **THEN** the epic counts in the totals, its member rows render under
  their lanes with the project's `[<slug>]` marker, and their states derive
  from the project repo

#### Scenario: Inside a member repo the board stays per-repo
- **GIVEN** the same workspace, invoked from inside a declared project repo
- **WHEN** `show` runs bare there
- **THEN** only that repo's universe is reported — no other project's epics
  appear and no `[<slug>]` markers print

#### Scenario: A project's standalone change folds in
- **GIVEN** a declared project repo holding a change planned outside any
  epic
- **WHEN** the workspace report prints from the workspace root
- **THEN** the change appears under its lane with the epic column
  `standalone` and the project's marker

#### Scenario: An absent project repo is skipped
- **GIVEN** a registry declaring a repo path that is not a directory on
  this machine
- **WHEN** the workspace report prints from the workspace root
- **THEN** the report renders without error and without that repo's
  universe

#### Scenario: Same epic slug in two projects stays distinct
- **GIVEN** two declared project repos each hosting an epic with the same
  slug
- **WHEN** the workspace report prints from the workspace root
- **THEN** both epics count and their rows are distinguished by their
  project markers

### Requirement: JSON output mode
id: json-output

The status CLI's read verbs — `show`, `status`, `locate`, `epic-show`, and
`workspace-show` — SHALL accept a `--json` flag that emits exactly one JSON
document on stdout and nothing else, derived from the same data as the text
rendering: `status` an object with `name`, `kind` (`change` or `epic`), and
`status`; `show` on a change an object with `name`, `kind`, `status`,
`tasks` (done/in_progress/total counts, or null when no checklist exists),
and `metadata`; `show`'s epic fallback and `epic-show` an object with
`name`, `kind": "epic"`, `status`, `metadata`, `worktree` (the hosting
worktree name or null), `project` (the owning declared project's slug when
the epic resolved from a project universe, else null), `shipped` counts,
and the four board `lanes` with member entries carrying `slug`, `state`,
`risk`, and a `worktree` boolean; the bare `show` workspace report an
object with `kind": "workspace"`, `totals`, `shipped`, and `lanes` whose
rows each carry a `project` field — the owning declared project's slug for
a row aggregated from a project universe, `null` for a row from the
invocation root's own universe; `locate` an array of objects with `change`,
`root`, `dir`, `status`, and `project` (the owning declared project's slug,
or `null` for a match from the invocation root's own universe); and
`workspace-show` an object mirroring the text report's fields. Without the
flag, the text output SHALL stay byte-identical to its pre-flag behavior,
and error handling (stderr `Error:` lines, exit codes) SHALL be unchanged in
both modes.

#### Scenario: Status of a change is machine-readable
- **WHEN** `status <change> --json` runs on an existing change
- **THEN** stdout parses as one JSON object with `kind` `change` and its
  status value

#### Scenario: Epic report is machine-readable
- **WHEN** `epic-show <slug> --json` runs
- **THEN** stdout parses as one JSON object with `kind` `epic`, the four
  lanes, and each member's slug, state, risk, and worktree flag

#### Scenario: A project-hosted epic's report carries its project
- **GIVEN** a workspace root whose declared project repo hosts the epic
- **WHEN** `epic-show <slug> --json` runs from the workspace root
- **THEN** the object's `project` is that project's slug, and a root-hosted
  epic's `project` is null

#### Scenario: Workspace report is machine-readable
- **WHEN** `show --json` runs with no name and no selection
- **THEN** stdout parses as one JSON object with `kind` `workspace` and the
  totals matching the text report's counts

#### Scenario: Workspace report rows carry their project
- **GIVEN** a workspace root with one declared project repo holding an epic
- **WHEN** `show --json` runs bare from the workspace root
- **THEN** the project repo's rows carry its slug in `project` and the
  invocation root's own rows carry `project` null

#### Scenario: Locate rows are an array
- **WHEN** `locate <change> --json` runs for a change hosted in a worktree
- **THEN** stdout parses as a JSON array whose entries carry change, root,
  dir, status, and a null `project`

#### Scenario: Text mode is unchanged without the flag
- **WHEN** any of the five verbs runs without `--json`
- **THEN** the output is byte-identical to the pre-change text rendering

#### Scenario: Errors are unaffected by the flag
- **WHEN** `status no-such-thing --json` runs for a name matching nothing
- **THEN** the behavior matches the flagless form (`?` on stdout per the
  status contract), and a fatal error path still prints `Error:` to stderr
  with a nonzero exit

### Requirement: Epic token breakdown aggregation
id: epic-token-breakdown

When `epic-sync` runs on a non-draft epic, it SHALL also rewrite the epic
file's trailing `## Token usage breakdown` section: a
`Tool | Calls | Output tokens` markdown table (rows sorted by output tokens
descending, a bold `**Total**` row) summing, per tool, the
`## Token usage breakdown` tables found in the epic's members' archived
`tasks.md` files — each member resolved the way the status derivation
already resolves member state, a member with no archived table or an
unparseable one contributing nothing. The rewrite SHALL be idempotent
(replacing an existing section, preserving all other content), and if no
member carries a table, then the epic SHALL end with no
`## Token usage breakdown` section (an existing one removed). The draft-epic
guard is unchanged: a draft epic's file is never touched.

#### Scenario: Member tables sum into the epic table
- **WHEN** `epic-sync` runs on an epic with two archived members whose
  `tasks.md` tables each show `Bash` with 100 output tokens and one call
- **THEN** the epic's trailing section shows a `Bash` row with 200 output
  tokens and 2 calls, and a `**Total**` row of 200

#### Scenario: A re-run is idempotent
- **WHEN** `epic-sync` runs twice with unchanged members
- **THEN** the second run leaves the epic file byte-identical

#### Scenario: A member without a table contributes nothing
- **WHEN** one member's archived `tasks.md` has no breakdown section
- **THEN** the epic table sums only the other members' tables and the sync
  raises no error

#### Scenario: No member tables, no epic section
- **WHEN** no member's archived `tasks.md` carries a breakdown table
- **THEN** the synced epic file carries no `## Token usage breakdown`
  section, even if one existed before

#### Scenario: A draft epic is untouched
- **WHEN** `epic-sync` runs on a `draft` epic
- **THEN** the epic file is not modified

### Requirement: Related-artifacts search verb
id: related-verb

The status CLI SHALL provide `related <term> [<term>...]` ranking the spec
library's artifacts by case-insensitive term-hit count: for each artifact, the
sum over all terms of substring occurrence counts across the artifact's files,
searching the resolved content directory's `verified/<slug>/spec.md` (kind
`verified`), `planned/<slug>/` artifact files (`plan.md`, `tasks.md`, delta
`specs/*/spec.md`; kind `planned`), `completed/*-<slug>/` artifact files (kind
`completed`, the slug printed with its `YYYY-MM-DD-` prefix stripped),
`research/<slug>/report.md` (kind `research`), and `epics/<slug>/epic.md`
(kind `epic`), and — where a workspace is discoverable — the workspace wiki
store's `wiki/<slug>.md` pages (kind `wiki`). The CLI SHALL print one keyed
block per matching artifact (`kind:`, `slug:`, `score:`, `path:`, the path
relative to the root when inside it and absolute otherwise) in descending
score order with ties broken by kind then slug, SHALL omit artifacts with no
hits, SHALL cap the printed blocks at ten followed by a single line naming the
count of remaining matches when more matched, and SHALL accept a `--json`
flag emitting exactly one JSON array of objects with those four keys instead.
If no artifact matches, then the CLI SHALL exit non-zero with a single
`Error:` line. Where no workspace or wiki store is discoverable, the CLI
SHALL skip the wiki surface silently and still search every other surface;
a missing corpus directory SHALL likewise be skipped without error.

#### Scenario: Matches print ranked keyed blocks
- **WHEN** `related export` runs in a repo where a verified capability's
  spec.md contains `export` three times and a completed change's plan.md
  contains it once
- **THEN** both artifacts print as keyed blocks with `kind:`, `slug:`,
  `score:`, and `path:`, the verified capability first

#### Scenario: Completed slug feeds the cat verb
- **WHEN** `related <term>` matches only `completed/2026-08-14-my-change/`
- **THEN** the block prints `slug: my-change`, so `cat change my-change`
  reads the match

#### Scenario: JSON mode is one array
- **WHEN** `related export --json` runs with at least one match
- **THEN** stdout parses as exactly one JSON array whose objects carry
  `kind`, `slug`, `score`, and `path`

#### Scenario: Output caps at ten with a remainder line
- **WHEN** `related <term>` matches twelve artifacts
- **THEN** exactly ten keyed blocks print, followed by one line naming the
  two remaining matches

#### Scenario: No match is an error
- **WHEN** `related zzz-no-such-term` runs and nothing contains the term
- **THEN** the CLI prints a single `Error:` line to stderr and exits
  non-zero

#### Scenario: Absent workspace degrades silently
- **WHEN** `related <term>` runs in a repo with no discoverable workspace
  and the term hits a verified spec
- **THEN** the verified match prints, no wiki error appears, and the exit
  code is `0`

### Requirement: Layout init verb
id: layout-init-verb

The status CLI SHALL provide an `init` verb that resolves the content
directory from the root's layered configuration and creates the `verified/`,
`planned/`, `completed/`, and `research/` directories under it — creating the
content directory itself and any missing parents — without modifying or
removing anything that already exists. For each of the four directories the
verb SHALL print one line, `created <path>/` when it made the directory and
`exists <path>/` when it was already a directory (`<path>` relative to the
root), followed by the summary line `all shipd directories are ready`, and
SHALL exit `0` whether it created all, some, or none of them. If the content
directory or any of the four targets exists as a non-directory, the verb
SHALL create nothing, report the offending path via the standard `Error:`
convention, and exit non-zero.

#### Scenario: Fresh repository gets the full layout
- **WHEN** `spec_status.py init --root <dir>` runs against a directory with
  no content directory
- **THEN** `<dir>/.shipd/verified`, `<dir>/.shipd/planned`,
  `<dir>/.shipd/completed`, and `<dir>/.shipd/research` exist afterward, each
  is reported `created`, and the run exits `0` ending with
  `all shipd directories are ready`

#### Scenario: Existing content is never clobbered
- **WHEN** `init` runs against a root whose `verified/` already holds a
  capability spec and whose `research/` already holds a report while
  `planned/` and `completed/` are missing
- **THEN** the existing spec and report files are untouched, `verified` and
  `research` are reported `exists`, the two missing directories are reported
  `created`, and the run exits `0`

#### Scenario: Idempotent re-run
- **WHEN** `init` runs a second time against an already-initialized root
- **THEN** all four directories are reported `exists` and the run still
  exits `0` with the ready summary

#### Scenario: Non-directory blocker refuses
- **WHEN** a regular file occupies the content-directory path or one of the
  four target paths
- **THEN** the verb creates no directory, prints an `Error:` line naming the
  offending path, and exits non-zero

#### Scenario: Configured content directory is honored
- **WHEN** the root's configuration declares `"dir": "specs"` and `init` runs
- **THEN** the layout is created under `specs/`, not `.shipd/`
