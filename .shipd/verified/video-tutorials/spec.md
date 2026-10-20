# video-tutorials

### Requirement: Episode template
id: video-episode-template

The repository SHALL carry `docs/tutorials/videos/template.md`, a `how-to` doc that defines the episode structure: a doc-type marker, an `# Episode <N>: <title>` heading, then the sections `## Introduction`, `## At a glance`, `## Script`, `## Takeaways`, `## Next`, and `## Sources`, in that order.

#### Scenario: Template names every section in order
- **WHEN** a reader opens `docs/tutorials/videos/template.md`
- **THEN** its fenced skeleton lists the six sections in the order above, and `docs_lint.py` exits 0 on the file

### Requirement: Episode scripts follow the template
id: video-episode-scripts

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

Each episode script SHALL describe shipd only as its `## Sources` docs and specs describe it, and SHALL use each glossary term of the documentation standard in its one defined meaning.

#### Scenario: An epic is never a group of PRDs
- **WHEN** episode 5 describes an epic
- **THEN** it calls the epic a decomposition of one feature into member changes, and a PRD the input that precedes it

### Requirement: Series overview
id: video-series-overview

The repository SHALL carry `docs/tutorials/videos/index.md`, a `concept` doc that links the intro, Episode 0, ahead of the groups, lists the ten episodes in the roadmap's three groups, links each episode file, and states that episodes 1–9 cover open-source shipd while episode 10 covers the commercial management plane.

#### Scenario: Overview links every episode
- **WHEN** a reader opens `index.md`
- **THEN** it links `00-intro.md` and all ten episode files, and `docs_lint.py` exits 0 on it

### Requirement: Intro episode
id: video-intro

The repository SHALL carry `docs/tutorials/videos/00-intro.md`, an Episode 0 script of about three minutes that declares `how-to`, carries the template's six sections in order, and tells where shipd came from in the author's own account. The repository SHALL also carry `docs/history.md`, a `concept` doc holding that account, and every history claim in the intro SHALL cite it.

#### Scenario: The intro follows the template and runs three minutes
- **WHEN** a reader opens `00-intro.md`
- **THEN** its level-2 headings read `Introduction`, `At a glance`, `Script`, `Takeaways`, `Next`, `Sources`, its first beat starts at `0:00` and its last beat ends at `3:00`, and `docs_lint.py` exits 0 on it

#### Scenario: The intro cites the history page
- **WHEN** a reader opens the intro's `## Sources`
- **THEN** it links `docs/history.md`, and `docs_lint.py` exits 0 on `docs/history.md`

#### Scenario: The history names the dated stages
- **WHEN** a reader opens `docs/history.md`
- **THEN** it places the start in late July 2025, names automikk with its first commit on 2026-07-22, and names shipd as open source under the MIT license with its first commit on 2026-08-13
