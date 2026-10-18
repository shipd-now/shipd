## 1. The level vocabulary and the stage defaults

- [x] 1.1 [req: stage-model-resolution, pipeline-stage-options, model-ladder-key]
      In `plugins/s/skills/build/tests/test_spec_common.py`, add tests:
      `EFFORT_LEVELS` is exactly `("high", "medium", "low")`; `STAGE_EFFORT`
      maps `plan`/`enrich`/`replan`/`epic` to `high`, `build`/`review` to
      `medium`, and an unknown stage to `low`; `resolve_effort("plan")` is
      `high` and `resolve_effort("build", "low")` is `low`; a concrete id
      passes through; the `models` map and the `model` base resolve; and a
      malformed `models`/`model` raises a `ConfigError` naming the key. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -p 'test_spec_common.py'`
      and observe the new tests fail.
- [x] 1.2 [req: stage-model-resolution, pipeline-stage-options, model-ladder-key]
      In `plugins/s/skills/build/scripts/spec_common.py`, replace
      `DEFAULT_MODEL_LADDER`/`resolve_model_ladder`/`resolve_model_tier` with
      `EFFORT_LEVELS`, `STAGE_EFFORT`, `resolve_effort(stage, declared=None)`,
      `resolve_models(config)` (the per-level map), and `resolve_model_base`
      (the `model` key); add `model` to `RECOGNIZED_CONFIG_KEYS`; and validate
      both keys with a `ConfigError` naming the key and the value. In
      `plugins/s/skills/build/scripts/pipeline_schema.py`, set
      `SYMBOLIC_TIERS = ("session", "high", "medium", "low")` and update the
      `eco`/`basic` preset tiers to `low`/`medium`.

## 2. The runners express a level

- [x] 2.1 [req: stage-model-resolution] In
      `plugins/s/skills/build/tests/test_session_driver.py`, add tests: the
      `claude` runner's argv for the level `high` carries `--effort high` and
      no `--model`; the `opencode` runner's argv for the level `medium` with
      a base model declared carries `--model <base>#medium`, and
      with no base carries no model flag; a concrete id renders `--model
      <id>`; and `session` renders neither. Run the suite and observe failure.
- [x] 2.2 [req: stage-model-resolution] In
      `plugins/s/skills/build/scripts/session_driver.py`, replace the runners'
      `model` argument with `effort` and `model_base`: the `claude` runner
      renders `--effort <level>` for a level and `--model <id>` for a concrete
      id; the `opencode` runner renders `--model <base>#<level>` for a level
      when a base is given, no model flag otherwise, and `--model <id>` for a
      concrete id. `run_turn_result`/`run_turn` take `effort` and `model_base`
      in place of `model`.

## 3. The autopilot resolves levels

- [x] 3.1 [req: stage-model-resolution] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add tests: a stage with
      no `model` resolves to its `STAGE_EFFORT` level; an entry's `model`
      overrides it; the dry run prints the stage levels; the report carries the
      levels and the `models`/`model` config. Run the suite and observe
      failure.
- [x] 3.2 [req: stage-model-resolution] In
      `plugins/s/skills/build/scripts/autopilot.py`, replace the ladder
      resolution with `sc.resolve_effort(stage, entry.get("model"))`, resolve
      the `models` map and the `model` base once per run, thread them to the
      runner, print each stage's level in the dry run, and record the levels
      and config in the report.

## 4. The prose and the format authority

- [x] 4.1 [req: stage-model-resolution, pipeline-grammar-docs] Replace the
      ladder/tier wording with the level wording in
      `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/skills/build/SKILL.md`,
      `plugins/s/harness/bodies/autopilot.md`,
      `plugins/s/harness/references/autopilot.md`,
      `plugins/s/skills/review/references/posting.md`, the content
      directory's `README.md` (the format authority), `docs/customise.md`, and
      the config example.
- [x] 4.2 [req: model-ladder-key] Update `docs/customise.md`'s `models` row to
      the per-level map and add a `model` row for the base. Author through the
      documentation standard and run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/customise.md`.

## 5. Version bump

- [x] 5.1 [req: *] In `plugins/s/.claude-plugin/plugin.json`, change `version`
      from `0.6.326` to `0.6.327`.

## 6. Verify

- [x] 6.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests`,
      `python3 -m unittest discover -s evals/tests`, and
      `python3 -m unittest discover -s plugins/s/skills/review/tests`; all exit
      0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py effort-level-tiers`
      and confirm `OK`. Confirm end to end: a temp repo with no model
      configuration makes `autopilot.py <epic> --dry-run` print `plan: high`,
      `build: medium`, `gate: low`, and `--harness opencode` with no base
      passes no `--model` flag.
