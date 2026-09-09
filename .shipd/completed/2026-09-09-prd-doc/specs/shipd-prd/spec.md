## ADDED Requirements

### Requirement: PRD user documentation
id: prd-user-docs

The repository SHALL provide `docs/prd.md`, a user-facing guide to the
discover phase that covers: the PRD concept and the
Initiative → PRD → Epic → Change hierarchy with every link optional (a
diagram included); workspace storage at the resolved
`prds/<slug>/prd.md` path with workspace-chain resolution and the PRD's
standalone nature; the `draft`/`approved`/`superseded` lifecycle with
approval as a staged re-install, never a hand edit of the store; the three
template tiers with their exact section lists, their additive nesting, and
`standard` as the default; the `/s:prd` interview as the authoring path; and
`shipd search` as the retrieval surface that lists PRDs. Every interactive
command in the guide SHALL invoke the `shipd` binary or name a `/s:` skill —
never an engine script path.

#### Scenario: Guide covers the discover phase
- **WHEN** `docs/prd.md` is inspected
- **THEN** it holds the hierarchy diagram, the workspace storage path and
  chain-resolution rule, the three-status lifecycle with staged approval,
  the three tiers' section lists with the standard default, the `/s:prd`
  walkthrough, and a `shipd search` example

#### Scenario: Commands stay binary-or-skill
- **WHEN** the guide's command invocations are scanned
- **THEN** none names a `spec_status.py` or `spec_emit.py` path

#### Scenario: Standalone nature is stated
- **WHEN** the guide's storage or FAQ prose is read
- **THEN** it states that a PRD needs no initiative and no epic, and that
  epics cite the PRD rather than the reverse
