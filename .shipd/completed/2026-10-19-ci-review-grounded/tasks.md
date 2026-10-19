## 1. Gate test harness

- [x] 1.1 [req: gate-review-grounding] In `plugins/s/skills/build/tests/test_copilot_verb.py`, add an `ENGINE_STUB` Python script beside `GIT_STUB`. It appends its argv, one argument per line, to the file named by `$ENGINE_ARGS`. On `files` it prints `$STUB_DIR/engine-files` when that file exists, else `{"summary": {"files": 3, "cohorts": 1}, "cohorts": []}`. On `diff` it prints `{"files": []}`. It exits with the integer in `$STUB_DIR/engine-code` when that file exists, else 0. In `GateScriptCase.setUp`, write it to the checkout path ".github/skills/code-review/scripts/semdiff.py" under `self.tmp`.
- [x] 1.2 [req: gate-review-grounding] In `plugins/s/skills/build/tests/test_copilot_verb.py`, extend `GIT_STUB` so that when the last argument of `cat-file` or `show` ends in `semdiff.py`, it serves `$STUB_DIR/base-engine` (exit 0) when that file exists, else exits 128 with a "does not exist" message. Leave the existing skill-path behaviour unchanged. Add `"base-engine"`, `"engine-files"`, and `"engine-code"` to `SCRIPTED`.
- [x] 1.3 [req: gate-review-grounding] In `plugins/s/skills/build/tests/test_copilot_verb.py`, change `gate_script` to copy the runner's step-output binding. After the run body of the step whose text carries `id: grounding`, insert `GROUNDING_OUTCOME="$(sed -n 's/^outcome=//p' "$GITHUB_OUTPUT" | tail -n 1)"; GROUNDING_FILES="$(sed -n 's/^files=//p' "$GITHUB_OUTPUT" | tail -n 1)"; export GROUNDING_OUTCOME GROUNDING_FILES`.
- [x] 1.4 [req: gate-review-grounding] In `plugins/s/skills/build/tests/test_copilot_verb.py`, extend `gate()`:
      - Point `GITHUB_OUTPUT` at a fresh empty `github-output` file in `self.tmp`, and set `ENGINE_ARGS` to `engine-args` in `self.tmp`. Remove both files before each run.
      - Add keyword parameters `engine_files=None` (an int: plant `engine-files` with that summary count), `engine_code=None`, `base_engine=None` (text: plant `base-engine`), and `fast_pass=""` (sets `SHIPD_FAST_PASS` in the env).

## 2. Gate tests (written to fail first)

- [x] 2.1 [req: gate-review-grounding] In `plugins/s/skills/build/tests/test_copilot_verb.py`, add a `GateGroundingTest(GateScriptCase)` class with the CLI secret set. Add tests for:
      - The engine args hold `files`, then the base SHA `"0"*39+"b"`, then `self.HEAD`, and the same order for `diff`.
      - `github-output` holds `outcome=ok` and `files=3`.
      - The prompt names "shipd-copilot-review-semdiff-files.json" and "shipd-copilot-review-semdiff-diff.json" and tells the reviewer not to run `files` or `diff`.
      - With `base_engine` planted, `git show` was asked for a path ending "scripts/semdiff.py" at `BASE_COMMIT`. With it absent, the stdout log says the head copy was used.
- [x] 2.2 [req: gate-review-grounding] In `GateGroundingTest`, add the zero-file test. Set `engine_files=0`, a one-entry `files` list, and `cli_out` ending in the ship-it marker, with `expect_failure=True` and the fail-open default. Assert:
      - The last posted status is `pending` with a description starting `Review not grounded:`.
      - No status is `success`.
      - Exactly one review was posted, its event is `COMMENT`, and its body starts with `**Not a verdict.**`.
      - with `fast_pass="true"`, `comments-args` records no `pr merge` call.
