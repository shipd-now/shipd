# honest-gate-degradation
Status: verified
Theme: reliability

## Idea

Make the semantic-review gate fail visibly when its reviewer produces nothing,
stop anchoring findings that the rubric says never block, and make a
human-produced status able to satisfy the required check.

### Motivation

`gate-workflow-template` requires the workflow to post a terminal
`semantic-review` status for every reviewed head, but a reviewer that produces
no output leaves it `pending` and exits zero — a green job over a review that
never happened, and a pull request blocked forever with nothing saying why.
The requirement carries no scenario for that case, so the outage path is
unspecified rather than wrong.

### Details

- Fail the gate job when the reviewer captured no output, or when the poll
  found no review, instead of exiting zero. The status still stays `pending` —
  nothing was judged — but the run is red and names the cause.
- Anchor only `high` and `medium` findings; route `low` through the prose path
  the workflow already has, so a finding the rubric says never blocks stops
  opening a merge-blocking review thread.
- Make `review_gate.py protect` write the required check as `checks` with an
  explicit `app_id` of null, so any source may report `semantic-review`.

Affected capabilities: `copilot-review-skill` (modified), `semantic-review`
(modified). Impact: `plugins/s/integrations/copilot/copilot-review-gate.yml`,
`plugins/s/skills/review/scripts/review_gate.py`, and their suites under
`plugins/s/skills/build/tests/` and `plugins/s/skills/review/tests/`. No new
dependencies; the engine stays stdlib-only.

### Non-goals

- No path from posted findings into automatic fixes. That is a new capability
  with its own design space and is planned separately.
- No change to `/s:fix`, which is spec-drift debugging and has no verb for
  reading findings off a pull request.
- No fallback reviewer: the gate gains no second review engine, and nothing
  here makes a review happen when the configured reviewer cannot run.
- No change to `required_conversation_resolution` itself — `protect` keeps
  setting it, because it still protects human review threads.
- No change to the verdict rubric, the severity vocabulary, or the review
  report's shape.

## Implementation

- **A no-output reviewer fails the job; a moved head does not.** The template
  carries three `exit 0` sites. Two are stalls and become `exit 1`: the CLI
  branch that finds no body file, and the poll branch that times out with no
  review. The third — the poll seeing the pull request's head move on — stays
  `exit 0` deliberately: that run is not stalled, it has handed the gate to the
  newer push's run, and failing it would paint a red X on every superseded
  push. Absorbs the change already written on `change/gate-fail-loudly`, which
  is abandoned rather than shipped separately, so one template change travels
  in one pull request.
- **The status stays `pending` on those paths, and that is deliberate.**
  Nothing was judged, so no verdict may be invented; the job's exit code — not
  a fabricated status — is what tells a human the reviewer broke. The failure
  message names the reviewer step's log as where the cause is, because an
  exhausted Copilot quota reports there and nowhere else.
- **`SHIPD_GATE_FAIL_OPEN` is not consulted on the no-output path, and stays
  that way.** It governs a review that ran but carried no verdict marker; a
  review that never ran is a different condition. The cai-api run log confirms
  the no-output branch prints its own message and returns before that check.
- **Severity gates anchoring, not reporting.** The anchor loop routes a `low`
  finding to `unverified` — the same list an unanchorable finding joins — so it
  renders through the existing `prose()` block in the review body. The finding
  is still reported in full; only its inline comment is withheld. Rejected:
  having the gate resolve its own superseded threads, which keeps every finding
  anchored but adds thread lifecycle management to a workflow that has none.
  Rejected: dropping `required_conversation_resolution` from `protect`, which
  would give up the protection for human reviewers too.
- **`protect` writes `checks`, not `contexts`.** `_protection_put_body`
  currently sends the legacy `contexts` field. GitHub derives `checks` from it
  with a null `app_id`, so today's behaviour is right by accident and
  undocumented. Sending `checks` with an explicit `"app_id": null` per context
  states the intent — any source may report this check — and makes a
  human-posted status able to satisfy the required check. Observed on
  `shipd-now/cai-api`: a status posted by a user account against a context
  pinned to `app_id` 15368 is ignored by protection, so a human review could
  never satisfy the gate there.
- **Both suites already pass on the clean worktree** — 150 tests in
  `test_copilot_verb`, 68 in `test_review_gate` — so every failure a task
  introduces is its own.

Risk: three tests in `test_copilot_verb` assert `exit 0` on the two paths that
now fail, and they encode the old contract rather than catching a regression;
they are updated to assert the failure and are named for the new behaviour. The
harness already carries an `expect_failure` flag, so no test-harness change is
needed. Risk: a repository whose required check is pinned to an app keeps that
pin until `protect` is re-run there — this change makes future writes explicit,
it does not retroactively repair a branch nobody re-protects.
