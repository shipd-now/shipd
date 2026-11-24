## MODIFIED Requirements

### Requirement: Whoami reports the acting account and refuses the author
id: room-whoami-verb
base: 765e7d0f8738

`shipd room whoami <pr>` SHALL read the acting login as
`room-login-normalise` defines and the pull request author from
`gh pr view --json author`, and print one JSON object with `login`, `author`,
`source`, `is_author` and `may_approve`. The `source` SHALL name the
credential `gh` uses, never a token value, following gh's precedence for the
room's host — the host of a pull request URL, else `GH_HOST`, else
`github.com`. For `github.com` or a `ghe.com` subdomain the order SHALL be
`GH_TOKEN`, `GITHUB_TOKEN`, `GH_CONFIG_DIR`, then `gh-login`; for any other
host it SHALL be `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`,
`GH_CONFIG_DIR`, then `gh-login`. The `room run` start line SHALL name the same
source. If either the login or the author cannot be read, then the verb SHALL
print one `Error:` line and exit `1`. When the login and the author name
different accounts, it SHALL print `is_author` false and `may_approve` true.
When they name the same account under `room.same_account` and
`distinct_reviewer` resolves `false`, it SHALL exit `0` printing `is_author`
true and `may_approve` false. When they name the same account and
`distinct_reviewer` resolves `true`, it SHALL print one `Error:` line naming
the login, saying the `distinct_reviewer` setting requires a reviewer account
other than the author's, and exit `1`. Where `--author` is given, the verb
SHALL instead exit `0` printing `is_author` true and `may_approve` false when
the login and the author name the same account, and SHALL print one `Error:`
line saying only the author may fix its findings and exit `1` when they differ
or either cannot be read. It SHALL write nothing to GitHub.

#### Scenario: A second account may approve
- **WHEN** `whoami` runs with login `reviewer-b` on a PR authored by `mikkel`
- **THEN** stdout is JSON with `may_approve` true, `is_author` false, and the
  verb exits `0`

#### Scenario: The author is refused
- **WHEN** `whoami` runs with login `Mikkel` on a PR authored by `mikkel` and
  `distinct_reviewer` resolves `true`
- **THEN** one `Error:` line naming `distinct_reviewer` is printed and the
  verb exits `1`

#### Scenario: The author's own account is allowed by default
- **WHEN** `whoami` runs with login `Mikkel` on a PR authored by `mikkel` and
  no configuration declares `distinct_reviewer`
- **THEN** stdout is JSON with `is_author` true and `may_approve` false, and
  the verb exits `0`

#### Scenario: A bot reviewer is refused on its own pull request
- **WHEN** `whoami` runs with login `shipd-factory[bot]` on a PR whose author
  gh names `app/shipd-factory` and `distinct_reviewer` resolves `true`
- **THEN** one `Error:` line is printed and the verb exits `1`

#### Scenario: The author flag confirms a bot author
- **WHEN** `whoami --author` runs with `gh api user` failing, the GraphQL
  viewer naming `shipd-factory[bot]`, on a PR authored by `app/shipd-factory`
- **THEN** stdout is JSON with `is_author` true and `may_approve` false, and
  the verb exits `0`

#### Scenario: The author flag refuses another account
- **WHEN** `whoami --author` runs with login `reviewer-b` on a PR authored by
  `mikkel`
- **THEN** one `Error:` line is printed, stdout is empty and the verb exits `1`

#### Scenario: An unreadable login is refused
- **WHEN** `gh api user` and the GraphQL viewer both fail during `whoami`
- **THEN** the verb prints an `Error:` line and exits `1`

#### Scenario: The credential source is named without a secret
- **WHEN** `GH_TOKEN` is set in the environment
- **THEN** `source` is `GH_TOKEN` and the token value appears nowhere in the output

#### Scenario: GITHUB_TOKEN alone is reported
- **WHEN** only `GITHUB_TOKEN` is set and the room is on `github.com`
- **THEN** `source` is `GITHUB_TOKEN` for `whoami` and on the `room run` start
  line, and the token value appears nowhere in the output

#### Scenario: An enterprise host reports the enterprise token
- **WHEN** `whoami` runs on a pull request URL whose host is not `github.com`
  with `GH_TOKEN` and `GH_ENTERPRISE_TOKEN` set
- **THEN** `source` is `GH_ENTERPRISE_TOKEN`, and with only `GH_TOKEN` set it
  is `gh-login`

### Requirement: The room skill checks identity before approving
id: room-skill-identity-check
base: 4b9d3b41e7a7

