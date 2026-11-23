# docs-start-here
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: c1dcd66d006b

## Idea

Finish the Start here docs group: write the install and core ideas pages,
retitle the first-change guide, and point the cheatsheet and the overview at
the new feature pages.

### Motivation

A newcomer cannot learn how to install shipd, or what its terms mean, without
reading the 619-line `README.md`. A reader of the cheatsheet finds a command
but not the page that explains it.

### Details

| file | title | type | cap |
| --- | --- | --- | --- |
| `docs/install.md` (new) | Install | how-to | 150 |
| `docs/core-ideas.md` (new) | Core ideas | concept | 100 |
| `docs/getting-started.md` | Your first change | how-to | 150 |
| `docs/what-is-shipd.md` | What is shipd? | concept | 100 |
| `docs/cheatsheet.md` | Command cheatsheet | reference | 250 |

Affected capabilities: `project-readme` (three modified requirements, four
added) and `shipd-install` (one modified, one added). Impact: five entry
pages under `docs/`, plus link additions on the feature pages; no plugin, engine, test, or CI change, so no version bump.

### Non-goals

- No edit to `README.md` or `AGENTS.md`; `docs-readme-slim` owns them,
  including the missing `/s:demo` row in the README skill table.
- No edit to another group's page beyond the cross-group link sweep (Q3),
  which adds links and rewords nothing.
- No change to any skill, the standard,
  `docs_lint.py`, or the caps.

## Implementation

**Every page goes through `/s:document`** (epic Decision): read
`plugins/s/skills/document/references/standard.md` first, keep the marker on
line 1, and run `docs_lint.py <file>` until it exits 0.

**Only `install.md` takes the main-page shape (Q1).** It is a feature page, with
the headings `docs-plan-group` fixed. The other four are entry pages with shapes that verified
requirements pin: the overview, the six-step walk, and the two tables. They
keep those shapes. `core-ideas.md` is a concept page of seven idea sections.
Rejected: reshaping all five, which rewrites three pinned requirements.

**Fact owners (binding).** A non-owner gives one sentence and a link.

| fact | owner |
| --- | --- |
| Install, auto-update, `shipd install`, `update`, `vendor`, dev mode | `install.md` |
| The pitch and the overview diagram | `what-is-shipd.md` |
| Definitions of shipd's terms | `core-ideas.md` |
| The six-step first run, `/s:onboard` | `getting-started.md` |
| The list of every command | `cheatsheet.md` |
| The doctor check list and `--fix` | `doctor.md` |
| `shipd harness add` and the registry | `harnesses.md` |

So `getting-started.md` loses its PATH, auto-update, and harness paragraphs
and its doctor check list. Its step headings stay; `copilot-review.md`
links `#1-install`. The cheatsheet loses its `## doctor --fix` section,
which `docs-configure-group` moved to `doctor.md`.

**Cheatsheet links.** Each row's description cell ends with one link to the
command's main page, the form the `/s:room` row already uses. The map is in
`cheatsheet-page-links`. It rests on the owners the feature groups set, plus
Q2 for the commands no group claimed. The `/s:room` row keeps its
`multi-agent-pr.md` link, which `multi-agent-pr-entry-links` pins. Rejected:
a fourth table column; the pinned row already sets the form. The
`/s:document` row links `document.md`, which `docs-configure-group` adds.

**Cross-group link sweep (Q3).** The feature groups wrote other groups'
skills as inline code, because their pages could merge in any order. This
member runs last, so it links them. On each feature main page, the first
mention of a command another page owns becomes a link to that owner, per
the `cheatsheet-page-links` map. The sweep adds one link per owner page at
most, rewords nothing, and keeps every page within its cap.

**Cheatsheet drift.** Add the `/s:demo` row, the `room` and `gate rules`
verb rows, and `s:demo` in the "Spec, build, ship" list. Match each verb
row's forms to `shipd --help`.

**The overview diagram.** It still matches the text, so it stays. One fix:
the subgraph `Ship` becomes `Review and merge`, the name of the docs group.
`Intent` and `Record` stay; no group carries those names.

**Links.** This member runs after the eight feature groups, so it links
their pages by the names their plans fixed. Task 1.1 checks each target.

