<!-- doc-type: concept -->

# Core ideas

This page defines shipd's terms, one idea per section. Each definition is
short and links the page that owns the detail.
[What is shipd?](what-is-shipd.md) owns the overview diagram of how the ideas
fit together.

## The spec

A **capability** covers one area of behavior, under one name. Its **spec** lives at
`verified/<capability>/spec.md` under the content directory, and that master
library is the single source of truth. A spec holds **requirements**, and each
requirement carries **scenarios** that state its testable behavior.

The content directory's [README](../.shipd/README.md) is the format authority
for the requirement grammar.

## A change

A **change** is one unit of planned work. It holds three artifacts under
`planned/<change>/`: `plan.md`, `tasks.md`, and one delta spec per affected
capability. A **delta** adds, modifies, removes, or renames requirements in
the master library when the change merges.

A change moves through six statuses: `draft`, `ready`, `active`, `complete`,
`verified`, and `rejected`. [Plan a change](plan.md) owns the lifecycle.

One change lives in one worktree, on one branch, and ships as one pull request.
[Worktrees and hooks](worktrees.md) owns the worktree, and
[Pull requests](pr.md) owns the pull request.

## Gates

A **gate** blocks progress until its required check passes. The
**context gate** checks that a plan holds enough context to build; a pass
promotes the change to `ready` ([Plan a change](plan.md)). The
**supersession gate** stops a build when merged work already implements the
plan ([The supersession gate](supersession-gate.md)).

The **semantic review** reads a change structurally and reports findings a
person can act on ([The semantic review](semantic-review.md)). The
**review gate** runs that review on every pull request and turns it into the
`semantic-review` commit status ([Review gate](copilot-review.md)).

## Agents

The **orchestrator** runs a build on the session's model. It plans,
coordinates, and verifies, and it never writes the final implementation code.
**Execution agents**, one model tier down, claim and implement the tasks. An
independent **validator** tries to refute every scenario against the running
code. [Build a change](build.md) owns all three.

The **room** is a pull request's comment thread, where agents and people take
turns on tasks ([Multi-agent PR](multi-agent-pr.md)).

## Epics

An **epic** decomposes a feature too large for one change into **member**
changes. The members share one set of decisions, which the epic records once
([Epics](epics.md)).

**Autopilot** drives an approved epic's members to shipped pull requests with
no human present ([Autopilot](autopilot.md)).

Two optional artifacts sit above an epic. An **initiative** is a workspace
brief that states the outcomes an epic delivers against. A **PRD** settles what
problem a feature solves, for whom, and what success looks like
([PRDs](prd.md)).

## Knowledge

An agent climbs a three-rung **ladder** before it asks a person: read, then
oracle, then human. The **oracle** is the non-interactive answerer that
consults durable knowledge before a human; it never asks you anything
([The oracle](oracle.md)).

The **wiki** holds the standing positions a team has settled, and the oracle
answers from it ([The wiki](wiki.md)). **Personal memory** is one wiki that
belongs to you, and the oracle reads it first ([Personal memory](memory.md)).

## Workspaces

A **workspace** is a git repository you clone to stand up one cross-repo job.
It carries the manifest of member repositories and the job's wiki
([Workspaces](workspaces.md)).

The **layered configuration** resolves `.shipd-config.json` by upward search,
then the user layer, then the built-in defaults. The nearest layer that
declares a key supplies its whole value ([Customising shipd](customise.md)).

[Command cheatsheet](cheatsheet.md) lists every command.
