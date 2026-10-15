# multi-agent-pr-docs
Status: verified
Theme: developer-experience

## Idea

Add a concept page for the Multi-agent PR feature and link it from the README,
the concept overview, and the cheatsheet, so a reader finds the PR room before
they meet its verbs.

### Motivation

A reader who hears "Multi-agent PR" has no page that says what it is: the two
room docs are a how-to and a reference that only link to each other, and no
entry doc names them. The user asked for an explanation page and a path in.

### Details

- Add `docs/multi-agent-pr.md`, a `concept` doc under the 100-line cap, that
  explains the model: the room as the PR's comment thread, the A2A objects,
  the six task states, who may act when, the round cap, and the two wake
  paths.
- Retitle `docs/pr-room.md` to "Run an agent's turn in a multi-agent PR" and
  link it to the concept page and to `docs/room-wake-reference.md`.
- Link the concept page from the README's "Getting started" paragraph, from
  `docs/what-is-shipd.md` after its diagram, and from the `/s:room` row of
  `docs/cheatsheet.md`.

Affected capabilities: `shipd-room` (modified, requirement
`room-skill-docs`) and `project-readme` (modified, one added requirement).
Impact: one new file and four edited files, all under `docs/` or the README.
Nothing under `plugins/s/`, so no plugin version bump.

### Non-goals

- No rename of the verbs, the `/s:room` skill, the `room` config key, or the
  comment markers. "Multi-agent PR" is the feature name; "room" stays the
  mechanism name.
- No edit to `docs/room-wake-reference.md`, which already describes the wake.
- No new test file: a test under `plugins/s/` would trip CI's version guard
  and force a plugin bump for a docs change.
- No change to the README's opening sentence, which the in-flight change
  `audience-guides` edits.

## Implementation

- **The concept page is `concept`, capped at 100 lines, titled
  `# Multi-agent PR`.** The marker `<!-- doc-type: concept -->` sits on line
  1. The title and every link text use the feature name "Multi-agent PR";
  the first paragraph names the PR room as the mechanism. Rejected: titling
  it "Multi-agent pull requests", which gives one feature two names.
- **The page states the model from the epic's Decisions, not from the
  code.** It covers, in this order: the room is the pull request's comment
  thread; agents post an Agent Card (name, skills) and Messages that carry a
  task id and state; the six task states `submitted`, `working`,
  `input-required`, `completed`, `failed`, `canceled`; one hidden marker per
  comment with prose below, so humans read prose and verbs read JSON; room
  traffic is issue comments only, so review threads never block the merge;
  an agent acts only on an `input-required` task addressed to it, or
  unaddressed and matching a skill on its card, and never on its own last
  message; the round cap `room.max_rounds`, default 6, after which the task
  posts `failed`; the two ways a turn runs, a developer session through
  `/s:room` and the Actions wake through `shipd copilot add --room`; and the
  semantic review gate as the first member, posting each finding as a task.
  It carries one compact Mermaid state diagram of the six states, with
  emoji-free labels and no colour. Rejected: a diagram of the three layers,
  which belongs to the epic's Design and reads as architecture, not concept.
- **The page closes with a "Where next" section** linking
  `pr-room.md`, `room-wake-reference.md`, `customise.md` for the `room`
  key, and `semantic-review.md`. It names no verb flags, so it stays a
  concept doc per the standard's one-doc-one-job rule.
- **The how-to keeps its file name and marker.** The existing test lints
  `docs/pr-room.md` by path, and the `room-skill-docs` requirement names it.
  The title becomes `# Run an agent's turn in a multi-agent PR`, the first
  paragraph gains one sentence linking the concept page, and "See also"
  gains the wake reference. Rejected: renaming the file, which breaks the
  test and every inbound link for no reader benefit.
- **The README link lands in the "Getting started" paragraph**, as a third
  question-then-link sentence after the `customise.md` one, in that
  paragraph's existing pattern. Rejected: the opening sentence, which the
  in-flight `audience-guides` change edits, inviting a merge conflict; and
  the `/s:room` table row, which a newcomer never reads.
