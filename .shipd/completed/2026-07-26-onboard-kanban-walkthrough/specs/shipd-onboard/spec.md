## REMOVED Requirements

### Requirement: Onboarding docs library
id: onboarding-docs-library
base: 790c8b4e8d0d
Reason: The chapter-based curriculum is retired — onboarding is now a single hands-on sandbox walkthrough whose teaching is woven into the build cycles, so a separate chapter library has no consumer.
Migration: Delete `docs/onboarding/` (all six chapter files). The walkthrough narrative in the onboard skill and the authoritative references (`.shipd/README.md`, `AGENTS.md`) carry the content.

## MODIFIED Requirements

### Requirement: Onboard tour skill
id: onboard-tour-skill
base: 15a575cec225

An `/s:onboard` skill SHALL run a hands-on walkthrough that starts in sandbox
mode without offering a choice: when invoked, it SHALL scaffold the throwaway
sandbox immediately, orient the user on what they can do there, and then drive
guided plan → build → merge cycles that incrementally build a CLI kanban app —
first the board view, then adding cards, then editing cards — prompting the
user with each cycle's planning task. The skill SHALL NOT present a chapter
menu or any start-choice, and SHALL NOT depend on a chapter library.

#### Scenario: Invocation goes straight to the sandbox
- **WHEN** a user runs `/s:onboard`
- **THEN** the session scaffolds the sandbox and tells the user what they can
  do, with no chapter menu or start-choice offered first

#### Scenario: Cycles follow the scripted sequence
- **WHEN** the walkthrough proceeds past the scaffold
- **THEN** the guided cycles run in order — the kanban board, then adding
  cards, then editing cards — each one a real plan → build → merge pass

#### Scenario: Lifecycle is explained after each merge
- **WHEN** a cycle's change is merged
- **THEN** the guide explains what happened to the artifacts: the change moved
  from the sandbox's `planned/` to its `completed/`, and the sandbox's master
  specs now carry the cycle's requirements

### Requirement: Sandbox hands-on session
id: sandbox-hands-on
base: a60e0a54ca5d

The walkthrough SHALL run entirely inside a scaffolded sandbox: a temporary
directory holding a git-initialized mini-repo with an empty `.shipd/` layout
(`verified/`, `planned/`). Each guided cycle SHALL author a change's lean
artifact set under the sandbox's `planned/`, lint it, drive its status, tick
its tasks with the coordinator, implement the kanban CLI code, and merge — all
by invoking the plugin's real engine scripts by absolute path with the sandbox
as their root. The session SHALL NOT create or modify any file in the user's
real repository, and the walkthrough SHALL end by offering to delete or keep
the sandbox.

#### Scenario: First cycle creates the kanban capability
- **WHEN** the first cycle's change merges
- **THEN** the sandbox's `.shipd/verified/kanban/spec.md` exists, seeded by the
  real `spec_merge.py` from the cycle's delta, and the implemented kanban CLI
  renders its board and list views over the sample cards

#### Scenario: The real repo is untouched
- **WHEN** any walkthrough cycle plans or builds
- **THEN** every engine invocation carries the sandbox root and every file
  write lands under the sandbox, leaving the user's repository unmodified

#### Scenario: Cleanup is offered, not forced
- **WHEN** the walkthrough ends
- **THEN** the user is asked whether to delete the sandbox or keep it for
  further exploration

### Requirement: Checkpoint resume after interruption
id: checkpoint-resume
base: c2997b1bd116

If a walkthrough turn is interrupted or a checkpoint question comes back
rejected, then the walkthrough SHALL resume from the last reached checkpoint
on the user's next message — re-offering that checkpoint's choices when the
message does not itself answer them — and SHALL NOT restart from the beginning
or treat the interruption as a stop. Only an explicit Stop choice SHALL end
the walkthrough.

#### Scenario: Interrupted checkpoint resumes in place
- **WHEN** a checkpoint prompt is rejected by a harness misfire and the user's
  next message asks to continue
- **THEN** the walkthrough re-offers that same checkpoint's choices and
  proceeds from that cycle, not from the scaffold

#### Scenario: Interruption is not a stop
- **WHEN** a walkthrough turn is interrupted mid-cycle
- **THEN** the walkthrough does not end; the next user message picks it up at
  the last reached checkpoint

### Requirement: Plain-text tour prompts
id: plain-text-tour-prompts
base: ffc710cf8ec2

Because the harness can drop narration sharing a turn with a dialog, the
walkthrough SHALL offer every cycle checkpoint and next-step prompt as a
plain-text numbered prompt in the same message as the narration it follows,
answered by the user's typed reply, with the recommended default named first.
The walkthrough SHALL NOT issue an AskUserQuestion in any turn that carries
narration or teaching content; dialogs MAY remain only for prose-free prompts
such as the sandbox cleanup offer.

#### Scenario: Checkpoint is typed, narration stays visible
- **WHEN** a cycle completes and the walkthrough reaches its checkpoint
- **THEN** the cycle's narration and a numbered continue/re-explain/stop
  prompt form one plain-text message and the choice is read from the user's
  typed reply, with no AskUserQuestion issued

#### Scenario: Prose-free prompts may stay dialogs
- **WHEN** the walkthrough ends and offers delete-or-keep
- **THEN** that prompt may be an AskUserQuestion, since its turn carries no
  narration content
