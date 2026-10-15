# detached-drift-replan
Status: verified
Epic: autopilot-preflight
Theme: reliability

## Idea

Give the detached driver (`autopilot.py`'s `run`, `run_member`, and
`drive_member`) a pre-build drift step: sync the member's worktree with the
base branch, check its `After` dependencies merged, run `spec_status.py
drift`, judge drift with a headless `/s:drift --json`, re-plan on `revise`
through the enrichment machinery, park on `conflict`, and carry on with the
members that do not depend on a parked one.

### Motivation

An unattended run builds a member from a plan gated against older code
whenever a sibling merged or other work moved `main`, so the build either
stops a run nobody is watching or implements a stale plan; the detached path
has no step that re-checks the plan before `/s:build`.

### Details

- `drive_member`: before the built-in `build` stage, `_pre_build_step` runs
  sync → dependency check → drift verb → judgment → re-plan/re-gate or park.
- `run`: a member whose `After` dependency did not ship earlier in the run is
  not driven; it is reported `needs_human` at stage `dependency`.
- `session_driver.run_turn_result` returns the turn's `result` text, which
  carries `/s:drift --json`'s one object.
- `judge_fn` joins `session_fn`/`gate_fn`/`command_fn` as an injectable seam.

Affected capabilities: `epic-autopilot` (added `detached-pre-build-drift`,
`detached-dependent-continue`, `session-turn-result-text`). Impact:
`plugins/s/skills/build/scripts/autopilot.py`, `session_driver.py`,
`plugins/s/skills/build/tests/test_autopilot.py`, `test_session_driver.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependency.

### Non-goals

- No `/s:autopilot` skill text, in-session drift step, or Phase 1 preflight —
  `autopilot-unattended-run` owns them; no `--preflight` or `compute_waves`
  edits (`autopilot-preflight-verb`, `wave-dependency-order`).
- No change to the drift verb's or `/s:drift`'s flags, exit codes, or shapes.
- No new report bucket, `MemberResult` outcome, heartbeat state, or `docs/`.

## Implementation

- **Placement.** A "Pre-build drift step" section after `_tier_anchor` holds
  `_session_extra_args`, `_make_judge_fn`, `_sync_base_ref`, `_drift_prompt`,
  `_parse_drift_verdict`, `_drift_summary`, `_replan_prompt`, and
  `_pre_build_step`; `drive_member` calls it only for the built-in `build`
  stage — a skipped or replaced entry is the whole stage. Rejected: a new
  pipeline stage, the epic's non-goal.
- **Base ref** (Q1): `_sync_base_ref(command_fn, root)` runs `git fetch
  origin main` (rc ignored) then `git rev-parse --verify --quiet
  origin/main`; `origin/main` on 0, else `main` (`ss.DEFAULT_AMEND_BASE`).
  The ref is merged into the worktree (`git merge --no-edit <ref>`) and
  passed as `--base <ref>` to the verb and the skill — the ref rule
  `_merged_into_base` uses.
- **Dependencies.** `waiting = [d for d in member.after if not
  _merged_into_base(command_fn, root, d)]` (wave-dependency-order's helper,
  called, never redefined); non-empty → `needs_human`, stage `dependency`,
  reason `waiting on <a, b>: not merged into <ref>; re-run with --member
  <slug> once merged`, no session id. In `run`, `outcomes[slug]` records each
  result; a member with a dependency in `outcomes` whose outcome is not
  `shipped` is not driven: `hb.member_finished` with a `needs_human` result
  at stage `dependency`, reason `waiting on <dep> (<outcome>)`, appended to
  `needs_human` (Q2). Rejected: a `blocked` bucket — a new outcome through
  heartbeat and dashboard for one line of reason.
- **Sync failure:** non-zero merge → `git merge --abort` → `needs_human`,
  stage `sync`, reason `merge of <ref> failed: <first line>`.
- **Verb:** `[sys.executable, <SCRIPTS_DIR>/spec_status.py, "--root", cwd,
  "drift", slug, "--base", ref, "--json"]` in `cwd` (the join
  `_default_sync_fn` uses). Exit 0 → `drift [clean]`, build. Exit 4 → parse
  stdout; `_drift_summary` = `file-drift 2, symbol-gone 1` (kind counts,
  first-seen order). Other exit or unparseable JSON → `needs_human`, stage
  `drift`, reason `drift verb exit <rc>: <first stderr line>` (drift-verb
  Q3: an unmeasurable plan is an error).
- **Judgment:** `judge_fn(member, cwd, prompt, timeout, model=None,
  on_session=None) -> (ok, session_id, failure, text)`; production
  `_make_judge_fn(claude_bin)` runs one `session_driver.run_turn_result`
  with `_session_extra_args(model)` (factored out of `_make_session_fn`).
  `_drift_prompt`: "Run `/s:drift <m> --base <ref> --json` for the change
  `<m>` in this worktree and reply with exactly its JSON object — no fence,
  no prose. Edit no file, run no gate, open no question." Under
  `_strike_loop` (label `drift`, the build entry's `attempts`):
  `_parse_drift_verdict(text, member)` strips a fence or surrounding prose
  to the outermost braces, `json.loads`, raises `ValueError` on `error`, a
  missing member, or an unknown verdict word, returns `holds` for a member
  in `clean`, else `(verdict, reason, contradicts, revise)`; a `ValueError`
  is the attempt's failure. Exhausted → `needs_human`, stage `drift`, reason
  `drift judgment failed after <n attempts>: <failure>`, judge session id.
  Rejected: routing through `session_fn` — it returns no text.
- **Verdicts.** `holds` → build. `conflict` → `needs_human`, stage `drift`,
  reason `plan conflicts with <contradicts>: <reason>`, judge session id.
  `revise` → `session_fn("replan", ...)` under `_strike_loop` (label
  `replan`, the entry's attempts/timeout/resumes/model), prompt
  `_stage_prompt("replan", slug, entry, drift=info)` → `_replan_prompt`:
  names the ref, reason, `revise:` text, and findings; says to revise the
  installed artifacts in place, keep every `**Answered by:** USER` answer
  and epic Decision, consult agent `s:oracle` for un-inferrable decisions,
  never wait for a human, and finish with `python3 <GATE_PY> <m> --root
  <cwd> --base <ref>`. `_make_session_fn` grades `replan` with `_plan_grade`
  like `enrich`. Then `_run_gate` over `gate_fn(m, c, base=ref)` —
  `_default_gate_fn(member, cwd, base=None)` appends `--base <base>` when
  given, and the two-argument call every other gate stage makes is unchanged
  — so the deterministic re-gate stamps `Planned-at` at the synced ref, as
  the in-session drive's re-gate does: pass → build; `rejected` → outcome `rejected`,
  stage `replan`, reason `context insufficient after drift re-plan (gate
  exit 2)`; `failed` → `needs_human`, stage `replan`. Drift is not
  re-measured: the re-gate stamps `Planned-at` at the synced base.
  Rejected: a stamp-change grade — a `revise` on doubt may change nothing.
- **Signature.** `_pre_build_step(root, member, cwd, entry, knobs,
  command_fn, session_fn, judge_fn, gate_fn, out, hook, on_sess) ->
  (outcome, stage, reason, session_id)`, `outcome` in `proceed`,
  `needs_human`, `rejected`; `drive_member` and `drive_single_member` gain
  `judge_fn=None`; a vanished worktree after the step resolves through
  `_resolve_vanished`.
- **Session driver:** `result_text_from_transcript(text)` and
  `run_turn_result(...) -> (ok, failure, session_id, result_text)`;
  `run_turn` returns the first three, unchanged for every caller.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next patch
  above `main` at build time (`0.6.293` when planned).

Risks: a re-plan session finding a contradiction the judge missed still
grades `ready` — bounded by `/s:drift`'s rule that `revise` means a repair
exists; a stale `origin/main` over-reports waiting, bounded by the fetch.
The plan calls `_merged_into_base` and relies on the `After`-layered
`select_and_order`, though the epic's `After` cell names only `drift-verb`
and `drift-skill` — noted for the epic's consistency pass.

## Questions and answers

### Q1: Which ref does the detached sync and drift use?
- **Question:** Options: (1) `git fetch origin main` best effort, then
  `origin/main` when it resolves else `main`, merged into the worktree and
  passed through `--base` to the verb and `/s:drift`, the main checkout's
  branch untouched; (2) `git pull --ff-only origin main` in the main checkout
  and the verb's default `main`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default, one decision with
  autopilot-unattended-run Q1: `git fetch origin main`, then `origin/main`
  where it resolves else `main`, merged into the worktree and passed as
  `--base` to the drift verb, `/s:drift`, and the re-gate; the main checkout
  is untouched.
- **Queued:** q-autopilot-drift-sync-base-ref

### Q2: How is a member waiting on a parked or unmerged dependency reported?
- **Question:** Options: (1) `needs_human` at stage `dependency`, reason
  naming the dependency and why, no session id, no new bucket; (2) a new
  `blocked` outcome, report bucket, heartbeat state, and dashboard rendering.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** USER accepted the default: `needs_human` at stage `dependency`,
  reason naming the dependency and why, no session id, no new bucket.
- **Queued:** q-detached-dependency-blocked-member-reporting

## Readiness attestation

### Problem and motivation

The detached driver builds straight from the gated plan with no check that
the code it cites still stands.

Evidence:

- `plugins/s/skills/build/scripts/autopilot.py:915-935` — the built-in build
  session starts with no sync, drift, or dependency step.
- Epic `autopilot-preflight`: Decisions "Mid-run drift is re-planned, not
  asked", "The launch confirmation is the last question"; Design "The
  detached driver gains the same pre-build drift step".

### Scope and non-goals

The step lives in `drive_member`, the dependent-skip in `run`, the text turn
in the session driver; skill text, verb, skill, preflight, and waves stay out.

Evidence:

- Epic `## Changes` rows `autopilot-unattended-run`, `drift-verb`,
  `drift-skill`, `autopilot-preflight-verb`, `wave-dependency-order`.
