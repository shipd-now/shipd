# docs-plan-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 9a954713e65c

## Idea

Give the Plan group one main page per feature: write the research, video
ingest, rubber duck, and plan-a-change pages, and reshape the PRD page.

### Motivation

A reader who wants to research a question, ingest a recording, talk an idea
through, or plan a change cannot find a docs page for it: those four features
are described only in the `README.md` skill table and the cheatsheet. A reader
of the PRD pages meets the lifecycle, the tiers, and the one-way epic link
explained on both pages and cannot tell which one to trust.

### Details

- New how-to pages: `docs/research.md`, `docs/video-ingest.md`,
  `docs/duck.md`, `docs/plan.md` (`/s:plan`, `/s:plan-deep`, the spec
  lifecycle, `/s:status`).
- `docs/prd.md` takes the main-page shape and keeps its `concept` marker;
  `docs/prd-reference.md` stays its nested reference. Each repeated fact
  keeps one owner.

Affected capabilities: `shipd-prd` (modified); `shipd-research`,
`shipd-video-ingest`, `shipd-duck`, `shipd-plan` (one added requirement
each). Impact: six files under `docs/`; no engine, skill, test, or CI change.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/cheatsheet.md`, or any page of
  another group; `docs-start-here` and `docs-readme-slim` own those.
- No change to the standard, `docs_lint.py`, the caps, or any skill.
- No new nested reference page and no new diagram.
- No main-page assignment for `shipd related`, `search`, or `render`.

## Implementation

**Every page is written through `/s:document`** (epic Decision), which reads
`plugins/s/skills/document/references/standard.md` and ends with
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` at exit 0.

**Files, types, and caps (binding):**

| file | type | cap |
| --- | --- | --- |
| `docs/prd.md` | concept | 100 |
| `docs/prd-reference.md` | reference | 250 |
| `docs/research.md` (new) | how-to | 150 |
| `docs/video-ingest.md` (new) | how-to | 150 |
| `docs/duck.md` (new) | how-to | 150 |
| `docs/plan.md` (new) | how-to | 150 |

Each page takes its facts from the feature's `SKILL.md` under
`plugins/s/skills/` (`plan.md` also from `plan-deep`, `status`, and
`README.md:303-403`); `tasks.md` names the files per task.

**The main-page shape.** After the title, the opening paragraphs say what the
feature is. Then come `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order and with those exact headings. A page may add
level-3 headings inside a section. `prd.md` may keep its two concept sections
(`## The hierarchy`, `## Where a PRD lives`) between the opening and
`## When to use it`; they are part of "what it is". No page keeps a
`## See also` section; its links move into prose or `## Reference`.

**Fact owners (binding).** The non-owner states the fact in one sentence at
most and links to the owner.

| fact | owner |
| --- | --- |
| Hierarchy, upward references, standalone nature, a PRD holds no epic list | `prd.md` |
| Storage path, chain resolution, the no-workspace refusal | `prd.md` |
| Statuses, approval by staged re-install, `shipd lint --prd` | `prd-reference.md` |
| Tier section lists, the default tier, when to pick each tier | `prd-reference.md` |
| `shipd prd`, `shipd search`, `shipd render`, the `PRD:` lint rule | `prd-reference.md` |
| The change lifecycle, `/s:status`, `shipd status`/`lint`/`list`/`locate` | `plan.md` |
| `/s:plan` taking a recording path, a bundle slug, or a supplied document | `plan.md` |

So `prd.md` drops its `## Lifecycle and tiers` section; its `## Reference`
names the three statuses and three tiers in one sentence each.
`prd-reference.md` cuts the "link runs one way only" paragraph to one linked
sentence. Every other fact on both pages survives.

**Commands.** Every command a page shows invokes the `shipd` binary or names
a `/s:` skill, never an engine script path. The context gate and the video
preflight have no binary verb, so the pages describe them as steps the skill
runs. Rejected: showing `spec_gate.py` — it breaks the rule `prd-user-docs`
already carries.

**Links.** A page links only to files on `main` plus this change's own pages
(Q5). Other groups' features appear as inline code (`/s:build`, `/s:epic`).
Every relative link must resolve; `.shipd/README.md` is `../.shipd/README.md`.

**Diagrams.** `prd.md` keeps its hierarchy diagram: it still matches the
text. No new page gains one: the research and ingest stages are lists, and
the lifecycle is a status table plus one sentence on `rejected`.

**Risks.** `docs/plan.md` is the tight page: three skills and the lifecycle
in 150 lines. The guard is the outline in `plan-user-docs` and leaving the
grammar to `.shipd/README.md`. `prd.md` adds `## When to use it` under a
100-line cap; the dropped section and `## See also` free about 20 lines.

## Questions and answers