The `/s:room` skill, its harness body and its reference SHALL require an agent
to run `shipd room whoami <pr>` before any approving or change-requesting
review and to stop, relaying the `Error:` line, when it exits non-zero. They
SHALL state that when `whoami` exits `0` with `may_approve` false, the review
still runs and posts as a comment with its status, never as an approval or a
change request. `room join` with role `reviewer` or `ci` SHALL warn on stderr
when the acting login equals the PR author and SHALL still join. Account
selection SHALL stay with `GH_TOKEN` or `GH_CONFIG_DIR`: the room gh runner
SHALL pass no `env` override.

#### Scenario: Join warns for a reviewer on the author's account
- **WHEN** `join --role reviewer` runs with login equal to the PR author
- **THEN** the card is posted and a warning line is written to stderr

#### Scenario: The skill carries the rule
- **WHEN** SKILL.md, the harness body and the reference are read
- **THEN** each names `shipd room whoami` before an approving review, and
  each names `may_approve` and says such a review posts as a comment

### Requirement: Second-account setup is documented and the version bumped
id: agent-identity-docs-version
base: e74f59945a34
Dropped: The page owns the refusal rule

`docs/agent-identity.md` SHALL be the one page that owns the second-account
setup: a lint-clean how-to of 150 lines or fewer, titled `# Give an agent its
own GitHub account`. It SHALL explain how to give an agent a second GitHub
account through `GH_TOKEN` or `GH_CONFIG_DIR`, how to verify it with
`whoami`, and that no token is stored in tracked files.

The page SHALL follow the main-page shape. Its opening SHALL state that a
second account is optional: GitHub does not count an author's approval of
their own pull request, so a reviewer on the author's account posts its
review as a comment, and a second account lets the review count as an
approval. Then come `## When to use it`, `## How to run it`, and a closing
`## Reference`, in that order, with no `## See also`.

`## When to use it` SHALL name the cases: when a review must count as a
GitHub approval, and when the repository sets `distinct_reviewer` to `true`.
It SHALL state that with `distinct_reviewer` `true`, a `shipd room run` with
role `reviewer` or `ci` on the author's own account exits `1` with one
`Error:` line and posts nothing, that without it the run continues with one
warning, and that an author run on any other account only gets a warning.

`## How to run it` SHALL hold these level-3 headings in this order:
`### Before you start`, `### 1. Set up the second account`,
`### 2. Start the reviewer session`, `### 3. Verify the account`,
`### Verify an author bot`, and `### Keep the token out of the repository`.
Each SHALL keep every fact its section holds today. `### Before you start`
SHALL state that a reviewer account that claims reviews needs push
permission, linking `room-review-claims.md`.

`## Reference` SHALL link `room-run.md`, `multi-agent-pr.md`,
`semantic-review.md` and `customise.md`.

`docs/room-run.md`, `docs/multi-agent-pr.md`, and `docs/semantic-review.md`
SHALL link to the page, and none of them SHALL say a reviewer needs its own
account. `docs/pr.md` SHALL state how one account works with the merge
rules: `merge.approvals` set to `0` with `semantic-review` kept in
`required_checks` makes the author's own posted review the gate, and removing
`semantic-review` from `required_checks` removes that gate. `plugin.json`
SHALL carry a version one patch above `main`'s.

#### Scenario: The doc lints clean and is linked
- **WHEN** `docs_lint.py` runs on `docs/agent-identity.md`
- **THEN** it exits `0`, the file has 150 lines or fewer, and `room-run.md`,
  `multi-agent-pr.md`, and `semantic-review.md` each link to the page

#### Scenario: The page follows the main-page shape
- **WHEN** the level-2 headings of `docs/agent-identity.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: The setup facts survive
- **WHEN** the page is read
- **THEN** it contains `GH_TOKEN`, `GH_CONFIG_DIR`, `shipd room whoami 412`,
  `shipd room whoami 412 --author`, `may_approve`, and the three rules that
  keep a token out of the repository

#### Scenario: A second account reads as optional
- **WHEN** `docs/agent-identity.md`, `docs/room-run.md` and
  `docs/multi-agent-pr.md` are read
- **THEN** `agent-identity.md` names `distinct_reviewer`, and none of the
  three says a reviewer needs its own account

#### Scenario: The single-account merge recipe is documented
- **WHEN** `docs/pr.md` is read
- **THEN** it names `merge.approvals` set to `0` together with the
  `semantic-review` required check as the single-account setup
