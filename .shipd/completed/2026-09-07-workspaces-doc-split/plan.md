# workspaces-doc-split
Status: verified

## Idea

Split the 666-line `docs/workspaces.md` into five focused part pages under
`docs/workspaces/`, and turn `docs/workspaces.md` itself into an index page
that explains the concept and introduces each part with one sentence, a basic
usage example, and a link.

### Motivation

The workspaces guide has grown to 666 lines across ten sections, and the user
asked for it to be split logically (3–5 parts) behind an index page so the
concept is graspable at a glance and each topic is reachable without scrolling
one monolith.

### Details

- New `docs/workspaces/` directory with five part pages, content moved
  verbatim from the current sections:
  `getting-started.md` (§1–§5), `nesting-and-stores.md` (§6–§7),
  `teams.md` (§8), `headless.md` (§9), `multi-workspace-repos.md` (§10).
- `docs/workspaces.md` becomes the index: the existing concept intro and
  layout diagram (current lines 1–28), then one entry per part — a single
  descriptive sentence, a basic usage example, and a relative link.
- Cross-section links that now cross a page boundary are rewritten to
  cross-file links; links within one part stay anchors.
- The two governing requirements in `shipd-workspace` (`workspaces-doc`,
  `workspaces-doc-examples`) are updated to describe the index + parts
  structure while keeping every existing content mandate.

Affected capabilities: `shipd-workspace` (modified). Impact:
`docs/workspaces.md`, five new files under `docs/workspaces/`; no code, no
dependencies, no plugin version bump.

### Non-goals

- No content rewrite: every section's prose, examples, tables, and diagrams
  move verbatim — only headings' numbering prefixes, cross-links, and the
  minimal connective lead-ins may change.
- No change to `docs/oracle.md:225`'s link or `spec_common.py:1760`'s comment
  — both reference `docs/workspaces.md`, which survives as the index (and
  touching `spec_common.py` would force a version bump this docs-only change
  avoids, per the PR #129/#151 precedent).
- No plugin version bump: nothing under `plugins/s/` changes.
- No renaming of the `~/workspaces/` convention, no new commands, no engine
  or skill changes.

## Implementation

- **Five parts, matching the doc's own section groupings.** §1–§5 form the
  standalone lifecycle (setup → create → commit → load → day-to-day); §6–§7
  are the advanced layout keys (`--nested`, `store_root`); §8 is team
  sharing; §9 is the headless contract; §10 is the multi-workspace worked
  examples. The user authorized any of 3–5 parts; five keeps every page
  57–160 lines. Rejected: folding §10 into §6–§7 — a ~300-line page would
  reproduce the monolith problem for the most example-heavy content.
- **Index keeps the `docs/workspaces.md` path.** The verified requirement,
  `docs/oracle.md`, and a `spec_common.py` comment all point there; keeping
  the path makes the split invisible to inbound references. Parts live in
  `docs/workspaces/` (subdirectory precedent: `docs/retros/`).
- **Index entry shape** (per the user's request): for each part, one
  sentence saying what it covers, one short fenced example (e.g.
  `shipd workspace init documents-linking --git` for getting started,
  `shipd workspace init <base>/job --nested --git` for nesting,
  `git pull` / `git push` for teams, the `spec_status.py --root /tmp/ws
  workspace-show` invocation for headless, `git clone` + `shipd workspace
  sync` for multi-workspace repos), then a `[Details →](workspaces/<part>.md)`
  link. The index keeps the `# Workspaces` title and the concept intro +
  labeled layout diagram verbatim.
- **Part page shape.** Each part opens with an `# <Title>` line and a
  one-line breadcrumb link back to the index (`[← Workspaces](../workspaces.md)`),
  then carries its sections verbatim. Section headings drop the global
  `<n>.` numbering prefix (e.g. `## 6. Nesting job workspaces` →
  `## Nesting job workspaces`) since the numbering was an artifact of the
  monolith; anchors change accordingly and the link-fix task sweeps them.
- **Cross-boundary link map** (current line → new target), applied
  mechanically: lines 49, 59 (§1→§6) → `workspaces/nesting-and-stores.md`
  from within getting-started (relative: `nesting-and-stores.md`); 70
  (§1→§9) → `headless.md`; 146 (§3→§8) → `teams.md`; 192 (§6→§2) →
  `getting-started.md`; 340, 455 (§8→§4/§3) → `getting-started.md`; 532,
  568, 630 (§10→§2/§4) → `getting-started.md`; 580, 610 (§10→§6) →
  `nesting-and-stores.md`; 645 (§10→§8) → `teams.md`. Line 82 (§2→§1) stays
  an in-file anchor. Bare textual `(§1)`/`(§n)` references are swept and
  rewritten to the part name with a link where they cross a boundary.
- **Delta shape.** Two MODIFIED requirements in `shipd-workspace`:
  `workspaces-doc` is restated for the index + parts structure — same
  content mandates, each located on its new page, plus the index mandates
  (concept, per-part sentence + example + link) and a no-dangling-links
  mandate; `workspaces-doc-examples` is restated to name the
  `multi-workspace-repos.md` part page instead of "a section". Base hashes
  computed this session via `spec_common.content_hash`: `dc3e2ca22814`,
  `bb550e790db0`.
- **Risk:** a dropped or dangling link after relocation. Guarded by the
  explicit link map above and a verification task that greps every
  `](#...)` anchor and `](...)`/`](workspaces/...)` relative link in the six
  files and confirms each target exists.
