# shipd-epic

### Requirement: Epic interview skill
id: epic-interview-skill

An `/s:epic` skill SHALL create an epic by investigating the codebase first,
asking only genuinely un-inferrable decisions in a single batched question
round, and authoring the epic in reader order: an `## Introduction` opening
with the problem and motivation, then the feature and its intended outcome
with success criteria, closing with `### Non-goals`; then the epic's
Decisions and Design sections; then the `## Changes` stub table with
per-change complexity ratings. It SHALL emit the epic at `Status: draft`,
lint it with the linter's single-epic mode, and promote it to `ready` via
`epic-set-status` only on user approval. It SHALL ship the epic through the
repository's worktree-and-PR workflow, and SHALL NOT create member changes —
it points the user at `/s:plan` per stub, whose emitted changes carry
`Epic: <slug>`.

#### Scenario: Epic opens with the why
- **WHEN** the skill authors an epic
- **THEN** the emitted document's first level-2 section is `## Introduction`,
  stating the problem before the feature description, and it contains a
  `### Non-goals` subsection

#### Scenario: Epic emission is draft until approved
- **WHEN** the skill finishes authoring an epic
- **THEN** `.shipd/epics/<slug>/epic.md` carries `Status: draft` until the user
  approves, at which point the skill promotes it to `ready`

#### Scenario: Member changes are not created by the skill
- **WHEN** the skill completes an epic with three stub rows
- **THEN** `.shipd/planned/` gains no new change directories, and the user is
  pointed at `/s:plan` for each stub

#### Scenario: Emitted epics lint clean
- **WHEN** the skill hands off an epic
- **THEN** the linter's single-epic mode exits zero for it

### Requirement: Research-fed epic authoring
id: research-fed-authoring

Where research is supplied for the feature — reports the user names, or
files the epic under authoring already links — the `/s:epic` skill SHALL
read those research files as pre-investigation context before its question
round, and SHALL record every consumed report as a link entry in the epic's
`## References` section. Where the epic under authoring already carries a
`## Research` section, the skill MAY extend that section in place instead —
the legacy section stays valid and is never migrated. The skill SHALL NOT
invent entries for files it did not read, and epics for features with no
research SHALL carry no entry for one in either section.

#### Scenario: Supplied research is consumed and recorded
- **GIVEN** the user points epic authoring at
  `.shipd/research/payment-apis/report.md`
- **WHEN** the epic is emitted
- **THEN** its `## References` section links that report and the epic's
  Decisions reflect context drawn from it

#### Scenario: A legacy Research section is extended in place
- **GIVEN** an epic under authoring already carries a `## Research` section
- **WHEN** a further report is consumed
- **THEN** recording it as a `## Research` entry is valid and no migration
  to `## References` is forced

#### Scenario: No research means no entry
- **WHEN** an epic is authored with no research supplied or discovered
- **THEN** the emitted epic carries no research link entry

### Requirement: Video-brief-fed epic authoring
id: video-fed-epic-authoring

Where a video intent brief is supplied for the feature — a bundle slug the
user names, or a brief the epic under authoring already links — the
`/s:epic` skill SHALL read that brief through the engine
(`spec_status.py cat video <slug>`) as pre-investigation context before its
question round, and SHALL record every brief it read as a link entry in the
epic's `## References` section; where the epic under authoring already
carries a `## Video` section, the skill MAY extend that section in place —
the legacy section stays valid and is never migrated. The brief SHALL be an
input to investigation and never a replacement for it: the codebase-first
rule still binds, so the affected capabilities and the decomposition seams
are still established by reading the repository. The skill SHALL NOT invent
entries for briefs it did not read, and an epic authored with no brief SHALL
carry no brief link entry.

#### Scenario: A supplied brief is consumed and recorded
- **GIVEN** the user points epic authoring at the bundle slug `kickoff-call`
- **WHEN** the epic is emitted
- **THEN** its `## References` section links
  `.shipd/video/kickoff-call/brief.md` and its Decisions reflect context
  drawn from that brief

#### Scenario: No brief means no entry
- **WHEN** an epic is authored with no video brief supplied
- **THEN** the emitted epic carries no brief link entry

#### Scenario: The brief does not replace reading the repository
- **WHEN** epic authoring proceeds from a brief
- **THEN** the member decomposition and the affected capabilities are still
  established by reading the repository, not taken from the brief alone

#### Scenario: An unread brief is never linked
- **WHEN** a brief exists under the content directory's `video/` folder but
  was not read for this feature
- **THEN** the emitted epic carries no entry for it

### Requirement: Epic authoring does not ingest recordings
id: epic-no-recording-ingest

If the argument given to `/s:epic` names a recording rather than an installed
intent brief, then the skill SHALL NOT ingest it and SHALL report that
`/s:video-ingest` produces the brief first, leaving the ingest surface in one
place. `/s:epic` SHALL consume only briefs already installed under the content
directory's `video/` folder.

#### Scenario: A recording is reported, not ingested
- **WHEN** `/s:epic` is invoked with a path to a video container
- **THEN** no ingest is performed and the skill directs the user to
  `/s:video-ingest` to produce the brief first

#### Scenario: An installed brief is consumed normally
- **WHEN** `/s:epic` is invoked with a slug naming an installed brief
- **THEN** the brief is read and authoring proceeds without any ingest

