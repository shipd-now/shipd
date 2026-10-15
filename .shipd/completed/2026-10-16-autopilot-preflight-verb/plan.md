# autopilot-preflight-verb
Status: verified
Epic: autopilot-preflight
Theme: reliability

## Idea

Add `autopilot.py <epic> --preflight [--json]`: a read-only launch rubric of
`ok|warn|fail <check> — <detail>` lines in the `shipd doctor` format that
exits non-zero on any `fail`.

### Motivation

`/s:autopilot` and `/s:epic-grill` have no deterministic way to tell before
launch whether every member is planned, gated, unchanged since gating, free
of `After` cycles, and free of unordered overlap, so an unattended run stops
mid-way on a question nobody is present to answer.

### Details

- `compute_preflight(root, epic, command_fn=None)` returns `{"epic",
  "checks": [{"level", "check", "detail"}], "problems", "failed"}`;
  `_print_preflight` renders it as lines plus `preflight: ok|<n>
  problem(s)`, or one JSON object.
- Checks in order: `epic-lint`, `epic-status`, `after-cycle`, `members`,
  `gate-check`, `gated-hash`, `drift`, `overlap-requirements`,
  `overlap-files`, `pipeline`, then `doctor:<check>` relays.
- `--preflight` is exclusive with `--waves`, `--dry-run`, `--member`.

Affected capabilities: `epic-autopilot` (added `launch-preflight`). Impact:
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/tests/test_autopilot.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependency.

### Non-goals

- No skill text: `/s:autopilot` Phase 1, the pre-build drift step, and
  park-and-continue are `autopilot-unattended-run`; the grill hand-off is
  `grill-preflight-handoff`.
- No model, no `/s:drift` judgment, no re-plan, no worktree sync.
- No new stamp, drift, or cycle logic: the verb composes `gate-plan-stamp`,
  `drift-verb`, and `wave-dependency-order` helpers and never redefines them.
- No `docs/` page (none names `autopilot.py` flags today).

## Implementation

- **Shape mirrors `--waves`.** `compute_preflight` + `_print_preflight` sit
  in `autopilot.py` after `compute_waves`; `command_fn` (default
  `_run_command`) is the only seam, as wave-dependency-order adds to
  `compute_waves`. Rejected: a new module — the driver already hosts its
  read-only modes.
- **The checks.** `epic-lint`: `lint_epic(root, epic, errors)` in-process
  (imported beside `lint_change`), `fail` with the count and first error.
  `epic-status`: `ss.read_epic_status`; `ready`/`active` ok; `draft` fails
  naming `spec_status.py epic-set-status <epic> ready`; `complete` fails
  "nothing left to drive"; `None` fails. `after-cycle`:
  `sc.find_after_cycle(sc.parse_epic_after(text))`, `fail` "After column has
  a dependency cycle: a -> b -> a". `members`: states from `parse_members`
  grouped — `unplanned`/`draft` fail with "run /s:epic-grill <epic>",
  `rejected` fails with "enrich with /s:plan <slug>", `active`/`complete`/
  `verified` warn "mid-build, left undriven", `ready`/`archived` ok with
  counts. `pipeline`: `sc.resolve_pipeline(root)` (what `pipeline-show`
  prints) → ok "<n> entries (source: <provenance>)", `ConfigError` → fail.
- **Never through `select_and_order`.** wave-dependency-order makes it raise
  on a cycle; the preflight reads `parse_members` and the cycle finder
  directly so a cyclic epic still prints its whole rubric.
