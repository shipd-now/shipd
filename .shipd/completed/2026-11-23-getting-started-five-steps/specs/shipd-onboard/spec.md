## ADDED Requirements

### Requirement: Guided tour user documentation
id: onboard-user-docs

The repository SHALL provide `docs/onboard.md`, titled "Guided tour", as the
main page for `/s:onboard`, conforming to the shipd documentation standard
with the marker `how-to` on its first line and a total line count within
that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying what
the tour is, then `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order. It SHALL cover: the nine-step tour over one
worked example; the sandbox at `~/.shipd/onboarding/sandbox/`, and that the
tour creates and changes no file in the reader's own repositories; the
`/s:onboard`, `/s:onboard next`, and `/s:onboard back` invocations; that the
tour never advances by itself; that progress saves to
`~/.shipd/onboarding/state.json` and a bare `/s:onboard` resumes there; and
that the last step offers to delete or keep `~/.shipd/onboarding/`.
`## Reference` SHALL hold a table with one row per step. The page SHALL link
`getting-started.md`, `plan.md`, `build.md`, and `cheatsheet.md`. Every
command on the page SHALL be a `/s:` skill; the page SHALL name no engine
script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/onboard.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the tour
- **WHEN** `docs/onboard.md` is inspected
- **THEN** it names the three invocations, the sandbox path, the state file,
  and the rule that the tour changes no file in the reader's repositories,
  and its step table holds nine rows

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/onboard.md`
- **THEN** it exits 0 with the page marked `how-to` at 150 lines or fewer,
  the file names no `spec_status.py`, `spec_lint.py`, or `spec_merge.py`
  path, and every relative link resolves
