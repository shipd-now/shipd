## 1. Contract tests first

- [x] 1.1 [req: epic-grill-planner-contract] In
      `plugins/s/skills/build/tests/test_epic_grill_contract.py`, add three
      tests to `EpicGrillContractTest`: `SKILL.md` contains
      "append your slug to that entry's `**Relied on by:**` field"; the
      harness body `plugins/s/harness/bodies/epic-grill.md` contains
      "`**Relied on by:**`"; `plugins/s/skills/plan/references/emission.md` contains
      "`- **Relied on by:**`" (its field-list style). Update the module docstring to name them.
- [x] 1.2 [req: epic-grill-amend-gate] In the same file, add a test that
      `SKILL.md` contains "re-run the consistency pass" and the harness body
      contains "re-run the consistency pass". Run
      `python3 -B -m unittest discover -s plugins/s/skills/build/tests -p
      "test_epic_grill_contract.py"` and observe the new tests fail.

## 2. Skill

- [x] 2.1 [req: epic-grill-planner-contract] In
      `plugins/s/skills/epic-grill/SKILL.md`, append the four-line block from
      plan.md's "Planner instruction addition" inside the verbatim planner
      instruction, directly after the `**Queued:**` sentence and before
      "Install the change through spec_emit.py".
- [x] 2.2 [req: epic-grill-planner-contract] In the same file's grading
      paragraph (after the two grading commands), state that the skill also
      re-runs `spec_lint.py <slug> --root <root>` on every member in the
      running list after each planner, and a failed re-lint stops and asks
      the human like a failed grade.
- [x] 2.3 [req: epic-grill-amend-gate] In "Amend and gate", add a numbered
      step 4 after "Epic-wide answers": when any answer chose a non-default
      option, re-run the consistency pass on each overturned entry's member
      and every member its `**Relied on by:**` names (every selected member
      when the field is absent), fix what the repository settles and re-lint,
      and ask any human-only conflict in one further dialog per the Final
      round rules; when every default was accepted, skip it. State that the
      field is kept when an entry is rewritten to `USER`.

## 3. Harness body

- [x] 3.1 [req: epic-grill-planner-contract] In
      `plugins/s/harness/bodies/epic-grill.md` step 3, add: where a plan
      builds on an earlier member's `PLANNER` default, append the member's
      slug to that entry's `**Relied on by:**` field, edit nothing else in
      the earlier plan, and re-lint the earlier member.
- [x] 3.2 [req: epic-grill-amend-gate] In step 6, before running
      `spec_gate.py`, add the re-check: when an answer overturned a default,
      re-run the consistency pass on that member and every member its
      `**Relied on by:**` names (all members without the field), and ask any
      human-only conflict as one more numbered typed round. Keep the body
      free of `subagent`, `sub-agent`, and `AskUserQuestion`.

## 4. Ledger grammar surfaces

- [x] 4.1 [req: plan-document-sections] In
      `plugins/s/skills/plan/references/emission.md`, after the
      `**Queued:**` field bullet (near line 236), add a bullet:
      `- **Relied on by:**` — on a `PLANNER` entry only, its last field: the
      later members whose plans built on its default, comma-separated, written
      by those members' planners and kept when the entry becomes `USER`.
- [x] 4.2 [req: plan-document-sections] In `.shipd/README.md`, after the
      `**Queued:**` bullet (near line 194), add the same field bullet in that
      list's style.

## 5. Version and verification

- [x] 5.1 [req: epic-grill-amend-gate] Bump `plugins/s/.claude-plugin/plugin.json` version from
      `0.6.282` to `0.6.283` (if `main` has moved past that, take the next
      patch above it).
- [x] 5.2 [req: epic-grill-amend-gate] Run `python3 -B -m unittest discover -s plugins/s/skills/build/tests`
      and grep the output for `OK` or `FAILED`; confirm `OK`, including
      `test_epic_grill_contract.py` and `test_harness_bodies.py`.
