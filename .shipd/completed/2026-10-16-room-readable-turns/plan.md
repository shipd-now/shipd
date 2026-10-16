# room-readable-turns
Status: verified

## Idea

Make a pull request's room readable to a person and let each user's agent stay
on the pull request for the whole review.

### Motivation

A person reading a PR room cannot follow it: PR 12 on the unkannybanny test
repository shows eleven comments for three questions, no speaker names, and a
CI reply full of tool trace with its code fences stripped. And `/s:room` takes
one turn and stops, so the intended model, where the author's agent and the
reviewer's agent each keep a watcher on the pull request, cannot run.

### Details

- One comment per turn: when an agent replies on a task it had claimed with
  `working`, the verb posts the reply and deletes its own claim comment.
- Every agent message opens with a header line naming the speaker, the
  addressee, and the state.
- An Agent Card renders as one muted line.
- The Actions wake runs the Copilot CLI in silent mode and asks for GitHub
  markdown, so a reply is only the answer, with fenced code.
- `watch` ends when the pull request is merged or closed and says so.
- `/s:room <pr> stay` keeps the agent on the pull request: an empty wait
  re-enters `watch`, and the turn ends only when the pull request closes, a
  round cap hits, or a verb fails.

Affected capabilities: `pr-room` (modified), `shipd-room` (modified). Impact:
`plugins/s/skills/room/scripts/room.py`, `room_schema.py`,
`plugins/s/integrations/copilot/room-wake.yml`,
`plugins/s/skills/room/SKILL.md`, the four room test files,
`docs/pr-room.md`, and the plugin version.

### Non-goals

- No agent changes code from the room; `/s:room` stays prose-only and the CI
  wake stays read-only.
- No change to the bare-harness body: harnesses without `background-tasks`
  still read the room once.
- The Actions wake is kept, off unless a repository sets the variable and the
  secret; it is not removed.
- No cleanup of comments already posted on existing pull requests.

## Implementation

- **Post the reply, then delete the claim.** `message --task` and `close`
  check the task's last comment: when it is an issue comment whose room
  Message was posted by the acting agent at state `working`, the verb posts
  the new Message as a new comment, then deletes that claim comment with
  `gh api -X DELETE repos/<repo>/issues/comments/<id>`. A failed delete prints
  `warning: could not remove claim comment <id>` on stderr and the verb still
  exits `0`, because the reply is posted. Rejected: editing the claim in
  place. `watch` advances its cursor by comment id, so a reply written into an
  older comment would never surface to the other agent's watcher.
- **The round is unchanged by this.** `next_round` already keeps the round
  when the same agent posts again, so the reply carries the claim's round and
  the cap counts exactly as before.
- **Speaker header.** `room_schema._message_prose` renders an agent Message as
  a first line `**☕ shipd** · **<agent>** → <to> · <state>`, the brand mark matching the review gate's `**☕ shipd** semantic review` line (the ` → <to>` part only when
  `metadata.to` is set, the ` · <state>` part only when `metadata.state` is
  set), a blank line, then the text. A human message (`role` `user`) renders
  its text alone. The marker line stays first and byte-for-byte unchanged in
  shape; parsing reads only the marker, so the header never reaches `text`.
- **One-line card.** `_card_prose` renders
  `<sub>**☕ shipd** · **<name>** joined the room from <harness> · skills: <a, b></sub>`,
  dropping the ` from <harness>` and ` · skills: …` parts when empty; a set
  description follows on its own paragraph as before.
- **Watch ends with the pull request.** Each poll also reads
  `gh pr view <n> --json state`. When the state is `MERGED` or `CLOSED`,
  `watch` prints one stdout line `{"closed": "merged"|"closed", "context":
  "<context>", "cursor": "<issue>:<review>"}`, prints
  `watch: <context> is <merged|closed>; the room is closed` on stderr, and
  exits `0`. A task surfaced in the same poll is printed first. Rejected: a new
  exit code, which would collide with the CLI conventions' usage and failure
  codes and break the wake guard's empty-stdout test.
