## 1. Gate check for provisional ledger entries

- [x] 1.1 [req: provisional-entry-check] In
      `plugins/s/skills/build/tests/test_spec_gate.py`, add a
      `ProvisionalEntryCheckTest(SpecGateTestBase)` class with two tests: a
      plan whose `## Questions and answers` section holds `### Q1:` (Answered
      by `USER`) and `### Q2:` (Answered by `PLANNER`) is rejected with exit 2
      and a finding naming `Q2` and not `Q1`; a plan whose entries carry only
      `ORACLE` and `USER` passes. Follow the fixture helpers in
      `SpecGateTestBase`. Run the file and observe the first test fail.
- [x] 1.2 [req: provisional-entry-check] In
      `plugins/s/skills/build/scripts/spec_gate.py`, add
      `_check_provisional_entries(root, change)` per plan.md's "Gate check"
      decision (section read via `sl._section_lines` and `sl.QA_ENTRY_RE`,
      finding text `ledger entry Q<n> is provisional (**Answered by:**
      PLANNER) and awaits a human answer`), call it last in
      `collect_findings`, and name the check in the module docstring and the
      `collect_findings` docstring after the four context checks.
- [x] 1.3 [req: provisional-entry-check] Run `python3 -m unittest
      discover -s plugins/s/skills/build/tests -p "test_spec_gate.py"` and
      confirm it passes.

## 2. Ledger format authority

- [x] 2.1 [req: plan-document-sections] In `.shipd/README.md` (the
      `**Answered by:**` bullet near line 186), list `ORACLE`, `USER`, or the
      provisional `PLANNER`, and add one sentence: a `PLANNER` entry records a
      default a planner adopted in place of a deferred human answer, is
      rewritten to `USER` once the human answers, and the context gate
      rejects a plan still holding one.

## 3. The /s:epic-grill skill

- [x] 3.1 [req: epic-grill-preflight-order] Create
      `plugins/s/skills/epic-grill/SKILL.md` with frontmatter (`name:
      epic-grill`, a description carrying the trigger phrases "grill an
      epic", "plan the whole epic", "/s:epic-grill"), the `shipd:epic-grill
      v<version>` banner read from
      `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, and a Preflight
      section: `epic-show <epic> --json` and `cat epic <epic>`, the
      `ready`/`active` stop rule, member selection (`unplanned` lane plus
      `draft` members, others reported), and the printed dependency order
      with one reason per member.
- [x] 3.2 [req: epic-grill-planner-contract] In the same `SKILL.md`, add the
      Planning section: `shipd worktree <member>` per member, one
      general-purpose sub-agent per member run one at a time, the planner
      instruction copied verbatim from plan.md's "Planner instruction"
      block, `locate <member>` for a `draft` member's root, and grading from
      disk (`--root <worktree> status <member>` prints `draft`,
      `spec_lint.py <member> --root <worktree>` exits 0) with a stop-and-ask
      on a failed grade.
- [x] 3.3 [req: epic-grill-consistency-pass] In the same `SKILL.md`, add the
      Consistency pass section: read each member with `--root <worktree> cat
      change <member>`, fix repository-settled mismatches in place, add
      human-only conflicts as `PLANNER` entries in each affected ledger, and
      note members that modify the same master requirement for the hand-off.
- [x] 3.4 [req: epic-grill-final-round] In the same `SKILL.md`, add the Final
      round section: agenda from on-disk `PLANNER` entries with duplicates
      merged, no dialog on an empty agenda, AskUserQuestion batches of at
      most four questions naming member(s) and `Q<n>` with the default first
      and marked "(Recommended)", no other prose in a dialog turn, the
      question-rejection recovery rule, and the queue capture step
      (`wiki-queue-answer` / `wiki-queue-discard` per
      `${CLAUDE_PLUGIN_ROOT}/skills/ask/references/capture-rubric.md`).
- [x] 3.5 [req: epic-grill-amend-gate] In the same `SKILL.md`, add the Amend
      and gate section and the Ending: in-place artifact edits per answer,
      ledger rewrite to `**Answered by:** USER`, epic-wide answers flagged for
      `/s:epic <epic> amend`, `spec_gate.py <member> --root <worktree>` per
      member with resolve-then-ask on exit 2, the never-force-status rule,
      the why-first per-member summary, the `## Summary` sentence, and
      `/s:autopilot <epic>` alone on its own line; never build.

## 4. Harness body and registration

- [x] 4.1 [req: *] Create `plugins/s/harness/bodies/epic-grill.md` modeled on
      `plugins/s/harness/bodies/explain.md`: a `<!-- description: ... -->`
      first line, `<!-- include:preamble -->`, no `if:` gates, no `{refs}`,
      none of the tokens `subagent`, `sub-agent`, `AskUserQuestion`; members
      planned in turn in-session and the agenda asked as one numbered typed
      round; under 120 lines.
- [x] 4.2 [req: *] Add `/s:epic-grill` to the roster sentence at
      `AGENTS.md` line 156 next to `/s:epic`, a row after `/s:epic` in the
      Orchestration table of `README.md` (near line 274), and in
      `docs/cheatsheet.md` both the "Epics, driven" list (line 44) and a
      command-table row after `/s:epic` (example `/s:epic-grill export-cli`).
- [x] 4.3 [req: *] Bump the patch `version` in
      `plugins/s/.claude-plugin/plugin.json` by one.

## 5. Verification

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -p "test_*.py"` and grep its output for
      `OK` or `FAILED`; confirm it passes, including
      `test_every_command_has_exactly_one_body_template`.
- [x] 5.2 [req: *] Re-read `plugins/s/skills/epic-grill/SKILL.md` against
      all five `shipd-epic-grill` requirements and confirm no file outside
      plan.md's named set changed.
