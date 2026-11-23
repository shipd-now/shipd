## ADDED Requirements

### Requirement: Fix user documentation
id: fix-user-docs

The repository SHALL provide `docs/fix.md`, a how-to page titled "Fix a bug"
that is the main page for `/s:fix`. The page SHALL follow the main-page
shape: the opening under the title saying what the feature is, then the exact
level-2 headings `## When to use it`, `## How to run it`, and `## Reference`,
in that order. It SHALL explain that the skill retrieves the related
spec artifacts with the engine's `related` verb before it reads code, and
that it reproduces the problem before it changes anything. It SHALL state the
two outcomes: where the code is wrong, the skill fixes the code and adds a
regression test; where the documented behaviour is wrong, the skill changes
nothing and hands off to `/s:plan`. It SHALL state that the skill never edits
a spec artifact and never commits, pushes, or opens a pull request. It SHALL
list the parts of the closing report. The page SHALL carry no diagram, and
every relative link in it SHALL resolve. The page SHALL conform to the shipd
documentation standard: `<!-- doc-type: how-to -->` as its first line and a
total line count within the how-to cap.

#### Scenario: Page follows the main-page shape
- **WHEN** `docs/fix.md` is inspected
- **THEN** its level-2 headings are exactly `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: Page states both outcomes and the boundaries
- **WHEN** `docs/fix.md` is inspected
- **THEN** it names the `related` verb, the reproduce-first step, the
  code-wrong and spec-wrong outcomes with the `/s:plan` hand-off, and states
  that the skill never edits a spec and never ships

#### Scenario: Page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/fix.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer,
  and the file holds no `mermaid` fence
