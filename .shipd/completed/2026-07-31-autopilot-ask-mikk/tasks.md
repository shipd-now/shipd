# Tasks — autopilot-ask-mikk

## 1. Oracle-aware reply and build prompt

- [x] 1.1 [req: oracle-aware-driven-sessions] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add failing tests:
      `autopilot.GOAHEAD_REPLY` contains `s:oracle`, the compact-question
      shape (decision/options/recommendation), `ANSWER`, and `INSUFFICIENT`;
      and `autopilot._stage_prompt("build", "m", {})` contains `s:oracle`
      and `QUESTION:`. Run them and observe them fail.
- [x] 1.2 [req: oracle-aware-driven-sessions] In
      `plugins/s/skills/build/scripts/autopilot.py`, replace the
      `GOAHEAD_REPLY` text and append the sub-agent `QUESTION:` oracle-routing
      paragraph to the build branch of `_stage_prompt`, both with the binding
      texts from `plan.md` `## Implementation`. Tests from 1.1 pass.

## 2. Oracle-backed enrichment on gate rejection

- [x] 2.1 [req: oracle-gate-enrichment] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add a failing test:
      with an injected `gate_fn` returning exit 2 then 0 and an injected
      `session_fn` recording stages, `drive_member` runs exactly one
      `"enrich"` session (its prompt naming `/s:plan` for the member and
      `s:oracle`), calls the gate twice, and the member proceeds through
      build to a `shipped` outcome.
- [x] 2.2 [req: oracle-gate-enrichment] Add a failing test: with `gate_fn`
      returning exit 2 on both calls, the member's result is
      `outcome="rejected"`, `stage="gate"`, a reason naming the enrichment,
      and `session_id` set from the enrich session — and only one enrich
      session ran.
- [x] 2.3 [req: oracle-gate-enrichment] Add failing tests: an enrich
      `session_fn` failure (ok False) parks the member `rejected` (not
      needs-human) with the failure appended to the reason and the session id
      recorded; and when the worktree vanishes during the enrich session with
      a merged PR, `_resolve_vanished` records the member `shipped`.
- [x] 2.4 [req: oracle-gate-enrichment, pipeline-stage-execution] In
      `plugins/s/skills/build/scripts/autopilot.py`, implement the gate
      branch of `drive_member` per `plan.md` `## Implementation`: heartbeat
      hook label `"enrich"`, one `session_fn("enrich", ...)` call with a new
      `"enrich"` branch in `_stage_prompt`, gate re-run deciding
      continue/park, `rejected` parking with reason + session id, vanished
      resolution, and an `"enrich"` → `_plan_grade` mapping in
      `_make_session_fn`. Tests from 2.1–2.3 pass.

## 3. Report and summary carry the enrichment session id

- [x] 3.1 [req: run-report-and-controls] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add failing tests:
      a `rejected` member's report entry includes its `session_id`, and the
      summary line for a rejected member with a session id includes
      `claude --resume <id>`.
- [x] 3.2 [req: run-report-and-controls] In
      `plugins/s/skills/build/scripts/autopilot.py`, include `session_id`
      in `report["rejected"]` entries in `run`, and make `_summarize` append
      the resume pointer to rejected lines carrying an id. Tests from 3.1
      pass.

## 4. Deliver skill wording and plugin version

- [x] 4.1 [req: deliver-skill] In `plugins/s/skills/deliver/SKILL.md`,
      update Phase 3's parking sentence to note the single oracle-backed
      enrichment attempt between gate rejection and the `rejected` park, and
      Phase 4's rejected bullet to note the failed automatic enrichment, keep
      the `/s:plan <member>` recovery pointer, and print
      `claude --resume <session-id>` when the report carries an enrichment
      session id.
- [x] 4.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.9 to 0.6.10.

## 5. Verify

- [x] 5.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the repo root and confirm the whole suite passes.
