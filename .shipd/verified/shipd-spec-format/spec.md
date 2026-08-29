# shipd-spec-format

### Requirement: Master spec library layout
id: master-spec-library-layout

The system SHALL store canonical specifications at
`<content-dir>/verified/<capability>/spec.md`, one file per capability,
where `<content-dir>` is the configured content directory (default `.shipd`).
Each file SHALL contain zero or more requirement blocks, each introduced by
a `### Requirement: <title>` header, and this location SHALL be the single
source of truth that the merge engine reads and writes.

#### Scenario: Locating a capability's canonical spec
- **WHEN** a tool needs the current definition of the `enforce-sso-timeout`
  requirement in the `auth` capability under the default configuration
- **THEN** it reads `.shipd/verified/auth/spec.md` and finds the requirement
  block whose `id` is `enforce-sso-timeout`

### Requirement: Stable requirement identifiers
id: stable-requirement-identifiers

Every requirement block SHALL carry an `id:` metadata line on the first
non-blank line immediately following its `### Requirement:` header, holding a
kebab-case slug that is unique within its capability. The slug SHALL be the merge key and
SHALL remain immutable across rewording of the title or body. The human-readable
title MAY change freely without affecting matching.

#### Scenario: Reworded title keeps its identity
- **WHEN** a change edits a requirement's `### Requirement:` title and prose but
  leaves its `id:` unchanged
- **THEN** the merge engine matches it to the existing master requirement by
  `id` and treats the edit as a modification, not an add-plus-remove

#### Scenario: Missing id is rejected
- **WHEN** a requirement block has no `id:` line
- **THEN** the linter reports an error and the change is not mergeable

### Requirement: Per-change artifact layout
id: per-change-artifact-layout

A change SHALL live at `<content-dir>/planned/<change>/` (default
`.shipd/planned/<change>/`) and SHALL always contain the lean artifact set: a
single `plan.md` holding the change's idea and implementation decisions, a
delta spec at `specs/<capability>/spec.md` for each affected capability, and
`tasks.md` as a separate executor-owned checklist. This artifact set SHALL
be produced for every change regardless of size.

A change MAY additionally carry an optional `artefacts/` directory holding the
standalone outputs of planning — a policy document, a block of verbatim text,
any content that must be preserved exactly rather than paraphrased into the
lean artifact set. Where the directory is present, every file inside it SHALL
be referenced by at least one of `plan.md`, `tasks.md`, or a delta spec, and
references SHALL use the change-relative path `artefacts/<file>` so they stay
correct after the change is archived. The directory SHALL travel with the
change through installation and through the merge's archive to
`<content-dir>/completed/<date>-<change>/artefacts/`.

#### Scenario: A change carries the lean artifact set
- **WHEN** a change `dark-mode-toggle` is authored under the default
  configuration
- **THEN** `.shipd/planned/dark-mode-toggle/` contains `plan.md`, at least one
  `specs/<capability>/spec.md`, and `tasks.md`

#### Scenario: Tasks stay out of the plan document
- **WHEN** an executor marks tasks done during a build
- **THEN** only `tasks.md` checkboxes change and `plan.md` is not rewritten

#### Scenario: A staged artefacts directory installs with the change
- **WHEN** a staging directory carrying `artefacts/policy.md`, referenced from
  `plan.md`, is installed with `spec_emit.py change`
- **THEN** the install succeeds and
  `.shipd/planned/<change>/artefacts/policy.md` holds the staged content

#### Scenario: Artefacts survive the archive
- **WHEN** a change carrying an `artefacts/` directory is merged and archived
- **THEN** `.shipd/completed/<date>-<change>/artefacts/` holds the same files

### Requirement: Delta operation headers
id: delta-operation-headers

A delta spec file SHALL express intent using level-2 operation headers only:
`## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`,
and `## RENAMED Requirements`. Requirement blocks under these headers carry the
same `id:` slugs used in the master library.

#### Scenario: Delta declares intent explicitly
- **WHEN** a change adds one new requirement and edits one existing requirement
- **THEN** the new requirement appears under `## ADDED Requirements` and the
  edited one under `## MODIFIED Requirements`, each with its `id:` slug

### Requirement: Base hash on delta edits
id: base-hash-on-delta-edits

