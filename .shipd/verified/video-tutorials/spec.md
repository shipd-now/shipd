# video-tutorials

### Requirement: Episode template
id: video-episode-template

The repository SHALL carry `docs/tutorials/videos/template.md`, a `how-to` doc that defines the episode structure: a doc-type marker, an `# Episode <N>: <title>` heading, then the sections `## Introduction`, `## At a glance`, `## Script`, `## Takeaways`, `## Next`, and `## Sources`, in that order.

#### Scenario: Template names every section in order
- **WHEN** a reader opens `docs/tutorials/videos/template.md`
- **THEN** its fenced skeleton lists the six sections in the order above, and `docs_lint.py` exits 0 on the file

### Requirement: Episode scripts follow the template
id: video-episode-scripts

The repository SHALL carry nine episode scripts, `01-core-loop.md` to `09-management-plane.md`, under `docs/tutorials/videos/`. Each script SHALL declare `how-to`, SHALL carry the template's sections in the template's order, and SHALL open its `## Script` with a beat starting at `0:00`.

#### Scenario: Every episode carries the template's sections
- **WHEN** a reader lists the level-2 headings of any episode script
- **THEN** they read `Introduction`, `At a glance`, `Script`, `Takeaways`, `Next`, `Sources`, in that order

#### Scenario: Episode 4 keeps the spotlight beats
- **WHEN** a reader opens `04-epics-and-epic-grill.md`
- **THEN** its beats start at `0:00`, `1:00`, `2:30`, and `4:00`, and the last beat ends at `5:00`

### Requirement: Scripts match documented behavior
id: video-scripts-grounded

Each episode script SHALL describe shipd only as its `## Sources` docs and specs describe it, and SHALL use each glossary term of the documentation standard in its one defined meaning.

#### Scenario: An epic is never a group of PRDs
- **WHEN** episode 4 describes an epic
- **THEN** it calls the epic a decomposition of one feature into member changes, and a PRD the input that precedes it

### Requirement: Series overview
id: video-series-overview

The repository SHALL carry `docs/tutorials/videos/index.md`, a `concept` doc that lists the nine episodes in the roadmap's three groups, links each episode file, and states that episodes 1–8 cover open-source shipd while episode 9 covers the commercial management plane.

#### Scenario: Overview links every episode
- **WHEN** a reader opens `index.md`
- **THEN** it links all nine episode files and `docs_lint.py` exits 0 on it
