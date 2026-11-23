## ADDED Requirements

### Requirement: Build user documentation
id: build-user-docs

The repository SHALL provide `docs/build.md`, a how-to page titled "Build a
change" that is the main page for `/s:build` and the `shipd board` verb. The
page SHALL follow the main-page shape: the opening under the title saying what the feature is, then the exact
level-2 headings `## When to use it`, `## How to run it`, and `## Reference`,
in that order. It SHALL explain that the
orchestrator runs on the session's model and delegates implementation to
execution sub-agents one model tier below. It SHALL walk the run in numbered
steps: the context gate, task execution, verification by the validator, merge
and archive, and shipping as a pull request. It SHALL name both PR modes,
`auto` as the default and `pr-mode: draft`, and SHALL show `shipd board` as
the way to watch progress. It SHALL carry exactly one `mermaid` fence showing
the branched build lifecycle. It SHALL link to `supersession-gate.md`,
`guardrails.md`, and `worktrees.md`, and every relative link in it SHALL
resolve. The page SHALL conform to the shipd documentation standard:
`<!-- doc-type: how-to -->` as its first line and a total line count within
the how-to cap.

#### Scenario: Page follows the main-page shape
- **WHEN** `docs/build.md` is inspected
- **THEN** its level-2 headings are exactly `## When to use it`,
  `## How to run it`, and `## Reference`, in that order, and the run steps
  are a numbered list

#### Scenario: Page covers the build's stages and PR modes
- **WHEN** `docs/build.md` is inspected
- **THEN** it names the model-down delegation, the validator, merge and
  archive, the `auto` and `draft` PR modes, and the `shipd board` verb

#### Scenario: Page carries one lifecycle diagram
- **WHEN** the fences in `docs/build.md` are counted
- **THEN** exactly one is a `mermaid` fence, and it shows the superseded stop
  and the two PR modes as branches

#### Scenario: Page links its group and the links resolve
- **WHEN** the relative links in `docs/build.md` are checked
- **THEN** it links `supersession-gate.md`, `guardrails.md`, and
  `worktrees.md`, and every link target exists

#### Scenario: Page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/build.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer
