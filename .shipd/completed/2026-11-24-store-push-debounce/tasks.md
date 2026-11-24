## 1. Delay key

- [x] 1.1 [req: store-push-delay-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests for a new
      `sc.store_push_delay(config)`: `{}` gives 60, `{"store_push_delay": 5}`
      gives 5, `0` gives 0, and `"soon"`, `-1`, `True` each give 60. In
      `plugins/s/skills/build/tests/test_config_registry.py`, add the
      `store_push_delay` row (scope `repo`) to the expected table and a
      validation case rejecting `"soon"`. Run both files and observe failures.
- [x] 1.2 [req: store-push-delay-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `STORE_PUSH_DELAY_KEY = "store_push_delay"`,
      `DEFAULT_STORE_PUSH_DELAY = 60`, the key in the recognized-keys list
      beside `store_sync`, and `store_push_delay(config)` returning the
      declared value only when it is an `int`, not a `bool`, and `>= 0`.
- [x] 1.3 [req: store-push-delay-key] In
      `plugins/s/skills/build/scripts/config_registry.py`, add a
      `store_push_delay` row after `store_autocommit`, scope `repo`, with a
      validator accepting only a non-negative non-bool integer and the
      expected text `a non-negative integer of seconds; 0 pushes at once`.
- [x] 1.4 [req: store-push-delay-key] In
      `plugins/s/skills/build/references/shipd.config.example.json`, add a
      `// store_push_delay` comment entry after `// store_sync`: "Seconds the
      delayed store push waits after the last store commit. A non-negative
      integer; default `60`. `store_sync` false turns the push off." Run
      `test_config_sample.py`, `test_config_registry.py` and the 1.1 tests;
      all pass.

## 2. Integrate routine in the helper

- [x] 2.1 [req: store-sync-hook] In
      `plugins/s/skills/workspace/tests/test_store_sync.py`, replace
      `test_divergent_upstream_warns_and_changes_nothing` with three tests
      matching the delta scenarios "A divergent upstream is rebased and
      pushed", "A conflicting rebase aborts and warns", and "Uncommitted work
      survives the rebase". Run the file and observe the three fail.
- [x] 2.2 [req: store-sync-hook] In
      `plugins/s/skills/build/scripts/spec_common.py`, rename
      `_store_commit_lock` to `store_commit_lock` and update its caller in
      `wiki_autocommit`, the docstring reference, and the one use in
      `plugins/s/skills/build/tests/test_spec_common.py`.
- [x] 2.3 [req: store-sync-hook] In
      `plugins/s/skills/workspace/scripts/store_sync.py`, make `_run` pass an
      environment copy with `GIT_TERMINAL_PROMPT=0`, and add
      `integrate(store)` exactly as the plan's "One integrate routine"
      decision states, using `git merge-base --is-ancestor` for the two
      ancestor checks and `spec_common.store_commit_lock(store)` around the
      merge or rebase. Make `sync_session_start` call `integrate(store)` then
      push. Update the module docstring. Run the file's tests; all pass.

## 3. Delayed mode in the helper

- [x] 3.1 [req: store-push-debounce] In
      `plugins/s/skills/workspace/tests/test_store_sync.py`, add tests that
      run `store_sync.py --delayed <store> --delay 0` against a clone of a
      bare remote: an unpushed commit reaches the remote; a diverged store is
      rebased and pushed; a store with no `origin` exits 0. Add a test that
      starts one helper with `--delay 2`, then a second with `--delay 0`, and
      asserts the first exits 0 after the second rewrote the token file.
      Observe failures.
- [x] 3.2 [req: store-push-debounce] In
      `plugins/s/skills/workspace/scripts/store_sync.py`, add the delayed
      mode: when `sys.argv` carries `--delayed <store> --delay <n>`, read no
      stdin, write the token as the plan's "Debounce by token" decision
      states, sleep `<n>` seconds, exit 0 when the token file no longer
      holds this helper's token, and otherwise skip silently unless the
      store is inside a git work tree with an `origin` remote, then run
      `integrate(store)` and `git push`. Wrap everything fail-soft; always
      exit 0. Run the file's tests; all pass.

## 4. Engine scheduling

- [x] 4.1 [req: store-push-debounce] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests patching
      `subprocess.Popen`: `wiki_autocommit` in a store with an `origin`
      remote starts one helper whose argv ends
      `--delayed <store> --delay 60`; no helper starts with no remote, with
      `store_sync` false, with `schedule_push=False`, or when no commit was
      made; a `Popen` raising `OSError` still returns True. Add one
      end-to-end test with a bare remote and `store_push_delay` 0 asserting
      the remote receives the commit within ten seconds. Observe failures.
- [x] 4.2 [req: store-push-debounce] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `schedule_store_push(store_dir, config)` and the `schedule_push=True`
      keyword on `wiki_autocommit`, per the plan's first two Implementation
      decisions. Call it after a successful commit, outside the lock.
- [x] 4.3 [req: store-push-debounce] Pass `schedule_push=not personal` at
      the personal-capable call sites: `emit_wiki` in
      `plugins/s/skills/build/scripts/spec_emit.py`, and
      `_wiki_write_autocommit` in
      `plugins/s/skills/build/scripts/spec_status.py`, which gains a
      `schedule_push=True` keyword that its `--personal` callers set false.
      Run the 4.1 tests; all pass.

## 5. Workspace artifact commits

- [x] 5.1 [req: workspace-artifact-autocommit] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add tests for the
      delta scenarios covering PRD and initiative emits; in
      `plugins/s/skills/build/tests/test_spec_status.py`, add the
      status-change scenario. Observe failures.
- [x] 5.2 [req: workspace-artifact-autocommit] In
      `plugins/s/skills/build/scripts/spec_emit.py`, call
      `sc.wiki_autocommit(ws_root, [dest_dir], <subject>,
      config_anchor=root)` after `_install_dir` in `emit_prd` and
      `emit_initiative`, with the subjects the plan names.
- [x] 5.3 [req: workspace-artifact-autocommit] In
      `plugins/s/skills/build/scripts/spec_status.py`, call
      `sc.wiki_autocommit(<workspace root>, [path], "shipd: initiative
      <slug> status <status>", config_anchor=root)` after
      `write_initiative_status` in `cmd_initiative_sync` and
      `cmd_initiative_set_status`. Run the 5.1 tests; all pass.

## 6. Docs, version, verification

- [x] 6.1 [req: workspaces-doc-store-push] Through `/s:document`, revise
      `docs/workspaces/teams.md`, `docs/customise.md`, and
      `docs/workspaces/external-stores.md` to satisfy every scenario of the
      requirement, then fix every documentation lint finding.
- [x] 6.2 [req: *] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json` by one.
- [x] 6.3 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -B -m unittest discover -s
      plugins/s/skills/workspace/tests`; grep each output for `OK` or
      `FAILED` and fix any failure.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 104 | 52.2k |
| Write | 2 | 9.2k |
| SubagentHandback | 4 | 6.4k |
| Edit | 6 | 2.8k |
| Agent | 3 | 1.8k |
| SendMessage | 2 | 865 |
| ToolSearch | 3 | 579 |
| (no tool) | 0 | 425 |
| Read | 2 | 368 |
| Monitor | 1 | 290 |
| Skill | 1 | 173 |
| TaskStop | 1 | 59 |
| **Total** | 129 | 75.2k |
