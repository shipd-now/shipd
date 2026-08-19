## 1. Interactive flow module

- [x] 1.1 [req: install-verb, install-selection] Add
      `plugins/s/skills/build/tests/test_install_tui.py` (unittest style)
      against the module's pure pieces and degradation paths: the
      selection-state reducer walks key events (down/space/all/confirm/
      abort) correctly; the record round-trips at
      `~/.shipd/harnesses.json` (isolated `HOME`) with `version` 1,
      atomic write, unknown ids dropped on load; the no-tty path prints
      the plain banner plus the non-interactive note, exits 0, and writes
      nothing; a repo-only harness in a confirmed selection is reported
      with the `shipd harness add` pointer and generates nothing; a
      pty-driven end-to-end run (send space, down, space, enter in an
      isolated `HOME`) writes the record and the toggled harnesses'
      user-global files, and restores tty attributes and cursor
      (`\x1b[?25h`) on both confirm and abort. Run and observe failure —
      the module does not exist yet.
- [x] 1.2 [req: install-verb, install-selection] Add
      `plugins/s/skills/build/scripts/install_tui.py`: stdlib-only
      (`termios`, `tty`, `json`, `os`, `sys`); imports `wordmark`,
      `harness_registry`, `harness_generate`, `cli_common` from its own
      directory; the pure selection reducer; record load/save per
      `plan.md`'s Implementation; the raw-mode multi-select on `/dev/tty`
      with in-place ANSI redraw, `a`/space/arrows/enter/`q` keys, the
      numbered line-prompt fallback on `termios.error`, and `finally`
      restoration; the headless degradation path; the per-selected-harness
      generation hand-off to `harness_generate`'s user mode with the
      installed/repo-only report. The 1.1 tests pass.

## 2. Binary and installer wiring

- [x] 2.1 [req: install-verb] In `plugins/s/bin/shipd` add `cmd_install`
      (on-demand import of `install_tui`, no arguments beyond `-h`), wire
      `install` into the in-binary dispatch, and add its usage-banner line;
      extend `plugins/s/skills/build/tests/test_shipd_cli.py`'s verb
      expectations so the banner scenarios cover `install`.
- [x] 2.2 [req: install-script] In `install.sh`, after the auto-update tip
      block, add the guarded fail-soft step from `plan.md`'s
      Implementation (POSIX sh, bash-3.2-safe: `/dev/tty` readable and
      writable → run `"$LAUNCHER" install </dev/tty >/dev/tty 2>&1`,
      `|| printf` one skipped-finish note); extend
      `plugins/s/skills/build/tests/test_install.py` with the two new
      scenarios (headless success output unchanged and verb not invoked;
      failing verb still exits 0 with the note) using a stub launcher.
- [x] 2.3 [req: *] Run the CI suite command
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      without `textual`/`pydantic` installed and observe all tests pass.

## 3. Ship the snapshot

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next patch above the branch's post-base-merge value.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 112 | 50.2k |
| Write | 6 | 25.7k |
| Edit | 26 | 14.6k |
| (no tool) | 0 | 6.3k |
| Agent | 2 | 1.5k |
| Monitor | 3 | 680 |
| TaskStop | 3 | 470 |
| Read | 2 | 263 |
| SendMessage | 1 | 193 |
| **Total** | 155 | 99.8k |
