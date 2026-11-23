# docs-by-feature
Status: draft
Theme: developer-experience

## Introduction

The shipd docs are hard to find a feature in. The site sidebar sorts by two
rules at once: "Reference" and "Concepts" group by doc type, while
"Multi-agent PRs" and "Workspaces" group by topic. A reader must guess which
rule holds a feature.

The same content also repeats. Three how-tos walk the same room flow
(`pr-room.md`, `room-run.md`, `multi-agent-autonomous-prs.md`). Two workspace
pages describe the same team layout. Review gate setup appears in the Copilot
pages, the README, and the gate skill. Meanwhile about 17 features have no
page at all: plan, build, epics, autopilot, memory and others live only in the
619-line `README.md` or the cheatsheet.

This epic regroups `docs/` by what the reader is doing, and gives every
feature one main page. Nine groups follow the delivery pipeline: Start here,
Plan, Build, Epics, Review and merge, Multi-agent PRs, Knowledge, Workspaces,
and Configure. Each member rewrites one group through `/s:document` in plain
language. The README then shrinks to install plus links.

Success criteria:

- Every `/s:` skill and every user-facing `shipd` verb has exactly one main
  page, in exactly one group.
- No fact is explained in full on two pages; one page owns it and others link.
- Every file under `docs/` (retros excepted) still passes `docs_lint.py` under
  its existing cap.
- `README.md` holds install, a short pitch, and links into `docs/`.

### Non-goals

- No change to the documentation standard, `docs_lint.py`, or the line caps.
- No new doc type. Pages stay concept, how-to, or reference.
- No redirects for retired page URLs. A retired slug returns 404.
- No website work in this epic. The sidebar regroup ships as one follow-on
  change in `shipd-now-website`, described under Design.
- No move or rewrite of `docs/retros/`, `docs/tutorials/videos/`,
  `team-merge-test.md`, `history.md`, or the two `shipd-factory` pages. They
  stay in place and stay off the sidebar.
- No change to any skill's behaviour. Members edit docs, the README, and links
  only.

## Decisions

- **Nine task groups, one main page per feature.** The groups and their pages
  are fixed by the page map under Design. A member may adjust a page title at
  planning time; it never moves a page to another group or adds a group.
- **The caps stand, so a reference page nests under its main page.** A feature
  whose detail exceeds its main page's cap keeps a separate reference file.
  The main page links it from a closing "Reference" section. The reference
  page stays off the sidebar. Rejected: a new "feature" doc type with a larger
  cap — it loosens a rule the `docs-rewrite` epic defended. Rejected: cutting
  detail until a merged page fits — flag tables and payloads would be lost.
- **A main page follows one shape.** In order: what the feature is, when to
  use it, how to run it, then a "Reference" section. That section holds a
  short table, or the link to the nested reference page.
- **One page owns each fact.** The second-account rule lives on the agent
  accounts page (`agent-identity.md`). Review gate setup lives on the review
  gate page (`copilot-review.md`). Install lives on the install page. Every
  other page states the fact in one sentence at most and links to the owner.
- **Merge only where text repeats and the result fits the cap.** The three
  room how-tos become one how-to of 150 lines or fewer. `workspaces/teams.md`
  and `workspaces/multi-workspace-repos.md` become one page.
  `nesting-and-stores.md` splits into a nesting page and an external stores
  page.
- **A surviving page keeps its file name.** A page that survives a rewrite
  keeps its path, even when its title changes. Code depends on some paths:
  `test_config_sample.py` guards `docs/customise.md`, and the doctor skill
  cites `docs/copilot-review.md`. A page that is merged away is deleted, and
  no redirect replaces it.
- **Every page is written through `/s:document`.** The skill applies the
  standard paragraph by paragraph: plain words, active voice, the sentence
  and paragraph caps. No member hand-writes docs prose outside it, and each
  member ends with `docs_lint.py` clean on every file it touched.
- **Diagrams are a judgement call inside the standard.** A member adds a
  mermaid diagram where it carries structure prose cannot, at most one per
  page. A member reviews every diagram it inherits against the rewritten
  text: it keeps the diagram when it still matches what the page explains,
  fixes it when it has drifted, and deletes it when it only restates a list.
- **New pages take their content from the shipped source.** A new feature
  page draws on the skill's `SKILL.md`, the README's skill table, and
  `shipd <verb> --help`. A member never documents behaviour it has not
  confirmed in one of those.
- **The cheatsheet is the only cross-feature list.** It sits last in Start
  here. No other page carries a table of all skills or all verbs.
- **The docs own the skill descriptions; the README links.** The README's
  skill tables, spec engine, CLI, statusline, telemetry and CI sections move
  into `docs/` pages. The README keeps one line per group with a link.

