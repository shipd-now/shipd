# shipd-teach

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
grammar and cite their backing repo artifacts by name. Where `wiki-show`
reports a present base store, the scan SHALL also read the base store's index
(and candidate pages) through the same engine reads rooted at the base store
path, and SHALL NOT stage a job-store page duplicating a surface a base page
already covers — base-worthy updates route through promotion instead. Where
the workspace declares a `focus` project, the scan SHALL prefer that
project's surfaces first. A single run SHALL bound its distillation to 5–15
page touch-ups, preferring decision-dense surfaces, and SHALL update existing
pages rather than create duplicates.

#### Scenario: Distilled page cites its artifact
- **WHEN** a run distills an epic's Decisions into a wiki page
- **THEN** the staged page names the backing artifact (e.g.
  `epic/mikk-knowledge`) so a reader can verify the position

#### Scenario: Run is bounded
- **WHEN** the repo's surfaces would yield more pages than the bound
- **THEN** the run touches at most 15 pages and its log entry records the
  coverage so a later run continues

#### Scenario: Base page is not duplicated
- **GIVEN** a present base store holding a page covering a surface
- **WHEN** a run distills that surface
- **THEN** no near-duplicate job-store page is staged for it

### Requirement: Gap-and-contradiction interview
id: teach-gap-interview

The skill SHALL interview the user only about gaps and contradictions its
scan surfaces and promote-to-base offers its classification produces, batched
into one round in the plugin's question shape: a visible context brief first,
then plain-text numbered options-first questions with the recommendation
listed first, answered by typed reply. If the scan surfaces no gaps,
contradictions, or promotion offers, then the skill SHALL run no interview.
Where the user defers an interview item, the skill SHALL queue it via
`wiki-queue-add` in the compact-question shape (decision, options,
recommendation).

#### Scenario: Nothing surfaced means no interview
- **WHEN** a run's scan finds no gaps, contradictions, or promotion offers
- **THEN** the skill ingests the distilled pages without asking the user
  anything

#### Scenario: Deferred item is queued
- **WHEN** the user defers an interview question
- **THEN** `queue.md` gains a `## q-<slug>` block for it with
  `Answer: pending`

#### Scenario: Promotion offers join the single round
- **GIVEN** a run whose classification marks a page job-independent
- **WHEN** the interview round opens
- **THEN** the promotion offer appears in that same batched round rather than
  a separate one

### Requirement: Queue draining
id: teach-queue-drain

The skill SHALL drain answered queue entries: every `## q-` block in
`queue.md` whose `Answer:` line is not `pending` SHALL be distilled into wiki
page content and removed from the staged `queue.md` in the same ingest, with
the run's log entry naming each drained `q-<slug>`. Where a drained block's
`Answer:` value begins with the `advisory: ` prefix, the distilled page
content SHALL carry an `Authority: advisory` line, preserving the advisory
standing so the oracle relays it as a recommendation rather than a
settlement; answers without the prefix distill as binding pages with no
`Authority:` line, as before. Blocks whose `Answer:` is `pending` SHALL be
left untouched.

#### Scenario: Answered entry is drained
- **WHEN** a run finds a queue block with a supplied answer
- **THEN** after the ingest the answer's content lives in a wiki page, the
  block is gone from `queue.md`, and the log entry names its `q-<slug>`

#### Scenario: Advisory answer drains into an advisory page
- **GIVEN** a queue block whose answer line reads
  `- Answer: advisory: always run the unlock first`
- **WHEN** a run drains it
- **THEN** the distilled page carries an `Authority: advisory` line and the
  block is gone from `queue.md`

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

### Requirement: Promote-to-base routing
id: teach-promote-to-base

Writes SHALL default to the job store — the discovered workspace's own wiki.
Where `wiki-show` reports a present base store, the skill SHALL classify each
distilled page and drained answer as job-scoped (the default) or
job-independent, and SHALL offer promotion of job-independent content in the
interview round. Content the user promotes SHALL install into the base store
through its own staged `spec_emit.py wiki --from <staging>` invocation rooted
at the base store path, carrying the base store's own full `index.md` and a
dated `log.md` entry, and SHALL NOT additionally land in the job store.
Staged pages SHALL NOT carry `[[wikilink]]`s to pages that live only in the
other store. Promotion SHALL never remove an existing job-store page. When no
base store is declared or the declared base is absent, all content SHALL land
in the job store and no promotion SHALL be offered.

#### Scenario: Default is the job store
- **WHEN** a run ingests where no `wiki_base` is declared
- **THEN** every staged file installs into the job store and no promotion is
  offered

#### Scenario: Promoted content lands in the base
- **GIVEN** a workspace whose `wiki-show` reports a present base store
- **WHEN** the user accepts promotion of a job-independent page
- **THEN** the page installs into the base store with matching base
  `index.md` and `log.md` bookkeeping, and the job store gains no copy of it

#### Scenario: Wikilinks stay store-local
- **WHEN** a run stages content for either store
- **THEN** no staged page links `[[…]]` to a page that exists only in the
  other store

#### Scenario: Promotion never removes job pages
- **WHEN** a run promotes content to the base
- **THEN** no existing job-store page is removed

### Requirement: Ledger-entry reference mode
id: teach-qa-reference

When the invocation argument matches `<change> Q<n>`, the skill SHALL bypass
the distillation sweep: it SHALL resolve the change through the engine's
`cat change` read (covering planned and archived-completed changes), print the
referenced `### Q<n>:` ledger entry in full so the user sees exactly what was
asked and answered, and interview the user for the corrected standing
position. The skill SHALL then install the correction through the staged wiki
emit — updating the page an `ANSWER` entry's `**Cited:**` field names when one
exists rather than minting a duplicate, preserving the user's correction
verbatim as a dated `sources/` file, and draining the queue block named by an
`INSUFFICIENT` entry's `**Queued:**` field in the same ingest when that block
is still queued. If the change cannot be resolved or the referenced entry does
not exist, then the skill SHALL report that and stop without writing.

#### Scenario: Entry is shown and the correction lands on the cited page
- **WHEN** `/s:teach dark-mode-toggle Q1` names an `ANSWER` entry citing
  `[[logging-conventions]]` and the user supplies a corrected position
- **THEN** the skill prints the entry in full and the staged emit updates
  `[[logging-conventions]]` with the corrected standing position

#### Scenario: Queued entry is drained with the correction
- **WHEN** the referenced entry carries `**Queued:** q-report-format` and that
  block is still in the wiki queue
- **THEN** the ingest drains `q-report-format` alongside installing the
  correction

#### Scenario: Unresolvable reference stops without writing
- **WHEN** the argument names a change with no `Q<n>` entry of that number
- **THEN** the skill reports the missing entry and writes nothing