- [x] 2.3 [req: gate-review-grounding] In `GateGroundingTest`, add the remaining fail-closed cases:
      - `engine_code=1`, `expect_failure=True`: `cli_args()` is empty, the last status is `pending` with a `Review not grounded:` description, and no review was posted.
      - `engine_files=0` with `files=[]` and a ship-it `cli_out`: the statuses are `["pending", "success"]` and the review event is `APPROVE`.
      - `fail_open="true"` with a zero-file grounding still ends `pending`.
- [x] 2.4 [req: gate-report-extraction] In `plugins/s/skills/build/tests/test_copilot_verb.py`, add a `GateReportExtractionTest(GateScriptCase)` class with the secret set. Add tests for:
      - `cli_args()` contains `-s`.
      - The fixture is the PR 24-shaped output: narration, `● Read …` with `  │ …` and `  └ …` lines, then `## Findings: ✅ Ship it`, `No problems found.`, `**Verdict: Ship it**`, the ship-it marker, then trailing narration. The posted review body's first line is `## Findings: ✅ Ship it`, it contains no `●`, and the status is `success`.
      - With output that has no `## Findings` line, the body keeps the prose lines and drops the block lines.
      - A fix-required marker inside the sliced report still posts `failure`.
- [x] 2.5 [req: gate-review-grounding, gate-report-extraction] Run `python3 -m unittest plugins/s/skills/build/tests/test_copilot_verb.py` from the worktree root, and confirm the tests from 2.1–2.4 fail. Confirm the existing tests still pass, or fail only because the harness now expects the grounding step.

## 3. Gate workflow

- [x] 3.1 [req: gate-review-grounding] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, insert the step "Ground the review in the engine's own output", `id: grounding`, between the difftastic install step and the reviewer step. Give it the reviewer step's `if:` and env `EVENT_NAME`, `HEAD_SHA`, `BASE_SHA`, `BASE_REF`, and no secret or token. Its script, under `set -euo pipefail`:
      - Act only when `EVENT_NAME` is `pull_request` and `COPILOT_CLI_REVIEWER` is `true`.
      - Fetch `BASE_SHA` and the base branch best-effort, as the reviewer step does.
      - Resolve `origin/$BASE_REF^{commit}`. If the base tree carries ".github/skills/code-review/scripts/semdiff.py", `git show` it into "$RUNNER_TEMP/shipd-copilot-review-semdiff.py"; otherwise copy the checkout's copy there and echo that the head copy is used. An unresolved base or unreadable file sets outcome `failed`.
      - Run `python3 <engine> files "$BASE_SHA" "$HEAD_SHA"` and the `diff` equivalent into the two grounding files named in plan.md.
      - Read `summary.files` with `python3 -c`.
      - Append `outcome=` and `files=` to `$GITHUB_OUTPUT`.
      - Never `exit` non-zero. Echo a line naming `semantic-review` on failure.
- [x] 3.2 [req: gate-review-grounding, gate-report-extraction] In the reviewer step of `plugins/s/integrations/copilot/copilot-review-gate.yml`, make four changes:
      - Bind `GROUNDING_OUTCOME: ${{ steps.grounding.outputs.outcome }}` and `GROUNDING_FILES: ${{ steps.grounding.outputs.files }}`.
      - When `GROUNDING_OUTCOME` is not `ok`, echo that the review is skipped and do not run `copilot`.
      - Replace the prompt's "Diff $BASE_SHA against the reviewed commit $HEAD_SHA." sentence with one that names the two grounding files' full paths. It says the workflow ran `files` and `diff` for base $BASE_SHA and head $HEAD_SHA, tells the reviewer to read them and not run those subcommands itself, and keeps `context` lookups allowed.
      - Add `-s` to the `copilot -p` invocation.
- [x] 3.3 [req: gate-review-grounding] In the publisher step of `plugins/s/integrations/copilot/copilot-review-gate.yml`, make these changes:
      - Bind the same two `GROUNDING_*` outputs in its env.
      - On the CLI path, do the paginated changed-files read into `files_file` once, before the body-file check. Count its entries with `"$py_bin"` and treat a failed read as unknown. Remove the duplicate read inside the `comment_file` block.
      - Compute the ungrounded condition from plan.md. When it holds:
        - Post `pending` with "Review not grounded: the review engine failed on this commit; no verdict posted." or "Review not grounded: the review engine saw 0 of N changed files; no verdict posted.".
        - Skip classification, fast-pass, and the fail-open branch, and force `review_event=COMMENT`.
        - If the body file exists, prepend a `**Not a verdict.** …` notice line naming the cause to the cleaned body and publish it.
        - Then `exit 1`.
