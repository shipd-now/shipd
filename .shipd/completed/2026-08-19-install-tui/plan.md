# install-tui
Status: verified
Epic: harness-install

## Idea

Add the interactive `shipd install` finish: the animated wordmark, a
`/dev/tty` harness multi-select over the registry, a persisted selection,
and user-global command generation for the chosen harnesses — wired into
`install.sh` fail-soft.

### Motivation

The curl install ends headless: it installs the plugin and launcher and
prints notices, but never asks which coding harnesses the user works in —
the one onboarding question the harness-install epic exists to add.

### Details

- New engine module `plugins/s/skills/build/scripts/install_tui.py`: the
  interactive flow (wordmark intro, multi-select, selection record,
  generation hand-off, degradation paths).
- `plugins/s/bin/shipd`: new in-binary curated verb `install`.
- `install.sh`: run the launcher's `install` verb at the end when a
  controlling terminal is available, fail-soft.
- Tests extending `plugins/s/skills/build/tests/` (`test_install_tui.py`,
  additions to `test_install.py`); plugin version bump.

Affected capabilities: `install-tui` (added), `shipd-cli` (modified — the
curated set gains `install`), `shipd-install` (modified — the wiring).
Impact: the files above plus `plugins/s/.claude-plugin/plugin.json`. Builds
after `harness-verb` (uses its user-mode generation); no new dependencies.

### Non-goals

- No repo-level generation from the TUI — repositories go through
  `shipd harness add` (the harness-verb member).
- No `textual`, no curses full-screen mode — raw ANSI + stdlib `termios`
  only, per the epic's constitution constraint.
- No change to the plugin-install steps, the launcher, or the auto-update
  notice — the wiring appends one fail-soft step after today's output.
- No rebrand: the ☕ completion line and every existing message stay
  byte-identical on non-TTY runs.

## Implementation

- **Verb flow (`shipd install`):** (1) resolve interactivity — the flow is
  interactive only when `/dev/tty` opens for read+write and
  `cli_common.color_enabled` holds for it; otherwise print the plain
  wordmark and a short "run `shipd install` from a terminal to pick your
  harnesses; `shipd harness add <id>` works per-repo" note, write nothing,
  exit 0. (2) play `wordmark.animate` on the tty. (3) run the multi-select
  over `harness_registry.HARNESSES` — every entry listed, `↑/↓` to move,
  space to toggle, `a` all, enter to confirm, `q`/Ctrl-C to abort with
  nothing written — implemented with stdlib `termios`/`tty` raw mode on
  the `/dev/tty` fd and in-place ANSI redraw; where raw mode fails
  (`termios.error`), fall back to a numbered line prompt ("toggle by
  number, empty line to confirm") on the same tty. Entries preselect from
  an existing selection record. (4) write the record. (5) for each selected
  harness with a `user_dir`, run the harness-verb `--user` generation
  in-process (`harness_generate`); report per-harness `installed` /
  `skipped (repo-level only — run shipd harness add in a repo)`. Abort
  paths restore the cursor and raw-mode settings in `finally`.
- **Selection record:** `~/.shipd/harnesses.json` —
  `{"version": 1, "harnesses": ["<id>", …]}` — written atomically
  (temp+rename), preloaded as the multi-select defaults on re-run, ids
  validated against the registry on load (unknown ids dropped silently).
  `~/.shipd/` is the established data home (`builds/`, `designs/`).
- **Binary wiring:** `cmd_install` in `plugins/s/bin/shipd` (in-binary
  verb, on-demand engine import of `install_tui`), added to the curated
  list, the non-delegating exceptions, and the usage banner
  (`install                     pick harnesses and install their commands`).
- **install.sh wiring:** after the existing tip block, a guarded step —
  `if [ -r /dev/tty ] && [ -w /dev/tty ]; then "$LAUNCHER" install
  </dev/tty >/dev/tty 2>&1 || printf …skipped-note…; fi` — POSIX sh,
  bash-3.2-safe, fail-soft: a nonzero TUI exit prints one note and the
  installer still exits 0. Headless runs (no `/dev/tty`) skip the step and
  keep today's output byte-identical, which is what keeps every existing
  `test_install.py` scenario green.
- **Testability:** the module separates pure pieces (selection-state
  reducer over key events, record load/save, per-harness outcome
  computation) from the raw tty loop, so tests drive the reducer and the
  non-TTY paths directly; a `pty`-based smoke test exercises the real loop
  end-to-end (send `␣`, `↓`, `␣`, `↵`; assert the record and the
  user-global files in an isolated `HOME`).
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` to the next
  patch above the branch's post-base-merge value.

Risk: raw-mode terminal handling is the classic breakage surface — bounded
by the line-input fallback, the `finally` restore, and the pty test. Risk:
`curl | sh` environments vary in `/dev/tty` availability — the guard makes
absence a clean skip, never a hang (input is bound to `/dev/tty`, never the
script's stdin, which the pipe owns).
