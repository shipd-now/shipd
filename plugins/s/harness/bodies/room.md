<!-- description: Take this agent's turn in a pull request's room — join, read, wait for a task, reply in prose, and stop cleanly. -->
# /s:room — take this agent's turn in a PR room

You are one agent in a pull request's room: the PR's comment thread, where
agents and people open tasks for each other and take turns on them. Every read
and write goes through the `shipd room` verbs; never hand-write a room comment.
Invoked as `/s:room [<pr>]` — a PR number, URL, or branch. Every verb
requires it: when it is omitted, pass the current branch
(`git branch --show-current`) as `<pr>`.

<!-- include:preamble -->

The verbs resolve the acting agent's name — `--agent`, then
`SHIPD_ROOM_AGENT`, then the `room.agent` config member. Never invent one:
when none resolves, relay the verb's usage error, name those three sources,
and stop.

You post prose only. You never edit, commit, or push code while working a
room task. A task that needs a code change gets an `input-required` reply to
the asker naming the hand-off — `/s:fix` for a defect against documented
behavior, `/s:plan` for new or changed behavior.

<!-- if:background-tasks -->
1. **Join.** `shipd room join <pr> --skill review-finding --skill question
   --skill status` — the default card; skills the user names replace that list.
2. **Read the room.** `shipd room list <pr>`, summarised for the user.
3. **Wait, in the foreground.** `shipd room watch <pr> --since <cursor>
   --timeout 600`, cursor `0` on entry. It prints one JSON line per task that
   is this agent's turn and exits 0. Never background, detach, or poll-loop
   `watch` — a delegated worker never runs it in the background either.
4. **Work each printed task, and only those.** Post
   `shipd room message <pr> "<doing>" --task <id> --state working`, do the
   work, then reply with an explicit state: `--state completed`, or
   `--state input-required --to <asker>`. A `review-finding` the head already
   addresses is closed with `shipd room close <pr> "<commit>" --task <id>
   --state completed`.
5. **Re-enter step 3** with the last printed line's `cursor`.

Stop and report, posting nothing more, when `watch` exits 0 with empty stdout
(report the cursor it printed on stderr; do not loop again), when `message`
exits 1 with the round-cap `Error:` (the verb already posted `failed`), or
when any verb exits non-zero (relay its `Error:` line).
<!-- else -->
This harness cannot hold a long foreground wait, so read the room once:

1. **Read the room.** `shipd room list <pr> --json` — one JSON object holding
   the room's cards and tasks.
2. **Report the actionable tasks** — those open and addressed to this agent,
   or asking for a skill on its card — with each task's id, skill, and last
   message, then end the turn. Do not post, and do not wait for new tasks;
   the user re-invokes this command, on a harness that can wait, to answer.
<!-- end -->
<!-- if:file-references -->
The watch output's fields and the full stop list are written out in
{refs}/room.md.
<!-- end -->
