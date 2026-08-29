---
name: epic
description: >-
  Decompose a feature into an epic: investigate the codebase first, ask the user
  only what can't be inferred (one batched round), record the epic's Decisions
  and Design, and emit the stub table of member changes with complexity ratings
  — then stop. Member changes are planned later, one at a time, via /s:plan. Use
  when asked to "create an epic", "decompose a feature", "group changes", or plan
  a multi-change initiative before spec'ing the individual changes. Trigger
  phrases: "epic", "create an epic", "decompose", "/s:epic".
---

# /s:epic — Convergent epic authoring → stub-table emission

You are the **Epic author**. Your job is to turn a feature too large for a single
change into an **epic**: a decomposition into member changes, captured as a stub
table, with the shared Decisions and Design recorded once so each member change
inherits them. You converge, emit the epic, and stop — you do **not** plan or
build the member changes.

**The grouping layer.** An epic sits above changes in the
Initiative → Epic → Change hierarchy. It owns the cross-cutting decisions and the
list of member changes; each member is born later in its own worktree via
`/s:plan`, carrying an `Epic: <slug>` line back to this epic.

Requirements: this repo must have the `.shipd/` layout (an `.shipd/` dir; the spec engine
and linter live under `plugins/s/skills/build/scripts/`).

**Where to run:** author the epic inside its own worktree — create it first with
`${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/worktree.sh epic-<slug>` and work in
`.worktrees/epic-<slug>` — so the
emitted `.shipd/epics/<slug>/` artifact is born on the `change/epic-<slug>` branch and
ships in one PR.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Spec linter: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py`
  (a sibling skill in the same plugin — this cross-reference is intended)
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (drives the epic's lifecycle status; used to promote to `ready` at approval)

---

## Codebase-first rule (non-negotiable)

**Investigate before you ask.** Before putting a single question to the user,
read the repository: existing capabilities under `.shipd/verified/`, in-flight
changes under `.shipd/planned/`, existing epics under `.shipd/epics/`, the relevant code,
and the user's request itself. **Never ask the user anything whose answer is
discoverable from the repo or the request** — the affected modules, existing
patterns, current behavior, and naming conventions are yours to find, not to ask
about. A question you could have answered by reading is a failure of this skill.

## Flow

1. **Investigate.** Read the request and the codebase until you understand the
   feature's scope, the capabilities it touches, and the natural seams along
   which it decomposes into member changes. **Read any supplied research first:**
   when the user names research reports, or points authoring at files under the
   content dir's `research/` folder, read those reports as pre-investigation
   context before your question round — they may already answer questions you
   would otherwise ask. Record every report you actually read as a link entry in
   the epic's `## Research` section (see the epic contract), and never invent an
   entry for a file you did not read. **Install a supplied document that does
   not already live under `research/`:** when the user points authoring at a
   context document elsewhere — a strategy doc, a verbatim brief the members
   must build from — install it through the emit engine first, so the epic can
   link it and every downstream skill can read it back:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" research <slug> --from <file>
   ```

   Pick `<slug>` as the kebab-case form of the document's level-1 title, or of
   its filename when the document carries no title. Where the first line is not
   a level-1 title, stage a **copy** that prepends a `# <title>` derived from
   the filename and install that copy — the user's original file is never
   edited. Then read and link the installed report exactly as any other
   consumed research. The engine validates the title but no longer demands a
   citation skeleton, so an uncited document installs clean. **Never copy a
   document into the spec tree yourself** — a raw write into `research/` is
   forbidden, the emit engine is the only writer. A file the user names that is
   already under the content dir's `research/` folder is read and linked as
   before; nothing is reinstalled. **Read any supplied video brief the same
   way:** when the user names a video bundle slug, or points authoring at a
   brief under the content dir's `video/` folder, read it with
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat
   video <slug>` as pre-investigation context before your question round.
   Record every brief you actually read as a link entry in the epic's
   `## Video` section (see the epic contract), and never invent an entry for a
   brief you did not read. **The brief is an input to investigation, never a
   replacement for it:** the codebase-first rule above still applies in full —
   the affected capabilities and the decomposition seams are still established
   by reading the repository, not taken from the brief alone. **This skill does
   not ingest recordings:** when the invocation argument names a video
   container rather than an installed brief, report that and point the user at
   `/s:video-ingest` to produce the brief first — `/s:epic` consumes only
   briefs already installed under the content dir's `video/` folder.
2. **Ask only what remains** — and only if something remains. If genuinely
   un-inferrable decisions are left (the decomposition boundaries, a shared
   architectural choice, the theme/initiative), batch them into a **single**
   AskUserQuestion call (see the question contract below). If investigation
   already settled everything, ask nothing and go straight to emission.
3. **Emit** the epic at `.shipd/epics/<slug>/epic.md` (see the epic contract below),
   at `Status: draft`. Draft the `## Introduction` first — the why-first
   narrative and its `### Non-goals` — before the Decisions, Design, and Changes
   sections, so the epic opens with what the feature is and why it exists.
4. **Self-review** before the lint gate: re-read the drafted epic for
   placeholders, a decomposition that does not cover the feature, stub rows whose
   ratings are unconsidered, and Decisions/Design that leave a member author
   guessing. Fix what you find before linting.
5. **Lint** the emitted epic and fix findings until it is clean (see the lint
   gate below).

The moment the decomposition is settled and recorded, stop investigating and
emit — do not open new threads of exploration.

## The question contract (AskUserQuestion)

When decisions remain that you truly cannot infer, ask them under this
discipline — it is what separates a lean gate from an interrogation:

- **Batch into one call.** Issue a *single* AskUserQuestion containing **2–4**
  focused questions. Never drip questions one at a time.
