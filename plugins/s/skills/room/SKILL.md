---
name: room
description: >-
  Hold this agent's turn in a pull request's room: join the room with a card,
  read it, wait in the foreground for a task that is this agent's turn, reply
  in prose with an explicit task state, and stop at an empty wait, the round
  cap, or any failing verb. Posts prose only — it never edits, commits, or
  pushes code; code work is handed to `/s:fix` or `/s:plan`. Use when asked
  to join a PR's room, answer the room, or take this agent's turn on a pull
  request. Trigger phrases: "join the PR room", "answer the room", "take my
  turn in the room", "/s:room".
---

# /s:room — take this agent's turn in a PR room

You are **one agent in a pull request's room**: the PR's comment thread, where
agents and people open tasks for each other and take turns on them. Your job is
to join the room, read it, wait for a task that is your turn, answer it in
prose, and stop cleanly. Every read and write goes through the `shipd room`
verbs; you never hand-write a room comment.

You are invoked as `/s:room [<pr>]`. `<pr>` is a pull request number, URL, or
branch. Every verb requires it, so when it is omitted, pass the current branch
(`git branch --show-current`) as `<pr>` and the verbs resolve that branch's
pull request.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:room
v<version>` in your first user-visible status sentence (e.g. "shipd:room
v0.6.293 — joining the room on PR 412"), so the user can always see which
plugin snapshot the session is running.

Every verb below runs as `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" room <verb> …`;
the steps write it as `shipd room <verb>` for short.

## Who you are in the room

The verbs resolve the acting agent's name themselves: `--agent`, then the
`SHIPD_ROOM_AGENT` environment variable, then the `room.agent` config member.
**Never invent a name.** Pass `--agent` only when the user named one. When no
name resolves, the verb exits with a usage error: relay that error line as it
stands, name the three sources above, and stop.

## The loop

1. **Join.** Post or refresh this agent's card:
   `shipd room join <pr> --skill review-finding --skill question --skill status`.
   Those three skills are the default card, so you pick up unaddressed review
   findings, questions, and status requests. When the user names skills, pass
   exactly those `--skill` flags instead — the user's list replaces the default,
   it does not extend it.
2. **Read the room.** `shipd room list <pr>` prints the cards and the open
   tasks. Show the user a compact summary of it.
3. **Wait for your turn — in the foreground.**
   `shipd room watch <pr> --since <cursor> --timeout 600`, with cursor `0` on
   entry. `watch` blocks until a task is this agent's turn, then prints one
   NDJSON line per surfaced task (fields: `task`, `skill`, `text`, `url`,
   `cursor`, and the rest of the task) and exits 0. The ten-minute timeout
   bounds every wait; never drop it.
4. **Work each surfaced task**, one line at a time, and only the tasks `watch`
   printed — never act on a task `watch` did not surface, even one `list`
   showed:
   - Claim the turn first:
     `shipd room message <pr> "<what you are doing>" --task <id> --state working`.
   - Do the work (see **Prose only** below).
   - Reply with the outcome, always naming the state:
     `shipd room message <pr> "<answer>" --task <id> --state completed` when
     the task is done, or
     `shipd room message <pr> "<question>" --task <id> --state input-required --to <asker>`
     when you need the asker to answer or act.
   - A `review-finding` task whose finding the PR head already addresses is
     closed, not re-litigated: `shipd room close <pr> "<one line naming the commit>" --task <id> --state completed`.
5. **Re-enter step 3** with the `cursor` from the last NDJSON line `watch`
   printed.

Every `message` call names `--state` explicitly; never lean on the verb's
default state.

## When to stop

End the turn and report — posting nothing further — on any of these:

- **Empty wait.** `watch` exits 0 with empty stdout: no task became this
  agent's turn within the timeout. Report "no actionable task" and the cursor
  `watch` printed on stderr, so the user or a later run re-enters with
  `--since <cursor>`. Do not loop back into `watch` on your own.
- **Round cap.** `message` exits 1 with an `Error:` line naming the round cap.
  The verb has already posted `failed` (reason `round-cap`) on the task; report
  that the task hit the round cap and stop. Do not post again on it.
- **Any other failure.** Any verb exiting non-zero: relay its `Error:` line
  verbatim and stop. Do not retry with altered flags or work around it.

## Foreground only

`watch` runs in the foreground, inside the one tool call that waits on it.
Never background it, detach it, or wrap it in a poll loop that outlives the
call — and a delegated worker never runs `watch` in the background either. A
backgrounded wait answers a turn after you have stopped watching for it.

## Prose only

This skill posts prose. You **never edit, commit, or push code** while working
a room task — no Edit or Write on a source file, no `git commit`, no
`git push`. Read the code you need to answer, then answer in words.

- A task that needs a code change gets an `input-required` reply to the asker
  that names the hand-off: `/s:fix` for a defect against documented behavior,
  `/s:plan` for new or changed behavior. Doing that work is the hand-off
  skill's job, not this one's.
- A `review-finding` the head already fixes is closed `completed` with a
  one-line note naming the commit that addressed it (step 4).

## Report

Close every turn with a short report: the PR, the tasks you answered and the
state you left each in, and why the turn ended — an empty wait with its cursor,
a round cap, or the failing verb's `Error:` line.
