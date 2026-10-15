## 1. Session driver result text

- [x] 1.1 [req: session-turn-result-text] In
      `plugins/s/skills/build/tests/test_session_driver.py`, after
      `RunTurnTest` (line 117), add `ResultTextTest`:
      `result_text_from_transcript('{"result": "x"}') == "x"`, `"not json"`
      → `""`, `'{"result": 3}'` → `""`; write an executable fake binary in a
      temp dir (`#!/bin/sh` + `printf '%s' '<transcript json>'`, mode
      `0o755`) printing `{"session_id": "s1", "result": "{\"mode\":
      \"change\"}"}` and assert `run_turn_result("p", tmp, claude_bin=fake)`
      returns `(True, None, "s1", '{"mode": "change"}')` and
      `run_turn("p", tmp, claude_bin=fake)` returns `(True, None, "s1")`;
      a missing cwd makes `run_turn_result` return `ok` false with `""` as
      the text. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_session_driver` and observe the
      failures.
- [x] 1.2 [req: session-turn-result-text] In
      `plugins/s/skills/build/scripts/session_driver.py`: add
      `result_text_from_transcript(text)` after `session_id_from_transcript`
      (line 47); rename the body of `run_turn` (line 78) into
      `run_turn_result(...)` returning `(ok, failure, session_id,
      result_text)` with `""` on every failure path, and make `run_turn`
      return `run_turn_result(...)[:3]`; update the module docstring's entry
      points. Re-run 1.1 until it passes.

## 2. Pre-build helpers

- [x] 2.1 [req: detached-pre-build-drift] In
      `plugins/s/skills/build/tests/test_autopilot.py`, after
      `GateEnrichmentTest`, add `PreBuildHelpersTest(unittest.TestCase)`:
      `_sync_base_ref` with a fake whose `git rev-parse --verify --quiet
      origin/main` returns rc 0 → `"origin/main"` and whose first recorded
      call is `["git", "fetch", "origin", "main"]`; rc 1 → `"main"`;
      `_parse_drift_verdict` on a plain object `{"verdicts": [{"member":
      "m", "verdict": "revise", "reason": "r", "contradicts": null,
      "revise": "tasks 2.x"}], "clean": [], "error": null}` →
      `("revise", "r", None, "tasks 2.x")`; the same wrapped in a
      ```` ```json ```` fence, and preceded by a prose line, → the same
      tuple; `{"clean": ["m"], "verdicts": [], "error": null}` → verdict
      `holds`; `error` set, no entry for `m`, verdict word `maybe`, and empty
      text → `ValueError`; `_drift_summary({"findings": [{"kind":
      "file-drift"}, {"kind": "file-drift"}, {"kind": "symbol-gone"}]})` →
      `"file-drift 2, symbol-gone 1"`; `_drift_prompt("m", "origin/main")`
      contains `/s:drift m --base origin/main --json`; `_stage_prompt(
      "replan", "m", {}, drift={"base_ref": "origin/main", "reason": "r",
      "revise": "tasks", "summary": "file-drift 1"})` contains `r`, `tasks`,
      `origin/main`, `s:oracle`, `USER`, `spec_gate.py`, and `--root`;
      `_session_extra_args(None)` is `["--plugin-dir", autopilot.PLUGIN_DIR,
      "--permission-mode", "bypassPermissions"]` and `_session_extra_args(
      "claude-x")` appends `["--model", "claude-x"]`. Run and observe the
      failures.
- [x] 2.2 [req: detached-pre-build-drift] In
      `plugins/s/skills/build/scripts/autopilot.py`, add a "Pre-build drift
      step (epic-autopilot detached-pre-build-drift)" section after
      `_tier_anchor` (line 699) holding `_session_extra_args(model)`,
      `_make_judge_fn(claude_bin)` (one `session_driver.run_turn_result`
      call, firing `on_session` when a session id arrives, returning
      `(ok, session_id, failure, text)`), `_sync_base_ref(command_fn, root)`,
      `_drift_prompt(member, base_ref)`, `_parse_drift_verdict(text,
      member)`, `_drift_summary(payload)`, and `_replan_prompt(member,
      drift)`, each as `plan.md` "Implementation" specifies; make
      `_make_session_fn` build `extra` from `_session_extra_args(model)` and
      grade `replan` with `_plan_grade` beside `plan`/`enrich`; add the
      `drift=None` keyword to `_stage_prompt` with a `replan` branch calling
      `_replan_prompt`. Re-run 2.1 until it passes.