- `autopilot.py:844-912` — the enrichment machinery reused unchanged.

### Affected capabilities and files

One capability and five files: the driver, the session driver, their two
test modules, and the manifest.

Evidence:

- `epic-autopilot`: three ADDED requirements; no master modified
  (`pipeline-stage-execution` base `e2351a61aa98` read, left as is).
- `autopilot.py:449-495` `_make_session_fn`, `:587-637` `_stage_prompt`,
  `:652-671` `_strike_loop`, `:701-960` `drive_member`, `:982-1011`
  `drive_single_member`, `:1014-1031` `_run_gate`, `:1143-1258` `run`;
  `session_driver.py:36-47`, `:78-108`; `test_autopilot.py:538-612` `_Seams`,
  `:1288-1398` `GateEnrichmentTest`; `test_session_driver.py:117-131`.
- Sibling plans: drift-verb (`drift <change> --base <ref> --json`, exits
  0/4/1, `findings[].kind`), drift-skill (`verdicts[].{member,verdict,
  reason,contradicts,revise}`, `clean`, `error`), wave-dependency-order
  (`_merged_into_base(command_fn, root, slug)`).
- Runnable: `git rev-parse --verify --quiet origin/main` in the worktree →
  sha, exit 0; `git merge --no-edit origin/main` → `Already up to date.`,
  exit 0.
- Runnable: `python3 -m unittest discover -s plugins/s/skills/build/tests -p
  test_autopilot.py` → 119 OK; `-p test_session_driver.py` → 10 OK.
- `evals/run.py:805-822` reads the headless transcript's string `result`
  field — the text `run_turn_result` returns.

### No open task-shaping decision

Five decisions existed; all are settled.

Evidence:

- Base ref: PLANNER default, Q1, oracle `INSUFFICIENT`.
- Dependent reporting: PLANNER default, Q2, oracle `INSUFFICIENT`.
- Judgment transport (single-turn result text), re-plan grade
  (`_plan_grade`), built-in-only placement: investigation.
