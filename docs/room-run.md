<!-- doc-type: how-to -->

# Run two agents on a pull request unattended

`shipd room run` joins your agent to a pull request's room once. It then
waits for a task addressed to it and answers each task with one headless
`/s:room` turn. It spends tokens only when a task arrives. This guide starts
an author and a reviewer in two terminals.

The Actions wake cannot do this for two agents, because a reply from the
workflow token wakes no other workflow. A run has no such limit: each agent
polls the room itself.

## Before you start

- You have an open pull request. The examples use number `412`.
- You have a second GitHub account for the reviewer. See
  [Give an agent its own GitHub account](agent-identity.md).
- You have a worktree with the pull request's branch checked out.
- You signed in to your harness. The run first sends one tiny probe turn. If
  you have signed out, it stops with one `Error:` line naming the sign-in
  command (`claude auth login`) and posts nothing.

## Start the author

Open a terminal in the pull request's worktree, keep the author's default
`gh` login, and run:

```sh
shipd room run 412 --role author --agent author-a --request-review reviewer-b
```

The `--request-review` flag opens the first review task for `reviewer-b`
once, after the author joins. A rerun does not open it again.

## Start the reviewer

In a second terminal in the same repository, point `gh` at the reviewer's
account and run:

```sh
GH_CONFIG_DIR=~/.config/gh-reviewer shipd room run 412 --role reviewer --agent reviewer-b
```

The reviewer role needs an account other than the author's. A reviewer or
`ci` run on the author's own account exits `1` with one `Error:` line and
posts nothing. An author on any other account only gets a warning.

The reviewer answers each review task with `/s:review`. That posts the ☕ shipd
summary, inline findings for the author, and a review with the full summary. The
reviewer sets `semantic-review` only when
`.github/workflows/copilot-review-gate.yml` is absent from the base branch. It
runs in a checkout of the pull request's repository.

To open the review task by hand, skip `--request-review` and run
`shipd room message 412 --new --to reviewer-b --skill review-finding "Please review this pull request."`.

## Re-review after a push

When the pull request's head moves, the author run opens one re-review task.
Any push counts: the author's own turn, a person, or another tool. The run
checks the head after each turn and between waits.

- The task goes to each reviewer who filed a finding to the author and to
  each agent that `--request-review` named.
- Each reviewer gets one task per head, so a rerun does not repeat it. If the
  run cannot read the head, it warns once and opens nothing.

## Act on the CI reviewer's findings

An author run also reads the pull request's reviews. When the CI reviewer
posts a "Fix required" review of the current head, the run spends one turn on
it. The prompt tells the author to fix the findings and push, or to reply with
the reason a finding is wrong. The turn counts toward `--max-turns`.

- The review must come from the `--ci-reviewer` login, belong to the current
  head, and carry the fix-required marker as its verdict line. The run reads
  the verdict as the CI gate does: the last line that is a verdict marker. A
  marker quoted in prose, "Ship it" reviews, and comments start nothing.
- The run handles each review once. A reply does not clear the CI verdict.
  Only a new push re-runs the CI reviewer, and a person decides otherwise.

An author run waits in slices of four `--interval` periods and checks the
reviews and the head between slices. `--ci-reviewer ""` turns off only the
reviews check; the run still waits in slices and checks the head. Reviewer and
`ci` runs ignore the flag and wait once over the whole budget.

## Answer a whole repository

Omit the number and pass `--repo`, and one reviewer answers every pull request:

```sh
GH_CONFIG_DIR=~/.config/gh-reviewer shipd room run --repo o/r --role reviewer --agent reviewer-b
```

The run lists the open pull requests with one `gh` call and spends no tokens
while it waits. It runs one turn at a time, on each pull request with a task
for the agent. It skips pull requests its own account authored, and takes only
the `reviewer` and `ci` roles. It keeps each cursor and session in `--state PATH`,
by default `~/.shipd/room-run/<owner>/<name>/<agent>.json`. A restart resumes
every conversation, and a second run on that file refuses to start. Ctrl-C
stops the run with `reason` `interrupted`.

## Set the limits

| Flag | Default | Meaning |
|------|---------|---------|
| `--max-turns` | `10` | Stop after this many turns. Repo mode parks a pull request at this count. |
| `--budget` | `14400` | Stop after this many seconds. Repo mode has no limit by default. |
| `--state` | see above | Repo mode only: the cursor and session file. |
| `--harness` | `claude` | The harness that runs each turn. |
| `--model` | harness default | A model id or an effort level. |
| `--turn-timeout` | `1800` | Seconds one turn may run. |
| `--interval` | `30` | Seconds between polls. |
| `--request-review` | none | Open a review task for this agent. Repeatable. Author role only. |
| `--ci-reviewer` | `github-actions[bot]` | The CI reviewer whose fix-required review starts an author turn. Empty disables. Author role only. |

## Read the result

`run` prints one JSON line on stdout and progress on stderr:

```json
{"turns": 2, "session_id": "s-1", "reason": "closed", "context": "o/r#412", "cursor": "2100:0", "closed": "merged"}
```

The `reason` value says why the run stopped:

- `closed` — the pull request merged or closed. The `closed` key says which.
- `turn-cap` — the run took `--max-turns` turns.
- `budget` — `--budget` seconds passed, or a reviewer or `ci` wait ended with no task.
- `turn-failed` — a turn failed. The `failure` key says why.
- `watch-failed` — the wait raised a room error. The `failure` key says why.
- `preflight-failed` — repo mode: a turn failed, then the harness check failed.
- `interrupted` — repo mode: you pressed Ctrl-C.

The run exits `0` for `closed`, `turn-cap`, and `budget`. It exits `1` with one
`Error:` line for a failure. It never retries a failed turn. In repo mode, a
failed turn parks only its pull request.

## Know what a turn may do

Every turn runs with `bypassPermissions`, as autopilot's turns do. Restrict
each agent through its GitHub account. A reviewer token without write access
cannot push, whatever the turn tries.

## See also

- [Run an agent's turn in a multi-agent PR](pr-room.md) — the room verbs.
- [Room wake reference](room-wake-reference.md) — the Actions wake and its limits.
- [Multi-agent PR](multi-agent-pr.md) — the model.
