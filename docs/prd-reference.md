<!-- doc-type: reference -->

# PRD reference

[PRDs](prd.md) is the concept guide: what a PRD is, where it lives, and how the
discover phase works. This page lists the formats, the rules, and the command
surfaces.

## The header

A PRD's header sits among the document's first five non-blank lines. The `# `
title names the slug, which is also the directory name.

```
# mobile-push
Status: draft
Template: standard
Initiative: retention
```

| Key | Required | Value |
| --- | --- | --- |
| `Status:` | yes | `draft`, `approved`, or `superseded` |
| `Template:` | yes | `basic`, `standard`, or `comprehensive` |
| `Initiative:` | no | the slug of a brief on the workspace chain |

The `Template:` line is mandatory, and its value must name one of the three
tiers. An absent or unknown value is an error, never a silent default to
`standard`.

`Initiative:` is the only optional key the header recognizes. Validation
rejects any other key. It also rejects an `Initiative:` value that resolves to
no brief on the workspace chain.

## Statuses

A PRD is a document, not a change, so it carries its own three-value status
vocabulary — deliberately not the change statuses.

| Status | Meaning |
| --- | --- |
| `draft` | Being written. Every PRD is authored at this status. |
| `approved` | Signed off. The problem statement is settled. |
| `superseded` | Replaced by a later PRD. Kept for the record, not for work. |

## Approval: a staged re-install

**Advancing the status is a re-install, never a hand edit.** No status verb
exists for a PRD. To approve one, edit a copy of the document with
`Status: approved`. `/s:prd` then re-installs that copy through the engine's
staged emit, with a replace flag.

The engine copies the staged file into place and validates the result. On any
finding it removes what it just staged, restores the document it replaced, and
exits non-zero. Nothing half-written ever lands in the store.

So never edit the file in the store directly. Validation runs on install, and a
hand edit bypasses the one gate that keeps the store lint-clean. The
restore-on-failure behavior lives only on the install path.

Check a single PRD against that same validation at any time:

```sh
shipd lint --prd mobile-push
```

## Template tiers

The engine defines three template tiers, and the plugin ships one skeleton per
tier. Their required sections are **exact level-2 headings**. The tiers **nest
additively**: every section a lower tier requires, the higher tier requires
too.

| Tier | Required sections |
| --- | --- |
| `basic` | `## Problem`, `## Solution`, `## Success criteria` |
| `standard` | `basic`'s three, plus `## Users`, `## Requirements`, `## Non-goals` |
| `comprehensive` | `standard`'s six, plus `## Risks`, `## Rollout`, `## Open questions` |

**`standard` is the default.** Choose `basic` for a small, self-contained idea
whose users and scope are obvious. Choose `comprehensive` for blast radius
across several projects, regulatory or risk weight, a phased rollout, or
several distinct user classes.

The nesting makes a mid-interview tier switch cheap. Escalating from `standard`
to `comprehensive` only *adds* sections to cover, and invalidates nothing you
already answered. De-escalating keeps the extra answers as sections beyond the
tier's list.

That costs nothing, because the tier list is a **floor, not a ceiling**.
Validation requires every section the declared tier names, and allows any
number of sections beyond them.

## The epic's `PRD:` link

An epic born from a PRD carries the link in its own header:

```
# push-delivery
PRD: mobile-push
```

The epic linter resolves that slug across the workspace chain whenever a
workspace is discoverable. It rejects a value that resolves to nothing, naming
the path it expected.

In a checkout with no discoverable workspace — a bare CI runner, for
instance — the linter skips the check silently. Repository lint never depends
on files outside the repository.

The link runs one way only. A PRD holds no list of its epics and knows nothing
about them. One PRD decomposes into several epics, or into none at all, and
deleting an epic leaves the PRD untouched.

## Finding PRDs: `shipd search`

`shipd search` is the retrieval surface that lists PRDs. It ranks a wide corpus
by case-insensitive term-hit count:

- the spec library, epics, research reports, and installed documents,
- the workspace wiki and the workspace's initiative briefs **and PRDs**,
- the invoking repo's git-tracked files.

```sh
shipd search mobile push notifications
```

```
kind: prd
slug: mobile-push
score: 34
path: /Users/you/workspaces/notifications/.shipd/prds/mobile-push/prd.md

kind: epic
slug: push-delivery
score: 12
path: .shipd/epics/push-delivery/epic.md

kind: code
slug: src/notify/apns.py
score: 9
path: src/notify/apns.py

… and 4 more
```

Each match prints as a four-line block — `kind`, `slug`, `score`, `path` — and
`kind: prd` marks a PRD. A path is relative to the invocation root when the
artifact lives inside it, and absolute otherwise. That is why a workspace PRD
reports an absolute path from a member repo.

At most ten blocks print, and the trailing line counts the rest. Add `--json`
for the same rows as one machine-readable document.

The workspace roster report — `shipd workspace` — lists the workspace's
projects and initiatives, but **not** its PRDs. `search` finds a PRD by what it
says; `shipd prd` lists and reports on them by slug.

## Inspecting PRDs: `shipd prd`

`shipd prd <slug>` prints one PRD's report: its header facts, where the slug
resolved, and which epics cite it.

```sh
shipd prd mobile-push
```

```
mobile-push: approved
Template: standard
Initiative: q3-activation
path: /Users/you/workspaces/notifications/.shipd/prds/mobile-push/prd.md
cited-by: push-delivery (active)
cited-by: push-analytics (draft)
```

The `Initiative:` line prints only when the header carries one. The `path:`
line is where the slug actually resolved on the workspace chain. It reads
relative when the document lives inside the invocation root, and absolute
otherwise. A workspace PRD read from a member repo takes the absolute form.

The `cited-by:` lines reverse the epic header's `PRD:` link, which the PRD
itself does not record. The engine derives them by reading the epics of the
repository you invoke from. That means the repo and its worktrees, so an epic
still sitting on a branch counts. It scans no further: epics in *other* repos
of the workspace stay out. A PRD no epic cites prints one explicit line:

```
cited-by: none
```

Bare `shipd prd` lists the roster instead — every PRD the workspace chain
holds, one line per slug, sorted:

```sh
shipd prd
```

```
mobile-push: approved (standard)
quiet-hours: draft (basic)
weekly-digest: superseded (comprehensive)
```

A slug held by more than one chain member appears once, showing the nearest
member's copy. That is the same shadowing that decides which document
`shipd prd <slug>` reports on. A chain holding no PRDs at all reports the empty
store rather than failing. Both forms accept `--json` for the same facts as one
machine-readable document.

## Reading the document: `shipd render`

The report holds facts, not the document. To read the PRD itself, hand
the report's `path:` line to the markdown viewer:

```sh
shipd render ~/workspaces/notifications/.shipd/prds/mobile-push/prd.md
```

## See also

- [PRDs](prd.md) — the discover phase, the hierarchy, and where a PRD lives.
- [Workspaces](workspaces.md) — the store that holds every PRD.
