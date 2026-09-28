# drive-human-takeover
Status: verified

## Idea

Let a human log in by hand and take over the live browser when `/s:drive`
cannot finish a step on its own.

### Motivation

The login worker fills one fixed selector list headless, so anyone driving a
target behind MFA, SSO, passkeys, or an OAuth consent screen gets a debug
screenshot and no way forward. When a driving verb fails mid-run, that same
person cannot see or touch the page the daemon holds, so the run stops instead
of being rescued.

### Details

- Add a fourth auth recipe kind, `manual`, with an optional `done` completion
  signal and `timeoutSeconds`, and add `--manual` to `login` to force a visible
  manual login for any target. Both write the storage-state cache file the
  daemon already loads.
- Add `--headed` to `session start`; the default stays headless. Record the
  mode in the session state file and report it from `session status`.
- Add `handoff [signal]` and `resume` driving verbs. `handoff` relaunches the
  browser visible when it is headless, carrying over the storage state, the
  current URL, and the accumulated evidence, stamps a handoff window, and
  optionally blocks on a completion signal. `resume` closes the window.
- Report handoff windows on the `console` and `network` replies, and teach
  `compute_verdict` to list events inside a window apart and never fail on
  them.
- Teach the skill and harness body to offer a manual login after a failed
  login and a handoff after a failed verb, as plain-text numbered options.

Affected capabilities: `shipd-drive` (modified). Impact:
`plugins/s/skills/drive/scripts/drive.py`,
`plugins/s/skills/drive/scripts/browser_worker.py`,
`plugins/s/skills/drive/SKILL.md`, `plugins/s/harness/bodies/drive.md`,
`plugins/s/skills/drive/references/targets.example.json`, tests under
`plugins/s/skills/drive/tests/`, and the plugin version bump. No new
dependencies.

### Non-goals

- No remote viewer, container, REST controller, or approval queue. The browser
  runs on the user's desktop and the window itself is the takeover surface.
- No change to the `record` or `probe` verbs, which keep their own launch
  behaviour.
- No persistent browser profile. Storage state stays the cache format.
- No correction of the `usernameEnv`/`usernameCmd` key names in
  `targets.example.json`, which the code never reads. That is a separate
  `/s:fix`.
- No change to the headless default of an unattended run.

## Implementation

Files: `plugins/s/skills/drive/scripts/drive.py` (`resolve_auth`,
`cmd_login`, `_session_start`, `_session_status`, `compute_verdict`,
`build_parser`, two new verb functions), `browser_worker.py` (`cmd_login`,
`cmd_session`, two new handlers, one relaunch helper, one shared wait helper),
`SKILL.md`, `plugins/s/harness/bodies/drive.md`,
`references/targets.example.json`, `plugins/s/.claude-plugin/plugin.json`.

- **Manual login is a flag on the existing worker subcommand.** `drive.py
  login` invokes `browser_worker.py login --manual --url <u> --out <p>
  [--done <signal>] [--timeout <s>]` when the recipe kind is `manual` or the
  `--manual` flag is given. The manual path calls neither `resolve_auth` nor
  `worker_env_with_secrets`, so no credential is resolved or placed anywhere.
  Rejected: a separate `manual-login` subcommand, which would duplicate the
  debug-screenshot and storage-state write path.
- **`--manual` always logs in.** A fresh cache is ignored when the flag is
  given, because the flag exists to replace a cached state the user knows is
  bad. The `manual` recipe kind without the flag honours the TTL like every
  other kind.
- **Default completion for a manual login.** Without `done`, the worker waits
  for `location.href !== loginUrl && location.host === targetHost`, so an SSO
  bounce to another host does not end the wait early. `done` overrides that
  with the `wait` verb's grammar (a load state, `url:<pattern>`, or a
  selector). `timeoutSeconds` defaults to 300, inside the Bash tool's 600 s
  ceiling. On expiry the worker writes the debug screenshot beside `--out`,
  prints one `Error:` line, exits non-zero, and leaves the cache untouched.
  The worker prints a stderr notice naming the window and the signal it waits
  for before it starts waiting.
