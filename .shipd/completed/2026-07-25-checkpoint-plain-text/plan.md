# checkpoint-plain-text
Status: verified

## Idea

A second, distinct Claude Code defect — beyond the rejection misfire the
`ask-rejection-recovery` change hardened against — makes text that shares a
turn with an AskUserQuestion call unreliable: anthropics/claude-code#74260
(open at v2.1.211) silently drops assistant text mid-turn in the
thinking → text → thinking → tool-call pattern, and older widget bugs
(#30422, #58207) clipped or covered the text above the dialog. Observed live,
twice: the onboarding tour's chapter lesson never rendered — the user got a
bare checkpoint menu with no chapter content above it. The am skills are
built on the opposite assumption: the plan skill's context-brief contract
*mandates* load-bearing prose and the dialog in the same turn, and the tour
pairs each lesson with a checkpoint dialog.

This change separates prose from dialogs:

- Add a `dialog-prose-separation` rule to `shipd-interaction`: a turn that
  issues an AskUserQuestion carries no load-bearing prose — context either
  lives inside the dialog's own fields or ends the turn as plain text with a
  typed-reply numbered prompt.
- Rework the plan skill's question protocol (fast path and depth path): the
  context brief stays mandatory and user-visible, but the decisions are put
  as plain-text numbered questions answered by typing; dialogs remain only
  for self-contained questions in prose-free turns.
- Switch the tour's checkpoints, chapter menu, and sandbox offer to
  plain-text numbered prompts; dialogs stay only for prose-free prompts
  (the sandbox cleanup offer).
- Bump the plugin version so the cache snapshot picks up the fix.

### Non-goals

- No upstream Claude Code fix; no attempt to steer thinking-block interleaving
  (unreliable per the bug's own reproduction).
- No prose alignment of the epic, initiative, build, and status skills in this
  change — they carry no same-turn brief contract; their short-prose gates are
  governed by the new `shipd-interaction` rule and any needed rewording is
  deferred until observed to matter.
- No removal of the `question-rejection-recovery` rule — dialogs still exist
  (prose-free prompts) and remain covered by it.

Affected capabilities: `shipd-interaction` (modified — new requirement),
`shipd-plan` (modified), `shipd-onboard` (modified — new requirement). Impact:
`plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/plan/references/dialogue.md`,
`plugins/s/skills/onboard/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

## Implementation

- **The rule, stated once in `shipd-interaction`.** A turn issuing an
  AskUserQuestion may carry at most a one-line lead-in outside the dialog;
  anything the user must read to answer (briefs, lessons, summaries) either
  goes into the dialog's own fields (question text, option labels and
  descriptions) or ends its turn as plain text with the choices as a numbered
  list answered by typing. Rejected: teaching skills to avoid the
  thinking-interleave pattern that triggers #74260 — prose cannot reliably
  control thinking-block placement, so the only robust separation is
  structural.
- **Plan skill: typed decision rounds.** In `plan/SKILL.md` (fast-path
  question contract) and `references/dialogue.md` (round protocol and the
  shared-understanding close): a round with a context brief presents the
  brief and its 2–4 numbered questions — each with lettered/numbered concrete
  options, recommended default first — as one plain-text message and waits
  for a typed reply (e.g. "1a 2c"); the shared-understanding summary closes
  with a typed confirm ("reply 'emit' or say what to refine"). AskUserQuestion
  stays allowed only when the turn needs no brief and carries no other
  substantive prose. Rejected: folding a full brief into dialog fields —
  restatements and diagrams do not fit option descriptions.
- **Tour: typed prompts wherever a lesson is on screen.** In
  `onboard/SKILL.md`: the chapter menu, every chapter checkpoint, and the
  chapter-6 sandbox offer become plain-text numbered prompts in the same
  message as the greeting/lesson; the sandbox cleanup offer (a prose-free
  turn) may remain an AskUserQuestion. The existing recovery and
  resume-at-checkpoint rules stay untouched and keep governing whatever
  dialogs remain.
- **Master deltas for `shipd-plan`.** `context-brief` (base `59538bc2d72a`) is
  MODIFIED: the brief remains a mandatory, user-visible precondition, but the
  round is collected by typed reply instead of a same-turn dialog. Likewise
  `investigation-findings-digest` (base `fad2f0c5bd79`, added by the
  parallel-session PR #27) is MODIFIED: it mandated a digest-then-dialog
  investigation turn — the same drop-prone prose+dialog pattern — so the
  go-ahead keeps its exact scope-locked semantics (proceed recommended /
  adjust scope / stop, digest precondition, no planning decisions) but is
  collected as a typed numbered prompt closing the digest message. The
  `shared-understanding-summary` requirement is mechanism-neutral and is not
  touched.
- **Version bump** at execution time per the cache-snapshot rule: one patch
  above the higher of the worktree's and `origin/main`'s value (expected
  `0.2.9` → `0.2.10`).
- Risk: typed replies are freer-form than dialog selections. Guard: prompts
  always number the options and name the recommended default, and the
  recovery rule already covers folding in typed answers.
- Risk: prose-only change, so no engine test can pin behavior. Guard: the
  verification task greps the reworked sections and confirms the tour skill
  no longer instructs dialogs at lesson-bearing moments.
