## ADDED Requirements

### Requirement: Rubber duck user documentation
id: duck-user-docs

The repository SHALL provide `docs/duck.md`, titled "Rubber duck", as the
main page for `/s:duck`, conforming to the shipd documentation standard with
the marker `how-to` on its first line and a total line count within that
type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what the
rubber duck is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL cover: the duck as an adversarial,
strictly read-only critic that changes nothing and invokes no other skill;
the `/s:duck <idea>` invocation; what each reply carries (a critique grounded
in the repository and the spec surfaces, each point labelled blocking,
non-blocking, or suggestion, and one closing question); the declined
implementation request with its pointer; the wrap-up debrief; and, in
`## Reference`, the exit map as a table naming the command for each outcome
(`/s:research`, `/s:epic`, `/s:plan`, `/s:fix`, `/s:ask`), which the duck
names and never runs.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/duck.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the skill
- **WHEN** `docs/duck.md` is inspected
- **THEN** it states the read-only rule, names the three point labels and
  the one closing question, and holds an exit-map table with the five
  commands

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/duck.md`
- **THEN** it exits 0 with the page marked `how-to`
