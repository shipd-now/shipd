# drive-cli-correctness
Status: verified
Theme: reliability

## Idea

Fix three defects in the `/s:drive` control CLI that let a failed drive run
report success and make a no-auth target unusable.

### Motivation

A real drive run against three sites found that `login` hard-fails on an
`auth.kind: "none"` target, every session verb exits `0` even when its reply
carries `"ok": false`, and `references/recording.md` documents helper method
names and argument orders the implementation does not have.

### Details

- `login` performs no login for an `auth.kind: "none"` target, instead of
  invoking the login worker that then demands `DRIVE_LOGIN_USERNAME` and
  `DRIVE_LOGIN_PASSWORD`.
- Every session verb exits non-zero when its reply carries `"ok": false`, so a
  `wait` that times out — the drive-verdict contract's own failure signal —
  cannot read as a pass.
- `references/recording.md` documents the helper's real API, and a test keeps
  the two from drifting apart again.

Affected capabilities: `shipd-drive` (modified), `drive-video` (added).
Impact: `plugins/s/skills/drive/scripts/drive.py`,
`plugins/s/skills/drive/references/recording.md`, and new tests under
`plugins/s/skills/drive/tests/`. No new dependencies; the CLI stays
stdlib-only.

### Non-goals

- No change to `record_worker.py`'s `Helper` implementation — the reference doc
  is corrected to match the code, not the reverse, because renaming a live
  helper method would break every action module already written against it.
- No change to the login worker's own credential handling for the `env` and
  `command` kinds.
- No new driving verbs, and no change to the verdict rules themselves.

## Implementation

- **`login` short-circuits on `kind: "none"` before resolving credentials.**
  `cmd_login` already calls `resolve_auth`, which returns `(None, None)` for
  that kind, and then invokes the worker anyway. Add the short-circuit in
  `cmd_login` after the TTL check: report that the target declares no login
  and return 0, writing no cache file. Rejected: seeding an empty storage-state
  file, which would fake a cache whose mtime then drives TTL logic that means
  nothing for a target that never logs in.
  Verified premise: `python3 drive.py login google` against a `kind: "none"`
  target exits `1` with
  `Error: login requires DRIVE_LOGIN_USERNAME and DRIVE_LOGIN_PASSWORD in the
  environment`.

- **`_print_reply` returns the exit status; every session verb returns it.**
  The ten session verbs (`open`, `snapshot`, `click`, `type`, `press`, `wait`,
  `eval`, `shot`, `console`, `network`) each call `_print_reply(...)` then
  `return 0` unconditionally, so the defect is one shared line, not a `wait`
  quirk. Make `_print_reply` return `0` when the reply's `ok` is truthy and `1`
  otherwise, and have each verb `return _print_reply(...)`. The reply is still
  printed to stdout unchanged, so callers parsing JSON are unaffected.
  Rejected: raising `DriveError` on a falsey reply — that would reroute the
  reply's own error text through a second format and lose the JSON on stdout.
  Verified premise: `python3 drive.py wait '#search' --timeout 20` printed
  `{"ok": false, "error": "Locator.wait_for: Timeout 20000ms exceeded...."}`
  and exited `0`.

- **Correct `recording.md` against the real `Helper`.** The helper exposes
  `content_ready()` (documented as `ready()`), and
  `annotate(text, anchor_selector=None, duration=2.5)` — text first — where the
  doc shows `annotate(selector, text, seconds=3.0)`. `highlight` takes
  `duration`, not `seconds`, and neither `glide_click` nor `glide_type` accepts
  the documented `label`. Rewrite those entries to the signatures in
  `record_worker.py`.

- **A doc-drift test pins the contract.** Add a test that imports `Helper` from
  `record_worker.py` and asserts each helper method the reference names exists
  with the documented parameter names, via `inspect.signature`. This is what
  stops the doc regressing again, and it satisfies the constitution's
  every-engine-change-carries-tests rule. Risk: `record_worker.py` imports
  Playwright at module scope, which CI does not install — mitigated by
  importing it through `importlib` with a stubbed `playwright` module, the
  pattern `tests/_stubs.py` already establishes for this suite.

Risk: a caller that today ignores exit codes and reads only stdout sees no
change; a caller that checks `$?` starts seeing failures it previously missed.
That is the point of the fix, and the drive skill's own flow already reads the
JSON, so nothing in-repo depends on the old always-zero behavior.
