# room-turn-hygiene
Status: verified
Epic: pr-conversations
Planned-at: 4dbd39712940f796520736363a14f1de45156124
Gated-hash: 00a6e973695e

## Idea

Make every room verb resolve its repository from the pull request URL or `--repo` first, and stop a merge from stranding an open task.

### Motivation

On https://github.com/mikkel-bergmann/unkannybanny/pull/14 the author agent's `watch` failed with "Could not resolve to a PullRequest with the number of 14" because its shell sat in the shipd checkout and the verbs read the repository from the working directory. The reviewer then merged while the author's `input-required` message to it was still open, so the question went unanswered.

### Details

- Every verb accepts a pull request URL as `<pr>` and `--repo <owner/name>`; the repository comes from them first, else from `gh repo view` in the working directory. Every `gh pr view` the verbs run carries that repository.
- `list --open` keeps only tasks in `working` or `input-required`.
- `watch`'s `closed` line gains an `open` array of those tasks, and a stderr line names them.
- The room skill reports those tasks as unresolved on a closed room, and the reviewer's agent merges only when `list --open` is empty.

Affected capabilities: `pr-room` (modified: `room-gh-seam`, `room-list-verb`, `room-watch-exit`), `shipd-room` (modified: `room-skill-stops`; added: `room-skill-merge-rule`). Impact: `plugins/s/skills/room/scripts/room.py`, the room tests, `room/SKILL.md`, the harness body and reference, `docs/pr-room.md`, the plugin version.

### Non-goals

- No change to `message`, `close`, or finding threads; `room-threaded-findings` owns `room-message-verb`.
- No new environment variable or config key for the repository.
- No enforcement outside the skill: `gh pr merge` itself is not wrapped or blocked.

## Implementation

- **One resolver.** `_resolve_room(gh, pr, repo=None)`. A `<pr>` matching `^https?://[^/]+/([^/]+/[^/]+)/pull/(\d+)` yields its repository from the URL. Else `--repo` supplies it. Else the repository is read with `gh repo view` as today. When both name different repositories (compared case-insensitively) it raises `RoomError("pull request URL names <a> but --repo names <b>")` (Q1). `gh pr view <pr> --json number,url` gains `--repo <repo>` whenever a repository came from a flag or URL.
- **`--repo` lives on the shared parent parser**, so all five verbs accept it; `cmd_*` pass `opts.repo`.
- **`_pr_closed(gh, repo, number)`** adds `--repo <repo>`; before, it used the working directory, the same fault.
- **Open tasks.** `OPEN_STATES = ("working", "input-required")` in `room.py`. `list --open` filters the `tasks` block and the JSON `tasks` array to those states; the exit code is unchanged, and the caller reads emptiness (Q2). Rejected: a `clear` verb, a second surface for one filter.
- **Closed line.** It always carries `"open": [{"task", "state", "to", "skill"}, ...]`, empty for a clean room (Q3), built from the tasks of the poll that saw the close. Before the existing `watch: <context> is <merged|closed>; the room is closed` stderr line, `watch` prints `watch: <n> unresolved task(s): #<id> <state>, ...` when any exist, so the closed line stays last.
- **Skill.** `SKILL.md`, the harness body, and the reference gain: on a `closed` line, report its `open` tasks as unresolved; before `gh pr merge` (arming auto-merge included) the reviewer's agent runs `shipd room list <pr> --open --json` and merges only when `tasks` is empty, otherwise it waits (`stay`) or reports the tasks and stops. The skill passes the user's URL, or `--repo` when the user names one, to every verb.
- **Version.** One patch above `main`'s `plugins/s/.claude-plugin/plugin.json` at build time.
- **Epic Decisions relied on.** "Verbs resolve the repository the same way everywhere" and "A merge does not strand a conversation".

Risk: a `working` claim on a finding thread (from `room-threaded-findings`) counts as open, which is intended. Risk: a bare number with no flag in a foreign checkout still resolves against that checkout; the skill's URL rule covers it.

## Questions and answers

### Q1: URL and `--repo` that disagree
- **Question:** When a verb gets a pull request URL and `--repo` naming different repositories, should it (1) fail with one `Error:` line naming both; (2) let the URL win silently; (3) let `--repo` win? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Fail. A silent winner would run a verb against a repository the caller did not mean, which is the fault this change removes.
- **Queued:** q-room-pr-url-repo-flag-conflict

### Q2: How the reviewer checks for open tasks
- **Question:** Should the merge check be (1) a `--open` flag on `list` that keeps only `working` and `input-required` tasks, read for emptiness; (2) a new `clear` verb that exits non-zero; (3) skill prose over `list --json`? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) The `--open` flag. It reuses the verb and output shape agents already read, and a non-zero exit would collide with the skill's rule that any failing verb stops the turn.
- **Queued:** q-room-open-task-check

### Q3: Shape of `open` on the closed line
- **Question:** Should the `closed` line (1) always carry an `open` array, empty when none; or (2) carry it only when non-empty? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) Always. A reader tests one field instead of its presence, and the line's shape stays the same for every room.

## Readiness attestation

### Problem and motivation

`watch` failed on PR 14 because repository resolution used the working directory, and a merge landed over an open `input-required` task.

Evidence:

- `plugins/s/skills/room/scripts/room.py:84-96` reads `gh repo view` with no repository argument; `room.py:600-606` reads the state with a bare number.
- Capability `pr-room`, requirement `room-gh-seam` fixes that resolution; `room-watch-exit` prints the closed line with no task list.
- Epic `pr-conversations`, Decisions "Verbs resolve the repository the same way everywhere" and "A merge does not strand a conversation".

### Scope and non-goals

The change covers repository resolution for all five verbs, the `list --open` filter, the closed line, and the skill's stop and merge rules; message routing and finding threads stay out.

Evidence:

- In scope: `room.py:84-96`, `room.py:387-657`, `room.py:695-778`, `plugins/s/skills/room/SKILL.md`.
- Out of scope: `room-message-verb` belongs to `room-threaded-findings`, whose plan edits it.

### Affected capabilities and files

Two capabilities and about nine files are affected, because the resolver and the filter live in `room.py` and the rules live in the skill, its harness copies, and the how-to.

Evidence:

- `pr-room`: `room-gh-seam` (base 039c543f20d7), `room-list-verb` (base 701cf4d9b7cc), `room-watch-exit` (base fea9e3b72d08). `shipd-room`: `room-skill-stops` (base 5626f970d47b).
- Files: `plugins/s/skills/room/scripts/room.py`, `plugins/s/skills/room/tests/test_room.py`, `test_room_skill.py`, `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`, `plugins/s/harness/references/room.md`, `docs/pr-room.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `gh pr view 14 --repo mikkel-bergmann/unkannybanny --json number,url,state` run from the shipd worktree exited 0 and printed number 14, state MERGED.
- Runnable premise: `gh pr view https://github.com/mikkel-bergmann/unkannybanny/pull/14 --json number,state` from the same directory exited 0 with the same number.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- URL against `--repo` conflict: planner default, Q1.
- Open-task check surface: planner default, Q2.
- Shape of `open` on the closed line: planner default, Q3.
- Which states count as open: fixed by the epic as `working` and `input-required`.
