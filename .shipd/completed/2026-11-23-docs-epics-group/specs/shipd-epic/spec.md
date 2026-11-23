## ADDED Requirements

### Requirement: Epics user documentation
id: epics-user-docs

The repository SHALL provide `docs/epics.md`, the main page for `/s:epic` and
`/s:explain`, titled "Epics". The page SHALL conform to the shipd
documentation standard with `<!-- doc-type: how-to -->` as its first line,
and SHALL open by saying what an epic is, then hold exactly three level-2
sections in this order: `## When to use it`, `## How to run it`, and
`## Reference`.

The page SHALL state:

- that an epic decomposes a feature too large for one change into member
  changes over shared decisions, stored at `.shipd/epics/<slug>/epic.md`;
- the four required sections of the artifact (Introduction with its
  Non-goals, Decisions, Design, Changes) and the stub table's rating columns
  (Code, Integration, Unknowns, Risk, each `low`, `medium`, or `high`) with
  the optional `After` column;
- the four epic statuses `draft`, `ready`, `active`, and `complete`;
- the `/s:epic` run as numbered steps: it works in the `epic-<slug>`
  worktree, investigates before it asks, asks one batched round, emits and
  lints the epic, promotes it to `ready` on approval, and ships it as a pull
  request;
- that `/s:epic` never plans a member, and that members are planned with
  `/s:plan <member>` or `/s:epic-grill <epic>`;
- amend mode, `/s:epic <slug> amend`: it changes the Decisions and the
  reference shelves only, it refuses a `draft` epic, and it ships from an
  `epic-amend-<slug>` worktree;
- that `/s:explain <epic>` prints a read-only explanation of an epic and its
  delivery state.

The `## Reference` section SHALL hold one table listing `/s:epic`,
`/s:epic <slug> amend`, `/s:explain <epic>`, `shipd epic <slug>`,
`shipd list epics`, `shipd lint --epic <slug>`, and
`shipd board --epic <slug>`, each with one line on what it does. The page
SHALL link `epic-grill.md`, `autopilot.md`, `drift.md`, `initiatives.md`, and
`prd.md` as the owner of the hierarchy diagram, and SHALL carry no mermaid
fence. Every command on the page SHALL be a `/s:` skill or a `shipd` verb.

#### Scenario: Page covers the artifact and the run
- **WHEN** `docs/epics.md` is inspected
- **THEN** it names the four artifact sections, the four statuses, the rating
  columns with `After`, and numbered run steps ending at a pull request

#### Scenario: Page covers amend and explain
- **WHEN** `docs/epics.md` is inspected
- **THEN** it states that amend mode changes only the Decisions and the
  reference shelves and refuses a `draft` epic, and that `/s:explain` is
  read-only

#### Scenario: Reference table lists the surfaces
- **WHEN** the `## Reference` section is read
- **THEN** its table holds the three skill invocations and the four `shipd`
  verbs, and no line on the page names a `spec_status.py`, `spec_emit.py`, or
  `spec_lint.py` path

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/epics.md`
- **THEN** it exits 0 with the file marked `how-to`, the file holds no
  mermaid fence, and every relative link resolves to an existing file
