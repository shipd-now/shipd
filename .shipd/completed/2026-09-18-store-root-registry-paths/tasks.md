## 1. Registry-path store derivation

- [x] 1.1 [req: store-repo-folder-name] In
      `plugins/s/skills/build/tests/test_spec_common.py`, extend
      `ExternalStoreRootTest` with failing cases: a declared registry member whose
      manifest path is `<ws>/shipd/shipd-app` relative to the workspace root,
      resolving `<ws>/store/shipd/shipd-app`; its
      linked worktree resolving the same path; a member relocated by the member
      map resolving its manifest path; an undeclared repository inside the
      workspace keeping the main-checkout basename; and two entries whose manifest paths
      differ only in their leading project segment, `<ws>/shipd/dittor` and
      `<ws>/cai/dittor`, resolving distinct store paths. Update the three
      existing assertions at lines 2582-2583 and 2591 to the new expectations.
      Run `python3 -m unittest tests.test_spec_common.ExternalStoreRootTest` from
      `plugins/s/skills/build` and observe the new cases fail.
- [x] 1.2 [req: store-repo-folder-name] In
      `plugins/s/skills/build/scripts/spec_common.py`, factor the matching loop
      inside `project_of` (line 2208) into a module-level helper
      `_registry_member_of(ws_root, path)` returning
      `(project_slug, manifest_path)` or `(None, None)`, preserving the existing
      equality-or-containment match, longest-entry-wins specificity, member-map
      matching, first-declaration tie-break, and fail-soft behavior. Rewrite
      `project_of` to return that helper's slug so its behavior is unchanged.
- [x] 1.3 [req: store-repo-folder-name] In the same file, rewrite
      `repo_store_folder` (line 631) to resolve `registry_root(root)` and, when
      it yields a root, call `_registry_member_of` with `root`: return the
      manifest path when one matches. When no registry or no member matches,
      keep the existing `git rev-parse --path-format=absolute --git-common-dir`
      basename derivation and its root-basename fallback. Keep the
      `_STORE_FOLDER_CACHE` memo keyed by `os.path.realpath(root)` and keep every
      failure path fail-soft. Update the docstring to state the registry-first
      derivation.
- [x] 1.4 [req: store-repo-folder-name, store-root-key] In the same file, change
      `specs_dir` (line 719) to join the derived value's `/`-separated
      components onto the store root with native separators, mirroring the
      `specs_dirname(config).split("/")` join on the in-repo branch directly
      below it. Run
      `python3 -m unittest tests.test_spec_common.ExternalStoreRootTest` from
      `plugins/s/skills/build` and confirm every case passes.

## 2. Doctor external-store check

- [x] 2.1 [req: doctor-store-check] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add `"store"` to
      `DoctorCheckTest.ALL_CHECKS` (line 1137) directly after `"wiki"`, and add
      failing `check_store` cases covering: no `store_root` declared; a declared
      store resolving an existing directory; a stranded basename directory
      present while the registry-path directory is absent; and a malformed
      configuration. Add an ordering case asserting `store` follows `wiki`, in
      the style of `test_default_checks_report_wiki_after_schema`. Run
      `python3 -m unittest tests.test_shipd_cli.DoctorCheckTest` from
      `plugins/s/skills/build` and observe the new cases fail.
- [x] 2.2 [req: doctor-store-check] In `plugins/s/bin/shipd`, add `check_store(root)`
      immediately after `check_wiki` (line 544), returning one
      `(level, name, detail)` triple per the delta requirement: `ok` when no
      `store_root` is declared, `ok` naming the resolved content directory when
      one is, `warn` naming both paths and the `git mv` remedy when the basename
      directory exists and the resolved one does not, and `ok` carrying the error
      string on a `sc.ConfigError`. Derive the basename comparison path with the
      same git probe the fallback uses; mutate nothing. Insert
      `check_store(root)` into `default_checks` (line 969) directly after
      `check_wiki(root)`. Run
      `python3 -m unittest tests.test_shipd_cli.DoctorCheckTest` from
      `plugins/s/skills/build` and confirm every case passes.
- [x] 2.3 [req: doctor-store-line] In `plugins/s/skills/doctor/SKILL.md`, add
      `store` to the recognized check names and record it as report-only with no
      remedy row, following the wording the file already uses for the `wiki`
      check.

## 3. Documentation

- [x] 3.1 [req: store-repo-folder-name] In
      `docs/workspaces/nesting-and-stores.md`, rewrite the "Per-repo folder
      naming" section to state the registry-path derivation, the basename
      fallback for an undeclared or non-git root, and worktree stability; update
      the store tree diagram near line 96 so each store folder nests under its
      project segment; and
      rescope the "Basename collisions are yours to avoid" limitation to
      repositories no registry declares. Add the `store` doctor line to the
      "Check what resolved" section. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/workspaces/nesting-and-stores.md`
      and fix any finding until it exits 0.

## 4. Ship preparation and verification

- [x] 4.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` by one patch level, from `0.6.225`
      to `0.6.226`, so the cached plugin snapshot picks up the edited engine and
      skill files. Required by `AGENTS.md` for every change touching
      `plugins/s/`.
- [x] 4.2 [req: *] From `plugins/s/skills/build`, run
      `python3 -m unittest discover -s tests -t .` and confirm the whole suite
      passes with no regression in the store, workspace, doctor, or status
      surfaces.
