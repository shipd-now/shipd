# Tasks — pipeline-schema

## 1. Schema module (test-first)

- [x] 1.1 [req: pipeline-stage-options] Create the pydantic-dependent test
      suite dir `plugins/s/skills/build/tests_pydantic/` with
      `test_pipeline_schema.py`: acceptance tests for the `pipeline_schema`
      module per `plan.md`'s Implementation — every stage form parses; build
      options (`validator`, `telemetry`, `parallelism`, `subagent_model`)
      and review `disposition` accepted; `autopilot` bounds (`attempts >= 1`
      default 3, `timeout > 0`, `max_resumes >= 0`); unknown keys rejected
      on every form; `skip: true` with any other field rejected; tier must
      be a non-empty string with `SYMBOLIC_TIERS == ("session",
      "tier-below", "tier-two-below")`; `validate_entries` dumps
      `exclude_unset` (bare `{"stage": "build"}` round-trips to exactly
      that) and renders errors as `entry <i> (<json>)`-prefixed lines
      covering every offending entry. To run locally: create a venv under
      the session scratchpad, `pip install "pydantic>=2.12,<3"` into it,
      and run `<venv-python> -m unittest discover -s
      plugins/s/skills/build/tests_pydantic -v` — observe failure (the
      module does not exist yet). Never install pydantic into the system
      interpreter.
- [x] 1.2 [req: pipeline-stage-options] Implement
      `plugins/s/skills/build/scripts/pipeline_schema.py` exactly per
      `plan.md`'s Implementation section: `AutopilotOpts`, the tier type,
      the per-stage models (common fields + build/review extras), the
      tools/replace submodels, `CustomStep`, all `extra="forbid"`; the skip
      and tools/replace exclusivity validators; `SYMBOLIC_TIERS`; and
      `validate_entries(raw) -> list[dict]` raising `ValueError` with the
      joined per-entry error lines. Confirm 1.1's suite passes in the venv.

## 2. Resolver wiring (test-first)

- [x] 2.1 [req: pipeline-entry-validation, autonomous-pipeline-key] Migrate
      the declared-pipeline tests out of
      `plugins/s/skills/build/tests/test_spec_common.py` (the
      declared-list, skip, tools, replace, custom, nearest-layer, and all
      validation-error tests of the pipeline test class — everything except
      the registry-constant and absent-key-default tests) into a new
      `plugins/s/skills/build/tests_pydantic/test_resolve_pipeline.py`,
      copying the small `_write_config`/`home_set_to` helpers it needs; add
      an unknown-key rejection test (`{"stage": "plan", "retries": 2}` →
      `ConfigError` naming entry 0 and `retries` — this passes today and
      must keep passing) and an option-acceptance test (`{"stage": "build",
      "validator": false}` resolves, entry carries exactly the declared
      keys). Run in the venv — migrated tests and the unknown-key test pass
      against current behavior; the option-acceptance test fails (the
      hand-rolled validator rejects `validator` as an unexpected key —
      observe that failure).
- [x] 2.2 [req: pipeline-entry-validation] In
      `plugins/s/skills/build/scripts/spec_common.py`, rewrite
      `resolve_pipeline`'s declared branch: keep the list-type check and
      provenance; replace the `_validate_pipeline_entry` loop with a
      function-local `import pipeline_schema` guarded so
      `ModuleNotFoundError` raises `ConfigError` naming pydantic, the
      provenance file, and `pip install -r requirements.txt`; call
      `pipeline_schema.validate_entries(raw)` and re-raise its
      `ValueError` message as `ConfigError`; keep the existing
      canonical-order loop on the returned dicts unchanged; delete
      `_validate_pipeline_entry`, keeping the `PIPELINE_STAGES`,
      `PIPELINE_FALLBACKS`, and `PIPELINE_KEY` exports. Confirm 2.1's venv
      suite is fully green.
- [x] 2.3 [req: pipeline-entry-validation] In
      `plugins/s/skills/build/tests/test_spec_common.py`, delete the
      migrated declared-pipeline tests, keep
      `test_registry_is_canonical_ordered_names` and
      `test_absent_key_yields_full_default`, and add the fail-closed test:
      patch the import machinery (e.g. a `sys.meta_path` hook or
      `builtins.__import__` wrapper) so importing `pipeline_schema` raises
      `ModuleNotFoundError`, then assert a declared pipeline raises
      `ConfigError` whose message names pydantic and
      `pip install -r requirements.txt` — deterministic whether or not
      pydantic is installed. Run the stdlib suite with the system
      interpreter (pydantic absent) and confirm it is green.

## 3. CI and close out

- [x] 3.1 [req: pipeline-entry-validation] In `.github/workflows/ci.yml`,
      add a `Run pydantic-dependent test suite` step directly after the
      `Run textual-dependent test suite` step:
      `python3 -m unittest discover -s
      plugins/s/skills/build/tests_pydantic -v` (the third-party install
      step above it already provides pydantic via `requirements.txt`).
- [x] 3.2 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.3 [req: *] Verify end to end on this machine: the stdlib suite
      passes on the system interpreter (pydantic absent); the
      `tests_pydantic` suite passes under the venv interpreter;
      `python3 plugins/s/skills/build/scripts/spec_status.py pipeline-show`
      on this repo (no declared key) prints the same six-stage
      `[default]` listing as before the change; and a temp directory with
      `.shipd-config.json` declaring
      `{"autonomous-pipeline": [{"stage": "build", "validator": false}]}`
      run through `spec_status.py --root <tmp> pipeline-show` (system
      interpreter) fails closed naming pydantic, while the same resolution
      under the venv interpreter succeeds.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 68 | 29.1k |
| Write | 6 | 26.0k |
| Edit | 13 | 7.9k |
| Read | 14 | 6.1k |
| (no tool) | 0 | 2.7k |
| SendMessage | 1 | 1.4k |
| Agent | 2 | 797 |
| **Total** | 104 | 74.0k |
