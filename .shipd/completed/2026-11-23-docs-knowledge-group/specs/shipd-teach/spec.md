## ADDED Requirements

### Requirement: Wiki user documentation
id: wiki-user-docs

The repository SHALL provide `docs/wiki.md`, titled "The wiki", as the main
page for the workspace wiki, `/s:teach`, and the `shipd wiki` verbs,
conforming to the shipd documentation standard with the marker `how-to` on
its first line and a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what the
wiki is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order.

The opening and `## When to use it` SHALL cover: the wiki as the store of
durable knowledge the oracle answers from, linking `docs/oracle.md`; the
workspace store and the repo-local fallback store a repo with no workspace
uses; when to run `/s:teach` (to distil decisions, to drain answered queue
entries, to correct a standing answer); and the teacher that runs after a
verified build, which distils that one change with no interview and at most
five pages.

`## How to run it` SHALL cover, for `/s:teach`: the invocation with its
optional topic argument; the scan of the spec surfaces (epic decisions,
verified capabilities, research reports, completed plans); pages that cite
their backing artifact and update an existing page before adding one; the
bound of 15 pages a run; the single interview round, opened only for gaps,
contradictions, and promotion offers; the deferred question that joins the
queue; the drain of answered queue entries, with an advisory answer keeping
its `Authority: advisory` line; and the one staged, lint-checked write that
restores the store on any finding. It SHALL cover `/s:teach <change> Q<n>` as
the way to correct one recorded consultation, and the promotion of
job-independent knowledge to a base store when one is present.

`## Reference` SHALL hold: a table of the store's files (`index.md`,
`queue.md`, `log.md`, `schema.md`, `wiki/`, `sources/`) with what each
holds; a table of the `shipd wiki`, `shipd wiki init`, and `shipd lint
--wiki` verbs; and links to `docs/memory.md` for personal preferences and
`docs/workspaces.md` for where a store lives.

Every interactive command on the page SHALL invoke the `shipd` binary or name
a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/wiki.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the teach sweep
- **WHEN** `docs/wiki.md` is inspected
- **THEN** it names the `/s:teach` invocation, the scanned surfaces, the
  15-page bound, the single interview round, the queue drain, the advisory
  marker, and the staged write

#### Scenario: Page covers correction and the teacher
- **WHEN** `docs/wiki.md` is inspected
- **THEN** it gives `/s:teach <change> Q<n>` as the correction path and
  states that a verified build's teacher distils one change with no
  interview

#### Scenario: Reference holds the store and the verbs
- **WHEN** the page's `## Reference` section is read
- **THEN** it lists the six store entries and the three `shipd` verbs, and
  links `oracle.md`, `memory.md`, and `workspaces.md` resolve

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/wiki.md`
- **THEN** it exits 0 with the page marked `how-to`, and the page names no
  `spec_status.py` or `spec_emit.py` path
