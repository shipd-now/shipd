## ADDED Requirements

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
