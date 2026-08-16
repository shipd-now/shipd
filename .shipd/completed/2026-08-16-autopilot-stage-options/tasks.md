## 1. Tier resolution authority

- [x] 1.1 [req: stage-model-resolution] Add tests to
      `plugins/s/skills/build/tests/test_spec_common.py`: with no anchor,
      `resolve_model_tier("session")` is None, `"tier-below"` -> `"opus"`,
      `"tier-two-below"` -> `"sonnet"`; with anchor `"sonnet"`, both below
      tiers clamp to `"haiku"`; with anchor `"opus"`, `"tier-below"` ->
      `"sonnet"`; `"session"` with anchor `"sonnet"` -> `"sonnet"`; a
      concrete id (`"claude-fable-5"`) returns verbatim; a concrete
      non-ladder anchor steps from the ladder top. Run and observe failure —
      the function does not exist yet.
- [x] 1.2 [req: stage-model-resolution] In
      `plugins/s/skills/build/scripts/spec_common.py` (the pipeline block
      near `PIPELINE_STAGES`), add `MODEL_LADDER = ("fable", "opus",
      "sonnet", "haiku")` and pure stdlib
      `resolve_model_tier(tier, session_model=None)` per the plan's anchor
      rules. Confirm 1.1 passes.

## 2. Per-stage driver knobs

- [x] 2.1 [req: per-stage-driver-knobs, three-strike-parking, oracle-gate-enrichment]
      In `plugins/s/skills/build/tests/test_autopilot.py`, extend
      `_Seams.session_fn` to also record its `timeout`, `max_resumes`, and
      `model` arguments, then add failing tests: a build entry
      `{"stage": "build", "autopilot": {"attempts": 1}}` with an
      always-failing session parks after exactly one build session; with
      `attempts` 2 and a second-try success the member proceeds; a custom
      entry with `attempts` 1 runs its command once before parking; a gate
      entry `{"stage": "gate", "autopilot": {"attempts": 1}}` with gate rcs
      `[2, 2]` makes exactly one gate-engine call before enrichment, runs at
      most one enrichment session, and parks rejected; an entry
      `autopilot.timeout`/`autopilot.max_resumes` reaches `session_fn` for
      that stage while other stages get the run-global values.
- [x] 2.2 [req: per-stage-driver-knobs, three-strike-parking, oracle-gate-enrichment]
      In `plugins/s/skills/build/scripts/autopilot.py`: add
      `_stage_opts(entry, timeout, max_resumes)` returning
      `(attempts, timeout, max_resumes)` from `entry.get("autopilot")` with
      defaults `(3, timeout, max_resumes)`; rename `_three_strike` to
      `_strike_loop(action, out, label, attempts=3, on_attempt=None)` with
      `attempt %d/%d` labels and update every caller; give `_run_gate` an
      `attempts=3` parameter; in `drive_member` wire each entry's values into
      its session drives, custom/replace command retries, and the gate's
      engine loop and enrichment loop (enrichment sessions use the gate
      entry's timeout/max_resumes). Confirm 2.1 passes.

## 3. Model tiers to headless sessions

- [x] 3.1 [req: stage-model-resolution] Add failing tests in
      `test_autopilot.py`: `drive_member` passes `model=None` to
      `session_fn` for an entry declaring `"model": "session"` with no
      anchor, and `model="opus"` for a build entry declaring
      `"model": "tier-below"`; a `session_model="sonnet"` argument shifts
      that resolution to `"haiku"`; the enrichment session receives the gate
      entry's resolved model; with `session_driver.run_turn` monkeypatched,
      `_make_session_fn`'s runner includes `--model opus` in its extra args
      when `model="opus"` is passed and no `--model` when it is None.
- [x] 3.2 [req: stage-model-resolution] In `autopilot.py`: add keyword
      `model=None` to the `session_fn` contract and `_make_session_fn`
      (per-call extra args: base plus `["--model", model]` when set); thread
      `session_model=None` through `drive_member`, `drive_single_member`,
      `run`, and `run_member`; resolve each entry's declared `model` (the
      gate entry's for enrichment) via `sc.resolve_model_tier`; add the
      `--session-model` argparse flag routed to both run modes. Update
      `_Seams` call sites as needed. Confirm 3.1 passes.
- [x] 3.3 [req: stage-model-resolution] Add failing tests in
      `test_autopilot.py`: the dry run prints a `Model tier anchor:` line
      naming the acting anchor (the ladder top when `--session-model` is
      absent), and a run's report dict/JSON carries a `tier_anchor` key.
- [x] 3.4 [req: stage-model-resolution] Implement 3.3 in `autopilot.py`:
      print the anchor line in the `dry_run` branch of `run` and record
      `"tier_anchor"` in the report dict built by `run` and `run_member`.
      Confirm 3.3 passes.

## 4. Prompts and dry-run labels

- [x] 4.1 [req: stage-options-in-prompts] Add failing tests in
      `test_autopilot.py`: the build prompt for `{"stage": "build",
      "validator": false, "telemetry": false, "parallelism": 2,
      "subagent_model": "tier-two-below"}` directs skipping the validator
      phase and telemetry, caps sub-agents at 2, and names the resolved
      sub-agent model with its `tier-two-below` provenance; the review
      prompt for `{"stage": "review", "disposition": "high-only",
      "model": "tier-below"}` carries `--disposition high-only` and
      `--model tier-below` on the poster invocation and directs implementing
      high-severity findings then `review_gate.py autoreply` before
      `resolve`; `disposition` `none` directs autoreplying every finding;
      bare `{"stage": "build"}` and `{"stage": "review"}` prompts equal
      today's optionless renderings; `_entry_label` renders
      `{"stage": "gate", "autopilot": {"attempts": 1}}` and the build/review
      option sets in their labels.
- [x] 4.2 [req: stage-options-in-prompts] Implement in `autopilot.py`:
      `_stage_prompt` appends the declared-option lines for build and
      review (resolving `subagent_model` against the build session's
      resolved model, falling back to the run anchor) and swaps the review
      disposition-loop paragraph by scope; `_entry_label` renders each
      entry's declared option keys. Confirm 4.1 passes.

## 5. Skill sync and shipping

- [x] 5.1 [req: in-session-stage-options] Update
      `plugins/s/skills/autopilot/SKILL.md`: mirror the conditional
      option lines in the verbatim stage instructions ("Running a stage");
      direct spawning a stage's sub-agent with the Agent tool `model`
      parameter resolved relative to the current session when the entry
      declares `model`; state that `autopilot.*` blocks are ignored
      in-session (the human is the retry loop); name `--session-model` and
      the acting anchor in the detached-run confirmation (Phase 3).
- [x] 5.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 5.3 [req: *] Verification barrier: from the repo root run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (the ci
      workflow's invocation) without pydantic installed and confirm the whole
      suite passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Edit | 46 | 39.1k |
| Bash | 82 | 22.0k |
| Write | 8 | 15.4k |
| (no tool) | 0 | 8.1k |
| Read | 19 | 5.2k |
| Agent | 2 | 815 |
| ToolSearch | 1 | 189 |
| **Total** | 158 | 90.8k |
