## 1. Constant, marker, helpers

- [x] 1.1 [req: schema-version-declaration, schema-marker-stamping] Add
      failing tests to `plugins/s/skills/build/tests/test_spec_common.py`:
      absent marker reads `1.0.0`; marker in an external `store_root` store
      is honored; malformed marker (`one.two`) raises naming the file;
      `stamp_schema_marker` writes `SCHEMA_VERSION` when absent, advances a
      same-major older value, and leaves a cross-major value untouched. Run
      and observe them fail.
- [x] 1.2 [req: schema-version-declaration, schema-marker-stamping] Implement
      in `plugins/s/skills/build/scripts/spec_common.py`:
      `SCHEMA_VERSION = "1.0.0"`, `read_schema_marker(root)`,
      `stamp_schema_marker(root)` (marker path
      `os.path.join(specs_dir(root), "schema")`, one line plus newline,
      tuple-of-ints comparison), and `check_schema_compat(root)` (major
      mismatch raises `ConfigError` naming repo version, engine version, and
      remedy; repo minor ahead prints one stderr warning). Confirm the 1.1
      tests pass.

## 2. Entry-point enforcement and stamping

- [x] 2.1 [req: schema-compat-gate, schema-marker-stamping] Add failing
      tests to `test_spec_common.py` (driving the scripts as subprocesses,
      the suite's existing pattern): a `2.0.0` marker makes a `spec_status.py`
      read verb, `spec_emit.py`, `spec_merge.py`, `spec_lint.py`, and
      `spec_gate.py` exit non-zero naming both versions before touching
      artifacts; a same-major higher-minor marker warns on stderr and
      proceeds; `spec_status.py init` on a fresh repo stamps the marker and
      does not refuse; an emit install and a merge advance a same-major
      older marker. Run and observe them fail.
- [x] 2.2 [req: schema-compat-gate] Wire `check_schema_compat` at verb
      dispatch in `plugins/s/skills/build/scripts/spec_status.py` (every
      verb except `init`) and at the main entries of `spec_emit.py`,
      `spec_merge.py`, `spec_lint.py`, and `spec_gate.py`.
- [x] 2.3 [req: schema-marker-stamping] Add `stamp_schema_marker` calls:
      `spec_status.py init` after scaffolding, `spec_emit.py` after a
      successful install, `spec_merge.py` after a successful merge. Confirm
      the 2.1 tests pass.

## 3. Doctor check

- [x] 3.1 [req: doctor-schema-check] Add failing tests to
      `plugins/s/skills/build/tests/test_shipd_cli.py`: `ok schema` naming
      the version on a matching repo (and the assumed wording with no
      marker), `warn` when the repo minor is ahead, `fail` naming both
      versions on a major mismatch with the preflight still completing. Run
      and observe them fail.
- [x] 3.2 [req: doctor-schema-check] Implement `check_schema(root)` in
      `plugins/s/bin/shipd` following the existing `(level, name, detail)`
      tuple convention and register it in the doctor's check sequence.
      Confirm the 3.1 tests pass.

## 4. Docs and version bump

- [x] 4.1 [req: schema-version-declaration] Add a "Schema version" section
      to `.shipd/README.md`: what the version covers, the marker file, the
      compat rules (tolerate minor, refuse major), and the bump rubric
      (major = grammar break, minor = additive, patch = clarification).
- [x] 4.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to `0.6.179`,
      then run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it passes.

## 5. Gate the binary's in-process read verbs (validation fix)

- [x] 5.1 [req: schema-compat-gate] Add failing tests to
      `plugins/s/skills/build/tests/test_shipd_cli.py`: in a repo whose
      `.shipd/schema` holds `9.9.9`, `shipd list verified` (text and
      `--json`) and `shipd metrics` each exit non-zero naming `9.9.9` and
      the engine's version, printing no artifact rows; the same verbs on a
      matching-marker repo stay exit 0 and row-printing. Run and observe the
      new tests fail.
- [x] 5.2 [req: schema-compat-gate] In `plugins/s/bin/shipd`, call
      `spec_common.check_schema_compat(root)` before the engine seam in
      `cmd_list` (the `ss.list_rows` call at ~line 260) and in the metrics
      verb's in-process path, converting the raised `ConfigError` into the
      binary's standard `Error:` line and non-zero exit. The doctor's
      report-only behavior is untouched. Confirm the 5.1 tests pass, then
      run the full engine suite and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 198 | 47.2k |
| Edit | 37 | 19.7k |
| Read | 46 | 4.4k |
| (no tool) | 0 | 3.0k |
| Agent | 4 | 1.5k |
| ToolSearch | 1 | 78 |
| **Total** | 286 | 75.9k |
