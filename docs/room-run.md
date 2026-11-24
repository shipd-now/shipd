<!-- doc-type: how-to -->

# Run agents in a pull request's room

A pull request's room is its comment thread, where agents and people take turns on tasks, as
[Multi-agent PR](multi-agent-pr.md) explains. [`/s:room`](multi-agent-pr.md) runs one agent's turn in a session.
`shipd room run` joins once, then answers each task with a headless `/s:room` turn. It spends
tokens only when a task arrives.

## When to use it

- **One turn in a session.** Run `/s:room` and read its report.
- **A whole review.** Run `/s:room` with `stay` to keep the agent on the pull request.
- **A pull request carried to merge.** Start two unattended listeners, an author and a reviewer.
- **A whole repository.** Start one reviewer listener with `--repo`.

The Actions wake serves a CI agent with no session; see [Room reference](room-wake-reference.md).

## How to run it

### Before you start

- The repository has an open pull request (the examples use `412`), and you signed in to `gh`.
- The verbs read the agent name from `--agent`, then `SHIPD_ROOM_AGENT`, then the `room.agent`
  key. No name resolves? The verbs stop with a usage error. See [Customising shipd](customise.md).
- For unattended runs, you installed the review gate with [`/s:gate`](copilot-review.md) and applied the merge rules
  with [`shipd gate rules apply`](pr.md).
- You signed in to your harness on each machine that runs a listener. The run first sends one
  tiny probe turn. If you have signed out, it stops with one `Error:` line naming the sign-in
  command (`claude auth login`) and posts nothing.
- A second GitHub account for the reviewer is optional; see [Give an agent its own GitHub
  account](agent-identity.md).

### 1. Take one turn in a session

1. Open a session in the repository.
2. Run `/s:room 412`, or run `/s:room` alone for the current branch's pull request.
3. Read the report at the end of the turn.

Run `/s:room 412 stay` to keep the agent on the pull request for the whole review. An empty wait
does not end the turn. The skill runs `watch` again with the cursor from stderr, and works each
task as it arrives. The turn ends on a `closed` line, when the pull request merges or closes. A
task at the round cap, or a failed verb, also ends it.

### 2. Take a turn by hand

The skill runs these verbs for you. Run them by hand to see each one:

```sh
shipd room join 412 --skill review-finding --skill question --skill status
shipd room list 412
shipd room watch 412 --since 0 --timeout 540
shipd room message 412 "Reading the parser now" --task 7 --state working
shipd room message 412 "The cap applies per task" --task 7 --state completed
shipd room close 412 "Fixed in a1b2c3d" --task 9 --state completed
```

Give the `watch` tool call its own timeout above 540 seconds (on Claude Code, a Bash `timeout` of
`600000` ms). Run `watch` again with the last line's `cursor` as the `--since` value. Run `watch`
in the foreground only. A wait in the background answers a turn after the agent stops listening.
To hand a task back to its asker, reply with `--state input-required --to <asker>`.

### 3. Start the reviewer listener

In a checkout of the repository, point `gh` at the reviewer's account and run:

```sh
GH_CONFIG_DIR=~/.config/gh-reviewer shipd room run 412 --role reviewer --agent reviewer-b
```

The reviewer answers each review task with [`/s:review`](semantic-review.md). That posts the ☕ shipd summary, inline
findings for the author, and a review with the full summary. The reviewer sets `semantic-review`
only when `.github/workflows/copilot-review-gate.yml` is absent from the base branch.

Omit the number and pass `--repo`, and one reviewer answers every pull request:

```sh
GH_CONFIG_DIR=~/.config/gh-reviewer shipd room run --repo o/r --role reviewer --agent reviewer-b
```

It keeps each cursor and session in its `--state` file, and `Ctrl-C` stops it. It takes only the
`reviewer` and `ci` roles, and one agent runs once per repository.

### 4. Start the author listener

In the pull request's worktree, keep the author's default `gh` login and run:

```sh
shipd room run 412 --role author --agent author-a --request-review reviewer-b
```

The `--request-review` flag opens the first review task for `reviewer-b` once, after the author
joins. To open it by hand instead, skip the flag and run
`shipd room message 412 --new --to reviewer-b --skill review-finding "Please review this pull request."`.

The listener takes a turn on each finding: it fixes the code and pushes, or replies with a
reason. Only an agent with role `author` commits a finding's fix to its own pull request; every
other role answers in prose.

When the head moves, the author run opens one re-review task. Any push counts: the author's own
turn, a person, or another tool. The task goes to each reviewer who filed a finding to the
author, and to each agent that `--request-review` named. Each reviewer gets one task per head.
The run also spends one turn on the CI reviewer's "Fix required" review of the current head;
[Room reference](room-wake-reference.md) lists the rules.

### 5. Watch the flow

Four actors carry [unkannybanny #40](https://github.com/mikkel-bergmann/unkannybanny/pull/40)
from opened to merged in under 20 minutes. Each step below gives the #40 instance in brackets.

- **The author agent** joins the room, asks for a review, fixes findings, and pushes.
- **The room reviewer agent** reviews each head with `/s:review`, and approves it or files
  findings to the author.
- **The CI reviewer** is the `semantic-review` gate in GitHub Actions. It reviews each push.
- **GitHub** enforces the merge rules and merges the pull request once they hold.

1. The author opens the pull request, arms auto-merge, joins the room, and asks for a review.
   [`author-a` joined and addressed `reviewer-b` at head `70a85ba`.]
2. The CI reviewer asks for changes on a blocking finding. [It requested changes on `70a85ba`.]
3. The room reviewer claims the head, reviews it, and approves it or files findings.
   [`reviewer-b` approved with three low findings.]
4. The author takes a turn on the findings, fixes the code, and pushes. [`author-a` pushed
   `a9877ec`.]
5. GitHub dismisses the approval on the old head, because the merge rules dismiss stale
   approvals. [GitHub dismissed the approval of `70a85ba`.]
6. The CI reviewer reviews the new head and approves it. [It approved `a9877ec`.]
7. The author listener sees the moved head and opens a re-review task. [`author-a` asked
   `reviewer-b` to re-review `a9877ec`.]
8. The room reviewer reviews the new head and approves it. [`reviewer-b` approved `a9877ec`.]
9. GitHub merges the pull request once two approvals and every required check hold. [#40
   squash-merged and deleted its branch.]

### 6. Merge from a clear room

Before `gh pr merge`, a `reviewer` agent runs `shipd room list 412 --open --json`. It merges only
when `tasks` is empty. Otherwise it keeps watching (`stay`), or reports the open tasks and stops.

A reviewer runner claims each head, so one review posts per head, and sets the
`room-review/<agent>` status; see [Review claims](room-review-claims.md).

## Reference

- [Room reference](room-wake-reference.md) — the verbs, `run` flags, result line, Actions wake.
- [Multi-agent PR](multi-agent-pr.md) — the model.
- [Give an agent its own GitHub account](agent-identity.md) — an optional reviewer account.
- [Review claims](room-review-claims.md) — one review per head.
- [Customising shipd](customise.md) — the `room` key.
- [Semantic review](semantic-review.md) — the gate that posts review findings.
- [Copilot review](copilot-review.md) — the CI reviewer's workflow.
