## 1. Config key

- [x] 1.1 [req: merge-config-key] Add `ResolveMergeTest` to `plugins/s/skills/build/tests/test_spec_common.py` (copy `ResolveRoomTest`'s helpers) covering defaults, a partial declaration, a workspace layer governing a member repo, and `ConfigError` for `approvals` true, `approvals` 11, a non-list `required_checks`, a duplicate check, a non-object value, and an unknown member `approvls`; each error message must contain `merge` and the config path. Run it and see it fail.
- [x] 1.2 [req: merge-config-key] In `plugins/s/skills/build/scripts/spec_common.py` add `MERGE_KEY = "merge"`, `DEFAULT_MERGE`, `resolve_merge(root)` after `resolve_room` per plan.md, and add `"merge"` to `RECOGNIZED_CONFIG_KEYS` after `"memory_dir"`. Confirm 1.1 passes.
- [x] 1.3 [req: merge-config-key] Add a `"// merge"` entry to `plugins/s/skills/build/references/shipd.config.example.json` naming the six members and defaults, and a `merge` row to the key table in `docs/customise.md`. Run `test_config_sample.py`.

## 2. Ruleset engine

- [x] 2.1 [req: gate-rules-verb] Create `plugins/s/skills/build/tests/test_merge_rules.py` with a recording fake runner and tests for `desired_ruleset` (body shape per plan.md, empty checks omits the rule), `diff`, create, update-only-owned (list holds `main` plus the owned ruleset; assert no call touches `main`'s id), no-drift writes nothing, duplicate name exits 1, a 403 exits 1 naming admin permission, and the bare report exits 0 with `differs` marks and no write. Run it and see it fail.
- [x] 2.2 [req: gate-rules-verb] Create `plugins/s/skills/build/scripts/merge_rules.py` with the interface in plan.md (`RULESET_NAME`, `gh_run`, `desired_ruleset`, `live_members`, `diff`, `find_owned`, `show`, `apply`, `main`) until 2.1 passes.

## 3. Verb wiring

- [x] 3.1 [req: cli-dispatch, gate-rules-verb] Add `"gate"` to `VERBS` in `plugins/s/skills/build/tests/test_shipd_cli.py` and add tests that `shipd --help` lists `gate`, that `shipd gate` with no or an unknown subverb exits 2 with usage, and that `shipd gate rules --help` exits 0. Run and see them fail.
- [x] 3.2 [req: cli-dispatch, gate-rules-verb] In `plugins/s/bin/shipd` add `_load_merge_rules`, `cmd_gate`, the `gate` line in `USAGE`, the docstring note, and `if verb == "gate": return cmd_gate(rest)` in `main` beside `copilot`. Confirm 3.1 passes.

## 4. Skill and release

- [x] 4.1 [req: gate-rules-consent] In `plugins/s/skills/gate/SKILL.md` add the `Apply merge rules` row to the step 5 table (command `shipd gate rules apply`, preview with bare `shipd gate rules` first), extend step 6's admin note, and add one line to the update flow that it never applies rules.
- [x] 4.2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` by one patch above `main`'s value at build time and run `python3 plugins/s/skills/build/scripts/version_guard.py --base main --head HEAD`.
- [x] 4.3 [req: *] Run the full suite for `plugins/s/skills/build/tests` and confirm no failures.
