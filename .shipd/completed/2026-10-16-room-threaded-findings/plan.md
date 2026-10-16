# room-threaded-findings
Status: verified
Epic: pr-conversations
Planned-at: 4dbd39712940f796520736363a14f1de45156124
Gated-hash: 71b21661552a

## Idea

Post every message on a review-finding task as a reply on the finding's own review thread, resolve that thread when the task completes, and let the author's agent commit the fix to its own pull request.

### Motivation

On https://github.com/mikkel-bergmann/unkannybanny/pull/14 the author's agent completed finding task 4290285040 in the room, but `review_gate.py resolve` still reported `unresolved=1` until the reviewer also ran `review_gate.py reply`, so every finding had to be closed twice. The same author agreed with the finding but, being prose-only, could not fix it, and the flaw merged.

### Details

- A finding task is a task whose opening comment came from the review-comment endpoint. `message`, `close`, and the round-cap posts reply on that thread (`in_reply_to` the task id). Every other task stays on issue comments.
- A `working` claim on a finding task lives on the thread too; the next reply deletes it through the pulls endpoint.
- A `completed` Message on a finding task resolves the thread with the same GraphQL mutation `review_gate.py resolve` uses.
- `/s:room`: an agent whose card role is `author` may fix a `review-finding` on its own pull request's head branch, then reply `completed` naming the commit. Every other role stays prose-only.

Affected capabilities: `pr-room` (modified: `room-message-verb`; added: `room-finding-thread-reply`, `room-finding-thread-resolve`), `shipd-room` (modified: `room-skill-no-code`, `room-skill-docs`). Impact: `room.py`, `room_schema.py`, `review_gate.py`, the room tests, `room/SKILL.md`, the harness body and reference, `docs/pr-room.md`, `docs/multi-agent-pr.md`, the plugin version.

### Non-goals

- No change to `review_gate.py resolve`, `reply`, or `autoreply` behavior, or to the gate's findings and verdicts.
- The reviewer's and the CI agent's roles never edit code, and no agent edits another pull request.
- No change to repository resolution or the merge rule; `room-turn-hygiene` owns those.

## Implementation

- **Finding task test.** `room.py` gains `_finding_root(comments, task)`: `task.id` when the comment whose id is `task.id` was read from the review endpoint, else `None`. Only the gate opens tasks there, so no skill check is needed. Rejected: keying on `task.skill == "review-finding"`, which a person could set on an issue-comment task.
- **Routing.** `_post_message(gh, repo, number, message, login="", role="", thread=None)` (the `login`/`role` keywords come from `room-speaker-identity`). With `thread` it runs `gh api -X POST repos/<repo>/pulls/<n>/comments --input -` with `{"body", "in_reply_to": thread}`; else the issue POST. `cmd_message` (reply and cap paths), `cmd_close`, and `_cap_task` pass `thread=_finding_root(...)`. `--new` never has a thread.
- **Claims on the thread (Q3).** `_own_claim` accepts a last comment from either endpoint and returns `(id, endpoint)`; `_drop_claim` deletes `repos/<repo>/pulls/comments/<id>` for a review claim and the issue path otherwise.
- **Resolve (Q1, Q2).** After posting and dropping the claim, when the posted state is `completed` and the task is a finding task, `_resolve_finding_thread(gh, repo, number, task_id)` runs `gh api graphql` with `THREAD_LOOKUP_QUERY` (owner, name, number; `reviewThreads(first:100)` with `id`, `isResolved`, and the first comment's `databaseId`), picks the thread whose first comment is the task id, and when unresolved runs `room_schema.RESOLVE_THREAD_MUTATION` with `-f threadId=<id>`. Already resolved: nothing. No match or a failed call: `warning: could not resolve the review thread for task <id>` on stderr, exit 0. `canceled` and `failed` never resolve. The stdout JSON is unchanged.
- **One owner for the mutation.** `RESOLVE_THREAD_MUTATION` moves from `review_gate._RESOLVE_MUTATION` into `room_schema` (pure strings, no new import); `review_gate._resolve_thread` uses it. Rejected: two copies, which can drift from `resolve`.
- **Author may fix (Q4).** `room/SKILL.md`, `harness/bodies/room.md`, and `harness/references/room.md` replace the blanket prose rule: the role is the `role` on this agent's own card in `shipd room list <pr> --json`. Only with role `author`, on a surfaced `review-finding` task, the working tree on the PR's head branch (`gh pr view <pr> --json headRefName` equals `git branch --show-current`) and clean, the agent makes the smallest fix, runs the tests covering the touched files, commits, runs plain `git push` (never `--force`), and closes the task `completed` naming the short SHA. Any failed check, or any other role, keeps the prose hand-off to `/s:fix` or `/s:plan`. The skill passes `--role` on every join, per `room-speaker-identity` Q4.
- **Epic Decisions relied on.** "Finding replies go on the finding's thread" and "Only the author's agent changes code, and only its own pull request".
- **Version.** One patch above `main`'s `plugins/s/.claude-plugin/plugin.json` at build time.

Risk: a `working` claim on the thread counts as reply evidence if someone runs `review_gate.py resolve` mid-task; `room-turn-hygiene`'s no-open-task merge rule covers it. Risk: lookups cap at 100 threads, the gate's known cap.

## Questions and answers

### Q1: Which terminal states resolve the thread
- **Question:** Should (1) only `completed` resolve the finding's thread, with `canceled`/`failed` posted on it and left unresolved; or (2) every terminal state resolve it? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Only `completed`. It is the epic's wording, and an unresolved thread keeps a canceled or failed finding in front of a person.
- **Queued:** q-finding-thread-resolve-on-canceled-failed

### Q2: Resolve failure after the reply posts
- **Question:** When the thread lookup finds nothing or the mutation fails after the reply posted, should the verb (1) warn on stderr and exit 0; or (2) print `Error:` and exit 1? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Warn and exit 0. The reply stands, `review_gate.py resolve` counts it as evidence later, and a failed claim delete already follows this pattern.
- **Queued:** q-room-thread-resolve-failure

### Q3: Where a finding task's claim goes
- **Question:** Should the `working` claim on a finding task (1) post on the thread and be deleted from it through the pulls endpoint; or (2) stay an issue comment? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) On the thread. The whole task then reads in one place, and the epic keeps issue comments for other tasks' traffic only.
- **Queued:** q-finding-task-working-claim-placement

