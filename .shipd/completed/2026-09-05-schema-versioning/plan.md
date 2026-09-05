# schema-versioning
Status: verified

## Idea

Give the shipd artifact grammar a declared semver — a `SCHEMA_VERSION`
constant, a repo-level marker stamped by engine writes, and a compatibility
gate on the engine's entry points — so any consumer (the shipd-app bindings
first) can tell whether a repo's artifacts and its engine speak the same
grammar, tolerating minor drift and refusing major breaks.

### Motivation

The shipd-app epic pins an engine checkout as its read contract, but nothing
declares which grammar version a repo's artifacts were written under, so a
pilot customer's repos authored by a newer plugin could silently misread
under the app's pinned engine. A declared semver makes the compatibility
check mechanical: tolerate minor, refuse major, loudly.

### Details

- `SCHEMA_VERSION = "1.0.0"` in `spec_common.py` — the artifact grammar's
  own semver, independent of the plugin version.
- A one-line marker at `<content-dir>/schema`, tracked with the artifacts;
  absent reads as `1.0.0`, so every existing repo stays valid unmigrated.
- A compat gate at the engine entry points: different major → hard error
  naming both versions and the remedy; repo minor ahead → one stderr
  warning, proceed; `init` and the doctor exempt.
- Writes (`init`, emit installs, merge/archive) stamp the marker when absent
  or same-major-and-older.
- A `schema` doctor check and a schema section in `.shipd/README.md`.

Affected capabilities: `schema-versioning` (added), `shipd-cli` (modified —
added doctor requirement). Impact: `plugins/s/skills/build/scripts/
spec_common.py`, `spec_status.py`, `spec_emit.py`, `spec_merge.py`,
`spec_lint.py`, `spec_gate.py`, `plugins/s/bin/shipd`, tests
(`test_spec_common.py`, `test_shipd_cli.py`), `.shipd/README.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No per-artifact version lines — one marker per repo; artifacts in a repo
  are a coherent set written by one grammar.
- No `config-show` changes — that verb prints configuration keys and
  provenance only; the schema surfaces through the marker, the gate's
  errors, and the doctor.
- No `schema` fields added to the read verbs' JSON output in this change.
- No migration tooling — a major bump ships with its own migration story
  when one ever happens.

## Implementation

- **Constant and helpers in `spec_common.py`**: `SCHEMA_VERSION = "1.0.0"`;
  `read_schema_marker(root)` (absent → `"1.0.0"`; malformed — not
  `N.N.N` digits-and-dots — raises `ConfigError` naming the file);
  `stamp_schema_marker(root)` (writes only when absent or same-major-and-
  older, one line plus newline); `check_schema_compat(root)` (major
  mismatch raises `ConfigError` naming repo version, engine version, and
  the remedy "upgrade the older side"; repo minor ahead prints one stderr
  warning and proceeds). Semver comparison is tuple-of-ints over the three
  dot parts — stdlib only, no packaging dependency, matching the
  constitution.
- **Marker location**: `os.path.join(sc.specs_dir(root), "schema")` — the
  resolved content directory, so an external `store_root` carries its own
  marker beside the artifacts it versions, and the marker travels with
  whatever git repo tracks those artifacts.
- **Enforcement at entry points, not in `specs_dir`**: an explicit
  `check_schema_compat` call at verb dispatch in `spec_status.py` (every
  verb except `init`, which stamps instead), at the main entry of
  `spec_emit.py`, `spec_merge.py`, `spec_lint.py`, and `spec_gate.py`, and
  before the engine seam in `bin/shipd`'s in-process artifact read verbs
  (`list`, `metrics`), which call `list_rows`/the metrics engine directly
  and never cross a script's dispatch (validator-caught bypass).
  Rejected: hooking `specs_dir()` — it sits on every hot path including the
  doctor's, and the doctor must report a mismatch rather than die on it.
- **Stamping**: `spec_status.py init` stamps after creating the layout;
  `spec_emit.py` stamps after a successful install; `spec_merge.py` stamps
  after a successful merge. All three go through `stamp_schema_marker`, so
  the never-rewrite-across-majors rule lives in one place. Stamp writes
  ride the existing `store_autocommit` behavior where an external store is
  git-backed — no new commit machinery.
- **Doctor**: a `check_schema(root)` in `bin/shipd` following the observed
  `(level, name, detail)` tuple convention — `ok schema — 1.0.0 (marker
  <path>)` / `ok schema — 1.0.0 (assumed; no marker yet)` / `warn` when the
  repo's minor is ahead / `fail` on a major mismatch, with the same remedy
  text as the gate. Runnable premise: `shipd doctor` observed printing
  `ok|warn|fail <check> — <detail>` lines and exiting 0 on this repo.
- **Docs**: a "Schema version" section in `.shipd/README.md` (the grammar's
  format authority): what the version covers, the marker, the compat rules,
  and when to bump which part — major for grammar breaks, minor for
  additive surface, patch for clarifications.
- **Risk**: entry-point enforcement touches five scripts' dispatch paths; a
  missed exemption could brick the doctor or init on a mismatched repo.
  Guard: tests cover exactly the exemption matrix (init stamps on a fresh
  repo; doctor reports `fail` instead of crashing on a future-major
  marker).
