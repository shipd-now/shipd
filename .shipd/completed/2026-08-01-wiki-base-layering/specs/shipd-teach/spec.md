## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Distillation scan
id: teach-distill-scan
base: ea701c1c34fd

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
base: 6dc2a5bca826

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
