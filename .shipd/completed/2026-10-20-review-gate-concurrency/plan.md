# review-gate-concurrency

Status: ready
Planned-at: 0a0ad6eea92ef799aa5643d49528a3c56b63d9f1
Gated-hash: 3392d343d20d

## Idea

The review gate workflow stops a non-Copilot review from cancelling the Copilot review that is still running on the same pull request.

### Motivation

On unkannybanny PR 26 the reviewer agent approved while the CLI reviewer was still running. The approval started a `pull_request_review` run in the same concurrency group, which cancelled the review in progress and then skipped its own job. Nothing was left to post `semantic-review`, so it stayed pending and the pull request could not merge. This happens whenever a second reviewer finishes before Copilot, which the room runner now makes the usual order.

### Details

- **Group key.** The `concurrency.group` in `plugins/s/integrations/copilot/copilot-review-gate.yml` gets a suffix for review events not submitted by Copilot: "-review-" plus the review id. Those runs land in a group of their own and cancel nothing.
- **Unchanged paths.** A push (`pull_request`) and Copilot's own review event keep the shared per-pull-request group, so a new push still cancels a superseded run and Copilot's review still supersedes the poll.
- **Docs and version.** `docs/copilot-review-reference.md` states the rule, and the plugin version moves up one patch.

Affected capability: `copilot-review-skill` (one new requirement). Repositories with the gate get the fix through `/s:gate update`.

### Non-goals

- No change to the job's `if:` guard, the poll, the grounding, or the verdict mapping.
- No change to `room-wake.yml`, whose group already does not cancel.

## Implementation

- The new group expression is "shipd-semantic-review-gate-${{ github.event.pull_request.number }}${{ github.event_name == 'pull_request_review' && github.event.review.user.login != 'copilot-pull-request-reviewer[bot]' && format('-review-{0}', github.event.review.id) || '' }}".
- The login literal matches the one in the job's `if:` guard, so both name the same reviewer.
- The comment above the `concurrency` block gains one sentence: a review by anyone other than Copilot runs in its own group, because its run skips its job and must not cancel a live review.
- Test: in `plugins/s/skills/build/tests/test_copilot_verb.py`, the existing concurrency test keeps its assertions, and a new test asserts the group line carries the event-name check, the Copilot login, and the review id suffix.
- Rejected: dropping `cancel-in-progress`, which lets two runs for successive heads post over each other.
- Rejected: dropping the `pull_request_review` trigger, which breaks the poll fallback's review-event path.

## Readiness attestation

- Problem: the shared concurrency group lets any review event cancel a live CLI review (seen on unkannybanny PR 26, run 39326808548).
- Scope: one workflow line and its comment, one test, one doc paragraph, the version bump.
- Affected: `plugins/s/integrations/copilot/copilot-review-gate.yml`, `plugins/s/skills/build/tests/test_copilot_verb.py`, `docs/copilot-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`.
- Open decisions: none.
