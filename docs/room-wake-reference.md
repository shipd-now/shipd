<!-- doc-type: reference -->

# Room wake reference

The room wake lets a PR-room task wake a repository's CI agent. No developer
session needs to run. A workflow runs the Copilot CLI on the task and posts
its reply to the room. [Copilot review reference](copilot-review-reference.md)
covers the review gate, which `shipd copilot` manages through the same verb.

## The managed files

`shipd copilot add --room` writes these six files and touches nothing else.
The five runtime files are byte-identical copies of the plugin's own files, at
their plugin-relative paths under `.github/shipd-room/`.

| File | Role |
| --- | --- |
| `.github/workflows/room-wake.yml` | The wake workflow. Its first line is the `# shipd-copilot v…` ownership marker. |
| `.github/shipd-room/.claude-plugin/plugin.json` | The plugin manifest. `room.py` reads its version for the agent card. |
| `.github/shipd-room/skills/room/scripts/room.py` | The room verbs the workflow runs: `watch`, `list`, `join`, `message`, and `close`. The bundled copy omits the modules `run` needs, so `run` prints one `Error:` line there; use `shipd room run` locally. |
| `.github/shipd-room/skills/room/scripts/room_schema.py` | The room comment schema that `room.py` reads and writes. |
| `.github/shipd-room/skills/build/scripts/spec_common.py` | The layered config reader that `room.py` imports. |
| `.github/shipd-room/skills/build/scripts/cli_common.py` | The shared CLI helpers that `room.py` imports. |

## Verbs

```bash
shipd copilot add --room       # install or refresh the six files
shipd copilot update           # refresh the gate files, and these six when installed
shipd copilot remove --room    # delete them and prune .github/shipd-room
shipd copilot                  # report both sets; the wake set comes last
```

`update` refreshes the wake set only when `room-wake.yml` carries the
ownership marker. It never installs the wake set, and it leaves a
`room-wake.yml` without the marker alone. `/s:gate update` runs it.

Plain `add` and `remove` act on the four review gate files only. They never
touch the wake set. `remove --room` prunes each emptied directory under
`.github/shipd-room/`, innermost first. It stops at the first directory that
still holds a file.

## Report states

Each wake file reports `installed`, `stale`, `foreign`, or `absent`. The
workflow marker decides ownership for all six files. A runtime file is
`foreign` while the workflow carries no marker, and `stale` when its bytes
differ from the plugin's copy. The workflow reports `stale` while any runtime
file is not `installed`.

Where a wake path is `foreign`, both `add --room` and `remove --room` refuse
and name the file. `--force` overrides the refusal.

## Configuration

| Setting | Kind | Effect |
| --- | --- | --- |
| `SHIPD_ROOM_AGENT` | repository Actions variable | Names the CI agent. Unset, the workflow runs no job. |
| `COPILOT_GITHUB_TOKEN` | repository secret | The Copilot CLI's credential. Unset, the guard logs the gap and leaves the task alone. |

Set the variable with `gh variable set SHIPD_ROOM_AGENT --body <name>`. Use a
fine-grained PAT that carries the "Copilot Requests" permission as the secret.

Only a comment whose `author_association` is `OWNER`, `MEMBER`, or
`COLLABORATOR` wakes the agent. An `issue_comment` run carries the
repository's secrets whoever wrote the comment, so the guard ignores comments
from anyone else.

## How a wake runs

The workflow fires on a new issue comment or review comment. Three jobs run
in turn.

- **guard** holds the workflow token. It runs `room.py watch --once` from the
  triggering comment, and acts only on a task addressed to the agent. It joins
  the room when the agent has no card, then posts `working` on the task.
- **run** holds the Copilot secret only. It checks out the pull request head
  without persisted credentials and runs a pinned Copilot CLI on the task.
- **reply** holds the workflow token on a fresh runner. It posts the reply to
  the asker, or closes the task as `failed` when the run failed.

The two credentials never share a job. Every `room.py` call runs under
`env -i` with an explicit `PATH`.

## The reply marker

A reply whose last non-blank line is exactly this line hands the task back to
the asker:

```
<!-- shipd-room-reply: input-required -->
```

The reply job first strips the CLI's tool-call transcript blocks, then strips
the marker and posts the reply as `input-required`. Any other reply completes
the task. A failed, cancelled, or empty run closes the
task with reason `wake-runner-failed`.

## Known limits

- **The bundle cannot run `run`.** `run` drives a local harness session, so
  the bundle leaves out its modules; use `shipd room run` from a developer
  machine.
- **Replies wake no other workflow.** The reply job posts with the workflow
  token, and GitHub starts no workflow run from that token's events. Two CI
  agents in one repository therefore never wake each other. A live session's
  `shipd room watch` still sees the reply. `shipd room run` keeps two local
  agents talking without the wake; see [Run two agents on a pull request
  unattended](room-run.md).
- **Fork review comments get no wake.** A review comment on a fork's pull
  request gets a read-only token and cannot write the room. A conversation
  comment runs with the base repository's token and secrets. The guard
  therefore accepts only owner, member, and collaborator comments.
- **Only addressed tasks wake the agent.** A task without a `to` stays with
  the live sessions that run `shipd room watch`.
