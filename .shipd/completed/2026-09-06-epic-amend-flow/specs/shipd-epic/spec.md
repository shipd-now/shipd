## ADDED Requirements

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
