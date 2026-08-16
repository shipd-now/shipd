# Tasks — pipeline-presets

## 1. Preset names and resolver string form (test-first)

- [x] 1.1 [req: pipeline-presets, autonomous-pipeline-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add stdlib preset
      tests (using the suite's existing config-writing and import-blocking
      helpers, with the `pipeline_schema` import blocked so they prove the
      no-pydantic guarantees): `spec_common.PIPELINE_PRESETS ==
      ("default", "eco", "basic")`; a repo config declaring
      `{"autonomous-pipeline": "default"}` resolves to the six bare
      registry stages with provenance `preset:default (<config-path>)`;
      declaring `"ecoo"` raises `ConfigError` naming `ecoo`, the config
      path, and the known presets `basic`, `default`, `eco` (and not
      pydantic); declaring `"eco"` raises the fail-closed `ConfigError`
      naming pydantic and `pip install -r requirements.txt`; declaring the
      number `7` raises `ConfigError` naming the key and the accepted
      list-or-preset-string forms. Run the stdlib suite on the system
      interpreter (pydantic absent) and observe the new tests fail.
- [x] 1.2 [req: pipeline-presets] In
      `plugins/s/skills/build/tests_pydantic/test_resolve_pipeline.py`, add
      venv tests: a repo config declaring `"eco"` resolves to exactly the
      eco entry list from `plan.md`'s Implementation (research/epic
      `{"skip": true}`, plan `{"model": "session"}`, gate
      `{"autopilot": {"attempts": 1}}`, build `{"validator": false,
      "subagent_model": "tier-two-below", "telemetry": false}`, review
      `{"model": "tier-below", "disposition": "high-only"}`) with
      provenance `preset:eco (<config-path>)`; `"basic"` resolves to the
      basic list likewise; `pipeline_schema.PRESETS` keys equal
      `spec_common.PIPELINE_PRESETS`; and every `PRESETS` list passes
      `pipeline_schema.validate_entries` and resolves through
      `resolve_pipeline` without error. To run locally: venv under the
      session scratchpad with `pip install "pydantic>=2.12,<3"`, then
      `<venv-python> -m unittest discover -s
      plugins/s/skills/build/tests_pydantic -v`; observe the new tests
      fail. Never install pydantic into the system interpreter.
- [x] 1.3 [req: pipeline-presets, autonomous-pipeline-key] Implement the
      resolver side: in `plugins/s/skills/build/scripts/spec_common.py`,
      export `PIPELINE_PRESETS = ("default", "eco", "basic")` beside
      `PIPELINE_STAGES`, and extend `resolve_pipeline` with the string
      branch per `plan.md`'s Implementation (unknown-name check first with
      no import; `"default"` short-circuit stdlib-only with
      `preset:default (<path>)` provenance; other known names through the
      existing lazy-import guard); update the non-list error message to
      "must be a JSON list or a preset name string". In
      `plugins/s/skills/build/scripts/pipeline_schema.py`, add the
      `PRESETS` table (its `"default"` entry built from
      `spec_common.PIPELINE_STAGES`) and `expand_preset(name)` returning
      `validate_entries(PRESETS[name])`. Confirm 1.1 (system interpreter)
      and 1.2 (venv) are green.

## 2. pipeline-show options rendering and --expand (test-first)

- [x] 2.1 [req: pipeline-show-verb] Add the show-side tests: in
      `plugins/s/skills/build/tests/test_spec_status.py` (stdlib suite),
      `pipeline-show --expand default` prints indented JSON that
      `json.loads` to the six bare stage entries and exits 0 with pydantic
      absent, and `pipeline-show --expand turbo` exits non-zero naming
      `turbo` and listing `basic`, `default`, `eco`; in
      `plugins/s/skills/build/tests_pydantic/test_pipeline_show.py` (venv),
      on a repo declaring `"eco"` the output's source line contains
      `preset:eco` and the config path, the build line contains
      `validator=false`, `subagent_model=tier-two-below`, and
      `telemetry=false`, the gate line contains `autopilot.attempts=1`,
      the review line contains `model=tier-below` and
      `disposition=high-only`, and the research line renders as skipped;
      and `pipeline-show --expand eco` prints JSON whose parsed value
      passes `pipeline_schema.validate_entries` and equals
      `pipeline_schema.PRESETS["eco"]`. Observe the new tests fail.
- [x] 2.2 [req: pipeline-show-verb] Implement in
      `plugins/s/skills/build/scripts/spec_status.py`: add
      `--expand <preset>` to the `pipeline-show` subparser (around line
      2505) and an expansion branch in `cmd_pipeline_show` per `plan.md`'s
      Implementation (`default` from `sc.PIPELINE_STAGES` with no import;
      known names via a lazy `pipeline_schema` import whose
      `ModuleNotFoundError` becomes the install-hint `StatusError`;
      unknown names a `StatusError` listing `sc.PIPELINE_PRESETS`;
      `json.dumps(entries, indent=2)`); extend `_format_pipeline_entry`
      (line 1599) with the options suffix (`model`, `subagent_model`,
      `validator`, `telemetry`, `parallelism`, `disposition` as
      `key=value` with lowercase booleans, `autopilot` sub-keys as
      `autopilot.<key>=<value>`, joined with `", "`, two spaces after the
      form label; no options, no suffix). Confirm 2.1 is green on both
      interpreters and that `python3
      plugins/s/skills/build/scripts/spec_status.py pipeline-show` on this
      repo still prints the pre-change six-stage `[default]` listing
      byte-identically.

## 3. Docs and close out

- [x] 3.1 [req: pipeline-presets] Document the string form: in
      `.shipd/README.md`'s "The autonomous pipeline" section (lines
      183-224), add the preset name form — `default`, `eco`, `basic`, one
      name or one list never both, unknown names rejected, `"default"`
      equal to the absent key, eco/basic requiring pydantic — and name
      `pipeline-show --expand <preset>` as the fork path; in the repo-root
      `README.md` autonomous-pipeline paragraph (lines 176-183), add one
      sentence that the key also accepts a built-in preset name and that
      `pipeline-show --expand` prints a preset as a custom-list starting
      point.
- [x] 3.2 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.3 [req: *] Verify end to end on this machine: the stdlib suites
      (`tests/`) pass on the system interpreter with pydantic absent; the
      `tests_pydantic` suite passes under the venv interpreter; a temp
      directory whose `.shipd-config.json` declares
      `{"autonomous-pipeline": "eco"}` fails closed naming pydantic via
      `spec_status.py --root <tmp> pipeline-show` on the system
      interpreter and prints the option-annotated eco pipeline with source
      `preset:eco` under the venv interpreter; the same temp config with
      `"default"` succeeds on the system interpreter; and
      `pipeline-show --expand eco` (venv) output pasted as the
      `autonomous-pipeline` value in a temp config resolves to the same
      entries as the preset name itself.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 75 | 24.4k |
| Edit | 18 | 17.0k |
| (no tool) | 0 | 4.8k |
| Read | 18 | 2.7k |
| Agent | 2 | 1.7k |
| **Total** | 113 | 50.6k |
