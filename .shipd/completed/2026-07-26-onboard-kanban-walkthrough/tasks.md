## 1. Retire the chapter library

- [x] 1.1 [req: onboarding-docs-library] Delete the six chapter files and the
      `docs/onboarding/` directory itself.

## 2. Rewrite the onboard skill

- [x] 2.1 [req: onboard-tour-skill] In `plugins/s/skills/onboard/SKILL.md`,
      rewrite the frontmatter `description` and the opening section: the
      description sells the sandbox-first kanban walkthrough (keep the
      "onboarding"/"onboard"/"/s:onboard" trigger phrases, drop
      chapter/tour framing); the opening replaces the chapter menu with —
      greet in a sentence or two, scaffold the sandbox immediately, then
      orient the user on what the walkthrough will build (CLI kanban:
      board → cards → edit) and what they can do at any point (steer, ask
      questions, stop). No menu, no AskUserQuestion, no start-choice.
- [x] 2.2 [req: sandbox-hands-on] In the same file, replace the scaffold
      section: pick `$SANDBOX` (session scratchpad when available, else
      `mktemp -d`), `git init`, create an empty `.shipd/verified/` and
      `.shipd/planned/` with **no** seed capability; show the user the layout
      and explain it is a real (if empty) am library about to receive its
      first capability. Remove the `greeter` fixture entirely.
- [x] 2.3 [req: onboard-tour-skill, sandbox-hands-on] In the same file, write
      the cycle-loop section with three scripted cycles — `add-board`,
      `add-cards`, `edit-cards`. Define the fixture inline: `kanban.py`
      (python3, single file) over `cards.json` (fields `id`, `title`, `lane`;
      lanes `todo`/`doing`/`done`); cycle 1 implements `list` and a
      three-column ASCII `board` and seeds `cards.json` with three sample
      cards; cycle 2 adds `add <title> [--lane]`; cycle 3 adds
      `edit <id> [--title] [--lane]`. Each cycle: prompt the user with the
      planning task, author `plan.md`/delta spec/`tasks.md` under
      `$SANDBOX/.shipd/planned/<change>/`, lint via `spec_lint.py --root
      "$SANDBOX"`, `set-status ready`, implement the code, tick tasks via
      `claim_task.sh`, `set-status complete` then `verified`, merge via
      `spec_merge.py`, then explain the artifact lifecycle (planned →
      completed, master spec grown). Cycle 1 fully narrated; cycles 2–3 hand
      decisions (flag names, card wording) to the user; after cycle 3 offer
      open-ended further cycles or finishing.
- [x] 2.4 [req: checkpoint-resume, plain-text-tour-prompts] In the same file,
      write the checkpoint and guardrail sections: a plain-text numbered
      checkpoint after each cycle (continue as recommended default,
      re-explain, stop); the cleanup delete-or-keep offer as the one prompt
      that may use AskUserQuestion; guardrails — never modify the user's real
      repository, never fabricate engine output, no dialog shares a turn with
      narration, interruption resumes from the last checkpoint, and
      AskUserQuestion rejection-recovery.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.3.1 → 0.3.2.
- [x] 3.2 [req: *] Smoke-verify the walkthrough mechanics without a live
      session: scaffold a sandbox exactly as the rewritten skill instructs,
      author the cycle-1 `add-board` change per the skill's fixture text, and
      run the real engine sequence (lint → ready → claim/complete →
      complete → verified → merge). Confirm `verified/kanban/spec.md` was
      seeded in the sandbox, the change archived under its `completed/`, and
      `python3 kanban.py board` renders the three-lane board with the sample
      cards. Then delete the smoke sandbox.
