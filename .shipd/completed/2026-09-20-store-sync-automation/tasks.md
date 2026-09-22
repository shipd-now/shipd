## 1. The two config keys

- [x] 1.1 [req: store-sync-keys] In `plugins/s/skills/build/tests/test_spec_common.py`,
      add tests for `spec_common.store_autocommit_enabled(config)` and
      `spec_common.store_sync_enabled(config)`: each returns True on an
      undeclared key, returns the declared boolean, and falls back to True on a
      non-boolean value. Run them and observe them fail — neither function
      exists yet.
- [x] 1.2 [req: store-sync-keys] In `plugins/s/skills/build/scripts/spec_common.py`,
      beside `WORKTREE_SWEEP_KEY` (around line 424), add the constants
      `STORE_AUTOCOMMIT_KEY = "store_autocommit"`,
      `DEFAULT_STORE_AUTOCOMMIT = True`, `STORE_SYNC_KEY = "store_sync"`, and
      `DEFAULT_STORE_SYNC = True`.
- [x] 1.3 [req: store-sync-keys] In the same file, add `"store_autocommit"` and
      `"store_sync"` to `RECOGNIZED_CONFIG_KEYS` (around line 388), keeping the
      tuple alphabetically ordered.
- [x] 1.4 [req: store-sync-keys] In the same file, beside `worktree_sweep`
      (around line 551), add `store_autocommit_enabled(config)` and
      `store_sync_enabled(config)`, each returning the built-in default for a
      non-boolean value rather than raising. Confirm the tests from 1.1 pass.
- [x] 1.5 [req: store-sync-keys] In
      `plugins/s/skills/build/references/shipd.config.example.json`, add a
      `"// store_autocommit"` and a `"// store_sync"` comment entry, each
      naming what the key gates and its `true` default. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -k config_sample`
      and confirm it passes.

## 2. The auto-commit gate and its lock

- [x] 2.1 [req: wiki-autocommit, store-autocommit] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests that a
      resolved configuration declaring `store_autocommit` false makes
      `wiki_autocommit` return False with no commit made, and that two
      sequential locked calls each land their own scoped commit. Run them and
      observe the gate test fail.
- [x] 2.2 [req: wiki-autocommit] In
      `plugins/s/skills/build/scripts/spec_common.py`, add a module-level
      `_store_commit_lock(store_dir)` context manager taking an exclusive
      `fcntl.flock` on a lock file in the system temp directory, named
      `shipd-store-<first 16 hex of sha256 of the store's absolute path>.lock`,
      so no file is ever created inside the store. Import `fcntl` inside a
      `try`/`except ImportError` so an unsupported platform yields a no-op
      lock, and yield the no-op lock on any acquisition failure rather than
      raising.
- [x] 2.3 [req: wiki-autocommit] In the same file, wrap `wiki_autocommit`'s
      `git add` and `git commit` pair (lines 1413-1428) in
      `_store_commit_lock(store_dir)`, leaving the `git status` probe and the
      existing warning-and-return-False error handling unchanged.
- [x] 2.4 [req: wiki-autocommit, store-autocommit] In the same file, gate
      `wiki_autocommit` on `store_autocommit_enabled` resolved from
      `store_dir`, returning False without touching git when it is false.
      Confirm the tests from 2.1 pass.

## 3. The session-boundary sync hook

- [x] 3.1 [req: store-sync-hook] Create
      `plugins/s/skills/workspace/tests/test_store_sync.py` covering: a
      fast-forward merge plus push at session start, a push at session end, a
      divergent upstream warning that changes nothing, `store_sync` false
      running no git, an in-repo fallback store running no git, and a non-git
      store exiting 0. Run it and observe it fail — the script does not exist.
- [x] 3.2 [req: store-sync-hook] Create
      `plugins/s/skills/workspace/scripts/store_sync.py`, stdlib-only, modelled
      on `plugins/s/skills/document/scripts/voice_digest.py`: resolve the store
      through a lazily imported `spec_common`, read the event name from the
      hook payload on stdin, and exit 0 printing nothing when `store_sync`
      resolves false, when no workspace or external store resolves, when the
      store is the repo-local fallback, when the store is not inside a git work
      tree, or when it has no `origin` remote.
