## MODIFIED Requirements

### Requirement: Staged emission with validate-then-install
id: staged-emission
base: aa49f3e2c0ab

A stdlib-Python `spec_emit.py` SHALL install spec content only after
validation: `change <name> --from <staging-dir>` SHALL copy the staged
artifact set to the resolved `<content-dir>/planned/<name>/`, run the
linter's change checks in-process, and on any finding remove everything it
installed and exit non-zero with the findings — an invalid change SHALL
never remain in the tree. `initiative <slug> --from <file>` SHALL install a
brief at the workspace's resolved brief path and validate it with the
initiative checks under the same remove-on-failure rule; `epic <slug>
--from <file>` likewise with the epic checks; `research <slug> --from
<file>` likewise SHALL install a research report at the resolved
`<content-dir>/research/<slug>/report.md` and validate it with the research
report checks; `video <slug> --from <file>` likewise SHALL install a video
intent brief at the resolved `<content-dir>/video/<slug>/brief.md` and
validate it with the video brief checks; `docs <slug> --from <file>`
likewise SHALL install a document at the resolved
`<content-dir>/docs/<slug>/doc.md` and validate it with the docs document
checks; `prd <slug> --from <file>` SHALL install a PRD at the workspace's
resolved `<content-dir>/prds/<slug>/prd.md` and validate it with the PRD
checks under the same remove-on-failure rule, exiting non-zero with an error
naming the missing workspace when none is discoverable. If the destination already exists, then the command SHALL refuse
unless `--replace` is given.

#### Scenario: Clean staged change is installed
- **GIVEN** a staging directory holding a lint-clean plan.md, delta specs,
  and tasks.md
- **WHEN** `spec_emit.py change my-change --from <staging>` runs
- **THEN** `<content-dir>/planned/my-change/` holds the artifacts and the
  exit code is zero

#### Scenario: Invalid staged change never lands
- **WHEN** `spec_emit.py change my-change --from <staging>` runs on staged
  artifacts with a lint error
- **THEN** the findings are printed, the exit code is non-zero, and
  `<content-dir>/planned/my-change/` does not exist

#### Scenario: Existing destination is refused
- **GIVEN** `<content-dir>/planned/my-change/` already exists
- **WHEN** the command runs without `--replace`
- **THEN** it refuses non-zero and the existing content is untouched

#### Scenario: Clean staged report is installed
- **WHEN** `spec_emit.py research payment-apis --from <staging report>` runs
  on a report passing the research checks
- **THEN** `<content-dir>/research/payment-apis/report.md` holds the report
  and the exit code is zero

#### Scenario: Invalid staged report never lands
- **WHEN** `spec_emit.py research payment-apis --from <staging report>` runs
  on a report with an unresolved citation marker
- **THEN** the findings are printed, the exit code is non-zero, and
  `<content-dir>/research/payment-apis/` does not exist

#### Scenario: Clean staged brief is installed
- **WHEN** `spec_emit.py video board-walkthrough --from <staging brief>` runs
  on a brief passing the video brief checks
- **THEN** `<content-dir>/video/board-walkthrough/brief.md` holds the brief
  and the exit code is zero

#### Scenario: Invalid staged brief never lands
- **WHEN** `spec_emit.py video board-walkthrough --from <staging brief>` runs
  on a brief whose intent carries no citation marker
- **THEN** the findings are printed, the exit code is non-zero, and
  `<content-dir>/video/board-walkthrough/` does not exist

#### Scenario: Clean staged document is installed
- **WHEN** `spec_emit.py docs payments-strategy --from <staging doc>` runs
  on a titled document
- **THEN** `<content-dir>/docs/payments-strategy/doc.md` holds the document
  and the exit code is zero

#### Scenario: Invalid staged document never lands
- **WHEN** `spec_emit.py docs payments-strategy --from <staging doc>` runs
  on a document whose first line is not a non-empty `# <title>`
- **THEN** the findings are printed, the exit code is non-zero, and
  `<content-dir>/docs/payments-strategy/` does not exist

#### Scenario: Existing document is refused without --replace
- **GIVEN** `<content-dir>/docs/payments-strategy/doc.md` already exists
- **WHEN** `spec_emit.py docs payments-strategy --from <staging doc>` runs
  without `--replace`
- **THEN** it refuses non-zero and the existing document is untouched

#### Scenario: PRD emit installs to the workspace
- **GIVEN** a discoverable workspace and a lint-clean PRD file
- **WHEN** `spec_emit.py prd mobile-push --from <file>` runs
- **THEN** the workspace's `prds/mobile-push/prd.md` holds the content and
  the exit code is zero

#### Scenario: Invalid PRD is not installed
- **WHEN** `spec_emit.py prd mobile-push --from <file>` runs with a file
  missing its tier sections
- **THEN** the findings print, nothing remains installed, and the exit code
  is non-zero

#### Scenario: PRD emit without a workspace is an error
- **WHEN** `spec_emit.py prd mobile-push --from <file>` runs where no
  workspace is discoverable
- **THEN** the command exits non-zero naming the missing workspace


### Requirement: Mediated spec reads
id: mediated-read-verb
base: 3ebb88c12710

The status CLI SHALL provide `cat
change|verified|epic|initiative|prd|research|video|docs <slug>` printing the
named artifact's content — for a change, its `plan.md`, every delta spec,
and `tasks.md`; for research, the report at the resolved
`research/<slug>/report.md`; for video, the brief at the resolved
`video/<slug>/brief.md`; for docs, the document at the resolved
`docs/<slug>/doc.md` — each file preceded by a `--- <relpath>` separator
line (the path relative to the invocation root when inside it, absolute
otherwise), resolving all locations through the engine's configuration.

For the kinds `change`, `verified`, `epic`, `research`, `video`, and `docs`,
the CLI SHALL resolve the artifact across the universes the engine's shared
universe-discovery seam yields (shipd-workspace
workspace-universe-discovery) — the invocation root's own universe first, then
each declared project universe in slug order — probing, within each universe,
the universe root first and then each `.worktrees/<name>` directory under it
in sorted name order, resolving the content directory independently per
candidate root and skipping a candidate whose configuration is unreadable.
The first candidate holding the artifact SHALL win, so the invocation root
always shadows a worktree's copy of the same slug. The `initiative` kind SHALL
keep resolving through the workspace chain, and the `prd` kind SHALL
resolve through the workspace chain the same way — the nearest chain
member holding `prds/<slug>/prd.md` wins, and no resolution exits
non-zero naming the expected path. This resolution is read-only: the
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

#### Scenario: Document prints with a separator
- **WHEN** `cat docs payments-strategy` runs on an installed document
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  document's content

#### Scenario: Worktree-hosted document is readable from the root
- **WHEN** `cat docs payments-strategy` runs from a main checkout whose
  `.worktrees/<name>/` alone hosts `docs/payments-strategy/doc.md`
- **THEN** stdout prints that worktree's document and the exit code is zero

#### Scenario: Unknown name errors naming the probed roots
- **WHEN** `cat epic no-such-epic` runs and no candidate root hosts it
- **THEN** the CLI exits non-zero with an error naming the missing epic and
  the probed candidate roots

#### Scenario: PRD content is printed through the chain
- **WHEN** `cat prd mobile-push` runs where a workspace-chain member hosts
  `prds/mobile-push/prd.md`
- **THEN** the PRD's content prints with its `--- <path>` separator

#### Scenario: Unknown PRD is an error
- **WHEN** `cat prd no-such-prd` runs
- **THEN** the CLI exits non-zero naming the expected `prd.md` path

