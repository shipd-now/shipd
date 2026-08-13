# Tasks — checkpoint-plain-text

## 1. Plan skill: typed decision rounds

- [x] 1.1 [P1] [req: dialog-prose-separation, context-brief] Rework
      `plugins/s/skills/plan/SKILL.md`'s fast-path question contract
      section: the brief stays mandatory, but the batched round is presented
      as plain-text numbered questions (2–4, concrete options, recommended
      default first) at the end of the brief's message and collected from
      the user's typed reply; state that no AskUserQuestion is issued in a
      turn carrying a brief or other substantive prose, and that dialogs
      remain only for self-contained questions in prose-free turns. Keep the
      existing "Question rejection recovery" section unchanged.
- [x] 1.2 [P1] [req: context-brief] Rework
      `plugins/s/skills/plan/references/dialogue.md`: the context-brief
      section and grouped-round protocol collect each round as a typed reply
      (brief + numbered questions in one message); dependent-chain
      follow-ups keep their one-line delta, also typed; the
      shared-understanding close collects confirmation as a typed reply
      ("reply 'emit' or say what to refine") instead of a final
      AskUserQuestion.

## 2. Onboard: plain-text tour prompts

- [x] 2.1 [P1] [req: dialog-prose-separation, plain-text-tour-prompts]
      Rework `plugins/s/skills/onboard/SKILL.md`: the opening chapter menu,
      the per-chapter checkpoint step, and the chapter-6 sandbox offer are
      plain-text numbered prompts in the same message as the greeting or
      lesson, answered by typed reply (recommended default named first);
      only the sandbox cleanup offer may remain an AskUserQuestion. Update
      the Guardrails wording accordingly, keeping the "Explicit stop means
      stop", resume-at-checkpoint, and "Question rejection recovery" rules
      intact (recovery still governs any remaining dialog).

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to one patch
      version above the higher of the worktree's current value and
      `origin/main`'s value at this moment (expected: `0.2.9` → `0.2.10`).
- [x] 3.2 [req: dialog-prose-separation, investigation-findings-digest]
      Rework `plugins/s/skills/plan/SKILL.md` Flow step 2 ("Report
      findings, then ask for the go-ahead"): the findings digest still ends
      the investigation turn, but the go-ahead becomes a plain-text numbered
      prompt closing that same message — options exactly: 1 proceed to the
      depth gate and planning (recommended, named first), 2 adjust scope
      first, 3 stop — collected from the user's typed reply; no
      AskUserQuestion in the investigation turn. Keep every other rule of
      that step (no planning decisions in the prompt, no depth-gate verdict
      in the investigation turn, adjust-scope delta line, polite stop)
      unchanged, and update step 3's "on the go-ahead turn" wording to
      reference the typed reply.
- [x] 3.3 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      `python3 plugins/s/skills/build/scripts/spec_lint.py
      checkpoint-plain-text`; confirm
      `plugins/s/skills/onboard/SKILL.md` instructs AskUserQuestion only
      for the sandbox cleanup offer, and that
      `plugins/s/skills/plan/SKILL.md` and
      `plugins/s/skills/plan/references/dialogue.md` instruct typed
      plain-text rounds whenever a brief is present; everything green.
- [x] 3.4 [req: dialog-prose-separation, context-brief] Rework
      `plugins/s/skills/plan/references/visualization.md`'s "Per-option
      diagrams via AskUserQuestion `preview`" section: remove the "as every
      depth-path question is" premise (depth-path rounds are now typed
      plain-text); instruct that per-option visuals for typed rounds are
      attached inline in the brief's plain-text message (each option's small
      diagram or table with its numbered entry, same carries-a-decision bar
      per option); and rescope the `preview` idiom to the only case where a
      dialog is permitted — a self-contained AskUserQuestion in a prose-free
      turn. Leave the rest of the reference's idioms and prohibitions
      unchanged.
- [x] 3.5 [req: *] Re-run the verification barrier of task 3.3, additionally
      confirming `plugins/s/skills/plan/references/visualization.md` no
      longer instructs an AskUserQuestion (or `preview` use) for depth-path
      or brief-bearing rounds; everything green.
