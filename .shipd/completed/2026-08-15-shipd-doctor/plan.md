# shipd-doctor
Status: verified
Epic: shipd-dx

## Idea

Add a read-only `shipd doctor` verb that preflights the environment — Python
version, git, gh auth, plugin snapshot freshness, optional textual, config
resolution — with one actionable line per check and a nonzero exit when a
required check fails.

### Motivation

Nothing preflights a consumer's environment today, so a missing prerequisite
surfaces as a mid-flow failure; the `shipd-dx` epic names a doctor preflight
as an install-and-first-run success criterion.

### Details

- New in-binary `doctor` verb in `plugins/s/bin/shipd` (like `list`: no
  engine delegate), printing one `ok|warn|fail <check> — <detail>` line per
  check and a closing `doctor: ok` / `doctor: N problem(s)` line.
- Required checks (fail → exit 1): `python` (>= 3.9), `git` (on PATH),
  `config` (the layered config at cwd resolves; absence of a content dir is
  `ok` with a note — `/s:plan` scaffolds it).
- Warning checks (never affect the exit): `gh` (present and `gh auth status`
  exits 0 — needed only to ship), `textual` (importable — board-only),
  `snapshot` (running from a plugin cache snapshot that is not the newest
  version directory warns; a repo-checkout run reports dev mode).

Affected capabilities: `shipd-cli` (modified). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/build/tests/test_shipd_cli.py`, plugin version bump. No new
dependencies.

### Non-goals

- No mutations and no auto-fix — `doctor` reports and hints, never installs
  or edits anything.
- No network checks (no marketplace reachability probe).
- No adoption of the `cli-conventions` helper — the verb is self-contained so
  epic build order stays free; its lines are plain text.
- No `--json` (the `cli-json` sibling owns machine output).

## Implementation

- **In-binary, not an engine script** — doctor aggregates environment facts
  the dispatcher already owns (its own resolved location, the manifest, the
  cache layout); `list` is the precedent for a non-delegating verb. Rejected:
  a new engine script — it would re-derive the binary's own location to judge
  snapshot freshness.
- **Check functions are injectable.** Each check is a small function taking
  its inputs (an env mapping, a `which` callable, the cache root path, the
  manifest version) and returning `(level, name, detail)`; `cmd_doctor`
  composes them. Tests drive each branch hermetically with stub PATH
  entries, a fake cache directory, and env dicts — no real gh/git calls.
- **Severity contract:** exit 1 iff any `fail` line printed; `warn` never
  affects the exit (epic: "exits nonzero when a required check fails"). gh is
  a warning because plan/build work without it; shipping is the first gh
  touchpoint.
- **Python floor 3.9:** the engine is stdlib-only Python 3 and the pinned
  `textual` supports 3.9+; the interpreter running the check is the one the
  engine runs on (`sys.version_info`).
- **Snapshot freshness:** the binary knows its own location; when it lies
  under `<cache>/shipd/s/<version>/`, compare `<version>` against the
  newest version directory in `<cache>/shipd/s/` (semver-aware sort, the
  cache layout observed: content directly under the version dir). Elsewhere
  it is a repo checkout → `ok dev mode` info line. Verified premises:
  `shipd --version` prints `0.6.101` from the manifest; the cache's newest
  dir is `0.6.101`; `gh auth status` exits 0 when authenticated.
- **Usage banner** gains the `doctor` line; unknown-verb and help behavior
  unchanged (exit 2 / exit 0 respectively).
- Risk: environment-dependent flakiness in tests; guard: no check shells out
  in tests — subprocess use is confined to the `gh` probe behind an
  injectable runner stubbed in tests.
