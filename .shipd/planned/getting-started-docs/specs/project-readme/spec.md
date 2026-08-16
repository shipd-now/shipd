## ADDED Requirements

### Requirement: Getting-started guide
id: getting-started-doc

A `docs/getting-started.md` SHALL walk a newcomer through their first working
session in this order: registering the ☕ statusline, then taking one change
through `/s:plan` and `/s:build`. The guide SHALL explain each planning
artifact — `plan.md`, the per-capability delta `spec.md`, and `tasks.md` —
with its purpose, and SHALL name the three durable outcomes of a build: the
`change/<name>` branch, the merge into `verified/`, and the archive under
`completed/`. Where it documents statusline registration for an installed
plugin, the guide SHALL give a command that resolves the newest cached
snapshot rather than a version-pinned path.

#### Scenario: Statusline precedes the walkthrough
- **WHEN** a reader follows `docs/getting-started.md` top to bottom
- **THEN** the statusline registration and its rendered segments are explained
  before the `/s:plan` walkthrough begins

#### Scenario: Artifacts are each explained
- **WHEN** the reader reaches the planning walkthrough
- **THEN** `plan.md`, the delta `specs/<capability>/spec.md`, and `tasks.md`
  are each explained with their purpose, and the delta's WHEN/THEN scenario
  grammar is shown in an excerpt

#### Scenario: Build outcomes are named
- **WHEN** the reader reaches the build walkthrough
- **THEN** the change branch, the `verified/` master-library merge, and the
  `completed/` archive are all named as the build's durable outcomes

#### Scenario: Install-mode registration survives updates
- **WHEN** the documented install-mode statusline command is executed with
  more than one snapshot in the plugin cache
- **THEN** it runs the newest snapshot's `integrations/statusline.sh` under
  dotted-version ordering, not a version-pinned path
