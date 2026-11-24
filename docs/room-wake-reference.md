<!-- doc-type: reference -->

# Room reference

This page lists the `shipd room` verbs and the Actions wake. [Run agents in a pull request's
room](room-run.md) walks the task, and [Multi-agent PR](multi-agent-pr.md) explains the model.
[Review gate reference](copilot-review-reference.md) covers the review gate, which
`shipd copilot` manages through the same verb.

The room wake lets a PR-room task wake a repository's CI agent. No developer session needs to
run. A workflow runs the Copilot CLI on the task and posts its reply to the room.

## When to use it

- **Install the wake** when a CI agent answers addressed tasks with no session.
- **Run a local `shipd room run`** when two agents answer each other. The wake cannot serve
  them, because a reply from the workflow token wakes no other workflow.

## How to run it

```bash
shipd copilot add --room       # install or refresh the six files
shipd copilot update           # refresh the gate files, and these six when installed
shipd copilot remove --room    # delete them and prune .github/shipd-room
shipd copilot                  # report both sets; the wake set comes last
```

Set the variable with `gh variable set SHIPD_ROOM_AGENT --body <name>`. Use a fine-grained PAT
that carries the "Copilot Requests" permission as the `COPILOT_GITHUB_TOKEN` secret.

## Reference

### The room verbs

| Verb | What it does |
| --- | --- |
| `join` | Post or refresh this agent's card. |
| `list` | Show the room's cards and tasks. |
| `whoami` | Show the acting account; `may_approve` is false when it authored the pull request, refused then only under `distinct_reviewer`. With `--author`, refused unless it did. |
| `message` | Open a task or advance one. |
| `close` | Post a task's terminal message. |
| `watch` | Wait for a task that is this agent's turn. |
| `run` | Join once, then answer each task with a headless `/s:room` turn. |

Run `shipd room --help` for every verb's flags. Every verb takes a pull request URL as `<pr>`,
or `--repo <owner/name>`, so it needs no checkout of that repository. A URL and a `--repo`
naming different repositories fail.

`join` edits only the one-line card comment it posted, even when the agent's card also appears
in the review summary. Agent messages open with `☕ agent · role (for @login)` and end with
`<sub>☕ Posted by Shipd</sub>`; `join --role author|reviewer|ci` sets the role.

`watch` prints one JSON line, with the task id and a `cursor` value, for each task that is this
agent's turn. A `message` reply removes the agent's own `working` claim. Each turn then shows as
one comment, headed by the speaker, addressee, and state.

### How a turn ends

Without `stay`, a turn ends in one of four ways:

- **The pull request ends.** `watch` prints a `closed` line when the pull request merges or
  closes. Its `open` array lists tasks still `working` or `input-required`. Report them as
  unresolved, then stop.
- **No task arrives.** `watch` exits `0` with empty output after the timeout. It prints the
  cursor on stderr. Pass that cursor to the next `watch`.
- **The round cap stops the task.** A task gets a fixed count of rounds, counted across every
  agent. The `room.max_rounds` key sets that count, and the default is 6. At the cap, `message`
  posts `failed` and exits `1`.
- **A verb fails.** Any other non-zero exit prints one `Error:` line. Read the line and fix the
  cause.

Run `watch` in the foreground only. A wait in the background answers a turn after the agent has
stopped listening.

### Run flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--max-turns` | `10` | Stop after this many turns. Repo mode parks a pull request at this count. |
| `--budget` | `14400` | Stop after this many seconds. Repo mode has no limit by default. |
| `--state` | `~/.shipd/room-run/<owner>/<name>/<agent>.json` | Repo mode only: the cursor and session file. |
| `--harness` | `claude` | The harness that runs each turn. |
| `--model` | harness default | A model id or an effort level. |
| `--turn-timeout` | `1800` | Seconds one turn may run. |
| `--interval` | `30` | Seconds between polls. |
| `--request-review` | none | Open a review task for this agent. Repeatable. Author role only. |
| `--ci-reviewer` | `github-actions[bot]` | The CI reviewer whose fix-required review starts an author turn. Empty disables. Author role only. |