Every requirement entry under `## MODIFIED Requirements` or
`## REMOVED Requirements` SHALL carry a `base:` metadata line holding the content
hash of the master requirement it was authored against, so the merge engine can
detect that the master changed since the delta was written.

#### Scenario: Edit records the base it was written against
- **WHEN** a change modifies `enforce-sso-timeout` whose current master content
  hash is `a3f9c1`
- **THEN** the delta entry for `enforce-sso-timeout` includes `base: a3f9c1`

### Requirement: Applied changes move to completed
id: archive-of-applied-changes

After a change's delta is merged into the master library, the change
directory SHALL be moved to `<content-dir>/completed/<date>-<change>/` so
the applied change is retained immutably for auditability and never
re-merged. `completed/` SHALL be a sibling of `planned/` inside the content
directory, so `planned/` contains only live changes.

#### Scenario: Applied change is retained under completed
- **WHEN** the merge engine finishes applying change `dark-mode-toggle`
  under the default configuration
- **THEN** `.shipd/planned/dark-mode-toggle/` no longer exists and
  `.shipd/completed/<date>-dark-mode-toggle/` contains its artifacts

### Requirement: Plan document sections
id: plan-document-sections

A change's `plan.md` SHALL, after the status header, carry a level-2
`## Idea` section followed by a level-2 `## Implementation` section. A
single gate-owned `## Context insufficient` section MAY precede `## Idea` —
written and removed only by the context-sufficiency gate, holding a
paragraph on the missing context followed by dot-point findings. The
`## Idea` section SHALL open with a one-sentence summary of the change,
SHALL then carry a level-3 `### Motivation` subsection of at most two
sentences stating why the change is being made — grounded in the planning
context, never a guess — SHALL then carry a level-3 `### Details`
subsection stating the concrete changes and naming the affected
capabilities and impact, and SHALL close with a level-3 `### Non-goals`
subsection explicitly listing the scope exclusions. The `## Implementation`
section SHALL hold the binding technical decisions — each with a rationale
and, where useful, the rejected alternative — and the risks. No section
named "Goals" SHALL be required anywhere. Additional sections MAY follow
the two required ones. Where a `## Questions and answers` section is
present, it SHALL hold one or more `### Q<n>: <one-line question summary>`
entries numbered sequentially from `Q1`, each carrying a `**Question:**`
field (the full compact question), a `**Verdict:**` field (`ANSWER` or
`INSUFFICIENT`), an `**Answered by:**` field (`ORACLE` or `USER`) directly
above the answer, and an `**Answer:**` field (the position or resolution
in full); an `ANSWER` entry additionally carries a `**Cited:**` field and
an `INSUFFICIENT` entry a `**Queued:**` field naming the filed `q-<slug>`.

#### Scenario: Plan carries both sections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` contains a `## Idea` section and a
  `## Implementation` section after the header

#### Scenario: Idea carries the ordered subsections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `## Idea` opens with a one-sentence summary and carries
  `### Motivation`, `### Details`, and `### Non-goals` subsections in that
  order

#### Scenario: Gate section may precede the Idea
- **WHEN** a rejected plan carries `## Context insufficient` between the
  header and `## Idea`
- **THEN** the plan remains structurally valid

#### Scenario: Questions-and-answers entries follow the grammar
- **WHEN** a plan carries a `## Questions and answers` section with an entry
  `### Q1: Which store holds the toggle?` carrying `**Question:**`,
  `**Verdict:** ANSWER`, `**Answered by:** ORACLE`, `**Answer:**`, and
  `**Cited:**` fields in that order
- **THEN** the plan remains structurally valid

### Requirement: EARS-recommended normative statements
id: ears-recommended-statements

The format documentation SHALL present the five EARS patterns — ubiquitous
("The system shall ..."), event-driven ("When ..."), state-driven
("While ..."), unwanted-behavior ("If ..., then ..."), and optional-feature
("Where ...") — as the recommended shape for requirement SHALL/MUST
statements, and authoring guidance SHALL recommend them when emitting delta
specs. Tooling SHALL NOT reject a requirement solely for not matching an EARS
template; the normative-statement check remains the presence of SHALL or MUST.

