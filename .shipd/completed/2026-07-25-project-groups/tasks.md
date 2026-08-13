# Tasks — project-groups

## 1. Registry semantics and resolution

- [x] 1.1 [req: project-registry-semantics, project-resolution] Add failing
      tests in `plugins/s/skills/build/tests/test_spec_common.py`:
      `validate_workspace` returns `[]` for
      `{"projects": {"alpha": {"repos": ["shipd", "apps/backend"]}}}`
      (paths need not exist); errors on a non-object `projects`, a
      non-kebab slug, a non-list `repos`, an empty-string repo entry, and an
      exact duplicate path across two projects (naming the path).
      `project_of` picks the most specific containing entry across projects
      (`alpha: apps` vs `beta: apps/backend` → `apps/backend/repo-x` is
      `beta`), returns the owning slug for an exact entry match, and `None`
      for an unmatched path. Run and observe the new tests fail.
- [x] 1.2 [req: project-registry-semantics, project-resolution] In
      `plugins/s/skills/build/scripts/spec_common.py`, implement
      `validate_workspace(registry)` returning a list of error strings and
      `project_of(ws_root, path)` per the plan's Implementation (normalize
      against `ws_root`, longest matching entry wins, first-declaration
      order breaks ties deterministically, `None` when unmatched). Confirm
      the 1.1 tests pass.

## 2. Lint wiring

- [x] 2.1 [req: workspace-lint-mode, initiative-brief-format] Add failing
      tests in `plugins/s/skills/build/tests/test_spec_lint.py`:
      `--workspace` passes a clean registry, reports duplicate-path and
      shape errors naming `.shipd/workspace.json` (non-zero), and errors
      "no workspace found" without a workspace. Brief `Project:` checks in
      `--initiative`: `Project: alpha` passes when `alpha` is declared;
      `Project: beta` errors listing the declared slugs; any `Project:` line
      errors when the registry declares no projects; a broken registry
      surfaces its `validate_workspace` errors when (and only when) the
      brief carries a `Project:` line — a brief without one never loads the
      registry.
- [x] 2.2 [req: workspace-lint-mode, initiative-brief-format] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add the `--workspace`
      CLI mode (workspace via `find_workspace_root`, findings from
      `spec_common.validate_workspace` as `LintError`s against the registry
      path) and extend `lint_initiative` with the `Project:` registry check
      per the plan. Confirm the 2.1 tests pass.

## 3. Status verbs

- [x] 3.1 [req: workspace-status-verbs] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_status.py`: `workspace-show`
      lists the root, project `alpha` with a present repo and an
      `(absent)`-annotated repo, `context: no` (then `context: yes` once
      `projects/alpha/context.md` exists), initiative `mvp-readiness` with
      status and `alpha` scope, and the implicit-default note when the repo
      resolves to no declared project; `project-show alpha` lists repos,
      context presence, and the scoped initiative; `project-show beta`
      errors non-zero naming declared slugs; both verbs error "no
      workspace" without one.
- [x] 3.2 [req: workspace-status-verbs] Implement `workspace-show` and
      `project-show` in `plugins/s/skills/build/scripts/spec_status.py`
      per the plan's Implementation, reusing the initiative verbs'
      workspace resolution and brief header parsing. Confirm the 3.1 tests
      pass.

## 4. Docs and version

- [x] 4.1 [P4] [req: project-registry-semantics, project-resolution, project-context-convention] Extend
      `am/README.md`'s Workspace section with a Projects subsection: the
      `projects` registry shape (relative paths, tolerance, duplicate rule),
      containment resolution and the anonymous implicit default,
      `projects/<slug>/context.md` as unlinted free prose, and the
      `Project:` brief-scoping rule.
- [x] 4.2 [P4] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.2.4` → `0.2.5`.

## 5. Verification

- [x] 5.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py project-groups`;
      everything green.