- **Headless stays the default; `--headed` opts in.** Settled by the user
  (Q1). `session start --headed` forwards `--headed` to the worker, the
  session state file gains `"headed": bool`, and `session status` prints the
  mode. The flag name matches `record_worker.py`'s existing `--headed`.
- **Handoff relaunches in-process, never restarts the daemon.** The daemon
  keeps its `Playwright` handle in `ctx`. `_relaunch_headed(ctx)` saves
  `context.storage_state()` as a dict, remembers `page.url`, closes the
  context and browser, launches with `headless=False`, opens a new context
  from the saved dict and a new page, re-attaches the same console and
  response listeners, and navigates to the remembered URL unless it is
  `about:blank`. The evidence lists live in the process, so they survive.
  Rejected: restarting the daemon headed from `drive.py`, which loses the
  buffers, the baseline, and the socket. Accepted cost: unsaved in-page state
  (typed form input, SPA memory) is lost, and the skill says so when it
  offers the handoff.
- **Handoff windows are a separate list, not marker events.** `ctx["handoffs"]`
  holds `{"start": <epoch>, "end": <epoch or null>}` dicts. The `handoff` op
  relaunches when `ctx["headed"]` is false, appends an open window, and, when
  a `signal` is given, blocks on the shared `_wait_for_signal(page, signal,
  timeout_seconds)` helper extracted from `_handle_wait` (default 300 s). On
  success it closes the window and replies `{"signal", "relaunched"}`; on
  timeout it closes the window and raises, so the reply is `ok: false`.
  Without a signal it replies `{"relaunched", "open": true}` at once. The
  `resume` op first calls `page.wait_for_timeout(50)` to drain queued events,
  then closes the open window; with none open it raises. `console` and
  `network` replies carry `"handoffs"`. Rejected: marker events inside the
  buffers, which every reader of the buffers would have to filter.
- **Idle event pump.** Sync Playwright dispatches listeners only inside a
  Playwright call, so events raised while the daemon idles in `accept()` wait
  for the next verb and take its timestamp. On each accept timeout the loop
  calls `ctx["page"].wait_for_timeout(1)` inside a guarded `try`, so a
  human's clicks between verbs land near their real time. The drain in
  `resume` is the safety net for the same problem.
- **Verdict.** `compute_verdict` gains a keyword argument
  `handoff_windows=None`, so every existing caller is unchanged. An event
  whose `time` falls inside any window never fails the run and is listed as
  `during handoff: <line>`. Settled by the user (Q2). The baseline rule is
  unaffected.
- **Skill wording.** After a failed login the skill ends its turn with three
  plain-text options: a manual login in a visible window, a retry, or stop.
  After a failed verb or a timed-out wait it offers a handoff on the failed
  signal, a retry, or stop, and states the relaunch cost. It runs `login
  --manual` and `handoff` with a 600000 ms Bash timeout. No dialog anywhere.
- **Version bump** to 0.6.240 in the plugin manifest.

Risks: the operating system may open the window behind the terminal, so the
skill tells the user to look for the Chromium window. A `done` signal already
satisfied at load returns at once, so the skill guidance names a post-login
signal. The worker cannot be unit-tested in CI, which has no Playwright, so
the worker tasks are verified by the smoke step in `tasks.md`, matching how
the existing worker code is covered.

## Questions and answers

### Q1: Does the session launch headed by default?
- **Question:** Should `session start` launch Chromium headed by default so a
  takeover needs no restart? Options: (1) headed by default with a
  `--headless` opt-out; (2) headless by default with a `--headed` flag and a
  relaunch on failure. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2. Headless stays the default and `--headed` opts in; a
  handoff relaunches the browser visible in-process, keeping storage state,
  URL, and evidence.
- **Queued:** q-drive-session-headed-default, discarded after the answer as
  scoped to this change.

