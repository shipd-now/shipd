## ADDED Requirements

### Requirement: Human handoff of the live session
id: drive-handoff

The CLI SHALL expose `handoff [signal] [--timeout <seconds>]` and `resume`
as driving verbs that each send one JSON request to the session socket. When
the daemon receives `handoff` while its browser is headless, it SHALL relaunch
the browser visible inside the same process, carrying over the context's
storage state, the page's current URL, and every accumulated console and
network event, and SHALL reply with a truthy `relaunched` field; while the
browser is already visible it SHALL relaunch nothing and reply with a falsey
`relaunched` field. On every `handoff` the daemon SHALL open a handoff window
stamped with the current time. Where `handoff` carries a `signal`, the daemon
SHALL wait for it with the `wait` verb's grammar and a default timeout of 300
seconds, closing the window when the signal appears; if the signal never
appears within the timeout, then the daemon SHALL close the window and reply
with a falsey `ok`. Where `handoff` carries no signal, the daemon SHALL reply
at once with an `open` field of true, and `resume` SHALL drain pending events
and close the open window. If `resume` arrives with no open window, then the
daemon SHALL reply with a falsey `ok`. If `handoff` arrives while a window is
already open, then the daemon SHALL open no second window, relaunch nothing,
and reply with a falsey `ok`. The `console` and `network` replies SHALL carry
a `handoffs` list of `{"start", "end"}` windows.

#### Scenario: A headless session relaunches visible on handoff
- **WHEN** `handoff` reaches a daemon launched without `--headed`
- **THEN** the browser reopens visible at the same URL with the same storage
  state, the events recorded before the handoff remain readable, and the reply
  carries `relaunched` true

#### Scenario: A handoff with a signal hands back on that signal
- **WHEN** `handoff url:**/dashboard` runs and the page later reaches that URL
- **THEN** the verb exits zero and the `console` reply carries one window with
  both `start` and `end` set

#### Scenario: A handoff without a signal waits for resume
- **WHEN** `handoff` runs with no signal, then `resume` runs
- **THEN** the first reply carries `open` true and the `network` reply after
  `resume` carries one closed window

#### Scenario: A resume with no open window fails
- **WHEN** `resume` runs while no handoff window is open
- **THEN** the reply carries `ok` false and the verb exits non-zero

#### Scenario: A second handoff while one is open fails
- **WHEN** `handoff` runs with no signal, then `handoff` runs again before
  `resume`
- **THEN** the second reply carries `ok` false, the verb exits non-zero, and
  the `console` reply still carries exactly one window

## MODIFIED Requirements

### Requirement: Target and credential resolution
id: drive-targets-config
base: f8043dbd753a

The control CLI SHALL resolve targets from `~/.shipd/drive/targets.json`,
overridden entry-by-entry by `<content-dir>/drive/targets.json` when the
repository ships one, where each target declares a `url` and an `auth` recipe
of kind `none`, `env`, `command`, or `manual`. For the `env` kind the CLI
SHALL read the two named environment variables; for the `command` kind it
SHALL run the two declared argv arrays and take each secret from stdout; for
the `manual` kind it SHALL resolve no credential at all and MAY read an
optional `done` completion signal and an optional `timeoutSeconds`. The CLI
SHALL pass resolved secrets to a worker through its environment only, and
SHALL never place a secret in a command line, in its own output, or in a saved
report. If a named target is absent from both files, then the CLI SHALL report
one `Error:` line naming the target and exit non-zero.

#### Scenario: Repository entry overrides the user entry
- **WHEN** both files declare a target of the same name with different urls
- **THEN** the resolved target carries the repository file's url

#### Scenario: Secrets never reach a command line
- **WHEN** a `command` auth recipe resolves a password and the CLI invokes the
  login worker
- **THEN** the worker's argv contains no secret value and the secret is passed
  in the worker's environment

