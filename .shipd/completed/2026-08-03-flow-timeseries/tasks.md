# Tasks

## 1. Snapshot + recorder (capture API in metrics.py)

- [x] 1.1 [req: flow-timeseries] In `plugins/s/skills/build/tests/test_metrics.py`,
      add capture tests against temp fixture roots (never `~`):
      `flow_snapshot(root)` maps every lifecycle state — `unplanned` and
      `archived` included — to sorted deduped member slugs; `record_flow(root,
      config=..., now=...)` appends one `{ts, root, states}` JSON line to
      `<log_dir>/flow.jsonl`, skips the append (returns `None`) when the same
      root's last record has an equal `states` map, resolves a linked-worktree
      `root` to the main checkout via a fixture `.git` file with a
      `gitdir: <main>/.git/worktrees/<name>` line, honors `AM_FLOW_LOG_DIR`
      over config (empty string → recording disabled, returns `None`). Run and
      observe failure.
- [x] 1.2 [req: flow-timeseries] In
      `plugins/s/skills/build/scripts/metrics.py`, implement
      `_resolve_project_root(root)` (local mirror of `build_report.py`'s
      gitdir-file resolution — keep the sc/ss/heartbeat import allowlist),
      `flow_snapshot(root)` (the `collect_wip` epic walk without the in-flight
      exclusion), and `record_flow(root, config=None, now=None)` (dir
      resolution env → config → `resolve_log_dir`; dedup; ISO-UTC `ts`) per
      plan.md Implementation. Confirm 1.1 passes.

## 2. Reader + derive flow block

- [x] 2.1 [req: flow-timeseries] In
      `plugins/s/skills/build/tests/test_metrics.py`, add reader tests:
      `collect_flow(root, config=...)` returns only the resolved root's
      records sorted by `ts`, each carrying `states` and a derived `by_state`
      count map; malformed lines and a missing file degrade to skipped/empty;
      `derive(root, now=..., config=...)` returns a `flow` block
      `{series: [{ts, by_state}], n}`, stays JSON-serializable, and writes no
      file into the fixture tree or the flow log. Run and observe failure.
- [x] 2.2 [req: flow-timeseries, metrics-engine] Implement
      `collect_flow(root, config=None)` in `metrics.py` and wire the `flow`
      block into `derive` (read-only — `derive` never calls `record_flow`,
      preserving the modified metrics-engine requirement's write-free derive).
      Confirm 2.1 passes.

## 3. Lifecycle hooks + CLI verb

- [x] 3.1 [req: flow-timeseries] In `plugins/s/skills/build/tests/`
      (`test_spec_status.py`, `test_spec_emit.py`, `test_spec_merge.py`), add
      hook tests: a `set-status` CLI run, a `spec_emit.py change` install, and
      a `spec_merge.archive_change` archive each append a flow record to the
      `AM_FLOW_LOG_DIR` temp dir; with the destination unwritable the mutation
      still succeeds (exit 0 / no raise). Also set `AM_FLOW_LOG_DIR` to a
      per-class temp dir in the setUp of the CLI-driving suites
      (`test_spec_status.py`, `test_spec_gate.py`, `test_spec_merge.py`,
      `test_spec_emit.py`) so no existing test writes to the real
      `~/.shipd/builds/`. Run and observe the new tests fail.
- [x] 3.2 [req: flow-timeseries] Implement the three best-effort hooks: in
      `spec_status.py` at the end of `write_status`, in `spec_emit.py` after a
      successful change install, and in `spec_merge.py` after
      `archive_change`'s move — each a function-level `import metrics` +
      `metrics.record_flow(root)` wrapped in `try/except Exception: pass`.
      Confirm 3.1 passes.
- [x] 3.3 [req: flow-timeseries] In
      `plugins/s/skills/build/tests/test_metrics.py`, add a CLI test:
      `metrics.py record-flow --root <fixture>` (subprocess, env seam set)
      exits 0 and prints the appended record as JSON, then `unchanged` on a
      repeat run. Implement the `record-flow` subparser verb in `metrics.py`
      beside `summary`. Confirm the test passes.

## 4. Version bump & verification

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above
      the branch base (base is 0.6.39, so 0.6.40 — pick the next free one if
      taken, verifying against branches/tags/history).
- [x] 4.2 [req: *] Run the full dependency-free suite `python3 -m unittest
      discover -s plugins/s/skills/build/tests` with `textual` NOT installed —
      all green — and confirm no `flow.jsonl` appeared under the real
      `~/.shipd/builds/` during the run (capture a before/after line count).
- [x] 4.3 [req: *] Manually exercise the real behavior: with `AM_FLOW_LOG_DIR`
      pointed at a scratch dir, run `metrics.py record-flow --root .` against
      THIS repo, then a real `spec_status.py set-status` round-trip on a
      scratch fixture root (never mutating this repo's changes), and
      `metrics.py summary --root . --json`; sanity-check
      the appended records (full bands, main-root path, dedup) and the derive
      `flow` block, and paste the observed record into the task completion
      note.