- **The concept overview gains one two-sentence paragraph** between the
  Mermaid block and "Today shipd builds itself", stating that the review
  gate also opens the pull request's room and linking the page. The file
  sits at 91 of 100 lines, so the edit adds at most three lines.
- **The cheatsheet links from the `/s:room` row's description cell.** The
  row keeps its example column. Rejected: a new intro sentence, which the
  cheatsheet's intro reserves for the two entry docs.
- **`room-skill-docs` is restated as a standing contract.** The master text
  says "the change SHALL add" and "the plugin version SHALL advance one
  patch", both one-time clauses from the shipping change. The MODIFIED body
  states what the repository ships and keeps both base scenarios by title.
  Rejected: keeping the version clause, which would read as a bump
  requirement on a docs-only change.
- **The inbound links are a new `project-readme` requirement**, since that
  capability owns the README, the overview layout, and the cheatsheet.

Risk: the overview sits three lines under its cap, so a longer paragraph
pushes it over. The task fixes the paragraph at two sentences and verifies
the line count. Risk: `audience-guides` merges first and moves README line
numbers. The README task anchors on the paragraph's text, not a line number.

## Readiness attestation

### Problem and motivation

A reader who hears "Multi-agent PR" has no page that explains it, and the
two existing docs are reachable only from each other.

Evidence:

- `docs/pr-room.md:103-106` links `customise.md` and `semantic-review.md`
  only; `docs/room-wake-reference.md` is linked from
  `docs/copilot-review-reference.md:6` alone.
- `docs/what-is-shipd.md` carries no mention of the room; `README.md:10`
  and `README.md:240-246` link only the four entry docs.
- The user's request in this conversation named the page and the three
  link sites.

### Scope and non-goals

One new concept doc, a retitle and two links in the how-to, and three
inbound links; no code, no plugin files, no version bump.

Evidence:

- In scope: `docs/multi-agent-pr.md` (new), `docs/pr-room.md:3`,
  `docs/pr-room.md:103-106`, `README.md:240-246`,
  `docs/what-is-shipd.md:80-82`, `docs/cheatsheet.md:77`.
- Out of scope: `plugins/s/`, guarded by `.github/workflows/ci.yml:23-27`
  (`version_guard.py` fails a PR that touches it without a bump);
  `docs/room-wake-reference.md`; `README.md:10`, which `audience-guides`
  edits.

### Affected capabilities and files

Two capabilities and five files: `shipd-room` owns the room docs and
`project-readme` owns the README, the overview, and the cheatsheet.

Evidence:

- Capability `shipd-room`: requirement `room-skill-docs` (base
  984ee6e6efac from `spec_status.py base-hash`).
- Capability `project-readme`: requirements `what-is-overview-layout` and
  `cheatsheet-doc` fix the two docs' shape; the new requirement adds links
  only.
- Files: `docs/multi-agent-pr.md`, `docs/pr-room.md`, `README.md`,
  `docs/what-is-shipd.md`, `docs/cheatsheet.md`.
- Runnable premise: `python3 plugins/s/skills/document/scripts/docs_lint.py`
  over `docs/pr-room.md`, `docs/what-is-shipd.md`,
  `docs/room-wake-reference.md`, `docs/cheatsheet.md`, and
  `docs/customise.md` exits 0 for each; over `README.md` it exits 1, so the
  README is not under the lint.
- Runnable premise: `wc -l` reports `docs/what-is-shipd.md` at 91 lines and
  `docs/pr-room.md` at 106 lines.
- Runnable premise: `version_guard.py --help` states it fails a pull request
  that touches `plugins/s/` without advancing the manifest's version.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Feature name "Multi-agent PR" and mechanism name "room": settled by the
  user in this conversation.
- The three inbound link sites: settled by the user; the README site within
  the file settled by investigation of `audience-guides`'s edit.
- Docs-only with no test and no bump: settled by investigation of the CI
  version guard.
- The how-to keeps its file name: settled by investigation of
  `plugins/s/skills/room/tests/test_room_skill.py:31`.