### Q1: File names of the four new pages
- **Question:** Which file names do the four new Plan-group pages take under
  `docs/`? Options: (1) `research.md`, `video-ingest.md`, `duck.md`,
  `plan.md`, short names that follow the skill as `prd.md` does; (2)
  `research.md`, `video-ingest.md`, `rubber-duck.md`, `plan-a-change.md`,
  mirroring the page titles. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It matches `prd.md` and the short-name default the
  Build group queued in `q-docs-build-page-filenames`.
- **Queued:** q-docs-plan-page-filenames
- **Relied on by:** docs-review-group, docs-start-here, docs-readme-slim

### Q2: Doc type of a new main page
- **Question:** Which doc-type marker does a new main page carry? Options:
  (1) how-to, 150 lines, for all four; (2) concept, 100 lines; (3) chosen per
  page. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: how-to for all four. The shape centres on running the
  feature. `prd.md` keeps `concept`, which its verified requirement pins.
- **Queued:** q-docs-feature-main-page-doc-type
- **Relied on by:** docs-knowledge-group, docs-review-group

### Q3: Home of the spec lifecycle
- **Question:** Does `docs/plan.md` hold the lifecycle in its closing
  Reference section, or gain a nested `plan-reference.md`? Options: (1) one
  page with a status table; (2) a nested reference page. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic's page map names four nested reference
  pages and no plan reference, and the status table fits the cap.
- **Queued:** q-docs-plan-lifecycle-nested-reference
- **Relied on by:** docs-readme-slim

### Q4: Main page for the status skill and lifecycle verbs
- **Question:** Which page is the main page for `/s:status` and the
  `shipd status`, `lint`, `list`, and `locate` verbs? Options: (1)
  `docs/plan.md`, beside the lifecycle; (2) the build page; (3) the
  cheatsheet alone. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The page map gives plan-a-change the spec lifecycle,
  and these are the lifecycle's skill and verbs.
- **Queued:** q-docs-plan-status-verbs-owner
- **Relied on by:** docs-start-here

### Q5: Links to pages a sibling member has not merged
- **Question:** May a new page link to a page another member has yet to
  merge? Options: (1) link only files on `main` plus the member's own pages,
  naming other skills as inline code; (2) link planned sibling file names and
  accept dead links. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The feature groups land in any order, so a link to an
  unmerged page stays dead for an unknown time.
- **Queued:** q-docs-links-to-unmerged-sibling-pages
- **Relied on by:** docs-knowledge-group, docs-review-group, docs-room-group

## Readiness attestation

### Problem and motivation

Four Plan-group features have no docs page, and the two PRD pages explain
the same facts twice.

Evidence:

- `README.md:259`, `README.md:277-284`: the only prose on `/s:duck`,
  `/s:plan`, `/s:plan-deep`, `/s:research`, and `/s:video-ingest`.
- `docs/prd.md:65-80` repeats `docs/prd-reference.md:35-88`;
  `docs/prd.md:60-63` repeats `docs/prd-reference.md:105-107`.
- Epic `docs-by-feature`, Changes row `docs-plan-group`.

### Scope and non-goals

Six docs files are in scope; the README, the cheatsheet, and every other
group's page are out.

Evidence:

- Epic `docs-by-feature`, Design "The seams": `docs-start-here` owns the
  cheatsheet, `docs-readme-slim` owns the README.
- Epic Decision "The caps stand": four nested reference pages, none for plan.

### Affected capabilities and files

Five capabilities pin one docs requirement each, over six files.

Evidence:

- `shipd-prd`: requirement `prd-user-docs` (base 22fc707e2c7f, from
  `spec_status.py base-hash shipd-prd prd-user-docs`).
- `shipd-research`, `shipd-video-ingest`, `shipd-duck`, `shipd-plan`: none
  carries a docs requirement today (grep of each `spec.md`).
- Files: `docs/prd.md:1-100`, `docs/prd-reference.md:1-223`, and four new
  files under `docs/`.
- Runnable premise: `docs_lint.py docs/prd.md docs/prd-reference.md` → exit
  0, no findings.
- Runnable premise: `shipd list research` → exit 0, one row per report;
  `shipd list video` → exit 0, `no video briefs`; `shipd status` → exit 0,
  the library summary; `shipd lint` → exit 0, `OK: master library is valid.`;
  `shipd --help` lists `locate [change]`.
- CI lints every file under `docs/` except `docs/retros/`
  (`.github/workflows` "Lint docs" step), so new pages need no CI edit.

### No open task-shaping decision

Every task-shaping decision is settled; five rest on planner defaults.

Evidence:

- File names, doc type, the lifecycle's home, the status verbs' owner, and
  sibling links: planner defaults, Q1 to Q5.
- Fact owners, headings, and diagrams: investigation, from the epic's
  Decisions and the two PRD pages.
