## ADDED Requirements

### Requirement: Research user documentation
id: research-user-docs

The repository SHALL provide `docs/research.md` as the main page for
`/s:research`, conforming to the shipd documentation standard with the marker
`how-to` on its first line and a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what a
research report is, then `## When to use it`, `## How to run it`, and a
closing `## Reference`, in that order. It SHALL cover: the report as a cited,
standalone artifact installed under the content directory's `research/`
folder that an epic links; the `/s:research <question>` invocation; the
report's own worktree and pull request; the single clarification round asked
only for an underspecified question; the stop when the session has no web
search and fetch tools; the five stages (decompose, search, select, extract,
compose); the report's sections (summary, themed findings, gaps and caveats,
numbered sources) with inline `[n]` citations and the provenance note; and
`shipd list research` as the way to list installed reports.

Every interactive command on the page SHALL invoke the `shipd` binary or name
a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/research.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the skill
- **WHEN** `docs/research.md` is inspected
- **THEN** it names the `/s:research` invocation, the five stages, the
  clarification round, the missing-web-tools stop, the report sections with
  `[n]` citations, and `shipd list research`

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/research.md`
- **THEN** it exits 0 with the page marked `how-to`, and the page names no
  `spec_status.py` or `spec_emit.py` path
