# docs-epics-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 8aa9d45d6b1a

## Idea

Write the five main pages of the Epics docs group: epics, epic grill,
autopilot, drift, and initiatives.

### Motivation

A reader who wants to decompose a feature, plan its members, or run them
unattended cannot find a docs page for any of those skills. The `docs-by-feature`
epic gives every feature one main page, and this member owns the Epics group.

### Details

- Add `docs/epics.md` (`/s:epic`, its amend mode, `/s:explain`).
- Add `docs/epic-grill.md` (`/s:epic-grill`).
- Add `docs/autopilot.md` (`/s:autopilot`, both modes).
- Add `docs/drift.md` (`/s:drift`).
- Add `docs/initiatives.md` (`/s:initiative`, four verbs).

Affected capabilities, one added requirement each: `shipd-epic`,
`shipd-epic-grill`, `epic-autopilot`, `shipd-drift`, `shipd-initiative`.
Impact: five new files under `docs/`. No engine, skill, test, or CI change;
the CI `Lint docs` step already globs every file under `docs/`.

### Non-goals

- No edit to an existing docs page, `README.md`, or `AGENTS.md`. This member
  renames and deletes nothing, so it owes no inbound link fix.
- No cheatsheet or core-ideas link to the new pages; `docs-start-here` adds
  those. No README row removal; `docs-readme-slim` owns it.
- No nested reference page, and no change to any skill, the standard, or
  `docs_lint.py`.
- No website manifest work.

## Implementation

**File names and types (binding).** Later members link to these paths.

| file | title | type | cap | diagram |
| --- | --- | --- | --- | --- |
| `docs/epics.md` | Epics | how-to | 150 | none |
| `docs/epic-grill.md` | Epic grill | how-to | 150 | none |
| `docs/autopilot.md` | Autopilot | how-to | 150 | one mermaid |
| `docs/drift.md` | Drift | how-to | 150 | none |
| `docs/initiatives.md` | Initiatives | how-to | 150 | none |

- **Every page is how-to (Q1).** The epic's page shape centres on running
  the feature. Rejected: concept, whose 100-line cap squeezes the run steps.
- **Page shape (Q4).** The opening says what the feature is. Then come the
  exact level-2 headings `## When to use it`, `## How to run it` (numbered
  steps), and `## Reference`, as `docs-plan-group` fixed them. The
  Reference section holds one short table plus links.
- **Autopilot stays one page (Q2).** The epic fixes the nested reference
  pages at four. The page covers what a person launching a run needs; stage
  entry grammar stays on `customise.md`, and sub-agent grading stays in the
  skill. Rejected: a nested `autopilot-reference.md`.
- **One diagram, on the autopilot page.** A member's path through plan, gate,
  build, and pull request, with the park and blocked branches, is a lifecycle
  with branches. The other four flows are linear lists, so they get none. The
  Initiative → PRD → Epic → Change diagram stays on `prd.md`, its owner;
  `epics.md` and `initiatives.md` link to it.
- **Links (Q3).** A page links only to its four siblings and to files that
  exist on `main` at build time: `prd.md`, `prd-reference.md`, `oracle.md`,
  `customise.md`, `workspaces.md`, `supersession-gate.md`. A skill owned by
  an unwritten page (`/s:plan`, `/s:plan-deep`, `/s:build`) appears as inline
  code with no link. Rejected: links to planned file names, dead until the
  sibling merges.
- **Commands.** A page invokes a `/s:` skill or a `shipd` verb. No binary
  verb exists for drift, autopilot, or the gate, so the pages name the skill
  and no engine script path.
- **Sources.** Each page takes its facts from the skill's `SKILL.md` under
  `plugins/s/skills/`, the README skill table, and `shipd --help`. A fact
  found in none of those stays out.
- **Authoring.** Write each page through the `/s:document` flow: read
  `plugins/s/skills/document/references/standard.md` first, put the marker on
  line 1, run `docs_lint.py`, and fix findings until it exits 0.
- **Spec placement.** Each page's requirement lands in the capability of the
  skill it documents, as `oracle-user-docs` does in `shipd-ask`. `/s:explain`
  shares the epics page, so `shipd-epic` carries it.

Risk: the autopilot skill runs 697 lines and the page cap is 150. The delta
lists the required facts; anything beyond that list is cut first.

## Questions and answers