#### Scenario: Guidance documents the patterns
- **WHEN** an author consults `.shipd/README.md` for how to phrase a
  requirement
- **THEN** the five EARS patterns are documented with their sentence templates

#### Scenario: Non-EARS phrasing still lints
- **WHEN** a requirement carries a SHALL statement that matches no EARS
  template
- **THEN** the linter reports no error for its phrasing

### Requirement: Constitution steering document
id: constitution-steering-document

The system SHALL reserve `.shipd/constitution.md` as an optional global
steering document holding the repository's non-negotiable engineering rules
(technology constraints, testing standards, anti-patterns). When the file is
present, the planning and build flows SHALL load it and treat its rules as
binding constraints on designs, emitted artifacts, and implementations. When
it is absent, all tooling SHALL behave exactly as before.

#### Scenario: Constitution grounds planning
- **GIVEN** a repo whose `.shipd/constitution.md` forbids third-party Python
  dependencies in engine scripts
- **WHEN** the plan flow authors a design that would add such a dependency
- **THEN** the constitution rule is honored and the design stays within the
  constraint

#### Scenario: Absent constitution changes nothing
- **WHEN** a repo has no `.shipd/constitution.md`
- **THEN** lint, status, merge, plan, and build behave with no errors or
  warnings about the missing file

### Requirement: Task traceability tags
id: task-traceability-tags

Every checkbox task in a change's `tasks.md` SHALL carry exactly one
traceability tag of the form `[req: <id>[, <id>...]]`, naming the requirement
id(s) from the change's own delta specs that the task implements or verifies,
or the wildcard form `[req: *]` for tasks that span the whole change (such as
verification barriers). The wildcard SHALL appear alone, never combined with
ids. The tag SHALL sit in the task text after the optional `[P<n>]` parallel
group tag and SHALL NOT affect task coordination.

#### Scenario: Task names its requirement
- **WHEN** a task implements the `export-report-csv` requirement from the
  change's delta specs
- **THEN** its task line carries `[req: export-report-csv]`

#### Scenario: Barrier uses the wildcard
- **WHEN** a verification barrier exercises the whole change
- **THEN** its task line carries `[req: *]` and no other requirement ids

#### Scenario: Tags do not disturb coordination
- **WHEN** a task line carries both `[P2]` and `[req: export-report-csv]`
- **THEN** the coordinator's group parsing behaves exactly as it would with
  the group tag alone

### Requirement: Plan header metadata lines
id: plan-header-metadata-lines

A change's `plan.md` MAY carry a metadata block: contiguous `<Key>: <value>`
lines immediately following the `Status:` line, ended by the first blank line
or heading. Tooling SHALL recognize exactly five keys — `Profile`, `Epic`,
`Initiative`, `Theme`, `Fixes` — and every value SHALL be a kebab-case slug.
The `Fixes` key SHALL be repeatable, each line naming one shipped change this
change remediates (the post-merge fix linkage the delivery-metrics
change-failure signal derives from); tooling SHALL NOT require the named slug
to resolve to an existing change. The block SHALL be optional: a plan whose
header carries only the title and `Status:` line SHALL remain valid.

#### Scenario: Metadata block is parsed
- **WHEN** a plan header reads `# csv-export`, `Status: draft`,
  `Theme: reliability`, `Epic: reporting-overhaul` on consecutive lines
- **THEN** tooling parses `Theme` and `Epic` as the change's metadata

#### Scenario: Fixes lines are parsed and repeatable
- **WHEN** a plan header carries `Status: draft` followed by
  `Fixes: board-theme` and `Fixes: board-search` on consecutive lines
- **THEN** tooling parses both slugs as changes this plan remediates, while a
  non-kebab `Fixes` value is a lint error

#### Scenario: Metadata-free header stays valid
- **WHEN** a plan header carries only the title and `Status:` line
- **THEN** the plan is treated exactly as before this feature existed

### Requirement: Plan profile values
id: plan-profile-values

The `Profile:` metadata key SHALL accept exactly `full` or `lite`, and an
absent `Profile:` line SHALL mean `full`. The `lite` profile SHALL relax
content expectations only (brevity, optional test-first ordering); it SHALL
NOT change the required artifact set or any structural lint rule — every
change carries `plan.md`, delta specs, and `tasks.md` regardless of profile.

