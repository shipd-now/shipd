## 1. Engine: `pipeline-show --json`

- [x] 1.1 [req: pipeline-show-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`'s
      `PipelineShowTest`, add three stdlib-only tests: (a) `pipeline-show
      --json` with no declared key parses as one JSON object with `source`
      equal to `"default"` and `entries` equal to
      `[{"stage": s} for s in sc.PIPELINE_STAGES]`; (b) `pipeline-show
      --expand default --json` output equals the flagless
      `--expand default` output (same JSON array); (c) flagless
      `pipeline-show` output is unchanged (starts with
      `pipeline (source: [default]):` and lists the six stages). Run the
      class and observe the new tests fail — the flag does not exist yet.
- [x] 1.2 [req: pipeline-show-verb] In
      `plugins/s/skills/build/tests_pydantic/test_pipeline_show.py`, add
      three tests following that file's existing declared-config fixtures:
      (a) with `{"autonomous-pipeline": "eco"}` declared, `pipeline-show
      --json` parses as one object whose `source` starts with `preset:eco`
      and names the config path, and whose `entries` build entry carries
      `subagent_model` `"tier-two-below"`, `validator` `False`, and
      `telemetry` `False`; (b) with a declared custom list carrying a
      skipped gate, `--json` `entries` include `{"stage": "gate", "skip":
      true}` and `source` is the config file path; (c) with a declared
      entry naming an unknown stage, `pipeline-show --json` exits non-zero
      printing the validation error to stderr, matching the flagless form.
      Run them and observe the new tests fail.
- [x] 1.3 [req: pipeline-show-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`: apply
      `_add_json_flag` to the `p_pipeline_show` subparser; change
      `cmd_pipeline_show(root, expand=None)` to
      `cmd_pipeline_show(root, expand=None, as_json=False)` and pass
      `as_json=args.json` from `main`. With `as_json` and no `expand`,
      print `json.dumps({"source": provenance, "entries": entries},
      indent=2)` where `provenance` is the raw value `sc.resolve_pipeline`
      returned (no `[default]` decoration); with `as_json` and `expand`,
      print exactly what the flagless expand prints (the indented entry
      array). Leave every error path (`StatusError` raising) untouched.
      Confirm the tests from 1.1 now pass, and the 1.2 tests pass with
      pydantic installed (`pip install -r requirements.txt`).
- [x] 1.4 [req: pipeline-show-verb] In the same file, update the module
      docstring's `pipeline-show` usage line to read
      `pipeline-show [--expand PRESET] [--json]` and describe the JSON
      object (`source` + `entries`); amend the "five read verbs" JSON
      paragraph to also name `pipeline-show`; reword `_add_json_flag`'s
      docstring so it no longer claims only the five read verbs get the
      flag; and extend `p_pipeline_show`'s `--expand`/`--json` help text
      accordingly.

## 2. Skill consumers move to the JSON contract

- [x] 2.1 [req: interactive-pipeline-resolution] In
      `plugins/s/skills/build/SKILL.md` step 1 ("Resolve the pipeline —
      once, at flow start"): change the command to `... spec_status.py
      pipeline-show --json`, and replace the "The rendered labels are the
      API" bullet with a "The JSON is the contract" bullet: read each
      entry's declared options from the emitted object's `entries` dicts,
      read the provenance from `source` (`"default"` means no layer
      declared one and changes nothing), and never parse the
      human-rendered label lines, which remain display-only. Keep the
      non-zero-exit stop rule, the honored/ignored option lists, and the
      conveyed-options precedence unchanged.
- [x] 2.2 [req: plan-pipeline-resolution] In
      `plugins/s/skills/plan/SKILL.md`'s "Resolve the pipeline in the same
      breath" block: change the command to `pipeline-show --json`, state
      that the provenance is the object's `source` field (announce it when
      it is not `"default"`; a `"default"` source announces nothing), and
      leave the non-zero-exit stop rule and the ignored-options paragraph
      unchanged. Do not alter the "What still stops the flow" bullet's
      meaning.
- [x] 2.3 [req: in-session-stage-options] In
      `plugins/s/skills/autopilot/SKILL.md`'s "Stage options declared by
      the resolved entry" section: replace the instruction to read options
      from the dry run's entry labels with running
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py"
      pipeline-show --json` once per run and reading each entry's declared
      options from the object's `entries` dicts; state that the dry run
      remains the source of the member order only and its labels are
      human-facing. Keep Phase 1 step 3's flagless `pipeline-show` display
      and every option-semantics rule (model table, autopilot-block
      ignore, build/review prompt lines) unchanged.
- [x] 2.4 [req: in-session-stage-options] In
      `plugins/s/skills/build/scripts/autopilot.py`, reword
      `_entry_label`'s docstring to drop "— which the in-session drive
      parses —": the dry-run labels are human-facing display only. No
      behavioral change.

## 3. `/s:status pipeline` route

- [x] 3.1 [req: interactive-status-skill] In
      `plugins/s/skills/status/SKILL.md`: add a fourth command mapping —
      `/s:status pipeline` runs `python3
      "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py"
      pipeline-show` and relays its output verbatim; `/s:status pipeline
      <preset>` runs `pipeline-show --expand <preset>` and relays that
      output (an unknown preset relays the CLI's error listing the known
      presets — that listing is the discovery answer, not a skill
      failure). Mention the pipeline report in the frontmatter
      description's command list.

## 4. Version bump and verification

- [x] 4.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.119` to `0.6.120`
      (if a concurrent merge already moved it, bump one patch above the
      current value).
- [x] 4.2 [req: *] Verification barrier: run `python3 -m unittest
      discover -s plugins/s/skills/build/tests -v` (must pass without
      pydantic installed) and, with `pip install -r requirements.txt`
      applied, `python3 -m unittest discover -s
      plugins/s/skills/build/tests_pydantic -v`; confirm both suites pass
      and `python3 plugins/s/skills/build/scripts/spec_status.py
      pipeline-show` output is byte-identical to its pre-change rendering.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 87 | 28.0k |
| Edit | 23 | 12.9k |
| (no tool) | 0 | 6.5k |
| Read | 21 | 2.8k |
| Agent | 2 | 1.0k |
| **Total** | 133 | 51.2k |
