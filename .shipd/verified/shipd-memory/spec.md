# shipd-memory

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

### Requirement: Memory listing skill
id: memory-list-skill

The plugin SHALL provide `/s:memory` at `plugins/s/skills/memory/SKILL.md`
that announces the running plugin version, resolves the personal memory store
with `wiki-show --personal`, and lists the stored memories by reading `cat wiki
index --personal` and filtering the catalogue to entries whose slug begins with
`memory-`. The skill SHALL be read-only: it SHALL NOT mutate any store file and
SHALL NOT require a new engine verb. When the store is absent or holds no
`memory-*` page, the skill SHALL report that no memories are stored and mutate
nothing.

#### Scenario: Skill definition is read-only
- **WHEN** `plugins/s/skills/memory/SKILL.md` is inspected
- **THEN** it directs announcing the version, resolving the store via
  `wiki-show --personal`, listing the `memory-*` entries from `cat wiki index
  --personal`, and mutating nothing

#### Scenario: Stored memories are listed
- **WHEN** `/s:memory` runs against a personal store holding `memory-*` pages
- **THEN** it prints those pages' catalogue entries and makes no store write

#### Scenario: Empty or absent store reports none
- **WHEN** `/s:memory` runs and the personal store is absent or holds no
  `memory-*` page
- **THEN** the skill reports that no memories are stored and mutates nothing

### Requirement: Forget skill
id: forget-skill

The plugin SHALL provide `/s:forget` at `plugins/s/skills/forget/SKILL.md`
that announces the running plugin version, takes a free-text description of the
memory to remove, resolves the personal memory store, and locates the matching
`memory-*` page by reading `cat wiki index --personal` and grepping the store's
page bodies for the description's terms. On exactly one match it SHALL confirm
the removal with a single AskUserQuestion carrying the matched page's identity
and summary, and — only on an affirmative selection — remove it with
`wiki-remove <slug> --personal`. If the description matches no page, then the
skill SHALL report that and remove nothing; if it matches more than one, then
the skill SHALL present the candidates for the user to pick before confirming.
The skill SHALL carry the question rejection recovery rule.

#### Scenario: Confirmed removal deletes the page
- **WHEN** the user runs `/s:forget` with a description matching exactly one
  `memory-*` page and affirms the AskUserQuestion
- **THEN** the skill runs `wiki-remove <slug> --personal` and reports the
  removal

#### Scenario: Declined removal keeps the page
- **WHEN** the user declines the confirmation dialog
- **THEN** no `wiki-remove` runs and the page remains

#### Scenario: No match removes nothing
- **WHEN** the description matches no `memory-*` page in the personal store
- **THEN** the skill reports the miss and removes nothing

#### Scenario: Multiple matches are disambiguated
- **WHEN** the description matches more than one `memory-*` page
- **THEN** the skill presents the candidates and removes only the one the user
  selects and confirms

### Requirement: Git-backing flow
id: git-backing-flow

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