- [x] 3.4 [req: gate-report-extraction] In the publisher step of `plugins/s/integrations/copilot/copilot-review-gate.yml`, on the CLI path, run a `"$py_bin"` heredoc right after the body-file check. It applies the extraction rule in plan.md (marker anchor, last `## Findings` line, tool-block fallback) and writes "$RUNNER_TEMP/shipd-copilot-review-report.md". Read `body` from that file and set `comment_file` to it.
- [x] 3.5 [req: gate-review-grounding, gate-report-extraction] Update the header comment block of `plugins/s/integrations/copilot/copilot-review-gate.yml` (lines 13-23 and the trust-boundary bullets) to describe the grounding step, the fail-closed rule, the base-pinned engine, and the report extraction. Run `python3 -m unittest plugins/s/skills/build/tests/test_copilot_verb.py` and confirm it reports OK.

## 4. Contract

- [x] 4.1 [req: skill-supplied-grounding] In `plugins/s/skills/build/tests/test_copilot_verb.py` `SkillTemplateTest`, add a test that the template says supplied `files` and `diff` output is read instead of re-running them, and mentions failing closed on an empty grounding. Run it and observe it fail.
- [x] 4.2 [req: skill-supplied-grounding] In `plugins/s/integrations/copilot/SKILL.md`, after the "Compare the pull request's base against its head" paragraph (lines 36-37), add the supplied-grounding paragraph from plan.md, without emoji. Confirm the 4.1 test passes.

## 5. Room wake

- [x] 5.1 [req: room-wake-reply-cleaning] In `plugins/s/skills/room/tests/test_room_wake.py` `ReplyScriptTest`, add the three scenarios of `room-wake-reply-cleaning`. Run the suite and observe them fail.
- [x] 5.2 [req: room-wake-reply-cleaning] In `plugins/s/integrations/copilot/room-wake.yml`, in the reply job's Python block, drop tool-call blocks from `lines` before the first `trim(lines)`. A block is a line starting `"● "` plus the following lines whose `lstrip()` starts with `"│"` or `"└"`. Run `python3 -m unittest discover -s plugins/s/skills/room/tests` and confirm OK.

## 6. Docs and version

- [x] 6.1 [req: ci-review-grounded-ships] In `docs/copilot-review-reference.md` "The CLI reviewer mode":
      - Add a step to the numbered list: the gate runs the base ref's engine with the base first and head second, and hands the outputs to the reviewer.
      - Add a bullet on the fail-closed rule: `pending`, a "Review not grounded" description, a COMMENT review, and a failed job.
      - Note that the posted body is cut down to the report.
- [x] 6.2 [req: ci-review-grounded-ships] In `docs/copilot-review.md` section 6, add a bullet saying a repository gated earlier picks up new gate behaviour, such as grounding, by running `/s:gate update`. In `docs/room-wake-reference.md` "The reply marker", add one sentence saying the reply job strips tool-call transcript blocks before posting.
- [x] 6.3 [req: ci-review-grounded-ships] Run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review.md docs/copilot-review-reference.md docs/room-wake-reference.md`. It must exit 0, and the edits must add no new warning.
- [x] 6.4 [req: ci-review-grounded-ships] Set `version` in `plugins/s/.claude-plugin/plugin.json` to one patch above the value on "origin/main" at build time, and confirm `python3 plugins/s/skills/build/scripts/version_guard.py --base main --head HEAD` exits 0.

## 7. Verification

- [x] 7.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests`, `python3 -m unittest discover -s plugins/s/skills/review/tests`, and `python3 -m unittest discover -s plugins/s/skills/room/tests`. Grep each run's stderr for `OK` or `FAILED`, and confirm all three report OK.
