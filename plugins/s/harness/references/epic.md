# /s:epic reference — the epic contract the linter enforces

`.shipd/epics/<slug>/epic.md`, where `<slug>` is the kebab-case directory name:

```
# <slug>
Status: draft
Theme: <kebab-theme>            (optional)
Initiative: <kebab-initiative>  (optional)

## Introduction

The why first — the problem and its motivation — then the what and its intended
outcome, success criteria recommended.

### Non-goals

- <what this epic explicitly does not do>

## Research                        (optional)

- [<report title>](../../research/<name>/report.md) <optional annotation>

## Video                           (optional)

- [<brief title>](../../video/<slug>/brief.md) <optional annotation>

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
  metadata block recognizes only `Theme:` and `Initiative:`, both kebab-case;
  `Profile:` and `Epic:` are not valid on an epic. Where the config declares a
  non-empty `valid_themes`, `Theme:` must be one of them.
- **Sections.** `## Introduction`, `## Decisions`, `## Design`, `## Changes`
  are all required, and `## Introduction` must be the first level-2 section and
  carry a `### Non-goals` subsection.
- **Research and Video (both optional).** Omit the section entirely when there
  is none. When present it holds at least one `- [title](path)` entry whose
  link resolves (epic-dir first, then repo root) to an existing file under the
  content directory's `research/` or `video/` folder; the epic-relative form
  above is the clickable convention. An empty section, a dead link, or a link
  outside that folder is a lint error. List only what you actually read.
- **Stub table.** The header row is exactly those six columns in that order,
  with at least one data row. Each `Change` cell is a kebab-case slug, unique
  within the table and, by convention, repo-unique — it should not collide with
  an existing or archived change. Each of `Code`, `Integration`, `Unknowns`,
  and `Risk` is `low`, `medium`, or `high`.
