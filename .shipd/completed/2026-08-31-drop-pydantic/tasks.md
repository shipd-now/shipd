## 1. Stdlib validator

- [x] 1.1 [req: pipeline-entry-validation] Move
      `plugins/s/skills/build/tests_pydantic/test_pipeline_schema.py`,
      `test_resolve_pipeline.py`, and `test_pipeline_show.py` into
      `plugins/s/skills/build/tests/` with `git mv`, and delete the now-empty
      `tests_pydantic/` directory. In each moved file, remove the module
      docstring's claim that the suite requires pydantic and lives outside the
      stdlib suite, and delete any `import pydantic`. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and record
      which of the 98 moved tests fail — they are the contract task 1.2 must
      satisfy.
- [x] 1.2 [req: pipeline-entry-validation, pipeline-presets] Rewrite
      `plugins/s/skills/build/scripts/pipeline_schema.py` stdlib-only: delete
      every `pydantic` import and every model class, and build a table-driven
      validator keeping the module's public names `SYMBOLIC_TIERS`, `PRESETS`,
      `validate_entries(raw)`, and `expand_preset(name)` with unchanged
      signatures and return shapes. Declare one key table per entry form
      (`research`, `epic`, `plan`, `gate`, `build`, `review`, `custom`) over
      the shared stage keys `skip`, `tools`, `replace`, `model`, `autopilot`
      plus build's `subagent_model`, `validator`, `telemetry`, `parallelism`
      and review's `disposition`, exactly as the current models declare them.
      Enforce: unknown keys rejected; no type coercion, testing `bool` before
      `int` so `{"skip": 1}` and `{"parallelism": true}` both fail; bounds
      `attempts >= 1`, `timeout > 0`, `max_resumes >= 0`, `parallelism >= 1`;
      non-empty `tools` list each with a `name` and a `fallback` of `builtin`
      or `skip`; `replace` naming a `command` or a `tool` plus a `fallback`;
      `custom` matching `spec_common.KEBAB_RE` with a non-empty `command`;
      `skip` true-only and exclusive of every other field; `tools` and
      `replace` mutually exclusive. Keep the `entry <i> (<sorted-json>):
      <path>: <message>` error line shape and report every offending entry.
      Return each entry carrying only the keys its author declared. Confirm
      the tests from 1.1 now pass.
- [x] 1.3 [req: pipeline-entry-validation] In
      `plugins/s/skills/build/scripts/spec_common.py`, delete the
      `try: import pipeline_schema / except ModuleNotFoundError: raise
      ConfigError(... requires pydantic ...)` block in `resolve_pipeline`
      (currently around line 569), leaving a plain lazy `import
      pipeline_schema`, and update the function docstring and the
      `PIPELINE_PRESETS` comment above it to stop naming pydantic.
- [x] 1.4 [req: pipeline-show-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, delete the same
      fail-closed pydantic branch in the `--expand` preset helper (currently
      around line 1897–1912) and update its docstring to stop naming pydantic.

## 2. Remove the dependency surface

- [x] 2.1 [req: doctor-verb] In `plugins/s/skills/build/tests/test_shipd_cli.py`,
      delete `test_declared_pipeline_without_pydantic_fails_naming_the_config`
      and the whole pydantic block of `DoctorCheckTest` (the
      `pydantic_check` helper, `PYDANTIC_HINT`, and every `test_pydantic_*`
      method), retarget the requirements-hint and externally-managed-hint
      assertions onto `textual`, and add a test asserting `shipd doctor` emits
      no line naming `pydantic` in a repo declaring an `autonomous-pipeline`
      list. Run the file and observe the new test fail.
- [x] 2.2 [req: doctor-verb] In `plugins/s/bin/shipd`, delete `check_pydantic`
      and `_pipeline_needs_pydantic`, remove the `check_pydantic(root)` entry
      from the checks list (currently line 878), and drop the `"pydantic"` key
      from `PINNED_SPECIFIERS`. Confirm the tests from 2.1 pass.
- [x] 2.3 [req: *] In `requirements.txt`, delete the `pydantic>=2.12,<3` line
      and update the header comment so it names only the delivery board's
      `tui` as the third-party surface and lists only the two remaining mirror
      sites for the textual range.
- [x] 2.4 [req: *] In `.github/workflows/ci.yml`, delete the
      `Run pydantic-dependent test suite` step and rename the
      `Install third-party deps (board tui + pipeline validation)` step to
      name the board tui only.
- [x] 2.5 [req: *] In `.shipd/constitution.md`, reduce the technology
      constraint to a single named exception — `textual` for `dashboard.py`'s
      `tui` — deleting the pydantic clause and the "two named exceptions"
      wording. Make the matching edit to `AGENTS.md`'s "The engine's two
      third-party dependencies" section, retitling it for one dependency.

## 3. Documentation and verification

- [x] 3.1 [req: pipeline-follower-docs] Remove the pydantic
      prose from `README.md` (line 315, the declared-pipeline sentence) and
      `docs/quickstart.md` (the doctor check list at line 52, and the
      dependency notes at lines 55, 60, and 131), so neither names pydantic
      and the doctor list matches the shipped checks.
- [x] 3.2 [req: plan-pipeline-resolution, interactive-pipeline-resolution] In `plugins/s/skills/plan/SKILL.md` (line 35) and
      `plugins/s/skills/build/SKILL.md` (line 98), drop "or a missing
      pydantic" from the pipeline-resolution paragraph and replace the quoted
      example error with one the rewritten validator actually emits for
      `{"stage": "build", "validater": false}`, copied from a real run.
- [x] 3.3 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`, delete the `warn pydantic` /
      `fail pydantic` remedy row (line 86) and remove `pydantic` from the
      check list at line 63. In `plugins/s/harness/bodies/doctor.md` (line
      30), drop `warn|fail pydantic` from the finding list.
- [x] 3.4 [req: *] With pydantic uninstallable or blocked from import, run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm all tests pass — including the three suites moved in 1.1, whose
      `test_pipeline_show.py` cases must now pass under the isolated `HOME`
      that previously hid a `--user`-installed pydantic from the subprocess.
- [x] 3.5 [req: *] Confirm no pydantic references remain outside
      `.shipd/completed/`: run `grep -rn pydantic . --exclude-dir=.git
      --exclude-dir=completed` and check every remaining hit is in an
      archived change. Then run `plugins/s/bin/shipd doctor` and confirm no
      `pydantic` line appears and the `pipeline` line still reports.
- [x] 3.6 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.164` to `0.6.165`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 37 | 23.3k |
| **Total** | 37 | 23.3k |
