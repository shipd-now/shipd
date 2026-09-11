## 1. The new reference part

- [x] 1.1 [req: workspaces-doc] Create `docs/workspaces/member-map.md`
      (marker `<!-- doc-type: reference -->` on line 1, ≤250 lines, opening
      back-link to the index): move the "Mapping members to existing
      checkouts" and "Resolving from outside the workspace" sections out of
      `docs/workspaces.md`, rewritten to the standard per plan.md — both
      `.shipd-workspace.local.json` fields, the `workspace-map`
      list/set/remove verbs led by `/s:workspace map` (raw verbs keep their
      `spec_status.py` form), mapped-member planner semantics, and the
      three-rung discovery ladder with URL normalization, the SSH-alias
      caveat, and the ambiguity warning. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/workspaces/member-map.md`
      until exit 0.

## 2. The index

- [x] 2.1 [req: workspaces-doc] Rewrite `docs/workspaces.md` as the concept
      index (marker `concept`, ≤100 lines): the workspace concept, the
      labeled layout tree, and one descriptive sentence + usage example +
      relative link per part for all six parts, `member-map.md` included; the
      two moved sections are deleted. Lint the file until exit 0.

## 3. Part rewrites

- [x] 3.1 [P3] [req: workspaces-doc] Rewrite
      `docs/workspaces/getting-started.md` (marker `how-to`, ≤150): keep the
      full setup-through-day-to-day coverage including every `workspaces_root`
      obligation the delta names. Lint until exit 0.
- [x] 3.2 [P3] [req: workspaces-doc] Rewrite
      `docs/workspaces/nesting-and-stores.md` (marker `reference`, ≤250):
      keep nesting inheritance, `--nested` semantics, and the full
      `store_root` coverage including auto-commit and known limitations. Lint
      until exit 0.
- [x] 3.3 [P3] [req: workspaces-doc] Rewrite `docs/workspaces/teams.md`
      (marker `how-to`, ≤150): keep sharing, concurrency, conflict-surface,
      and hooks-consent coverage; reshape the enterprise section to the
      dedicated-workspaces-repository layout (one folder per team or group,
      each folder a job workspace, partial materialization, member map,
      linking `multi-workspace-repos.md` for the shape mechanics) with the
      per-group-repo isolation escape hatch stated. Retarget its member-map
      link to `member-map.md`. Lint until exit 0.
- [x] 3.4 [P3] [req: workspaces-doc] Rewrite `docs/workspaces/headless.md`
      (marker `how-to`, ≤150): keep the footprint contract; `spec_status.py`
      examples stay. Lint until exit 0.
- [x] 3.5 [P3] [req: workspaces-doc] Rewrite
      `docs/workspaces/multi-workspace-repos.md` (marker `how-to`, ≤150):
      keep both shapes, their layout trees, both tables, the pros/cons, the
      plain-`git clone` direction, and the isolation-boundary warning. Lint
      until exit 0.

## 4. Links and README

- [x] 4.1 [req: workspaces-doc] Sweep every relative link and `#` anchor
      across the seven guide files and fix any that fail to resolve
      (including links into the moved sections from any page); confirm
      `docs/prd.md` and `docs/oracle.md` links to `workspaces.md` still
      resolve.
- [x] 4.2 [P4] [req: readme-workspaces-flagship-link] Add the flagship link
      to `docs/workspaces.md` in `README.md`'s introduction, immediately
      after the existing `docs/what-is-shipd.md` link and before any other
      link into `docs/`.

## 5. Verification

- [x] 5.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/workspaces.md docs/workspaces/getting-started.md docs/workspaces/member-map.md docs/workspaces/nesting-and-stores.md docs/workspaces/teams.md docs/workspaces/headless.md docs/workspaces/multi-workspace-repos.md`
      and observe exit 0; run `shipd lint docs-workspaces-rework` and observe
      a clean structural validation; verify each delta scenario by
      inspection.
