## 1. Manual login recipe

- [x] 1.1 [req: drive-targets-config] In
      `plugins/s/skills/drive/tests/test_drive_targets.py`, add tests: a
      target with `auth.kind: manual` resolves through `resolve_auth` to
      `(None, None)` with no environment variable set; `targets` prints
      `<name>: <url> (auth: manual)`. Run them and observe them fail.
- [x] 1.2 [req: drive-targets-config] In
      `plugins/s/skills/drive/scripts/drive.py` `resolve_auth`, return
      `(None, None)` for kind `manual` and extend the docstring; confirm the
      1.1 tests pass.
- [x] 1.3 [req: drive-auth-cache] In
      `plugins/s/skills/drive/tests/test_drive_auth_cache.py`, using the
      existing `uv` spy, add tests: `login <manual-target>` with no cache runs
      the worker with `--manual`, `--url`, `--out`, forwards `--done` and
      `--timeout` from the recipe's `done` and `timeoutSeconds`, and sets
      neither `DRIVE_LOGIN_USERNAME` nor `DRIVE_LOGIN_PASSWORD`; `login
      <env-target> --manual` with a fresh cache still runs the worker with
      `--manual`; a failing manual login (spy in `DRIVE_TEST_SPY_FAIL` mode)
      reports the screenshot path, exits non-zero, and leaves the previous
      cache byte-identical. Run them and observe them fail.
- [x] 1.4 [req: drive-auth-cache] In `drive.py`, add `--manual`
      (`store_true`) to the `login` parser; in `cmd_login`, skip the TTL
      reuse when `--manual` is set, take the manual path when the flag is set
      or the recipe kind is `manual`, call neither `resolve_auth` nor
      `worker_env_with_secrets` on that path, build the worker argv
      `login --manual --url <url> --out <cache>` plus `--done <done>` and
      `--timeout <timeoutSeconds>` when the recipe declares them, and print
      `drive: a browser window is open for <name> — log in there` before
      running the worker; confirm the 1.3 tests pass.
- [x] 1.5 [req: drive-auth-cache] In
      `plugins/s/skills/drive/scripts/browser_worker.py`, add `--manual`,
      `--done`, and `--timeout` (float, default 300) to the `login`
      subparser; in `cmd_login`, when `--manual` is set skip the credential
      check, launch with `headless=False`, `goto` the url, print
      `drive: waiting for <signal description> (up to <timeout> s)` on
      stderr, then wait: with `--done`, use the `_wait_for_signal` helper
      from task 2.5; without it, `page.wait_for_function` on
      `([u, h]) => location.href !== u && location.host === h` with the
      login url and its host, timeout in ms; on success write the storage
      state through `_write_storage_state_privately`; on any exception keep
      the existing debug-screenshot and `Error:` path.
- [x] 1.6 [req: drive-targets-config] In
      `plugins/s/skills/drive/references/targets.example.json`, add a
      `sso-manual` target with `auth.kind: manual`, `done: "url:**/home"`,
      `timeoutSeconds: 300`, and `//`-prefixed notes explaining the kind, the
      default completion rule, and the `--manual` flag.

## 2. Headed session and handoff

- [x] 2.1 [req: drive-session] In
      `plugins/s/skills/drive/tests/test_drive_session.py`, using the `uv`
      session spy, add tests: `session start --headed` puts `--headed` on
      the worker argv and writes `"headed": true` to the state file; plain
      `session start` puts no `--headed` on the argv and writes `"headed":
      false`; `session status` with a live fake server prints `headed` or
      `headless` from the state file. Run them and observe them fail.
- [x] 2.2 [req: drive-session] In `drive.py`, add `--headed` (`store_true`)
      to the `session` parser; in `_session_start` append `--headed` to the
      worker argv when set; extend `_write_session_state` with a `headed`
      field and `_session_status` to print the mode; confirm the 2.1 tests
      pass.
- [x] 2.3 [req: drive-handoff] In `test_drive_session.py`, using
      `_FakeSessionServer`, add tests: `handoff` with no argument sends
      `{"op": "handoff"}` and prints the reply; `handoff url:**/home
      --timeout 30` sends `signal` and `timeout` fields; `resume` sends
      `{"op": "resume"}`; a `resume` reply with `ok` false is printed and
      exits non-zero. Run them and observe them fail.
