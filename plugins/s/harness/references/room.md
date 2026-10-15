# /s:room — reference

The fuller protocol behind the room command's turn loop.

## The watch output

`shipd room watch <pr> --since <cursor> --timeout 600` blocks until at least
one task is this agent's turn, then prints one NDJSON line per surfaced task
and exits 0. Each line carries the `list --json` task fields plus:

| Field | Meaning |
| --- | --- |
| `task` | the task id to pass as `--task` |
| `context` | the room the task lives in (`<owner>/<repo>#<number>`) |
| `comment` | the id of the task's newest comment |
| `text` | the task's newest message text |
| `url` | the newest comment's URL |
| `cursor` | `<issue>:<review>` comment ids; pass it as the next `--since` |

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
--state completed`.

## The stop list

End the turn and report, posting nothing further, when:

- `watch` exits 0 with empty stdout — no task became this agent's turn within
  the timeout. Report the cursor `watch` printed on stderr
  (`watch: no actionable task on <room> (cursor <c>)`) for the next run.
- `message` exits 1 with an `Error:` line naming the round cap — the verb has
  already posted `failed` with reason `round-cap` on the task.
- any verb exits non-zero — relay its `Error:` line verbatim.
- no agent name resolves — relay the usage error and name `--agent`,
  `SHIPD_ROOM_AGENT`, and the `room.agent` config member.
