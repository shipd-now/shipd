# shipd-cli
Status: verified

## Idea

Add a single `shipd` binary — a stdlib-only dispatcher at `plugins/s/bin/shipd`
— that fronts the engine's human-workflow verbs (`list`, `status`, `board`,
`metrics`, …) so the engine is usable from a terminal without typing raw
script paths.

### Motivation

Every human interaction with the engine today is a raw
`python3 plugins/s/skills/build/scripts/<script>.py <verb>` invocation spread
across five scripts; the user asked for one `shipd` binary that covers the
workflow verbs (list, status, board, etc.), and no entry point exists anywhere
in the repo.

### Details

- New executable `plugins/s/bin/shipd` (stdlib-only Python 3, shebang
  `#!/usr/bin/env python3`) with a curated verb table that delegates to the
  engine scripts, resolved relative to the binary's own location so it works
  from a checkout or a plugin cache snapshot.
- New `list` verb implemented in the binary itself: enumerate in-flight
  changes across the invocation root's `planned/` and every
  `.worktrees/<name>`, reusing `spec_status.read_status`.
- `--version` reads the plugin version from the adjacent
  `.claude-plugin/plugin.json`.
- Tests in `plugins/s/skills/build/tests/test_shipd_cli.py`; plugin version
  bump in `plugins/s/.claude-plugin/plugin.json`; a "put shipd on your PATH"
  note in `README.md`.

Affected capabilities: `shipd-cli` (added). Impact: `plugins/s/bin/shipd`
(new), `plugins/s/skills/build/tests/test_shipd_cli.py` (new),
`plugins/s/.claude-plugin/plugin.json`, `README.md`; no new dependencies.

### Non-goals

- No mutating verbs: `set-status`, `merge`, `emit`, `autopilot`, and
  `worktree remove` stay behind their guarded scripts and skills — the CLI is
  a read/inspect surface in v1.
- No universal passthrough (`shipd <script> <args>`): it would bypass guarded
  verbs and freeze the internal script layout into a public contract.
- No packaging (pyproject/pipx) — distribution stays the plugin snapshot;
  PATH is a documented symlink to the checkout copy.
- No changes to any engine script's own CLI.

## Implementation

- **Location — `plugins/s/bin/shipd`.** The plugin snapshot is shipd's
  distribution unit (AGENTS.md), so the binary ships inside `plugins/s/` and
  resolves the engine at `<own dir>/../skills/build/scripts/` via
  `Path(__file__).resolve()`. Rejected: repo-root `tools/` (the `port.py`
  precedent is deliberately repo-only) and pyproject packaging (a second
  distribution channel with its own staleness story).
- **Dispatch — process replacement, not reimplementation.** Each curated verb
  maps to `[sys.executable, <script>, <mapped-verb>, *args]` and is run with
  `os.execv`, so stdout/stderr, interactivity (`tui`), and exit codes pass
  through verbatim. Verified premises: `dashboard.py board --root .` prints
  the delivery board (exit 0); `metrics.py summary --root .` prints the
  delivery summary (exit 0); `spec_status.py locate <missing>` prints
  `Error: change '…' not found` and exits 1. Rejected: importing the scripts'
  mains — argparse `prog`/exit behavior would leak and couple the binary to
  internals.
- **Verb table (curated, per the guarded-verb convention in
  `verified/shipd-port` and `verified/spec-status`):**
  `list` (in-binary), `status …` → `spec_status.py show`, `locate …` →
  `spec_status.py locate`, `epic …` → `spec_status.py epic-show`,
  `workspace` → `spec_status.py workspace-show`, `board` → `dashboard.py
  board`, `tui` → `dashboard.py tui`, `metrics …` → `metrics.py` (bare
  `shipd metrics` becomes `metrics.py summary`), `lint …` → `spec_lint.py`.
  Trailing arguments always pass through verbatim (so `--root`, slugs, and
  flags keep working). Unknown or missing verb → usage on stderr, exit 2;
  `shipd help`/`-h`/`--help` → usage on stdout, exit 0.
- **`list` semantics.** Probe the invocation root's `<content-dir>/planned/`
  and each `.worktrees/<name>/<content-dir>/planned/` (content dir resolved
  via `spec_common.resolve_config`/`specs_dir`); one line per change —
  `<name>  <location>  <status>` — with status from
  `spec_status.read_status` (import via `sys.path.insert` of the scripts
  dir). Dedupe by change name, the worktree occurrence winning (matching
  `locate`'s precedence). `--all` appends archived changes from
  `<content-dir>/completed/` labeled `archived`. Empty result prints
  `no changes in flight` and exits 0.
- **`--version`.** Read `version` from `<own dir>/../.claude-plugin/
  plugin.json`; print it and exit 0. Missing/unreadable manifest is a general
  error (`Error: …` on stderr, exit 1), matching the engine's error style.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` 0.6.96 → 0.6.97 in
  this change, per the snapshot contract in AGENTS.md.

Risk: a future engine-script rename silently breaks a verb mapping; guarded
by the delegation test exercising every table entry against the real scripts.
Risk: `list` walking a foreign `.worktrees/` entry with no content dir;
guarded by skipping worktrees without a `planned/` directory.
