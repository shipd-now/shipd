# gate-resolve-job
Status: verified
Theme: reliability
Planned-at: 5d1590fa88cd50d4bf2cfb4967413c2edc0abc63
Gated-hash: 26ff93c08a71

## Idea

The review gate resolves its superseded review threads in a second job that runs after the grounded decision review is posted, and that job alone holds the "contents: write" token the GraphQL mutation needs.

### Motivation

On unkannybanny PR 32 (run 39377558198) every "resolveReviewThread" call from the gate failed with "Resource not accessible by integration", so the gate's old threads stayed open and a repository requiring conversation resolution stayed blocked after the gate approved. Granting "contents: write" to the gate job would hand a write token to the job where the Copilot CLI runs over an untrusted diff, and resolving before the post also loses threads whenever that post fails.

### Details

- The posting step no longer resolves threads. After a decision review (APPROVE or REQUEST_CHANGES) posts, it sets the step outputs "resolve_threads=true" and "head_sha", which the "gate" job exports as job outputs.
- A new job "resolve-threads" ("needs: gate") runs only on a "pull_request" event when those outputs say so and "head_sha" is the event's head. Its job-level permissions are "contents: write" and "pull-requests: write". It checks out nothing and runs only the existing thread query, selection, and resolve calls.
- The workflow-level permissions, which the "gate" job keeps, stay "contents: read", "statuses: write", "pull-requests: write".
- Tests, `docs/copilot-review-reference.md`, and the plugin version (0.6.339) follow.

Affected capability: `copilot-review-skill` (requirement "gate-resolves-superseded-threads" modified). Repositories get it through "/s:gate update".

### Non-goals

- No change to which threads are selected, the 100-thread bound, or warn-and-continue on a failed call.
- No PAT or GitHub App token for resolution, and no change to the session flow's `review_gate.py resolve`.
- No change to the concurrency group, the poll path, or the review-event path.

## Implementation

- **Files.** `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/skills/build/tests/test_copilot_verb.py`, `docs/copilot-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`. `shipd copilot` compares the installed file to the template by content and ownership marker only (`plugins/s/bin/shipd:2026-2034`), so no install machinery changes.
- **Posting step.** Gains "id: verdict". The whole resolution block (query, selection heredoc, loop) is deleted from it. A shell variable "decision_posted" starts empty; it is set to "true" when the anchored POST or the plain-body retry succeeds and "review_event" is not COMMENT. The neutral COMMENT fallback never sets it: that review carries no decision and no inline comments, so resolving would drop findings. When it is set and "ungrounded" is empty, the step writes "resolve_threads=true" and "head_sha=$HEAD_SHA" to `"${GITHUB_OUTPUT:-/dev/null}"`. Rejected: deciding in the new job from the posted review list, a second read for a fact the step already has.
- **Gate job outputs.** "resolve_threads: ${{ steps.verdict.outputs.resolve_threads }}" and "head_sha: ${{ steps.verdict.outputs.head_sha }}". The gate job's guard, env, steps, and permissions are otherwise unchanged.
- **New job.** "resolve-threads", named "Resolve the gate's superseded review threads", "needs: gate", "runs-on: ubuntu-latest", job-level "permissions:" of "contents: write" and "pull-requests: write" only. Its "if:" is "github.event_name == 'pull_request' && needs.gate.outputs.resolve_threads == 'true' && needs.gate.outputs.head_sha == github.event.pull_request.head.sha". Carrying no status function, it gets the implicit "success()", so a skipped, failed, or cancelled gate skips it. One step binds "GH_TOKEN: ${{ github.token }}", "REPO", "PR_NUMBER" from the event, and "HEAD_SHA: ${{ needs.gate.outputs.head_sha }}". It binds no secret, uses no action, and checks out nothing. Its script is the deleted block moved verbatim apart from two names: plain "gh" and "python3" replace "$gh_bin" and "$py_bin". No reviewer runs in this job, so no "$GITHUB_PATH" shim can exist there. It always exits 0. Rejected: "contents: write" at workflow level, which hands the gate job a write token.
- **Ordering.** Resolution now follows the post, so a failed post resolves nothing, and threads the new review just opened sit on HEAD_SHA and are never selected.
- **Concurrency.** The workflow-level group still cancels a run, both jobs included, on a new push. A cancelled "resolve-threads" leaves threads for the next head's run, which selects every earlier-commit gate thread. A review-event run never sets the outputs, because its posting path posts no review.
- **Tests.** In `test_copilot_verb.py`: "gate_job" returns the "gate" job by name instead of asserting one job. A new "resolve_script(text)" returns the "resolve-threads" step's run block. "GateScriptCase.gate()" runs the gate script, then reads "resolve_threads" and "head_sha" from the output file; when the gate exited 0, the event is "pull_request", "resolve_threads" is "true", and "head_sha" equals HEAD, it runs the resolve script under the same stubs with PATH holding only the stub directory first (no shim). "GateThreadResolveTest" changes its order assertion to the review before the resolve and adds cases for the neutral fallback and a plain retry. "GateWorkflowTemplateTest" replaces "test_one_job_serves_both_triggers" and "test_thread_resolution_runs_only_in_the_posting_step" with static checks of the two jobs, the new job's permissions, guard, outputs, and the absence of "secrets." and "checkout" from it.
- **Docs.** In `docs/copilot-review-reference.md`, the thread bullet (line 69) and the permissions paragraph (line 177) say a separate job resolves after the post with "contents: write", which GitHub requires for the mutation. The doc stays at or under 250 lines and lint-clean.

Risk: an organisation policy that caps workflow permissions at read would refuse the job's token; the step then warns exactly as today and the merge stays blocked.

## Readiness attestation

### Problem and motivation

The mutation fails under the gate's token, so stale gate threads block merges, and the fix must not widen the reviewer job's token.

Evidence:

- "gh run view 39377558198 --repo mikkel-bergmann/unkannybanny --log": token permissions "Contents: read", "PullRequests: write", "Statuses: write", then "gh: Resource not accessible by integration" and "Could not resolve the superseded gate review thread PRRT_kwDOVKqsBM6uNuZX".
- `plugins/s/integrations/copilot/copilot-review-gate.yml:1296-1366` resolves before the POST at `:1367`.

### Scope and non-goals

The scope is one workflow template, one test file, one doc, and the version.

Evidence:

- In scope: `plugins/s/integrations/copilot/copilot-review-gate.yml:152-192,553,1296-1366`.
- Out of scope: `plugins/s/skills/review/scripts/review_gate.py` (session flow); `plugins/s/skills/review/tests/test_review_gate.py` exercises only that flow's resolve.

### Affected capabilities and files

One requirement and four files change.

Evidence:

- Capability `copilot-review-skill`: requirement "gate-resolves-superseded-threads" (base b096c4a39f01).
- Files: the four named under Implementation.
- Runnable premise: calling "gate_job" from `plugins/s/skills/build/tests/test_copilot_verb.py:263` on a two-job "jobs:" block raised "expected exactly one job, found 2: a, b", so the helper must change before a second job lands.

### No open task-shaping decision

Every decision is settled; the user fixed the design and investigation settled the rest.

Evidence:

- Second job, job-level permissions, outputs, post-then-resolve order, kept selection rules: the user's request.
- "contents: write" requirement: GitHub community discussions 204269 and 44650 report the mutation refused without it.
- Neutral fallback resolves nothing, outputs named "resolve_threads" and "head_sha", plain "gh" in the new job: investigation, recorded above.
