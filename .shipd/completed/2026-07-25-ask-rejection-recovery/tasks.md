# Tasks — ask-rejection-recovery

## 1. Shared recovery rule (canonical text in plan.md ## Implementation)

- [x] 1.1 [P1] [req: question-rejection-recovery] Add the canonical
      "Question rejection recovery" paragraph from `plan.md` as a section in
      `plugins/s/skills/plan/SKILL.md`, placed after "The fast-path question
      contract (AskUserQuestion)".
- [x] 1.2 [P1] [req: question-rejection-recovery] Add the same canonical
      paragraph as a section in `plugins/s/skills/build/SKILL.md`, adjacent
      to its existing AskUserQuestion/question prose.
- [x] 1.3 [P1] [req: question-rejection-recovery] Add the same canonical
      paragraph as a section in `plugins/s/skills/epic/SKILL.md`, adjacent
      to its existing AskUserQuestion/question prose.
- [x] 1.4 [P1] [req: question-rejection-recovery] Add the same canonical
      paragraph as a section in `plugins/s/skills/initiative/SKILL.md`,
      adjacent to its existing AskUserQuestion/question prose.
- [x] 1.5 [P1] [req: question-rejection-recovery] Add the same canonical
      paragraph as a section in `plugins/s/skills/status/SKILL.md`, adjacent
      to its existing AskUserQuestion/question prose.

## 2. Onboard: recovery rule + resume semantics

- [x] 2.1 [req: question-rejection-recovery, checkpoint-resume] In
      `plugins/s/skills/onboard/SKILL.md`: add the canonical recovery
      paragraph as a bullet in the **Guardrails** section; narrow the "Stop
      means stop" guardrail to explicit stops (a selected Stop option or a
      typed stop — never a rejected/interrupted dialog); and extend the
      **Checkpoint** step of the per-chapter loop to state that after any
      interruption the next user message resumes from the last reached
      checkpoint, re-offering its choices when the message does not already
      answer them, never restarting the tour.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to one patch
      version above the higher of the worktree's current value and
      `origin/main`'s value at this moment (expected: `0.2.8` → `0.2.9`).
- [x] 3.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      `python3 plugins/s/skills/build/scripts/spec_lint.py
      ask-rejection-recovery`; then
      `grep -l "Question rejection recovery" plugins/s/skills/*/SKILL.md`
      and confirm exactly the six interactive skills match; everything green.
