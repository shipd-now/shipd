<!-- doc-type: how-to -->

# Episode 1: Install shipd and ship a change

## Introduction

You have asked an AI coding agent for a feature and received something close, but not what you meant. This episode starts from that problem. It tells the story of prompt-and-hope, shows the five steps shipd puts in its place, then installs shipd and ships a change through those steps. It is for developers who have Claude Code and `python3` and want to see shipd work before they learn how it plans.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Tactical execution |
| Runtime | 5 minutes |
| Prerequisites | Claude Code and `python3` on your PATH |
| Commands shown | `curl -fsSL https://shipd.now/install \| sh`, `shipd doctor`, `shipd init`, `/s:build`, `shipd status`, `shipd list`, `shipd board` |

## Script

### 0:00–0:45 Before: prompt and hope

**On screen:** No terminal. Three cards appear in a loop: "Prompt", "Hope", "Rework". An arrow runs from "Rework" back to "Prompt", and the loop turns twice.

**Narration:** You type a request to an agent. The agent writes code at once, from its own guess at what you meant. The result is close, so you correct it in the chat, and the agent guesses again. Your intent lives only in a transcript that scrolls away. Nothing written down says what you asked for, so nothing can check the code against it.

### 0:45–1:30 After: five steps

**On screen:** The loop clears. Five cards appear one at a time on one line: "Idea", "Spec", "Build", "Check", "Ship". The strip stays in a corner for the rest of the episode.

**Narration:** shipd replaces the loop with five steps. You state an idea in plain words. The agent reads your code, asks only what it cannot work out, and writes a spec: the behavior you want, as scenarios you can test. Agents build against that spec. An independent check then tries to break each scenario. Only a change that survives the check ships.

### 1:30–2:15 Install and check

**On screen:** A fresh terminal. The presenter runs `curl -fsSL https://shipd.now/install | sh`, then types the `export PATH="$HOME/.local/bin:$PATH"` line the installer prints, then runs `shipd doctor`.

**Narration:** One command installs shipd. It registers the `shipd` marketplace, installs the `s` plugin, and writes the `shipd` launcher to `~/.local/bin`. If the installer says so, add that directory to your PATH. Then run `shipd doctor`. It reports one line per check and ends with `doctor: ok` or a count of problems. Only a `fail` line blocks you, and the verb changes nothing.

### 2:15–2:45 The kanban demo

**On screen:** A git repository holding the one-file demo, `kanban.py` and `cards.json`. The presenter runs `shipd init`, then `python3 kanban.py remove "Draft the board layout"`. The command fails with `usage: kanban.py {list|board}`. The "Idea" card in the strip lights up.

**Narration:** The demo is a tiny kanban board over a JSON file. It sits in a git repository because `/s:build` creates a worktree. `shipd init` creates the spec layout, and it is safe to re-run. The board has no `remove` command, so this call fails. That gap is our idea.

### 2:45–4:30 Ship it, one step at a time

**On screen:** The presenter types `/s:build Add a remove command to kanban.py that deletes a card from any column`. The video pauses at each step, and the matching card lights up:

1. **Spec** — the session names the change and writes its artifacts. The camera holds on one scenario: removing a card deletes it from its column.
2. **Build** — the task checkboxes in `tasks.md` tick over.
3. **Check** — the verification pass runs the scenario against the real code and reports it confirmed.
4. **Ship** — the session reports the change archived. The presenter reruns `python3 kanban.py remove "Draft the board layout"`, then `python3 kanban.py list`. The card is gone.

**Narration:** `/s:build` finds no planned change, so it plans one first. Here is the spec: one scenario says what "remove" means. Execution agents then work through the tasks. The check runs that scenario against the real code, and it passes, so the change ships. The remove command that failed now deletes the card. Every step left a file you can read.

### 4:30–5:00 Watch the change

**On screen:** Three terminals in turn run `shipd status`, `shipd list`, and `shipd board`. The board fills the screen, and the five-card strip returns beside it.

**Narration:** `shipd status` reports a change and its task progress. `shipd list` shows everything in flight across the repository and its worktrees. `shipd board` opens the full-screen delivery board. You went from idea to spec to build to check to ship with one request. The next episode slows down the spec step.

## Takeaways

- Prompt-and-hope keeps your intent in a transcript, so nothing checks the code against it.
- shipd puts five steps in its place: idea, spec, build, check, ship.
- One `curl` command installs shipd, and `shipd doctor` checks it without changing anything.
- `/s:build` with a prose request runs all five steps on one change.

## Next

Episode 2 slows the loop down and shows the planning step: [Plan a change and read its specs](02-plan-and-specs.md).

## Sources

- [Getting started](../../getting-started.md)
- [What is shipd?](../../what-is-shipd.md)
- [Cheatsheet](../../cheatsheet.md)
- [The onboard kanban demo](../../../plugins/s/skills/onboard/assets/solutions/add-board/kanban.py)
