## ADDED Requirements

### Requirement: Remember capture skill
id: remember-skill

The plugin SHALL provide `/s:remember` at
`plugins/s/skills/remember/SKILL.md` that announces the running plugin
version, resolves the personal memory store with `wiki-show --personal`
(scaffolding it with `wiki-init --personal` when no store exists), extracts
memory candidates from the invocation argument or the session, reconciles
each against existing `memory-*` pages in the personal store — adding a new
page, updating an existing one, or skipping a duplicate — confirms the proposed
set with the user in a typed plain-text round before any write, and installs the
touched subset through a single staged `spec_emit.py wiki --personal` call
(touched `memory-<subject>.md` pages, the full `index.md`, and a dated `log.md`
entry). The skill SHALL never edit store files in place, and SHALL issue no
AskUserQuestion (its confirmation is a typed round), so it does not join the
question-rejection-recovery roster.

#### Scenario: Skill definition carries the capture contract
- **WHEN** `plugins/s/skills/remember/SKILL.md` is inspected
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
- **WHEN** `/s:remember` runs and `wiki-show --personal` reports no store
- **THEN** the skill scaffolds it with `wiki-init --personal` before installing
  the captured pages

#### Scenario: Confirmation precedes any write
- **WHEN** the skill has a proposed set of captures
- **THEN** it presents them with their add/update/skip classification and writes
  nothing until the user gives a typed go-ahead

#### Scenario: No stale preferences skill remains
- **WHEN** the plugin's skills directory is inspected
- **THEN** `plugins/s/skills/preferences/` no longer exists and no
  `plugins/s/` file or `.shipd/verified/` master references `/s:preferences`

## MODIFIED Requirements

### Requirement: Git-backing flow
id: git-backing-flow
base: 85e098c1e4d6

`/s:remember` SHALL run a git-backing flow around the capture install,
driven by the skill (not the engine) and confirmed in typed rounds (no
AskUserQuestion). It SHALL detect whether the personal store's git root
`<memory_dir>` (the parent of the `<memory_dir>/wiki` store) is inside a git work
tree. When it is not, the skill SHALL offer to `git init <memory_dir>` before the
staged emit — so the capture's `wiki_autocommit` includes the first page — and,
only on the user's confirmation and where `gh` is available and authenticated,
SHALL offer to create and wire a private `shipd-memory` remote (`gh repo create
shipd-memory --private` plus `git remote add origin`) and then offer a confirmed
`git push`; where `gh` is absent or the user declines the remote, the skill SHALL
complete the local `git init` and print the manual remote-and-push commands.
When the store is already a git repo with an `origin` remote and unpushed
commits, the skill SHALL offer a confirmed `git push`. The engine SHALL NOT push,
pull, or fetch — all remote and push actions are skill-driven and always
confirmed, and a failed `gh` or `git push` SHALL be non-fatal (reported, with the
local commit remaining the durable outcome). The personal repo MAY also hold a
copy of `~/.shipd-config.json` as a documented user convention, but no engine reads
or syncs settings.

#### Scenario: First-run offers git init before the commit
- **GIVEN** a capture against a personal store whose `<memory_dir>` is not a git
  work tree
- **WHEN** the user accepts the offered `git init`
- **THEN** the skill initializes the repo at `<memory_dir>` before the staged
  emit, so the captured page lands in a commit via `wiki_autocommit`

#### Scenario: Remote wiring and push are confirmed and gh-gated
- **WHEN** the first-run flow reaches the remote step with `gh` available
- **THEN** it offers `gh repo create shipd-memory --private` and `git remote add
  origin` and a subsequent `git push` only on the user's typed confirmation

#### Scenario: gh absent degrades to local init
- **WHEN** `gh` is not available or the user declines the remote
- **THEN** the skill completes the local `git init` and prints the manual
  remote-and-push commands, and the capture still succeeds

#### Scenario: Ongoing push offered when out of sync
- **GIVEN** a git-backed personal store with an `origin` remote and unpushed
  commits
- **WHEN** a later capture completes
- **THEN** the skill offers a confirmed `git push`

#### Scenario: Engine never pushes
- **WHEN** `plugins/s/skills/remember/SKILL.md` and the flow are inspected
- **THEN** every `git push` / `gh` action is skill-driven and typed-confirmed,
  the engine's role stays the local `wiki_autocommit` commit, and a failed push
  is non-fatal

#### Scenario: Flow uses no AskUserQuestion
- **WHEN** the git-backing flow prompts for init, remote, or push
- **THEN** each prompt is a typed plain-text round and the skill issues no
  AskUserQuestion, keeping `/s:remember` off the question-rejection-recovery
  roster

## REMOVED Requirements

### Requirement: Preferences capture skill
id: preferences-skill
base: c6edd9d038db
Reason: Renamed to `/s:remember` — the capture verb pairs with `/s:forget` and matches the general "memory" framing; "preferences" wrongly narrowed the concept.
Migration: The capture skill moves to `plugins/s/skills/remember/` with its contract preserved under `remember-skill`; invoke `/s:remember` in place of `/s:preferences`.
