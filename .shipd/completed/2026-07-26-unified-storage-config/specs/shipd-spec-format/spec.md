## MODIFIED Requirements

### Requirement: Master spec library layout
id: master-spec-library-layout
base: 8090c008ed0b

The system SHALL store canonical specifications at
`<content-dir>/verified/<capability>/spec.md`, one file per capability,
where `<content-dir>` is the configured content directory (default `.am`).
Each file SHALL contain zero or more requirement blocks, each introduced by
a `### Requirement: <title>` header, and this location SHALL be the single
source of truth that the merge engine reads and writes.

#### Scenario: Locating a capability's canonical spec
- **WHEN** a tool needs the current definition of the `enforce-sso-timeout`
  requirement in the `auth` capability under the default configuration
- **THEN** it reads `.shipd/verified/auth/spec.md` and finds the requirement
  block whose `id` is `enforce-sso-timeout`

### Requirement: Per-change artifact layout
id: per-change-artifact-layout
base: d42969309eee

A change SHALL live at `<content-dir>/planned/<change>/` (default
`.shipd/planned/<change>/`) and SHALL always contain the lean artifact set: a
single `plan.md` holding the change's idea and implementation decisions, a
delta spec at `specs/<capability>/spec.md` for each affected capability, and
`tasks.md` as a separate executor-owned checklist. This artifact set SHALL
be produced for every change regardless of size.

#### Scenario: A change carries the lean artifact set
- **WHEN** a change `dark-mode-toggle` is authored under the default
  configuration
- **THEN** `.shipd/planned/dark-mode-toggle/` contains `plan.md`, at least one
  `specs/<capability>/spec.md`, and `tasks.md`

#### Scenario: Tasks stay out of the plan document
- **WHEN** an executor marks tasks done during a build
- **THEN** only `tasks.md` checkboxes change and `plan.md` is not rewritten

### Requirement: Applied changes move to completed
id: archive-of-applied-changes
base: a28d89bbf703

After a change's delta is merged into the master library, the change
directory SHALL be moved to `<content-dir>/completed/<date>-<change>/` so
the applied change is retained immutably for auditability and never
re-merged. `completed/` SHALL be a sibling of `planned/` inside the content
directory, so `planned/` contains only live changes.

#### Scenario: Applied change is retained under completed
- **WHEN** the merge engine finishes applying change `dark-mode-toggle`
  under the default configuration
- **THEN** `.shipd/planned/dark-mode-toggle/` no longer exists and
  `.shipd/completed/<date>-dark-mode-toggle/` contains its artifacts

### Requirement: Theme vocabulary config
id: theme-vocabulary-config
base: 06291a1c2bd5

The system SHALL read the theme vocabulary from the resolved layered
configuration's top-level `valid_themes` key. When the resolved value is a
non-empty array, a plan's `Theme:` value SHALL be validated against it; when
no layer declares `valid_themes`, any kebab-case theme SHALL be accepted.
The retired `am/config.json` SHALL NOT be read.

#### Scenario: Theme outside the vocabulary is invalid
- **GIVEN** the repo's `.shipd-config.json` declares
  `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: developer-experience`
- **THEN** tooling reports the theme as outside the vocabulary

#### Scenario: No declared vocabulary accepts any kebab theme
- **WHEN** no config layer declares `valid_themes` and a plan carries
  `Theme: any-label`
- **THEN** the theme is accepted

### Requirement: Epic artifact layout
id: epic-artifact-layout
base: 2da9da452a36

An epic SHALL live at `<content-dir>/epics/<slug>/epic.md` (default
`.shipd/epics/<slug>/epic.md`), beginning with a `# <slug>` title matching its
directory, a `Status:` line whose value is one of `draft`, `ready`,
`active`, `complete`, and optionally a header metadata block. The document
SHALL carry `## Introduction`, `## Decisions`, `## Design`, and `## Changes`
sections, and `## Introduction` SHALL be the first level-2 section. The
Introduction SHALL open with the problem and its motivation before
describing the feature and its intended outcome, with success criteria
recommended, and SHALL include a `### Non-goals` subsection listing the
scope exclusions. `## Changes` SHALL hold a stub table with the exact
columns `| Change | Description | Code | Integration | Unknowns | Risk |`,
at least one data row, kebab-case change slugs unique within the table, and
every rating cell one of `low`, `medium`, `high`.

#### Scenario: Conforming epic is valid at the new path
- **WHEN** `.shipd/epics/reporting-overhaul/epic.md` starts with
  `# reporting-overhaul`, `Status: draft`, opens with an `## Introduction`
  carrying a `### Non-goals` subsection, carries `## Decisions`,
  `## Design`, and `## Changes`, and its stub table lists `csv-export` with
  ratings `low`/`medium`/`low`/`low`
- **THEN** tooling accepts the epic as structurally valid

#### Scenario: Missing introduction is rejected
- **WHEN** an epic carries `## Decisions`, `## Design`, and `## Changes`
  but no `## Introduction` section
- **THEN** tooling reports the missing section

#### Scenario: Invalid rating is rejected
- **WHEN** a stub row's Risk cell reads `huge`
- **THEN** tooling reports the invalid rating