## Design

### The page map

Bold names are new pages. Plain names are existing files that stay.

| Group | Main pages |
| --- | --- |
| Start here | `what-is-shipd.md`, **install**, `getting-started.md` (titled "Your first change"), **core ideas**, `cheatsheet.md` |
| Plan | `prd.md`, **research**, **video ingest**, **rubber duck**, **plan a change** (`/s:plan`, `/s:plan-deep`, the spec lifecycle) |
| Build | **build a change**, **fix a bug**, **worktrees and hooks**, `guardrails.md`, `supersession-gate.md`, **drive a browser and record a demo** |
| Epics | **epics** (`/s:epic`, `/s:explain`), **epic grill**, **autopilot**, **drift**, **initiatives** |
| Review and merge | `semantic-review.md`, `copilot-review.md` (titled "Review gate"), **pull requests** |
| Multi-agent PRs | `multi-agent-pr.md`, one merged run how-to, `agent-identity.md`, `room-wake-reference.md`, `room-review-claims.md` |
| Knowledge | `oracle.md`, **the wiki** (`/s:teach`), **personal memory** |
| Workspaces | `workspaces.md`, `workspaces/getting-started.md`, one merged team page, `workspaces/member-map.md`, **nesting**, **external stores**, `workspaces/headless.md` |
| Configure | `customise.md`, **harnesses**, **statusline and telemetry**, **doctor** |

Nested reference pages, off the sidebar: `prd-reference.md`,
`semantic-review-reference.md`, `copilot-review-reference.md`, and
`harness-agents-reference.md`.

### The seams

Each group is one member. A group's pages link mostly to each other, so the
eight feature groups can land in any order. Two members run last:

- `docs-start-here` writes the core ideas page and refreshes the cheatsheet.
  Both link to feature pages, so it runs after the feature groups.
- `docs-readme-slim` deletes README sections only once a docs page owns each
  one, so it runs after every other member.

Each member also fixes inbound links to the files it renames or deletes:
cross-doc links, `README.md`, `AGENTS.md`, skill files, and tests. The
existing CI docs-lint step already covers every new page.

### The website follow-on

The sidebar lives in `shipd-now-website/content/docs.manifest.json`, in
another repository. Its docs sync adopts each new upstream page as hidden and
prunes each deleted one, so the site keeps building while this epic runs.
After the last member merges, one change in `shipd-now-website` finishes the
job:

- Set the nine sections and their page order, with a description per page.
- Keep the four nested reference pages routable but off the sidebar. A
  `hidden` page has no route today, so this needs a new manifest flag.
- Set `hidden: true` on `shipd-factory`, taking it fully off the site.
- Remove the duplicate `semantic-review-reference` entry.
- Link `history.md` from an About link instead of the sidebar.
- Update the `docs-corpus` spec scenario that lists the sections.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| docs-plan-group | Write the research, video ingest, rubber duck, and plan-a-change pages; reshape `prd.md` and remove its overlap with `prd-reference.md` | medium | low | low | low | |
| docs-build-group | Write the build, fix, worktrees-and-hooks, and drive-and-demo pages; reshape `guardrails.md` and `supersession-gate.md` | medium | low | low | low | |
| docs-epics-group | Write the epics, epic grill, autopilot, drift, and initiatives pages | medium | low | low | low | |
| docs-review-group | Reshape the semantic review and review gate pages with nested references, move the README "CI" setup onto the review gate page, and write the pull requests page | medium | medium | low | medium | |
| docs-room-group | Merge the three room how-tos into one, make `agent-identity.md` the owner of the second-account rule, and reshape the room concept, wake, and claims pages | medium | medium | medium | medium | |
| docs-knowledge-group | Reshape `oracle.md`; write the wiki and personal memory pages | low | low | low | low | |
| docs-workspaces-group | Merge the team and multi-workspace-repos pages, split `nesting-and-stores.md` in two, and reshape the remaining workspace pages | medium | medium | low | medium | |
| docs-configure-group | Reshape `customise.md`; write the harnesses, statusline-and-telemetry, and doctor pages, nesting `harness-agents-reference.md` | medium | medium | low | low | |
| docs-start-here | Write the install and core ideas pages, retitle `getting-started.md`, refresh `cheatsheet.md` and the `what-is-shipd.md` diagram against the new pages | medium | medium | low | low | docs-plan-group, docs-build-group, docs-epics-group, docs-review-group, docs-room-group, docs-knowledge-group, docs-workspaces-group, docs-configure-group |
| docs-readme-slim | Cut `README.md` to install, pitch, and one link per group; fix every remaining inbound link | low | medium | low | medium | docs-start-here |
