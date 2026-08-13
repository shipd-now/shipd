## ADDED Requirements

### Requirement: Onboarding docs library
id: onboarding-docs-library

The repository SHALL carry the onboarding content as six numbered chapters —
`docs/onboarding/01-concepts.md`, `02-artifacts.md`, `03-planning.md`,
`04-building.md`, `05-scaling.md`, `06-workflow.md` — and these files SHALL
be the single source of tour content. Each chapter SHALL open with a short
"what you'll learn" lead, SHALL narrate rather than restate normative
grammar, and SHALL end by pointing at the authoritative references it draws
on (`am/README.md`, `AGENTS.md`, or the relevant skill).

#### Scenario: Chapters exist as the content source
- **WHEN** the onboarding content is inspected
- **THEN** the six numbered chapter files exist under `docs/onboarding/` and
  the tour skill contains no duplicated chapter text

#### Scenario: Chapters point at authority instead of restating it
- **WHEN** a chapter covers the delta-spec grammar
- **THEN** it explains the idea in narrative form and links `am/README.md`
  for the normative rules rather than reproducing them

### Requirement: Onboard tour skill
id: onboard-tour-skill

An `/s:onboard` skill SHALL run the guided tour: loading the chapters in
numbered order, opening with a chapter menu whose recommended option is the
full start-to-finish path, teaching one chapter at a time, illustrating each
chapter from the user's live repository state where the relevant features
exist, and pausing after each chapter at a checkpoint offering continue,
re-explain, jump, or stop. The plugin SHALL NOT retain the `am:hello`
command; `/s:onboard` SHALL be the onboarding entry point.

#### Scenario: Tour follows the chapters with checkpoints
- **WHEN** a user runs `/s:onboard` and accepts the default path
- **THEN** the tour teaches chapter 1 from `docs/onboarding/01-concepts.md`,
  pauses at a checkpoint, and proceeds through the chapters in numbered
  order

#### Scenario: Live repo illustrates the lesson
- **WHEN** the tour reaches the artifacts chapter in a repo with a populated
  `am/verified/`
- **THEN** the tour lists that repo's actual capabilities as its example
  rather than a fictional one

#### Scenario: Hello command is retired
- **WHEN** the plugin's `commands/` directory is inspected
- **THEN** no `hello.md` exists and the onboarding entry point is the
  `/s:onboard` skill

### Requirement: Sandbox hands-on session
id: sandbox-hands-on

The tour's final chapter SHALL offer a hands-on session in a scaffolded
sandbox: a temporary directory with a git-initialized mini-repo carrying an
`am/` layout and a toy `greeter` capability. The tour SHALL guide the user
through authoring a toy change's lean artifact set, linting it, driving its
status, ticking its tasks with the coordinator, and merging it — all by
invoking the plugin's real engine scripts by absolute path against the
sandbox — and SHALL end by offering to delete or keep the sandbox. The
session SHALL NOT touch the user's real repository.

#### Scenario: Sandbox exercises the real engine
- **WHEN** the hands-on session lints the toy change
- **THEN** the command is the plugin's own `spec_lint.py` run with the
  sandbox as its root, and its real output is shown to the user

#### Scenario: The real repo is untouched
- **WHEN** the hands-on session completes
- **THEN** no file under the user's repository has been created or modified
  by the session

#### Scenario: Cleanup is offered, not forced
- **WHEN** the sandbox session ends
- **THEN** the user is asked whether to delete the sandbox or keep it for
  further exploration
