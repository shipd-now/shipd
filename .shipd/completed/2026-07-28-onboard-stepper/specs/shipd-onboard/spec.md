## ADDED Requirements

### Requirement: Step navigation
id: onboard-step-navigation

The `/s:onboard` skill SHALL run as a nine-step sequence driven by explicit
navigation arguments: with no argument it SHALL start at step 1 (scaffolding
first) when no state exists, or resume at the persisted current step; `next`
SHALL advance one step; `back` SHALL return to the previous step, clamped at
step 1 and offered on the explainer steps. The skill SHALL persist the
current step and sandbox path in `~/.shipd/onboarding/state.json`, with the
sandbox at the stable path `~/.shipd/onboarding/sandbox/`, so navigation
survives across sessions. Mutating steps SHALL be idempotent on re-entry:
when step 8's build has already merged in the sandbox, re-entering step 8
SHALL re-show the built summary rather than re-running the build.

#### Scenario: Fresh start scaffolds and records step 1
- **WHEN** `/s:onboard` runs with no argument and no state file exists
- **THEN** the sandbox is scaffolded at the stable path, the state file
  records step 1, and step 1 renders

#### Scenario: Next advances and persists
- **WHEN** `/s:onboard next` runs
- **THEN** the state file's step increments by one and the new step renders

#### Scenario: Back returns without restarting
- **WHEN** `/s:onboard back` runs on an explainer step
- **THEN** the state file's step decrements — never below 1 — and that step
  renders again

#### Scenario: Resume across sessions
- **WHEN** `/s:onboard` runs with no argument in a new session and a state
  file exists
- **THEN** the walkthrough resumes at the recorded step without restarting

## MODIFIED Requirements

### Requirement: Onboard tour skill
id: onboard-tour-skill
base: a23744fbfad6

An `/s:onboard` skill SHALL teach through a fixed nine-step walkthrough:
(1) what Spec-Driven Development is, in one paragraph; (2) how shipd
works — it creates artifacts and executes in worktrees, briefly explained,
enabling many changes in parallel; (3) the artifacts as short dot points;
(4) the example `plan.md`; (5) the example delta spec; (6) the example
tasks plus the model-tiering approach — the best model plans and the
second-best executes, for efficiency, speed, and cost; (7) a pause that
summarizes what was learned; (8) implementing the tasks and building the
kanban board, ending with what was built and how to test it in the shell;
(9) a suggested small enhancement with the exact copy/paste command to plan
it. On a fresh start the first visible output SHALL be the shipd ASCII
banner — carried verbatim in the skill, identical to the README masthead —
in a fenced code block above the greeting. The skill SHALL NOT present a
chapter menu or any start-choice, and SHALL NOT depend on a chapter library.

#### Scenario: Banner opens a fresh start
- **WHEN** `/s:onboard` starts fresh
- **THEN** the first visible output is the shipd ASCII banner in a fenced
  code block, followed by the greeting and step 1

#### Scenario: Steps follow the fixed order
- **WHEN** the user advances with `next` from step 1 onward
- **THEN** the steps render in the fixed order — SDD, how shipd works,
  artifact dot points, plan.md, spec, tasks, summary, implement, enhancement
  handoff

#### Scenario: Model tiering is taught
- **WHEN** step 6 renders
- **THEN** it explains that shipd plans on the best model and executes
  tasks on the second-best for efficiency, speed, and cost

### Requirement: Sandbox hands-on session
id: sandbox-hands-on
base: 5478a78c999d

The walkthrough SHALL use the shipped template's pre-baked `add-board`
change as its single worked example: steps 4–6 SHALL quote short excerpts
from the sandbox's actual `plan.md`, delta spec, and `tasks.md`. Step 8
SHALL execute the change for real — lint, promote, copy the reference
implementation in, tick tasks with the coordinator, drive complete and
verified, and merge — always via the plugin's engine scripts by absolute
path with the sandbox as their root — then SHALL state what was built and
print copy/paste shell instructions to try it. Step 9 SHALL suggest a small
enhancement and print the exact copy/paste commands to plan it in the
sandbox. The session SHALL NOT create or modify any file in the user's real
repository, and the walkthrough SHALL end by offering to delete or keep
`~/.shipd/onboarding/`.

#### Scenario: The real artifacts are shown, not paraphrased
- **WHEN** steps 4, 5, or 6 render
- **THEN** the excerpts shown come from the sandbox's actual artifact files

#### Scenario: Step 8 builds and hands over testing
- **WHEN** step 8 completes its build
- **THEN** the `add-board` change is merged in the sandbox, the rendered
  board is shown, and the user receives copy/paste shell commands to run
  `kanban.py` themselves

#### Scenario: Step 9 hands over a runnable plan command
- **WHEN** step 9 renders
- **THEN** it names a small enhancement and prints the exact commands to
  open a session in the sandbox and run `/s:plan` for it

#### Scenario: The real repo is untouched
- **WHEN** any step runs
- **THEN** every engine invocation carries the sandbox root and every file
  write lands under `~/.shipd/onboarding/`, leaving the user's repository
  unmodified

#### Scenario: Cleanup is offered, not forced
- **WHEN** the walkthrough ends
- **THEN** the user is asked whether to delete or keep `~/.shipd/onboarding/`

### Requirement: Walkthrough pacing
id: walkthrough-pacing
base: 3bbf43c58638

The walkthrough SHALL advance only on explicit navigation: each step SHALL
end by naming the exact command to continue (`/s:onboard next`, plus
`/s:onboard back` on explainer steps) and SHALL NOT auto-advance to the
next step. Within a step, the guide SHALL explain before doing, keep the
step brief rather than a recap essay, quote files only as short excerpts,
and keep post-merge lifecycle explanations to a few sentences. The
walkthrough SHALL NOT narrate internal troubleshooting or command-syntax
discovery — the documented engine invocations are used as written.

#### Scenario: A step never auto-advances
- **WHEN** a step finishes rendering
- **THEN** the turn ends with the navigation instruction and the next step
  renders only after the user runs the named command

#### Scenario: No internal noise reaches the user
- **WHEN** the guide runs an engine command during step 8
- **THEN** it uses the invocation documented in the skill and shows the
  command's real output, without narrating syntax discovery or
  troubleshooting detours

### Requirement: Plain-text tour prompts
id: plain-text-tour-prompts
base: 02190aa0c6e4

Because the harness can drop narration sharing a turn with a dialog, every
step's navigation instruction SHALL be plain text in the same message as
the step's content, naming the `/s:onboard next` (and, where available,
`back`) commands. The walkthrough SHALL NOT issue an AskUserQuestion in any
turn that carries step content; dialogs MAY remain only for prose-free
prompts such as the cleanup offer.

#### Scenario: Navigation is plain text with the content
- **WHEN** a step renders
- **THEN** its content and the navigation instruction form one plain-text
  message with no AskUserQuestion issued

#### Scenario: Prose-free prompts may stay dialogs
- **WHEN** the walkthrough ends and offers delete-or-keep
- **THEN** that prompt may be an AskUserQuestion, since its turn carries no
  step content

## REMOVED Requirements

### Requirement: Checkpoint resume after interruption
id: checkpoint-resume
base: 1d27ae1ffdd0
Reason: Superseded — resume is now mechanical: `/s:onboard` with no argument reads the persisted state file and re-renders the recorded step, so a conversational checkpoint-recovery contract no longer defines the mechanism.
Migration: The resume contract lives in `onboard-step-navigation` (persisted `~/.shipd/onboarding/state.json`); interrupted sessions resume by re-running `/s:onboard`.