#### Scenario: Absent profile defaults to full
- **WHEN** a plan carries no `Profile:` line
- **THEN** tooling treats the change as `full` profile

#### Scenario: Lite keeps the artifact set
- **WHEN** a change's plan carries `Profile: lite`
- **THEN** the change still requires `plan.md`, at least one delta spec, and
  `tasks.md`, and structural lint rules apply unchanged

### Requirement: Initiative attaches through the epic
id: initiative-attaches-through-epic

If a change's plan carries an `Epic:` line, then the plan SHALL NOT also
carry an `Initiative:` line — a grouped change derives its initiative through
its epic. Where a change belongs to no epic, it MAY carry an `Initiative:`
line directly.

#### Scenario: Epic and initiative together are invalid
- **WHEN** a plan carries both `Epic: reporting-overhaul` and
  `Initiative: mvp-readiness`
- **THEN** tooling treats the plan as invalid and points at the epic as the
  place to attach the initiative

#### Scenario: Standalone change may carry an initiative
- **WHEN** a plan with no `Epic:` line carries `Initiative: mvp-readiness`
- **THEN** the plan is valid

### Requirement: Theme vocabulary config
id: theme-vocabulary-config

The system SHALL read the theme vocabulary from the resolved layered
configuration's top-level `valid_themes` key. When the resolved value is a
non-empty array, a plan's `Theme:` value SHALL be validated against it; when
no layer declares `valid_themes`, any kebab-case theme SHALL be accepted.
The retired `.shipd/config.json` SHALL NOT be read.

#### Scenario: Theme outside the vocabulary is invalid
- **GIVEN** the repo's `.shipd-config.json` declares
  `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: developer-experience`
- **THEN** tooling reports the theme as outside the vocabulary

#### Scenario: No declared vocabulary accepts any kebab theme
- **WHEN** no config layer declares `valid_themes` and a plan carries
  `Theme: any-label`
- **THEN** the theme is accepted

### Requirement: Epic artifact layout
id: epic-artifact-layout

An epic SHALL live at `<content-dir>/epics/<slug>/epic.md` (default
`.shipd/epics/<slug>/epic.md`), beginning with a `# <slug>` title matching its
directory, a `Status:` line whose value is one of `draft`, `ready`,
`active`, `complete`, and optionally a header metadata block. The document
SHALL carry `## Introduction`, `## Decisions`, `## Design`, and `## Changes`
sections, and `## Introduction` SHALL be the first level-2 section. The
Introduction SHALL open with the problem and its motivation before
describing the feature and its intended outcome, with success criteria
recommended, and SHALL include a `### Non-goals` subsection listing the
scope exclusions. `## Changes` SHALL hold a stub table with the exact
columns `| Change | Description | Code | Integration | Unknowns | Risk |`,
at least one data row, kebab-case change slugs unique within the table, and
every rating cell one of `low`, `medium`, `high`.

#### Scenario: Conforming epic is valid at the new path
- **WHEN** `.shipd/epics/reporting-overhaul/epic.md` starts with
  `# reporting-overhaul`, `Status: draft`, opens with an `## Introduction`
  carrying a `### Non-goals` subsection, carries `## Decisions`,
  `## Design`, and `## Changes`, and its stub table lists `csv-export` with
  ratings `low`/`medium`/`low`/`low`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Missing introduction is rejected
- **WHEN** an epic carries `## Decisions`, `## Design`, and `## Changes`
  but no `## Introduction` section
- **THEN** tooling reports the missing section

#### Scenario: Invalid rating is rejected
- **WHEN** a stub row's Risk cell reads `huge`
- **THEN** tooling reports the invalid rating

### Requirement: Epic header metadata
id: epic-header-metadata

An epic's header metadata block SHALL recognize exactly two keys — `Theme:`
and `Initiative:` — with kebab-case values; `Theme:` SHALL be validated
against `valid_themes` when `.shipd/config.json` declares a non-empty vocabulary,
and any other key (including `Profile:` and `Epic:`) SHALL be rejected.

#### Scenario: Epic carries theme and initiative
- **WHEN** an epic header carries `Theme: reliability` and
  `Initiative: mvp-readiness`
