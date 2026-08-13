# plan-content-contract — tasks

## 1. Contract docs, fixtures, and failing tests first

- [x] 1.1 [P1] In `plugins/s/skills/build/tests/fixtures/sample/am/planned/sample-change/plan.md`,
      reshape the `## Idea` section to the new contract: open with a
      one-sentence problem statement, then the change list, then a
      `### Non-goals` subsection with at least one exclusion, then the
      capabilities/impact line. Content stays fixture-trivial.
- [x] 1.2 [P1] In `plugins/s/skills/build/tests/test_spec_lint.py`, add the
      failing tests for the non-goals check (TDD — they must fail until the
      linter task lands): a `plan.md` with both level-2 sections but no
      `### Non-goals` heading produces an error naming `### Non-goals` and a
      non-zero exit; the updated sample fixture passes with no error. Run
      them and observe the first one fail for the right reason (missing
      check, not a typo).
- [x] 1.3 [P1] Rewrite the plan.md portion of
      `plugins/s/skills/plan/references/emission.md`: the `## Idea` element
      order (why first — problem and motivation before any list; then
      concrete changes; then a required `### Non-goals` subsection; then
      capabilities and impact), an explicit note that no Goals section
      exists anywhere (Idea is the goals; how-level negative space lives in
      per-decision rejected alternatives), an `## Implementation`
      decision-kinds menu (files/components touched; interfaces and data
      shapes when relevant; each decision ADR-style with rationale and
      rejected alternative; risks), an updated worked example showing the
      new shape, and a TDD-ordering rule appended to the task discipline
      (failing test precedes the implementation it validates, where a
      testable surface exists).
- [x] 1.4 [P1] In `plugins/s/skills/plan/SKILL.md`, add a self-review step
      to the Flow between emission and lint: re-read the drafted `plan.md`,
      delta specs, and `tasks.md` for placeholders, internal contradictions,
      and decisions left to the executor; fix findings before linting.
      Renumber/reword the surrounding steps minimally.
- [x] 1.5 [P1] In `am/README.md`'s "The plan document" section, update the
      element description: Idea opens with the why, then the what, then a
      required `### Non-goals` subsection, then capabilities and impact;
      Implementation holds ADR-style decisions and risks; note the linter
      enforces the `### Non-goals` heading.

## 2. Linter implementation (after its tests exist)

- [x] 2.1 [P2] In `plugins/s/skills/build/scripts/spec_lint.py`, extend
      `check_plan_header` to error when `plan.md` lacks a level-3
      `### Non-goals` heading (message naming the missing subsection),
      matching the tests from task 1.2; confirm those tests now pass.

## 3. Cutover hygiene

- [x] 3.1 Verify: `python3 -m unittest discover -s
      plugins/s/skills/build/tests -q` all green; `python3
      plugins/s/skills/build/scripts/spec_lint.py` (master library) exit 0;
      `python3 plugins/s/skills/build/scripts/spec_lint.py
      plan-content-contract` exit 0 (this change's own plan.md already
      carries `### Non-goals`).
- [x] 3.2 Bump `plugins/s/.claude-plugin/plugin.json` `"version"` to
      `"0.1.4"`, run `claude plugin marketplace update shipd` and
      `claude plugin update s@shipd`, and verify the snapshot
      `~/.claude/plugins/cache/shipd/am/0.1.4/skills/plan/references/emission.md`
      contains `### Non-goals` and the TDD-ordering rule.
