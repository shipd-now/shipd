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

### Requirement: Epic amendment mode
id: epic-amend-mode

Where `/s:epic` is invoked as `/s:epic <slug> amend`, the skill SHALL run an
amendment flow instead of authoring: it SHALL create a fresh worktree via
`shipd worktree epic-amend-<slug> --fresh` and edit the epic there, SHALL
change only the `## Decisions` section and the shelf sections
(`## References`, and a pre-existing `## Research` or `## Video` extended in
place), and SHALL stamp every new or extended Decision bullet with a dated
provenance marker of the form `*(amended YYYY-MM-DD: <one-line note>)*`,
never rewriting or deleting existing Decision text — a superseded Decision
is recorded as a stamped addition. Reference-tier material SHALL be
installed through the emit engine's `docs` kind and linked from
`## References`, never pasted into `## Decisions`. Before shipping, the flow
SHALL pass both gates — the linter's single-epic mode and
`spec_status.py epic-amend-check <slug>` — and SHALL ship the amendment as
an auto-merging pull request on `change/epic-amend-<slug>`, reported with
its full URL. If the epic's status is `draft`, then the skill SHALL refuse
the amendment and point at the epic's authoring worktree instead. The flow
SHALL NOT edit `## Introduction`, `## Design`, the `## Changes` stub table,
or the epic's header metadata.

Where the consuming repository's configuration resolves the epic into an
external store (`store_root` declared), the flow SHALL NOT create a
worktree, branch, or pull request: it SHALL edit the epic in place in the
store's working tree, SHALL pass both gates against the uncommitted edit —
with `--root` naming the consuming repository, never the store — before any
commit, and SHALL then ship the amendment as one local git commit in the
store's repository scoped to the epic file alone, subject
`shipd: amend epic <slug>`, never pushing, reporting the commit hash in
place of a PR URL. If the gates fail — including a store outside any git
work tree, where `epic-amend-check` errors because no base is readable —
then the flow SHALL report the failure and stop without committing.

#### Scenario: A binding decision is amended in
- **GIVEN** an active epic and mid-delivery binding information routed to
  the epic by the capture rubric
- **WHEN** `/s:epic <slug> amend` runs
- **THEN** the amendment is made in a fresh `epic-amend-<slug>` worktree,
  the new Decision bullet carries a dated `*(amended …)*` stamp, the epic
  lint and `epic-amend-check` both pass, and the edit ships as an
  auto-merging PR reported with its full URL

#### Scenario: A protected-section edit is blocked before shipping
- **GIVEN** an amendment worktree whose epic edit strayed into
  `## Introduction`
- **WHEN** the flow runs `epic-amend-check` before shipping
- **THEN** the verb reports the protected-section finding and the flow stops
  to fix the epic rather than pushing

#### Scenario: A draft epic is refused
- **WHEN** `/s:epic <slug> amend` is invoked for an epic at `Status: draft`
- **THEN** the skill amends nothing and reports that a draft epic is edited
  in its authoring worktree

#### Scenario: Reference material routes through the docs kind
- **GIVEN** an amendment whose substance is a consulted document rather than
  a binding constraint
- **WHEN** the flow classifies it against the capture rubric
- **THEN** the document is installed via `spec_emit.py docs` and linked from
  `## References`, and `## Decisions` gains no copy of its content

#### Scenario: A store-resident amendment ships as a scoped local commit
- **GIVEN** an active epic resolving into an external git-backed store
- **WHEN** `/s:epic <slug> amend` runs
- **THEN** no worktree, branch, or PR is created in either repository, both
  gates run against the uncommitted store edit with `--root` naming the
  consuming repository, and the amendment lands as one local commit in the
  store repository scoped to the epic file, unpushed, its hash reported in
  place of a PR URL

#### Scenario: A non-git store stops the amendment ungated
- **GIVEN** an epic resolving into a store outside any git work tree
- **WHEN** the flow runs `epic-amend-check`
- **THEN** the verb's error is reported and the flow stops without
  committing anything