- **THEN** both are parsed as the epic's metadata and accepted

#### Scenario: Profile on an epic is rejected
- **WHEN** an epic header carries `Profile: lite`
- **THEN** tooling reports an unrecognized-key error

### Requirement: Epic reference resolution
id: epic-reference-resolution

A change plan's `Epic: <slug>` line SHALL resolve to an existing
`.shipd/epics/<slug>/epic.md`; an unresolvable reference SHALL be an error. Where
the referenced epic's stub table does not list the change's slug, tooling
SHALL surface a warning — membership drift is visible but not fatal.

#### Scenario: Dangling epic reference is an error
- **WHEN** a change carries `Epic: no-such-epic` and `.shipd/epics/no-such-epic/`
  does not exist
- **THEN** tooling reports an error for the unresolvable reference

#### Scenario: Missing stub row warns
- **GIVEN** `.shipd/epics/reporting-overhaul/epic.md` exists but its stub table
  has no `csv-export` row
- **WHEN** change `csv-export` carrying `Epic: reporting-overhaul` is checked
- **THEN** tooling emits a warning naming the missing membership row and the
  check still passes

### Requirement: Epic research section
id: epic-research-section

An epic MAY carry a `## Research` section associating research with the
epic. When present, the section SHALL hold at least one markdown list entry
whose link targets a file under the content directory's `research/` folder
(default `.shipd/research/`); annotation prose MAY follow a link on its line.
When absent, the epic SHALL be exactly as valid as before this feature. The
system SHALL reserve `<content-dir>/research/` as the home of research
artifacts; this requirement mandates no internal format for them.

#### Scenario: Epic lists an existing research report
- **GIVEN** a file at `.shipd/research/payment-apis/report.md`
- **WHEN** an epic carries a `## Research` section with the entry
  `- [Payment APIs](../../research/payment-apis/report.md)`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Research section is optional
- **WHEN** an epic carries no `## Research` section
- **THEN** no research-related finding is reported

#### Scenario: Empty research section is rejected
- **WHEN** an epic carries a `## Research` section with no link entries
- **THEN** tooling reports the empty section as an error

### Requirement: Research report format
id: research-report-format

A research report installed at `<content-dir>/research/<slug>/report.md`
SHALL open with a non-empty level-1 title on its first line. Where the report
carries a citation signal — a `## Sources` section, or any inline `[n]`
citation marker outside fenced code blocks — it SHALL satisfy the full
citation skeleton: a `## Sources` section holding at least one numbered entry
(`N. …`), at least one inline `[n]` marker, and every marker outside fenced
code blocks referencing a number present in the sources list (a bracketed
number immediately followed by `(` is a markdown link, not a marker). A titled
report carrying neither signal SHALL be accepted — the document's origin never
gates installation. This format is enforced at engine install time; a file
linked from an epic's `## Research` section is still validated for existence
only (epic-research-section is unchanged).

#### Scenario: Conforming cited report is accepted
- **WHEN** a report with a title line, `[1]`-style markers, and a
  `## Sources` section listing source 1 is checked
- **THEN** tooling reports no findings

#### Scenario: Uncited titled document is accepted
- **WHEN** a titled report with no `## Sources` section and no `[n]` markers
  is checked
- **THEN** tooling reports no findings

#### Scenario: Markers without a sources section are rejected
- **WHEN** a report carries citation markers but no `## Sources` section
- **THEN** tooling reports the missing section as an error

#### Scenario: Unresolved citation marker is rejected
- **WHEN** a report cites `[4]` while its sources list holds three entries
- **THEN** tooling reports the unresolved marker as an error naming it

#### Scenario: Code blocks never trip the marker check
- **WHEN** a report's fenced code block contains `items[0]` and its prose
  citations all resolve
- **THEN** tooling reports no findings

### Requirement: Video brief format
id: video-brief-format

