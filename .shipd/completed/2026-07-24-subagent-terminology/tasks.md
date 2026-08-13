# subagent-terminology — tasks

## 1. Terminology sweep (live skills, docs, script comments)

- [x] 1.1 [P1] In `plugins/s/skills/build/SKILL.md`, replace every
      `teammate`/`teammates`/`Teammate` with `sub-agent`/`sub-agents`/
      `Sub-agent` (~30 occurrences), and update the two references to
      `references/teammate-prompt.md` (the "Paths in this skill" list and
      Phase 3) to `references/subagent-prompt.md`. Leave the phrase
      "Execution Team" in the title as-is.
- [x] 1.2 [P1] `git mv plugins/s/skills/build/references/teammate-prompt.md
      plugins/s/skills/build/references/subagent-prompt.md`, then in the
      moved file change the title to "Execution Sub-agent — initialization
      prompt" and replace the remaining `teammate` occurrences with
      `sub-agent` phrasing. Also fix one leftover in step 3 of the loop:
      "Follow the spec deltas and `design.md` precisely" should read
      "Follow the spec deltas and `plan.md`'s `## Implementation` decisions
      precisely" (drift from the lean-spec-format cutover).
- [x] 1.3 [P1] In `plugins/s/skills/build/scripts/claim_task.sh`, update the
      three header-comment mentions of teammates to sub-agents (lines ~2, ~5,
      ~8); no functional lines change.
- [x] 1.4 [P1] In the root `README.md`, replace the `teammate` occurrences
      (the `/s:build` catalog row, the `active` lifecycle bullet, and any
      others `grep -n teammate README.md` shows) with sub-agent wording.

## 2. Cutover hygiene

- [x] 2.1 Verify the sweep: `grep -ri teammate . --include="*.md"
      --include="*.py" --include="*.sh" --include="*.json"` returns hits only
      under `am/spec/changes/archive/`, `openspec/`, and
      `am/spec/changes/subagent-terminology/` (this change's own artifacts);
      note `am/spec/specs/` masters still say teammate until the merge engine
      applies this change's deltas — that is expected and not a sweep failure.
      Then run `python3 -m unittest discover -s plugins/s/skills/build/tests
      -q` (all green) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py
      subagent-terminology` (exit 0).
- [x] 2.2 Bump `plugins/s/.claude-plugin/plugin.json` `"version"` to
      `"0.1.2"`, run `claude plugin marketplace update shipd` and
      `claude plugin update s@shipd`, and verify the new snapshot
      `~/.claude/plugins/cache/shipd/am/0.1.2/skills/build/` contains
      `references/subagent-prompt.md` and zero `teammate` matches.
