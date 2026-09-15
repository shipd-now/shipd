## 1. Config keys and their resolution

- [x] 1.1 [req: worktree-sweep-keys] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests for three new
      accessors — `worktree_sweep(config)`, `worktree_idle_minutes(config, env)`,
      `worktree_stale_days(config, env)` — covering a declared layer value, an
      environment value overriding it, a malformed value falling back to the
      default, and the defaults `true` / `30` / `7`. Run them and observe them
      fail: the accessors do not exist yet.
- [x] 1.2 [req: worktree-sweep-keys] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `"worktree_idle_minutes"`, `"worktree_sweep"`, and `"worktree_stale_days"`
      to `RECOGNIZED_CONFIG_KEYS` (keeping the tuple alphabetical) and add the
      module constants for their key names and defaults beside
      `COMPLETED_RETENTION_KEY`.
- [x] 1.3 [req: worktree-sweep-keys] In the same file, implement the three
      accessors beside `completed_retention_days`, following its tolerance
      pattern: a wrong type, a boolean where an integer is expected, or an
      out-of-range value yields the built-in default rather than raising. The
      two integer accessors read their environment variable first
      (`SHIPD_WORKTREE_IDLE_MINUTES`, `SHIPD_WORKTREE_STALE_DAYS`) and fall
      through to the config layer, then the default. Confirm 1.1 passes.
- [x] 1.4 [req: worktree-sweep-keys] In
      `plugins/s/skills/build/references/shipd.config.example.json`, add a
      `"// worktree_sweep"`, `"// worktree_idle_minutes"`, and
      `"// worktree_stale_days"` entry documenting each key's meaning and
      default, matching the surrounding entries' voice. Run
      `plugins/s/skills/build/tests/test_config_sample.py` and confirm the
      registry/reference agreement check passes in both directions.

## 2. Surfacing the settings through config-show

