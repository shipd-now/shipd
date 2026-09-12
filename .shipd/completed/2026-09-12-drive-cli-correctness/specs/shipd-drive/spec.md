## MODIFIED Requirements

### Requirement: Cached login reuse
id: drive-auth-cache
base: cf0c1ca7e2e7

The `login` verb SHALL write the browser's storage state to
`~/.shipd/drive/auth/<target>.json`. While that file exists and its
modification time is within the resolved `authCacheTtlHours` (default 8), the
CLI SHALL reuse it and perform no login; otherwise it SHALL log in again and
overwrite it. Where the resolved target declares an `auth` recipe of kind
`none`, the CLI SHALL perform no login at all: it SHALL NOT invoke the login
worker, SHALL NOT require any credential, SHALL write no cache file, and SHALL
exit zero. Where a login fails, the CLI SHALL report the failure with the path
of a debug screenshot and exit non-zero, leaving any previous cache untouched.

#### Scenario: A fresh cache skips the login
- **WHEN** a session starts for a target whose auth file was written inside
  the TTL
- **THEN** no login worker runs and the cached state is loaded

#### Scenario: An expired cache logs in again
- **WHEN** the auth file's modification time is older than the TTL
- **THEN** the login worker runs and the auth file is rewritten

#### Scenario: A no-auth target needs no credentials
- **WHEN** `login` names a target whose `auth` kind is `none`, with neither
  `DRIVE_LOGIN_USERNAME` nor `DRIVE_LOGIN_PASSWORD` set and no cache file
  present
- **THEN** no login worker runs, no cache file is written, and the exit code is
  zero

### Requirement: Session daemon and driving verbs
id: drive-session
base: e1c4416abecb

The CLI SHALL expose `session start`, `session status`, and `session stop`,
where `session start` launches a background worker owning one browser and one
page and listening on a Unix socket under `~/.shipd/drive/`, loading the
target's cached storage state. The driving verbs — navigating, snapshotting
the accessibility tree, clicking, typing, pressing, waiting, evaluating, and
screenshotting — SHALL each send one JSON request to that socket and print the
JSON reply. If a reply carries a falsey `ok` field, then the verb SHALL still
print that reply to stdout unchanged and SHALL exit non-zero, so a caller
reading only the exit status never mistakes a failed verb for a successful one.
The daemon SHALL attach console and response listeners once at
startup and accumulate every event for the life of the session, so the
`console` and `network` verbs report events emitted before the verb ran.
Starting a session for a different target SHALL replace the running one.
Fatal errors SHALL be reported as a single `Error: <reason>` line on stderr
with a non-zero exit, and an unknown or missing verb SHALL print usage on
stderr and exit 2.

#### Scenario: Console events survive a navigation
- **WHEN** a page logs an error, the session then navigates elsewhere, and the
  `console` verb runs
- **THEN** the reply still carries the error logged before the navigation

#### Scenario: Switching target replaces the session
- **WHEN** `session start` names a target other than the running session's
- **THEN** the running daemon is stopped and a new one starts with the new
  target's storage state

#### Scenario: An unknown verb is a usage error
- **WHEN** the CLI is invoked with a verb it does not define
- **THEN** usage is printed on stderr and the exit code is 2

#### Scenario: A timed-out wait exits non-zero
- **WHEN** the `wait` verb's completion signal never appears and the daemon
  replies with `ok` false
- **THEN** the reply is printed to stdout and the exit code is non-zero

#### Scenario: A failed driving verb exits non-zero
- **WHEN** any driving verb receives a reply whose `ok` field is false
- **THEN** the exit code is non-zero
