## ADDED Requirements

### Requirement: PRD show verb
id: prd-show-verb

The status CLI SHALL provide `prd-show [slug]`. With a slug it SHALL print
the PRD's report: the slug and status, the `Template:` tier, the
`Initiative:` link when the header carries one, the resolved path (relative
to the invocation root when inside it, absolute otherwise, the nearest
workspace-chain member winning), and one `cited-by:` line per epic in the
invocation root's universe (the root and its worktrees, deduped root-first)
whose header carries `PRD: <slug>` — with an explicit `cited-by: none` line
when no epic cites it. An unknown slug SHALL exit non-zero naming the
expected `prd.md` path, and no discoverable workspace SHALL exit non-zero
with the no-workspace error. Bare `prd-show` SHALL list every PRD across the
workspace chain — one `<slug>: <status> (<tier>)` line per slug, the nearest
chain member winning, sorted by slug — reporting an empty store rather than
erroring when the chain holds none. Both forms SHALL accept `--json`
emitting the same facts as one JSON document. The verb is read-only.

#### Scenario: Report prints the PRD's facts and citing epics
- **WHEN** `prd-show mobile-push` runs where a chain member hosts the PRD
  and a universe epic carries `PRD: mobile-push`
- **THEN** the report holds the status, `Template:` tier, resolved path,
  and a `cited-by:` line naming that epic and its status

#### Scenario: Uncited PRD says so
- **WHEN** `prd-show mobile-push` runs and no epic carries `PRD: mobile-push`
- **THEN** the report holds `cited-by: none`

#### Scenario: Unknown slug is an error
- **WHEN** `prd-show no-such-prd` runs in a workspace with no such PRD
- **THEN** the CLI exits non-zero naming the expected `prd.md` path

#### Scenario: Bare form lists the roster with chain shadowing
- **WHEN** `prd-show` runs where an inner chain member shadows an outer
  member's copy of the same slug
- **THEN** one line prints per slug, the shadowed slug showing the inner
  copy's status and tier

#### Scenario: Empty store lists nothing without erroring
- **WHEN** `prd-show` runs in a workspace whose chain holds no PRDs
- **THEN** the CLI reports the empty store and exits zero

#### Scenario: JSON mode carries both forms
- **WHEN** `prd-show mobile-push --json` and `prd-show --json` run
- **THEN** the first emits one object with `slug`, `status`, `template`,
  `initiative`, `path`, and `cited_by`, and the second emits one array of
  `{slug, status, template}` objects

## MODIFIED Requirements

### Requirement: PRD user documentation
id: prd-user-docs
base: 98763c90ac28

The repository SHALL provide `docs/prd.md`, a user-facing guide to the
discover phase that covers: the PRD concept and the
Initiative → PRD → Epic → Change hierarchy with every link optional (a
diagram included); workspace storage at the resolved
`prds/<slug>/prd.md` path with workspace-chain resolution and the PRD's
standalone nature; the `draft`/`approved`/`superseded` lifecycle with
approval as a staged re-install, never a hand edit of the store; the three
template tiers with their exact section lists, their additive nesting, and
`standard` as the default; the `/s:prd` interview as the authoring path;
`shipd search` as the retrieval surface that lists PRDs by content; and
`shipd prd` as the inspection surface — the slugged report with its citing
epics and the bare roster — including composing the report's path with
`shipd render` for a full-screen view. Every interactive
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

#### Scenario: Guide covers the inspection verb
- **WHEN** `docs/prd.md` is inspected
- **THEN** it documents `shipd prd <slug>` (the report with citing epics)
  and bare `shipd prd` (the roster), and names `shipd render` composition

