# usage-help

### Requirement: Usage help skill
id: usage-help-skill

The plugin SHALL provide `/s:help <question>` at `plugins/s/skills/help/SKILL.md`, with a harness body at `plugins/s/harness/bodies/help.md`. It SHALL answer how-to questions about shipd. Its `SKILL.md` SHALL direct announcing the running plugin version. The skill SHALL be read-only: it SHALL write no file, SHALL run no command it suggests, and SHALL open no dialog. When invoked with no question, it SHALL ask for one in plain text and stop.

#### Scenario: A how-to question is answered
- **WHEN** a user runs `/s:help How do I handle mid-spec changes?`
- **THEN** the reply gives steps drawn from shipd skills, and no file changes

#### Scenario: A bare invocation asks for a question
- **WHEN** a user runs `/s:help` with no argument
- **THEN** the reply asks for a question in plain text and stops

### Requirement: Usage help sources
id: usage-help-sources

The skill SHALL read the frontmatter description of every installed skill, then open only the skills that match and the references they name. It SHALL run `shipd --help` when a CLI verb may answer. It SHALL NOT answer from model memory, fetch online docs, or read the state of the user's repository.

#### Scenario: Sources are the installed plugin
- **WHEN** `plugins/s/skills/help/SKILL.md` and its harness body are inspected
- **THEN** each names the skill files and `shipd --help` as the only sources and forbids answering from model memory

### Requirement: Honest usage verdict
id: usage-help-verdict

The answer SHALL open with exactly one of `Supported`, `Partly supported`, or `Not supported`. A supported answer SHALL give numbered steps, as many as the task needs, each with its exact command and the skill or verb that backs it. A partly supported answer SHALL also state the gap. If shipd cannot do what the user asks, then the skill SHALL say so and SHALL name the nearest supported option, or state that there is none. It SHALL NOT invent a command, flag, or workflow.

#### Scenario: An unsupported request gets an honest no
- **WHEN** a user runs `/s:help How do I deploy to Kubernetes with shipd?`
- **THEN** the reply opens with `Not supported` and names no invented command

#### Scenario: A multi-step task gets ordered steps
- **WHEN** the answer needs more than one command
- **THEN** the steps are numbered in the order to run them, and each names its command and source

### Requirement: Decisions route to the oracle
id: usage-help-oracle-route

When the question asks for a project decision instead of shipd usage, the skill SHALL name `/s:ask <decision>` without invoking it, and SHALL stop.

#### Scenario: A decision question is redirected
- **WHEN** a user runs `/s:help should the queue prune answered entries?`
- **THEN** the reply names `/s:ask` with the decision and gives no position on it

### Requirement: Usage help documentation
id: usage-help-docs

The repository SHALL provide `docs/help.md` as the how-to page for `/s:help`. It SHALL carry the `how-to` marker, show the three verdicts, and link `oracle.md` for `/s:ask`. `AGENTS.md` SHALL name `/s:help`.

#### Scenario: The page passes the docs lint
- **WHEN** `docs_lint.py docs/help.md` runs
- **THEN** it exits 0
