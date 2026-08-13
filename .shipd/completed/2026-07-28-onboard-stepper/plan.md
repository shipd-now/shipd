# onboard-stepper
Status: verified

## Idea

Live testing showed the walkthrough still reads as the guide doing the work
and talking past the learner: it wrote and explained the plan in its own
conversational pacing, and a learner has no explicit control over progression.
The fix is a fixed, numbered step sequence the user drives with
`/s:onboard next` and `/s:onboard back`.

This change restructures `/s:onboard` into nine navigable steps:

1. The shipd ASCII banner + what Spec-Driven Development is (one
   paragraph), then pause.
2. How shipd works: it creates artifacts, executes in worktrees (briefly
   explained), letting you work on many changes at once.
3. The artifacts, as short dot points.
4. Deep-dive: the example `plan.md` — what we'll build.
5. Deep-dive: the example delta spec.
6. Deep-dive: the example tasks, plus the model-tiering story (best model
   plans, second-best executes — efficiency, speed, cost).
7. Pause and summarize what we learned.
8. Implement: execute the tasks for real and build the kanban board, then
   say what was built and how to test it in the shell.
9. Suggest a small enhancement and hand over exact copy/paste commands to
   plan it.

Step state and the sandbox move to stable disk paths so `next`/`back` work
across sessions. The three-cycle arc (`add-cards`, `edit-cards`) is retired:
the pre-baked `add-board` change is the single worked example, and step 9
hands the learner their first self-serve plan. The earlier unbuilt
`onboard-banner` change is absorbed here (step 1 opens with the banner).

### Non-goals

- No engine-script changes; the state file is read/written with plain shell,
  not a new CLI.
- No changes to the sandbox template assets or the reference solution.
- No guided cycles beyond the single worked example.
- No `/s:onboard` eval case.

Affected capabilities: `shipd-onboard` (one added, four modified, one removed
requirement). Impact: `plugins/s/skills/onboard/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json` (0.4.1 → 0.4.2).

## Implementation

- **State on disk:** `~/.shipd/onboarding/state.json`, schema
  `{"step": <int 1-9>, "sandbox": "<abs path>"}`; sandbox at the stable path
  `~/.shipd/onboarding/sandbox/` (scaffolded by copying the shipped template, as
  today). `~/.am` is already shipd's home (build logs live there).
  Rejected: session scratchpad — it dies with the session, breaking `next`
  from a fresh session.
- **Navigation semantics:** no argument → fresh start (scaffold, write state
  at step 1, render step 1) or resume at the persisted step; `next` →
  increment, render; `back` → decrement, clamped at 1, and available on the
  explainer steps. Steps never auto-advance — every step ends by naming the
  exact command to continue.
- **Step-8 idempotence:** re-entering step 8 when the sandbox's
  `.shipd/completed/` already holds the archived `add-board` re-shows the
  built-summary and test instructions instead of re-running the build.
- **Steps 4–6 show the real files:** short excerpts quoted from the
  sandbox's actual `plan.md`, `specs/kanban/spec.md`, and `tasks.md` — the
  learner sees the artifacts, not a paraphrase. Pacing rules (excerpts, no
  essays, no internal noise) carry over.
- **Step 8 runs the documented engine sequence** (lint → ready → copy
  reference solution → tick tasks → complete → verified → merge) with
  condensed explain-before-do narration, then prints a copy/paste test
  block: `cd ~/.shipd/onboarding/sandbox` then `python3 kanban.py board` and
  `python3 kanban.py list`.
- **Step 9's exact handoff:** suggest a `move` command enhancement and print
  two copy/paste blocks — `cd ~/.shipd/onboarding/sandbox && claude` and the
  prompt `/s:plan Add a move command to kanban.py: "move <id> <lane>" moves
  a card to another lane` — noting the sandbox is a real am library so the
  plan lands in its `planned/`. Cleanup (delete or keep `~/.shipd/onboarding/`)
  is offered after.
- **Banner absorbed:** the fresh-start turn opens with the shipd ASCII
  banner in a fenced code block, byte-identical to the `README.md` masthead,
  above the greeting.
- **checkpoint-resume requirement is removed:** resume is now mechanical —
  re-running `/s:onboard` reads the state file — so the conversational
  recovery contract is superseded by `onboard-step-navigation`.

Risk: navigation is LLM-interpreted (no engine enforces the state machine);
mitigated by pinning the state schema and per-argument behavior in the skill
text, and smoke-testing the mechanical parts (template copy, state file
round-trip, full step-8 engine sequence) under a temp HOME.
