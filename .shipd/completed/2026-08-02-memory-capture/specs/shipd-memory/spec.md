## ADDED Requirements

### Requirement: Memory page family
id: memory-page-family

A captured user preference SHALL be stored as an ordinary wiki page
`wiki/memory-<subject>.md` in the **personal memory store** (`<memory_dir>/wiki`,
default `~/.shipd-memory/wiki`), with a kebab-case `<subject>`, carrying a one-line
preference statement followed by a provenance block naming the originating repo
(`- Origin:`) and the capture date (`- Captured:`). A `memory-*` page SHALL be
indexed, linted, and retrieved through the same store machinery as any other
wiki page — no new store file and no schema change — distinguished only by the
`memory-` slug prefix. The engine SHALL NOT introduce embeddings, a vector
store, a database, or any external service for preference storage or retrieval.

#### Scenario: Captured preference is an ordinary indexed page
- **WHEN** a `memory-editor-choice` page is installed into the personal store
  through the staged `--personal` wiki emit
- **THEN** it lives at `<memory_dir>/wiki/wiki/memory-editor-choice.md`, appears
  in that store's `index.md` as a `- [[memory-editor-choice]] — <summary>`
  entry, and passes the whole-store wiki lint

#### Scenario: Provenance recorded
- **WHEN** a memory page is captured
- **THEN** its body carries the one-line statement plus `- Origin:` (the
  invoking repo) and `- Captured:` (the date) provenance lines

### Requirement: Preferences capture skill
id: preferences-skill

The plugin SHALL provide `/s:preferences` at
`plugins/s/skills/preferences/SKILL.md` that announces the running plugin
version, resolves the personal memory store with `wiki-show --personal`
(scaffolding it with `wiki-init --personal` when no store exists), extracts
preference candidates from the invocation argument or the session, reconciles
each against existing `memory-*` pages in the personal store — adding a new
page, updating an existing one, or skipping a duplicate — confirms the proposed
set with the user in a typed plain-text round before any write, and installs the
touched subset through a single staged `spec_emit.py wiki --personal` call
(touched `memory-<subject>.md` pages, the full `index.md`, and a dated `log.md`
entry). The skill SHALL never edit store files in place, and SHALL issue no
AskUserQuestion (its confirmation is a typed round), so it does not join the
question-rejection-recovery roster.

#### Scenario: Skill definition carries the capture contract
- **WHEN** `plugins/s/skills/preferences/SKILL.md` is inspected
- **THEN** it directs announcing the version, resolving the store via
  `wiki-show --personal`, reconciling candidates against existing `memory-*`
  pages, confirming in a typed round, and installing only through staged
  `spec_emit.py wiki --personal`

#### Scenario: Duplicate is skipped, new is added, changed is updated
- **WHEN** the skill reconciles a candidate against the personal store
- **THEN** a candidate the store already records is skipped, a novel candidate
  becomes a new `memory-<subject>` page, and a candidate that changes an
  existing page's statement re-emits that page (no in-place edit)

#### Scenario: Absent store is scaffolded first
- **WHEN** `/s:preferences` runs and `wiki-show --personal` reports no store
- **THEN** the skill scaffolds it with `wiki-init --personal` before installing
  the captured pages

#### Scenario: Confirmation precedes any write
- **WHEN** the skill has a proposed set of captures
- **THEN** it presents them with their add/update/skip classification and writes
  nothing until the user gives a typed go-ahead
