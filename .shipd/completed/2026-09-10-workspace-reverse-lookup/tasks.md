## 1. URL normalization

- [x] 1.1 [P1] [req: workspace-reverse-lookup] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for a new pure helper `normalize_repo_url(url)` in
      `plugins/s/skills/build/scripts/spec_common.py`:
      `git@github.com:acme/repo.git`, `https://github.com/Acme/Repo`,
      `ssh://git@github.com/acme/repo/`, and the bare scheme-less form all
      normalize equal; a normalized form differing in host or path does
      not. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the worktree root and observe the failures.
- [x] 1.2 [P2] [req: workspace-reverse-lookup] Implement
      `normalize_repo_url` (strip scheme or user prefix, read a colon-separated host and path
      as slash-separated, strip one trailing `.git` and trailing
      slashes, case-fold) until
      1.1 passes.

## 2. The fallback rungs

- [x] 2.1 [req: workspace-reverse-lookup, workspace-root-discovery] In
      `test_spec_common.py`, add failing `workspace_chain` fixture tests
      (throwaway dirs + local `git init` repos, an env/config layer
      declaring `workspaces_root`): unique origin-URL match resolves the
      matching workspace; a pointer file (`.shipd-workspace.local.json`
      with `workspace_root`) beats the scan; a pointer at a non-declaring
      target resolves nothing with one stderr warning; two matching
      workspaces resolve nothing with one stderr warning naming both and
      the pointer remedy; no pointer and no `workspaces_root` stays empty
      and silent; a fallback-resolved chain lists the matched root then
      its enclosing declaring directory; an ancestor-resolvable start
      never consults the rungs (assert no git probe by pointing the scan
      at a poisoned fixture).
- [x] 2.2 [req: workspace-reverse-lookup, workspace-root-discovery] In
      `spec_common.py`, extend `workspace_chain`: on an empty upward
      result, try the pointer rung (read `workspace_root` from the
      starting repo root's `.shipd-workspace.local.json` via a tolerant
      reader beside `load_repo_map`), then the scan rung (resolve
      `workspaces_root` from the layered config, probe
      `git -C <start> remote get-url origin` with the repo's short-timeout
      subprocess idiom, enumerate immediate children declaring
      `workspace`, match member urls via `normalize_repo_url`); resolve
      the chain as the upward chain from the resolved root; warn once on
      stderr for the pointer-invalid and ambiguous cases. Confirm 2.1
      passes and the whole suite stays green.

## 3. Docs and version

- [x] 3.1 [req: workspace-reverse-lookup] Add a "Resolving from outside
      the workspace" section to `docs/workspaces.md`: the
      ancestor-pointer-scan ladder, the `workspace_root` pointer key in
      `.shipd-workspace.local.json`, URL normalization, the ambiguity
      warning and remedy, and the CI-unchanged guarantee.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from the
      version main carries at build time (`0.6.199` as planned) to the
      next patch (`0.6.200` as planned).

## 4. Verification

- [x] 4.1 [req: *] From the worktree root, run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm `OK`. Then exercise the real behavior: from
      `~/projects/shipd` (an outside checkout whose origin is declared by
      the `~/workspaces/shipd-now` workspace), run the status CLI's
      `workspace-show` and confirm it resolves the workspace root; unset
      the fallback (point `HOME` at a throwaway with no
      `.shipd-config.json`) and confirm the no-workspace error returns.
