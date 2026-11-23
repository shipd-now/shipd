# docs-knowledge-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 5654cdbdaace

## Idea

Give the Knowledge group one main page per feature: reshape `docs/oracle.md`,
and write the wiki and personal memory pages.

### Motivation

A reader who wants to fill the workspace wiki or manage personal preferences
cannot find a docs page for it: `/s:teach`, `/s:remember`, `/s:memory`, and
`/s:forget` are described only in the `README.md` skill table and the
cheatsheet. A reader of the oracle page cannot tell when to run `/s:ask`,
because the page does not follow the shape every other main page takes.

### Details

- New how-to pages: `docs/wiki.md` (the wiki store, `/s:teach`, the `shipd
  wiki` verbs) and `docs/memory.md` (`/s:remember`, `/s:memory`,
  `/s:forget`).
- `docs/oracle.md` takes the main-page shape, keeps its `reference` marker
  and its ladder diagram, and hands the teach and memory detail to the two
  new pages.

Affected capabilities: `shipd-ask` (modified); `shipd-teach` and
`shipd-memory` (one added requirement each). Impact: three files under
`docs/`; no engine, skill, test, or CI change, so no version bump.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/cheatsheet.md`, or any page of
  another group; `docs-start-here` and `docs-readme-slim` own those.
- No change to the standard, `docs_lint.py`, the caps, or any skill.
- No nested reference page and no new diagram.
- No page for store nesting, `wiki_base`, or config keys; the Workspaces and
  Configure groups own those.

## Implementation

**Every page is written through `/s:document`** (epic Decision), which reads
`plugins/s/skills/document/references/standard.md` and ends with
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` at exit 0.

**Files, types, and caps (binding).** Later members link to these paths.

| file | title | type | cap | diagram |
| --- | --- | --- | --- | --- |
| `docs/oracle.md` | The oracle | reference | 250 | keeps the ladder |
| `docs/wiki.md` (new) | The wiki | how-to | 150 | none |
| `docs/memory.md` (new) | Personal memory | how-to | 150 | none |

**The main-page shape.** After the title, the opening says what the feature
is. Then come `## When to use it`, `## How to run it`, and a closing
`## Reference`, with those exact headings, as `docs-plan-group` uses them.
`oracle.md` keeps `## The ladder` between its opening and
`## When to use it`; the ladder is part of "what it is". No page keeps a
`## See also` section; its links move into prose or `## Reference`.

**`oracle.md` stays one page (Q3).** Its content moves; nothing pinned by
`oracle-user-docs` is dropped. `## How to run it` takes "Using it directly".
`## Reference` takes four level-3 sections: `### The two verdicts` (the
examples become level 4), `### The bar: definitive evidence, or nothing`,
`### What gets captured`, and `### Correcting an answer`. The anchor
`#what-gets-captured` survives. Rejected: a nested `oracle-reference.md`,
which the epic's list of four nested pages does not name.

**Fact owners (binding).** A non-owner gives one sentence at most and links.

| fact | owner |
| --- | --- |
| The ladder, both verdicts, the advisory variant, the evidence bar, the three capture tiers, `/s:ask` | `oracle.md` |
| The store's files, the `/s:teach` sweep, queue draining, `/s:teach <change> Q<n>`, promotion to a base store, the build-time teacher, `shipd wiki`, `shipd lint --wiki` | `wiki.md` |
| The `memory-<subject>` page, the three memory skills, the git backing | `memory.md` |
| Workspace discovery, the store chain | `workspaces.md` and its nested pages |
| The `memory_dir` and `wiki_base` keys | `customise.md` |

So `### Correcting an answer` shrinks to the write-once rule, `/s:teach` as
the correction path with a link to `wiki.md`, and the rule that a typed
answer wins.

**Commands.** A page shows a `/s:` skill or a `shipd` verb, never an engine
script path. `oracle.md` names `oracle-lookup`, `wiki-queue-answer`, and
`wiki-queue-discard` as bare verb names; its `spec_status.py` prefix goes.

**Links (Q4).** A page links only to files on `main` plus this change's three
pages: `oracle.md`, `wiki.md`, `memory.md`, `workspaces.md`, `customise.md`,
`what-is-shipd.md`. `wiki.md` links `workspaces.md`, never
`workspaces/nesting-and-stores.md`, which another member splits. Other
groups' skills (`/s:plan`, `/s:build`, `/s:init`) appear as inline code.

**Diagrams.** The ladder diagram still matches the text, so it stays. The
teach sweep and the memory flows are linear lists, so they get none.

