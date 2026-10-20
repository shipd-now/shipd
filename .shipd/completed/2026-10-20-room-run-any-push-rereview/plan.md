# room-run-any-push-rereview

Status: ready
Planned-at: 73156d3ce5cd7c38ac953d31cd0771c4a89ffd93
Gated-hash: 87617ba87d3b

## Idea

An author `shipd room run` opens re-review tasks whenever the pull request's head moves, whoever pushed, not only when one of its own turns moved it.

### Motivation

On unkannybanny PR 26 a human pushed a fix directly, GitHub dismissed reviewer-b's approval, and the author run asked nobody to re-review, so a person had to open the task by hand with `shipd room message ... --new --to reviewer-b`. The unattended pair stalls on any push the author run did not make itself.

### Details

- **Last known head.** An author run remembers the last head it read. It reads it once at the start, after the kick-off.
- **Head check.** After every watch slice that surfaces no task, and after every turn that returns ok, the run reads the head again. When the read succeeds and differs from the last known head, the run opens the existing re-review tasks at the new head, then remembers the new head.
- **Always slice.** Every author run watches in slices of at most four `--interval` periods, so the head check runs while it waits. An empty `--ci-reviewer` now only turns off the reviews check, not the slicing.
- **Docs and version.** `docs/room-run.md` says any push counts; the plugin version moves up one patch.

Affected capability: `room-runner` (two modified requirements: `room-run-rereview`, `room-run-ci-findings`). Impact: `plugins/s/skills/room/scripts/room_run.py`, `plugins/s/skills/room/tests/test_room_run.py`, `docs/room-run.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to reviewer or `ci` runs: they never read the head and never open a re-review.
- No change to the re-review targets, the task text, or the per-head idempotency.
- No new flag; the head check cannot be turned off.

## Implementation

### Head tracking

- Add a helper "_sync_head(gh, repo, number, context, agent, opts, known, memo, warned)" in `plugins/s/skills/room/scripts/room_run.py`. It reads the head with the existing "_head". When the read fails it returns "known" unchanged and opens nothing (the existing warn-once on a failed read still applies). When "known" is non-empty and the new head differs, it calls the existing "_re_review" at the new head, catching a room error as the per-turn code does today ("warning: re-review request failed: ..."). It returns the new head.
- The run keeps "known" for author runs only. It is the head the kick-off read when `--request-review` was given, otherwise one fresh read right after the kick-off step. Reviewer and `ci` runs keep "known" empty and never call the helper.
- Decision: compare against the last known head, not a before/after pair around each turn. The per-turn "before" read is removed; the after-turn check compares against "known", which the start read and every earlier check keep current. Rejected: keeping the before/after pair and adding a second slice check, which would read the head twice per turn for no gain.
- An empty "known" (the start read failed) never opens a re-review: the first successful read only sets it. This keeps today's rule that a failed read opens nothing.

### Where the check runs

- After a watch slice that returns no task line and no closed line, an author run calls the helper, then (with a non-empty `--ci-reviewer`) checks CI reviews as today, then watches again while budget remains.
- After a turn that returns ok, an author run calls the helper. This replaces today's before/after comparison. A failed turn still opens nothing.
- No double request: when the author's own turn moved the head, the after-turn check opens the re-review and updates "known", so the next slice check sees no difference. "_re_review" is also idempotent per head and target.

### Slicing for every author run

- Every author run passes `timeout = min(remaining, opts.interval * 4)` to each watch, and drops the "watch: no actionable task" stderr line a slice prints while re-emitting every other line.
- For author runs, a slice with no task is never the end of the run; only a spent budget ends it with reason `budget`. Reviewer and `ci` runs keep the single full-budget watch and end with `budget` when it surfaces no task.
- `--ci-reviewer ""` now only skips the reviews read.

### Tests

- In `plugins/s/skills/room/tests/test_room_run.py`: a push between slices (the fake head changes during a watch, no turn runs) opens exactly one re-review task to the `--request-review` agent with `head` the new SHA; when an author turn moves the head, exactly one re-review task exists at the new head after later slices; a reviewer run whose head moves between slices opens nothing; an author run with `--ci-reviewer ""` watches in slices of four intervals and makes no reviews read.
- Replace the existing "test_an_empty_ci_reviewer_keeps_the_single_watch" with the slicing test, since the single watch is gone.

### Docs and version

- `docs/room-run.md`'s "Re-review after a push" section says any push to the head counts, the author's or anyone's, checked between waits and after each turn. The CI section's last paragraph says `--ci-reviewer ""` turns off only the reviews check. Lint with `plugins/s/skills/document/scripts/docs_lint.py`.
- `plugins/s/.claude-plugin/plugin.json` moves up one patch.

Risk: one extra head read per slice (every two minutes at the default interval). This is well inside the gh rate limit and matches the reviews read the CI check already makes.

## Readiness attestation

### Problem and motivation

An author run requests re-reviews only after its own turns, so a human push leaves the reviewer unasked.

Evidence:

- `plugins/s/skills/room/scripts/room_run.py` compares a head read before and after each turn and calls "_re_review" only then.
- Live: unkannybanny PR 26 needed a manual room message to reviewer-b after a human push.

### Scope and non-goals

Only the author role's loop changes; reviewer and `ci` runs and the re-review rules stay as they are.

Evidence:

- In scope: the run loop and a new helper in `plugins/s/skills/room/scripts/room_run.py`.
- Out of scope: `plugins/s/skills/room/scripts/room.py` is not edited.

### Affected capabilities and files

One capability with two modified requirements, four files.

Evidence:

- Capability `room-runner`: `room-run-rereview` (base 6cb5338aa7a3) and `room-run-ci-findings` (base dc11bdabd1dc), hashes from `spec_status.py base-hash`.
- Files: `plugins/s/skills/room/scripts/room_run.py`, `plugins/s/skills/room/tests/test_room_run.py`, `docs/room-run.md`, `plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

Every decision is settled in Implementation; the user pre-approved the recommended defaults.

Evidence:

- Head tracking, check points, and always-slice behavior: settled above.
