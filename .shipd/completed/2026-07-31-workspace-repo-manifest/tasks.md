# Tasks

## 1. Registry widening and focus (spec_common.py)

- [x] 1.1 [req: project-registry-semantics, workspace-focus] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for the widened registry: mixed string/object repos entries validate
      clean; an object entry without `path` (or with an empty/non-string
      `path`, `url`, or `branch`) is a shape error naming the project; a
      duplicate resolved path across a string entry and an object entry is an
      ambiguous-ownership error; `focus` naming a declared project is clean;
      an unknown or non-kebab `focus` errors naming the declared slugs; and
      `repo_entry_path` returns the path for both shapes and `None` for
      malformed entries.
- [x] 1.2 [req: project-registry-semantics, workspace-focus] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement
      `repo_entry_path(entry)` and extend `validate_workspace` with the
      widened entry shapes and the `focus` check; confirm the 1.1 tests pass.
- [x] 1.3 [req: project-registry-semantics] In `test_spec_common.py`, add
      failing tests that `project_of` resolves containment for repos declared
      via object entries (and still via string entries).
- [x] 1.4 [req: project-registry-semantics] In `spec_common.py`, route
      `project_of` through `repo_entry_path`; confirm the 1.3 tests pass.

## 2. Git-seeding init (spec_common.py + spec_status.py)

- [x] 2.1 [req: workspace-initialization, workspace-init-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests
      for `workspace-init <path> --git`: a non-git target becomes a git
      repository with a `.gitignore` carrying the marked member-repos block
      (`# >>> shipd-workspace members` / `# <<< shipd-workspace members`); running
      again does not duplicate the block; a target already inside a git work
      tree is not re-initialized; without `--git` no git repository or
      `.gitignore` is created.
- [x] 2.2 [req: workspace-initialization, workspace-init-verb] Implement:
      `init_workspace(path, git=False)` in `spec_common.py` (git-init via
      `git rev-parse --is-inside-work-tree` probe, idempotent marked-block
      append; local subprocess git only) and the `--git` flag on the
      `workspace-init` verb in `spec_status.py`; confirm the 2.1 tests pass.

## 3. Show verbs (spec_status.py)

- [x] 3.1 [req: workspace-status-verbs] In `test_spec_status.py`, add failing
      tests: `workspace-show` prints a `focus:` line when the registry
      declares one and omits it otherwise; a repo entry carrying a `url` is
      annotated `[url]` in both `workspace-show` and `project-show`; object
      entries display their `path` exactly like string entries.
- [x] 3.2 [req: workspace-status-verbs] In `spec_status.py`, implement the
      focus line and `[url]` annotation, routing path reads through
      `repo_entry_path`; confirm the 3.1 tests pass.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      the version on remote main (0.6.13 at planning time — re-check before
      editing; other changes merge concurrently).
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and observe an
      all-green run.
