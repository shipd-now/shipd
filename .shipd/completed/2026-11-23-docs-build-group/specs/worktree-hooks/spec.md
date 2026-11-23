## ADDED Requirements

### Requirement: Worktree user documentation
id: worktree-user-docs

The repository SHALL provide `docs/worktrees.md`, a how-to page titled
"Worktrees and hooks" that is the main page for the `shipd worktree` verb
family and `/s:worktree-hooks`. The page SHALL follow the main-page shape:
the opening under the title saying what the feature is, then the exact
level-2 headings `## When to use it`, `## How to run it`, and `## Reference`,
in that order. It SHALL state that one change lives in one worktree at
`.worktrees/<change>` on branch `change/<change>`. It SHALL show how to
create a worktree, with `--fresh`, and how to register a setup script through
`shipd worktree hooks add` or `/s:worktree-hooks`. It SHALL state that a
failing hook exits `3` and leaves the worktree in place, resumable with
`shipd worktree hooks run`. Its Reference section SHALL hold a table of the
verbs `remove`, `prune-branches`, `sweep`, and `hooks list`, `add`, `remove`,
`run`, and `trust`. Where the page names a worktree config key, it SHALL give
one sentence and link `customise.md`. The page SHALL carry no diagram, and
every relative link in it SHALL resolve. The page SHALL conform to the shipd
documentation standard: `<!-- doc-type: how-to -->` as its first line and a
total line count within the how-to cap.

#### Scenario: Page follows the main-page shape
- **WHEN** `docs/worktrees.md` is inspected
- **THEN** its level-2 headings are exactly `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: Page covers the verb family
- **WHEN** the Reference section of `docs/worktrees.md` is inspected
- **THEN** its table lists `remove`, `prune-branches`, `sweep`, and the five
  `hooks` verbs, each matching the `shipd worktree --help` usage

#### Scenario: Page covers hooks and their failure
- **WHEN** `docs/worktrees.md` is inspected
- **THEN** it names `/s:worktree-hooks`, `shipd worktree hooks add`, the
  exit code `3`, and `shipd worktree hooks run` as the resume path

#### Scenario: Page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/worktrees.md`
- **THEN** it exits 0 with the file marked `how-to` at 150 lines or fewer