### Q2: How does the verdict treat events from the human's window?
- **Question:** Should console errors and 4xx/5xx origin responses recorded
  inside a handoff window fail the run? Options: (1) report them apart and
  never fail on them; (2) apply the current rules regardless of who acted.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Events inside a handoff window are listed under their
  own heading and never fail the run, since the agent cannot attribute them to
  the change under test.
- **Queued:** q-drive-handoff-window-verdict-attribution, discarded after the
  answer as scoped to this change.

## Readiness attestation

### Problem and motivation

The login worker fills one fixed form headless, so a target behind MFA, SSO,
passkeys, or OAuth consent ends in a debug screenshot with no way forward, and
a failed driving verb stops the run because nobody can see or touch the page.

Evidence:

- `plugins/s/skills/drive/scripts/browser_worker.py:173-247` drives one
  fixed selector list and reports a screenshot on any failure.
- `plugins/s/skills/drive/scripts/browser_worker.py:456` launches the session
  browser with `pw.chromium.launch()`, headless.
- Requirement `drive-auth-cache` names a screenshot as the only failure
  output; requirement `drive-session` fixes one browser and one page.

### Scope and non-goals

The change adds the manual recipe, the headed flag, the handoff and resume
verbs, handoff windows on evidence and verdict, and the skill wording; remote
viewers, persistent profiles, record, probe, and the example key names stay
out.

Evidence:

- In scope: `drive.py:405-452` (`resolve_auth`), `drive.py:515-595`
  (`cmd_login`), `drive.py:714-764` (`_session_start`), `drive.py:1254-1309`
  (`compute_verdict`), `browser_worker.py:415-517` (`cmd_session`).
- Out of scope: `record_worker.py:330` keeps its own `--headed` launch;
  `browser_worker.py:519` (`cmd_probe`) is not edited.

### Affected capabilities and files

One capability, `shipd-drive`, with five requirements modified and one added;
seven files change because the CLI, the worker, the skill text, the harness
body, the example, the tests, and the manifest each carry part of the flow.

Evidence:

- Capability `shipd-drive`: `drive-skill-flow` (base 45b50844ae51),
  `drive-targets-config` (base f8043dbd753a), `drive-auth-cache` (base
  518731a83d60), `drive-session` (base fc0ff58915a5), `drive-verdict` (base
  7f429daddf2c), hashes from `spec_status.py base-hash`; `drive-handoff`
  added.
- Files: `plugins/s/skills/drive/scripts/drive.py`,
  `plugins/s/skills/drive/scripts/browser_worker.py`,
  `plugins/s/skills/drive/SKILL.md`, `plugins/s/harness/bodies/drive.md`,
  `plugins/s/skills/drive/references/targets.example.json`,
  `plugins/s/skills/drive/tests/test_drive_targets.py`,
  `test_drive_auth_cache.py`, `test_drive_session.py`,
  `test_drive_verdict.py`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 plugins/s/skills/drive/scripts/drive.py doctor`
  exited 0 with `uv`, the browser, `ffmpeg`, `ffprobe`, and `vhs` present.
- Runnable premise: `drive.py targets` exited 0 and listed four targets, all
  `auth: none`.
- Runnable premise: `drive.py session status` exited 0 and printed `drive: no
  session is running`.
- Runnable premise: `spec_status.py base-hash shipd-drive <id>` printed the
  five hashes above.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Session window default (headless, `--headed` opt-in): settled by the user,
  Q1.
- Verdict treatment of handoff-window events (reported apart, never fail):
  settled by the user, Q2.
- Manual-login completion default (URL left the login page and host matches):
  settled by investigation of `browser_worker.py:210-221`.
- In-process relaunch over daemon restart: settled by investigation of the
  in-process evidence buffers at `browser_worker.py:445-447`.
- Handoff windows as a list rather than marker events: settled by
  investigation of the buffer readers at `browser_worker.py:334-339` and
  `drive.py:1254-1309`.