- [x] 2.1 [req: config-show-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests asserting
      `config-show` prints `worktree-sweep: true`, `worktree-idle-minutes: 30`,
      and `worktree-stale-days: 7` on a default-only resolution, and prints the
      declared values when a repo layer declares `worktree_sweep` false and
      `worktree_stale_days` 14. Run them and observe them fail.
- [x] 2.2 [req: config-show-verb] In `cmd_config_show` in
      `plugins/s/skills/build/scripts/spec_status.py`, print the three keyed
      lines after the existing `wiki:` line, reading each value through the
      accessors added in 1.3. Print them unconditionally, unlike the
      declaration-gated `store:` line. Confirm 2.1 passes.

## 3. The sweep verb in worktree.sh

- [x] 3.1 [req: worktree-sweep-verb] In
      `plugins/s/skills/build/tests/test_worktree.py`, add a `SweepTest` class
      following `PruneBranchesTest`'s fixture style, covering: a merged
      guard-clean worktree is swept; a worktree whose branch is zero commits
      ahead of the base is untouched and unreported; a merged worktree carrying
      an unshipped planned change and a `[~]` claim is kept with both reasons; a
      clean unmerged worktree with an old branch tip yields a `stale:` line and
      survives; the same worktree with a recent tip yields a `kept:` line and no
      `stale:` line; a merged branch with no worktree is pruned in the same run;
      `--dry-run` prints the same lines and changes nothing; and a detached root
      HEAD removes nothing and exits zero. Run them and observe them fail.
- [x] 3.2 [req: worktree-sweep-verb] In
      `plugins/s/skills/build/scripts/worktree.sh`, extract the four guard
      probes currently inline in `cmd_remove` into a
      `collect_remove_reasons <worktree> <change>` helper that populates the
      `reasons` array and prints nothing, and rewrite `cmd_remove` to call it.
      Keep every guard's behavior byte-identical and confirm the existing
      `RemoveWorktreeTest` suite still passes.
- [x] 3.3 [req: worktree-sweep-verb, worktree-sweep-keys] In the same file, add a
      `resolve_worktree_settings` helper that reads `worktree-sweep:`,
      `worktree-idle-minutes:`, and `worktree-stale-days:` from
      `spec_status.py config-show` with the same `sed -n 's/^<key>: //p'` idiom
      the content-dir resolution already uses, falling back to `true`, `30`, and
      `7` on any failure. Use its idle value in `cmd_remove` in place of the
      current environment-only read, keeping `SHIPD_WORKTREE_IDLE_MINUTES` as
      the higher-precedence override.
- [x] 3.4 [req: worktree-sweep-verb] In the same file, implement `cmd_sweep`:
      resolve the base branch, iterate `.worktrees/*/`, skip any worktree whose
      branch is not ahead of the base (`branch_counts`), judge merged-ness with
      `branch_is_merged` then `branch_remote_ref_gone`, run
      `collect_remove_reasons` on merged candidates, and emit `swept:`,
      `kept:`, or `stale:` lines. Compare branch tips against the stale window
      with `git log -1 --format=%ct` and `date +%s`. Then call
      `cmd_prune_branches`, and return 0 unconditionally. A detached root HEAD
      reports that no base resolves and skips both passes. Keep the file bash
      3.2-safe: no `mapfile`, no associative arrays.
- [x] 3.5 [req: worktree-sweep-verb] In the same file, add `--dry-run` handling
      to `cmd_sweep` so it prints its full report while performing no
      `git worktree remove` and no branch deletion, add `sweep` to the
      subcommand dispatch beside `remove` and `prune-branches`, and extend
      `usage()` with its line. Confirm 3.1 passes.

## 4. Engine dispatch and the opportunistic call

- [x] 4.1 [req: engine-worktree-create] In
      `plugins/s/skills/build/tests/test_worktree_engine.py`, add tests
      asserting `worktree.py sweep --dry-run` reproduces `worktree.sh`'s output
      and exit code; that a create run removes a merged guard-clean worktree
      while leaving the newly created one in place; that a create run in a
      detached-HEAD repository still creates the worktree and exits zero; and
      that a configuration declaring `worktree_sweep` false runs no sweep and
      prints no sweep output. Run them and observe them fail.
- [x] 4.2 [req: engine-worktree-create] In
      `plugins/s/skills/build/scripts/worktree.py`, add `"sweep"` to
      `PASSTHROUGH_VERBS` and to the `usage()` text, and extend the module
      docstring's dispatch list to name it alongside `remove` and
      `prune-branches`.
- [x] 4.3 [req: engine-worktree-create] In `cmd_create` in the same file, after
      the post-worktree scripts have run, call `worktree.sh sweep` when
      `worktree_sweep` resolves true, capturing its output and printing only the
      `swept:` and `pruned:` lines. Discard its exit code so the create path's
      own return value is unchanged under every sweep outcome. Confirm 4.1
      passes.

## 5. Documentation

- [x] 5.1 [req: worktree-sweep-verb] In `AGENTS.md`, extend the "After merge"
      paragraph to name `worktree.sh sweep` as the verb that reclaims merged
      worktrees and their branches together, and state that the engine's
      worktree create path runs it automatically unless `worktree_sweep` is
      declared false.

## 6. Verification

- [x] 6.1 [req: *] Run the full engine test suite under
      `plugins/s/skills/build/tests/` and confirm it passes with no new
      failures. Then run `worktree.sh sweep --dry-run` from this repository's
      root and confirm the report names the merged leftover branches and leaves
      every worktree in place.
- [x] 6.2 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` to the next patch version, as every
      change touching `plugins/s/` must, so the cached plugin snapshot picks the
      change up.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 152 | 53.6k |
| Edit | 31 | 51.0k |
| Read | 43 | 24.3k |
| Agent | 2 | 1.6k |
| (no tool) | 0 | 1.5k |
| SendMessage | 1 | 779 |
| ToolSearch | 1 | 601 |
| **Total** | 230 | 133.4k |
