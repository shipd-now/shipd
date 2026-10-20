# gate-thread-resolve-model
Status: complete
Planned-at: 73156d3ce5cd7c38ac953d31cd0771c4a89ffd93
Gated-hash: 1e469edc040f

## Idea

The CLI reviewer path of the review gate resolves its own superseded review threads when it publishes a new grounded review, and it names the model that reviewed, which a repository variable can now choose.

### Motivation

On unkannybanny PR 28 the gate approved the fixed head, but its earlier inline thread stayed unresolved, so a repository requiring conversation resolution kept the pull request blocked until a human resolved it. Nobody can tell which model reviewed, because the CLI runs with no `--model` and `-s` drops the run stats.

### Details

- **Superseded threads.** Before the posting step submits an `APPROVE` or `REQUEST_CHANGES` review, it resolves every unresolved review thread whose first comment the gate's own identity wrote on an earlier commit. A grounded review is a full re-review, so it supersedes those threads and re-anchors any finding still present.
- **Model knob.** An optional repository variable `SHIPD_REVIEW_MODEL`. When it is non-empty, the CLI gets `--model` with its value. The posted body's footer gains a line naming the model, or "Copilot CLI default" when the variable is unset.
- **Docs, contract, version.** `docs/copilot-review-reference.md` and the template `SKILL.md` describe both, and the plugin version moves up one patch.

Affected capability: `copilot-review-skill` (two new requirements). Files: `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/integrations/copilot/SKILL.md`, `plugins/s/skills/build/tests/test_copilot_verb.py`, `docs/copilot-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`. Repositories with the gate get it through `/s:gate update`.

### Non-goals

- No thread resolution on a `COMMENT` review, on the ungrounded path, or on the poll and review-event paths.
- No resolution of threads written by anyone but the gate.
- No model selection on the poll fallback, whose Copilot surface exposes none.
- No change to `review_gate.py` or its `review_footer`.

## Implementation

- **Where it runs.** Thread resolution lives in the posting step only, the one step holding `github.token`, and every call goes through `"$gh_bin"`. It runs inside the existing `if [[ -n "$comment_file" ]]` block, after the payload builder and before the first review POST, guarded by `review_event` being `APPROVE` or `REQUEST_CHANGES` and `ungrounded` being empty. Resolving first means the new decision lands on a pull request with no stale gate thread. A decision GitHub later refuses still went out as a full re-review body, so the threads stay superseded. Rejected: resolving after the POST, which leaves a window where the approval sits beside the stale thread.
- **The query.** One call: `"$gh_bin" api graphql` with `-f query=` a `reviewThreads(first: 100)` query on the pull request, selecting each thread's `id`, `isResolved`, and the first comment's `author { login }` and `originalCommit { oid }`. Variables: `-f owner="${REPO%%/*}"`, `-f name="${REPO#*/}"`, `-F number="$PR_NUMBER"`. The output goes to the workspace file "shipd-copilot-review-threads.json" under the runner temp directory. Only the first 100 threads are read. Rejected: `--paginate`, whose concatenated output needs a second parser for a case no pull request here has reached.
- **The selection.** A `"$py_bin"` heredoc reads that file and writes thread ids, one per line, to "shipd-copilot-review-stale-threads.txt". It selects a thread when `isResolved` is false, its first comment's author login is "github-actions" or "github-actions[bot]", and that comment's `originalCommit.oid` is not `HEAD_SHA`. A missing `originalCommit` counts as an earlier commit. GraphQL reports a bot login without the "[bot]" suffix that REST carries, so both spellings are the gate's identity. The identity is a literal, the same `github-actions[bot]` the event mapping already names. Rejected: a `viewer` query, one more call whose behavior under the workflow token is not verified here. Unparseable JSON exits nonzero.
- **The mutation.** For each id, `"$gh_bin" api graphql -f query=` a `resolveReviewThread(input: {threadId: $threadId})` mutation with `-f threadId=<id>`, output discarded. Success logs "Resolved superseded gate review thread <id>.".
- **Failures warn.** A failed query, a failed selection, or a failed mutation prints a `::warning::` line and moves on. None changes the status, the review event, or the step's exit code. The status was posted earlier, so the verdict cannot depend on these calls.
- **Model binding.** Both the CLI step and the posting step bind `SHIPD_REVIEW_MODEL: ${{ vars.SHIPD_REVIEW_MODEL }}` in their own step `env:`, the way the posting step re-binds `SHIPD_GATE_FAIL_OPEN`, so a `$GITHUB_ENV` write cannot change what the CLI runs or what the footer claims.
- **The CLI flag.** The CLI step builds `model_args=()` and sets it to `(--model "$SHIPD_REVIEW_MODEL")` when the variable is non-empty. The call passes `${model_args[@]+"${model_args[@]}"}` after `-s`, which expands to nothing for an empty array under `set -u` on the bash 3.2 that macOS ships.
- **The footer.** `footer(files)` stays byte-for-byte as it is, so its parity test against `review_gate.review_footer` still holds. A new `model_line()` in the payload builder returns "Model: " plus the variable's value with whitespace collapsed, or "Model: Copilot CLI default" when that is empty. A new `stats(files)` returns `footer(files) + [model_line()]`, or nothing when `footer(files)` is empty, and the builder folds it where it folded `footer(files)`. The model line therefore sits directly below the stat line. A diff that could not be read still appends nothing, which keeps the existing "Unreadable diff appends nothing" scenario true, and an ungrounded review carries neither line, as today.
- **Tests.** `plugins/s/skills/build/tests/test_copilot_verb.py`: the `GH_STUB` gains a `graphql` branch. It logs each call's arguments to `$GH_GRAPHQL`. A mutation logs the thread id to `$GH_RESOLVED` and `resolve <id>` to `$GH_ORDER`, or exits 1 for an id listed in the scripted "resolve-fail" file. A query exits 1 when "threads-fail" is scripted, and otherwise prints the scripted "threads" file or an empty thread list. A review POST appends `review` to `$GH_ORDER`. `gate()` gains `threads`, `threads_fail`, `resolve_fail`, and `review_model` (`None` drops the variable). A new `GateThreadResolveTest` and `GateReviewModelTest` drive the scenarios, and `GateWorkflowTemplateTest` gains the static binding checks.
- **Docs.** `docs/copilot-review-reference.md` sits at the 250-line cap. The new facts go into existing bullets of "The CLI reviewer mode" and "Tokens, permissions, and the session flow", plus a short `SHIPD_REVIEW_MODEL` bullet. The "No repository-side model selection" limit is narrowed to the poll fallback. Wrapped lines nearby are merged to stay at or under 250. `docs_lint.py` must exit 0.
- **Contract.** In `plugins/s/integrations/copilot/SKILL.md`, the sentence about the posting step's stat line gains "and a `Model:` line naming the reviewing model", and the "No repository-side model selection" bullet says the CLI reviewer reads `SHIPD_REVIEW_MODEL`.