### Q1: Which doc type does a feature main page carry?
- **Question:** Which doc-type marker does a docs-by-feature main page for a
  skill carry? Options: (1) how-to, 150-line cap, for every new main page;
  (2) concept, 100-line cap, with the run steps cut short; (3) chosen per
  page by its heaviest section. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** How-to for every new main page in this group, option 1.
- **Queued:** q-docs-feature-main-page-doc-type
- **Relied on by:** docs-knowledge-group, docs-configure-group, docs-review-group, docs-workspaces-group, docs-start-here

### Q2: Does autopilot get a nested reference page?
- **Question:** Does the autopilot page stay one main page? Options: (1) one
  how-to page covering modes, launch controls, park reasons, and resume
  pointers, with stage options left on `customise.md`; (2) add a nested
  `docs/autopilot-reference.md` off the sidebar. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** One page, option 1.
- **Queued:** q-docs-autopilot-nested-reference

### Q3: May a new page link to a sibling member's unmerged page?
- **Question:** May a new page link to a page another member has not merged?
  Options: (1) link only files present on `main` at build time plus this
  member's own pages, naming other skills as inline code; (2) link the
  planned sibling file names and accept dead links until they merge.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Link only what exists, option 1.
- **Queued:** q-docs-links-to-unmerged-sibling-pages
- **Relied on by:** docs-knowledge-group, docs-configure-group, docs-review-group, docs-workspaces-group, docs-room-group

### Q4: Exact heading text on a main page
- **Question:** Eight sibling members fix the exact level-2 headings
  `## When to use it`, `## How to run it`, and `## Reference` on every main
  page. This member fixes the order only and lets the heading text vary.
  Options: (1) use the three exact headings here too; (2) keep free heading
  text in this member. Recommendation: (1).
- **Answered by:** USER
- **Answer:** Option 1. A reader finds the same three headings on every
  feature page.

## Readiness attestation

### Problem and motivation

Five skills in the Epics group have no docs page, so a reader cannot learn
them outside the README table. The epic assigns this member those pages.

Evidence:

- `.shipd/epics/docs-by-feature/epic.md:15-17` states about 17 features have
  no page; line 105 maps the Epics group to five new pages; line 152 is this
  member's row.
- `ls docs/` shows no file for epics, epic grill, autopilot, drift, or
  initiatives.

### Scope and non-goals

Five new files and nothing else. Existing pages, the README, and the
cheatsheet belong to other members.

Evidence:

- `epic.md:126-128` limits inbound link fixes to renamed or deleted files.
- `epic.md:121-124` gives the cheatsheet to `docs-start-here` and README
  cuts to `docs-readme-slim`; `epic.md:44` bars skill changes.

### Affected capabilities and files

Five capabilities gain one requirement each, and five files are created,
one per page in the group.

Evidence:

- Capabilities: `shipd-epic`, `shipd-epic-grill`, `epic-autopilot`,
  `shipd-drift`, `shipd-initiative`; none holds a `*-user-docs` id today.
- Sources: `plugins/s/skills/epic/SKILL.md:56-68,308-451`,
  `explain/SKILL.md:9-48`, `epic-grill/SKILL.md:10-286`,
  `autopilot/SKILL.md:31-140,539-697`, `drift/SKILL.md:9-151`,
  `initiative/SKILL.md:9-228`.
- Runnable premise: `plugins/s/bin/shipd --help` → exit 0; lists `epic`,
  `list`, `lint`, `board`, `workspace`, and no drift, autopilot, or
  initiative verb.
- Runnable premise: `shipd epic docs-by-feature`, `shipd lint --epic
  docs-by-feature`, `shipd board text --epic docs-by-feature`, `shipd list
  epics`, and `shipd workspace` → each exit 0 with the expected report.
- Runnable premise: `docs_lint.py docs/prd.md docs/oracle.md` → exit 0.
- `.github/workflows/ci.yml:123-130` lints every `docs/*.md` outside retros.

### No open task-shaping decision

Three decisions shaped the tasks, and each holds a planner default.

Evidence:

- File names and spec placement: settled by investigation (the epic's page
  map and the `oracle-user-docs` pattern).
- Doc type: planner default, Q1. Autopilot nesting: planner default, Q2.
  Link targets: planner default, Q3.
- Personal memory store: absent, so no preference applied.
