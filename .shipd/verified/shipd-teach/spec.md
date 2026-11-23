# shipd-teach

### Requirement: Teach skill entry
id: teach-skill

The plugin SHALL provide `/s:teach` at `plugins/s/skills/teach/SKILL.md`,
which SHALL announce the running plugin version in its first user-visible
status sentence and SHALL run the intake flow: resolve the wiki store, scan
and distill the repo's spec artifacts, interview only on gaps and
contradictions, and ingest through the staged emit verb. When the resolved
store does not exist yet, the skill SHALL scaffold it with `wiki-init`.
Where no workspace is discoverable but the repo's resolved content directory
exists, the skill SHALL continue on the repo-local fallback store `wiki-show`
reports (annotated `(repo-local fallback)`), scaffolding it the same way;
only where neither a workspace nor a content directory exists SHALL the
skill stop and point the user at `workspace-init` or `shipd init` instead of
inventing a store location.

#### Scenario: Skill file carries the flow
- **WHEN** `plugins/s/skills/teach/SKILL.md` is inspected
- **THEN** it directs the version announcement and the
  resolve → scan → distill → interview → ingest flow with `wiki-init`
  scaffolding for a missing store

#### Scenario: Bare repo teaches into the fallback store
- **WHEN** the skill runs where no ancestor declares a workspace and the
  content directory exists
- **THEN** it continues on the repo-local fallback store rather than
  stopping, scaffolding it when absent

#### Scenario: Uninitialized repo stops with guidance
- **WHEN** the skill runs where no ancestor declares a workspace and no
  content directory exists
- **THEN** it stops, names both missing prerequisites, and points at
  `workspace-init` or `shipd init` — no store is created or written

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

### Requirement: Build-time teacher agent contract
id: teacher-agent-contract

The plugin SHALL ship the `s:teacher` role contract at
`plugins/s/agents/teacher.md`: a clean-context agent whose spawn message
carries only the change name and the absolute path of the plugin's build
scripts directory, and whose inputs are engine reads only — `cat change
<change>` for the plan's `## Implementation` and `## Questions and answers`,
`wiki-show --json`, `cat wiki index`, `cat wiki schema`, `cat wiki queue`,
candidate pages via `cat wiki <slug>`, and the knowledge capture and capture
durability rubrics — never builder summaries, the orchestrator's conversation,
the code, or the change's delta specs and master requirements. If `wiki-show
--json` fails or reports `present` false or `fallback` true, then the agent
SHALL write nothing and report `skipped — <reason>`. The agent SHALL classify
each candidate — ledger entries answered by USER, implementation decisions
stating a position beyond the change, and answered queue blocks (the ledger's
`Queued:` slugs first, then other answered blocks oldest first) — through the
knowledge capture rubric and, for the Durable tier, the capture durability
rubric: Include SHALL become a page, Consent-gated SHALL be withheld and named
in the report, Exclude SHALL be dropped. A candidate contradicting an existing
page SHALL write nothing and SHALL file a pending block with `wiki-queue-add
--origin "build/<change>"`. The agent SHALL touch at most five pages per run,
updating an existing page over minting a slug, citing `change/<slug>` on every
page, preserving drained answers verbatim in a dated `sources/` file, carrying
`Authority: advisory` for an `advisory: ` answer, and staging `index.md`,
`queue.md`, and `log.md` in full with a `## [YYYY-MM-DD] teach | build <change>`
entry. It SHALL write only through one `spec_emit.py wiki --from <staging>`
call carrying `--expect` with the fingerprint from its `wiki-show --json`
gate read, and on a fingerprint refusal SHALL re-read and restage `index.md`,
`queue.md`, and `log.md` once and retry, reporting `failed — store changed
during the run` on a second refusal. It SHALL never edit store files in
place, SHALL never ask a question or run `wiki-queue-answer`, and SHALL never
touch the repository, the change artifacts, or git. Its report SHALL be one
line per outcome — `taught — [[slug]] (new|updated): <summary>`,
`drained — q-<slug>`, `withheld — <item>: consent-gated`,
`queued — q-<slug>: contradiction with [[page]]`, `skipped — <reason>`,
`failed — <reason>`, or the single line `nothing durable` — closed by a
one-line count. The frontmatter SHALL pin no `model:`. The `/s:teach` skill
SHALL name the teacher as the build-time path and itself as the full sweep.

#### Scenario: Contract file carries the flow
- **WHEN** `plugins/s/agents/teacher.md` is inspected
- **THEN** it names `cat change`, `wiki-show --json`, the two rubrics, the
  five-page bound, `spec_emit.py wiki --from` as the only write, the
  `skipped`/`taught`/`drained`/`withheld`/`queued`/`failed`/`nothing durable`
  output lines, and forbids in-place store edits, questions,
  `wiki-queue-answer`, and repository writes, with no `model:` in frontmatter