**Sources.** `install.md`: `README.md` sections "Install mode", "Per-repo
mode", "Dev mode", and the install finish; `shipd install --help`.
`core-ideas.md`: `docs/what-is-shipd.md`, `.shipd/README.md`, `README.md`
section "The spec engine", and each linked page. A fact found in none of
those stays out.

Risk: `install.md` condenses 170 README lines into 150. Guard: cut launcher
internals and the wordmark first; the cap is a task exit condition.

## Questions and answers

### Q1: Shape of the Start here entry pages
- **Question:** Does the main-page shape apply to the entry pages? Options:
  (1) only `install.md` takes it; the overview, the first-change guide, core
  ideas, and the cheatsheet keep their own shapes; (2) all five take it; (3)
  install and core ideas take it. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic defines the shape for a feature, and three
  verified requirements pin the entry pages' current shapes.
- **Queued:** q-docs-start-here-entry-page-shape

### Q2: Main page for commands the page map leaves out
- **Question:** Which page is the main page for `/s:document`, `/s:onboard`,
  `shipd related`, `shipd search`, and `shipd render`? Options: (1)
  `/s:onboard` on `getting-started.md`, `related` on `fix.md`, `search` and
  `render` on the PRD page's nested `prd-reference.md`, and `/s:document`
  with a cheatsheet row only; (2) also add a `/s:document` section to an
  existing page; (3) cheatsheet rows only for all five. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 for `/s:onboard`, `related`, `search`, and `render`.
  `/s:document` gets its own page, `docs/document.md`, which
  `docs-configure-group` adds; its cheatsheet row links it.
- **Queued:** q-docs-start-here-unassigned-command-pages

### Q3: Cross-group links on feature pages
- **Question:** The feature groups wrote other groups' skills as inline
  code. Does this member turn them into links? Options: (1) no; the
  cheatsheet and core ideas are the cross-group routes; (2) yes, a sweep
  over every feature page. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2. This member sweeps every feature main page and
  links the first mention of each command another page owns. It rewords
  nothing, and a page at its cap gains room by rewrap only.
- **Queued:** q-docs-cross-group-links

## Readiness attestation

### Problem and motivation

Install and the core terms have no docs page, and the cheatsheet does not
say where a command is explained.

Evidence:

- `README.md:13-238` holds the only install prose; `ls docs/` shows no
  `install.md` or `core-ideas.md`.
- `docs/cheatsheet.md:56-114`: one row of 54 carries a link.
- Epic `docs-by-feature`, Changes row `docs-start-here`.

### Scope and non-goals

Five docs files are in scope. The README, other groups' pages, and every
skill are out.

Evidence:

- Epic Design "The seams" gives the README to `docs-readme-slim`; the page
  map fixes the five pages.

### Affected capabilities and files

Two capabilities are affected: four modified requirements and five added.
Five entry pages change, and the feature pages gain links.

Evidence:

- `project-readme`: `pipeline-follower-docs` (base 0f1eb0e388cf),
  `harness-mode-docs` (ecc8f8987338), `entry-docs-standard` (5d4db84ecc08).
  `shipd-install`: `install-mode-docs` (ef32c3bb4f4a). Hashes from
  `spec_status.py base-hash`.
- Pins that hold unedited: `getting-started-doc`, `cheatsheet-doc`,
  `what-is-overview-layout`, `multi-agent-pr-entry-links`,
  `customisation-guide`.
- Files: `docs/getting-started.md:1-150`, `docs/what-is-shipd.md:1-94`,
  `docs/cheatsheet.md:1-127`, and two new files.
- Runnable premise: `docs_lint.py` over the three pages → exit 0.
- Runnable premise: `plugins/s/bin/shipd --help` → exit 0, 25 verbs,
  including `room` and `gate rules`, which the cheatsheet lacks.
- Runnable premise: `ls plugins/s/skills` → 32 directories; the
  cheatsheet lacks `demo`.
- Runnable premise: `shipd install --help`, `shipd update --check`, and
  bare `shipd vendor` → each exit 0; `vendor` printed four surface states.

### No open task-shaping decision

Every task-shaping decision is settled; three rest on planner defaults.

Evidence:

- Entry-page shape, unassigned commands, link sweep: the owner's answers,
  Q1 to Q3.
- Link targets and command owners: the eight sibling plans.
- File names, doc types, link form, the diagram fix: investigation. The
  personal memory store is absent.