In repo mode, the run lists the open pull requests with one `gh` call and spends no tokens while
it waits. It runs one turn at a time, on each pull request with a task for the agent. It skips
pull requests its own account authored. A restart resumes every conversation. A second run of one
agent, or a single-PR run of it, refuses to start, whatever its `--state`.

### The result line

`run` prints one JSON line on stdout and progress on stderr:

```json
{"turns": 2, "session_id": "s-1", "reason": "closed", "context": "o/r#412", "cursor": "2100:0", "closed": "merged"}
```

The `reason` value says why the run stopped:

- `closed` — the pull request merged or closed. The `closed` key says which.
- `turn-cap` — the run took `--max-turns` turns.
- `budget` — `--budget` seconds passed, or a reviewer or `ci` wait ended with no task.
- `turn-failed` — a turn failed. The `failure` key says why.
- `watch-failed`, `claim-failed` — the wait or the claim raised a room error. The `failure` key
  says why.
- `preflight-failed` — repo mode: a turn failed, then the harness check failed.
- `interrupted` — repo mode: you pressed Ctrl-C.

The run exits `0` for `closed`, `turn-cap`, and `budget`. It exits `1` with one `Error:` line for
a failure. It never retries a failed turn. In repo mode, a failed turn parks only its pull
request.

### The CI reviewer's review

An author run also reads the pull request's reviews. When the CI reviewer posts a "Fix
required" review of the current head, the run spends one turn on it. The prompt tells the
author to fix the findings and push, or to reply with the reason a finding is wrong. The turn
counts toward `--max-turns`.

- The review must come from the `--ci-reviewer` login, belong to the current head, and carry
  the fix-required marker as its verdict line. The run reads the verdict as the CI gate does:
  the last line that is a verdict marker. A marker quoted in prose, "Ship it" reviews, and
  comments start nothing.
- The run handles each review once. A reply does not clear the CI verdict. Only a new push
  re-runs the CI reviewer, and a person decides otherwise.

An author run waits in slices of four `--interval` periods and checks the reviews and the head
between slices. `--ci-reviewer ""` turns off only the reviews check; the run still waits in slices
and checks the head. Reviewer and `ci` runs ignore the flag and wait once over the whole budget.
The run also checks the head after each turn. If it cannot read the head, it warns once and opens
no re-review task. A rerun opens no task a head already has.

### What a turn may do

Every turn runs with `bypassPermissions`, as autopilot's turns do. Restrict each agent through
its GitHub account. A reviewer needs push permission for its review claims; see [Review
claims](room-review-claims.md).

`/s:room` posts prose, with one exception. An agent whose card role is `author` commits a
finding's fix to its own pull request, then closes the task naming the commit. It must be the
PR's author, because agents declare the role themselves, and the head must be in the same
repository. It needs the PR head branch checked out and a clean tree. It runs the tests that
cover the change and pushes without `--force`. Any failed check falls back to the prose hand-off.

Every other role never edits, commits, or pushes code. A task that needs a code change gets an
`input-required` reply that names the next skill:

- `/s:fix` fixes a defect against the documented behavior.
- `/s:plan` plans new or changed behavior.

### When a run stalls

- **The runner refuses to start with `another room run already serves`.** Another run of the
  same agent holds the lock on this machine. Stop that run, or keep it.
- **The reviewer refuses to start on push permission.** Its account cannot create the claim
  ref. Give that account write access to the repository.
- **The pull request stays blocked.** Run `gh pr checks <pr>` for a missing check, then resolve
  every open review thread. Each required check must pass on the current head.

### The managed files

`shipd copilot add --room` writes these six files and touches nothing else. The five runtime
files are byte-identical copies of the plugin's own files, at their plugin-relative paths under
`.github/shipd-room/`.

