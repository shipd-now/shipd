---
name: room
description: >-
  Hold this agent's turn in a pull request's room: join the room with a card,
  read it, wait in the foreground for a task that is this agent's turn, reply
  in prose with an explicit task state, and stop at an empty wait (or, with
  `stay`, when the pull request closes), the round cap, or any failing verb.
  Posts prose — only an agent whose card role is `author` may fix a
  `review-finding` on its own pull request's head branch and commit it; every
  other role never edits, commits, or pushes code and hands off to `/s:fix`
  or `/s:plan`. Use when asked
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

You are invoked as `/s:room [<pr>] [stay]`. `<pr>` is a pull request number,
URL, or branch. Every verb requires it, so when it is omitted, pass the current
branch (`git branch --show-current`) as `<pr>` and the verbs resolve that
branch's pull request. Pass every verb the user's pull request URL as `<pr>`,
or `--repo <owner/name>` when the user names a repository, so the verb never
reads the repository from the working directory. With `stay`, you stay on the pull request for the whole
review: an empty wait does not end the turn, and you keep taking tasks until
the pull request closes.

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
   it does not extend it. When the user names this agent's role, add
   `--role author|reviewer|ci`; pass it on every join, because a rejoin
   without it clears the role.
2. **Read the room.** `shipd room list <pr>` prints the cards and the open
   tasks. Show the user a compact summary of it.
3. **Wait for your turn — in the foreground.**
   `shipd room watch <pr> --since <cursor> --timeout 540`, with cursor `0` on
   entry. `watch` blocks until a task is this agent's turn, then prints one
   NDJSON line per surfaced task (fields: `task`, `skill`, `text`, `url`,
   `cursor`, and the rest of the task) and exits 0. The nine-minute timeout
   bounds every wait; never drop it. Give the tool call that runs `watch` its
   own timeout above 540 seconds (on Claude Code, a Bash `timeout` of
   `600000` ms), so the harness never moves the wait to the background.
4. **Work each surfaced task**, one line at a time, and only the tasks `watch`
   printed — never act on a task `watch` did not surface, even one `list`
   showed:
   - Claim the turn first:
     `shipd room message <pr> "<what you are doing>" --task <id> --state working`.
   - Do the work (see **Prose, and the author's fix** below).
   - Reply with the outcome, always naming the state:
     `shipd room message <pr> "<answer>" --task <id> --state completed` when
     the task is done, or
     `shipd room message <pr> "<question>" --task <id> --state input-required --to <asker>`
     when you need the asker to answer or act.
   - A `review-finding` task whose finding the PR head already addresses is
     closed, not re-litigated: `shipd room close <pr> "<one line naming the commit>" --task <id> --state completed`.
5. **Re-enter step 3** with the `cursor` from the last NDJSON line `watch`
   printed. With `stay`, also re-enter after an empty wait, using the cursor
   `watch` printed on stderr.

Every `message` call names `--state` explicitly; never lean on the verb's
default state.

## When to stop

End the turn and report — posting nothing further — on any of these:

- **Room closed.** `watch` printed a `closed` line (`{"closed": "merged"}` or
  `{"closed": "closed"}`): the pull request merged or closed. Post nothing, not
  even on a task printed before it; report, and stop. When the line's `open`
  array is not empty, report those tasks as unresolved, each with its id and
  state.
- **Empty wait** (a turn without `stay`). `watch` exits 0 with empty stdout: no
  task became this agent's turn within the timeout. Report "no actionable
  task" and the cursor `watch` printed on stderr, so the user or a later run
  re-enters with `--since <cursor>`. Do not loop back into `watch` on your
  own. With `stay`, the skill re-enters `watch` with that cursor, each call
  still in the foreground with `--timeout 540`, and the turn goes on until a
  `closed` line, the round cap, or a failing verb.
- **Round cap.** `message` exits 1 with an `Error:` line naming the round cap.
  The verb has already posted `failed` (reason `round-cap`) on the task; report
  that the task hit the round cap and stop. Do not post again on it.
- **Any other failure.** Any verb exiting non-zero: relay its `Error:` line
  verbatim and stop. Do not retry with altered flags or work around it.

## Merging

Before `gh pr merge`, with or without `--auto`, an agent whose card role is
`reviewer` runs `shipd room list <pr> --open --json` and merges only when
`tasks` is empty. A task still `working` or `input-required` blocks the merge:
with `stay`, keep watching; otherwise report the open tasks and end the turn.

## Approving

Before any approving or change-requesting review, run `shipd room whoami <pr>`.
It prints the acting login, the author and the credential source, and exits 1
with an `Error:` line when the login is the author's or unreadable. On a
non-zero exit, relay the `Error:` line and stop: do not submit the review.

## Reviewing

A surfaced task addressed to you that asks for a review or re-review of the
pull request, when your card role is `reviewer`:

1. Claim it: `shipd room message <pr> "Reviewing <head>" --task <id> --state working`.
2. Run `shipd room whoami <pr>`. On a non-zero exit, relay the `Error:` line
   and stop without posting.
3. Run `/s:review <pr-url> status=auto room-agent=<to> room-to=<last_agent>`,
   taking `to` and `last_agent` from the task's watch line. It posts the shared
   ☕ shipd summary comment, anchored findings that open `review-finding` tasks
   for the asker, and an approve or request-changes review whose body carries
   the full summary.
4. Close the task: `shipd room close <pr> "<verdict>: <summary comment url>" --task <id> --state completed`.

`status=auto` follows one rule. Where `.github/workflows/copilot-review-gate.yml`
exists on the pull request's base commit, the CI gate owns `semantic-review`
and the post sets no status. Where that file is absent (the read returns 404),
the post sets `semantic-review` itself. On any other read failure it sets none.

Never submit a separate freeform `gh pr review`: the review `/s:review` posts
is the only one. A re-review after a push runs the same command; the one
summary comment is edited in place, and a new full review lands on the new
head. Posting that review is not a code change, so the no-code rule below
still holds.

## Foreground only

`watch` runs in the foreground, inside the one tool call that waits on it.
Never background it, detach it, or wrap it in a poll loop that outlives the
call — and a delegated worker never runs `watch` in the background either. A
backgrounded wait answers a turn after you have stopped watching for it.

## Prose, and the author's fix

Your role is the `role` on this agent's own card in
`shipd room list <pr> --json`. Only the `author` role may change code, and only
for a surfaced `review-finding` task on its own pull request:

1. The role is self-declared, so also check
   `gh pr view <pr> --json author,headRefName,isCrossRepository`: the
   `author.login` equals `gh api user --jq .login`, `isCrossRepository` is
   `false`, and `headRefName` equals `git branch --show-current`. Check
   `git status --porcelain` prints nothing.
2. Make the smallest fix, and run the tests that cover the files you touched.
3. `git commit`, then plain `git push` — never `--force`, never another branch.
4. `shipd room close <pr> "Fixed in <short sha>: <one line>" --task <id> --state completed`.
   It replies on the finding's review thread and resolves that thread.

If any check or test fails, push nothing and use the prose hand-off below.

Every other role — `reviewer`, `ci`, or none — never edits, commits, or pushes
code: no Edit or Write on a source file, no `git commit`, no `git push`. Read
the code you need to answer, then answer in words.

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
