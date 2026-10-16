<!-- doc-type: how-to -->

# Episode 2: Plan a change and read its specs

## Introduction

Episode 1 built a change from one request. For a change you want to inspect first, you plan it on its own and read what the plan says before any code exists. This episode plans a second change to the kanban demo with `/s:plan`, reads the three artifacts, and then builds the planned change. The episode is for developers who have shipped a first change and want to review the spec before they build.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Tactical execution |
| Runtime | 5 minutes |
| Prerequisites | [Episode 1](01-install-and-build.md) completed, with the kanban demo initialised |
| Commands shown | `/s:plan`, `/s:build` |

## Script

### 0:00–0:45 Why plan before you build

**On screen:** The [What is shipd?](../../what-is-shipd.md) page, with the flowchart in view. The cursor traces the path from idea to spec to build.

**Narration:** Prompting an agent and hoping is a gamble. shipd makes the agent converge on a specification first. The spec, not the chat transcript, is the one source of context every agent works from. That is why what got built and what you asked for are the same document.

### 0:45–1:45 Plan a change with `/s:plan`

**On screen:** A terminal in the kanban demo. The presenter types `/s:plan Add a move command to kanban.py that moves a card to another column`.

**Narration:** Describe the change in prose. The Planner investigates your codebase first and asks only what it cannot infer. It names the change, creates a worktree at `.worktrees/<change>` on branch `change/<change>`, and writes the artifacts there. Then it stops. No code exists yet.

### 1:45–3:15 Read the artifacts

**On screen:** The editor opens `plan.md`, `specs/<capability>/spec.md`, and `tasks.md` side by side. The cursor moves through each in turn.

**Narration:** Three files describe the change. In `plan.md`, the Idea section holds the motivation, the details, and the non-goals, and the Implementation section holds the binding decisions. The spec holds each requirement with WHEN and THEN scenarios, so every behavior is testable. The tasks file holds the checklist. Read them now. This is the cheapest moment to correct course.

### 3:15–4:15 The context gate

**On screen:** The `plan.md` header changes from a draft status to `Status: ready`.

**Narration:** A deterministic context gate runs before implementation starts. It rejects a plan that still holds placeholders or an open question. When the plan passes, it moves to ready. Nothing builds from a plan that has not passed.

### 4:15–5:00 Build the planned change

**On screen:** The presenter types `/s:build <change>`. Task checkboxes in `tasks.md` tick over as execution agents work.

**Narration:** The Orchestrator adopts the planned change and delegates the checklist to execution agents one model tier down. It answers their questions and verifies the result against the scenarios in the spec. Working code lands on the change branch, and the change moves to the archive.

## Takeaways

- `/s:plan` writes `plan.md`, a spec, and `tasks.md` in a new worktree, then stops.
- The context gate promotes a plan to ready before anything builds.
- `/s:build <change>` verifies the result against the spec's scenarios.

## Next

Episode 3 shows how each change gets its own worktree and pull request: [Git worktrees and small PRs](03-worktrees-and-small-prs.md).

## Sources

- [Getting started](../../getting-started.md)
- [What is shipd?](../../what-is-shipd.md)
- [Spec library guide](../../../.shipd/README.md)
