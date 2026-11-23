## MODIFIED Requirements

### Requirement: PRD user documentation
id: prd-user-docs
base: 22fc707e2c7f

The repository SHALL provide the discover-phase guide as two documents, each
conforming to the shipd documentation standard: a doc-type marker comment on
the first line and a total line count within that type's cap.

`docs/prd.md` SHALL be the main page (marker `concept`) and SHALL follow the
main-page shape. Its opening sections say what a PRD is: the PRD concept and
the Initiative → PRD → Epic → Change hierarchy with every link optional (a
mermaid diagram included) and references written upward; workspace storage at
the resolved `prds/<slug>/prd.md` path with workspace-chain resolution, the
no-workspace refusal, and the PRD's standalone nature. A `## When to use it`
section SHALL follow, then a `## How to run it` section covering the `/s:prd`
interview as the authoring path, then a closing `## Reference` section. That
section SHALL link `docs/prd-reference.md` and SHALL name the
`draft`/`approved`/`superseded` statuses and the three template tiers in one
sentence each. The page SHALL carry no `## See also` section.

`docs/prd-reference.md` SHALL be the nested reference (marker `reference`),
opening with a link back to the main page and covering: the header format
with its recognized keys (`Status:`, `Template:`, `Initiative:` as the only
optional key); the three-status vocabulary; the staged re-install approval
mechanics with `shipd lint --prd` as the validation check; the three template
tiers with their exact section lists, their additive nesting, the `standard`
default, and the floor-not-ceiling rule; `shipd search` as the retrieval
surface with an example; `shipd prd` as the inspection surface — the slugged
report with its `cited-by` epics and the bare roster — including composing
the report's path with `shipd render`; and the epic header's `PRD:` link with
its workspace-resolution lint rule.

Each fact SHALL have one owning page. The main page owns the hierarchy, the
storage rules, and the standalone nature; the reference owns the statuses,
the approval mechanics, the tier lists, and the command surfaces. The page
that does not own a fact SHALL state it in one sentence at most and link to
the owner.

Every interactive command in either guide SHALL invoke the `shipd` binary or
name a `/s:` skill — never an engine script path.

#### Scenario: Concept hub covers the discover phase
- **WHEN** `docs/prd.md` is inspected
- **THEN** it holds the hierarchy mermaid diagram, the workspace storage path
  and chain-resolution rule, the standalone nature, the `/s:prd` authoring
  path, and a resolving relative link to `docs/prd-reference.md`

#### Scenario: Main page follows the shape
- **WHEN** the level-2 headings of `docs/prd.md` are listed
- **THEN** `## When to use it`, `## How to run it`, and `## Reference` appear
  in that order, `## Reference` is the last heading, and no `## See also` or
  `## Lifecycle and tiers` heading remains

#### Scenario: Reference covers the formats and surfaces
- **WHEN** `docs/prd-reference.md` is inspected
- **THEN** it documents the header keys, the three statuses with staged
  re-install approval, the three tiers' exact section lists with the
  `standard` default, a `shipd search` example, `shipd prd <slug>` (the
  report with citing epics) and bare `shipd prd` (the roster), and names
  `shipd render` composition

#### Scenario: Each fact has one owner
- **WHEN** both guides are read side by side
- **THEN** `docs/prd.md` gives the statuses and the tiers one sentence each,
  and `docs/prd-reference.md` gives the one-way direction of the `PRD:` link
  one sentence with a link to `docs/prd.md`

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
