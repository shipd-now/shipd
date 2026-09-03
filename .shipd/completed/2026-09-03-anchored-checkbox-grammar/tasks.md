# Tasks — anchored-checkbox-grammar

## 1. Failing tests first

- [x] 1.1 [P1] [req: traceability-tag-enforcement] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add failing tests
      for the anchored grammar (build the fixture tasks text by string
      concatenation so no raw marker lands at a line start in prose): a
      correctly tagged task whose wrapped description carries backticked
      checkbox-marker literals on continuation lines lints with no
      traceability errors; when a genuinely untagged task FOLLOWS such a
      literal-carrying task, the error names the untagged task's real
      ordinal (not a literal-shifted one); and an indented real checkbox
      line (leading blanks before the marker) still counts as a task. Run
      the new tests and observe the first two fail.
- [x] 1.2 [P1] [req: atomic-task-claiming-with-stable-ids] In
      `plugins/s/skills/build/tests/test_claim_task.py`, add failing tests
      on a literal-carrying tasks fixture (same concatenation rule): the
      `status` first line counts only real tasks; `claim` returns the real
      task's ordinal and flips the real task's line (assert the literal's
      line is byte-unchanged); readiness/barrier evaluation ignores
      literals (a literal between a barrier and a group changes nothing);
      `complete <id>` marks the same line the claim marked; and an indented
      real checkbox participates in ordinals and rewrites (the rewrite
      preserves its leading blanks). Run the new tests and observe them
      fail.

## 2. Implementation

- [x] 2.1 [P2] [req: traceability-tag-enforcement] In
      `plugins/s/skills/build/scripts/spec_lint.py`, anchor `CHECKBOX_RE`
      (spec_lint.py:91) to optional leading blanks plus the marker,
      per plan.md's canonical grammar, and update its comment. Both call
      sites (the brief-requirements presence check and the traceability
      walk) consume the constant unchanged.
- [x] 2.2 [P2] [req: atomic-task-claiming-with-stable-ids] In
      `plugins/s/skills/build/scripts/claim_task.sh`, anchor every matcher
      with `[[:blank:]]*` per plan.md's Implementation: the
      `all_checkboxes` and `first_pending` greps, the `first_ready_line`
      awk line-filter, the in-progress enumeration awk and the `status`
      count greps, `set_box`'s sed (capture and preserve the leading
      blanks), and `strip_marker`. Update the header comment's ID-semantics
      paragraph. Keep bash 3.2/BRE-safe constructs.
- [x] 2.3 [req: traceability-tag-enforcement, atomic-task-claiming-with-stable-ids] Run
      the task-1.1 and 1.2 tests plus the full `test_spec_lint.py` and
      `test_claim_task.py`; confirm everything passes.

## 3. Version and barrier

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version`
      from `0.6.172` to `0.6.173`.
- [x] 3.2 [req: *] From the repo root run the full stdlib suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p
      "test_*.py"`; confirm green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 78 | 34.7k |
| Edit | 17 | 12.3k |
| Write | 4 | 7.1k |
| (no tool) | 0 | 1.7k |
| SendMessage | 2 | 1.5k |
| Read | 15 | 1.1k |
| Agent | 2 | 909 |
| **Total** | 118 | 59.2k |
