## 1. Skill rewrite

- [x] 1.1 [req: onboard-step-navigation] In
      `plugins/s/skills/onboard/SKILL.md`, replace the opening and scaffold
      sections with the argument-driven state machine: no argument → fresh
      start (copy the shipped template to `~/.shipd/onboarding/sandbox/`,
      `git init` it, write `~/.shipd/onboarding/state.json` as
      `{"step": 1, "sandbox": "<abs path>"}`, render step 1) or resume at
      the persisted step; `next` → increment the step in the state file and
      render it; `back` → decrement clamped at 1 (offered on explainer
      steps 1–7); step 8 is idempotent — when the sandbox's `.shipd/completed/`
      already holds the archived `add-board`, re-entering step 8 re-shows
      the built summary and test instructions instead of rebuilding.
- [x] 1.2 [req: onboard-tour-skill] In the same file, write the explainer
      steps 1–7 as directives (what to teach and show, not scripts to
      recite): 1 — the shipd ASCII banner (byte-copied from the fenced
      masthead at the top of `README.md`) above the greeting, then one
      paragraph on Spec-Driven Development; 2 — shipd creates artifacts,
      executes in worktrees (one-breath explanation of a worktree), and so
      supports many changes in parallel; 3 — the three artifacts as short
      dot points; 4 — short excerpts from the sandbox's actual
      `.shipd/planned/add-board/plan.md` and what we'll build; 5 — excerpts
      from its `specs/kanban/spec.md`; 6 — excerpts from its `tasks.md`
      plus the model-tiering explanation (best model plans, second-best
      executes: efficiency, speed, cost); 7 — a short summary of what was
      learned. Every step ends with the plain-text navigation line naming
      `/s:onboard next` (and `back` where available).
- [x] 1.3 [req: sandbox-hands-on, walkthrough-pacing] In the same file,
      write step 8 — execute the pre-baked change with the documented
      engine sequence (lint → set-status ready → copy
      `assets/solutions/add-board/` files in → tick tasks via the
      coordinator → set-status complete then verified → merge), condensed
      explain-before-do narration, then a "what we built" summary and a
      copy/paste test block (`cd ~/.shipd/onboarding/sandbox`,
      `python3 kanban.py board`, `python3 kanban.py list`) — and step 9 —
      suggest a `move` command enhancement and print the exact copy/paste
      blocks (`cd ~/.shipd/onboarding/sandbox && claude`, then the
      `/s:plan Add a move command to kanban.py: "move <id> <lane>" moves a
      card to another lane` prompt), followed by the delete-or-keep cleanup
      offer for `~/.shipd/onboarding/`.
- [x] 1.4 [req: plain-text-tour-prompts, checkpoint-resume] Sweep the whole `SKILL.md` for
      stale structure — beats, cycles 2–3, typed numbered checkpoints, the
      scratchpad sandbox location, the old resume guardrail — and align the
      frontmatter description and trigger phrases with the stepper design
      (include "next" and "back" argument handling), keeping the pacing and
      isolation guardrails and the one-dialog-only cleanup rule.

## 2. Version and verification

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.4.1 → 0.4.2.
- [x] 2.2 [req: *] Smoke-verify the mechanical parts under a temporary HOME
      (`HOME=$(mktemp -d)`): copy the template to
      `$HOME/.shipd/onboarding/sandbox`, `git init`, write and re-read
      `state.json` (step round-trip 1 → 2 → 1), then run the full step-8
      engine sequence against the sandbox (lint prints OK → ready → copy
      solution files → claim/complete all tasks → complete → verified →
      merge) and confirm `verified/kanban/spec.md` was seeded, the change
      archived under `completed/`, and `python3 kanban.py board` renders
      the three-lane board. Delete the temporary HOME afterwards.
