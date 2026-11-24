## MODIFIED Requirements

### Requirement: Run starts on a checked account and joins once
id: room-run-start
base: d4998752aa46

`room.py run <pr> --role author|reviewer|ci [--skill S]... [--description D]
[--harness H] [--model M] [--max-turns N] [--budget S] [--turn-timeout S]
[--interval S] [--since CURSOR]` SHALL resolve the agent, the root, and the
room exactly as the other verbs do, and SHALL reject an unknown `--harness`
(checked with `session_driver.runner_for`) and a missing `--role` as usage
errors (exit `2`). Before posting anything it SHALL read the acting login (as
`room-login-normalise` defines: `gh api user`, then the GraphQL viewer) and
the PR author (`gh pr view --json author`). If the login cannot be read, then
it SHALL print one `Error:` line and exit `1`. If the role is `reviewer` or
`ci` and the author cannot be read, then it SHALL print one `Error:` line and
exit `1` having posted nothing. If the role is `reviewer` or `ci`, the author
names the same account as the login under `room.same_account`, and
`distinct_reviewer` resolves `true`, then it SHALL print `whoami`'s `Error:`
line and exit `1` having posted nothing. Where the role is `reviewer` or `ci`,
the two name the same account, and `distinct_reviewer` resolves `false`, it
SHALL warn once on stderr that the review posts as a comment, not an
approval, and continue. Where the role is `author` and the login and
the PR author do not name the same account, it SHALL warn on stderr and
continue. It SHALL then post or refresh its card once through `join`'s logic,
with the given role, harness, description, and skills — `review-finding`,
`question`, `status` when no `--skill` is given. It SHALL pass no `env`
override to any subprocess, so `GH_TOKEN` or `GH_CONFIG_DIR` in the process
environment reaches both the `gh` calls and the spawned session.

#### Scenario: A reviewer on the author's account is refused
- **WHEN** `run 7 --role reviewer` runs with login `Mikkel` on a PR authored by
  `mikkel` and `distinct_reviewer` resolves `true`
- **THEN** one `Error:` line is printed, the exit code is `1`, no comment is
  posted, and the turn runner is never called

#### Scenario: A reviewer on the author's account runs by default
- **WHEN** `run 7 --role reviewer` runs with login `Mikkel` on a PR authored by
  `mikkel` and no configuration declares `distinct_reviewer`
- **THEN** one warning line naming a comment review is written to stderr, the
  card is posted with role `reviewer`, and the run does not exit `1` at start

#### Scenario: A bot reviewer is refused on the bot's own pull request
- **WHEN** `run 7 --role reviewer` runs with login `shipd-factory[bot]` on a
  PR whose author gh names `app/shipd-factory` and `distinct_reviewer`
  resolves `true`
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

### Requirement: Repo mode answers each PR that asks for the agent
id: room-run-repo-poll
base: da2c5fb513dd

Each poll, repo mode SHALL list the open pull requests with `gh pr list --repo <R> --state open --json number,url,author,updatedAt --limit 100` and SHALL visit them in ascending number. It SHALL skip a PR whose author login is empty, and, where `distinct_reviewer` resolves `true`, a PR whose author login equals the acting login ignoring case; it SHALL warn once per skipped PR on stderr and SHALL never join, read, or post on it. Where `distinct_reviewer` resolves `false`, it SHALL treat a PR authored by the acting login like any other. It SHALL read `distinct_reviewer` once at start. It SHALL also skip a PR parked earlier in this process, and a PR whose `updatedAt` equals the value seen on its last visit when that visit surfaced no task. For every other PR it SHALL run `watch`'s own logic once, with `once` set and from that PR's cursor, capturing stdout. When task lines surface, it SHALL first post or refresh its card through `join`'s logic once per PR per process, with the run's role, harness, description, and skills. It SHALL then call the turn runner once with the prompt `/s:room <url> role <role>, skills <s1>, ...`, the run's root as working directory, and that PR's own stored session id as resume id (`None` the first time). After the turn it SHALL store the returned session id, advance the PR's cursor to the last surfaced line's `cursor`, and continue with the next PR. Only one turn SHALL run at a time. Between polls it SHALL sleep `--interval` seconds, and an idle poll SHALL call no turn runner.

#### Scenario: Two PRs each get their own session
- **WHEN** open PRs 7 and 9 each hold a task to `rev-b`, and the fake runner returns `s-7` for PR 7's turn and `s-9` for PR 9's
- **THEN** the runner is called once per PR with resume id `None`, each prompt names its own PR URL, and a later task on PR 7 resumes `s-7`

#### Scenario: A PR authored by the acting login is skipped
- **WHEN** `distinct_reviewer` resolves `true`, the acting login is `rev-b-login` and open PR 7, authored by `REV-B-LOGIN`, holds a task to `rev-b`
- **THEN** nothing is posted on PR 7, the runner is never called, and stderr names PR 7 once

#### Scenario: A PR authored by the acting login is answered by default
- **WHEN** no configuration declares `distinct_reviewer`, the acting login is `rev-b-login` and open PR 7, authored by `REV-B-LOGIN`, holds a task to `rev-b`
- **THEN** the runner is called once with a prompt naming PR 7's URL

#### Scenario: A PR without a task for the agent costs no turn
- **WHEN** the only open PR holds a task addressed to another agent
- **THEN** the runner is never called and no card is posted

#### Scenario: An unchanged PR is not re-read
- **WHEN** two polls see PR 7 with the same `updatedAt` and no task
- **THEN** PR 7's comments are read only once
