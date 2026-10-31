## 1. Pipeline check defers an unloadable configuration

- [x] 1.1 [req: doctor-pipeline-unloadable-config] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, directly after
      `test_unresolvable_pipeline_carries_the_resolver_error_verbatim`, add
      `test_pipeline_malformed_config_is_ok_carrying_the_error`: create a
      directory under `self.tmp`, write `{not json` to its
      `.shipd-config.json`, call `self.pipeline_check(root)` with no `resolve`,
      and assert the result is `("ok", "pipeline", <detail>)` with `skipped`
      and `not valid JSON` in the detail. Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_shipd_cli.py -k pipeline_malformed_config`
      and observe it fail.
- [x] 1.2 [req: doctor-pipeline-unloadable-config] In the same file, after the
      test from 1.1, add `test_pipeline_unknown_preset_still_fails`: use
      `self.repo_with_config("unknown-preset", {"autonomous-pipeline": "nope"})`,
      call `self.pipeline_check(root)`, and assert level `fail`, name
      `pipeline`, and `nope` in the detail. Run it and observe it pass.
- [x] 1.3 [req: doctor-pipeline-unloadable-config] In `check_pipeline` in
      `plugins/s/bin/shipd`, when `resolve` is `None`: call
      `config, prov = sc.resolve_config(root)` in a `try`; on
      `sc.ConfigError as exc` return `("ok", "pipeline",
      "configuration unresolvable — skipped (%s)" % exc)`; otherwise set
      `resolve = lambda _root: sc.pipeline_from_config(config, prov)`. Leave
      the existing `try` around `resolve(root)` unchanged. Add one docstring
      sentence: an unloadable configuration is reported as the detail rather
      than failing, because the `config` check owns it. Confirm the tests from
      1.1 and 1.2 now pass.
- [x] 1.4 [req: doctor-pipeline-unloadable-config] In
      `plugins/s/.claude-plugin/plugin.json`, change `"version": "0.6.358"` to
      `"version": "0.6.359"`.
- [x] 1.5 [req: *] Run
      `python3 -B -m unittest discover -s plugins/s/skills/build/tests` from the
      repo root and confirm the final line reads `OK`. Then, in a fresh
      temporary git repo whose `.shipd-config.json` holds `{not json`, run
      `python3 -B <repo-root>/plugins/s/bin/shipd doctor` and confirm the
      `pipeline` line begins `ok` and the last line is `doctor: 1 problem(s)`.
      Delete the temporary directory.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 16 | 4.8k |
| SubagentHandback | 2 | 1.3k |
| Agent | 2 | 807 |
| (no tool) | 0 | 286 |
| Monitor | 1 | 76 |
| **Total** | 21 | 7.3k |
