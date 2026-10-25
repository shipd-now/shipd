## 1. Failing tests

Tests that need the plugin installed write, under the isolated `HOME`,
`.claude/plugins/installed_plugins.json` as `{"version": 2, "plugins":
{"s@shipd": [{"scope": "user"}]}}` and `.claude/settings.json` as
`{"enabledPlugins": {"s@shipd": true}}`. Put one helper for this in each
test file that needs it.

- [x] 1.1 [req: registry-plugin-provided] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, add a test
      that `hr.PLUGIN_PROVIDED == {"claude-code": "s@shipd"}` and every key
      is in `hr.ids()`.
- [x] 1.2 [req: harness-plugin-provided] In
      `plugins/s/skills/build/tests/test_harness_generate.py`, add a
      `PluginProvidedTest(ActionTestCase)` covering the four scenarios of
      requirement `harness-plugin-provided` in
      this change's harness-verb delta spec, driving the binary through `self.cli`.
      For the project-scope scenario use three sub-cases: `scope`
      `project`, `enabledPlugins` `false`, and an `installed_plugins.json`
      holding `not json`.
- [x] 1.3 [req: harness-status] In the same file's `StatusTest`, add the
      scenario `Status reports a plugin-provided surface`: write owned files
      with `add claude-code --user` before installing the plugin helper,
      then install it, check `stale`, run `add claude-code --user`, check
      `skipped`.
- [x] 1.4 [req: install-plugin-provided] In
      `plugins/s/skills/build/tests/test_install_tui.py`
      `InstallSelectionTest`, add the two scenarios of requirement
      `install-plugin-provided`. Run the three test files and observe the
      new tests fail.

## 2. Implementation

- [x] 2.1 [req: registry-plugin-provided] In
      `plugins/s/skills/build/scripts/harness_registry.py`, after
      `LEGACY_USER_PATTERNS`, add `PLUGIN_PROVIDED = {"claude-code":
      "s@shipd"}` with the comment from plan.md's Registry data bullet.
- [x] 2.2 [req: harness-plugin-provided] In
      `plugins/s/skills/build/scripts/harness_generate.py`, add
      `plugin_installed(plugin_id)` and `plugin_provided(entry, mode)` per
      plan.md's Detection bullets, reading `~/.claude/plugins/
      installed_plugins.json` and `~/.claude/settings.json` with `json` and
      returning `False` on `OSError`, `ValueError`, or any other shape.
- [x] 2.3 [req: harness-plugin-provided] In `harness_generate.py` `add`,
      split off provided entries before `planned`, then after the legacy
      removal report each as skipped and retire its owned
      `surface_paths(entry, mode)` files, pruning emptied directories with
      `_prune(directory, _boundaries(mode, root))`, per plan.md's `add`
      bullet.
- [x] 2.4 [req: harness-status] In `harness_generate.py` `status`, report
      a provided entry as `stale` or `skipped` with the details, `expected`,
      and `present` from plan.md's `status` bullet.
- [x] 2.5 [req: install-plugin-provided] In
      `plugins/s/skills/build/scripts/install_tui.py` `install_selection`,
      pass provided entries to `hg.add` and report each with the `provided`
      line from plan.md's `install_selection` bullet. Run the three test
      files and confirm they pass.

## 3. Docs and version

- [x] 3.1 [req: harness-plugin-provided] In `docs/customise.md` `## The
      harness`, add one paragraph: with the `s@shipd` plugin installed at
      user scope and enabled, `shipd install` and `shipd harness add
      claude-code --user` write no Claude Code command or agent files,
      because the plugin already provides `/s:*`, and they retire the copies
      shipd wrote earlier.
- [x] 3.2 [req: harness-plugin-provided] In
      `docs/harness-agents-reference.md`, under the Claude Code row's
      commands block, add one sentence that the user-global agent files are
      skipped and retired while the `s@shipd` plugin is installed.
- [x] 3.3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.348` to the next patch version.

## 4. Verification

- [x] 4.1 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests -p 'test_harness*.py'` and the same for
      `test_install_tui.py`, and grep the output for `OK`.
- [x] 4.2 [req: *] On the build machine, count `ls ~/.claude/commands/shipd
      | wc -l`, and from an empty scratch directory made with `mktemp -d`
      run `claude -p "/context" --output-format json --max-turns 1` and
      save its `result` field. Run `plugins/s/bin/shipd harness add
      claude-code --user`, then count and read `/context` again the same
      way. Record for the PR body both file counts, the Skills category
      total before and after, and that no `shipd:*` row remains in the
      after reading's per-skill table (plan.md's Proof bullet). Touch no
      ceiling file.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 66 | 29.7k |
| SubagentHandback | 3 | 2.8k |
| Agent | 5 | 2.3k |
| Monitor | 3 | 758 |
| Skill | 2 | 541 |
| ToolSearch | 1 | 154 |
| (no tool) | 0 | 152 |
| **Total** | 80 | 36.4k |
