## 1. Tests first

- [x] 1.1 [req: merged-dependency-check] In
      `plugins/s/skills/build/tests/test_autopilot.py`, extend `_FakeGit`: add
      a `toplevel=None` constructor argument and answer
      `["git", "rev-parse", "--show-toplevel"]` with rc 0 and `self.toplevel`,
      or `os.path.dirname(cwd)` when it is `None`; keep `fail_all` answering
      rc 1 for every call. In `_Seams.command_fn`, answer the same argv with
      rc 0 and `os.path.dirname(cwd)`.
- [x] 1.2 [req: merged-dependency-check] In `MergedIntoBaseTest` in
      `plugins/s/skills/build/tests/test_autopilot.py`: in
      `test_date_prefixed_entry_is_merged`, replace the all-cwd assertion with
      one that the `ls-tree` call's cwd is `self.root`. Replace
      `test_git_failure_is_not_merged` with three tests: `fail_all=True`
      raises `autopilot.AutopilotError` naming the content directory;
      `refs=()` returns `False` without raising; a fake whose `ls-tree`
      answers `(128, "", "fatal: not a tree")` raises `AutopilotError` whose
      message carries `a` and `fatal: not a tree`.
- [x] 1.3 [req: merged-dependency-check] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add
      `ExternalStoreDependencyTest`: in a temp directory write
      `.shipd-config.json` holding `{"store_root": "specs"}`, `git init -b
      main` a `code` repository with one empty commit, and `git init -b main`
      a `specs` repository. Under the directory
      `sc.specs_dir(<code>)` returns, create the `completed` directory, an
      entry directory named `2026-01-01-change-a` inside it, and a `plan.md`
      inside that; commit it. Assert
      `autopilot._merged_into_base(autopilot._run_command, <code>, "change-a")`
      is true and the same call for `change-z` is false. Add a second test
      with `specs` as a plain directory (no `git init`) asserting
      `AutopilotError`. Pass `-c user.name=t -c user.email=t@t` on each
      commit.
- [x] 1.4 [req: member-wave-scheduling] In the waves test class of
      `plugins/s/skills/build/tests/test_autopilot.py` (beside
      `test_unmerged_dependency_blocks_a_build_wave`), add a test that
      `compute_waves` with `command_fn=_FakeGit([], fail_all=True)` and a ready
      member `b` after ready `a` raises `autopilot.AutopilotError`.
- [x] 1.5 [req: merged-dependency-check] In the pre-build test class of
      `plugins/s/skills/build/tests/test_autopilot.py` (beside
      `test_unmerged_dependency_parks_before_the_sync`), add two tests using
      `_Seams` with a member after `a`. First: a `command_fn` whose `ls-tree`
      answers `(128, "", "fatal: not a tree")` parks `needs_human` at stage
      `dependency`, the reason carries `fatal: not a tree`, and no
      `git merge` command was recorded. Second: with
      `autopilot.sc.store_root_dir` patched to return a path and
      `autopilot.sc.store_sync_enabled` patched to return `True`, exactly two
      `["git", "fetch", "origin", "main"]` commands are recorded, the second
      with cwd `sc.specs_dir(root)`, and the waiting reason carries
      `in the store repository`.
- [x] 1.6 [req: *] Run `python3 -B -m unittest tests.test_autopilot` from
      `plugins/s/skills/build` and observe the new tests fail.

## 2. Implementation

- [x] 2.1 [req: merged-dependency-check] In
      `plugins/s/skills/build/scripts/autopilot.py`, add
      `_dependency_base(command_fn, root)` directly above
      `_merged_into_base`, exactly as the plan's `## Implementation` first
      decision specifies.
- [x] 2.2 [req: merged-dependency-check] In
      `plugins/s/skills/build/scripts/autopilot.py`, rewrite
      `_merged_into_base` to the signature and behaviour of the plan's second
      decision, including its docstring.
- [x] 2.3 [req: merged-dependency-check] In
      `plugins/s/skills/build/scripts/autopilot.py`, add
      `_sync_store_ref(command_fn, root)` directly below `_sync_base_ref`, per
      the plan's fourth decision.
- [x] 2.4 [req: merged-dependency-check] In `_pre_build_step` in
      `plugins/s/skills/build/scripts/autopilot.py`, apply the plan's fifth
      decision: call order, the `AutopilotError` park, and the waiting
      reason. Update the function's docstring to name the store fetch.
- [x] 2.5 [req: member-wave-scheduling] In the `compute_waves` docstring in
      `plugins/s/skills/build/scripts/autopilot.py`, add one sentence: a
      failed merged-dependency check raises `AutopilotError`.
- [x] 2.6 [req: *] Run `python3 -B -m unittest tests.test_autopilot` from
      `plugins/s/skills/build`; grep the output for `OK` or `FAILED` and
      repair any fake that still lacks the `--show-toplevel` answer until it
      prints `OK`.

## 3. Documentation and version

- [x] 3.1 [req: member-wave-scheduling] In
      `plugins/s/skills/autopilot/SKILL.md`, in the paragraph starting
      "The `blocked` array", insert the words "of the repository that
      tracks the content directory" directly before ", never from a
      worktree". Rewrap the
      paragraph so the file's line count does not grow.
- [x] 3.2 [req: merged-dependency-check] In
      `docs/workspaces/nesting-and-stores.md`, add a level-3 section
      `### Dependencies between epic members` directly above
      `### Known limitations`. State in at most four sentences: autopilot
      reads an `After` dependency from the store repository's base branch
      (the remote-tracking `main`, else the local `main`); a dependent releases once that branch
      carries the dependency's `completed/` entry; push the store to release
      dependents; a store outside any git work tree makes the check fail with
      an error.
- [x] 3.3 [req: *] In `plugins/s/.claude-plugin/plugin.json`, raise the patch
      component of `version` by one.
- [x] 3.4 [req: *] From `plugins/s/skills/build`, run
      `python3 -B -m unittest discover -s tests` and grep the output for `OK`
      or `FAILED`; fix any failure this change caused.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 47 | 22.5k |
| SubagentHandback | 4 | 5.6k |
| Write | 2 | 5.6k |
| Agent | 3 | 1.8k |
| Edit | 3 | 1.2k |
| SendMessage | 2 | 1.0k |
| (no tool) | 0 | 930 |
| Read | 6 | 879 |
| ToolSearch | 2 | 693 |
| Monitor | 1 | 377 |
| **Total** | 70 | 40.7k |
