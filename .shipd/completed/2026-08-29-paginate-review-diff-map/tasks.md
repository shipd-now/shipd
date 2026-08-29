## 1. The changed-files read fetches every page

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, extend the test that
      already asserts the posting step reads the changed-files endpoint (the
      `assertIn('"repos/$REPO/pulls/$PR_NUMBER/files', posting, ...)` at line
      1099) with an assertion, in the same `run_block(self.posting_step())`
      style and beside it, that the posting step's text carries `--paginate` on
      that read. Assert on the step's source text; do not extend the runnable
      `gh` stub, which serves `*/files*` from a fixture and records no argv for
      it. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_copilot_verb` and observe it fail.
- [x] 1.2 [req: gate-workflow-template] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, add `--paginate`
      to the changed-files read at line 632 — the
      `"$gh_bin" api "repos/$REPO/pulls/$PR_NUMBER/files?per_page=100"` call —
      matching how the reviews poll at line 487 already spells it. Keep
      `per_page=100`: it sets the page size and pagination fetches the rest.
      Change nothing else about the call, including its
      `: > "$files_file"` failure branch. Confirm 1.1 passes.
- [x] 1.3 [req: gate-workflow-template] In the same file, update the comment
      above that read so it states the diff map must cover every changed file
      and that a truncated read would silently withhold anchoring rather than
      report a finding as unplaceable. Do not restate the plan; one or two
      sentences in the file's existing comment voice.

## 2. Verification

- [x] 2.1 [req: *] Confirm the template still parses at all three layers: load
      `plugins/s/integrations/copilot/copilot-review-gate.yml` as YAML, run
      `bash -n` over every step's `run` script, and `compile()` the Python
      embedded in the posting step's heredoc. All three must succeed.
- [x] 2.2 [req: *] Run `python3 -m unittest
      plugins.s.skills.build.tests.test_copilot_verb` and confirm it reports OK
      with no failures. The clean-worktree baseline was 153 tests, so it must
      report at least that.
- [x] 2.3 [req: *] Confirm both list calls in the template now paginate:
      `grep -n -- "--paginate" plugins/s/integrations/copilot/copilot-review-gate.yml`
      returns the reviews poll and the changed-files read, and no other
      `gh api` list call in that file lacks it.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 66 | 16.6k |
| Read | 12 | 1.6k |
| Agent | 2 | 1.0k |
| ScheduleWakeup | 1 | 263 |
| Edit | 4 | 40 |
| (no tool) | 0 | 3 |
| Write | 1 | 3 |
| **Total** | 86 | 19.6k |
