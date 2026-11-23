## MODIFIED Requirements

### Requirement: Second-account setup is documented and the version bumped
id: agent-identity-docs-version
base: ee81084670ab

`docs/agent-identity.md` SHALL be the one page that owns the second-account
rule: a lint-clean how-to of 150 lines or fewer, titled `# Give an agent its
own GitHub account`. It SHALL explain how to give an agent a second GitHub
account through `GH_TOKEN` or `GH_CONFIG_DIR`, how to verify it with
`whoami`, and that no token is stored in tracked files.

The page SHALL follow the main-page shape. Its opening SHALL state the rule:
GitHub does not count an author's approval of their own pull request, and an
agent that shares the author's `gh` login is the same account. Then come
`## When to use it`, `## How to run it`, and a closing `## Reference`, in that
order, with no `## See also`.

`## When to use it` SHALL name the cases: before a reviewer agent approves,
and before a `shipd room run` with role `reviewer` or `ci`. It SHALL state
that such a run on the author's own account exits `1` with one `Error:` line
and posts nothing, and that an author run on any other account only gets a
warning.

`## How to run it` SHALL hold these level-3 headings in this order:
`### Before you start`, `### 1. Set up the second account`,
`### 2. Start the reviewer session`, `### 3. Verify the account`,
`### Verify an author bot`, and `### Keep the token out of the repository`.
Each SHALL keep every fact its section holds today. `### Before you start`
SHALL state that a reviewer account that claims reviews needs push
permission, linking `room-review-claims.md`.

`## Reference` SHALL link `room-run.md`, `multi-agent-pr.md`, and
`semantic-review.md`.

`docs/room-run.md`, `docs/multi-agent-pr.md`, and `docs/semantic-review.md`
SHALL link to the page, and no other page under `docs/` SHALL state the
account refusal rule. `plugin.json` SHALL carry a version one patch above
`main`'s.

#### Scenario: The doc lints clean and is linked
- **WHEN** `docs_lint.py` runs on `docs/agent-identity.md`
- **THEN** it exits `0`, the file has 150 lines or fewer, and `room-run.md`,
  `multi-agent-pr.md`, and `semantic-review.md` each link to the page

#### Scenario: The page follows the main-page shape
- **WHEN** the level-2 headings of `docs/agent-identity.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: The page owns the refusal rule
- **WHEN** `docs/` outside `docs/retros/` is searched for the sentence that a
  reviewer or `ci` run on the author's own account exits `1`
- **THEN** only `docs/agent-identity.md` states it

#### Scenario: The setup facts survive
- **WHEN** the page is read
- **THEN** it contains `GH_TOKEN`, `GH_CONFIG_DIR`, `shipd room whoami 412`,
  `shipd room whoami 412 --author`, `may_approve`, and the three rules that
  keep a token out of the repository
