## 1. Anchor the verdict parse

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, rewrite the
      `GateWorkflowTemplateTest` verdict assertions to the anchored
      contract, failing against the current template: the bridge script
      extracts the body's last non-empty line with pure-bash parameter
      expansion (carriage returns and surrounding whitespace tolerated)
      and compares it for **equality** (`[[ "$..." == '<marker>' ]]`, no
      `*` wildcards around the marker) against both markers; keep the
      no-pipe regression test; drop or replace the anywhere-substring
      assertions. Add behavioral cases exercising the extracted script
      under bash with a stubbed `gh` (the file's existing style): a body
      quoting both markers mid-text ending with the ship-it marker line →
      `success`; a body ending with the fix-required marker line (also
      with trailing CRLF/whitespace) → `failure`; a body quoting markers
      only mid-text → fail-open `success`; an empty body → fail-open
      `success`.
- [x] 1.2 [req: gate-workflow-template] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, replace
      the two anywhere-substring tests in the bridge job with the
      last-non-empty-line extraction (parameter expansion only: strip
      carriage returns, trim trailing whitespace/newlines, take the
      substring after the last newline, trim that line's surrounding
      whitespace) and equality comparisons, `fix-required` first; update
      the step's explanatory comment to record why the parse is anchored
      (a review may quote the markers) alongside the existing no-pipe
      rationale. Make the 1.1 tests pass.

## 2. Bootstrap documentation

- [x] 2.1 [req: copilot-review-guide] In `docs/copilot-review.md`, update
      the merge-gate section's verdict table/text to the last-line
      anchoring (quoted markers never count) and add a short bootstrap
      subsection: `pull_request_review` workflows run from the default
      branch's workflow file, so the bridge never fires on the pull
      request that first installs the gate (its `pending` job does fire);
      post that one PR's `semantic-review` status via the session flow
      (`review_gate.py post`) or a one-time admin bypass; every later PR
      is unaffected.

## 3. Release

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.127` -> `0.6.128`.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from
      the worktree root and confirm it passes without `textual` or
      `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 132 | 84.5k |
| Edit | 31 | 32.7k |
| Write | 5 | 11.6k |
| (no tool) | 0 | 10.4k |
| Read | 38 | 5.6k |
| SendMessage | 4 | 4.9k |
| Agent | 4 | 2.1k |
| **Total** | 214 | 151.8k |
