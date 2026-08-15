# spec-io

### Requirement: Staged emission with validate-then-install
id: staged-emission

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
validate it with the video brief checks. If the destination already exists,
then the command SHALL refuse unless `--replace` is given.

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

### Requirement: Mediated spec reads
id: mediated-read-verb

The status CLI SHALL provide `cat change|verified|epic|initiative|research|video
<slug>` printing the named artifact's content — for a change, its `plan.md`,
every delta spec, and `tasks.md`; for research, the report at the resolved
`<content-dir>/research/<slug>/report.md`; for video, the brief at the resolved
`<content-dir>/video/<slug>/brief.md` — each file preceded by a
`--- <relpath>` separator line, resolving all locations through the engine's
configuration. For a change, the CLI SHALL resolve `planned/<slug>/` first
and, when absent, SHALL fall back to the archived `completed/*-<slug>/`
directory, selecting the newest (lexicographically last) archive when several
match. An unknown name SHALL exit non-zero with an error.

#### Scenario: Change contents print with separators
- **WHEN** `cat change my-change` runs on a change with one delta spec
- **THEN** stdout holds three `--- <relpath>` separators followed by each
  file's content

#### Scenario: Completed change still prints after archive
- **WHEN** `cat change my-change` runs after the change was archived to
  `completed/2026-08-14-my-change/`
- **THEN** stdout prints that archive's artifacts with `--- <relpath>`
  separators instead of exiting non-zero

#### Scenario: Research report prints with a separator
- **WHEN** `cat research payment-apis` runs on an installed report
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  report's content

#### Scenario: Video brief prints with a separator
- **WHEN** `cat video board-walkthrough` runs on an installed brief
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  brief's content

#### Scenario: Unknown name errors
- **WHEN** `cat epic no-such-epic` runs
- **THEN** the CLI exits non-zero naming the missing epic

### Requirement: Engine-mediated skill access
id: engine-mediated-skill-access

Skills SHALL create and modify spec content only through engine verbs
(`spec_emit.py`, the status CLI's transition and header verbs, the merge
engine) and SHALL obtain spec content and locations only from engine output
(`cat`, `config-show`, show verbs). A skill SHALL NOT construct a storage
path from naming convention in either direction.

#### Scenario: Planning emits through the engine
- **WHEN** `/s:plan` reaches emission
- **THEN** the artifacts are authored in a staging area and installed via
  `spec_emit.py change`, not written directly into the spec tree

#### Scenario: Briefs are written through the engine
- **WHEN** `/s:initiative new` authors a brief
- **THEN** the brief reaches the workspace via `spec_emit.py initiative`,
  and the skill never writes to a workspace path it composed itself

### Requirement: Staged wiki emission
id: wiki-emission

The emit engine SHALL provide a `wiki` subcommand installing a staged store
subset — `wiki/<slug>.md` pages, `index.md`, `log.md`, `queue.md`, and
`sources/<file>` additions — into the workspace wiki: it SHALL back up the
affected store files, install the staged set (overwriting existing pages and
top-level files), validate the resulting whole store with the wiki lint, and
if any finding is reported, then it SHALL restore the backup and exit non-zero
so an invalid store state never lands. If a staged `sources/` file already
exists in the store, then the emission SHALL be refused before any install
(sources are immutable). The `wiki` subcommand SHALL accept a `--personal` flag:
when set, it SHALL install into the personal memory store at `<memory_dir>/wiki`
(default `~/.shipd-memory/wiki`), resolved by fixed path and bypassing workspace
discovery, instead of the workspace store, with the identical backup, lint, and
restore semantics.

#### Scenario: Page install with index update
- **WHEN** `spec_emit.py wiki --from <staging>` stages a new page and an
  `index.md` cataloging it
- **THEN** both land in the store and the command reports the install and
  exits zero

#### Scenario: Invalid result rolls back
- **WHEN** the staged set would leave a dead wikilink or an unindexed page
- **THEN** the store's prior content is restored byte-for-byte and the command
  exits non-zero printing the findings

#### Scenario: Source overwrite refused
- **WHEN** the staging dir holds `sources/notes.md` and the store already has
  `sources/notes.md`
- **THEN** nothing is installed and the command exits non-zero citing source
  immutability

#### Scenario: Personal flag installs into the memory store
- **WHEN** `spec_emit.py wiki --from <staging> --personal` runs
- **THEN** the staged set installs into `<memory_dir>/wiki` (default
  `~/.shipd-memory/wiki`) by fixed path, with the same lint and rollback
  guarantees, and the workspace store is untouched
