## 1. /s:build pipeline resolution and honoring

- [x] 1.1 [req: interactive-pipeline-resolution] In
      `plugins/s/skills/build/SKILL.md`, add a "Resolve the pipeline"
      step to Phase 0 (before the readiness evaluation): run
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py"
      pipeline-show` once; on non-zero exit report the engine's error and
      stop the flow; read declared options from the rendered entry labels
      and never re-derive them from config; state that `autopilot` blocks,
      `replace` bindings, custom steps, the build entry's own `model`, and
      a `skip` on the explicitly invoked stage are ignored interactively,
      and that stage-option instructions conveyed by a driving invoker's
      prompt supersede self-resolution.
- [x] 1.2 [req: interactive-pipeline-resolution] In the same SKILL.md's
      "Model policy" section and Phase 3, honor a declared
      `subagent_model`: spawn `s:sub-agent` workers with the Agent tool's
      `model` set per the session-relative table (mirror the autopilot
      SKILL's table verbatim — `session` omits the parameter;
      `tier-below`/`tier-two-below` step down the ladder `fable` → `opus`
      → `sonnet` → `haiku`, clamped at `haiku`; anything else passes
      verbatim), falling back to the existing one-tier-below policy when
      undeclared; and give the Phase 3 fan-out cap the precedence
      pipeline `parallelism` > the `parallelism` config key > 3.
- [x] 1.3 [req: adversarial-validation-gates-verified] In the same
      SKILL.md Phase 5, condition step 5 on the resolved build entry:
      when it declares `validator` false, do not spawn `s:validator` and
      allow `set-status verified` on mechanical verification alone (tasks
      complete, suite green, re-lint clean); when a validator does spawn,
      its `model` follows the resolved `subagent_model` (same tier as
      executors).
- [x] 1.4 [req: standard-end-of-build-report, interactive-pipeline-resolution]
      In the same SKILL.md Phases 6-7, when the resolved build entry
      declares `telemetry` false: skip the Phase 6 per-tool token
      breakdown persist into `tasks.md`, skip Phase 7 step 1's
      `TOKENS`/`TABLE` generation, and print the report without the token
      summary, per-model table, and total-runtime line (first line
      `Build complete. <summary sentence>`); keep the change header,
      warnings, description, and Observations, and leave the step-2
      build-log append unchanged (best-effort).
- [x] 1.5 [req: ship-changes-as-prs] In the same SKILL.md Phase 6 (the
      gate-posting instructions around `mergeStateStatus`), pass the
      resolved review entry's declared `disposition` and `model` to the
      `/s:review` post flow (its "Review stage options") and follow that
      flow's matching scoped disposition loop, including on every re-post
      after a new head; when the resolved pipeline skips or omits the
      `review` stage, post no gate and let the Phase 7 watch surface a PR
      blocked on a still-required check as a blocker.

## 2. /s:plan pipeline resolution

- [x] 2.1 [req: plan-pipeline-resolution] In
      `plugins/s/skills/plan/SKILL.md`, add a pipeline-resolution step to
      the flow's start (with the version announcement): run
      `pipeline-show` via the status CLI; on non-zero exit report the
      engine's error and stop (add this to the "What still stops the
      flow" list); when a config layer declares the pipeline, include the
      resolved provenance (e.g. `preset:eco (<config-path>)`) in the
      first status sentence, and add no announcement for `[default]`
      provenance; document that the plan entry's `model` and all
      `autopilot` blocks are ignored interactively and that the ending's
      context-gate promotion runs unchanged whatever the pipeline's gate
      entry declares.

## 3. Close-out

- [x] 3.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump), since this
      change touches `plugins/s/`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest
      discover -s plugins/s/skills/build/tests -q` and confirm it passes
      without pydantic or textual installed (no engine script changed),
      and run `python3 plugins/s/skills/build/scripts/spec_lint.py
      interactive-pipeline` and confirm exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 132 | 48.0k |
| (no tool) | 0 | 19.7k |
| Edit | 19 | 12.5k |
| Agent | 9 | 6.7k |
| Read | 35 | 6.0k |
| SendMessage | 3 | 2.3k |
| ToolSearch | 4 | 602 |
| **Total** | 202 | 95.8k |
