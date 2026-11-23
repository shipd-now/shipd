# Exact replacements — docs-findings-sweep

Each entry replaces its `Old` text with its `New` text, once, in the file its
heading names. `Old` occurs exactly once in that file. Apply the text as
written: change no other word, and keep every line break.

## `docs/pr.md`

### Entry 1 (finding 1)

Old:

````text
The default
rules require two checks, `ci` and `semantic-review`, and zero unresolved review conversations.
They bind once `shipd gate rules apply` writes them. The [review gate](copilot-review.md) posts the
`semantic-review` check.
````

New:

````text
Among the
default rules are two checks, `ci` and `semantic-review`, and zero unresolved review conversations;
[Customising shipd](customise.md) lists the rest. They bind once `shipd gate rules apply` writes
them. The [review gate](copilot-review.md) posts the `semantic-review` check.
````

## `docs/semantic-review-reference.md`

### Entry 1 (finding 2)

Old:

````text
| `location` | `path/to/file.ext:LINE` |
````

New:

````text
| `locations` | a non-empty array of `path/to/file.ext:LINE`; the first is the primary site |
````

### Entry 2 (finding 2)

Old:

````text
- `location` anchors to a right-side line of the diff
````

New:

````text
- `locations[0]` anchors to a right-side line of the diff
````

## `docs/semantic-review.md`

### Entry 1 (finding 3)

Old:

````text
| low | style, naming, minor redundancy | no |
````

New:

````text
| low | a real but minor defect, such as a swallowed error or dead code; never pure style or naming | no |
````

## `docs/install.md`

### Entry 1 (finding 4)

Old:

````text
The installer then writes the launcher to `~/.local/bin/shipd`. It prints a
hint when that directory is not on your PATH. A re-run is safe: an existing
marketplace or plugin counts as success.
````

New:

````text
The installer then writes the launcher to `~/.local/bin/shipd`. When that
directory is not on your PATH, it prints the line to add to your shell profile:
`export PATH="$HOME/.local/bin:$PATH"`. A re-run is safe: an existing
marketplace or plugin counts as success.
````

## `docs/history.md`

### Entry 1 (finding 5)

Old:

````text
- [Getting started](getting-started.md) walks
````

New:

````text
- [Your first change](getting-started.md) walks
````

## `docs/guardrails.md`

### Entry 1 (finding 6)

Old:

````text
- [Install the Copilot review gate](copilot-review.md) —
````

New:

````text
- [Review gate](copilot-review.md) —
````

## `docs/room-wake-reference.md`

### Entry 1 (finding 6)

Old:

````text
[Copilot review reference](copilot-review-reference.md) covers
````

New:

````text
[Review gate reference](copilot-review-reference.md) covers
````

### Entry 2 (finding 13)

Old:

````text
The run exits `0` for `closed`, `turn-cap`, and `budget`. It exits `1` with one `Error:` line
for a failure. It never retries a failed turn. In repo mode, a failed turn parks only its pull
request.
````

New:

````text
The run exits `0` for `closed`, `turn-cap`, and `budget`. It exits `1` with one `Error:` line for
a failure. It never retries a failed turn. In repo mode, a failed turn parks only its pull
request.
````

### Entry 3 (finding 13)

Old:

````text
An author run waits in slices of four `--interval` periods and checks the reviews and the head
between slices. `--ci-reviewer ""` turns off only the reviews check; the run still waits in
slices and checks the head. Reviewer and `ci` runs ignore the flag and wait once over the whole
budget.
````

New:

````text
An author run waits in slices of four `--interval` periods and checks the reviews and the head
between slices. `--ci-reviewer ""` turns off only the reviews check; the run still waits in slices
and checks the head. Reviewer and `ci` runs ignore the flag and wait once over the whole budget.
The run also checks the head after each turn. If it cannot read the head, it warns once and opens
no re-review task. A rerun opens no task a head already has.
````

### Entry 4 (finding 13)

Old:

