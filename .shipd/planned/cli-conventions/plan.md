# cli-conventions
Status: complete
Epic: shipd-dx

## Idea

Codify one human-first output convention for the whole CLI surface — error
format, usage exit codes, TTY-aware color honoring `NO_COLOR` — in a shared
stdlib helper, and adopt it across `shipd` and the engine scripts.

### Motivation

The engine scripts each grew their own output handling with no shared
authority and no terminal color anywhere, and the `shipd-dx` epic names
clig.dev-conformant conventions as a top-of-funnel DX lever for the public
consumer.

### Details

- New stdlib module `plugins/s/skills/build/scripts/cli_common.py`:
  `color_enabled(stream)`, `err(reason, *, stream)`, `warn(message, *,
  stream)` — a red `Error:` / yellow `WARNING:` prefix only when the stream
  is a TTY and `NO_COLOR` is unset, plain text otherwise.
- Adopt it on the error/warning paths of `spec_status.py`, `spec_lint.py`,
  `spec_emit.py`, `spec_merge.py`, `spec_gate.py`, `metrics.py`,
  `heartbeat.py`, and `dashboard.py`'s CLI verbs; `bin/shipd` inlines the
  same guard.
- A new `cli-conventions` capability records the convention: single
  `Error: <reason>` line on stderr with nonzero exit, usage errors exit 2,
  color gated on TTY + `NO_COLOR`, piped output byte-identical to today.

Affected capabilities: `cli-conventions` (added). Impact:
`plugins/s/skills/build/scripts/` (new `cli_common.py` + eight adopters),
`plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_cli_common.py`,
plugin version bump. No new dependencies.

### Non-goals

- No change to any pinned output text: piped (non-TTY) bytes stay identical,
  so no other capability's scenarios are amended.
- No new verbosity/quiet flags and no `--json` (the `cli-json` sibling owns
  machine output).
- No color in the TUI (textual owns its own theming) and none on stdout data
  output — only the `Error:`/`WARNING:` prefixes on stderr.
- Sibling members do not depend on this module; adoption here covers the
  scripts as they exist when this member builds.

## Implementation

- **Helper lives in a new `cli_common.py`, not `spec_common.py`** —
  `spec_common`'s charter is the on-disk spec format; a tiny, dependency-free
  output module keeps that boundary. Rejected: extending `spec_common` —
  wrong authority, and every adopter already imports it for other reasons so
  a second small import is cheap.
- **Interfaces.** `color_enabled(stream) -> bool` returns
  `stream.isatty() and not os.environ.get("NO_COLOR")` (any non-empty value
  disables, per the no-color.org convention). `err(reason, stream=sys.stderr)`
  writes `Error: <reason>\n` — the `Error:` token wrapped in
  `\x1b[31m…\x1b[0m` only when `color_enabled(stream)`. `warn(message,
  stream=sys.stderr)` mirrors it with `WARNING:` and `\x1b[33m`. Neither
  exits — callers keep owning exit codes, so existing exit contracts cannot
  drift.
- **Adoption is mechanical:** each adopter's `sys.stderr.write("Error: …")` /
  `print("Error: …", file=sys.stderr)` call routes through `cli_common.err`
  with the reason text unchanged. `spec_lint.py`'s `ERROR:`/`WARNING:`
  finding lines keep their exact prefixes (they are its report format, not an
  error path) — only its own fatal errors adopt `err`.
- **`bin/shipd` inlines the three-line guard** instead of importing
  `cli_common`: dispatch replaces the process via `os.execv` before any
  engine import, and adding a path-insert + import to every invocation for
  two error sites is not worth it. The inline copy names `cli_common` as the
  authority in a comment.
- **Testability of the TTY branch:** tests exercise the color branch through
  `pty.openpty()` (stdlib) and the plain branch through pipes, plus
  `NO_COLOR=1` over a pty asserting plain bytes. Piped-output byte-identity
  is the load-bearing property protecting every pinned scenario.
- Risk: an adopter's error text accidentally reworded during the sweep;
  guard: adoption tasks forbid text changes and the suite's existing
  pinned-string tests fail on any drift.
