## ADDED Requirements

### Requirement: Pre-built sandbox template
id: sandbox-template

The plugin SHALL ship a pre-built sandbox template in the onboard skill's
assets: an `.shipd/` layout with an empty `verified/` and a lint-clean,
pre-authored `add-board` change under `planned/`, plus a cycle-1 reference
implementation (`kanban.py` and a seeded `cards.json`) stored outside the
sandbox layout. When `/s:onboard` scaffolds, it SHALL create the sandbox by
copying the template and running `git init`, and SHALL NOT author cycle-1
artifacts live or read the user's real repository for example shapes.

#### Scenario: Scaffold is a copy, not an authoring session
- **WHEN** `/s:onboard` scaffolds the sandbox
- **THEN** the sandbox is created by copying the shipped template plus
  `git init`, with no live authoring of cycle-1 artifacts and no exploration
  of the user's repository

#### Scenario: Template lints clean through the real engine
- **WHEN** `spec_lint.py add-board` runs with a freshly scaffolded sandbox as
  its root
- **THEN** it exits 0 and prints OK

#### Scenario: Reference implementation renders the board
- **WHEN** the reference `kanban.py` and `cards.json` are copied into a
  sandbox and `python3 kanban.py board` runs
- **THEN** it prints a three-column board (todo/doing/done) showing the
  seeded sample cards

### Requirement: Walkthrough pacing
id: walkthrough-pacing

The walkthrough SHALL teach interactively, in short beats: before each
action the guide SHALL state in a sentence or two what is about to happen
and why, then perform that one beat and show its result — and SHALL NOT
execute a cycle end-to-end silently and explain it retrospectively. Each
cycle SHALL pause at its beat boundaries with a plain-text typed prompt, so
no plan → merge sequence ever completes without at least one user reply in
between. Teaching turns SHALL stay brief rather than recap essays, file
contents SHALL be quoted only as short excerpts (never full dumps), cycle 1
SHALL show the rendered board to the user early as the visual payoff, and
each post-merge lifecycle explanation SHALL be limited to a few sentences.
The walkthrough SHALL NOT narrate internal troubleshooting or command-syntax
discovery — the skill documents the exact engine invocations and they SHALL
be used as written.

#### Scenario: No cycle runs silently to completion
- **WHEN** cycle 1 runs
- **THEN** the guide explains each beat before performing it and pauses at
  the beat boundaries for a typed reply, so the plan → merge sequence never
  completes without user interaction

#### Scenario: The board payoff comes early
- **WHEN** cycle 1's build step completes
- **THEN** the rendered `board` output is shown to the user promptly, and the
  closing lifecycle explanation stays within a few sentences instead of a
  full recap of every step

#### Scenario: No internal noise reaches the user
- **WHEN** the guide runs an engine command during the walkthrough
- **THEN** it uses the invocation documented in the skill and shows the
  user the command's real output, without narrating syntax discovery or
  troubleshooting detours

## MODIFIED Requirements

### Requirement: Sandbox hands-on session
id: sandbox-hands-on
base: 9a7642c0e678

The walkthrough SHALL run entirely inside a scaffolded sandbox: a temporary
directory holding a git-initialized mini-repo created from the shipped
template — an `.shipd/` layout with an empty `verified/` and the pre-authored
`add-board` change in `planned/`. Cycle 1 SHALL walk the pre-authored
artifact set; later cycles SHALL author their changes live under the
sandbox's `planned/`. Every cycle SHALL lint, drive status, tick tasks with
the coordinator, implement the kanban CLI code, and merge — all by invoking
the plugin's real engine scripts by absolute path with the sandbox as their
root. The session SHALL NOT create or modify any file in the user's real
repository, and the walkthrough SHALL end by offering to delete or keep the
sandbox.

#### Scenario: First cycle creates the kanban capability
- **WHEN** the first cycle's change merges
- **THEN** the sandbox's `.shipd/verified/kanban/spec.md` exists, seeded by the
  real `spec_merge.py` from the pre-authored delta, and the kanban CLI
  renders its board and list views over the sample cards

#### Scenario: Later cycles are authored live
- **WHEN** cycle 2 or 3 begins
- **THEN** its artifact set is authored in the session under the sandbox's
  `planned/`, folding in the user's design decisions

#### Scenario: The real repo is untouched
- **WHEN** any walkthrough cycle plans or builds
- **THEN** every engine invocation carries the sandbox root and every file
  write lands under the sandbox, leaving the user's repository unmodified

#### Scenario: Cleanup is offered, not forced
- **WHEN** the walkthrough ends
- **THEN** the user is asked whether to delete the sandbox or keep it for
  further exploration