### Q4: Guard on the author's code push
- **Question:** Should the author's fix require (1) the PR head branch checked out and clean, a covering test run, a plain push, else the prose hand-off; or (2) no guard beyond role and task skill? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) The guard. It keeps the push on the agent's own pull request and never rewrites history; any failed check falls back to today's hand-off.
- **Queued:** q-room-author-push-guard

## Readiness attestation

### Problem and motivation

Findings needed a second close, and an author agent could not fix a finding it agreed with.

Evidence:

- PR 14: thread `PRRT_kwDOVKqsBM6tCk6k` root 4290285040 got its only reply, 4290308572, from `review_gate.py reply`, while the room close went to an issue comment.
- `room.py` `_post` always POSTs `issues/<n>/comments`; `room/SKILL.md` "Prose only" forbids any commit.

### Scope and non-goals

Routing, claim delete, and resolve in `room.py`; the author rule in the skill text; docs.

Evidence:

- In scope: `room.py` `cmd_message`, `cmd_close`, `_cap_task`, `_own_claim`, `_drop_claim`, `_post_message`; `review_gate.py:135` mutation constant.
- Out of scope: `review_gate.py` `resolve` logic; repository resolution (`room-turn-hygiene`).

### Affected capabilities and files

Two capabilities, three modified and two added requirements.

Evidence:

- `pr-room`: `room-message-verb` (base bdf44e8c1f32); added `room-finding-thread-reply`, `room-finding-thread-resolve`. `shipd-room`: `room-skill-no-code` (base f275dad071e2), `room-skill-docs` (base 06503f4836a1). Hashes from `spec_status.py base-hash`.
- Files: `plugins/s/skills/room/scripts/room.py`, `room_schema.py`, `plugins/s/skills/review/scripts/review_gate.py`, `plugins/s/skills/room/tests/test_room.py`, `test_room_schema.py`, `test_room_skill.py`, `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`, `plugins/s/harness/references/room.md`, `docs/pr-room.md`, `docs/multi-agent-pr.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `gh api graphql` on PR 14's `reviewThreads` returned one thread whose first comment `databaseId` is 4290285040, the room task id; `gh api repos/mikkel-bergmann/unkannybanny/pulls/14/comments` showed reply 4290308572 with `in_reply_to_id` 4290285040.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Resolving states, resolve failure, claim placement, author guard: planner defaults Q1 to Q4.
- Finding-task test and mutation owner: settled by investigation.
- Thread replies and author-only code: settled by the epic Decisions.