#### Scenario: Nothing durable writes nothing
- **GIVEN** a change whose ledger holds only oracle-answered entries and whose
  decisions are all change-scoped, and a queue with no answered block
- **WHEN** the teacher runs
- **THEN** no staging emit runs and the report is the single line
  `nothing durable`

#### Scenario: Consent-gated knowledge is withheld
- **WHEN** a ledger answer is a workflow preference the durability rubric
  classes consent-gated
- **THEN** no page or queue block is written for it and the report carries
  `withheld — <item>: consent-gated`

#### Scenario: Answered blocks drain with their standing
- **GIVEN** an answered queue block whose answer begins `advisory: `
- **WHEN** the teacher runs against a workspace store
- **THEN** the distilled page carries `Authority: advisory`, the block is gone
  from `queue.md`, the answer sits verbatim under `sources/`, and the report
  carries `drained — q-<slug>`

#### Scenario: Contradiction is queued, not resolved
- **WHEN** a durable decision contradicts an existing wiki page
- **THEN** neither page is written and `queue.md` gains a pending block whose
  origin is `build/<change>`

#### Scenario: The write carries the gate read's fingerprint
- **GIVEN** a store whose `queue.md` changes after the teacher's
  `wiki-show --json` gate read
- **WHEN** the teacher's `spec_emit.py wiki --from <staging> --expect
  <fingerprint>` is refused
- **THEN** it re-reads and restages `index.md`, `queue.md`, and `log.md` on
  the new fingerprint and retries once, and a second refusal reports
  `failed — store changed during the run`

#### Scenario: Teach skill points at the teacher
- **WHEN** `plugins/s/skills/teach/SKILL.md` is inspected
- **THEN** it names `s:teacher` as the change-scoped build-time path and keeps
  the sweep as the full path

### Requirement: Wiki user documentation
id: wiki-user-docs

The repository SHALL provide `docs/wiki.md`, titled "The wiki", as the main
page for the workspace wiki, `/s:teach`, and the `shipd wiki` verbs,
conforming to the shipd documentation standard with the marker `how-to` on
its first line and a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what the
wiki is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order.

The opening and `## When to use it` SHALL cover: the wiki as the store of
durable knowledge the oracle answers from, linking `docs/oracle.md`; the
workspace store and the repo-local fallback store a repo with no workspace
uses; when to run `/s:teach` (to distil decisions, to drain answered queue
entries, to correct a standing answer); and the teacher that runs after a
verified build, which distils that one change with no interview and at most
five pages.

`## How to run it` SHALL cover, for `/s:teach`: the invocation with its
optional topic argument; the scan of the spec surfaces (epic decisions,
verified capabilities, research reports, completed plans); pages that cite
their backing artifact and update an existing page before adding one; the
bound of 15 pages a run; the single interview round, opened only for gaps,
contradictions, and promotion offers; the deferred question that joins the
queue; the drain of answered queue entries, with an advisory answer keeping
its `Authority: advisory` line; and the one staged, lint-checked write that
restores the store on any finding. It SHALL cover `/s:teach <change> Q<n>` as
the way to correct one recorded consultation, and the promotion of
job-independent knowledge to a base store when one is present.

`## Reference` SHALL hold: a table of the store's files (`index.md`,
`queue.md`, `log.md`, `schema.md`, `wiki/`, `sources/`) with what each
holds; a table of the `shipd wiki`, `shipd wiki init`, and `shipd lint
--wiki` verbs; and links to `docs/memory.md` for personal preferences and
`docs/workspaces.md` for where a store lives.

Every interactive command on the page SHALL invoke the `shipd` binary or name
a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/wiki.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the teach sweep
- **WHEN** `docs/wiki.md` is inspected
- **THEN** it names the `/s:teach` invocation, the scanned surfaces, the
  15-page bound, the single interview round, the queue drain, the advisory
  marker, and the staged write

#### Scenario: Page covers correction and the teacher
- **WHEN** `docs/wiki.md` is inspected
- **THEN** it gives `/s:teach <change> Q<n>` as the correction path and
  states that a verified build's teacher distils one change with no
  interview

#### Scenario: Reference holds the store and the verbs
- **WHEN** the page's `## Reference` section is read
- **THEN** it lists the six store entries and the three `shipd` verbs, and
  links `oracle.md`, `memory.md`, and `workspaces.md` resolve

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/wiki.md`
- **THEN** it exits 0 with the page marked `how-to`, and the page names no
  `spec_status.py` or `spec_emit.py` path
