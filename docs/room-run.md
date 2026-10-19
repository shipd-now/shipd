<!-- doc-type: how-to -->

# Run two agents on a pull request unattended

`shipd room run` joins your agent to a pull request's room once. It then
waits for a task addressed to it and answers each task with one headless
`/s:room` turn. It spends tokens only when a task arrives. This guide starts
an author and a reviewer in two terminals and lets them talk a pull request
through.

The Actions wake cannot do this for two agents, because a reply from the
workflow token wakes no other workflow. A run has no such limit, because each
agent polls the room itself.

## Before you start

- You have an open pull request. The examples use number `412`.
- You have a second GitHub account for the reviewer. See
  [Give an agent its own GitHub account](agent-identity.md).
- You have a worktree with the pull request's branch checked out for the
  author.
- You signed in to your harness. The run first sends one tiny probe turn. If
  you have signed out, it stops with one `Error:` line naming the
  sign-in command (`claude auth login`) and posts nothing.

## Start the author

1. Open a terminal in the pull request's worktree. Keep the default `gh`
   login, which is the author's.
2. Run:

   ```sh
   shipd room run 412 --role author --agent author-a --request-review reviewer-b
   ```

   The `--request-review` flag opens the first review task for `reviewer-b`
   once, after the author joins. A rerun does not open it again.

## Start the reviewer

1. Open a second terminal in the same repository.
2. Point `gh` at the reviewer's account and run:

   ```sh
   GH_CONFIG_DIR=~/.config/gh-reviewer shipd room run 412 --role reviewer --agent reviewer-b
   ```

The reviewer role needs an account other than the author's. `run` reads the
login and the pull request author first. It exits `1` with one `Error:` line
and posts nothing when a reviewer or `ci` role runs on the author's own
account. An author on any other account only gets a warning on stderr.

## Ask for a review by hand

To open the review task yourself, skip `--request-review` and run:

```sh
shipd room message 412 --new --to reviewer-b --skill review-finding "Please review this pull request."
```

## Re-review after a push

When an author turn moves the pull request's head, the run opens one
re-review task. It goes to each reviewer who filed a finding to the author and
to each agent that `--request-review` named. Each reviewer gets one task
per head, so a rerun does not repeat it.

## Set the limits

| Flag | Default | Meaning |
|------|---------|---------|
| `--max-turns` | `10` | Stop after this many turns. |
| `--budget` | `14400` | Stop after this many seconds. |
| `--harness` | `claude` | The harness that runs each turn. |
| `--model` | harness default | A model id or an effort level. |
| `--turn-timeout` | `1800` | Seconds one turn may run. |
| `--interval` | `30` | Seconds between polls. |
| `--request-review` | none | Open a review task for this agent. Repeatable. Author role only. |

## Read the result

`run` prints one JSON line on stdout and progress on stderr. For example:

```json
{"turns": 2, "session_id": "s-1", "reason": "closed", "context": "o/r#412", "cursor": "2100:0", "closed": "merged"}
```

The `reason` value says why the run stopped:

- `closed` — the pull request merged or closed. The `closed` key says which.
- `turn-cap` — the run took `--max-turns` turns.
- `budget` — `--budget` seconds passed, or a wait ended with no task.
- `turn-failed` — a turn failed. The `failure` key says why.
- `watch-failed` — the wait raised a room error. The `failure` key says why.

The run exits `0` for `closed`, `turn-cap`, and `budget`. It exits `1` with one
`Error:` line for the two failures. It never retries a failed turn.

## Know what a turn may do

Every turn runs with `bypassPermissions`, as autopilot's turns do. Restrict
each agent through its GitHub account, not through the run. A reviewer token
without write access cannot push, whatever the turn tries.

## See also

- [Run an agent's turn in a multi-agent PR](pr-room.md) — the room verbs.
- [Room wake reference](room-wake-reference.md) — the Actions wake and its limits.
- [Multi-agent PR](multi-agent-pr.md) — the model.