- **The wake's reply.** The `run` job calls
  `copilot -p "$prompt" -s --allow-all-tools`. The prompt gains one sentence:
  write the reply in GitHub-flavoured markdown, put code in fenced blocks with
  a language, and do not describe the search steps taken. Observed locally:
  `copilot -p … -s` prints only the final answer with fences intact, while the
  default mode prints the tool trace and run statistics. The guard keeps its
  `picked up by the CI wake` claim; the reply job's `message` and `close`
  calls now delete it.
- **Stay mode.** `/s:room [<pr>] [stay]`. Without `stay` the skill behaves as
  today. With `stay`, an empty wait re-enters `watch` with the cursor `watch`
  printed on stderr, each `watch` call still runs in the foreground with
  `--timeout 600`, and the turn ends on a `closed` line, a round cap, or any
  failing verb. Each surfaced task is worked and reported as it happens.
  Rejected: a background watcher, which the foreground-only rule forbids
  because nothing would resume the agent.
- **Version.** One patch above `main`'s `plugins/s/.claude-plugin/plugin.json`
  at build time.

Risk: deleting the claim races a second agent reading the room between the
reply and the delete; that agent sees the task completed either way, since
state comes from the newest Message. Risk: the extra `gh pr view` per poll
adds one API call every 20 seconds per watcher, well inside GitHub's limits.

## Readiness attestation

### Problem and motivation

PR rooms are unreadable to people, and the two-watcher model the user
described cannot run because `/s:room` stops after one turn.

Evidence:

- https://github.com/mikkel-bergmann/unkannybanny/pull/12 holds eleven room
  comments for three questions: three `picked up by the CI wake`, two
  `closed: failed`, and a card, all posted as `github-actions[bot]` or the
  user's own login.
- The stored reply text on task 6203288932 holds the tool trace lines and no
  code fences.
- `plugins/s/skills/room/SKILL.md` "When to stop" ends the turn on an empty
  wait.

### Scope and non-goals

The change touches the room verbs, schema rendering, the wake template, and
the room skill; code-changing agents and the bare-harness body stay out.

Evidence:

- In scope: `room.py` `cmd_message`, `cmd_close`, `cmd_watch`;
  `room_schema.py` `_card_prose`, `_message_prose`; `room-wake.yml` run step.
- Out of scope: requirement `room-skill-no-code` and `room-skill-body` stay
  unmodified.

### Affected capabilities and files

Two capabilities, eight modified requirements.

Evidence:

- `pr-room`: `room-message-verb` (base 9308e29c74dd), `room-close-verb`
  (f8bf3e10b7b0), `room-agent-card` (9ad2ee39bfc7), `room-message-shape`
  (8f9f5069d0d5), `room-watch-exit` (ab638884d0c6),
  `room-wake-workflow-template` (257e18027686).
- `shipd-room`: `room-skill-loop` (1bb3c42ea4fc), `room-skill-stops`
  (ce7a0352ba6e).
- Runnable premise: `copilot -p "<prompt>" -s --no-color` printed only the
  answer with a fenced js block; without `-s` it appended `Changes` and
  `AI Credits` lines, and in the wake run it interleaved the tool trace.
- Runnable premise: `gh api repos/mikkel-bergmann/unkannybanny/issues/12/comments`
  listed the eleven comments above.
- `room.py` `_is_new` and `_advance` compare comment ids, so an edited
  comment is never new to a watcher; this is why the claim is deleted.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- One comment per turn, no code changes by the CI agent, keep the wake off by
  default, and fold the watcher in: settled by the user.
- Post-then-delete over edit-in-place: settled by investigation of the watch
  cursor.
- Header and card formats, the `closed` stdout line, and the `stay` keyword:
  settled by investigation.
