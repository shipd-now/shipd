## ADDED Requirements

### Requirement: Room wake workflow template
id: room-wake-workflow-template

The plugin SHALL ship `plugins/s/integrations/copilot/room-wake.yml`, whose
first line is `# shipd-copilot v{version}`, triggered on `issue_comment` and
`pull_request_review_comment` with `types: [created]`, and composed of three
jobs. The `guard` job SHALL run only when `vars.SHIPD_ROOM_AGENT` is
non-empty, the comment body contains `<!-- shipd-room `, and the event is a
review comment or an issue comment on a pull request; it SHALL bind
`github.token` and never `COPILOT_GITHUB_TOKEN`, check out the default
branch, and report not-actionable when the `COPILOT_GITHUB_TOKEN` secret is
absent. Otherwise it SHALL run the bundled
`.github/shipd-room/skills/room/scripts/room.py watch <pr> --once --since
<cursor>` as the agent `SHIPD_ROOM_AGENT` names — the cursor being the
`<issue>:<review>` pair `watch` accepts, `<id - 1>:0` for an `issue_comment`
trigger and `0:<id - 1>` for a `pull_request_review_comment` trigger — treat
empty stdout
as not actionable, and act only on the NDJSON line whose `comment` equals
the triggering comment id and whose `to` equals that agent; when acting it
SHALL `join` with `--harness copilot-cli` if no card of that name exists,
post `working` on the task, and output `actionable`, `pr`, `task`, `asker`
(the line's `last_agent`) and `text`. The `run` job SHALL depend on an
actionable guard, bind only `COPILOT_GITHUB_TOKEN`, check out
`refs/pull/<pr>/head` with `persist-credentials: false`, install
`@github/copilot@1.0.80`, run `copilot -p` with `--allow-all-tools` under a
`timeout` defaulting to 600 seconds, and output the reply truncated to
60000 characters. The `reply` job SHALL run with `if: always()` whenever the
guard was actionable, bind `github.token` and never `COPILOT_GITHUB_TOKEN`,
check out the default branch, read the reply only through `env:`, and post
via the bundled `room.py message <pr> --task <task> --to <asker>`: state
`input-required` with the marker stripped when the reply's last non-blank
line is exactly `<!-- shipd-room-reply: input-required -->`, else
`completed`. If the `run` job did not succeed or the reply is empty, then
the `reply` job SHALL instead post `close --task <task> --state failed
--reason wake-runner-failed`. Every `room.py` invocation SHALL run through
`/usr/bin/env -i` with an explicit `PATH=/usr/bin:/bin` and
`/usr/bin/python3 -B`.

#### Scenario: Addressed task is picked up
- **WHEN** the guard script runs with a stub `room.py` whose `watch` prints
  a line with `comment` equal to the event id and `to` equal to
  `SHIPD_ROOM_AGENT`
- **THEN** the guard outputs `actionable=true` with that task, asker and
  text, and the stub recorded a `message --task <id> --state working` call

#### Scenario: Other or empty lines are ignored
- **WHEN** the stub `watch` prints nothing, or a line for another comment
  id, or a line whose `to` names another agent
- **THEN** the guard outputs `actionable=false`, exits `0`, and the stub
  recorded no `message` or `join` call

#### Scenario: Reply marker selects input-required
- **WHEN** the reply script runs on a reply ending with the line
  `<!-- shipd-room-reply: input-required -->`
- **THEN** the stub recorded `message --task <id> --to <asker> --state
  input-required` with text that no longer holds the marker line

#### Scenario: Plain reply completes, failed run closes
- **WHEN** the reply script runs on a plain reply, and again with the run
  result `failure`
- **THEN** the first records `--state completed`; the second records `close
  --task <id> --state failed --reason wake-runner-failed`

#### Scenario: Credentials never share a job
- **WHEN** the template text is split into its three jobs
- **THEN** `COPILOT_GITHUB_TOKEN` is bound only in `run`, `github.token`
  only in `guard` and `reply`, and `run` checks out with
  `persist-credentials: false`

### Requirement: Room wake template tests
id: room-wake-tests

The template SHALL be covered by
`plugins/s/skills/room/tests/test_room_wake.py`, which extracts the guard
and reply `run:` scripts from the template, executes them with `bash`
in a temporary working directory holding a recording stub `room.py` at the
bundled path, with the `/usr/bin/python3` literal rewritten to the test
interpreter as the gate tests rewrite theirs, and asserts the triggers, the job split, the CLI pin and the
marker line; the suite SHALL need no network and be discovered by the `ci`
workflow's `Run room test suite` step.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests -v`
  runs with no network
- **THEN** it reports `OK`, including the `test_room_wake` cases
