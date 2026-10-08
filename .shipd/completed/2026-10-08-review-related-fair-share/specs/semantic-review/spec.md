## MODIFIED Requirements

### Requirement: Related-file context subcommand
id: related-context
base: b0346df77d43

The system SHALL provide `semdiff related <base> [<head>] [--mode
balanced|max]` emitting, per changed file, the files that import it and the
files it imports, as JSON carrying the same best-effort note
`semdiff context` carries — the candidates come from ripgrep when present and
`git grep` otherwise, and are never a complete call graph.

The set SHALL be bounded, and the bound SHALL be part of the contract rather
than a tuning detail: at most 8 related files per changed file and 40 across
the review in `balanced` mode, and at most 20 and 120 in `max` mode.
Candidates SHALL be ranked by proximity — same directory first, then nearest
common ancestor — so the cap keeps the files most likely to matter. Every
truncation SHALL be reported in the output as a count, never applied silently,
so a review can name withheld context among what it could not verify.

`--mode` SHALL default to `balanced`, and the output SHALL state the mode it
ran in.

The per-review budget SHALL be allocated **fairly across changed files**, never
in arrival order. Allocation SHALL proceed in passes: on each pass every changed
file with an unallocated candidate takes its next one, so no changed file
receives a second related file while another with candidates has none. Within a
pass, files SHALL be visited in ascending order of candidate count, so a file
with few candidates is served before a hub with many. Within a changed file,
importees SHALL rank above importers, since an arbitrary sample of a hub's
callers is the weakest context the subcommand can return.

A related file shared by several changed files SHALL be charged against the
per-review cap **once**, and SHALL still be listed under every changed file that
relates to it. The cap bounds what the review must read, and a shared file is
read once however many changed files point at it.

The summary SHALL distinguish the two reasons a changed file carries no related
file: `files_without_candidates`, where the search found nothing to relate, and
`files_starved`, where candidates existed and the budget denied them all. It
SHALL also report `related_files`, the distinct count charged against the cap,
alongside `related_edges`, the number of file-to-related pairs listed.

#### Scenario: No file takes a second while another has none
- **WHEN** more changed files carry candidates than the per-review cap can
  satisfy twice over
- **THEN** every candidate-bearing file holds at least one related file before
  any holds two

#### Scenario: A starved file is distinguished from a file with nothing to relate
- **WHEN** one changed file has no candidates at all and the budget is
  exhausted before another candidate-bearing file is reached
- **THEN** the summary counts the first under `files_without_candidates` and
  the second under `files_starved`

#### Scenario: A shared related file is charged once
- **WHEN** several changed files all relate to the same module
- **THEN** that module counts once against the per-review cap, appears under
  each of those changed files, and `related_edges` exceeds `related_files`

#### Scenario: A scarce file outranks a hub within a pass
- **WHEN** one changed file has two candidates and another has twenty
- **THEN** the file with two is served first in each pass

A candidate SHALL be an **import**, not a mention. An importer SHALL be matched
by the importing syntax of a language — the import, require, use, or include
form that names the module — never by a bare occurrence of the file's name, so
prose that merely discusses a module is not reported as depending on it. The
candidate set SHALL be restricted to files a language could import: a
documentation file, a specification artifact, or any other non-source file
SHALL NOT appear as an importer. An importee SHALL resolve to a path that
exists in the repository, and a changed file that imports in-repository modules
SHALL report them.

#### Scenario: Prose that names a module is not an importer
- **WHEN** a markdown file discusses `semdiff.py` by name and no source file
  imports it
- **THEN** that markdown file does not appear among the importers

#### Scenario: A real importer outranks a cap
- **WHEN** more candidates exist than the per-file cap allows
- **THEN** the surviving entries are importers matched by import syntax, not
  whichever paths sorted first

#### Scenario: Importers and importees both appear
- **WHEN** `semdiff related main` runs over a diff changing one module
- **THEN** each changed file's entry names the files that import it and the
  files it imports, with the best-effort note present

#### Scenario: The bound is reported, not hidden
- **WHEN** a changed file has more related files than the mode's per-file cap
- **THEN** the entry carries the capped list and a count of what was dropped

#### Scenario: Max mode raises the caps
- **WHEN** the same diff is run with `--mode max`
- **THEN** the per-file and per-review caps are the higher pair, and the
  output names the mode

#### Scenario: Neither search tool is present
- **WHEN** `semdiff related` runs where both `rg` and `git` are absent
- **THEN** it fails the way `semdiff context` does, naming the missing tools
