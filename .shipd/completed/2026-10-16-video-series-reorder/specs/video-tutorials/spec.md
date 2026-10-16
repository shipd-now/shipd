## MODIFIED Requirements

### Requirement: Episode scripts follow the template
id: video-episode-scripts
base: 2b5e188bf81e
Dropped: Episode 4 keeps the spotlight beats

The repository SHALL carry ten episode scripts under `docs/tutorials/videos/`: `01-install-and-build.md`, `02-plan-and-specs.md`, `03-worktrees-and-small-prs.md`, `04-prds-and-guardrails.md`, `05-epics-and-epic-grill.md`, `06-oracle-and-supersession-gate.md`, `07-workspaces-101.md`, `08-advanced-workspaces.md`, `09-ci-and-copilot-review.md`, and `10-management-plane.md`. Each script SHALL declare `how-to`, SHALL carry the template's sections in the template's order, and SHALL open its `## Script` with a beat starting at `0:00`. Episode 1 SHALL show installing shipd and shipping a change with `/s:build` from a prose request; episode 2 SHALL show `/s:plan` and the artifacts it writes.

#### Scenario: Every episode carries the template's sections
- **WHEN** a reader lists the level-2 headings of any episode script
- **THEN** they read `Introduction`, `At a glance`, `Script`, `Takeaways`, `Next`, `Sources`, in that order

#### Scenario: Episode 5 keeps the spotlight beats
- **WHEN** a reader opens `05-epics-and-epic-grill.md`
- **THEN** its beats start at `0:00`, `1:00`, `2:30`, and `4:00`, and the last beat ends at `5:00`

#### Scenario: Episode 1 installs before it builds
- **WHEN** a reader opens `01-install-and-build.md`
- **THEN** its `Commands shown` row names the install command and `/s:build`, and no beat shows `/s:plan`

### Requirement: Scripts match documented behavior
id: video-scripts-grounded
base: 7c2c2f036d9d

Each episode script SHALL describe shipd only as its `## Sources` docs and specs describe it, and SHALL use each glossary term of the documentation standard in its one defined meaning.

#### Scenario: An epic is never a group of PRDs
- **WHEN** episode 5 describes an epic
- **THEN** it calls the epic a decomposition of one feature into member changes, and a PRD the input that precedes it

### Requirement: Series overview
id: video-series-overview
base: 3e9efcd0b6fe

The repository SHALL carry `docs/tutorials/videos/index.md`, a `concept` doc that lists the ten episodes in the roadmap's three groups, links each episode file, and states that episodes 1–9 cover open-source shipd while episode 10 covers the commercial management plane.

#### Scenario: Overview links every episode
- **WHEN** a reader opens `index.md`
- **THEN** it links all ten episode files and `docs_lint.py` exits 0 on it