````text
- **Replies wake no other workflow.** The reply job posts with the workflow token, and GitHub
  starts no workflow run from that token's events. Two CI agents in one repository therefore
  never wake each other. A live session's `shipd room watch` still sees the reply.
  `shipd room run` keeps two local agents talking without the wake; see [Run agents in a pull
  request's room](room-run.md).
````

New:

````text
- **Replies wake no other workflow.** The reply job posts with the workflow token, and GitHub
  starts no workflow run from that token's events. Two CI agents in one repository therefore never
  wake each other. A live session's `shipd room watch` still sees the reply. `shipd room run`
  keeps two local agents talking without the wake; see [Run agents in a pull request's
  room](room-run.md).
````

### Entry 5 (finding 13)

Old:

````text
- **Fork review comments get no wake.** A review comment on a fork's pull request gets a
  read-only token and cannot write the room. A conversation comment runs with the base
  repository's token and secrets. The guard therefore accepts only owner, member, and
  collaborator comments.
````

New:

````text
- **Fork review comments get no wake.** A review comment on a fork's pull request gets a read-only
  token and cannot write the room. A conversation comment runs with the base repository's token
  and secrets. The guard therefore accepts only owner, member, and collaborator comments.
````

## `docs/copilot-review-reference.md`

### Entry 1 (finding 6)

Old:

````text
[Room wake reference](room-wake-reference.md) covers
````

New:

````text
[Room reference](room-wake-reference.md) covers
````

## `docs/tutorials/videos/09-ci-and-copilot-review.md`

### Entry 1 (finding 6)

Old:

````text
- [Install the Copilot review gate](../../copilot-review.md)
````

New:

````text
- [Review gate](../../copilot-review.md)
````

### Entry 2 (finding 6)

Old:

````text
- [Copilot review reference](../../copilot-review-reference.md)
````

New:

````text
- [Review gate reference](../../copilot-review-reference.md)
````

### Entry 3 (finding 6)

Old:

````text
The last three lines show `protection`, `automerge`, and `copilot-secret`.
````

New:

````text
Its output includes the `protection`, `automerge`, and `copilot-secret` lines.
````

## `docs/tutorials/videos/01-install-and-build.md`

### Entry 1 (finding 6)

Old:

````text
- [Getting started](../../getting-started.md)
````

New:

````text
- [Your first change](../../getting-started.md)
````

## `docs/tutorials/videos/02-plan-and-specs.md`

### Entry 1 (finding 6)

Old:

````text
- [Getting started](../../getting-started.md)
````

New:

````text
- [Your first change](../../getting-started.md)
````

## `docs/tutorials/videos/03-worktrees-and-small-prs.md`

### Entry 1 (finding 6)

Old:

````text
- [Getting started](../../getting-started.md)
````

New:

````text
- [Your first change](../../getting-started.md)
````

## `docs/what-is-shipd.md`

### Entry 1 (finding 7)

Old:

````text
orchestrator on the strongest model plans
````

New:

````text
orchestrator on the session's model plans
````

### Entry 2 (finding 7)

Added at build time: the validator found the page's diagram still carried the
old label, which the scenario's search for `strongest model` also matches.

Old:

````text
        orch["Orchestrator<br/>(strongest model)"]
````

New:

````text
        orch["Orchestrator<br/>(session's model)"]
````

## `docs/cheatsheet.md`

### Entry 1 (finding 8)

Old:

````text
and the generated `/s:` command files in a repo
````

New:

````text
and the generated command files in a repo
````

## `docs/statusline-and-telemetry.md`

### Entry 1 (finding 9)

Old:

````text
Each build appends one record to `builds.jsonl`, and writes one file under
the configured `log_dir`.
````

New:

````text
Each build writes one file under the configured `log_dir`, and appends one
record to `builds.jsonl` in that directory.
````

### Entry 2 (finding 9)

Old:

````text
Names the directory for the per-build files. |
````

New:

````text
Names the directory for the per-build files and `builds.jsonl`. |
````

## `docs/plan.md`

### Entry 1 (finding 10)

Old:

````text
It then runs the
context gate again, which is the only exit to `ready`.
````

New:

````text
It then runs the
context gate again. The skill never forces the status: a gate pass is its only
exit to `ready`.
````

### Entry 2 (finding 10)

Old:

````text
The gate
enters `rejected` from `draft` or `ready`.
````

New:

````text
The gate
enters `rejected` from `draft` or `ready`. After enrichment, a person can also
return the plan to `draft` or `ready` through `/s:status`.
````

## `docs/oracle.md`

### Entry 1 (finding 11)

Old:

````text
Corrections go through **`/s:teach`**; [the wiki](wiki.md#correct-an-answer)
gives the steps.
````

New:

````text
Corrections go through **`/s:teach`**; [the wiki](wiki.md#correct-an-answer)
gives the steps. A wiki page outranks a raw queue entry on the ladder, so later
lookups cite the corrected page.
````

## `docs/workspaces/external-stores.md`

### Entry 1 (finding 12)

Old:

````text
Push and pull the store repo yourself, exactly as you do the workspace repo.
````

New:

````text
Push and pull the store repo yourself, exactly as you do the workspace repo.
Two paths run networked git on a store while `store_sync` is `true`. Autopilot
fetches the store's `origin main` before it checks a dependency. The
session-boundary hook also pushes a store that lives in the workspace
repository; see [Sharing a workspace with a team](teams.md#concurrency-expectations).
````

## `docs/room-run.md`

### Entry 1 (finding 13)

Old:

````text
Give the `watch` tool call its own timeout above 540 seconds (on Claude Code, a Bash `timeout`
of `600000` ms). Run `watch` again with the last line's `cursor` as the `--since` value. Run
`watch` in the foreground only. A wait in the background answers a turn after the agent stops
listening.
````

New:

````text
Give the `watch` tool call its own timeout above 540 seconds (on Claude Code, a Bash `timeout` of
`600000` ms). Run `watch` again with the last line's `cursor` as the `--since` value. Run `watch`
in the foreground only. A wait in the background answers a turn after the agent stops listening.
To hand a task back to its asker, reply with `--state input-required --to <asker>`.
````

### Entry 2 (finding 13)

Old:

````text
Before `gh pr merge`, a `reviewer` agent runs `shipd room list 412 --open --json`. It merges
only when `tasks` is empty. Otherwise it keeps watching (`stay`), or reports the open tasks and
stops.
````

New:

````text
Before `gh pr merge`, a `reviewer` agent runs `shipd room list 412 --open --json`. It merges only
when `tasks` is empty. Otherwise it keeps watching (`stay`), or reports the open tasks and stops.
````

## `plugins/s/bin/shipd`

### Entry 1 (finding 8)

Old:

````text
generated ``/s:`` command files inside a repository or the user's own harness
````

New:

````text
generated command files inside a repository or the user's own harness
````

### Entry 2 (finding 8)

Old:

````text
                             the harness registry, and the generated /s:
                             command files in a repo or in your home
````

New:

````text
                             the harness registry, and the generated
                             command files in a repo or in your home
````

### Entry 3 (finding 15)

Old:

````text
``merge``, ``emit``, ``autopilot``, ``worktree remove``) stay behind their
guarded scripts and skills. One more verb writes outside the repository:
````

New:

````text
``merge``, ``emit``, ``autopilot``) stay behind their
guarded scripts and skills. ``worktree`` passes through to the guarded
``worktree.py``, so ``worktree remove`` runs here under that script's guards.
One more verb writes outside the repository:
````

### Entry 4 (finding 8)

Old:

````text
maintain the generated ``/s:``
    command files
````

New:

````text
maintain the generated
    command files
````

## `plugins/s/skills/build/SKILL.md`

### Entry 1 (finding 14)

Old:

````text
This reads (and, on first run, creates) `~/.shipd-config.json` — the place to
````

New:

````text
This only reads `~/.shipd-config.json`, and never creates it — the place to
````
