# tasks

- [x] 1.1 [P1] [req: delta-operation-headers] Add failing tests to `plugins/s/skills/build/tests/` covering the `Dropped:` grammar: `spec_common.parse_requirement_block` exposes a repeatable `Dropped:` line as a list on the parsed `Requirement`, and `render_requirement` omits it, exactly as it omits `base:`, `Reason:` and `Migration:`
- [x] 1.2 [P1] [req: modified-scenario-retention] Add failing tests to `plugins/s/skills/build/tests/test_spec_lint.py` covering all five retention scenarios: a silent omission is an error naming the id and each omitted title; a `Dropped:`-named omission is clean; rewording a scenario body while keeping its title is clean; a `Dropped:` title absent from the base is an error; and a MODIFIED entry whose id has no master is skipped
- [x] 1.3 [P1] [req: modified-operation] Add a failing test asserting `spec_merge.py` writes no `Dropped:` line into the master when merging a MODIFIED entry that carries one
- [x] 2.1 [P2] [req: delta-operation-headers, modified-operation] In `plugins/s/skills/build/scripts/spec_common.py`, add a `dropped` field to `Requirement` (a list, defaulting to empty) alongside `reason` and `migration`, parse repeated `Dropped:` lines into it in `parse_requirement_block`, and leave `render_requirement` emitting only title, `id:` and content so the field never reaches the master. Update the `Requirement` docstring's attribute list
- [x] 2.2 [P2] [req: modified-scenario-retention] In `plugins/s/skills/build/scripts/spec_lint.py`, add a `check_modified_scenario_retention(root, change, errors)` check and call it from the same place the other change-level checks run: for each MODIFIED entry in each delta spec, load the matching master requirement, compare scenario titles, and report one error per omitted title not named in `Dropped:` and one per `Dropped:` title absent from the base. Skip an entry whose id has no master requirement
- [x] 3.1 [req: delta-operation-headers] Document the `Dropped:` line in `.shipd/README.md` alongside the existing `base:` and `Reason`/`Migration` metadata bullets, and show it in the MODIFIED worked example
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` from the repo root and confirm the whole build suite passes
- [x] 3.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.212` to `0.6.213` — AGENTS.md requires every change touching `plugins/s/` to bump the plugin version in the same PR
- [x] 4.1 [req: modified-operation] Complete `spec_merge._clean`'s docstring so its list of withheld delta-only metadata names `Dropped` alongside `base`/`Reason`/`Migration` — the behaviour is already correct and covered by the task 1.3 test; only the prose was left incomplete

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 164 | 57.6k |
| Agent | 4 | 2.3k |
| (no tool) | 0 | 2.1k |
| Edit | 3 | 37 |
| Read | 1 | 3 |
| **Total** | 172 | 62.0k |