## 3. The step in drive_member

- [x] 3.1 [req: detached-pre-build-drift] In `test_autopilot.py`, extend
      `_Seams.__init__` (line 541) with `session_replan=None`, `drift=(0,
      "", "")`, `judge=None`, `completed=()`; give the seam's `gate_fn` a
      `base=None` keyword and record it with each `gate_calls` entry; make `command_fn` answer a
      list command whose fourth element is `"drift"` with `self.drift`, a
      `["git", "ls-tree", ...]` command with one `.shipd/completed/001-<s>`
      line per slug in `completed`, and record every call as today; route
      stage `replan` to `session_replan` in `session_fn`; add
      `judge_fn(self, member, cwd, prompt, timeout, model=None,
      on_session=None)` recording `(member, prompt)` in `self.judgements`,
      counting attempts, firing `on_session`, and returning `judge(n)` when
      given else `(True, "sess-drift-%d" % n, None, <holds JSON for member>)`;
      pass `judge_fn=self.judge_fn` from `drive`. Add module helper
      `_verdict_json(member, verdict, reason="r", contradicts=None,
      revise=None)`. Add `PreBuildDriftTest(AutopilotTestBase)` with the
      `PGB` pipeline: (a) default seams → `shipped`, sessions `["plan",
      "build"]`, no judgement, and `s.commands` holds `["git", "merge",
      "--no-edit", "origin/main"]` in `<root>/.worktrees/m` followed by
      `[sys.executable, <SCRIPTS_DIR>/spec_status.py, "--root", <worktree>,
      "drift", "m", "--base", "origin/main", "--json"]` in the worktree,
      the fetch recorded in `root`; (b) `drift=(4, json.dumps({"findings":
      [{"kind": "file-drift"}]}), "")` with the default judge → `shipped`,
      one judgement whose prompt contains `/s:drift m --base origin/main
      --json`; (c) judge returning `conflict` with `contradicts="Q2"` →
      `needs_human`, stage `drift`, reason containing `Q2` and `r`,
      `session_id == "sess-drift-1"`, no build session; (d) judge `revise`
      with `revise="tasks 2.x"` and default gate → `shipped`, sessions
      `["plan", "replan", "build"]`, the replan prompt containing `r`,
      `tasks 2.x`, `s:oracle`, `USER`, `spec_gate.py`, `--base origin/main`,
      `len(s.gate_calls) == 2` with the second call's `base ==
      "origin/main"`; (e) `gate_rcs=[0, 2]` with `revise` → outcome `rejected`, stage
      `replan`, `session_id == "sess-replan-1"`, no build; (f) a judge
      failing on attempt 1 (`(False, None, "connection closed", "")`) then
      returning a fenced holds object → two judgements, `shipped`; (g) a
      judge returning `(True, "sess-drift-%d", None, "not json")` every time
      → `needs_human`, stage `drift`, reason containing `3 attempts`, no
      build; (h) `drift=(1, "", "Error: no Planned-at")` → `needs_human`,
      stage `drift`, reason containing `exit 1` and `no Planned-at`, no
      judgement; (i) a command fake making `git merge --no-edit` return rc 1
      → `["git", "merge", "--abort"]` recorded in the worktree and
      `needs_human` at stage `sync`; (j) `_member()` with `after=["a"]` and
      `completed=()` → `needs_human`, stage `dependency`, reason containing
      `a` and `origin/main`, no merge, drift, or build command; with
      `completed=("a",)` → `shipped`; (k) pipeline with `{"stage": "build",
      "replace": {"command": "echo x"}}` and with `{"stage": "build",
      "skip": true}` → no drift command recorded; (l)
      `drive_single_member` on a planted `ready` member with
      `judge_fn=s.judge_fn` → the drift command precedes the build session.
      Run and observe the failures.
- [x] 3.2 [req: detached-pre-build-drift] In `autopilot.py`: add
      `_pre_build_step(root, member, cwd, entry, knobs, command_fn,
      session_fn, judge_fn, gate_fn, out, hook, on_sess)` returning
      `(outcome, stage, reason, session_id)` per `plan.md` (`knobs` is the
      `(attempts, timeout, resumes, model)` tuple; strike-loop labels
      `drift` and `replan`; `_merged_into_base(command_fn, root, dep)` for
      the dependency check; the re-gate runs `_run_gate(lambda m, c:
      gate_fn(m, c, base=ref), ...)`, and `_default_gate_fn(member, cwd,
      base=None)` appends `["--base", base]` when given); add `judge_fn=None` to `drive_member` and
      `drive_single_member`, defaulting to `_make_judge_fn(claude_bin)`;
      in `drive_member`'s loop, when `stage == "build"` is built-in, call
      the step before building the prompt: `proceed` falls through,
      `needs_human` sets `last_session_id` when given and returns
      `_park(stage, reason)`, `rejected` returns `_finish(MemberResult(
      outcome="rejected", stage=stage, reason=reason,
      session_id=session_id))`, and a vanished worktree after the step
      resolves through `_resolve_vanished(..., "build", ...)`; add a module
      docstring paragraph on the step. Re-run 3.1 until it passes and
      the whole `test_autopilot.py` module stays green.

## 4. The run continues past a parked dependency

- [x] 4.1 [req: detached-dependent-continue] In `test_autopilot.py`
      `RunTest`, add tests with `_make_epic(self.root, "ep", [("a", "low"),
      ("b", "low")], after={"b": ["a"]})` and a `member_driver` recording
      slugs: a driver parking `a` as `needs_human` → calls `["a"]`, and
      `report["needs_human"]` holds `b` with `stage == "dependency"`,
      reason containing `a` and `needs_human`, `session_id` `None`; a
      driver shipping `a` → calls `["a", "b"]`; a driver returning
      `drafted` for `a` → `b` at stage `dependency` and
      `_summarize(report, ...)` prints a `needs-human: b` line without
      `claude --resume`; a `_SnapshotHeartbeat`-style read of the heartbeat
      file shows `b` in state `needs-human`. Run and observe the failures.
- [x] 4.2 [req: detached-dependent-continue] In `autopilot.py` `run`
      (line 1210): keep `outcomes = {}`; before `member_driver`, compute
      `waiting = [(d, outcomes[d]) for d in member.after if d in outcomes
      and outcomes[d] != "shipped"]`; when non-empty build
      `MemberResult(outcome="needs_human", stage="dependency",
      reason="waiting on %s" % ", ".join("%s (%s)" % w for w in waiting))`,
      call `hb.member_finished(member.slug, result)`, `out("Member %s: not
      driven — %s" ...)`, and record it as the member's result; append every
      result to `outcomes[member.slug] = result.outcome` before the
      existing bucket logic. Re-run 4.1 until it passes.

## 5. Version and verification

- [x] 5.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      to the next patch above the value on `main` at build time (`0.6.293`
      when this plan was written; rebase and re-bump if a sibling member
      landed first).
- [x] 5.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests` from the worktree root and confirm every test passes;
      then run `python3 plugins/s/skills/build/scripts/autopilot.py
      autopilot-preflight --dry-run` and confirm it still prints the member
      order and pipeline and drives nothing.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 91 | 1.5k |
| (no tool) | 0 | 948 |
| ToolSearch | 2 | 714 |
| SubagentHandback | 4 | 63 |
| Agent | 4 | 40 |
| TaskStop | 1 | 12 |
| **Total** | 102 | 3.3k |
