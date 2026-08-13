## ADDED Requirements

### Requirement: Teach skill entry
id: teach-skill

The plugin SHALL provide `/s:teach` at `plugins/s/skills/teach/SKILL.md`,
which SHALL announce the running plugin version in its first user-visible
status sentence and SHALL run the intake flow: resolve the workspace wiki
store, scan and distill the repo's spec artifacts, interview only on gaps and
contradictions, and ingest through the staged emit verb. When the workspace
has no wiki store, the skill SHALL scaffold it with `wiki-init`; if no
workspace is discoverable, then the skill SHALL stop and point the user at
`workspace-init` instead of inventing a store location.

#### Scenario: Skill file carries the flow
- **WHEN** `plugins/s/skills/teach/SKILL.md` is inspected
- **THEN** it directs the version announcement and the
  resolve → scan → distill → interview → ingest flow with `wiki-init`
  scaffolding for a missing store

#### Scenario: No workspace stops with guidance
- **WHEN** the skill runs where no ancestor declares a workspace
- **THEN** it stops, names the missing workspace, and points at
  `workspace-init` — no store is created or written

### Requirement: Distillation scan
id: teach-distill-scan

The skill SHALL scan the invoking repo's spec surfaces through engine reads
only — `cat epic <slug>` (Decisions/Design), `cat verified <capability>`,
`cat research <slug>`, `project-show`, and completed changes' plan decisions —
together with the existing wiki (`cat wiki index`, then candidate pages), and
SHALL distill entity/convention pages that follow the store's `schema.md`
grammar and cite their backing repo artifacts by name. A single run SHALL
bound its distillation to 5–15 page touch-ups, preferring decision-dense
surfaces, and SHALL update existing pages rather than create duplicates.

#### Scenario: Distilled page cites its artifact
- **WHEN** a run distills an epic's Decisions into a wiki page
- **THEN** the staged page names the backing artifact (e.g.
  `epic/mikk-knowledge`) so a reader can verify the position

#### Scenario: Run is bounded
- **WHEN** the repo's surfaces would yield more pages than the bound
- **THEN** the run touches at most 15 pages and its log entry records the
  coverage so a later run continues

### Requirement: Gap-and-contradiction interview
id: teach-gap-interview

The skill SHALL interview the user only about gaps and contradictions its
scan surfaces, batched into one round in the plugin's question shape: a
visible context brief first, then plain-text numbered options-first questions
with the recommendation listed first, answered by typed reply. If the scan
surfaces no gaps or contradictions, then the skill SHALL run no interview.
Where the user defers an interview item, the skill SHALL queue it via
`wiki-queue-add` in the compact-question shape (decision, options,
recommendation).

#### Scenario: Nothing surfaced means no interview
- **WHEN** a run's scan finds no gaps or contradictions
- **THEN** the skill ingests the distilled pages without asking the user
  anything

#### Scenario: Deferred item is queued
- **WHEN** the user defers an interview question
- **THEN** `queue.md` gains a `## q-<slug>` block for it with
  `Answer: pending`

### Requirement: Queue draining
id: teach-queue-drain

The skill SHALL drain answered queue entries: every `## q-` block in
`queue.md` whose `Answer:` line is not `pending` SHALL be distilled into wiki
page content and removed from the staged `queue.md` in the same ingest, with
the run's log entry naming each drained `q-<slug>`. Blocks whose `Answer:` is
`pending` SHALL be left untouched.

#### Scenario: Answered entry is drained
- **WHEN** a run finds a queue block with a supplied answer
- **THEN** after the ingest the answer's content lives in a wiki page, the
  block is gone from `queue.md`, and the log entry names its `q-<slug>`

#### Scenario: Pending entries survive
- **WHEN** a run ingests while `queue.md` holds `Answer: pending` blocks
- **THEN** those blocks remain in `queue.md` unchanged

### Requirement: Staged ingest bookkeeping
id: teach-ingest-bookkeeping

The skill SHALL write to the store exclusively by authoring the touched
subset in a staging directory and installing it with
`spec_emit.py wiki --from <staging>` — never by editing store files in
place. Every ingest SHALL keep `index.md` entries in step with the touched
pages and SHALL append a dated `log.md` entry describing the run. Interview
and drained-queue answers SHALL be preserved verbatim as a dated add-only
file under `sources/`; repo artifacts SHALL never be copied into `sources/`.

#### Scenario: Ingest goes through the staged verb
- **WHEN** `plugins/s/skills/teach/SKILL.md` is inspected
- **THEN** it directs staging plus `spec_emit.py wiki --from` as the only
  store write path and forbids in-place store edits

#### Scenario: Bookkeeping accompanies every ingest
- **WHEN** a run installs distilled pages
- **THEN** the staged set carries matching `index.md` entries and a dated
  `log.md` entry, and any user-supplied answers land as a new `sources/`
  file
