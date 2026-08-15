## 1. The shared helper

- [x] 1.1 [req: error-output-convention, tty-gated-color] Add failing tests in
      `plugins/s/skills/build/tests/test_cli_common.py`: `err`/`warn` write
      `Error: <reason>` / `WARNING: <message>` to the given stream;
      `color_enabled` is false for a pipe, false under `NO_COLOR=1` on a pty,
      true on a pty with `NO_COLOR` unset; the pty branch wraps only the
      prefix in `\x1b[31m`/`\x1b[33m` … `\x1b[0m`; the pipe branch emits no
      escape bytes.
- [x] 1.2 [req: error-output-convention, tty-gated-color] Implement
      `plugins/s/skills/build/scripts/cli_common.py` (stdlib-only:
      `color_enabled`, `err`, `warn`; no exit calls); run the 1.1 tests green.

## 2. Adoption sweep

- [x] 2.1 [req: error-output-convention] Route the fatal-error prints of
      `spec_status.py`, `spec_emit.py`, `spec_merge.py`, `spec_gate.py`,
      `metrics.py`, and `dashboard.py`'s CLI verbs through `cli_common.err`,
      keeping every reason text byte-identical; route `heartbeat.py`'s
      fail-soft warnings through `cli_common.warn`.
- [x] 2.2 [req: error-output-convention] In `spec_lint.py`, route only its
      fatal errors through `cli_common.err`; the `ERROR:`/`WARNING:` finding
      report lines keep their exact current format.
- [x] 2.3 [req: error-output-convention] In `plugins/s/bin/shipd`, inline the
      three-line TTY/`NO_COLOR` guard (comment naming `cli_common` as the
      authority) on its two error sites; usage text and exit codes unchanged.
- [x] 2.4 [req: error-output-convention, tty-gated-color] Run the full
      `plugins/s/skills/build/tests/` suite with no `textual` installed —
      green proves no pinned stderr text drifted.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Run `plugins/s/skills/build/tests_textual/`; green.
