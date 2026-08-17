## 1. The polling bridge

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, update the gate
      template tests to the polling contract, failing against the current
      template: the `concurrency` group keyed on the pull request number
      with `cancel-in-progress: true`; `permissions` adding
      `pull-requests: read`; the `pull_request` path posting `pending` then
      polling the reviews API (20-second cycles, 15-minute bound) for the
      newest Copilot review whose `commit_id` equals the triggering head;
      the quiet exits on timeout and on a moved head; the polling body
      landing in a workspace file read back with `$(<file)` (asserting no
      env var carries it); and the `pull_request_review` path keeping its
      reviewer/head guards. Behavioral cases run the extracted script with
      a stubbed `gh` that serves scripted API responses: review found →
      pending then terminal status; head moved → pending only; timeout
      (stub never returns a matching review, poll interval overridable to
      keep the test fast) → pending only; verdict matrix (fix-required
      last line → failure; ship-it → success; quoted-markers-mid-text →
      fail-open success) reused on both paths.
- [x] 1.2 [req: gate-workflow-template] Rewrite the gate job in
      `plugins/s/integrations/copilot/copilot-review-gate.yml` per the
      delta requirement and `plan.md`'s workflow contract: single job
      serving both triggers; `pull_request` path posts `pending`, polls
      `gh api` for the reviews (paginated) and the PR's current head each
      cycle, writes the found review body to a workspace file and reads it
      with bash redirection; `pull_request_review` path classifies its
      `env:`-passed body; both share the existing anchored classification
      block (windowed trim, last-line equality, fix-required first,
      fail-open else). Keep the file-header commentary accurate (recursion
      suppression as the polling rationale, the no-pipe and no-env notes,
      timeout semantics). Make the 1.1 tests pass.

## 2. Docs corrections

- [x] 2.1 [req: copilot-review-guide] In `docs/copilot-review.md`: replace
      the bootstrap section (retract the default-branch claim — head-branch
      workflow files trigger both events' runs; what never fires is a run
      for Copilot-authored review submissions) with the polling design:
      rationale, poll bounds, timeout-leaves-pending with
      `review_gate.py post` as the manual out, runner-minutes cost. Add
      the private-repository prerequisites note (runner checkout failure
      → skill never loads → reviews classify fail-open; verify the
      checkout once; session flow as the fallback gate). Keep the fork
      read-only-token limit and the coexistence paragraph.

## 3. Release

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.131` -> `0.6.132`.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from
      the worktree root and confirm it passes without `textual` or
      `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 46 | 30.3k |
| Edit | 13 | 26.2k |
| Write | 9 | 17.1k |
| (no tool) | 0 | 5.9k |
| Read | 20 | 3.5k |
| Agent | 2 | 1.3k |
| SendMessage | 1 | 675 |
| **Total** | 91 | 84.9k |
