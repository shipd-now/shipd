## 1. Replace first-come allocation with fair-share passes

- [x] 1.1 [req: related-context] Confirm the starting point: `python3 -m
      unittest discover -s plugins/s/skills/review/tests` is green at 269
      tests, and `cmd_related` in
      `plugins/s/skills/review/scripts/semdiff.py` still holds the single
      `remaining = per_review_cap` counter decremented inside the per-file
      loop. That counter is the defect.
- [x] 1.2 [req: related-context] Split `cmd_related` into two phases. First
      collect every changed file's full ranked candidate list with no budget
      applied, keeping each candidate's importer-or-importee tag. Then
      allocate. Do not apply the per-file cap during collection — the
      per-file cap bounds what is listed, and collection needs the full list
      to compute each file's candidate count for ordering and its truncation
      count for reporting.
- [x] 1.3 [req: related-context] Allocate in passes. On each pass, every
      changed file with an unallocated candidate takes its next one, subject
      to the per-file cap. Stop when the budget is exhausted and no further
      candidate can be taken for free, or when no file has an unallocated
      candidate. The invariant to hold is that no changed file receives a
      second related file while another candidate-bearing file has none.
- [x] 1.4 [req: related-context] Order files within each pass by ascending
      total candidate count, so a file with two candidates is served before a
      hub with twenty-seven. Break ties by path so the output is
      deterministic — the same diff must produce the same allocation, which
      `semdiff`'s existing subcommands all guarantee and a benchmark depends
      on.
- [x] 1.5 [req: related-context] Rank candidates within a changed file with
      importees above importers, each group ordered by the existing
      `_proximity_key`. Do not change `_proximity_key` itself.

## 2. Charge the review cap per distinct file

- [x] 2.1 [req: related-context] Charge a related file against the per-review
      cap only the first time it is selected. A file already selected for
      another changed file costs nothing further and may be listed even once
      the budget is spent, because listing it adds no reading for the review.
      Track the distinct selected set explicitly rather than inferring it from
      the entries.
- [x] 2.2 [req: related-context] Keep the per-file cap a per-file limit on
      what is listed: a changed file lists at most the mode's per-file cap of
      related files, whether or not those files were free.

## 3. Report the four counts

- [x] 3.1 [req: related-context] In the summary, report `related_files` as the
      distinct count charged against the cap and `related_edges` as the number
      of file-to-related pairs listed. Keep the existing `changed_files` and
      `truncated` fields.
- [x] 3.2 [req: related-context] Add `files_without_candidates` and
      `files_starved`. The first counts changed files the search found nothing
      to relate; the second counts files that had candidates and received none
      because the budget was spent. Do not collapse them into one number: a
      single count reads 7 on a healthy run of the benchmark's apilix PR and
      would be dismissed as a failure.
- [x] 3.3 [req: related-context] Keep the per-file `truncated` count meaning
      what it means today — candidates found for that file and not listed,
      whether dropped by the per-file cap or by the budget.

## 4. Tests

- [x] 4.1 [req: related-context] Add a test to
      `plugins/s/skills/review/tests/test_semdiff_files_context.py` that no
      changed file holds two related files while another candidate-bearing
      file holds none. Build a fixture with more candidate-bearing changed
      files than the cap can serve twice, so the fairness invariant is what
      the assertion rests on.
- [x] 4.2 [req: related-context] Add a test that the two zero reasons are
      reported separately: one changed file with no candidates and one starved
      by the budget, asserting each lands in its own count.
- [x] 4.3 [req: related-context] Add a test that a shared related file is
      charged once — several changed files relating to one module, asserting
      the module appears under each, that `related_edges` exceeds
      `related_files`, and that the distinct count is what the cap bounded.
- [x] 4.4 [req: related-context] Add a test that a file with few candidates is
      served before a hub within a pass, and a test that two runs over the
      same fixture produce identical allocations.
- [x] 4.5 [req: related-context] Prove the fairness test fails against the old
      allocation before trusting it. Temporarily restore the single running
      counter, watch the test fail, then restore the fair-share code and
      report that you did. Two tests in this series passed vacuously because
      nobody checked they could fail.

## 5. Version and verification

- [x] 5.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.265` to `0.6.266`.
- [x] 5.2 [req: *] Run `python3
      plugins/s/skills/review/scripts/semdiff.py related HEAD~1` and the
      `--mode max` form against this repository, and report the full summary
      block for each. `files_starved` must read 0.
- [x] 5.3 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      269-test baseline.
- [x] 5.4 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs266.log
      2>&1; tail -4 /tmp/bs266.log` — because its summary goes to stderr and
      a stdout-only pipe loses the verdict silently. Expect 3172 tests.
- [x] 5.5 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 5.6 [req: related-context] Confirm no prompt surface changed: `git diff
      --name-only` must not list `plugins/s/skills/review/SKILL.md` or
      `plugins/s/harness/bodies/review.md`. The caps and the subcommand's
      described behaviour are unchanged, so nothing either surface says
      becomes false, and the rendered harness body has one line of headroom
      left.
