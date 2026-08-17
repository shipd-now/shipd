## 1. Gate strictness knob

- [x] 1.1 [req: gate-workflow-template] In
      `plugins/s/skills/build/tests/test_copilot_verb.py`, add failing
      tests: the gate job's `env` reads
      `${{ vars.SHIPD_GATE_FAIL_OPEN }}` into `SHIPD_GATE_FAIL_OPEN`;
      behaviorally (extracted script, existing stubs), with the variable
      `false` a no-marker text leaves only `pending` (no terminal status)
      and logs the no-verdict condition on all three classify paths (CLI
      output, polled review, review event), while marker-carrying texts
      still post `failure`/`success`; with the variable unset or `true`
      the fail-open `success` posts exactly as today.
- [x] 1.2 [req: gate-workflow-template] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, add the
      job-level env read and branch the shared classification block's
      no-marker case on `[[ "${SHIPD_GATE_FAIL_OPEN:-true}" == "false" ]]`
      (strict: log and exit 0; default: today's fail-open post), updating
      the header commentary. Make the 1.1 tests pass.

## 2. Fail-soft setup workflow

- [x] 2.1 [req: setup-workflow-template] In `test_copilot_verb.py`, add
      failing `WorkflowTemplateTest` cases for
      `plugins/s/integrations/copilot/copilot-code-review.yml`: the
      checkout step carries `continue-on-error: true` and an `id`; the
      difftastic and ripgrep steps each carry an `if` on that step's
      outcome being `success`; the difftastic script tests its located
      binary path for emptiness and fails with a message before any
      `install` invocation.
- [x] 2.2 [req: setup-workflow-template] Edit
      `plugins/s/integrations/copilot/copilot-code-review.yml`
      accordingly, keeping the single `copilot-setup-steps` job contract
      and updating its header comment. Make the 2.1 tests pass.

## 3. Engine: empty is not absent

- [x] 3.1 [req: structural-diff] In
      `plugins/s/skills/review/tests/test_semdiff_diff.py`, add a failing
      test: in a repo where one committed non-empty file is emptied and
      one committed empty file gains content, `semdiff diff HEAD` reports
      kind `modified` for both (currently `deleted` and `added` — verified
      live).
- [x] 3.2 [req: structural-diff] In
      `plugins/s/skills/review/scripts/semdiff.py`, make the blob reader
      distinguish absent-at-ref from present-but-empty (a sentinel, not
      the empty string) and base kind classification on presence,
      preserving the whitespace-only filter. Make the 3.1 test pass.

## 4. Engine: extract regular files only

- [x] 4.1 [req: doctor-provisioning] In
      `plugins/s/skills/review/tests/test_semdiff_doctor.py`, add a
      failing test: the release-binary extraction helper refuses an
      archive whose only `difft` member is a symlink (clear error, nothing
      extracted) and extracts a regular-file `difft` member.
- [x] 4.2 [req: doctor-provisioning] In
      `plugins/s/skills/review/scripts/semdiff.py`, require the selected
      tar member to satisfy `isreg()` before extraction. Make the 4.1 test
      pass.

## 5. Docs

- [x] 5.1 [req: copilot-review-guide] In `docs/copilot-review.md`, add the
      strictness-knob subsection to the merge-gate section
      (`SHIPD_GATE_FAIL_OPEN`, fail-open default, strict semantics on
      every classify path, `gh variable set` enable path,
      `review_gate.py post` as the strict manual out) and extend the
      private-repository note with the fail-soft setup behavior.

## 6. Release

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.133` -> `0.6.134`.
- [x] 6.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      the review engine's suite (`python3 -m unittest discover -s
      plugins/s/skills/review/tests`) from the worktree root, confirming both
      pass without `textual` or `pydantic` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 109 | 49.5k |
| Edit | 34 | 26.3k |
| Read | 37 | 10.6k |
| (no tool) | 0 | 8.7k |
| SendMessage | 6 | 3.9k |
| Write | 1 | 2.3k |
| Agent | 4 | 1.3k |
| WebFetch | 1 | 426 |
| **Total** | 192 | 103.0k |
