# docs-workspaces-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: bb85fbf5a54e

## Idea

Regroup the Workspaces docs into one index and six part pages: merge the two
team pages, split `nesting-and-stores.md` in two, and give every page the
main-page shape.

### Motivation

A reader setting up a team workspace meets the same layout on two pages, and
a reader who wants nesting must read past the external store to find it. The
`docs-by-feature` epic assigns this member the Workspaces group.

### Details

| file | title | type | cap |
| --- | --- | --- | --- |
| `docs/workspaces.md` | Workspaces | concept | 100 |
| `docs/workspaces/getting-started.md` | Getting started | how-to | 150 |
| `docs/workspaces/teams.md` (merged) | Sharing a workspace with a team | reference | 250 |
| `docs/workspaces/member-map.md` | The member map and workspace discovery | reference | 250 |
| `docs/workspaces/nesting.md` (new) | Nesting job workspaces | how-to | 150 |
| `docs/workspaces/external-stores.md` (new) | External stores | reference | 250 |
| `docs/workspaces/headless.md` | Headless consumers | how-to | 150 |

Deleted: `docs/workspaces/multi-workspace-repos.md` and
`docs/workspaces/nesting-and-stores.md`.

Affected capabilities: `shipd-workspace` (four modified requirements),
`epic-autopilot` and `shipd-config` (one modified each, a path rename only).
Impact: nine files under `docs/`, one test file, and the plugin version.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/tutorials/videos/`, or another
  group's page. No file there links a deleted page.
- No change to a skill, the engine, the standard, or the caps.
- No new nested reference page and no mermaid diagram.
- No website sidebar work.

## Implementation

**Every page goes through `/s:document`** (epic Decision). Read
`plugins/s/skills/document/references/standard.md` first, keep the marker on
line 1, and run `python3 plugins/s/skills/document/scripts/docs_lint.py
<file>` until it exits 0.

**Main-page shape (binding, all seven pages).** After the title, and the
back link on a part page, the opening says what the page covers. Then come
`## When to use it`, `## How to run it`, and a closing `## Reference`, with
those exact headings, as `docs-plan-group` fixed them. They are the page's
only level-2 headings. Today's sections become level-3 sections under them;
`tasks.md` gives each page's outline.

**Content moves; it is not re-derived.** Keep each fact's wording unless a
task says otherwise. Only the `## When to use it` sections are new prose.

**File names.** `teams.md` survives the merge, so it keeps its path (epic
Decision); two tutorial pages link it. The two split pages take the page-map
names, `nesting.md` and `external-stores.md`, beside the other part pages.

**Doc types.** `nesting.md` is how-to, the default the Epics group set for a
new main page (its Q1). `teams.md` and `external-stores.md` are `reference`
(Q1): the merged team page needs about 225 lines and the stores page about
175, and the epic rejects cutting detail to fit. Rejected: a nested reference
page, which the epic's list of four does not name.

**The index is the main page for `/s:workspace` and `shipd workspace` (Q2).**
Its `## Reference` holds two tables: the six parts (link, one sentence, one
example command), and the verbs.

**Fact owners (binding).** A non-owner gives one sentence and a link.

| fact | owner |
| --- | --- |
| The concept, the layout tree, the verb table | `workspaces.md` |
| Machine setup, create, check in, load, the sync ladder, the consent round | `getting-started.md` |
| Shared surfaces, the team layout, isolation, the hooks consent gate, concurrency, the `shipd board` folder rule | `teams.md` |
| The machine-local file, the map and sources verbs, discovery | `member-map.md` |
| `--nested`, what inherits, what stays nearest-only, `wiki_base` beside nesting | `nesting.md` |
| `store_root` behaviour, folder naming, store commits, the `After` rule, limits | `external-stores.md` |
| The headless footprint and its guarantees | `headless.md` |
| Config key rows | `customise.md` |

So `teams.md` states the read-through and write-nearest split once and links
`nesting.md`. Each layout fact from the two merged pages appears once.

**Room under the caps.** `getting-started.md` and `member-map.md` sit at
their caps and gain headings. First rewrap prose paragraphs to 100 columns,
rewording nothing. `getting-started.md` also shrinks its `/s:ask` and
`/s:teach` bullets to one line each. Never drop a fact the delta lists.

