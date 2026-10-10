<!-- doc-type: how-to -->

# Episode 1: The core loop: `/s:plan` then `/s:build`

## Introduction

You ask an AI coding agent for a feature and hope the result matches your intent. This episode shows the shipd answer. You plan a change first, read the spec artifacts, and only then build. The episode is for developers who have installed shipd and want to ship a first change.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Tactical execution |
| Runtime | 5 minutes |
| Prerequisites | Claude Code and `python3` on your PATH, and shipd installed |
| Commands shown | `/s:plan`, `/s:build`, `shipd status`, `shipd list`, `shipd board` |

## Script

### 0:00–0:45 Why plan before you build

**On screen:** The [What is shipd?](../../what-is-shipd.md) page, with the flowchart in view. The cursor traces the path from idea to spec to build.

**Narration:** Prompting an agent and hoping is a gamble. shipd makes the agent converge on a specification first. The spec, not the chat transcript, is the one source of context every agent works from. That is why what got built and what you asked for are the same document.

### 0:45–2:00 Plan a change with `/s:plan`

**On screen:** A terminal in a repository. The presenter types `/s:plan Add a --json flag to the export command so scripts can consume its output`.

**Narration:** Describe the change in prose. The Planner investigates your codebase first and asks only what it cannot infer. It names the change, creates a worktree at `.worktrees/<change>` on branch `change/<change>`, and writes the artifacts there. Then it stops. No code exists yet.

### 2:00–3:00 Read the artifacts

**On screen:** The editor opens `plan.md`, `specs/<capability>/spec.md`, and `tasks.md` side by side.

**Narration:** Three files describe the change. The plan holds the idea and the binding implementation decisions. The spec holds the testable delta for each affected capability. The tasks file holds the checklist. Read them now. This is the cheapest moment to correct course.

### 3:00–4:15 Build with `/s:build`

**On screen:** The presenter types `/s:build <change>`. Task checkboxes in `tasks.md` tick over as execution agents work.

**Narration:** The Orchestrator adopts the planned change and delegates the checklist to execution agents one model tier down. It answers their questions and verifies the result against the scenarios in the spec. Three outcomes follow. Working code lands on the change branch, the deltas merge into the verified library, and the change moves to the archive.

### 4:15–5:00 Watch the change

**On screen:** Three terminals in turn run `shipd status`, `shipd list`, and `shipd board`. The board fills the screen.

**Narration:** `shipd status` reports one change and its task progress. `shipd list` shows everything in flight across the repository and its worktrees. `shipd board` opens the full-screen delivery board. That is the loop: plan, read, build, watch.

## Takeaways

- `/s:plan` writes `plan.md`, a spec, and `tasks.md` in a new worktree, then stops.
- `/s:build` delegates the checklist to execution agents and verifies against the spec's scenarios.
- `shipd status`, `shipd list`, and `shipd board` show progress without a prompt.

## Next

Episode 2 shows how each change gets its own worktree and pull request: [Git worktrees and small PRs](02-worktrees-and-small-prs.md).

## Sources

- [Getting started](../../getting-started.md)
- [What is shipd?](../../what-is-shipd.md)
