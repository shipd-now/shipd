# docs-build-group
Status: verified
Epic: docs-by-feature
Theme: developer-experience
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 99eed1c9f82c

## Idea

Write the four missing Build-group pages and reshape `docs/guardrails.md` and
`docs/supersession-gate.md` into the epic's main-page shape.

### Motivation

A reader who wants to build a change, fix a bug, manage worktrees, or drive a
browser finds no docs page; those features live only in `README.md` and the
cheatsheet. The `docs-by-feature` epic gives every feature one main page, and
assigns this member the Build group.

### Details

| file | title | type | cap |
| --- | --- | --- | --- |
| `docs/build.md` (new) | Build a change | how-to | 150 |
| `docs/fix.md` (new) | Fix a bug | how-to | 150 |
| `docs/worktrees.md` (new) | Worktrees and hooks | how-to | 150 |
| `docs/drive-and-demo.md` (new) | Drive a browser and record a demo | how-to | 150 |
| `docs/guardrails.md` | Guardrails | reference | 250 |
| `docs/supersession-gate.md` | The supersession gate | concept | 100 |

Affected capabilities: `build-spec-lifecycle`, `shipd-fix`, `worktree-hooks`,
`shipd-drive` (one added docs requirement each); `shipd-config`,
`build-context-gate` (one modified docs requirement each). Impact: six files
under `docs/`; no plugin, engine, or CI change, so no version bump.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/cheatsheet.md`, or any other
  group's page. `docs-readme-slim` and `docs-start-here` own those.
- No page for `/s:status`, `shipd lint`, `shipd metrics`, or build telemetry;
  the Plan and Configure groups own them.
- No change to the standard, `docs_lint.py`, the caps, or any skill.
- No nested reference page; the epic's nested list names none for this group.

## Implementation

**Every page goes through `/s:document`.** Read
`plugins/s/skills/document/references/standard.md` first. Put the marker on
line 1. Run `python3 plugins/s/skills/document/scripts/docs_lint.py <file>`
and fix findings until it exits 0.

**Main-page shape (binding, all six pages).** The intro under the title says
what the feature is. Then come the exact level-2 headings `## When to use it`,
`## How to run it`, and `## Reference`, in that order, as `docs-plan-group`
fixed them (Q6). Reference holds short tables and links. No page keeps a
`## See also` section.

**Sources (binding).** State only behaviour confirmed in the named source.

- `build.md`: `plugins/s/skills/build/SKILL.md`. Cover the orchestrator and
  its sub-agents one model tier below; the run steps (context gate, execute,
  verify with the validator, merge and archive, ship); the two PR modes
  (`auto` default, `pr-mode: draft`); and `shipd board` for watching
  progress. One mermaid flowchart carries the branched lifecycle
  (clean / drift / superseded, auto / draft).
- `fix.md`: `plugins/s/skills/fix/SKILL.md`. Cover retrieve-before-diving
  with the `related` verb, reproduce first, the two branches (code wrong:
  fix plus regression test; spec wrong: stop and hand off to `/s:plan`), and
  the report. State that it never edits a spec and never ships. No diagram.
- `worktrees.md`: `shipd worktree --help` and
  `plugins/s/skills/worktree-hooks/SKILL.md`. Cover one change, one
  worktree, one branch; create with `--fresh`; `remove`, `prune-branches`,
  `sweep`; `hooks list|add|remove|run|trust`; exit 3 on a failing hook; and
  `/s:worktree-hooks`. Reference is a verb table. No diagram.
- `drive-and-demo.md`: `plugins/s/skills/drive/SKILL.md`,
  `plugins/s/skills/demo/SKILL.md`, `drive.py --help`. Cover targets,
  `doctor`, login with `--manual`, probe before selectors, named waits, the
  `PASS`/`FAIL` verdict, `handoff`/`resume`; then demo's browser or terminal
  medium, `record` or `tape`, and `post`. Reference is a `drive.py` verb
  table. No diagram.
- `guardrails.md`: content moves, it is not re-derived. `## When to use it` takes
  the deny-for-certain / remind-for-fuzzy guidance. `## How to run it` takes add,
  edit, and override as steps. Reference takes hook events, rule format,
  sources, cooldown, kill-switches, and token cost as level-3 sections.
- `supersession-gate.md`: `## When to use it` takes Phase 0 and the three
  outcomes. `## How to run it` keeps the invocation. Reference takes
  the findings table and exit codes. Add a link to `build.md`.

**One owner per fact.** Config keys belong to `customise.md`, review gate
setup to `copilot-review.md`, install to the install page. These pages give
one sentence and a link.

