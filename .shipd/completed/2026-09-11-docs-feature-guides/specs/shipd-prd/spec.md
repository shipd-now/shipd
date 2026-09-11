## MODIFIED Requirements

### Requirement: PRD user documentation
id: prd-user-docs
base: 7263c7ca98c8

The repository SHALL provide the discover-phase guide as two documents, each
conforming to the shipd documentation standard: a doc-type marker comment on
the first line and a total line count within that type's cap.

`docs/prd.md` SHALL be the concept hub (marker `concept`), covering: the PRD
concept and the Initiative → PRD → Epic → Change hierarchy with every link
optional (a mermaid diagram included) and references written upward;
workspace storage at the resolved `prds/<slug>/prd.md` path with
workspace-chain resolution, the no-workspace refusal, and the PRD's
standalone nature; an overview of the `draft`/`approved`/`superseded`
lifecycle with approval as a staged re-install, never a hand edit of the
store; an overview of the three template tiers with `standard` as the
default; the `/s:prd` interview as the authoring path; and a relative link
to `docs/prd-reference.md`.

`docs/prd-reference.md` SHALL be the reference (marker `reference`), opening
with a link back to the hub and covering: the header format with its
recognized keys (`Status:`, `Template:`, `Initiative:` as the only optional
key); the three-status vocabulary; the staged re-install approval mechanics
with `shipd lint --prd` as the validation check; the three template tiers
with their exact section lists, their additive nesting, and the
floor-not-ceiling rule; `shipd search` as the retrieval surface with an
example; `shipd prd` as the inspection surface — the slugged report with its
`cited-by` epics and the bare roster — including composing the report's path
with `shipd render`; and the epic header's `PRD:` link with its
workspace-resolution lint rule.

Every interactive command in either guide SHALL invoke the `shipd` binary or
name a `/s:` skill — never an engine script path.

#### Scenario: Concept hub covers the discover phase
- **WHEN** `docs/prd.md` is inspected
- **THEN** it holds the hierarchy mermaid diagram, the workspace storage path
  and chain-resolution rule, the standalone nature, the lifecycle and tier
  overviews, the `/s:prd` authoring path, and a resolving relative link to
  `docs/prd-reference.md`

#### Scenario: Reference covers the formats and surfaces
- **WHEN** `docs/prd-reference.md` is inspected
- **THEN** it documents the header keys, the three statuses with staged
  re-install approval, the three tiers' exact section lists with the
  `standard` default, a `shipd search` example, `shipd prd <slug>` (the
  report with citing epics) and bare `shipd prd` (the roster), and names
  `shipd render` composition

#### Scenario: Commands stay binary-or-skill
- **WHEN** both guides' command invocations are scanned
- **THEN** none names a `spec_status.py` or `spec_emit.py` path

#### Scenario: Standalone nature is stated
- **WHEN** the hub's storage prose is read
- **THEN** it states that a PRD needs no initiative and no epic, and that
  epics cite the PRD rather than the reverse

#### Scenario: Both guides carry their markers and fit their caps
- **WHEN** `docs_lint.py` runs over `docs/prd.md` and `docs/prd-reference.md`
- **THEN** it exits 0, with `docs/prd.md` marked `concept` and
  `docs/prd-reference.md` marked `reference`