### Requirement: Supplied document install
id: epic-supplied-document-install

Where the user supplies a context document for the feature that does not
already reside under the content directory's `research/`, `video/`, or
`docs/` folder, the `/s:epic` skill SHALL install it through
`spec_emit.py docs <slug> --from <file>` — never by writing into the spec
tree directly — choosing a kebab-case slug derived from the document's
level-1 title, or from its filename when the document carries no title.
Where the document lacks a level-1 title on its first line, the skill SHALL
stage a copy that prepends a `# <title>` derived from the filename and
install the staged copy, leaving the user's original file unmodified. The
skill SHALL then record the installed document as a link entry in the epic's
`## References` section, creating the section when absent. A supplied file
already residing under one of those three folders SHALL be read and linked
without reinstalling.

#### Scenario: Supplied document is installed and linked
- **GIVEN** the user points epic authoring at a titled markdown document
  outside the content directory
- **WHEN** the epic is authored
- **THEN** the document is installed at the resolved `docs/<slug>/doc.md`
  via the emit engine and the epic's `## References` section links it

#### Scenario: Untitled document gains a staged title
- **GIVEN** the user supplies a document whose first line is not a level-1
  title
- **WHEN** the skill installs it
- **THEN** the installed document opens with a `# <title>` derived from the
  filename and the user's original file is unchanged

#### Scenario: Already-installed artifacts are not reinstalled
- **GIVEN** the user points epic authoring at a file already under the
  content directory's `research/`, `video/`, or `docs/` folder
- **WHEN** the epic is authored
- **THEN** no install runs and the file is read and linked as before

### Requirement: Knowledge capture rubric
id: knowledge-capture-rubric

The plugin SHALL provide a knowledge capture rubric reference at
`plugins/s/skills/epic/references/capture-rubric.md` defining four tiers for
routing information that arrives during planning, building, or epic
authoring: **binding** (changes what executors do — the change's own
artifacts at change scope; at epic scope the epic's `## Decisions`, changed
only through the sanctioned amendment discipline of a fresh
`epic-amend-<slug>` worktree, a dated provenance line on the amended
Decision, and a lint-gated pull request, never a free edit), **reference**
(supports the feature without binding executors — installed through the
emit engine's document kinds and linked from the epic's `## References`
shelf, or cited in `plan.md` prose when no epic resolves), **durable**
(outlives the feature — routed to the workspace wiki via `/s:teach` or the
oracle queue, where the capture durability rubric at
`plugins/s/skills/ask/references/capture-rubric.md` governs the queue
write), and **noise** (recorded nowhere, deliberately). The rubric SHALL
name itself the "knowledge capture rubric", SHALL explicitly distinguish
itself from the capture durability rubric and name the durable tier's
handoff to it without duplicating its tiers, SHALL carry a calibrated
examples table of at least eight rows with at least two per tier, and SHALL
carry tie-breakers covering at least: binding versus reference decided by
obeyed-versus-consulted, reference versus durable decided by the feature's
lifetime, borderline cases leaning toward the less-capturing tier, and the
binding tier's home decided by scope. The rubric SHALL NOT reference any
unshipped verb, flag, or skill argument.

#### Scenario: Rubric reference exists with four tiers
- **WHEN** `plugins/s/skills/epic/references/capture-rubric.md` is inspected
- **THEN** it defines the binding, reference, durable, and noise tiers, each
  with its destination, and names the epic-scope amendment discipline for
  the binding tier

#### Scenario: Durable tier hands off to the durability rubric
- **WHEN** the rubric's durable tier is inspected
- **THEN** it routes to the workspace wiki or oracle queue and names
  `plugins/s/skills/ask/references/capture-rubric.md` as governing the
  queue write, and the include/exclude/consent-gated tiers are not
  restated as the knowledge capture rubric's own

#### Scenario: Calibrated examples and tie-breakers are present
- **WHEN** the rubric's examples table and tie-breakers are inspected
- **THEN** the table holds at least eight rows spanning all four tiers with
  at least two rows per tier, each with a rationale, and each named
  tie-breaker appears

### Requirement: Rubric consult in epic authoring
id: epic-authoring-rubric-consult

The `/s:epic` skill SHALL name the knowledge capture rubric, by the path
`${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`, at the
moment question-round answers fold in: each substantive piece of arriving
information is classified into exactly one tier, with binding information
landing in the `## Decisions` section being authored, reference material
installed through the emit engine and linked from `## References`, durable
knowledge routed to the wiki or oracle queue, and noise deliberately
dropped. The harness epic body SHALL carry a compact consult sentence
naming the four tiers and the rubric by its `"$S/../../epic/references/`
path.

#### Scenario: Epic skill consults at the fold-in
- **WHEN** `plugins/s/skills/epic/SKILL.md`'s question-round flow is
  inspected
- **THEN** it directs classifying folded-in answers against the knowledge
  capture rubric by its plugin-root path and names all four tier
  destinations

#### Scenario: Harness epic body mirrors the consult
- **WHEN** `plugins/s/harness/bodies/epic.md` is inspected
- **THEN** its question-round section carries the consult sentence naming
  the four tiers and the rubric path, and the rendered body stays under the
  120-line budget
