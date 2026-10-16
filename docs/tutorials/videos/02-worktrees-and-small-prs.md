<!-- doc-type: how-to -->

# Episode 2: Git worktrees and small PRs

## Introduction

Large pull requests stall in review, and parallel work collides in one checkout. This episode shows how shipd gives each change its own worktree, branch, and pull request. You create a worktree with one command and see how the review gate and auto-merge ship it. The episode is for developers who run more than one change at a time.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Tactical execution |
| Runtime | 5 minutes |
| Prerequisites | [Episode 1](01-core-loop.md); a repository with shipd installed |
| Commands shown | `shipd worktree`, `shipd list`, `shipd status`, `git push`, `/s:pr`, `gh pr merge --auto --squash` |

## Script

### 0:00–0:45 One change, one worktree

**On screen:** A slide shows four terms joined by "one": change, worktree, branch, pull request. The terminal shows an empty `.worktrees/` directory.

**Narration:** Every change in shipd is one unit of planned work. It gets one worktree, one branch, and one pull request. The rule keeps each pull request small, because a change never holds more than its own plan.

### 0:45–2:00 Create a worktree

**On screen:** The terminal runs `shipd worktree add-login-flow`. Then `ls .worktrees` lists the new directory, and `git branch` shows `change/add-login-flow`.

**Narration:** The `shipd worktree` command creates `.worktrees/add-login-flow` on the branch `change/add-login-flow`. It then runs any post-worktree scripts that your configuration declares. A fresh checkout arrives already set up. The `/s:plan` command creates the same worktree for you.

### 2:00–3:00 Work in parallel

**On screen:** Two terminal panes sit side by side, one in each of two worktrees. In a third pane, `shipd list` and `shipd status` report both changes.

**Narration:** Each worktree has its own files and its own branch. Two sessions can build two changes at once without touching each other. The `shipd list` command shows everything in flight across the repository and its worktrees. The `shipd status` command shows one change and its task progress.

### 3:00–4:15 Ship through a pull request

**On screen:** The terminal runs `git push -u origin change/add-login-flow`, then `/s:pr`, then `gh pr merge --auto --squash --delete-branch`. The browser shows a pull request with two required checks.

**Narration:** You never push to main. You push the change branch and open a pull request. Auto-merge waits on two required checks, `ci` and `semantic-review`. It also waits until no review thread stays unresolved.

### 4:15–5:00 Clean up

**On screen:** The terminal runs the guarded `worktree.sh remove` verb, then `git pull` on main. The `.worktrees/` directory is empty again.

**Narration:** After the merge, remove the worktree through the guarded verb. The verb refuses while the worktree still shows work in progress. A sweep also reclaims merged worktrees and their branches on its own.

## Takeaways

- One change is one worktree, one branch, and one pull request.
- The `shipd worktree` command creates the worktree and runs your setup scripts.
- Auto-merge waits on the `ci` and `semantic-review` gates and on resolved threads.

## Next

[Episode 3](03-prds-and-guardrails.md) shows how a PRD and guardrails steer what your changes build.

## Sources

- [Getting started](../../getting-started.md)
- [What is shipd](../../what-is-shipd.md)
- [Command cheatsheet](../../cheatsheet.md)
- [Customising shipd](../../customise.md)
- [Working in this repo](../../../AGENTS.md)
