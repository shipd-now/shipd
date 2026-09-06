## 1. Resolution seam (spec_common)

- [x] 1.1 [req: wiki-store-layout] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_common.py`: a new
      `resolve_wiki_root(start)` returns the nearest chain member with
      `is_fallback=False` when a workspace chain exists, `(start, True)` when
      the chain is empty and `specs_dir(start)` exists on disk, and `None`
      when neither; `resolve_wiki_stores(start)` returns the existing
      fallback store as its single entry when the chain is empty; and
      `wiki_base_dir` treats a `wiki_base` equal to the fallback store's own
      directory as undeclared. Run the tests and observe them fail.
- [x] 1.2 [req: wiki-store-layout] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement
      `resolve_wiki_root(start)` beside `resolve_wiki_stores` (l.900), extend
      `resolve_wiki_stores` with the chain-empty fallback branch, and extend
      the `wiki_base_dir` guard (l.1237) to also compare against
      `wiki_dir(ws_root)` itself when the chain is empty. Confirm the 1.1
      tests pass.

## 2. Status verbs

- [x] 2.1 [req: wiki-status-verbs, config-show-verb] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_status.py`: in a temp repo with
      a content directory and no workspace, `wiki-init` scaffolds
      `<root>/<content-dir>/wiki`; `wiki-queue-add`/`wiki-queue-answer`/
      `wiki-queue-discard` operate on it (scaffolding on demand); `cat wiki`
      resolves pages/index/queue from it with no provenance annotation;
      `wiki-show` prints `wiki: <path> (repo-local fallback)` plus
      `chain: none`; in a temp dir with no content directory every verb
      exits non-zero naming both the missing workspace and the missing
      content directory; and `config-show` prints the `wiki:` line in all
      three states (workspace store path, fallback path with marker,
      `wiki: none`).
- [x] 2.2 [req: wiki-status-verbs, config-show-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, route `_wiki_store`
      (l.2689), the `cat wiki` branch (l.2599–2660, single-store fallback:
      `stores=[wiki_dir(root)]`, `nearest_root=root`), `cmd_wiki_show`
      (l.3149–3196, fallback marker, `chain: none`, `base:` resolved from the
      fallback root), and the queue verbs (l.3276, l.3339) through
      `sc.resolve_wiki_root`, replacing their `_resolve_workspace` calls;
      make the ineligible-root error name both prerequisites; add the
      `wiki:` line to `cmd_config_show` (l.2288). Confirm the 2.1 tests pass.
- [x] 2.3 [req: wiki-autocommit] Add failing tests (extend
      `test_spec_status.py`): in a git-initialized temp repo with a content
      directory, no workspace, and no `store_root`, `wiki-queue-add`,
      `wiki-queue-answer`, and `wiki-queue-discard` succeed with **no**
      commit created; with `store_root` redirecting the content directory
      into a separate git-initialized store repo, the same writes do commit
      there.
- [x] 2.4 [req: wiki-autocommit] In `spec_status.py`, switch the queue verbs'
      auto-commit calls (l.3313, l.3391 and the discard sibling) to use
      `sc.store_autocommit(root, …)` when the resolution is the fallback
      store, keeping `sc.wiki_autocommit` for workspace stores. Confirm the
      2.3 tests pass.
- [x] 2.5 [req: wiki-remove-verb] Add failing tests to
      `plugins/s/skills/build/tests/test_wiki_remove.py`: `wiki-remove`
      removes a page from the fallback store in a bare repo, updating index
      and log, with no commit made in the repo's git history.
- [x] 2.6 [req: wiki-remove-verb] In `spec_status.py`, route `cmd_wiki_remove`
      (l.3412) through `sc.resolve_wiki_root` and apply the same fallback
      auto-commit carve-out. Confirm the 2.5 tests pass.

## 3. Wiki emission

- [x] 3.1 [req: wiki-emission] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_emit.py`: `spec_emit.py wiki
      --from <staging>` installs into `<root>/<content-dir>/wiki` in a bare
      repo with a content directory (lint/rollback semantics intact, no
      commit made in the repo's git history), and exits non-zero naming both
      prerequisites when the content directory is missing too.
- [x] 3.2 [req: wiki-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py` (l.291–299), replace the
      `find_workspace_root`-is-None refusal with `sc.resolve_wiki_root`
      resolution, and switch the auto-commit call (l.368) to
      `sc.store_autocommit(root, …)` for a fallback resolution. Confirm the
      3.1 tests pass.

## 4. Doctor and config reporting

- [x] 4.1 [req: doctor-wiki-check] Add failing tests to
      `plugins/s/skills/build/tests/test_shipd_cli.py`: `check_wiki(root)`
      returns `("ok", "wiki", …)` in all three states (workspace store,
      repo-local fallback naming the path and that `wiki-init` scaffolds an
      absent one, no store resolvable naming both missing prerequisites),
      and `default_checks` places `wiki` directly after `schema`.
- [x] 4.2 [req: doctor-wiki-check] In `plugins/s/bin/shipd`, implement
      `check_wiki(root)` (read-only, always `ok`, via `_load_engine` and
      `sc.resolve_wiki_root`/`sc.wiki_dir`; catch `sc.ConfigError` and report
      `ok` with the error text — the `config` check owns config failures) and
      insert it after `check_schema(root)` in `default_checks` (l.894–912).
      Confirm the 4.1 tests pass.
- [x] 4.3 [req: doctor-wiki-line] In `plugins/s/skills/doctor/SKILL.md`, add
      `wiki` to the parsed check-name list (l.62–64) and note it is
      report-only with no remedy row.

## 5. Prose surfaces

- [x] 5.1 [req: oracle-fallback-store, oracle-insufficient-queue] In
      `plugins/s/agents/oracle.md`, update the wiki rung and "Queue behavior"
      item 4 (l.270–277): in a bare shipd-initialized repo the reads and the
      queue write operate on the repo-local fallback store `wiki-show`
      reports (same verbs, scaffold on demand), answered fallback queue
      blocks cite as `queue q-<slug>`, and `Queued: none (<missing
      prerequisites>)` remains only for a repo with neither a workspace nor
      a content directory.
- [x] 5.2 [req: teach-skill] In `plugins/s/skills/teach/SKILL.md`, rewrite the
      store-resolution step (l.107–126): continue on the repo-local fallback
      store when `wiki-show` reports one (noting the `(repo-local fallback)`
      marker), scaffold with `wiki-init` when absent, and stop pointing at
      `workspace-init`/`shipd init` only when neither a workspace nor a
      content directory exists.

## 6. Verification and ship prep

- [x] 6.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` to the next unclaimed patch
      release.
- [x] 6.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole suite passes
      without `textual` installed; then run `plugins/s/bin/shipd doctor` in
      this worktree and confirm it prints an `ok wiki — repo-local fallback
      …` line and still exits 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 191 | 47.2k |
| (no tool) | 0 | 11.5k |
| Edit | 38 | 10.8k |
| Read | 45 | 4.8k |
| Agent | 8 | 444 |
| Monitor | 1 | 261 |
| ToolSearch | 2 | 181 |
| **Total** | 285 | 75.2k |
