## MODIFIED Requirements

### Requirement: Teach skill entry
id: teach-skill
base: 18443a1ca203

The plugin SHALL provide `/s:teach` at `plugins/s/skills/teach/SKILL.md`,
which SHALL announce the running plugin version in its first user-visible
status sentence and SHALL run the intake flow: resolve the wiki store, scan
and distill the repo's spec artifacts, interview only on gaps and
contradictions, and ingest through the staged emit verb. When the resolved
store does not exist yet, the skill SHALL scaffold it with `wiki-init`.
Where no workspace is discoverable but the repo's resolved content directory
exists, the skill SHALL continue on the repo-local fallback store `wiki-show`
reports (annotated `(repo-local fallback)`), scaffolding it the same way;
only where neither a workspace nor a content directory exists SHALL the
skill stop and point the user at `workspace-init` or `shipd init` instead of
inventing a store location.

#### Scenario: Skill file carries the flow
- **WHEN** `plugins/s/skills/teach/SKILL.md` is inspected
- **THEN** it directs the version announcement and the
  resolve → scan → distill → interview → ingest flow with `wiki-init`
  scaffolding for a missing store

#### Scenario: Bare repo teaches into the fallback store
- **WHEN** the skill runs where no ancestor declares a workspace and the
  content directory exists
- **THEN** it continues on the repo-local fallback store rather than
  stopping, scaffolding it when absent

#### Scenario: Uninitialized repo stops with guidance
- **WHEN** the skill runs where no ancestor declares a workspace and no
  content directory exists
- **THEN** it stops, names both missing prerequisites, and points at
  `workspace-init` or `shipd init` — no store is created or written