A video intent brief installed at `<content-dir>/video/<slug>/brief.md` SHALL
open with a non-empty level-1 title on its first line and SHALL carry a `Video:`
header line naming the source recording in the `Key: value` header block
immediately following the title; `Bundle:` and `Project:` header lines are
optional. Where a `Project:` line is present its value SHALL name a project slug
declared in the workspace registry; where it is absent the registry SHALL NOT be
consulted. The brief SHALL carry an `## Intents` section holding at least one
level-3 intent heading, and a `## Sources` section holding at least one numbered
entry (`N. …`) whose text opens with a bracketed timestamp (`[HH:MM:SS]`,
fractional seconds permitted). A source entry SHALL NOT be required to name a
speaker. Every level-3 intent SHALL carry at least one inline citation marker
`[n]`, and every citation marker outside fenced code blocks SHALL reference a
number present in the sources list (a bracketed number immediately followed by
`(` is a markdown link, not a marker). The brief SHALL NOT be required to carry
a `## Speakers` section. Where the brief carries `## Open questions` or
`## Gaps & caveats` sections they are optional and unvalidated, and an
unrecognized level-2 section SHALL NOT be an error. This format is enforced at
engine install time.

#### Scenario: Conforming brief is accepted
- **WHEN** a brief with a title line, a `Video:` header, one cited intent, and a
  timestamped source entry is checked
- **THEN** tooling reports no findings

#### Scenario: Missing Video header is rejected
- **WHEN** a brief carries a title and all required sections but no `Video:`
  header line
- **THEN** tooling reports the missing header as an error

#### Scenario: A brief with no Speakers section is accepted
- **WHEN** an otherwise conforming brief carries no `## Speakers` section
- **THEN** tooling reports no findings

#### Scenario: A speaker-free source entry is accepted
- **WHEN** a source entry opens with a bracketed timestamp followed only by what
  was said, naming no speaker
- **THEN** tooling reports no findings for that entry

#### Scenario: A brief without a Project line stays valid
- **WHEN** an otherwise conforming brief carries no `Project:` header line
- **THEN** tooling reports no findings and the workspace registry is not
  consulted

#### Scenario: An undeclared project is rejected
- **WHEN** a brief carries `Project:` naming a slug the workspace registry does
  not declare
- **THEN** tooling reports an error naming that value

#### Scenario: Uncited intent is rejected
- **WHEN** a brief carries a level-3 intent holding no `[n]` citation marker
- **THEN** tooling reports an error naming that intent

#### Scenario: Untimestamped source entry is rejected
- **WHEN** a brief's `## Sources` entry opens with no bracketed timestamp
- **THEN** tooling reports an error naming that entry

#### Scenario: Unresolved citation marker is rejected
- **WHEN** a brief cites `[4]` while its sources list holds three entries
- **THEN** tooling reports the unresolved marker as an error naming it

#### Scenario: Code blocks never trip the marker check
- **WHEN** a brief's fenced code block contains `items[0]` and its prose
  citations all resolve
- **THEN** tooling reports no findings

#### Scenario: A retained Speakers section is not an error
- **WHEN** a previously installed brief still carries a `## Speakers` section
- **THEN** tooling treats it as an unrecognized level-2 section and reports no
  findings

### Requirement: Epic video section
id: epic-video-section

An epic MAY carry a `## Video` section associating video intent briefs with the
epic. When present, the section SHALL hold at least one markdown list entry
whose link targets a file under the content directory's `video/` folder
(default `.shipd/video/`); annotation prose MAY follow a link on its line. When
absent, the epic SHALL be exactly as valid as before this feature. The section
SHALL be independent of `## Research`: a brief SHALL NOT be linked from
`## Research`, a research report SHALL NOT be linked from `## Video`, and the
presence of either section SHALL neither imply nor constrain the other.

#### Scenario: Epic lists an existing intent brief
- **GIVEN** a file at `.shipd/video/kickoff-call/brief.md`
- **WHEN** an epic carries a `## Video` section with the entry
  `- [Kickoff call](../../video/kickoff-call/brief.md)`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Video section is optional
- **WHEN** an epic carries no `## Video` section
- **THEN** no video-related finding is reported

#### Scenario: Empty video section is rejected
- **WHEN** an epic carries a `## Video` section with no link entries
- **THEN** tooling reports the empty section as an error

#### Scenario: The two context sections are independent
- **WHEN** an epic carries both a `## Research` section and a `## Video`
  section
- **THEN** each is validated against its own reserved folder and neither
  section's contents affect the other's findings
