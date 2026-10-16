# video-series-reorder
Status: verified

## Idea

Split the video series' first episode in two, install-then-build and plan-and-specs, and renumber the series to ten episodes.

### Motivation

A viewer who starts the series meets `/s:plan` and its artifacts before seeing shipd install or ship anything. No episode shows the install at all, so a new viewer cannot follow along from an empty machine.

### Details

- New `01-install-and-build.md`: install shipd, run `shipd doctor`, run `shipd init` in the kanban demo, then ship a change with one `/s:build` request and watch it.
- New `02-plan-and-specs.md`: plan a change with `/s:plan`, read `plan.md`, the delta spec, and `tasks.md`, then build the planned change.
- Delete `01-core-loop.md`; its plan and artifact beats move into episode 2.
- Rename the current episodes 2–9 to 3–10, keeping each slug, and renumber their headings, prerequisites, and `## Next` links.
- Update `index.md` and `template.md` for ten episodes.

Affected capabilities: `video-tutorials` (modified). Impact: files under `docs/tutorials/videos/` only; no code, no engine, no dependency.

### Non-goals

- No change to the content of the renumbered episodes beyond their numbers and links.
- No website edit, and no recording of the videos.
- No change to the `episode-1-kanban-script` worktree; the user removes it.

## Implementation

- **File names.** The new files are `01-install-and-build.md` and `02-plan-and-specs.md`. The renamed files keep their slugs: `03-worktrees-and-small-prs.md`, `04-prds-and-guardrails.md`, `05-epics-and-epic-grill.md`, `06-oracle-and-supersession-gate.md`, `07-workspaces-101.md`, `08-advanced-workspaces.md`, `09-ci-and-copilot-review.md`, `10-management-plane.md`. Use `git mv` so history follows each file.
- **Renumber rule.** In every renamed episode, a reference to old episode `n` (for `n` of 2 or more) becomes episode `n+1`, and its link points at the renamed file. A reference to old episode 1, the plan-then-build loop, becomes episode 2. A range or pair that starts at old episode 1 means every earlier episode, so it starts at episode 1: "episodes 1 to 8" becomes "episodes 1 to 9", "episodes 1 to 5" becomes "episodes 1 to 6", and "episodes 1 and 2" becomes "episodes 1 to 3".
- **Episode 1 beats.** 0:00–0:45 what shipd is, over the [What is shipd?] page; 0:45–1:45 `curl -fsSL https://shipd.now/install | sh`, the PATH line, and `shipd doctor`; 1:45–2:15 `shipd init` in the kanban demo; 2:15–4:15 `/s:build Add a remove command to kanban.py that deletes a card from any column`, where build finds no planned change, runs the planning flow itself, delegates, and verifies; 4:15–5:00 `shipd status`, `shipd list`, `shipd board`. Commands shown: `curl … | sh`, `shipd doctor`, `shipd init`, `/s:build`, `shipd status`, `shipd list`, `shipd board`.
- **The kanban demo.** The demo is a git repository holding the onboard tour's one-file board, since `/s:build` creates a worktree; `plugins/s/skills/onboard/assets/solutions/add-board/kanban.py`. Before the build, `python3 kanban.py remove "Draft the board layout"` fails with `usage: kanban.py {list|board}`. After it, the same command deletes the card and `python3 kanban.py list` shows it gone. Use a card that exists in its `cards.json`.
- **Episode 2 beats.** 0:00–0:45 why plan before you build; 0:45–1:45 `/s:plan Add a move command to kanban.py that moves a card to another column` on the kanban demo, where the Planner investigates first, asks only what it cannot infer, creates the worktree, and stops; 1:45–3:15 read `plan.md` (Idea with Motivation, Details, Non-goals; Implementation), the delta spec (requirements with WHEN/THEN scenarios), and `tasks.md`; 3:15–4:15 the context gate promotes the plan to `ready`; 4:15–5:00 `/s:build <change>` builds it and verifies against the scenarios. Commands shown: `/s:plan`, `/s:build`.
- **Sources.** Episode 1: `docs/getting-started.md`, `docs/what-is-shipd.md`, `docs/cheatsheet.md`, and the onboard kanban asset. Episode 2: `docs/getting-started.md`, `docs/what-is-shipd.md`, `.shipd/README.md`. Read each source before writing the beat that relies on it.
- **Index groups.** Tactical execution holds episodes 1–3, Spec authoring and pressure testing holds 4–5, and Verification and governance holds 6–10. Episodes 1–9 cover open-source shipd and episode 10 the commercial management plane, in `index.md` and in `10-management-plane.md`'s own text.
- **Template.** `template.md` step 7 names episode 10 as the episode that links `index.md`.
- **Authoring.** Write and revise every file with `/s:document` and run `docs_lint.py` until it exits 0.

Risk: a stale episode number or link survives the renumber. Guard: a final task greps the directory for every old file name and for "Episode 9" outside `09-ci-and-copilot-review.md`.

## Questions and answers

### Q1: How many episodes after the reorder?
- **Question:** New episode 1 is install then `/s:build`; new episode 2 is `/s:plan` and its specs; together they replace the current episode 1. Options: (a) ten episodes, with the current 2–9 moving unchanged to 3–10; (b) nine, folding worktrees and small PRs into the new episode 2. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a), ten episodes.
- **Queued:** q-video-series-episode-count-after-reorder

## Readiness attestation

### Problem and motivation

The series opens with planning before a viewer has installed shipd or seen it ship a change.

Evidence:

- `docs/tutorials/videos/01-core-loop.md` lists install only as a prerequisite and opens its first command beat on `/s:plan`.
- `docs/getting-started.md` documents the install step that no episode shows.

### Scope and non-goals

Episode files, the overview, the template, and one capability; content of the renumbered episodes, the website, and recordings stay out.

Evidence:

- Capability `video-tutorials` fixes the count and file names in `video-episode-scripts` and `video-series-overview`.
- No file under `shipd-now-website` references `tutorials/videos`, so the renames break no website link.

### Affected capabilities and files

One capability, three modified requirements, and the files under `docs/tutorials/videos/`.

Evidence:

- `video-tutorials`: `video-episode-scripts`, `video-scripts-grounded` (its scenario names episode 4), `video-series-overview`.
- Files: `docs/tutorials/videos/01-core-loop.md` (deleted), `02-` to `09-` (renamed), `index.md:43`, `template.md:30`, `08-ci-and-copilot-review.md:58`, `09-management-plane.md:3`.
- Runnable premise: `python3 kanban.py remove "Write episode 1"` in the onboard `add-board` asset exited 2 with `usage: kanban.py {list|board}`; `python3 kanban.py list` exited 0 and listed three cards, none named "Write episode 1".
- Documented behavior: `/s:build` with a prose request and no planned change runs the planning flow itself (`plugins/s/skills/build/SKILL.md`, Phase 0 step 3; `docs/cheatsheet.md:58`, "Plan, delegate … end to end").

### No open task-shaping decision

Every decision is settled; none remain.

Evidence:

- Episode count: the user, Q1.
- File names, renumber rule, beats, demo card, and sources: investigation of the template, the spec, `docs/getting-started.md`, and the kanban asset.
