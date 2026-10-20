# room-acting-account

### Requirement: Whoami reports the acting account and refuses the author
id: room-whoami-verb

`shipd room whoami <pr>` SHALL read the acting login from `gh api user` and the
pull request author from `gh pr view --json author`, and print one JSON object
with `login`, `author`, `source` and `may_approve`. The `source` SHALL name the
credential `gh` uses, never a token value, following gh's precedence for the
room's host — the host of a pull request URL, else `GH_HOST`, else
`github.com`. For `github.com` or a `ghe.com` subdomain the order SHALL be
`GH_TOKEN`, `GITHUB_TOKEN`, `GH_CONFIG_DIR`, then `gh-login`; for any other
host it SHALL be `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`,
`GH_CONFIG_DIR`, then `gh-login`. The `room run` start line SHALL name the same
source. If the login equals the author case-insensitively, or either cannot be
read, then the verb SHALL print one `Error:` line naming the login and saying
an author cannot approve their own pull request, and exit `1`. It SHALL write
nothing to GitHub.

#### Scenario: A second account may approve
- **WHEN** `whoami` runs with login `reviewer-b` on a PR authored by `mikkel`
- **THEN** stdout is JSON with `may_approve` true and the verb exits `0`

#### Scenario: The author is refused
- **WHEN** `whoami` runs with login `Mikkel` on a PR authored by `mikkel`
- **THEN** one `Error:` line is printed and the verb exits `1`

#### Scenario: An unreadable login is refused
- **WHEN** `gh api user` fails during `whoami`
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

The `/s:room` skill, its harness body and its reference SHALL require an agent
to run `shipd room whoami <pr>` before any approving or change-requesting
review and to stop, relaying the `Error:` line, when it exits non-zero. `room
join` with role `reviewer` or `ci` SHALL warn on stderr when the acting login
equals the PR author and SHALL still join. Account selection SHALL stay with
`GH_TOKEN` or `GH_CONFIG_DIR`: the room gh runner SHALL pass no `env` override.

#### Scenario: Join warns for a reviewer on the author's account
- **WHEN** `join --role reviewer` runs with login equal to the PR author
- **THEN** the card is posted and a warning line is written to stderr

#### Scenario: The skill carries the rule
- **WHEN** SKILL.md, the harness body and the reference are read
- **THEN** each names `shipd room whoami` before an approving review

### Requirement: Second-account setup is documented and the version bumped
id: agent-identity-docs-version

`docs/agent-identity.md` SHALL explain, as a lint-clean how-to, how to give an
agent a second GitHub account through `GH_TOKEN` or `GH_CONFIG_DIR`, how to
verify it with `whoami`, and that no token is stored in tracked files. The
three related docs SHALL link to it, and `plugin.json` SHALL carry a version
one patch above `main`'s.

#### Scenario: The doc lints clean and is linked
- **WHEN** `docs_lint.py` runs on `docs/agent-identity.md`
- **THEN** it exits `0`, and `pr-room.md` links to the page