**Links.** Link only files on `main` plus this change's pages, the default
the Epics group set (its Q3). `/s:teach` and `/s:ask` appear as inline code.

**The test.** `test_workspace_team.py` reads both team pages by name. It
changes with the merge, so the plugin version bumps (`AGENTS.md`).

**Diagrams.** The text layout trees stay, one per page. No mermaid.

Risk: `teams.md` merges 250 lines into a 250-line cap. Guard: the cap is a
task exit condition, and the duplicated layout prose goes first.

## Questions and answers

### Q1: Marker for a page over the how-to cap
- **Question:** Which doc-type marker does a Workspaces main page carry when
  its content exceeds the 150-line how-to cap (the merged `teams.md` and the
  new `external-stores.md`)? Options: (1) `reference`, 250 lines, reordered
  into the main-page shape; (2) how-to, with detail cut or moved; (3) a
  how-to main page plus a new nested reference page. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. `customise.md`, `oracle.md`, and `guardrails.md` keep
  `reference` in the same shape, and no detail is lost.
- **Queued:** q-docs-workspaces-over-cap-page-type

### Q2: Main page for the workspace skill and verb
- **Question:** Which page is the main page for `/s:workspace` and the
  `shipd workspace` verb? Options: (1) `docs/workspaces.md`, the group index,
  with a verb table in its Reference section; (2)
  `docs/workspaces/getting-started.md`; (3) no single page, each part page
  owning its own sub-verb. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The index has room under its cap, and
  `getting-started.md` sits at its cap.
- **Queued:** q-docs-workspaces-skill-main-page
- **Relied on by:** docs-start-here

## Readiness attestation

### Problem and motivation

Two pages describe the same team layout, and one page mixes nesting with the
external store.

Evidence:

- Epic `docs-by-feature`, Decision "Merge only where text repeats" and
  Changes row `docs-workspaces-group`.
- `docs/workspaces/teams.md:102-150` and
  `docs/workspaces/multi-workspace-repos.md:1-100` both give the wizard, the
  `shipd board` rule, and the isolation boundary.

### Scope and non-goals

Nine docs files, one test file, and the plugin version are in scope. The
README, the tutorials, and other groups' pages are out.

Evidence:

- Epic Design "The seams": each member fixes inbound links to the files it
  deletes; `docs-readme-slim` owns the README.
- `git grep` for the two deleted names: outside archives, hits are only the
  group's own pages, three verified specs, and `test_workspace_team.py`.

### Affected capabilities and files

Three capabilities and eleven files are affected.

Evidence:

- `shipd-workspace`: `workspaces-doc` (base f3dbc7f271b3),
  `workspaces-doc-examples` (002a90b9f5da), `workspaces-doc-store-sync`
  (7cac6b88ba2c), `workspace-universe-discovery` (f16e9f238c90).
- `epic-autopilot` `merged-dependency-check` (82640e6cf564) and
  `shipd-config` `store-repo-folder-name` (0eafddeb07b4). Hashes from
  `spec_status.py base-hash`.
- Files: `docs/workspaces.md:1-91`, the six files under `docs/workspaces/`,
  two new files, `plugins/s/skills/build/tests/test_workspace_team.py:514-555`,
  `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `docs_lint.py docs/workspaces.md docs/workspaces/*.md` →
  exit 0.
- Runnable premise: `python3 -B -m unittest
  plugins/s/skills/build/tests/test_workspace_team.py` → 35 tests, OK.
- Runnable premise: `plugins/s/bin/shipd --help` lists
  `workspace [init|sync|team]`; `shipd workspace init --help` lists `--git`
  and `--nested`.
- Runnable premise: `version_guard.py --help` lists no `--advance`.

### No open task-shaping decision

Every task-shaping decision is settled; two rest on planner defaults here and
two on defaults an earlier member set.

Evidence:

- The marker for the two long pages and the owner of the workspace verbs:
  planner defaults, Q1 and Q2.
- The how-to marker for `nesting.md` and the link targets: the Epics group's
  planner defaults, its Q1 and Q3.
- File names and the heading set: investigation, from the epic's page map and
  the `docs-plan-group` plan.
