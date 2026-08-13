## 1. Reword the gate literal in the skill prose

- [x] 1.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md`, replace all three occurrences of the
      literal "Shall we proceed with the plan?" — the digest's go-ahead ending
      (~line 196), the re-ask inside the go-ahead loop (~lines 200–201), and
      the depth-gate trigger reference "when the user affirms …" (~line 213) —
      with "We have enough details — shall I write the plan now?".
- [x] 1.2 [req: investigation-findings-digest] In the same
      `plugins/s/skills/plan/SKILL.md` "Without open questions" bullet, add a
      guard clause: this readiness-asserting go-ahead is printed only when no
      genuinely open task-shaping question remains; whenever one does, the turn
      takes the `OPEN QUESTIONS` ending instead of asserting readiness.
- [x] 1.3 [req: shared-understanding-summary] In
      `plugins/s/skills/plan/references/dialogue.md` (~line 136), replace the
      "Shall we proceed with the plan?" literal in the "sole approval for a
      clean gate" sentence with "We have enough details — shall I write the
      plan now?".

## 2. Refresh the snapshot version

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.68` to `0.6.69` so the
      cached snapshot picks up the reworded skill.

## 3. Verify no stale literal remains

- [x] 3.1 [req: *] Grep the edited skill prose for the old literal
      (`grep -rn "Shall we proceed with the plan" plugins/s/`) and confirm
      zero hits — both live skill surfaces now carry the new wording. Do not
      grep `.shipd/verified/`: its master still holds the old literal until the
      delta merge propagates the new one at change completion.