- [x] 2.4 [req: drive-handoff] In `drive.py`, add `handoff` (positional
      `signal`, `nargs="?"`, and `--timeout` float) and `resume` subparsers
      with `cmd_handoff` and `cmd_resume` that forward through
      `_session_request` exactly like `cmd_wait`; update the module
      docstring's verb list; confirm the 2.3 tests pass.
- [x] 2.5 [req: drive-handoff] In `browser_worker.py`, extract
      `_wait_for_signal(page, signal, timeout_seconds)` from `_handle_wait`
      and call it from there; store `pw`, `browser`, `headed`, and
      `handoffs: []` in `ctx` inside `cmd_session`; add `--headed`
      (`store_true`) to the `session` subparser and launch with
      `headless=not args.headed`; move the listener attachment into
      `_attach_listeners(ctx, page)`; add `_relaunch_headed(ctx)` that saves
      `ctx["context"].storage_state()` as a dict, remembers `page.url`,
      closes context and browser, launches `headless=False`, opens a new
      context with `storage_state=<dict>`, a new page, re-attaches the
      listeners, navigates to the remembered url unless `about:blank`, and
      sets `ctx["headed"] = True`; add `_handle_handoff(ctx, signal=None,
      timeout=None)` and `_handle_resume(ctx)` per the plan's handoff-window
      decision; register both in `_build_handlers`; add `"handoffs":
      list(ctx["handoffs"])` to the `console` and `network` replies; update
      the module docstring.
- [x] 2.6 [req: drive-handoff] In `browser_worker.py` `cmd_session`'s accept
      loop, on `socket.timeout` call `ctx["page"].wait_for_timeout(1)`
      inside a `try`/`except Exception: pass` before continuing, so queued
      events dispatch while the daemon idles.

## 3. Verdict

- [x] 3.1 [req: drive-verdict] In
      `plugins/s/skills/drive/tests/test_drive_verdict.py`, add tests: a 500
      to the target origin whose `time` lies inside a window passed as
      `handoff_windows=[{"start": t0, "end": t1}]` yields `PASS` and an
      evidence line starting `during handoff:`; a new console error inside a
      window yields `PASS` with a `during handoff:` line; the same 500 outside
      the window still yields `FAIL`; calling without `handoff_windows` is
      unchanged. Run them and observe them fail.
- [x] 3.2 [req: drive-verdict] In `drive.py` `compute_verdict`, add the
      keyword argument `handoff_windows=None`, add a pure helper
      `_inside_handoff(time, windows)` treating an `end` of `None` as open,
      and route console errors and origin 4xx/5xx events whose `time` is
      inside a window to a `during handoff: <line>` evidence entry that never
      sets `ok` false; confirm the 3.1 tests pass.

## 4. Skill, harness, and release

- [x] 4.1 [req: drive-skill-flow] In `plugins/s/skills/drive/SKILL.md`:
      in step 3, after a failed login end the turn with a numbered plain-text
      list — (1) `login <target> --manual` in a visible window, (2) retry,
      (3) stop — and note the 600000 ms Bash timeout for the manual run; in
      step 5, after a failed verb or timed-out `wait` end the turn with (1)
      `handoff <signal>` (state that a relaunch keeps login, URL, and
      evidence but loses unsaved in-page state, and to look for the Chromium
      window), (2) retry, (3) stop, followed by `resume` when no signal was
      given; add `handoff` and `resume` to the verb list; in the verdict
      contract add a bullet that events inside a handoff window are listed
      under `during handoff` and never fail the run; mention `session start
      --headed`.
- [x] 4.2 [req: drive-skill-flow] Mirror the 4.1 additions in
      `plugins/s/harness/bodies/drive.md`, keeping its numbered-section
      shape.
- [x] 4.3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.239` to `0.6.240`.
- [x] 4.4 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/drive/tests -v` and confirm every test passes. Then
      smoke the worker by hand: `drive.py session start duckduckgo`,
      `drive.py open https://duckduckgo.com`, `drive.py handoff` (observe a
      visible window at the same URL and `relaunched: true`), `drive.py
      resume`, `drive.py console` (observe one closed window under
      `handoffs`), `drive.py resume` (observe `ok: false` and a non-zero
      exit), `drive.py session stop`.
