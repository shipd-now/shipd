<!-- doc-type: how-to -->

# Run an agent's turn in a multi-agent PR

A pull request's room is its comment thread. Agents and people open tasks
there and take turns on them. The `shipd room` verbs read and write the room,
and `/s:room` runs one agent's turn through those verbs.
[Multi-agent PR](multi-agent-pr.md) explains the model this guide runs.

This guide walks one agent through one turn: join, read, wait, reply, and
close. Run `shipd room --help` for every verb's flags. Every verb takes a pull
request URL as `<pr>`, or `--repo <owner/name>`, so it needs no checkout of
that repository. A URL and a `--repo` naming different repositories fail.

## Before you start

- The repository has an open pull request, and you have signed in to `gh`.
- The agent has a name. The verbs read it from `--agent`, then from the
  `SHIPD_ROOM_AGENT` environment variable, then from the `room.agent` key.
- No name resolves? The verbs stop with a usage error. Set one first.

[Customising shipd](customise.md) documents the `room` key and its two
members, `agent` and `max_rounds`.

## Run a turn with the skill

1. Open a session in the repository.
2. Run `/s:room 412`, or run `/s:room` alone for the current branch's pull
   request.
3. Read the report at the end of the turn.

The skill runs the steps below for you. Run them by hand to see each verb.

## Run a turn by hand

1. Join the room. The card names the skills this agent answers:

   ```sh
   shipd room join 412 --skill review-finding --skill question --skill status
   ```

   `join` edits only the one-line card comment it posted, even when the
   agent's card also appears in the review summary. Agent messages open with
   `☕ agent · role (for @login)` and end with `<sub>☕ Posted by Shipd</sub>`;
   `join --role author|reviewer|ci` sets the role.

2. Read the room's cards and open tasks:

   ```sh
   shipd room list 412
   ```

3. Wait for a task that is this agent's turn. Start the cursor at `0`:

   ```sh
   shipd room watch 412 --since 0 --timeout 540
   ```

   `watch` prints one JSON line, with the task id and a `cursor` value, for
   each task that is this agent's turn. Give the tool call its own timeout
   above 540 seconds (on Claude Code, a Bash `timeout` of `600000` ms).

4. Claim the task before you work on it:

   ```sh
   shipd room message 412 "Reading the parser now" --task 7 --state working
   ```

5. Post the answer with an explicit state:

   ```sh
   shipd room message 412 "The cap applies per task" --task 7 --state completed
   ```

   Ask the asker instead with `--state input-required --to <asker>`.

   The reply removes the agent's own `working` claim from step 4. Each turn
   then shows as one comment, headed by the speaker, addressee, and state.

6. Run `watch` again, with the last line's `cursor` as the `--since` value.

## Stay on the pull request

Run `/s:room 412 stay` to keep the agent on the pull request for the whole
review. An empty wait does not end the turn. The skill runs `watch` again
with the cursor from stderr, and it works each task as it arrives. Each
`watch` call still runs in the foreground with `--timeout 540`.

A stay turn ends in one of these ways:

- The pull request merges or closes. `watch` prints a `closed` line, and the
  skill reports and stops.
- A task hits the round cap, or a verb fails.

## Close a task

`close` posts a task's terminal message. Close a review finding that the head
already fixes, and name the commit:

```sh
shipd room close 412 "Fixed in a1b2c3d" --task 9 --state completed
```

## Know when a turn ends

Without `stay`, a turn ends in one of four ways:

- **The pull request ends.** `watch` prints a `closed` line when the pull
  request merges or closes. Its `open` array lists tasks still `working` or
  `input-required`. Report them as unresolved, then stop.
- **No task arrives.** `watch` exits `0` with empty output after the timeout.
  It prints the cursor on stderr. Pass that cursor to the next `watch`.
- **The round cap stops the task.** A task gets a fixed count of rounds,
  counted across every agent. The `room.max_rounds` key sets that count, and
  the default is 6. At the cap, `message` posts `failed` and exits `1`.
- **A verb fails.** Any other non-zero exit prints one `Error:` line. Read the
  line and fix the cause.

Run `watch` in the foreground only. A wait in the background answers a turn
after the agent has stopped listening.

## Merge from a clear room

Before `gh pr merge`, a `reviewer` agent runs `shipd room list 412 --open
--json`. It merges only when `tasks` is empty. Otherwise it keeps watching
(`stay`), or reports the open tasks and stops.

## Keep the room to prose

`/s:room` posts prose, with one exception. An agent whose card role is
`author` commits a finding's fix to its own pull request, then closes the task
naming the commit. It must be the PR's author, because agents declare the
role themselves, and the head must be in the same repository. It needs the PR
head branch checked out and a clean tree. It runs the tests that cover the
change and pushes without `--force`. Any failed check falls back to the prose
hand-off.

Every other role never edits, commits, or pushes code. A task that needs a
code change gets an `input-required` reply that names the next skill:

- `/s:fix` fixes a defect against the documented behavior.
- `/s:plan` plans new or changed behavior.

## See also

- [Customising shipd](customise.md) — the `room` key.
- [Semantic review](semantic-review.md) — the gate that posts review findings.
- [Room wake reference](room-wake-reference.md) — the Actions wake, no session.
- [Agent identity](agent-identity.md) — a second account, checked by `whoami`.
- [Run two agents unattended](room-run.md) — a local loop of headless turns.
