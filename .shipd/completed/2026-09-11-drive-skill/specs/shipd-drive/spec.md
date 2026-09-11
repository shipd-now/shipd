## ADDED Requirements

### Requirement: Drive skill flow
id: drive-skill-flow

The plugin SHALL ship a `/s:drive` skill at `plugins/s/skills/drive/SKILL.md`
whose first user-visible status sentence names the running plugin version read
from the plugin manifest, and whose flow runs in order: resolve the target,
run the preflight, obtain or reuse a login, start the session, drive the
requested instructions, and print a verdict. The skill SHALL issue no
`AskUserQuestion`; where the request names no target, it SHALL print the
resolved targets as a numbered plain-text list and read a typed reply. Before
authoring any precise selector the skill SHALL sample the live DOM with the
read-only `probe` verb rather than guessing, and SHALL wait for a named
completion signal — never a fixed sleep — before reporting an outcome. The
plugin SHALL ship a matching harness body at
`plugins/s/harness/bodies/drive.md`.

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

### Requirement: Target and credential resolution
id: drive-targets-config

The control CLI SHALL resolve targets from `~/.shipd/drive/targets.json`,
overridden entry-by-entry by `<content-dir>/drive/targets.json` when the
repository ships one, where each target declares a `url` and an `auth` recipe
of kind `none`, `env`, or `command`. For the `env` kind the CLI SHALL read the
two named environment variables; for the `command` kind it SHALL run the two
declared argv arrays and take each secret from stdout. The CLI SHALL pass
resolved secrets to a worker through its environment only, and SHALL never
place a secret in a command line, in its own output, or in a saved report. If
a named target is absent from both files, then the CLI SHALL report one
`Error:` line naming the target and exit non-zero.

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

### Requirement: Cached login reuse
id: drive-auth-cache

The `login` verb SHALL write the browser's storage state to
`~/.shipd/drive/auth/<target>.json`. While that file exists and its
modification time is within the resolved `authCacheTtlHours` (default 8), the
CLI SHALL reuse it and perform no login; otherwise it SHALL log in again and
overwrite it. Where a login fails, the CLI SHALL report the failure with the
path of a debug screenshot and exit non-zero, leaving any previous cache
untouched.

#### Scenario: A fresh cache skips the login
- **WHEN** a session starts for a target whose auth file was written inside
  the TTL
- **THEN** no login worker runs and the cached state is loaded

#### Scenario: An expired cache logs in again
- **WHEN** the auth file's modification time is older than the TTL
- **THEN** the login worker runs and the auth file is rewritten

### Requirement: Session daemon and driving verbs
id: drive-session

The CLI SHALL expose `session start`, `session status`, and `session stop`,
where `session start` launches a background worker owning one browser and one
page and listening on a Unix socket under `~/.shipd/drive/`, loading the
target's cached storage state. The driving verbs — navigating, snapshotting
the accessibility tree, clicking, typing, pressing, waiting, evaluating, and
screenshotting — SHALL each send one JSON request to that socket and print the
JSON reply. The daemon SHALL attach console and response listeners once at
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

### Requirement: Verification verdict
id: drive-verdict

Unless the request asks for a recording with no checking, a drive run SHALL
end on a `PASS` or `FAIL` verdict carrying its evidence. The CLI SHALL treat
the console errors present immediately after the first navigation as the
baseline, SHALL fail the run only on an error absent from that baseline, and
SHALL never fail on a warning. The run SHALL fail on any 4xx or 5xx response
to the target's own origin. If the named completion signal never appears
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

### Requirement: Drive preflight
id: drive-doctor

The CLI SHALL expose a `doctor` verb reporting each prerequisite's state:
`uv` and a Playwright browser binary are required for every verb, and
`ffmpeg` and `ffprobe` are required only for recording and post-processing.
The verb SHALL exit non-zero when a required tool is missing and zero
otherwise, and SHALL name a remedy for each missing tool. Where `doctor` is
invoked with `--fix`, it SHALL install the missing browser binary through the
Playwright worker and re-report, and SHALL state the network access it
performs before performing it.

#### Scenario: A missing required tool fails the preflight
- **WHEN** `doctor` runs with `uv` absent from PATH
- **THEN** the report marks `uv` missing with a remedy and the exit code is
  non-zero

#### Scenario: Video tools are optional for driving
- **WHEN** `doctor` runs with `ffmpeg` absent but `uv` and the browser present
- **THEN** the report marks `ffmpeg` as required for recording only and the
  exit code is zero
