## ADDED Requirements

### Requirement: Pull request user documentation
id: pr-user-docs

The repository SHALL provide `docs/pr.md`, titled "Pull requests", as the
main page for `/s:pr` and the `shipd gate rules` verb, conforming to the
shipd documentation standard with the marker `how-to` on its first line and
a total line count within that type's cap.

The page SHALL follow the main-page shape: opening paragraphs saying that
every change ships as one pull request from its `change/<slug>` branch and
that `/s:pr` writes its title and body, then `## When to use it`,
`## How to run it`, and a closing `## Reference`, in that order.

`## When to use it` SHALL state that `/s:build` and `/s:autopilot` open the
pull request themselves, and SHALL name the cases for running `/s:pr` by
hand (a branch with no pull request, and a title or body to rewrite) and for
`shipd gate rules`.

`## How to run it` SHALL hold three level-3 steps. `### Write the pull
request` SHALL cover: pushing the branch first; the `/s:pr` invocation; that
the skill reads the change on a `change/<slug>` branch and the commit log on
any other; the body's shape (the `## ☕ Pull Request` heading, a why-first
paragraph, a short list of what changed); that the body is linted against
the documentation standard; that the title comes from the `pr.title`
template with a ticket id found through `pr.ticket_pattern`; that the skill
creates the pull request or updates the existing one, leaving its draft
state; that it prints the full URL; and that it never pushes and never arms
auto-merge. `### Merge it` SHALL show `gh pr merge --auto --squash
--delete-branch` as the command that arms auto-merge, SHALL name the default
required checks `ci` and `semantic-review` and the conversation-resolution
rule, and SHALL state in one sentence that `pr-mode: draft` opens a draft a
person merges. `### Set the merge rules` SHALL cover: bare `shipd gate
rules` as a report that prints each member of the `merge` configuration
beside the live ruleset and changes nothing; `shipd gate rules apply` as
the write that creates or updates the one ruleset named `shipd merge rules`;
that applying needs admin permission; that `/s:gate` offers the apply step
in its consent round; and that `shipd doctor` reports drift on its
`merge-rules` line.

`## Reference` SHALL hold a table of the `/s:pr` flags (`--ticket <id>`,
`--draft`, `--base <ref>`), a table of the `shipd gate rules` forms (bare,
`apply`, `--repo`, `--root`), and links to `customise.md` for the `pr`,
`pr-mode`, and `merge` keys, to `semantic-review.md`, to `copilot-review.md`,
and to `agent-identity.md` for the second-account rule. The page SHALL NOT
restate the `merge` key's members or defaults beyond the two default
required checks.

Every command on the page SHALL invoke the `shipd` binary, `git`, or `gh`,
or name a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/pr.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the skill
- **WHEN** `### Write the pull request` is read
- **THEN** it names the `/s:pr` invocation, the `## ☕ Pull Request` heading,
  the why-first paragraph, the `pr.title` template, the create-or-update
  rule, the full URL, and that the skill never pushes or arms auto-merge

#### Scenario: Page covers merging
- **WHEN** `### Merge it` and `### Set the merge rules` are read
- **THEN** they show `gh pr merge --auto --squash --delete-branch`, name the
  `ci` and `semantic-review` checks, show bare `shipd gate rules` and
  `shipd gate rules apply`, name the `shipd merge rules` ruleset, and name
  the `merge-rules` doctor line

#### Scenario: Reference holds the flags and the links
- **WHEN** the page's `## Reference` section is read
- **THEN** it lists the three `/s:pr` flags and the `shipd gate rules`
  forms, and its links to `customise.md`, `semantic-review.md`,
  `copilot-review.md`, and `agent-identity.md` resolve

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/pr.md`
- **THEN** it exits 0 with the page marked `how-to` at 150 lines or fewer,
  and the page names no `spec_status.py`, `review_gate.py`, or
  `merge_rules.py` path