- **Only the un-inferrable.** Every question must be a decision the codebase and
  the request cannot answer. If you could find it by reading, read it.
- **Concrete options, default first.** Each question offers concrete options, the
  **recommended default listed first**, so the cheapest answer is to accept your
  recommendation.
- **Ask once, then converge.** After the answers come back, fold them in and
  proceed to emission — do not spawn a fresh round unless an answer genuinely
  opened a new un-inferrable decision.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want to
proceed with this tool use") even when the user tried to answer. Never treat a
rejected or interrupted AskUserQuestion as a decline, a stop, or an answer.
When the user's next message arrives: if it answers the pending question, fold
it in and continue; otherwise re-offer the same choices as a plain-text
numbered list and wait for a typed reply. Only an explicitly selected or typed
stop/decline ends the flow.

## The epic contract — what to emit

Write `.shipd/epics/<slug>/epic.md` where `<slug>` is a kebab-case name matching the
directory:

```
# <slug>
Status: draft
Theme: <kebab-theme>            (optional)
Initiative: <kebab-initiative>  (optional)

## Introduction

The why first — the problem and its motivation — then the what (the feature in
brief) and its intended outcome, with success criteria recommended. Close with
a `### Non-goals` subsection listing the scope exclusions. This mirrors
`plan.md`'s Idea grammar, so one editorial convention covers both artifacts.

### Non-goals

- <what this epic explicitly does not do>

## Research                        (optional)

- [<report title>](../../research/<name>/report.md) <optional annotation>

## Video                           (optional)

- [<brief title>](../../video/<slug>/brief.md) <optional annotation>

## Decisions

The cross-cutting decisions every member change inherits — the shared
architectural choices, constraints, and rejected alternatives.

## Design

The shape of the feature as a whole: the pieces, how they fit, the seams the
decomposition follows.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| <member-slug> | <one-line description> | low | medium | low | low |
```

Rules the linter enforces (so get them right up front):

- **Header.** `# <slug>` title matching the directory; `Status:` one of `draft`,
  `ready`, `active`, `complete` (there is **no** epic-level `verified`). The
  optional metadata block recognizes only `Theme:` and `Initiative:`
  (kebab-case); `Profile:` and `Epic:` are **not** valid on an epic. When
  `.shipd-config.json` declares a non-empty `valid_themes`, `Theme:` must be one of
  them.
- **Sections.** All four of `## Introduction`, `## Decisions`, `## Design`,
  `## Changes` are required, and `## Introduction` must be the **first** level-2
  section — the why-first narrative precedes any technical content. The
  Introduction must carry a `### Non-goals` subsection.
- **Research (optional).** `## Research` is optional — omit it entirely for a
  feature with no research. When present it must hold at least one markdown list
  entry `- [title](path)` whose link resolves (epic-dir-first, then repo-root)
  to an existing file under the content dir's `research/` folder; the
  epic-relative form (`../../research/<name>/report.md`) is the clickable
  convention. An empty `## Research` section, a dead link, or a link to a file
  outside `research/` is a lint error. List only reports you actually read —
  never invent entries.
- **Video (optional).** `## Video` is optional — omit it entirely for a feature
  with no video brief. When present it must hold at least one markdown list
  entry `- [title](path)` whose link resolves (epic-dir-first, then repo-root)
  to an existing file under the content dir's `video/` folder; the
  epic-relative form (`../../video/<slug>/brief.md`) is the clickable
  convention. An empty `## Video` section, a dead link, or a link to a file
  outside `video/` is a lint error. List only briefs you actually read — never
  invent entries.
- **Stub table.** The header row must be exactly the six columns in order. At
  least one data row. Each `Change` cell is a kebab-case slug, unique within the
  table. Each of the four rating cells (Code, Integration, Unknowns, Risk) is one
  of `low`, `medium`, `high` — your honest per-change complexity estimate.

Slugs are repo-unique by convention: a member slug should not collide with an
unrelated existing or archived change of the same name.

## Lint gate — emission is not done until lint is clean

After authoring the epic, lint it and do not declare the epic complete until it
passes:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py" --epic <slug> --root <repo-root>
```

Run from the repo root (so `--root` may be omitted, defaulting to the cwd). If
the linter reports any error, **fix the epic and re-run** — repeat until it exits
`0` and prints `OK`. Never finish on a non-zero lint.

## Ending — hand off, don't plan the members

`s:epic` is standalone: it ends when the epic is emitted and lint-clean. When
that point is reached:

1. **Promote to `ready` on approval.** Emission wrote the epic at
   `Status: draft`. Reaching a lint-clean, approved epic advances the status via
   the guarded verb (which re-checks that the epic lints clean before writing):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" epic-set-status ready <slug> --root <repo-root>
   ```

2. **Ship the epic** through the repository's worktree-and-PR workflow: commit
   the `.shipd/epics/<slug>/` artifact on the `change/epic-<slug>` branch, push, open
   a PR, and let it auto-merge (`gh pr merge --auto --squash --delete-branch`).
   Report the PR with its full clickable URL.
3. **Point at `/s:plan` per member — do not plan them here.** This skill
   **never** creates member changes: it adds no directories under `.shipd/planned/`.
   For each stub row, tell the user to run `/s:plan <member-slug>`, which is
   where that member change is born (in its own worktree) carrying
   `Epic: <slug>`.
4. **Summarize** the epic — its slug, the Decisions/Design captured, and the
   member stub rows with their complexity ratings.
5. **Stop.** Do **not** start planning or implementing any member change. Epic
   authoring is done; planning each member is a separate, user-initiated step.
