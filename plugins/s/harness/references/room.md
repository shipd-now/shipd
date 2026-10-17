# /s:room — reference

The fuller protocol behind the room command's turn loop.

## The watch output

`shipd room watch <pr> --since <cursor> --timeout 540` blocks until at least
one task is this agent's turn, then prints one NDJSON line per surfaced task
and exits 0. The tool call that runs `watch` needs its own timeout above 540
seconds, or the harness may move the wait to the background. Each line
carries the `list --json` task fields plus:

| Field | Meaning |
| --- | --- |
| `task` | the task id to pass as `--task` |
| `context` | the room the task lives in (`<owner>/<repo>#<number>`) |
| `comment` | the id of the task's newest comment |
| `text` | the task's newest message text |
| `url` | the newest comment's URL |
| `cursor` | `<issue>:<review>` comment ids; pass it as the next `--since` |

When the pull request merges or closes, `watch` prints one more line,
`{"closed": "merged"|"closed", "context", "cursor", "open"}`. `open` lists
every task still `working` or `input-required` as `{task, state, to, skill}`,
and is `[]` for a clean room; stderr first names them in a `watch: <n>
unresolved task(s)` line.

Re-enter `watch` with the last line's `cursor`, so a task already answered is
not surfaced again. Cursor `0` (the backlog) is the entry value.

## Replies

Every `message` names `--state` explicitly:

- `--state working` claims the turn before the work starts.
- `--state completed` posts the answer and finishes the task.
- `--state input-required --to <asker>` asks the asker to answer or act —
  the reply for any task that needs a code change, naming `/s:fix` or
  `/s:plan` as the hand-off.

A `review-finding` task whose finding the PR head already addresses is closed
with `shipd room close <pr> "<one line naming the commit>" --task <id>
--state completed`. A finding's messages reply on its review thread, and a
`completed` one resolves that thread.

Only an agent whose card role is `author` (see `shipd room list <pr> --json`)
may fix a `review-finding` itself, and only on its own pull request. The role
is self-declared, so from `gh pr view <pr> --json author,headRefName,isCrossRepository`
the `author.login` must equal `gh api user --jq .login`, `isCrossRepository`
must be `false`, `headRefName` must equal `git branch --show-current`, and the
tree must be clean. It makes the smallest
fix, runs the tests covering it, commits, runs plain `git push` (never
`--force`), and closes the task `completed` naming the short SHA. Any failed
check, or any other role, keeps the prose hand-off to `/s:fix` or `/s:plan`.

## Merging

Before `gh pr merge` (arming `--auto` included), an agent whose card role is
`reviewer` runs `shipd room list <pr> --open --json`, which keeps only
`working` and `input-required` tasks. It merges only when `tasks` is empty;
otherwise it keeps watching (`stay`) or reports the open tasks and stops.

Every verb takes the user's pull request URL as `<pr>`, or `--repo
<owner/name>`; a URL and a `--repo` naming different repositories fail.

## The stop list

End the turn and report, posting nothing further, when:

- `watch` printed a `closed` line — report its `open` tasks as unresolved,
  with each id and state.
- `watch` exits 0 with empty stdout — no task became this agent's turn within
  the timeout. Report the cursor `watch` printed on stderr
  (`watch: no actionable task on <room> (cursor <c>)`) for the next run.
- `message` exits 1 with an `Error:` line naming the round cap — the verb has
  already posted `failed` with reason `round-cap` on the task.
- any verb exits non-zero — relay its `Error:` line verbatim.
- no agent name resolves — relay the usage error and name `--agent`,
  `SHIPD_ROOM_AGENT`, and the `room.agent` config member.
