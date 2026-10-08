## 1. Land the recovered test and its spec

- [x] 1.1 [req: related-context] Confirm the recovery is already applied in the
      worktree: `PerFileCapBoundsFreeCandidatesTest` is present in
      `plugins/s/skills/review/tests/test_semdiff_files_context.py`, the review
      suite runs 275 tests green, and that test passes when run alone. The
      cherry-pick of `e6e085c` was performed by the orchestrator before this
      change was authored, so verify rather than re-apply.
- [x] 1.2 [req: related-context] Confirm the test would actually fail if the
      per-file cap stopped applying to free candidates. Temporarily move the
      allocator's per-file cap check after its free-or-paid branch in
      `plugins/s/skills/review/scripts/semdiff.py`, watch this test fail,
      then restore the original ordering and leave `semdiff.py` byte-identical
      to `main`. Report the failure you saw and confirm with `git diff
      --name-only` that `semdiff.py` is unchanged. A test recovered for being
      the only guard on an ordering must be shown to guard it.
- [x] 1.3 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.266` to `0.6.267`.

## 2. Verification

- [x] 2.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      274-test baseline on `main`.
- [x] 2.2 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs267.log 2>&1;
      tail -4 /tmp/bs267.log` — and report the verdict verbatim.
- [x] 2.3 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 2.4 [req: related-context] Confirm `git diff --name-only main` lists only
      the test file and `plugin.json`. Any other path means the recovery picked
      up something it should not have.
