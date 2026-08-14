## 1. Poster engine

- [x] 1.1 [req: gate-poster, required-check-protect, gate-test-coverage] Add
      `plugins/s/skills/review/tests/test_review_gate.py` with an injectable
      fake-`gh` runner seam covering: marker comment create vs in-place
      update (exactly one marker comment after a re-post), RIGHT-side
      commentable-line computation from `pulls/{n}/files` patch text, inline
      anchoring of an in-diff finding and summary folding of an out-of-diff
      finding, status payloads (`success` for verdict `pass`, `failure`
      otherwise, context `semantic-review`), the retry-without-inline
      fallback on a rejected review POST, and `protect` add / `--remove` /
      already-present idempotency preserving other contexts. Run it and
      observe it fail — `review_gate.py` does not exist yet.
- [x] 1.2 [req: gate-poster] Add
      `plugins/s/skills/review/scripts/review_gate.py` (stdlib-only, all
      network through an injectable `gh` command runner) with a `post <pr>
      --from <path|->` subcommand: load the review JSON; resolve the PR's
      head SHA and repo via `gh pr view`/`gh api`; render the summary body
      (marker `<!-- am-semantic-review -->`, verdict header, effort,
      `# | rating | details` table, unanchorable findings under "Additional
      findings"); upsert the marker comment; compute commentable lines from
      `pulls/{n}/files` and post one `COMMENT` review with anchored inline
      comments, retrying once without inline on rejection; set the
      `semantic-review` commit status on the head SHA with the summary
      comment as target URL.
- [x] 1.3 [req: required-check-protect] In the same script, add the
      `protect [--remove]` subcommand: GET the default branch's protection,
      union or remove `semantic-review` in
      `required_status_checks.contexts`, PATCH only that object, and exit
      zero unchanged when already in the desired state.
- [x] 1.4 [req: gate-test-coverage] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and make the whole review suite
      pass with no network access.

## 2. Autopilot review stage

- [x] 2.1 [req: pipeline-stage-execution] Extend
      `plugins/s/skills/build/tests/test_autopilot.py` via the existing
      injectable `session_fn`/`command_fn` seams: the `review` stage is
      driven after `build` (no longer "not yet automated"), its grade passes
      when the fake combined-status command reports `semantic-review` =
      `success` on the head SHA, a persistent failing status exhausts three
      strikes and parks the member as `needs-human`, and a skipped review
      entry is honored. Run and observe the new cases fail.
- [x] 2.2 [req: pipeline-stage-execution] In
      `plugins/s/skills/build/scripts/autopilot.py`: add `review` to
      `DRIVEN_STAGES` and delete `NOT_AUTOMATED_STAGES` and its loop branch;
      add a `_review_grade(cwd, member)` that reads the PR head SHA
      (`gh pr view change/<member> --json headRefOid`) and passes iff
      `gh api repos/{owner}/{repo}/commits/{sha}/status` shows context
      `semantic-review` with state `success`; wire it in `_make_session_fn`;
      extend `_stage_prompt` with the review prompt — run `/s:review` on
      `change/<member>` vs `main`, post via `review_gate.py post`, and on a
      `changes-requested` verdict fix the findings, push, and re-review
      until the status is green. Confirm the 2.1 cases pass.

## 3. Skill and docs

- [x] 3.1 [req: skill-post-flow] Add a "Posting to a PR (the gate)" section
      to `plugins/s/skills/review/SKILL.md`: only on an explicit user or
      driving-session request, resolve the PR (`gh pr view <branch>`),
      review base vs head with merge-base semantics, emit the `--json`
      object to a temp file, run `review_gate.py post`, and report the
      posted status state and summary comment URL; never post without an
      explicit request.
- [x] 3.2 [req: *] Update `AGENTS.md`'s ship-via-PR section: auto-merge now
      waits on both `ci` and `semantic-review`, so after `gh pr create` run
      the `/s:review` post flow on the PR (and re-post after any new
      push); note the poster script location.
- [x] 3.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.5.0 → 0.5.1.

## 4. Bootstrap and verification

- [x] 4.1 [req: skill-post-flow, gate-poster] After this change's PR is
      opened: run the `/s:review` post flow on it — review
      the change/semantic-review-gate branch vs main, post the summary, inline
      comments, and `semantic-review` status to the PR — and confirm the
      status is green (fix findings, push, and re-post if not).
- [x] 4.2 [req: required-check-protect] Verify `protect`'s add/remove/idempotency behavior through its unit tests (GET current protection, union/remove `semantic-review`, PATCH only `required_status_checks` preserving `strict` and other contexts), and record in the build summary that the live flip on this repository's default branch is deferred to the orchestrator's ship-time bootstrap (PR opened, `semantic-review` posted green on it, then `protect` flips the contexts) — the flip must never run while PRs without a posted status are in flight.
- [x] 4.3 [req: *] Verification barrier: full engine + review unittest suites pass; the poster is proven against a throwaway draft PR (summary upsert, anchored inline comment, `semantic-review` commit status, idempotent re-post) with that PR deleted afterward; this repository's live default-branch protection is confirmed UNCHANGED (contexts still `ci` only — the flip belongs to the orchestrator's ship-time bootstrap); `AGENTS.md` and the plugin version reflect the change.