#### Scenario: An unknown target fails loudly
- **WHEN** `login` names a target declared in neither file
- **THEN** stderr carries a single line beginning `Error: ` and the exit code
  is non-zero

#### Scenario: A manual target needs no credential
- **WHEN** `targets` and `login` run against a target whose `auth` kind is
  `manual` with no credential variable set
- **THEN** `targets` prints `auth: manual` and `login` resolves no secret and
  sets neither login variable in the worker's environment

### Requirement: Cached login reuse
id: drive-auth-cache
base: 518731a83d60

The `login` verb SHALL write the browser's storage state to
`~/.shipd/drive/auth/<target>.json`. While that file exists and its
modification time is within the resolved `authCacheTtlHours` (default 8), the
CLI SHALL reuse it and perform no login; otherwise it SHALL log in again and
overwrite it. Where the resolved target declares an `auth` recipe of kind
`none`, the CLI SHALL perform no login at all: it SHALL NOT invoke the login
worker, SHALL NOT require any credential, SHALL write no cache file, and SHALL
exit zero. Where the recipe kind is `manual`, or `login` carries the
`--manual` flag, the CLI SHALL invoke the login worker with `--manual`,
forwarding the recipe's `done` and `timeoutSeconds` when present, and the
worker SHALL open a visible browser at the target url, print a notice naming
the window and the signal it waits for, wait until that signal appears (by
default until the URL differs from the login url while the host still matches
the target's), and write the storage state to the same cache path. Where
`--manual` is given, the CLI SHALL log in even while a fresh cache exists.
Where a login fails, or a manual login's signal never appears within its
timeout (default 300 seconds), the CLI SHALL report the failure with the path
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

#### Scenario: A manual recipe opens a visible login
- **WHEN** `login` names a target whose `auth` kind is `manual` with a `done`
  of `url:**/home` and no fresh cache
- **THEN** the login worker runs with `--manual` and `--done url:**/home` on
  its argv and no login variable in its environment

#### Scenario: The manual flag overrides a fresh cache
- **WHEN** `login <target> --manual` runs while the target's auth file is
  inside the TTL
- **THEN** the login worker still runs with `--manual`

#### Scenario: A timed-out manual login leaves the cache untouched
- **WHEN** a manual login's signal never appears within its timeout
- **THEN** the CLI reports a debug screenshot path, exits non-zero, and the
  previous auth file is unchanged

### Requirement: Session daemon and driving verbs
id: drive-session
base: fc0ff58915a5

The CLI SHALL expose `session start [--headed]`, `session status`, and
`session stop`, where `session start` launches a background worker owning one
browser and one page and listening on a Unix socket under `~/.shipd/drive/`,
loading the target's cached storage state. The browser SHALL launch headless
unless `--headed` is given, and the CLI SHALL record the mode in the session
state file and report it from `session status`. The driving verbs —
navigating, snapshotting the accessibility tree, clicking, typing, pressing,
waiting, evaluating, screenshotting, handing off, and resuming — SHALL each
send one JSON request to that socket and print the JSON reply. If a reply
carries a falsey `ok` field, then the verb SHALL still print that reply to
stdout unchanged and SHALL exit non-zero, so a caller reading only the exit
status never mistakes a failed verb for a successful one. The daemon SHALL
attach console and response listeners once at startup and accumulate every
event for the life of the session, so the `console` and `network` verbs
report events emitted before the verb ran. Starting a session for a different
target SHALL replace the running one. Fatal errors SHALL be reported as a
single `Error: <reason>` line on stderr with a non-zero exit, and an unknown
or missing verb SHALL print usage on stderr and exit 2.

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

#### Scenario: The headed flag reaches the worker and the status
- **WHEN** `session start --headed` runs and `session status` follows
- **THEN** the worker's argv carries `--headed`, the state file records
  `headed` true, and the status line names the visible mode

### Requirement: Verification verdict
id: drive-verdict
base: 7f429daddf2c

Unless the request asks for a recording with no checking, a drive run SHALL
end on a `PASS` or `FAIL` verdict carrying its evidence. The CLI SHALL treat
the console errors present immediately after the first navigation as the
baseline, SHALL fail the run only on an error absent from that baseline, and
SHALL never fail on a warning. The run SHALL fail on any 4xx or 5xx response
to the target's own origin. While an event's time falls inside a handoff
window, the CLI SHALL list that event under a `during handoff` evidence line
and SHALL NOT fail the run on it. If the named completion signal never appears
within its timeout, then the verdict SHALL be `FAIL` and SHALL state that the
signal was never observed, never `PASS`.

#### Scenario: Pre-existing noise does not fail a run
- **WHEN** the same console error appears in the baseline and again after the
  actions
- **THEN** the verdict is not failed by that error

#### Scenario: A server error fails the run
- **WHEN** a request to the target's origin returns 500 during the run
- **THEN** the verdict is `FAIL` and the evidence names that request

#### Scenario: A missing completion signal is a failure
- **WHEN** the awaited completion signal does not appear before its timeout
- **THEN** the verdict is `FAIL` and states the signal was never observed

#### Scenario: A human's server error is reported apart
- **WHEN** a request to the target's origin returns 500 at a time inside a
  handoff window and no other evidence fails the run
- **THEN** the verdict is `PASS` and the evidence lists that request under
  `during handoff`

### Requirement: Drive skill flow
id: drive-skill-flow
base: 45b50844ae51

The plugin SHALL ship a `/s:drive` skill at `plugins/s/skills/drive/SKILL.md`
whose first user-visible status sentence names the running plugin version read
from the plugin manifest, and whose flow runs in order: resolve the target,
run the preflight, obtain or reuse a login, start the session, drive the
requested instructions, and print a verdict. The skill SHALL issue no
`AskUserQuestion`; where the request names no target, it SHALL print the
resolved targets as a numbered plain-text list and read a typed reply. When a
login fails, the skill SHALL end its turn with a numbered plain-text list
offering a manual login in a visible window, a retry, or a stop. When a
driving verb fails or a wait times out, the skill SHALL end its turn with a
numbered plain-text list offering a handoff on the failed signal, a retry, or
a stop, stating that a relaunch loses unsaved in-page state. Before authoring
any precise selector the skill SHALL sample the live DOM with the read-only
`probe` verb rather than guessing, and SHALL wait for a named completion
signal — never a fixed sleep — before reporting an outcome. The plugin SHALL
ship a matching harness body at `plugins/s/harness/bodies/drive.md`.

#### Scenario: The skill names its version first
- **WHEN** a `/s:drive` session begins
- **THEN** its first user-visible status sentence carries `s:drive v<version>`
  read from the plugin manifest

#### Scenario: A missing target is asked for as plain text
- **WHEN** the request names no target and more than one is resolved
- **THEN** the skill ends its turn with the targets as a numbered plain-text
  list and issues no `AskUserQuestion`

#### Scenario: The probe verb samples the live DOM
- **WHEN** the control CLI's `probe` verb runs against a reachable page
- **THEN** it drives the browser worker's read-only sampler and reports the
  accessibility tree, testid inventory, scoped HTML, and screenshot it wrote,
  exiting zero without submitting, saving, or creating anything

#### Scenario: Harness body parity holds
- **WHEN** the harness body template ids are compared against the
  `SKILL.md`-bearing directories under `plugins/s/skills/`
- **THEN** `drive` appears in both sets

#### Scenario: A failed login offers a manual one
- **WHEN** the `login` verb exits non-zero during the login stage
- **THEN** the skill ends its turn with a numbered plain-text list whose first
  option is `login <target> --manual`, and issues no `AskUserQuestion`

#### Scenario: A failed verb offers a handoff
- **WHEN** a driving verb exits non-zero or `wait` times out during the drive
  stage
- **THEN** the skill ends its turn with a numbered plain-text list whose first
  option is `handoff <signal>`, naming the relaunch cost
