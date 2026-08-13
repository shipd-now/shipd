## 1. State the rule in the readiness checklist

- [x] 1.1 [req: verified-runnable-premises, premise-evidence-in-attestation] In
      `plugins/s/skills/plan/references/readiness.md`, add the runnable-premise
      rule to the **Attestation** section as evidence under item 3 (affected
      capabilities and files) — not as a fifth checklist item. State: where a plan
      asserts how an existing command, script, or flag behaves and a task or delta
      requirement depends on it, that command must have been run before emission,
      and the attestation must cite the invocation and its observed output or exit
      code. State that a citation of the command's implementation source does not
      satisfy it.
- [x] 1.2 [req: verified-runnable-premises] In the same file, state the two
      exemptions explicitly: assertions about behavior this change will create,
      and assertions no task or delta requirement depends on.
- [x] 1.3 [req: premise-evidence-in-attestation] In the same file, confirm the
      "The four items" section still lists exactly four items and that the rule is
      worded as evidence within item 3, not as an additional gate.

## 2. Carry it into the emission guide

- [x] 2.1 [req: verified-runnable-premises] In
      `plugins/s/skills/plan/references/emission.md`, in the `## Implementation`
      guidance where decision kinds are listed, add a short paragraph
      cross-referencing the runnable-premise rule in `readiness.md` — do not
      restate the rule in full — noting that an ADR-style decision resting on an
      existing command's behavior cites the observed run.

## 3. Name it in the skill's investigation step

- [x] 3.1 [req: verified-runnable-premises] In
      `plugins/s/skills/plan/SKILL.md`, in the Flow's investigation step, add one
      sentence directing the planner to run the commands whose behavior the plan
      will rely on, cross-referencing `plugins/s/skills/plan/references/readiness.md` for the rule.
      Include the concrete failure it prevents: two individually reasonable
      decisions can be jointly broken, and only running the command reveals it.

## 4. Verification

- [x] 4.1 [req: *] Read
      `plugins/s/skills/plan/references/readiness.md`,
      `plugins/s/skills/plan/references/emission.md`, and
      `plugins/s/skills/plan/SKILL.md` and confirm the rule is stated once in
      `readiness.md` and cross-referenced (not restated) from the other two.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the engine suite still passes.
- [x] 4.3 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` by one patch increment.
