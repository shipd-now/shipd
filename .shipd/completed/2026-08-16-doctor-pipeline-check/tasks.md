## 1. Pipeline check in the doctor (engine)

- [x] 1.1 [req: doctor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`'s `DoctorCheckTest`,
      add failing tests for `shipd.check_pipeline`: (a) a tmp repo with no
      `autonomous-pipeline` key (HOME redirected, per `config_check`'s
      pattern) returns `("ok", "pipeline", ...)` with `default` in the
      detail; (b) a tmp repo declaring an entry list on an interpreter
      without pydantic returns `("fail", "pipeline", ...)` whose detail
      contains ``requires pydantic`` and the config path; (c) an injected
      `resolve=lambda root: ([{"stage": "plan"}], "preset:eco (<path>)")`
      returns `ok` naming the entry count and provenance; (d) an injected
      `resolve` raising `shipd.sc.ConfigError("boom")` (call
      `shipd._load_engine()` first) returns `fail` with detail `boom`. Run
      the class and observe the new tests fail.
- [x] 1.2 [req: doctor-verb] In `plugins/s/bin/shipd`, add
      `check_pipeline(root, resolve=None)` next to `check_config`: call
      `_load_engine()`, default `resolve` to `sc.resolve_pipeline`, and
      return `("ok", "pipeline", "resolves: <n> entries (source:
      <provenance>)")` on success (provenance string used verbatim;
      `default` when undeclared) or `("fail", "pipeline", str(exc))` on
      `sc.ConfigError`. Confirm the 1.1 tests pass.
- [x] 1.3 [req: doctor-verb] In the same test file, convert the existing
      `check_pydantic` tests to the new `check_pydantic(root, find_spec=...)`
      signature (a tmp repo with no declaration as `root`) and add failing
      tests for the pydantic escalation and ordering: (a) a tmp repo
      declaring an
      entry list with `find_spec=lambda name: None` makes
      `shipd.check_pydantic(root, ...)` return `("fail", "pydantic", ...)`
      naming the config path and the `pip install -r requirements.txt`
      hint; (b) the same with `"autonomous-pipeline": "default"` stays
      `("warn", "pydantic", ...)`; (c) an unknown preset string stays
      `warn`; (d) no declaration stays `warn` with the existing text; (e)
      importable pydantic stays `ok` regardless of declaration; (f) update
      the `default_checks` ordering test to the sequence python, git,
      config, pipeline, gh, textual, pydantic, snapshot, statusline. Run
      and observe them fail.
- [x] 1.4 [req: doctor-verb] In `plugins/s/bin/shipd`, add
      `_pipeline_needs_pydantic(root)` (resolve via `sc.resolve_config`,
      return the supplying config path when the `autonomous-pipeline`
      value is a list or a string in `sc.PIPELINE_PRESETS` other than
      `"default"`, else `None`; swallow `sc.ConfigError` as `None`),
      change `check_pydantic` to `check_pydantic(root,
      find_spec=importlib.util.find_spec)` implementing the
      warn/fail branching per the delta, and update `default_checks(root)`
      to the nine-check order with `check_pipeline(root)` after
      `check_config(root)`, `check_pydantic(root)` in place, and
      `check_statusline()` staying last. Confirm the 1.3 tests pass.
- [x] 1.5 [req: doctor-verb] Run the full engine suite
      `python3 -m unittest discover -s plugins/s/skills/build/tests` on an
      interpreter without pydantic installed and confirm it passes.

## 2. Skill and follower surfaces

- [x] 2.1 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`: add `pipeline` to step 2's check
      enumeration (after `config`); reword the remedy table's pydantic row
      to cover `warn pydantic` and the escalated `fail pydantic` with the
      same `python3 -m pip install "pydantic>=2.12,<3"` command; add a
      `fail pipeline` row marked report-only (never edit
      `.shipd-config.json`; when the detail names missing pydantic, point
      at the pydantic row's remedy instead of proposing a config edit).
- [x] 2.2 [req: doctor-verb] In `docs/quickstart.md`'s doctor step (around
      line 45), extend the check list to `python`, `git`, `config`,
      `pipeline`, `gh`, `textual`, `pydantic`, `snapshot`, `statusline`
      (insert `pipeline` after `config` in the existing list), keeping
      the existing pydantic and statusline notes.
- [x] 2.3 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.118 to 0.6.119
      (standing convention: every change touching `plugins/s/` bumps the
      plugin version).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 15 | 7.4k |
| Agent | 1 | 3.9k |
| WebSearch | 5 | 2.6k |
| (no tool) | 0 | 2.3k |
| WebFetch | 2 | 2.3k |
| Read | 1 | 242 |
| **Total** | 24 | 18.8k |
