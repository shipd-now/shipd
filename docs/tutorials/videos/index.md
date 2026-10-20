<!-- doc-type: concept -->

# The shipd video series

The shipd video series teaches the spec-driven workflow in a three-minute
intro and ten episodes of five minutes each. Each episode has a script that
lists what the viewer sees and what the presenter says. Every script follows
the same structure, which [the template](template.md) defines.

## The three groups

The roadmap sorts the episodes into three groups. Each group answers one
question about the work.

- **Tactical execution** — how one change goes from idea to pull request.
- **Spec authoring and pressure testing** — how a feature becomes specs that
  survive questions before any code exists.
- **Verification and governance** — how shipd checks the work, shares
  knowledge across repositories, and reports delivery.

## The episodes

0. [Where shipd came from](00-intro.md)

### Tactical execution

1. [Install shipd and ship a change](01-install-and-build.md)
2. [Plan a change and read its specs](02-plan-and-specs.md)
3. [Git worktrees and small PRs](03-worktrees-and-small-prs.md)

### Spec authoring and pressure testing

4. [PRDs and guardrails](04-prds-and-guardrails.md)
5. [Epics and `/s:epic-grill`](05-epics-and-epic-grill.md)

### Verification and governance

6. [The oracle and the supersession gate](06-oracle-and-supersession-gate.md)
7. [Workspaces 101](07-workspaces-101.md)
8. [Member maps and headless runs](08-advanced-workspaces.md)
9. [CI and Copilot review](09-ci-and-copilot-review.md)
10. [The management plane (commercial)](10-management-plane.md)

## The open-source boundary

Episodes 1 to 9 cover open-source shipd: the plugin, the engine, and the
documented workflows. Episode 10 covers the management plane, which is
commercial. The management plane reports delivery across repositories, and
the episode describes only what the product ships today.

## Where to start

Start with Episode 0, which tells where shipd came from, then watch the
episodes in order. Each episode names its prerequisites in the
`At a glance` table. A viewer who has used shipd before can start at the
group that matches the next job.