- [x] 3.3 [req: store-sync-hook] In the same script, implement the
      `SessionStart` path: `git fetch origin`, then `git merge --ff-only`
      against the branch's upstream, then push local commits. Implement the
      `SessionEnd` path as the push alone. Give every `subprocess.run` a
      timeout.
- [x] 3.4 [req: store-sync-hook] In the same script, route every failure — a
      non-fast-forward merge, a rejected push, a timeout, a missing upstream,
      an unresolvable configuration — to at most one stderr warning line and
      exit 0. Confirm the tests from 3.1 pass.
- [x] 3.5 [req: guardrail-hook-registration] In
      `plugins/s/skills/build/tests/test_guardrails.py`, update
      `test_hooks_json_declares_the_three_events` (line 739) to assert the four
      events and the two `SessionStart` commands, and add an assertion for the
      `SessionEnd` entry. Run it and observe it fail.
- [x] 3.6 [req: guardrail-hook-registration] In `plugins/s/hooks/hooks.json`,
      add the `store_sync.py` command entry to the existing `SessionStart`
      group and add a `SessionEnd` event with the same command. Confirm the
      tests from 3.5 pass.
- [x] 3.7 [req: store-sync-hook] In `.github/workflows/ci.yml`, add a step
      running `python3 -m unittest discover -s plugins/s/skills/workspace/tests -v`,
      placed beside the existing per-skill discovery steps (lines 42-51).

## 4. The doctor check

- [x] 4.1 [req: doctor-store-sync-check] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add tests for a
      `check_store_sync(root)` function: `warn` naming the unpushed count and
      the store path for a store ahead of its upstream, `ok` for a synced
      store, `ok` for a branch with no upstream, and `ok` for an in-repo
      fallback store. Run them and observe them fail.
- [x] 4.2 [req: doctor-store-sync-check] In `plugins/s/bin/shipd`, add
      `check_store_sync(root)` beside `check_store` (line 602). Resolve the
      store through `sc.resolve_wiki_root`, return `ok` early for the
      fallback-store, non-git, and no-upstream cases, and otherwise read the
      counts from `git rev-list --count --left-right @{u}...HEAD`. Use local
      git only and mutate nothing.
- [x] 4.3 [req: doctor-store-sync-check] In the same file, add
      `check_store_sync(root)` to the doctor's check list directly after
      `check_store(root)` (line 1051). Confirm the tests from 4.1 pass.
- [x] 4.4 [req: doctor-store-sync-line] In
      `plugins/s/skills/doctor/SKILL.md`, add `store-sync` to the report-only
      check names alongside `wiki` and `store`, stating that the skill relays
      the line and proposes no remedy.

## 5. Documentation

- [x] 5.1 [req: workspaces-doc-store-sync] In `docs/customise.md`, add a table
      row for `store_autocommit` and one for `store_sync` after the
      `worktree_stale_days` row (line 54), each naming what the key gates and
      its `true` default.
- [x] 5.2 [req: workspaces-doc-store-sync] In `docs/workspaces/teams.md`,
      rewrite the "Concurrency expectations" section (lines 71-98): replace the
      opening claim that the engine takes no locks and runs no networked git
      with the auto-commit, the exclusive lock, and the session-boundary sync,
      and replace the closing manual pull-and-push protocol with the two keys
      that turn the automation off. Keep the conflict-surface list. The file is
      exactly 150 lines, its how-to cap, so the rewrite must not grow it.
- [x] 5.3 [req: workspaces-doc-store-sync] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/workspaces/teams.md docs/customise.md`
      and fix every finding until it exits clean.

## 6. Ship prerequisites

- [x] 6.0 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.226` to `0.6.227`. The plugin cache snapshot is keyed by
      version, so a change touching `plugins/s/` without a bump leaves every
      session running the stale skills.

## 7. Verification

- [x] 7.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests`
      and `python3 -m unittest discover -s plugins/s/skills/workspace/tests`,
      and confirm both suites pass.
- [x] 7.2 [req: *] Run `python3 plugins/s/bin/shipd doctor` from the repo root
      and confirm it prints a `store-sync` line naming this workspace's pending
      commits.