**Links.** Link only to files present under `docs/` on the branch (Q5). The
four new pages link each other where related; `build.md` links
`supersession-gate.md`, `guardrails.md`, and `worktrees.md`.

Risk: `guardrails.md` sits at 220 lines and gains two headings. Guard: the
250 cap is a task exit condition; compress prose, never drop a pinned fact.

## Questions and answers

### Q1: File names of the four new pages
- **Question:** Which file names do the new pages take? Options: (1)
  `build.md`, `fix.md`, `worktrees.md`, `drive-and-demo.md`; (2) names that
  mirror the titles, such as `build-a-change.md`; (3) a `docs/build/`
  subfolder. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Short flat names match the existing `docs/` files.
- **Queued:** q-docs-build-page-filenames
- **Relied on by:** docs-review-group, docs-start-here, docs-readme-slim

### Q2: Shape of the guardrails page
- **Question:** Does `guardrails.md` stay one page or split? Options: (1) one
  reference page, reordered into the main-page shape; (2) a how-to main page
  plus a new nested `guardrails-reference.md`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic's nested reference list names no guardrails
  page, and the content fits the reference cap.
- **Queued:** q-docs-build-guardrails-shape

### Q3: Main page for `shipd board`
- **Question:** Which page owns the `shipd board` verb? Options: (1) the
  build page, in a short watch-progress step; (2) the autopilot page; (3)
  `getting-started.md` keeps it. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The board shows a build's progress first.
- **Queued:** q-docs-build-board-owner
- **Relied on by:** docs-start-here

### Q4: Doc type of the new pages
- **Question:** Which doc type do the four new pages carry? Options: (1)
  how-to for all four; (2) concept for all four; (3) how-to for three and
  reference for worktrees. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The main-page shape centres on how to run the
  feature, and the how-to cap of 150 lines fits each page.
- **Queued:** q-docs-build-page-doc-type
- **Relied on by:** docs-review-group

### Q5: Links to pages another member has not written
- **Question:** Who adds a link to a page that does not exist yet? Options:
  (1) link only to files on the branch; a later member adds the rest; (2)
  link the future path now; (3) add an After dependency. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It keeps every merged link resolving while the
  feature groups land in any order.
- **Queued:** q-docs-cross-group-links
- **Relied on by:** docs-review-group, docs-room-group

### Q6: Exact heading text on a main page
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

Build, fix, worktrees, and drive and demo have no docs page; the epic assigns
this member the Build group.

Evidence:

- `.shipd/epics/docs-by-feature/epic.md:104` lists the Build group's pages;
  line 151 is this member's row.
- `README.md:266-273` holds the only prose on `/s:build`, `/s:fix`,
  `/s:drive`, and `/s:worktree-hooks`.

### Scope and non-goals

Six files under `docs/` are in scope. The README, the cheatsheet, and other
groups' pages are out.

Evidence:

- `.shipd/epics/docs-by-feature/epic.md:121-124` gives the cheatsheet and
  README to `docs-start-here` and `docs-readme-slim`.
- `.shipd/epics/docs-by-feature/epic.md:112-114` fixes the nested reference
  list.

### Affected capabilities and files

Six capabilities and six files are affected: four added docs requirements,
two modified ones.

Evidence:

- Added: `build-spec-lifecycle`, `shipd-fix`, `worktree-hooks`, `shipd-drive`.
- Modified: `shipd-config` `guardrails-key-docs` (base 7704309d4a44) and
  `build-context-gate` `supersession-gate-doc` (base 273eecfa0d0f), hashes
  from `spec_status.py base-hash`.
- Files: `docs/guardrails.md:1-220`, `docs/supersession-gate.md:1-61`, and
  four new files under `docs/`.
- Runnable premise: `plugins/s/bin/shipd worktree --help` → exit 0, printed
  the create, `remove`, `prune-branches`, `sweep`, and five `hooks` verbs.
- Runnable premise: `python3 plugins/s/skills/drive/scripts/drive.py --help`
  → exit 0, listed twenty verbs including `record`, `tape`, and `post`.
- Runnable premise: `plugins/s/bin/shipd board text` → printed the board.
- Runnable premise: `spec_status.py check-base --help` → exit 0, one
  optional `change` argument.
- Runnable premise: `docs_lint.py docs/guardrails.md
  docs/supersession-gate.md` → exit 0.

### No open task-shaping decision

Five decisions existed; each carries a planner default.

Evidence:

- File names, guardrails shape, board owner, doc type, and cross-group
  links: planner defaults, Q1 to Q5.
- Capability homes for the new requirements: investigation, following
  `.shipd/completed/2026-09-11-docs-feature-guides/`.
