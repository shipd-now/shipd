## ADDED Requirements

### Requirement: Workspaces guide practical examples
id: workspaces-doc-examples

The workspaces guide SHALL provide a practical-examples section on
multi-workspace repos that documents both supported shapes: sibling
workspaces inside a plain repo whose root declares no workspace, and a base
workspace root holding `--nested` job workspaces. For each shape the section
SHALL show a layout diagram distinguishing tracked from machine-local
content, SHALL tabulate where the manifest, wiki, oracle queue, initiatives,
and member repos live, and SHALL give the setup and day-to-day commands
through the `shipd` binary. The section SHALL compare the shapes' pros and
cons, SHALL state that multi-workspace repos are cloned with plain
`git clone` rather than the workspace clone verb, and SHALL warn that git
provides no per-directory access control, so separate repos remain the
isolation boundary.

#### Scenario: Both shapes are walked with storage tables
- **WHEN** the guide's practical-examples section is inspected
- **THEN** it documents the sibling-workspaces shape and the nested-jobs
  shape, each with a layout diagram and a table naming where the manifest,
  wiki, queue, initiatives, and member repos live

#### Scenario: Commands honor the guide's conventions
- **WHEN** the practical-examples section's commands are inspected
- **THEN** every interactive command invokes the `shipd` binary and no
  `spec_status.py` path appears in the section

#### Scenario: Trade-offs and boundaries are stated
- **WHEN** the practical-examples section is inspected
- **THEN** it compares the two shapes' pros and cons, directs multi-workspace
  repos to plain `git clone`, and warns that separate repos — not
  directories — are the access-control boundary
