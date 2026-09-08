## MODIFIED Requirements

### Requirement: Epic amendment mode
id: epic-amend-mode
base: b3bd755c5b9f

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
