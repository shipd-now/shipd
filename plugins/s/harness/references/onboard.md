# /s:onboard — the nine step directives

The long form the router points at. Each step is one rendered turn: a short
explanation, whatever excerpt or output it calls for, then the plain-text
navigation line. Render **only** the current step.

Steps 1–7 explain shipd over the pre-baked `add-board` change already sitting
in the sandbox; they run no engine commands and change no files. That change
gives a single-file kanban app — `kanban.py` at the sandbox root, over a
`cards.json` store beside it — two read views: a flat `list` and a three-lane
`board` (todo / doing / done). Steps 4–6 quote its real artifact files; step 8
builds it for real.

## Step 1 — the banner, and what SDD is

The first visible output is the shipd ASCII banner in a fenced code block.
Greet the user in a sentence, then explain **spec-driven development** in one
paragraph: instead of prompting an agent straight into code, you first
converge on a short written spec — what to build and why — and the build works
from that spec, so intent is captured, reviewable, and reusable before any
code is written. Close with the navigation line: run `/s:onboard next` to
continue.

## Step 2 — how shipd works

In a few sentences: shipd turns that spec into a small set of **artifacts** on
disk, then **executes** the work inside a git *worktree* — a second working
copy of the repository on its own branch, so a build runs in isolation without
disturbing the main checkout. Because each change gets its own worktree, many
changes can be in flight at once. Close with `next` / `back`.

## Step 3 — the artifacts

Three short dot points, one line each:

- `plan.md` — the idea (why and what) plus the implementation decisions.
- `specs/<capability>/spec.md` — the delta spec: the requirements this change
  adds or changes, in a fixed grammar.
- `tasks.md` — the implementation checklist, each task tagged with the
  requirement it satisfies.

Close with `next` / `back`.

## Step 4 — the example `plan.md`

Open the real file at `$SANDBOX/.shipd/planned/add-board/plan.md` and quote a
short excerpt — the `## Idea` with its `### Motivation` and `### Non-goals`, a
few lines only. Say in one sentence what the change will build: the `list` and
`board` read views over `cards.json`. Close with `next` / `back`.

## Step 5 — the example delta spec

Open `$SANDBOX/.shipd/planned/add-board/specs/kanban/spec.md` and quote a short
excerpt. Point out that it is an `## ADDED Requirements` delta — `ADDED`
because `kanban` is a brand-new capability — carrying two requirement blocks
(`list-cards` and `board-view`), each with an `id:` and a `#### Scenario:`.
Close with `next` / `back`.

## Step 6 — the example tasks, and model tiering

Open `$SANDBOX/.shipd/planned/add-board/tasks.md` and quote a couple of the
`[req: …]`-tagged checklist lines. Then explain **model tiering** in a few
sentences: shipd plans on the **best** available model, because planning is
the hard, high-leverage part, and executes the tasks on the **second-best**,
which is enough for well-specified work. Splitting the work this way buys
efficiency, speed, and lower cost. Close with `next` / `back`.

## Step 7 — summary

In a short paragraph, recap what the learner has seen: a spec becomes three
artifacts; the best model plans and a cheaper one executes; the whole thing
runs in an isolated worktree. Say that the next step builds the change for
real. Close with `/s:onboard next` to build it, `/s:onboard back` to review.

## Step 8 — build it for real

The one step that runs the real engine. Explain before each action and show
the real output — never a fabricated `OK` or merge result.

**Idempotence:** when `$SANDBOX/.shipd/completed/` already holds the archived
`add-board`, skip the build entirely and jump to the "what we built" summary
and the copy/paste block.

The sequence, each command preceded by a sentence of intent: lint the change;
promote it to `ready`; copy the shipped reference implementation
(`kanban.py` and `cards.json`) into the sandbox root, which is what an
execution agent would otherwise have written; tick the checklist through the
coordinator, claiming and completing until `status` reports `pending=0`;
advance the status to `complete` and then `verified`, whose guards require the
finished checklist; and finally merge and archive.

Then say in a few sentences **what we built**: the change moved from
`planned/` to `completed/`, its requirements were seeded into the master
library at `$SANDBOX/.shipd/verified/kanban/spec.md`, and the app now renders
its board. Show it once by running the `board` view from the sandbox, then
hand the learner a copy/paste block:

```
cd ~/.shipd/onboarding/sandbox
python3 kanban.py board
python3 kanban.py list
```

Close with `/s:onboard next` for a suggested enhancement, `/s:onboard back` to
review.

## Step 9 — your turn: plan an enhancement

Suggest one small enhancement: a `move` command that moves a card to another
lane (`move <id> <lane>`). Explain in a sentence that the sandbox is a real
shipd library, so planning there lands a new change in its `planned/`. Then
print the two exact copy/paste blocks — first, open a session in the sandbox:

```
cd ~/.shipd/onboarding/sandbox && claude
```

then, inside that session, plan the enhancement:

```
/s:plan Add a move command to kanban.py: "move <id> <lane>" moves a card to another lane
```

After the handoff, offer cleanup: delete `~/.shipd/onboarding/` or keep it for
further exploration, reporting its path. Never delete without the user
choosing to. This is the final step — there is no `next`, though
`/s:onboard back` still returns to step 8.
