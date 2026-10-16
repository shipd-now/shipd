<!-- doc-type: how-to -->

# Episode 1: Install shipd and ship a change

## Introduction

You have heard that shipd turns an agent request into a verified, reviewable change, but you have not installed it. This episode starts from an empty machine. You install shipd, run its preflight, set up a small kanban demo, and ship a change with one `/s:build` request. It is for developers who have Claude Code and `python3` and want to see shipd work before they learn how it plans.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Tactical execution |
| Runtime | 5 minutes |
| Prerequisites | Claude Code and `python3` on your PATH |
| Commands shown | `curl -fsSL https://shipd.now/install \| sh`, `shipd doctor`, `shipd init`, `/s:build`, `shipd status`, `shipd list`, `shipd board` |

## Script

### 0:00–0:45 What shipd is

**On screen:** The [What is shipd?](../../what-is-shipd.md) page, with the flowchart in view. The cursor traces the path from idea to spec to build.

**Narration:** shipd is a spec-driven delivery system for AI coding agents. Instead of prompting an agent and hoping, you make the agent converge on a specification first. The spec, not the chat transcript, is the one source of context every agent works from. In this episode you install it and watch it ship a change.

### 0:45–1:45 Install and check

**On screen:** A fresh terminal. The presenter runs `curl -fsSL https://shipd.now/install | sh`, then types the `export PATH="$HOME/.local/bin:$PATH"` line the installer prints, then runs `shipd doctor`.

**Narration:** One command installs shipd. It registers the `shipd` marketplace, installs the `s` plugin, and writes the `shipd` launcher to `~/.local/bin`. If the installer says so, add that directory to your PATH. Then run `shipd doctor`. It reports one line per check and ends with `doctor: ok` or a count of problems. Only a `fail` line blocks you, and the verb changes nothing.

### 1:45–2:15 Set up the kanban demo

**On screen:** A git repository holding the one-file demo, `kanban.py` and `cards.json`. The presenter runs `shipd init`, then `python3 kanban.py remove "Draft the board layout"`. The command fails with `usage: kanban.py {list|board}`.

**Narration:** The demo is a tiny kanban board over a JSON file, in a git repository because `/s:build` creates a worktree. Run `shipd init` in the folder to create the spec layout. It is safe to re-run. The board has no `remove` command yet, so this call fails with the usage line. That failure is our starting point.

### 2:15–4:15 Ship it with one request

**On screen:** The presenter types `/s:build Add a remove command to kanban.py that deletes a card from any column`. The session names the change, works through its tasks, and runs a verification pass. The presenter then reruns `python3 kanban.py remove "Draft the board layout"` and `python3 kanban.py list`. The card is gone.

**Narration:** Describe the change in prose. `/s:build` finds no planned change, so it runs the planning flow itself. Then it delegates the tasks to execution agents and verifies the result against the spec. When it finishes, the same remove command that failed now deletes the card, and the list no longer shows it.

### 4:15–5:00 Watch the change

**On screen:** Three terminals in turn run `shipd status`, `shipd list`, and `shipd board`. The board fills the screen.

**Narration:** `shipd status` reports a change and its task progress. `shipd list` shows everything in flight across the repository and its worktrees. `shipd board` opens the full-screen delivery board. You have installed shipd and shipped a change. The next episode slows down and shows how planning works.

## Takeaways

- One `curl` command installs shipd, and `shipd doctor` checks it without changing anything.
- `shipd init` creates the spec layout in a folder, so `/s:build` can work there.
- `/s:build` with a prose request plans, delegates, and verifies a change end to end.

## Next

Episode 2 slows the loop down and shows the planning step: [Plan a change and read its specs](02-plan-and-specs.md).

## Sources

- [Getting started](../../getting-started.md)
- [What is shipd?](../../what-is-shipd.md)
- [Cheatsheet](../../cheatsheet.md)
- [The onboard kanban demo](../../../plugins/s/skills/onboard/assets/solutions/add-board/kanban.py)
