# tasks

- [x] 1.1 [P1] [req: drive-auth-cache] Add a failing test to `plugins/s/skills/drive/tests/test_drive_auth_cache.py` asserting `login` on an `auth.kind: "none"` target runs no login worker, writes no cache file, and exits 0 with neither `DRIVE_LOGIN_USERNAME` nor `DRIVE_LOGIN_PASSWORD` set
- [x] 1.2 [P1] [req: drive-session] Add failing tests to `plugins/s/skills/drive/tests/test_drive_session.py` asserting a driving verb whose reply carries `"ok": false` still prints that reply to stdout and exits non-zero — cover `wait` on a timeout reply and at least one other verb
- [x] 1.3 [P1] [req: drive-helper-docs] Add a new test file `plugins/s/skills/drive/tests/test_drive_helper_docs.py` that parses the helper method entries out of `plugins/s/skills/drive/references/recording.md` and asserts, via `inspect.signature` on `record_worker.Helper`, that every documented method name and parameter name exists — import `record_worker` through `importlib` with a stubbed `playwright` module so the suite still needs no Playwright installed
- [x] 2.1 [P2] [req: drive-auth-cache] In `plugins/s/skills/drive/scripts/drive.py`, short-circuit `cmd_login` for an `auth` recipe of kind `none`: after the TTL check, print that the target declares no login, invoke no worker, write no cache file, and return 0 — then repair the two pre-existing tests this breaks (`ExpiredCacheReLoginsTest`, `FailedLoginLeavesCacheUntouchedTest`), whose shared `write_target_config()` fixture hardcodes the `app` target to `{"kind": "none"}`: move that fixture to an `env` auth kind supplying the credentials through `extra_env`, so both keep exercising the worker-invocation path they were written for
- [x] 2.2 [P2] [req: drive-session] In `plugins/s/skills/drive/scripts/drive.py`, make `_print_reply` return `0` for a truthy `ok` and `1` otherwise, and change all ten session verbs (`cmd_open`, `cmd_snapshot`, `cmd_click`, `cmd_type`, `cmd_press`, `cmd_wait`, `cmd_eval`, `cmd_shot`, `cmd_console`, `cmd_network`) to return that status instead of a bare zero
- [x] 2.3 [P2] [req: drive-helper-docs] Rewrite the helper API entries in `plugins/s/skills/drive/references/recording.md` to the real signatures — `content_ready()` not `ready()`, `annotate(text, anchor_selector=None, duration=2.5)` with text first, `highlight(selector, duration=1.5)`, `glide_click(selector, steps=24)` / `glide_type(selector, text, steps=24, delay=40)` with no `label` parameter, and `hold(seconds)` / `wait(seconds)` with their documented `label=None` dropped too — keeping the reveal rule and the contract prose intact
- [x] 3.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/drive/tests -v` from the repo root and confirm the whole drive suite passes
- [x] 4.1 [req: drive-helper-docs] Extend `plugins/s/skills/drive/tests/test_drive_helper_docs.py` to pin parameter **order**, not just membership: assert the parameter sequence each `references/recording.md` entry documents appears as a subsequence, in that order, of the real `Helper` signature — and extend the parse to cover every documented `h.<name>`, including a parenthesis-free one like `h.cursor`, asserting it resolves on `Helper` as a method or an attribute. Verify the test fails on the old broken `annotate(anchor_selector, text, duration=2.5)` order and on the current `h.cursor` entry before fixing either
- [x] 4.2 [req: drive-helper-docs] Correct the `h.cursor` entry in `plugins/s/skills/drive/references/recording.md`: `Helper` defines no public `cursor` attribute (only `_cursor_pos` and `_inject_cursor`), so rewrite that bullet to describe the injected cursor overlay without presenting `h.cursor` as an API an action module may touch. Do not add a `cursor` attribute to `Helper` — the plan's non-goals forbid changing it
- [x] 4.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.210` to `0.6.211` — AGENTS.md requires every change touching `plugins/s/` to bump the plugin version in the same PR, since the cache snapshot is keyed by version and without a bump `claude plugin update` is a no-op

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 222 | 94.8k |
| Edit | 7 | 10.2k |
| Write | 2 | 7.3k |
| Read | 15 | 6.3k |
| (no tool) | 0 | 6.2k |
| SendMessage | 8 | 6.1k |
| Agent | 8 | 5.6k |
| AskUserQuestion | 1 | 1.1k |
| **Total** | 263 | 137.6k |