Risk: the workflow token may lack the right to resolve a thread in some repositories. The warning path covers it: the merge stays blocked exactly as today and the log says why.

## Readiness attestation

### Problem and motivation

Stale gate threads block merges under required conversation resolution, and the reviewing model is invisible.

Evidence:

- unkannybanny PR 28, as reported by the user: the gate's fix-required inline thread stayed unresolved after the gate approved the next head, and the pull request stayed BLOCKED.
- `plugins/s/integrations/copilot/copilot-review-gate.yml:509`: `copilot -p "$prompt" -s` with no `--model`.

### Scope and non-goals

The scope is the CLI reviewer's CLI step and posting step, the contract template, one test file, one doc, and the version. The poll paths and `review_gate.py` are out.

Evidence:

- In scope: `plugins/s/integrations/copilot/copilot-review-gate.yml:353-530` (CLI step) and `:977-1289` (review publication), `plugins/s/integrations/copilot/SKILL.md:141-143,269-272`.
- Out of scope: `plugins/s/skills/review/scripts/review_gate.py:350`, whose `review_footer` the parity test in `plugins/s/skills/review/tests/test_skill_references.py:1634` pins the workflow's `footer` against.

### Affected capabilities and files

One capability gains two requirements; five files change.

Evidence:

- Capability `copilot-review-skill`: new requirements `gate-resolves-superseded-threads` and `gate-review-model`.
- Files: `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/integrations/copilot/SKILL.md`, `plugins/s/skills/build/tests/test_copilot_verb.py`, `docs/copilot-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: "npx -y @github/copilot@1.0.80 --help" exits 0 and lists `--model <model>`, "Set the AI model to use", beside `-s, --silent`. The pinned version therefore takes the flag.
- Runnable premise: `wc -l docs/copilot-review-reference.md` prints 250, the cap.

### No open task-shaping decision

Every decision is settled in Implementation under the user's pre-approved defaults for this batch; none remain.

Evidence:

- Ordering (resolve before the POST), identity (both login spellings), the 100-thread bound, warn-only failures, footer placement, and step-level binding are each recorded above with the rejected alternative where one exists.
