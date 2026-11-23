## ADDED Requirements

### Requirement: Document skill user documentation
id: document-user-docs

The repository SHALL provide `docs/document.md`, titled "Write docs", as the
main page for `/s:document`. The page SHALL conform to the shipd
documentation standard with `<!-- doc-type: how-to -->` as its first line and
a total line count within the how-to cap.

The page SHALL follow the main-page shape: opening paragraphs saying what
the skill is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL state:

- that `/s:document` writes or revises documentation against the shipd
  documentation standard, and that it edits documentation only: it never
  commits, pushes, or opens a pull request;
- that the standard lives in one rules file inside the plugin, which the
  skill reads before it writes;
- the run as numbered steps: classify each doc as concept, how-to, or
  reference; write or rewrite it; run the docs lint; fix every error until
  the lint exits clean; self-review the judgement rules;
- that a rewrite keeps every fact, and that a doc over its cap gets split or
  cut, never re-typed to buy a larger cap;
- that a lint error blocks and a lint warning is advice;
- that CI lints every file under `docs/` except `docs/retros/`.

The `## Reference` section SHALL hold one table of the three doc types with
each type's job and line cap (concept 100, how-to 150, reference 250), and
SHALL state the diagram rule: at most one mermaid diagram per doc, only
where it carries structure prose cannot. The page SHALL carry no mermaid
fence. Every command on the page SHALL be a `shipd` verb or a `/s:` skill;
the page SHALL describe the docs lint as a step the skill runs and SHALL
name no engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/document.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Reference table carries the three caps
- **WHEN** the `## Reference` section is read
- **THEN** its table lists concept, how-to, and reference with the caps 100,
  150, and 250 lines

#### Scenario: Page states the skill's boundary
- **WHEN** `docs/document.md` is inspected
- **THEN** it states that the skill edits documentation only and never
  commits, pushes, or opens a pull request

#### Scenario: Page passes the lint and names no script path
- **WHEN** `docs_lint.py` runs over `docs/document.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  and the file holds no mermaid fence and no `docs_lint.py` path
