# /s:epic reference — the epic contract the linter enforces

`.shipd/epics/<slug>/epic.md`, where `<slug>` is the kebab-case directory name:

```
# <slug>
Status: draft
Theme: <kebab-theme>            (optional)
Initiative: <kebab-initiative>  (optional)
PRD: <kebab-prd>                (optional; must resolve to a workspace PRD)

## Introduction

The why first — the problem and its motivation — then the what and its intended
outcome, success criteria recommended.

### Non-goals

- <what this epic explicitly does not do>

## Research                        (optional)

- [<report title>](../../research/<name>/report.md) <optional annotation>

## Video                           (optional)

- [<brief title>](../../video/<slug>/brief.md) <optional annotation>

## References                      (optional)

- [<title>](../../docs/<slug>/doc.md) <optional annotation>

## Decisions

The cross-cutting decisions every member change inherits — shared architectural
choices, constraints, rejected alternatives.

## Design

The shape of the feature as a whole: the pieces, how they fit, the seams the
decomposition follows.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| <member-slug> | <one-line description> | low | medium | low | low |
```

## Rules

- **Header.** `# <slug>` matches the directory. `Status:` is one of `draft`,
  `ready`, `active`, `complete` — there is no epic-level `verified`. The
  metadata block recognizes only `Theme:`, `Initiative:` and `PRD:`, all
  kebab-case; `Profile:` and `Epic:` are not valid on an epic. Where the config
  declares a non-empty `valid_themes`, `Theme:` must be one of them. `PRD:`
  cites the discover-phase PRD this epic decomposes and must resolve to a PRD
  across the workspace chain wherever a workspace is discoverable (skipped
  silently in a workspace-less checkout) — write it only when that PRD exists.
- **Sections.** `## Introduction`, `## Decisions`, `## Design`, `## Changes`
  are all required, and `## Introduction` must be the first level-2 section and
  carry a `### Non-goals` subsection.
- **Research, Video, and References (all optional).** Omit a section entirely
  when there is nothing for it. When present it holds at least one
  `- [title](path)` entry whose link resolves (epic-dir first, then repo root)
  to an existing file under the content directory's `research/` or `video/`
  folder (`## Research`, `## Video`) — or, for `## References`, under any of
  `research/`, `video/`, or `docs/`, its entries mixing freely across the
  three kinds; the epic-relative form above is the clickable convention. An
  empty section, a dead link, or a link outside the folder(s) it covers is a
  lint error. List only what you actually read. `## References` is a superset
  shelf: new authoring prefers it, but `## Research` and `## Video` stay valid
  forever and are never migrated.
- **Stub table.** The header row is exactly those six columns in that order,
  with at least one data row. Each `Change` cell is a kebab-case slug, unique
  within the table and, by convention, repo-unique — it should not collide with
  an existing or archived change. Each of `Code`, `Integration`, `Unknowns`,
  and `Risk` is `low`, `medium`, or `high`.

## The amend contract — what `<slug> amend` may change

A live epic (anything past `draft`) accretes only through the amendment
discipline: a fresh `epic-amend-<slug>` worktree, gated edits, a pull request.
A `draft` epic is not amended at all — it is edited in its authoring worktree.

- **Amendable.** `## Decisions`, and the shelf sections `## References`,
  `## Research`, and `## Video`. Reference material is installed through the
  `docs` kind and linked from `## References`; its content is never pasted into
  `## Decisions`.
- **Protected.** Everything else: the pre-section header block (title,
  `Status:`, `Theme:`, `Initiative:`, `PRD:`), `## Introduction` and its
  subsections,
  `## Design`, the `## Changes` stub table, the machine-owned
  `## Token usage breakdown`, and any unrecognized level-2 section. An
  amendment that needs one of these is a re-decomposition, not an amendment.
- **Stamp grammar.** Every new or extended Decision bullet carries
  `*(amended YYYY-MM-DD: <one-line note>)*` with the real current date.
  Existing Decision text is never rewritten or deleted; a superseded decision
  is recorded as a stamped addition beneath the original. The grammar is the
  flow's discipline — no verb enforces it.
- **The two gates**, both from the amendment worktree, both before pushing:
  `spec_lint.py --epic <slug>` (exit `0`, prints `OK`), then
  `spec_status.py epic-amend-check <slug> [--base <ref>]`, which compares the
  epic against its content at the merge-base of `HEAD` and the base ref
  (default `main`). It prints one `protected-section <name>` line per changed
  protected region (`header` for the pre-section block) plus a summary, exiting
  `0` clean and `4` on findings. A finding stops the flow. Any other non-zero
  exit is an error, not a finding — no epic in the work tree, no epic at the
  merge-base, an unresolvable base ref, or a root outside a git work tree.
