# flow-timeseries
Status: verified
Epic: delivery-metrics

## Idea

Record the delivery board's per-lifecycle-state membership as an append-only
time series (`flow.jsonl` beside `builds.jsonl`), captured best-effort at the
engine's three lifecycle mutation chokepoints and exposed read-only through
`metrics.derive` as a `flow` block — the historical data a cumulative-flow
diagram and work-item aging need.

### Motivation

The board's lifecycle state exists only as a live snapshot — `metrics.py`'s
`collect_wip` re-derives it on demand and nothing records how it evolves — so a
CFD and historical work-item aging are underivable from today's events. The
epic isolates this genuinely-new capture into this member, and the shipped
`metrics-engine` explicitly deferred it ("no flow time-series — the
`flow-timeseries` member records history").

### Details

- New capture API in `metrics.py`: `flow_snapshot(root)` (full-band state →
  slug-list map) and `record_flow(root, ...)` appending
  `{ts, root, states}` records to `<log_dir>/flow.jsonl`, deduped against the
  root's last record.
- Best-effort hooks at the three lifecycle mutation primitives:
  `spec_status.write_status`, `spec_emit.py`'s change install, and
  `spec_merge.archive_change` — a capture failure never fails the mutation.
- Reader `collect_flow(root, config=None)` plus a `flow` block on
  `derive` (counts-only series), and a `record-flow` CLI verb on `metrics.py`.
- An `AM_FLOW_LOG_DIR` env seam (redirect; empty value disables) keeping every
  test suite off the real `~/.shipd/builds/`.

Affected capabilities: `delivery-metrics` — added `flow-timeseries`
requirement, plus a modified `metrics-engine` requirement (its "only
user-facing surface is the `summary` shell" clause must admit the new
`record-flow` verb and name the capture API as the module's one writing
surface; `derive` additionally lists the read-only `flow` block). Impact: `plugins/s/skills/build/scripts/metrics.py`,
`spec_status.py`, `spec_emit.py`, `spec_merge.py`; new tests plus env-seam
setUps in `plugins/s/skills/build/tests/` (`test_spec_status.py`,
`test_spec_gate.py`, `test_spec_merge.py`, `test_spec_emit.py`); plugin version
bump. Stdlib-only throughout — no `textual` anywhere near this change.

### Non-goals

- No redefinition of `derive`'s cycle time or WIP aging from the recorded
  history — the v1 definitions stand until consuming members
  (`metrics-board-view`, later refinements) exist and history has accumulated.
- No change to `metrics-cli`'s rendered summary lines (the `--json` derive dict
  gains the `flow` block for free; that mode already prints the full dict).
- No CFD rendering — that is the `metrics-board-view` member.
- No backfill of history predating the capture: evidence for past transitions
  does not exist.
- No per-individual attribution — records carry change slugs and lifecycle
  states only (SPACE guardrail).

## Implementation

- **Storage: `<log_dir>/flow.jsonl` beside `builds.jsonl`**, resolved
  `AM_FLOW_LOG_DIR` env → explicit `config` dict (`log_dir`) → layered
  `build.log_dir` → default `~/.shipd/builds` (reusing `resolve_log_dir`).
  Rejected: an in-repo `.shipd/flow/` file — every worktree would fork its own
  copy and append-only JSONL branches conflict on merge; the gitignored
  in-repo pattern (`.shipd/autopilot/`) is per-checkout ephemera, while this
  series must be one durable stream per project.
- **Record shape**: one JSON line
  `{"ts": <ISO-8601 UTC>, "root": <abs main-checkout path>, "states":
  {<state>: [<slug>, ...] sorted}}`. Slug lists, not bare counts: counts are
  `len()`-derivable, and the epic's aging goal needs per-item state-entry
  evidence (first record where a slug appears in a state). The `root` field
  exists because the default log dir is shared across projects — the reader
  filters on it (fixing, for flow, `builds.jsonl`'s known mixing quirk).
- **Full-band snapshot**: every epic stub member across all
  `.shipd/epics/*/epic.md` (same `sc.parse_epic_changes` +
  `_member_state_and_location` walk as `collect_wip`, dedup first-seen), but
  **including** `unplanned` (backlog band) and `archived` (cumulative done
  band) — the two bands `collect_wip` excludes and a CFD needs.
- **Main-root resolution**: snapshots are taken from the project's main
  checkout, resolved from a linked worktree via the `.git`-file `gitdir:`
  shape — a local mirror of `build_report.resolve_project_root`, kept local to
  preserve `metrics.py`'s sc/ss/heartbeat import allowlist (the same precedent
  as `resolve_log_dir`).
- **Trigger — event-driven hooks at the three mutation primitives**:
  `ss.write_status` (covers `set-status`, `sync`, and `spec_gate`
  promote/reject), `spec_emit.py`'s change-install path (unplanned → draft),
  and `spec_merge.archive_change` (→ archived). Each hook lazily
  `import metrics` inside `try/except Exception` so capture can never fail or
  block a lifecycle mutation (heartbeat's write-tolerance rule). Rejected:
  periodic sampling (no daemon exists) and capture-on-derive (cadence too
  coarse for a CFD). Epic installs (new `unplanned` members) are not hooked —
  dedup makes the next transition capture the new baseline.
- **Dedup**: `record_flow` skips the append when the `states` map equals the
  same root's last record — the series is a compact step function readers
  forward-fill. It returns the appended record, or `None` when unchanged or
  disabled.
- **Reader**: `collect_flow(root, config=None)` filters records to the
  resolved main root, skips malformed lines (mirroring
  `collect_ship_events`), sorts by `ts`, and returns
  `[{ts, states, by_state}]` with `by_state` counts derived from the slug
  lists. `derive` gains `"flow": {"series": [{ts, by_state}], "n": <len>}` —
  counts-only in the JSON dict; later members needing slugs call
  `collect_flow` directly. `derive` stays write-free: it never calls
  `record_flow`.
- **CLI**: a `record-flow` verb (`metrics.py record-flow [--root <root>]`) on
  the existing subparser — prints the appended record as JSON or `unchanged`,
  exits 0; the manual/cron capture surface and the observable verification
  seam.
- **Test hygiene**: `AM_FLOW_LOG_DIR` wins over all config resolution; set to
  the empty string it disables recording. The suites driving the hooked paths
  (`test_spec_status.py`, `test_spec_gate.py`, `test_spec_merge.py`,
  `test_spec_emit.py`) set it to a temp dir in setUp (their subprocess-driven
  CLIs inherit it), so no test ever writes to the real `~/.shipd/builds/`.

Risk: the hooks touch three battle-tested scripts — guarded by the never-raise
wrapper, the env seam, and full-suite runs. Note for the executor: when an
engine CLI runs as `__main__` and its hook imports `metrics`, a second module
copy of `spec_status` loads — harmless (read-only helpers); do not "fix" it.
