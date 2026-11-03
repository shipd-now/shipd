## MODIFIED Requirements

### Requirement: Run starts on a checked account and joins once
id: room-run-start
base: 2ad4ae6cb1ab

`room.py run <pr> --role author|reviewer|ci [--skill S]... [--description D]
[--harness H] [--model M] [--max-turns N] [--budget S] [--turn-timeout S]
[--interval S] [--since CURSOR]` SHALL resolve the agent, the root, and the
room exactly as the other verbs do, and SHALL reject an unknown `--harness`
(checked with `session_driver.runner_for`) and a missing `--role` as usage
errors (exit `2`). Before posting anything it SHALL read the acting login (as
`room-login-normalise` defines: `gh api user`, then the GraphQL viewer) and
the PR author (`gh pr view --json author`). If the login cannot be read, then
it SHALL print one `Error:` line and exit `1`. If the role is `reviewer` or
`ci` and the author cannot be read or names the same account as the login
under `room.same_account`, then it SHALL print `whoami`'s `Error:` line and
exit `1` having posted nothing. Where the role is `author` and the login and
the PR author do not name the same account, it SHALL warn on stderr and
continue. It SHALL then post or refresh its card once through `join`'s logic,
with the given role, harness, description, and skills — `review-finding`,
`question`, `status` when no `--skill` is given. It SHALL pass no `env`
override to any subprocess, so `GH_TOKEN` or `GH_CONFIG_DIR` in the process
environment reaches both the `gh` calls and the spawned session.

#### Scenario: A reviewer on the author's account is refused
- **WHEN** `run 7 --role reviewer` runs with login `Mikkel` on a PR authored by
  `mikkel`
- **THEN** one `Error:` line is printed, the exit code is `1`, no comment is
  posted, and the turn runner is never called

#### Scenario: A bot reviewer is refused on the bot's own pull request
- **WHEN** `run 7 --role reviewer` runs with login `shipd-factory[bot]` on a
  PR whose author gh names `app/shipd-factory`
- **THEN** one `Error:` line is printed, the exit code is `1`, and no comment
  is posted

#### Scenario: A bot author on its own pull request is not warned
- **WHEN** `run 7 --role author` runs with `gh api user` failing, the GraphQL
  viewer naming `shipd-factory[bot]`, on a PR authored by `app/shipd-factory`
- **THEN** no `but ... was authored by` warning is written

#### Scenario: The card is joined once with the run's role and skills
- **WHEN** `run 7 --role reviewer --agent rev-b` runs on a PR authored by
  `mikkel` with login `reviewer-b` and the PR is already merged
- **THEN** exactly one card is posted, carrying role `reviewer`, and skills
  `review-finding`, `question`, `status`

#### Scenario: An unknown harness is a usage error
- **WHEN** `run 7 --role author --harness nope` runs
- **THEN** the exit code is `2` and nothing is read from or posted to GitHub
