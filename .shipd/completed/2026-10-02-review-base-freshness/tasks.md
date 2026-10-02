## 1. Engine: resolve the base

- [x] 1.1 [req: base-resolution] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, add a fixture that
      builds a bare origin repository, clones it, advances origin by three
      commits, and cuts `feature` from the advanced origin — so the clone's
      local `main` is three commits behind its remote-tracking counterpart.
      Add tests over it:
      `semdiff diff main feature` reports only `feature`'s files and emits a
      base naming the remote-tracking counterpart; `semdiff diff main` in the
      stale checkout with one edited file reports only that file; `semdiff diff
      refs/heads/main feature` resolves the base to the local branch's commit;
      a commit-id base in a remote-less repository resolves unchanged. Run the
      module and observe the four new tests fail.
- [x] 1.2 [req: base-resolution] In
      `plugins/s/skills/review/scripts/semdiff.py`, add a helper beside
      `resolve_endpoints` that returns a base's remote-tracking counterpart
      commit, or `None`. It returns `None` unless `git rev-parse --verify
      --quiet refs/heads/<base>` succeeds, then tries `git rev-parse
      --symbolic-full-name <base>@{upstream}` and falls back to
      `refs/remotes/origin/<base>`. It runs no fetch and writes nothing.
- [x] 1.3 [req: base-resolution] In `resolve_endpoints` in the same file, call
      that helper and use the counterpart's commit as the base for all three
      modes when it resolves; keep the given value for a qualified ref, commit
      id, or tag.
- [x] 1.4 [req: base-resolution] In `resolve_endpoints`, change working-tree
      mode so `old_ref` and the `diff_spec` entry become `git merge-base
      <resolved-base> HEAD` instead of the base itself. Confirm the 1.1 tests
      pass and the pre-existing tests in the module still pass.

## 2. Engine: disclose the endpoints

- [x] 2.1 [req: endpoint-disclosure] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, add tests asserting
      that `semdiff diff main feature` emits `base_given`, `base_sha`,
      `head_sha` and `merge_base` as 40-character commit ids; that `semdiff diff
      main` emits a null `head_sha` and a `merge_base` equal to the fork point;
      and that `semdiff diff main feature --linear` emits no `merge_base`. Run
      and observe them fail.
- [x] 2.2 [req: endpoint-disclosure] In `resolve_endpoints` in
      `plugins/s/skills/review/scripts/semdiff.py`, extend the returned `meta`
      dict with `base_given`, `base_sha`, `head_sha` and the mode-dependent
      `merge_base` described in 2.1. Confirm the 2.1 tests pass; `cmd_diff`,
      `cmd_files` and `cmd_lint` need no edit because all three splat `meta`.

## 3. Engine: doctor base probe

- [x] 3.1 [req: doctor-base-probe] In
      `plugins/s/skills/review/tests/test_semdiff_doctor.py`, add tests
      asserting that `semdiff doctor` in a clone whose local `main` is behind
      its remote-tracking counterpart prints a base line naming the behind
      count and the remedy
      and still exits zero while every required tool is present, and that a
      repository whose default branch has no remote-tracking counterpart prints
      a base line saying there is nothing to compare without changing the exit
      code. Run and observe them fail.
- [x] 3.2 [req: doctor-base-probe] In `cmd_doctor` in
      `plugins/s/skills/review/scripts/semdiff.py`, add the base probe after the
      tool loop: pick `main` else `master`, resolve its counterpart with the 1.2
      helper, and print the comparison using `git rev-list --left-right --count
      <base>...<counterpart>` for the ahead and behind counts. Under `--fix`,
      fetch that remote before comparing. Leave the `ok` flag and the exit code
      untouched. Confirm the 3.1 tests pass.

## 4. Poster: guard the base before any write

- [x] 4.1 [req: post-base-guard] In
      `plugins/s/skills/review/tests/test_review_gate.py`, give the `_review`
      helper a default `endpoints` object whose `merge_base` matches a new
      `FakeGit` runner's merge-base answer, extend `FakeGh` to answer
      `baseRefOid` and `headRefOid`, and add tests asserting that a mismatched
      `endpoints.merge_base` and an absent one each abort with no recorded `gh`
      write and a non-zero exit, while a matching one writes the summary
      comment, inline comments and status exactly as before. Run and observe the
      new tests fail.
