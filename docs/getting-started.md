<!-- doc-type: how-to -->

# Your first change

This guide takes you from a fresh machine to your first shipd-built change,
in five steps. New to the idea? Read [What is shipd?](what-is-shipd.md)
first.

You need [Claude Code](https://claude.com/claude-code) (`claude`) and
`python3` on your PATH.

## 1. Install

```bash
curl -fsSL https://shipd.now/install | sh
```

<details>
<summary>Alternative install</summary>

You can also install by hand with the Claude Code CLI, vendor shipd into one
repository, or run it from a checkout. [Install](install.md) covers each
mode.

</details>

## 2. Plan your first change

Open Claude Code in the repository you want to change. Describe the change
in plain words:

```
/s:plan Add a --json flag to the export command so scripts can read its output
```

The planner reads your code first. It asks only what the code cannot answer.
It writes three kinds of file into `.shipd/planned/<change>/`, inside a
worktree at `.worktrees/<change>`:

- `plan.md` — the idea and the decisions the build must follow
- `specs/<capability>/spec.md` — the testable delta for each capability the
  change touches
- `tasks.md` — the task checklist

The planner writes no code. Read the three files now: this is the cheapest
moment to correct course. [`.shipd/README.md`](../.shipd/README.md) defines
their grammar. [Plan a change](plan.md) covers the full flow.

In a new repository, the first `/s:plan` runs the `/s:init` setup wizard
first.

## 3. Build it

```
/s:build <change>
```

The build runs the tasks with sub-agents. It then checks the result against
the scenarios in the spec. A finished build leaves three things behind:

- working code on the `change/<change>` branch
- the deltas merged into `.shipd/verified/`
- the change archived under `.shipd/completed/`

By default the build then pushes the branch and opens a pull request that
merges itself once its checks pass. [Build a change](build.md) covers the
build in full.

## 4. Turn on the statusline

The statusline shows the live change, its status, and its task progress in
the status bar of Claude Code. Register it once:

```bash
shipd statusline install
```

The command writes a `statusLine` entry into `~/.claude/settings.json`. The
entry finds the newest installed shipd at each render, so it keeps working
after an update. The statusline appears in your next Claude Code session.

The statusline works in Claude Code only. No other harness has a statusline
integration. [Statusline and telemetry](statusline-and-telemetry.md) covers
the layout and the other reports.

## 5. Watch the board

```bash
shipd board
```

The full-screen board shows the progress of each change. For plain text, run
`shipd status` for one change, or `shipd list` for every change in flight.

## Where to go next

- [Cheatsheet](cheatsheet.md) — every `/s:` command and `shipd` verb, with
  one example each
- [What is shipd?](what-is-shipd.md) — the model behind the loop you just ran
- [Core ideas](core-ideas.md) — the definitions of shipd's terms
- [Customising shipd](customise.md) — the presets and every config key
- [Workspaces](workspaces.md) — one job across several repositories