- **Gate and hash from one `--check` run per `ready` member**, from its
  hosting root (`ss._member_state_with_root`): `[sys.executable, GATE_PY,
  slug, "--root", hosting, "--check"]`. Dot-point findings containing
  `gated-hash mismatch` feed `gated-hash` (fail, "re-gate with spec_gate.py
  <slug>"); the rest feed `gate-check`; exit codes other than 0/2 fail
  `gate-check`. A `ready` plan whose `sc.read_plan_stamp` yields no
  `Gated-hash` is a `gated-hash` warn. Rejected: recomputing the hash with
  `plan_gated_hash` — it would duplicate the finding `--check` already owns.
- **Drift** (Q1): `[sys.executable, STATUS_PY, "--root", root, "drift",
  "--epic", epic, "--json"]`; exit 0 ok; exit 4 warn listing `<change>
  (<kind> <n>, ...)` per member with findings plus "judge with /s:drift
  <epic>"; any other exit or unparseable JSON fails.
- **Overlap** (Q3): over planned members (state not `unplanned`/`archived`,
  table order), `reach` is the transitive closure of the `After` map; a pair
  is unordered when neither reaches the other. Targets are `<cap>/<id>` from
  `sc.parse_delta`'s `modified`, `removed`, and `renamed.from_id`; paths are
  `sc.cited_paths(text, strip_line_suffix=True)` over `plan.md`, `tasks.md`,
  and `specs/*/spec.md` minus `artefacts/` tokens and
  `sc.VERSION_BUMP_EXEMPT_PATHS`. Shared targets fail, shared paths warn, each
  as `"a & b: <item>"`.
- **Doctor relay** (Q2): `[sys.executable, SHIPD_BIN, "doctor"]` in `root`
  with `SHIPD_BIN = PLUGIN_DIR/bin/shipd`; each stdout line matching
  `DOCTOR_LINE_RE` becomes `(level, "doctor:" + name, detail)`, the
  `doctor:` summary line is dropped, and a run with no matching line is one
  `fail doctor`. The prefix keeps the preflight's `pipeline` name unique.
- **Exit.** `main` returns 1 when `failed`; `warn` never fails. `--json`
  help now covers both read-only modes.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.292` when planned; re-bump after a rebase
  if a sibling lands first).

Risk: `shipd doctor` reaches GitHub (bounded by its own `GH_TIMEOUT`), so
the preflight takes seconds — acceptable once per launch.

## Questions and answers

### Q1: What level does drift at launch get?
- **Question:** When `drift --epic` exits 4, is the `drift` line `warn`
  (launch proceeds, naming `/s:drift <epic>`; a verb error stays `fail`) or
  `fail` (launch blocked until re-planned)? Options: (1) warn; (2) fail.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: the `drift` line is `warn` naming
  `/s:drift <epic>` when the verb exits 4; a verb error stays `fail`.
- **Queued:** q-preflight-drift-line-level
- **Relied on by:** grill-preflight-handoff, autopilot-unattended-run

### Q2: How are `shipd doctor` lines carried into the rubric?
- **Question:** Options: (1) relay each line with its check name prefixed
  `doctor:`, level and detail verbatim, summary dropped; (2) verbatim names,
  accepting a duplicate `pipeline`; (3) one collapsed `doctor` line.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: each doctor line is relayed with its
  check name prefixed `doctor:`, level and detail verbatim, the summary line
  dropped.
- **Queued:** q-autopilot-preflight-doctor-line-relay

### Q3: What counts as an `After` edge for the overlap rules?
- **Question:** Options: (1) any path through the `After` graph in either
  direction orders the pair; (2) a direct `After` entry only.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: any path through the `After` graph in
  either direction orders a pair for the overlap rules.
- **Queued:** q-preflight-overlap-edge-transitivity

## Readiness attestation

### Problem and motivation

The driver has no launch check, so an unattended run discovers unplanned,
edited, cyclic, or overlapping members only when it stops to ask.

Evidence:

- Epic `autopilot-preflight`: Decisions "Preflight output", "Unplanned
  members fail the preflight", "Edited-after-gate fails the preflight",
  "Overlap rules"; Design "Orchestration layer".
- `plugins/s/skills/build/scripts/autopilot.py:1143-1165` — `run` only
  checks the epic file and status before driving.

### Scope and non-goals

One read-only driver mode, its tests, and the manifest bump; skill text,
the drift step, and the grill hand-off stay with later members.

Evidence:

- Epic `## Changes` rows `autopilot-unattended-run` and
  `grill-preflight-handoff` (After: `autopilot-preflight-verb`).
- `plugins/s/skills/autopilot/SKILL.md:49-73` Phase 1 is untouched here.

### Affected capabilities and files

One capability and three files: the driver gains the mode, the test module
its tests, the manifest its bump.

Evidence:

- `epic-autopilot`: one ADDED requirement `launch-preflight`; no master
  requirement modified.
- `autopilot.py:205-265` `compute_waves`, `:333-345` `_run_command`,
  `:1342-1426` `_print_waves` and `main`; `spec_lint.py:731` `lint_epic`;
  `spec_status.py:1394` `read_epic_status`, `:1467`
  `_member_state_with_root`; `spec_common.py:176-205` `Rename`/`DeltaFile`,
  `:319` `parse_delta`, `:3122` `parse_epic_after`;
  `plugins/s/bin/shipd:1213-1221` `doctor_report`;
  `test_autopilot.py:57-85` fixtures, `:454-465` `_FakeRunCommand`.
- Runnable: `spec_lint.py --epic autopilot-preflight` → `OK`, exit 0;
  `--epic nosuch` → `ERROR:` line, exit 1; `--json` → `{"ok", "errors",
  "warnings"}`.
- Runnable: `python3 plugins/s/bin/shipd doctor` → 18 `ok|warn|fail <check>
  — <detail>` lines incl. `ok pipeline — resolves: 6 entries (source:
  default)` and `warn protection — ...`, then `doctor: 2 problem(s)`, exit 0.
- Runnable: `pipeline-show --json` → `source: default`, 6 entries.
- Runnable: `autopilot.py autopilot-preflight --waves --dry-run` → usage
  error, exit 2; `--waves --json` → one object, exit 0.
- Runnable: `sc.parse_delta` on gate-plan-stamp's delta → `added` ids
  `plan-stamp-write`, `gate-check-mode`; `modified` `(context-gate-verb,
  9851e28d228d)`.

### No open task-shaping decision

Three decisions existed; all are settled.

Evidence:

- Drift line level (warn): PLANNER default, Q1.
- Doctor relay naming (`doctor:` prefix): PLANNER default, Q2.
- Overlap edge semantics (transitive): PLANNER default, Q3.
- Placement, seam, check order, `--check` as the hash source, exclusivity:
  investigation, runnable premises above.
