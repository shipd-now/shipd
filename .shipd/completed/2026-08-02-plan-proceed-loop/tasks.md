## 1. Reshape the post-digest go-ahead

- [x] 1.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md`, Flow step 2, replace the "Without open
      questions" bullet's numbered proceed/adjust prompt with a single
      plain-text question, "Shall we proceed with the plan?" (no numbered
      options, no AskUserQuestion). State the loop: an affirmative reply advances
      to the depth gate; any other reply (further questions, new information,
      scope changes) is folded in as continued planning — the skill keeps
      planning, shows a one-line delta of what changed, and re-asks once the
      plan is settled again — looping until the user affirms; and an explicit
      go-ahead already in the reply (e.g. answering an OPEN QUESTIONS list)
      counts as the affirmative and skips a redundant re-ask.
- [x] 1.2 [req: investigation-findings-digest] In the same `SKILL.md`, Flow
      step 3, update the parenthetical trigger so the depth gate fires on the
      user's affirmative to "Shall we proceed with the plan?" (or an in-line
      go-ahead answering open questions), replacing the "a proceed, or answers
      to the open questions" wording.

## 2. Make the emit confirmation conditional

- [x] 2.1 [req: shared-understanding-summary] In
      `plugins/s/skills/plan/references/dialogue.md`, "Close with a
      shared-understanding summary", reframe the close as the depth-path
      ("gate needed more info") confirmation: the affirmative to "Shall we
      proceed with the plan?" is the sole approval for a clean gate, which emits
      directly; only when the grill loop ran does the skill present the summary
      and ask the user to reply "emit" to proceed or say what to refine. Keep
      "the fast path adds no such step."

## 3. Ship discipline

- [x] 3.1 [req: *] Bump the plugin version `0.6.19 → 0.6.20` in
      `plugins/s/.claude-plugin/plugin.json` so the cached snapshot picks up
      the edited skill.
- [x] 3.2 [req: *] Run a local eval (`python3 evals/run.py`) from the repo root
      to confirm the plan skill still drives to a lint-clean `ready` change with
      the new free-text go-ahead; the runner's generic proceed reply already
      answers the new question, so expect no eval-harness change.
