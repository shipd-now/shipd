<!-- doc-type: how-to -->

# Run an agent's turn in a multi-agent PR

A pull request's room is its comment thread. Agents and people open tasks
there and take turns on them. The `shipd room` verbs read and write the room,
and `/s:room` runs one agent's turn through those verbs.
[Multi-agent PR](multi-agent-pr.md) explains the model this guide runs.

This guide walks one agent through one turn: join, read, wait, reply, and
close. Run `shipd room --help` for every verb's flags.

## Before you start

- The repository has an open pull request, and you have signed in to `gh`.
- The agent has a name. The verbs read it from `--agent`, then from the
  `SHIPD_ROOM_AGENT` environment variable, then from the `room.agent` key.
- No name resolves from any of the three sources? The verbs stop with a usage
  error. Set one before you continue.

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

2. Read the room's cards and open tasks:

   ```sh
   shipd room list 412
   ```

3. Wait for a task that is this agent's turn. Start the cursor at `0`:

   ```sh
   shipd room watch 412 --since 0 --timeout 600
   ```

   `watch` prints one JSON line for each task that is this agent's turn.
   Each line carries the task id and a `cursor` value.

4. Claim the task before you work on it:

   ```sh
   shipd room message 412 "Reading the parser now" --task 7 --state working
   ```

5. Post the answer with an explicit state:

   ```sh
   shipd room message 412 "The cap applies per task" --task 7 --state completed
   ```

   Ask the asker instead with `--state input-required --to <asker>`.

6. Run `watch` again, with the last line's `cursor` as the `--since` value.

## Close a task

`close` posts a task's terminal message. Close a review finding that the head
already fixes, and name the commit:

```sh
shipd room close 412 "Fixed in a1b2c3d" --task 9 --state completed
```

## Know when a turn ends

A turn ends in one of three ways:

- **No task arrives.** `watch` exits `0` with empty output after the timeout.
  It prints the cursor on stderr. Pass that cursor to the next `watch`.
- **The round cap stops the task.** A task gets a fixed count of rounds,
  counted across every agent. The `room.max_rounds` key sets that count, and
  the default is 6.
  At the cap, `message` posts `failed` on the task and exits `1`.
- **A verb fails.** Any other non-zero exit prints one `Error:` line. Read the
  line and fix the cause.

Run `watch` in the foreground only. A wait in the background answers a turn
after the agent has stopped listening.

## Keep the room to prose

`/s:room` posts prose. It never edits, commits, or pushes code. A task that
needs a code change gets an `input-required` reply that names the next skill:

- `/s:fix` fixes a defect against the documented behavior.
- `/s:plan` plans new or changed behavior.

## See also

- [Customising shipd](customise.md) — the `room` key.
- [Semantic review](semantic-review.md) — the gate that posts review findings.
- [Room wake reference](room-wake-reference.md) — the Actions wake that runs a
  turn with no session.
- [Multi-agent PR](multi-agent-pr.md) — the model.
