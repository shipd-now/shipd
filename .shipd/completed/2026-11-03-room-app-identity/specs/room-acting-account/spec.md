## ADDED Requirements

### Requirement: The acting login falls back to GraphQL and compares as one account
id: room-login-normalise

The room SHALL read the acting login from `gh api user` first. If that call
exits non-zero or names no login, then the room SHALL read it from
`gh api graphql -f query={viewer{login}}` (`data.viewer.login`), and only when
both reads fail SHALL it warn on stderr as before and use `""`. The read SHALL
happen at most once per source per verb. The room SHALL compare a login with a
pull request or review author through one helper, `room.login_key`, which
lowercases the login and maps `app/<slug>` to `<slug>[bot]`; two logins SHALL
name the same account (`room.same_account`) only when both keys are non-empty
and equal. `join`'s reviewer/ci warning, `whoami`, `room run`'s start check,
the CI-review author match and repo mode's skip of the acting login's own pull
requests SHALL all use that helper. Two ordinary user logins SHALL compare
exactly as before, ignoring case.

#### Scenario: An installation token reads its login through GraphQL
- **WHEN** `gh api user` exits non-zero and the GraphQL viewer names
  `shipd-factory[bot]`
- **THEN** the acting login is `shipd-factory[bot]` and no login warning is
  written

#### Scenario: Both reads failing still warns
- **WHEN** `gh api user` and the GraphQL viewer read both fail during `close`
- **THEN** the warning line is written and the message posts without a
  `(for @login)` segment

#### Scenario: The app form and the bot form are one account
- **WHEN** `same_account` compares `app/shipd-factory` with
  `Shipd-Factory[bot]`, and `shipd-factory[bot]` with `app/shipd-factory`
- **THEN** both comparisons are true, and `shipd-factory` against
  `app/shipd-factory` is false

#### Scenario: Repo mode skips the bot's own pull request
- **WHEN** repo mode runs with login `shipd-factory[bot]` and an open PR whose
  `gh pr list` author is `app/shipd-factory`
- **THEN** that PR is skipped with the `authored by the acting` warning and
  never joined

#### Scenario: A reviewer card on a bot's own pull request warns
- **WHEN** `join --role reviewer` runs with login `shipd-factory[bot]` on a PR
  authored by `app/shipd-factory`
- **THEN** the card is posted and the `who authored this pull request`
  warning is written

#### Scenario: A user token is read as before
- **WHEN** `gh api user` names `mikkel`
- **THEN** no GraphQL viewer read is made

## MODIFIED Requirements

### Requirement: Whoami reports the acting account and refuses the author
id: room-whoami-verb
base: dceec222f7db

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
source. If the login and the author name the same account under
`room.same_account`, or either cannot be read, then the verb SHALL print one
`Error:` line naming the login and saying an author cannot approve their own
pull request, and exit `1`; otherwise it SHALL print `is_author` false and
`may_approve` true. Where `--author` is given, the verb SHALL instead exit `0`
printing `is_author` true and `may_approve` false when the login and the
author name the same account, and SHALL print one `Error:` line saying only
the author may fix its findings and exit `1` when they differ or either cannot
be read. It SHALL write nothing to GitHub.

#### Scenario: A second account may approve
- **WHEN** `whoami` runs with login `reviewer-b` on a PR authored by `mikkel`
- **THEN** stdout is JSON with `may_approve` true, `is_author` false, and the
  verb exits `0`

#### Scenario: The author is refused
- **WHEN** `whoami` runs with login `Mikkel` on a PR authored by `mikkel`
- **THEN** one `Error:` line is printed and the verb exits `1`

#### Scenario: A bot reviewer is refused on its own pull request
- **WHEN** `whoami` runs with login `shipd-factory[bot]` on a PR whose author
  gh names `app/shipd-factory`
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