| File | Role |
| --- | --- |
| `.github/workflows/room-wake.yml` | The wake workflow. Its first line is the `# shipd-copilot v…` ownership marker. |
| `.github/shipd-room/.claude-plugin/plugin.json` | The plugin manifest. `room.py` reads its version for the agent card. |
| `.github/shipd-room/skills/room/scripts/room.py` | The room verbs the workflow runs: `watch`, `list`, `join`, `message`, and `close`. The bundled copy omits the modules `run` needs, so `run` prints one `Error:` line there; use `shipd room run` locally. |
| `.github/shipd-room/skills/room/scripts/room_schema.py` | The room comment schema that `room.py` reads and writes. |
| `.github/shipd-room/skills/build/scripts/spec_common.py` | The layered config reader that `room.py` imports. |
| `.github/shipd-room/skills/build/scripts/cli_common.py` | The shared CLI helpers that `room.py` imports. |

### The wake verbs

`update` refreshes the wake set only when `room-wake.yml` carries the ownership marker. It never
installs the wake set, and it leaves a `room-wake.yml` without the marker alone. `/s:gate
update` runs it.

Plain `add` and `remove` act on the four review gate files only. They never touch the wake set.
`remove --room` prunes each emptied directory under `.github/shipd-room/`, innermost first. It
stops at the first directory that still holds a file.

### Report states

Each wake file reports `installed`, `stale`, `foreign`, or `absent`. The workflow marker decides
ownership for all six files. A runtime file is `foreign` while the workflow carries no marker,
and `stale` when its bytes differ from the plugin's copy. The workflow reports `stale` while any
runtime file is not `installed`.

Where a wake path is `foreign`, both `add --room` and `remove --room` refuse and name the file.
`--force` overrides the refusal.

### Configuration

| Setting | Kind | Effect |
| --- | --- | --- |
| `SHIPD_ROOM_AGENT` | repository Actions variable | Names the CI agent. Unset, the workflow runs no job. |
| `COPILOT_GITHUB_TOKEN` | repository secret | The Copilot CLI's credential. Unset, the guard logs the gap and leaves the task alone. |

Only a comment whose `author_association` is `OWNER`, `MEMBER`, or `COLLABORATOR` wakes the
agent. An `issue_comment` run carries the repository's secrets whoever wrote the comment, so the
guard ignores comments from anyone else.

### How a wake runs

The workflow fires on a new issue comment or review comment. Three jobs run in turn.

- **guard** holds the workflow token. It runs `room.py watch --once` from the triggering
  comment, and acts only on a task addressed to the agent. It joins the room when the agent has
  no card, then posts `working` on the task.
- **run** holds the Copilot secret only. It checks out the pull request head without persisted
  credentials and runs a pinned Copilot CLI on the task.
- **reply** holds the workflow token on a fresh runner. It posts the reply to the asker, or
  closes the task as `failed` when the run failed.

The two credentials never share a job. Every `room.py` call runs under `env -i` with an
explicit `PATH`.

### The reply marker

A reply whose last non-blank line is exactly this line hands the task back to the asker:

```
<!-- shipd-room-reply: input-required -->
```

The reply job first strips the CLI's tool-call transcript blocks, then strips the marker and
posts the reply as `input-required`. Any other reply completes the task. A failed, cancelled,
or empty run closes the task with reason `wake-runner-failed`.

### Known limits

- **The bundle cannot run `run`.** `run` drives a local harness session, so the bundle leaves
  out its modules; use `shipd room run` from a developer machine.
- **Replies wake no other workflow.** The reply job posts with the workflow token, and GitHub
  starts no workflow run from that token's events. Two CI agents in one repository therefore never
  wake each other. A live session's `shipd room watch` still sees the reply. `shipd room run`
  keeps two local agents talking without the wake; see [Run agents in a pull request's
  room](room-run.md).
- **Fork review comments get no wake.** A review comment on a fork's pull request gets a read-only
  token and cannot write the room. A conversation comment runs with the base repository's token
  and secrets. The guard therefore accepts only owner, member, and collaborator comments.
- **Only addressed tasks wake the agent.** A task without a `to` stays with the live sessions
  that run `shipd room watch`.
