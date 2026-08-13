# Tasks

## 1. Auto-commit helper (spec_common.py)

- [x] 1.1 [req: wiki-autocommit] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing
      tests for `wiki_autocommit(store_dir, paths, subject)` over tempdir
      fixtures with real git repos (identity configured in-repo via
      `git config user.name`/`user.email`): a non-git directory → returns
      False, no error; a nested store (`<ws>/.shipd/wiki`) in a repo rooted at
      `<ws>` with one new and one modified file → returns True and
      `git log -1` shows the subject with exactly those files; a
      byte-identical write (paths matching HEAD) → returns False and no new
      commit; an unrelated file staged in the index stays staged and out of
      the helper's commit; an identity-less repo (env `HOME` pointed at an
      empty tempdir with `GIT_CONFIG_NOSYSTEM=1`, no in-repo identity) →
      returns False with a stderr warning and the written files intact.
- [x] 1.2 [req: wiki-autocommit] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement
      `wiki_autocommit` beside the existing local-git helpers per the
      plan's Implementation (gate on `_inside_git_work_tree`, skip on empty
      `status --porcelain -- <paths>`, `add` + pathspec-scoped `commit`,
      stderr warning and False on any git failure); confirm the 1.1 tests
      pass.

## 2. Emit hook (spec_emit.py)

- [x] 2.1 [req: wiki-autocommit] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add failing tests
      for the `wiki` mode: a successful emit into a git-initialized
      workspace (identity configured in-repo) → exit 0 and a new commit
      with subject `shipd-wiki: emit <n> file(s)` containing exactly the
      installed store files; a workspace not under git → exit 0 and no
      `.git` created; a lint-failing emit (rolled back) → no new commit.
- [x] 2.2 [req: wiki-autocommit] In
      `plugins/s/skills/build/scripts/spec_emit.py`, call
      `sc.wiki_autocommit` from `emit_wiki` after the whole-store lint
      passes, passing the installed destination paths and the subject
      `shipd-wiki: emit <n> file(s)`; confirm the 2.1 tests pass.

## 3. Queue-add hook (spec_status.py)

- [x] 3.1 [req: wiki-autocommit] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing
      tests for `wiki-queue-add`: in a git-initialized workspace → exit 0
      and a new commit with subject `shipd-wiki: queue-add q-<slug>`
      containing only `queue.md`; a duplicate-slug rerun → exit non-zero
      and no new commit; a non-git workspace → exit 0 with the block
      appended.
- [x] 3.2 [req: wiki-autocommit] In
      `plugins/s/skills/build/scripts/spec_status.py`, call
      `sc.wiki_autocommit` from `cmd_wiki_queue_add` after the queue
      validation succeeds, with `[queue_path]` and the subject
      `shipd-wiki: queue-add q-<slug>`; confirm the 3.1 tests pass.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      the version on remote main (0.6.16 at planning time — re-check
      before editing; other changes merge concurrently).
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and observe an
      all-green run.
