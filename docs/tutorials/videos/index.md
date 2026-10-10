<!-- doc-type: concept -->

# The shipd video series

The shipd video series teaches the spec-driven workflow in nine episodes of
five minutes each. Each episode has a script that lists what the viewer sees
and what the presenter says. Every script follows the same structure, which
[the template](template.md) defines.

## The three groups

The roadmap sorts the episodes into three groups. Each group answers one
question about the work.

- **Tactical execution** — how one change goes from idea to pull request.
- **Spec authoring and pressure testing** — how a feature becomes specs that
  survive questions before any code exists.
- **Verification and governance** — how shipd checks the work, shares
  knowledge across repositories, and reports delivery.

## The episodes

### Tactical execution

1. [The core loop: `/s:plan` then `/s:build`](01-core-loop.md)
2. [Git worktrees and small PRs](02-worktrees-and-small-prs.md)

### Spec authoring and pressure testing

3. [PRDs and guardrails](03-prds-and-guardrails.md)
4. [Epics and `/s:epic-grill`](04-epics-and-epic-grill.md)

### Verification and governance

5. [The oracle and the supersession gate](05-oracle-and-supersession-gate.md)
6. [Workspaces 101](06-workspaces-101.md)
7. [Member maps and headless runs](07-advanced-workspaces.md)
8. [CI and Copilot review](08-ci-and-copilot-review.md)
9. [The management plane (commercial)](09-management-plane.md)

## The open-source boundary

Episodes 1 to 8 cover open-source shipd: the plugin, the engine, and the
documented workflows. Episode 9 covers the management plane, which is
commercial. The management plane reports delivery across repositories, and
the episode describes only what the product ships today.

## Where to start

Watch the episodes in order. Each episode names its prerequisites in the
`At a glance` table. A viewer who has used shipd before can start at the
group that matches the next job.
