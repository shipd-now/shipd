## ADDED Requirements

### Requirement: Personal memory user documentation
id: memory-user-docs

The repository SHALL provide `docs/memory.md`, titled "Personal memory", as
the main page for `/s:remember`, `/s:memory`, and `/s:forget`, conforming to
the shipd documentation standard with the marker `how-to` on its first line
and a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what the
personal memory store is, then `## When to use it`, `## How to run it`, and a
closing `## Reference`, in that order.

The opening and `## When to use it` SHALL cover: the store as one personal
wiki at `<memory_dir>/wiki` (default `~/.shipd-memory/wiki`) holding
`memory-<subject>` pages; that the oracle reads it first, linking
`docs/oracle.md`; that it has no base store and no promotion; and the choice
between a personal preference, which belongs here, and workspace knowledge,
which belongs in the wiki, linking `docs/wiki.md`.

`## How to run it` SHALL cover, for `/s:remember`: the invocation with and
without a preference argument; the add, update, or skip classification
against existing pages; the typed confirmation before any write; the store
scaffolded on first use; and the git backing — the offered `git init` of the
memory directory, the private `shipd-memory` remote created through `gh`, and
the confirmed push, each offered and never automatic. For `/s:memory` it
SHALL cover the read-only listing. For `/s:forget` it SHALL cover the
free-text description, the choice among several matches, and the single
confirmation that defaults to keeping the page.

`## Reference` SHALL hold: the `memory-<subject>` page shape as a code block
(title, one-line statement, `Origin:` and `Captured:` lines); a table of the
three skills; `shipd wiki --personal` as the store report; and a link to
`docs/customise.md` for the `memory_dir` key.

Every interactive command on the page SHALL invoke the `shipd` binary, `git`,
`gh`, or name a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/memory.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the three skills
- **WHEN** `docs/memory.md` is inspected
- **THEN** it names `/s:remember` with its typed confirmation, `/s:memory` as
  read-only, and `/s:forget` with its confirmation that defaults to keeping
  the page

#### Scenario: Page covers the git backing
- **WHEN** the `/s:remember` prose is read
- **THEN** it names the offered `git init`, the private `shipd-memory`
  remote, and the confirmed push, and states that none runs without consent

#### Scenario: Reference holds the page shape
- **WHEN** the page's `## Reference` section is read
- **THEN** it shows a `memory-<subject>` page with its `Origin:` and
  `Captured:` lines, names `shipd wiki --personal`, and links `customise.md`

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/memory.md`
- **THEN** it exits 0 with the page marked `how-to`, and the page names no
  `spec_status.py` or `spec_emit.py` path