**Sources.** `wiki.md`: `plugins/s/skills/teach/SKILL.md`,
`plugins/s/agents/teacher.md`, `shipd --help`. `memory.md`: the `remember`,
`memory`, and `forget` skills' `SKILL.md`. `oracle.md`: its current text and
`plugins/s/skills/ask/SKILL.md`. A fact found in none of those stays out.

**Spec placement.** Each requirement lands in the capability of the page's
lead skill, as `oracle-user-docs` does in `shipd-ask`.

Risk: `oracle.md` sits at 236 lines and gains three headings and one
section. Guard: the 250 cap is a task exit condition; the cut `## See also`
and the shorter correction section free about 12 lines. Compress prose
before any pinned fact.

## Questions and answers

### Q1: File names of the two new pages
- **Question:** Which file names do the wiki and personal memory pages take
  under `docs/`? Options: (1) `wiki.md` and `memory.md`, short names that
  follow the feature; (2) `the-wiki.md` and `personal-memory.md`, mirroring
  the titles; (3) `teach.md` and `remember.md`, following the lead skill.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It matches `oracle.md` and the short names the Plan
  and Build groups chose.
- **Queued:** q-docs-knowledge-page-filenames
- **Relied on by:** docs-start-here

### Q2: Doc type of a new main page
- **Question:** Which doc-type marker do the two new main pages carry?
  Options: (1) how-to, 150 lines, for both; (2) concept, 100 lines; (3)
  chosen per page. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: how-to for both. The shape centres on running the
  feature. `oracle.md` keeps `reference`, which its requirement pins.
- **Queued:** q-docs-feature-main-page-doc-type

### Q3: Shape of the oracle page
- **Question:** Does `docs/oracle.md` stay one page or split? Options: (1)
  one reference page of 250 lines or fewer, reordered into the main-page
  shape; (2) a concept main page plus a new nested `oracle-reference.md`.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic names four nested reference pages and no
  oracle reference, and the content fits the reference cap.
- **Queued:** q-docs-oracle-page-shape

### Q4: Links to pages a sibling member has not merged
- **Question:** May a page link to a page another member has yet to merge?
  Options: (1) link only files on `main` plus this member's own pages,
  naming other skills as inline code; (2) link planned sibling file names
  and accept dead links. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The feature groups land in any order, so a link to an
  unmerged page stays dead for an unknown time.
- **Queued:** q-docs-links-to-unmerged-sibling-pages

## Readiness attestation

### Problem and motivation

The wiki and personal memory have no docs page, and the oracle page does not
follow the main-page shape.

Evidence:

- `README.md:293-301`: the only prose on `/s:teach`, `/s:remember`,
  `/s:memory`, and `/s:forget`.
- `docs/oracle.md:156-174` holds the run steps under "Using it directly";
  the page has no when-to-use section.
- Epic `docs-by-feature`, Changes row `docs-knowledge-group`.

### Scope and non-goals

Three docs files are in scope; the README, the cheatsheet, and every other
group's page are out.

Evidence:

- Epic `docs-by-feature`, Design "The seams": `docs-start-here` owns the
  cheatsheet, `docs-readme-slim` owns the README.
- Epic page map: nesting and external stores sit in Workspaces, `customise.md`
  in Configure.

### Affected capabilities and files

Three capabilities pin one docs requirement each, over three files.

Evidence:

- `shipd-ask`: requirement `oracle-user-docs` (base a602655b1083, from
  `spec_status.py base-hash shipd-ask oracle-user-docs`).
- `shipd-teach`, `shipd-memory`: neither holds a `*-user-docs` id today.
- Files: `docs/oracle.md:1-236`, and two new files under `docs/`.
- Inbound: `docs/tutorials/videos/06-oracle-and-supersession-gate.md:62`
  links `oracle.md`, which keeps its path.
- Runnable premise: `docs_lint.py docs/oracle.md` → exit 0, no findings.
- Runnable premise: `shipd wiki` → exit 0, printed the store root, page
  count, coverage, pending questions, and last log entry.
- Runnable premise: `shipd wiki --personal` → exit 1, `no wiki store at
  ~/.shipd-memory/wiki`; the flag resolves the personal store.
- Runnable premise: `shipd lint --wiki` → exit 0, `OK: wiki is valid.`;
  `shipd --help` lists `wiki [init]`.
- `.github/workflows/ci.yml:123-130` lints every file under `docs/` outside
  retros, so new pages need no CI edit.

### No open task-shaping decision

Every task-shaping decision is settled; four rest on planner defaults.

Evidence:

- File names, doc type, the oracle page's shape, and sibling links: planner
  defaults, Q1 to Q4.
- Fact owners, headings, diagrams, and spec placement: investigation, from
  the epic's Decisions and the `docs-plan-group` and `docs-epics-group` plans.
- Personal memory store: absent, so no preference applied.
