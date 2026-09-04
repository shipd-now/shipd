## MODIFIED Requirements

### Requirement: Mediated spec reads
id: mediated-read-verb
base: e2203720e871

The status CLI SHALL provide `cat change|verified|epic|initiative|research|video
<slug>` printing the named artifact's content — for a change, its `plan.md`,
every delta spec, and `tasks.md`; for research, the report at the resolved
`research/<slug>/report.md`; for video, the brief at the resolved
`video/<slug>/brief.md` — each file preceded by a `--- <relpath>` separator
line (the path relative to the invocation root when inside it, absolute
otherwise), resolving all locations through the engine's configuration.

For the kinds `change`, `verified`, `epic`, `research`, and `video`, the CLI
SHALL resolve the artifact across the universes the engine's shared
universe-discovery seam yields (shipd-workspace
workspace-universe-discovery) — the invocation root's own universe first, then
each declared project universe in slug order — probing, within each universe,
the universe root first and then each `.worktrees/<name>` directory under it
in sorted name order, resolving the content directory independently per
candidate root and skipping a candidate whose configuration is unreadable.
The first candidate holding the artifact SHALL win, so the invocation root
always shadows a worktree's copy of the same slug. The `initiative` kind SHALL
keep resolving through the workspace chain. This resolution is read-only: the
mutating verbs keep resolving the invocation root alone.

For a change, the CLI SHALL resolve each candidate's `planned/<slug>/` first
and, when absent, SHALL fall back to that candidate's archived
`completed/*-<slug>/` directory, selecting the newest (lexicographically last)
archive when several match. If no candidate holds the artifact, then the CLI
SHALL exit non-zero with an error naming the probed candidate roots.

Where the resolved change directory carries an `artefacts/` directory holding at
least one file, `cat change` SHALL additionally print, after the artifact
contents, a `--- artefacts` header followed by one line per artefact giving its
path relative to the invocation root and its size in bytes, sorted by path. The
CLI SHALL print the artefacts' paths and sizes only, never their contents, so a
mediated read stays within the context-economy budget. Where the change carries
no such directory, or the directory holds no files, the output SHALL be exactly
what it is without the directory.

#### Scenario: Change contents print with separators
- **WHEN** `cat change my-change` runs on a change with one delta spec
- **THEN** stdout holds three `--- <relpath>` separators followed by each
  file's content

#### Scenario: Completed change still prints after archive
- **WHEN** `cat change my-change` runs after the change was archived to
  `completed/2026-08-14-my-change/`
- **THEN** stdout prints that archive's artifacts with `--- <relpath>`
  separators instead of exiting non-zero

#### Scenario: Worktree-hosted epic is readable from the root
- **WHEN** `cat epic my-epic` runs from a main checkout whose
  `.worktrees/<name>/` alone hosts `epics/my-epic/epic.md`
- **THEN** stdout prints that worktree's `epic.md` with a separator and the
  exit code is zero — the same epic `epic-show` resolves

#### Scenario: Invocation root shadows a worktree copy
- **WHEN** `cat epic my-epic` runs and both the invocation root and a worktree
  host `epics/my-epic/epic.md`
- **THEN** the invocation root's copy prints

#### Scenario: Worktree-hosted change is readable from the root
- **WHEN** `cat change my-change` runs from a main checkout where only
  `.worktrees/<name>/`'s `planned/` holds the change
- **THEN** stdout prints that worktree's artifacts and the exit code is zero

#### Scenario: Artefacts are listed, not dumped
- **WHEN** `cat change my-change` runs on a change whose `artefacts/` directory
  holds `policy.md`
- **THEN** stdout ends with a `--- artefacts` header and a line naming
  `policy.md`'s root-relative path and byte size, and the file's content does
  not appear

#### Scenario: A change without artefacts prints unchanged
- **WHEN** `cat change my-change` runs on a change with no `artefacts/`
  directory
- **THEN** stdout carries no `--- artefacts` header

#### Scenario: Research report prints with a separator
- **WHEN** `cat research payment-apis` runs on an installed report
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  report's content

#### Scenario: Video brief prints with a separator
- **WHEN** `cat video board-walkthrough` runs on an installed brief
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  brief's content

#### Scenario: Unknown name errors naming the probed roots
- **WHEN** `cat epic no-such-epic` runs and no candidate root hosts it
- **THEN** the CLI exits non-zero with an error naming the missing epic and
  the probed candidate roots