- [x] 4.2 [req: post-base-guard] In
      `plugins/s/skills/review/scripts/review_gate.py`, add a `_default_git`
      runner beside `_default_gh` with the same `(rc, stdout, stderr)` signature,
      and thread a `git=_default_git` parameter through `post` and `_cmd_post`.
- [x] 4.3 [req: post-base-guard] In the same file, extend `_resolve_pr` to
      request `baseRefOid` and `headRefOid` alongside the fields it already
      asks for, and return them.
- [x] 4.4 [req: post-base-guard] In the same file, add the guard as the first
      statement of `post` after resolving the pull request and before
      `_upsert_summary`: compute the merge base of the pull request's base and
      head commits through the `git` runner, compare it with the payload's
      `endpoints.merge_base`, and raise `ReviewGateError` naming both values —
      or the missing field — on any mismatch. Confirm the 4.1 tests pass and the
      existing poster tests still pass.

## 5. Prose: state the rule on every surface

- [x] 5.1 [req: review-base-fetch, endpoint-disclosure] In
      `plugins/s/skills/review/SKILL.md`, add a short `Base freshness` block to
      the `Determine what to review` section, before any `diff`, `files`, or
      `lint` command: fetch the base's remote before the first `semdiff` call in
      every mode; the fetch writes remote-tracking refs only and never the
      working tree, the index, or a local branch; the engine resolves a short
      branch base to its remote-tracking commit, so no manual check is needed; a
      failed fetch becomes a could-not-verify entry rather than ending the
      review; a two-ref `lint` run records a could-not-verify entry naming that
      the linters read the checkout rather than the reviewed head; the skill
      never pulls, rebases, or checks out. Replace the
      parenthetical `fetch first` in the two-ref bullet with a pointer to that
      block. Add the resolved-endpoint line to the `Presentation` section
      directly under the effort score, and amend the `Read-only` guardrail to
      name the fetch's write scope.
- [x] 5.2 [req: post-base-guard] In
      `plugins/s/skills/review/references/posting.md`, change step 1 to request
      `baseRefOid` and `headRefOid` with the fields it already asks for, change
      step 2 to review as the two resolved commit ids with a preceding fetch of
      the pull request's head ref and its base branch, and state that the report
      names the base commit used. Add to step 5 that the poster aborts when the
      payload's merge base does not match the pull request's own.
- [x] 5.3 [req: endpoint-disclosure] In
      `plugins/s/skills/review/references/json-output.md`, add the `endpoints`
      object to the payload shape with `base_given`, `base`, `base_sha`, `head`,
      `head_sha`, `merge_base` and `mode`, and state that the poster rejects a
      payload lacking `endpoints.merge_base`.
- [x] 5.4 [req: review-base-fetch] In `plugins/s/harness/bodies/review.md`,
      extend step 1 with the same fetch-before-every-mode rule, the fetch's
      write scope, and the fork-point anchor for the default mode.
- [x] 5.5 [req: endpoint-disclosure] In
      `plugins/s/harness/references/review.md`, add the same `endpoints` object
      to its machine-payload section and the base resolution to its posting
      flow's step 1 and step 2.

## 6. Pin the prose and verify

- [x] 6.1 [req: review-skill-references] In
      `plugins/s/skills/review/tests/test_skill_references.py`, raise the
      `SKILL.md` line ceiling from 300 to 330 in `test_under_line_ceiling`, and
      add a test asserting the base-freshness block stays inline in `SKILL.md`.
- [x] 6.2 [req: review-base-fetch, endpoint-disclosure] In the same file, add a
      parity test class asserting that `SKILL.md` and
      `plugins/s/harness/bodies/review.md` both state the fetch-before-every-mode
      rule, and that `plugins/s/skills/review/references/json-output.md` and
      `plugins/s/harness/references/review.md` both name the same `endpoints`
      field set.
- [x] 6.3 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests` and confirm the whole module set passes.
- [x] 6.4 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` to the next patch release, since
      this change edits files under `plugins/s/` and the plugin cache snapshot
      is keyed by version.
