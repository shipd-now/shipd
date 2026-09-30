## MODIFIED Requirements

### Requirement: Knowledge capture rubric
id: knowledge-capture-rubric
base: b94eb0d5c570

The plugin SHALL provide a knowledge capture rubric reference at
`plugins/s/skills/epic/references/capture-rubric.md` defining four tiers for
routing information that arrives during planning, building, or epic
authoring: **binding** (changes what executors do — the change's own
artifacts at change scope; at epic scope the epic's `## Decisions`, changed
only through the sanctioned amendment discipline of a fresh
`epic-amend-<slug>` worktree, the amended Decision rewritten to state the
current fact, and a lint-gated pull request, never a free edit and never a
dated note), **reference** (supports the feature without binding executors —
installed through the emit engine's document kinds and linked from the
epic's `## References` shelf, or cited in `plan.md` prose when no epic
resolves), **durable** (outlives the feature — routed to the workspace wiki
via `/s:teach` or the oracle queue, where the capture durability rubric at
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
unshipped verb, flag, or skill argument, and SHALL NOT describe a dated
provenance stamp on an amended Decision.

#### Scenario: Rubric reference exists with four tiers
- **WHEN** `plugins/s/skills/epic/references/capture-rubric.md` is inspected
- **THEN** it defines the binding, reference, durable, and noise tiers, each
  with its destination, and names the epic-scope amendment discipline for
  the binding tier as rewriting the Decision to state the current fact

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

### Requirement: Epic amendment mode
id: epic-amend-mode
base: f6f126f9594a

Where `/s:epic` is invoked as `/s:epic <slug> amend`, the skill SHALL run an
amendment flow instead of authoring: it SHALL create a fresh worktree via
`shipd worktree epic-amend-<slug> --fresh` and edit the epic there, SHALL
change only the `## Decisions` section and the shelf sections
(`## References`, and a pre-existing `## Research` or `## Video` extended in
place), and SHALL write every touched Decision as the current fact: a new
Decision states its rule, a superseded Decision is rewritten in place, and a
Decision no longer true is deleted. The flow SHALL NOT append a dated
marker, an "amended" note, or a before-and-after narrative to any Decision,
because the epic's git history is its amendment record. Reference-tier
material SHALL be installed through the emit engine's `docs` kind and
linked from `## References`, never pasted into `## Decisions`. Before
shipping, the flow SHALL pass both gates — the linter's single-epic mode and
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
  the touched Decision bullet reads as the current fact with no dated
  marker, the epic lint and `epic-amend-check` both pass, and the edit
  ships as an auto-merging PR reported with its full URL

#### Scenario: A superseded decision is rewritten, not annotated
- **GIVEN** a live epic whose Decision states a count that delivery proved
  wrong
- **WHEN** `/s:epic <slug> amend` runs with the corrected count
- **THEN** the Decision bullet states the corrected count in place, the
  earlier text is gone from the file, and no `*(amended …)*` note or
  "previously" sentence is added

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
