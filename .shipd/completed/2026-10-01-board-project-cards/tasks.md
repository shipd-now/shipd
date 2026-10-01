## 1. Universe seam: scope a project-folder invocation

- [x] 1.1 [req: workspace-universe-discovery] In
      `plugins/s/skills/build/tests/test_spec_common.py`, class
      `WorkspaceUniverseSeamTest`, add three tests using its `_workspace`
      helper and `home_set_to`: a registry declaring project `alpha` with two
      repos, web and api, inside an alpha directory, and project `beta` with
      one repo, svc, inside a beta directory, all created on disk. Queried at
      the alpha directory, the seam returns only the two `alpha` pairs in
      declaration order and `aggregation_universes` lists that directory with
      a null project first; a created scratch directory holding no repo
      returns an empty list; the registry root itself still returns all
      three. Run the class and observe the first two
      fail.
- [x] 1.2 [req: workspace-universe-discovery] In
      `plugins/s/skills/build/scripts/spec_common.py`,
      `workspace_project_roots`: after the `project_of` check, compute
      `real_root = os.path.realpath(root)` and `real_reg =
      os.path.realpath(reg_root)`; when `real_root != real_reg` and
      `real_root.startswith(real_reg + os.sep)`, skip every repo whose real
      path is not `real_root` or does not start with `real_root + os.sep`.
      Leave every other path through the function unchanged. Extend the
      docstring with the project-folder case, naming requirement
      `workspace-universe-discovery`. Confirm the tests from 1.1 pass.
- [x] 1.3 [req: workspace-universe-discovery] Rewrite the sentence at
      `docs/workspaces/teams.md:150` and `docs/workspaces/multi-workspace-repos.md:80`
      to say that from the workspace root `shipd board` reports delivery across
      every declared project's repos, and from a folder inside it only the
      repos beneath that folder. Re-wrap the surrounding paragraph so
      `teams.md` stays at 150 lines or fewer. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/workspaces/teams.md docs/workspaces/multi-workspace-repos.md`
      and `wc -l` on both; confirm exit 0 and both within 150 lines.

## 2. Card project marker

- [x] 2.1 [req: board-card-project-marker] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, class
      `TaskCardRowTest`, add tests: `dashboard.TaskCard("ep", member, {},
      "active", epic_project="cai")` renders
      `"[$risk-low]●[/] sl [$fg-muted]\\[cai][/]"` for a low-risk member; a
      card with `epic_project=None` and member `{"slug": "sl", "state":
      "ready", "actions": [], "project": "shipd"}` ends with the `shipd`
      marker; a driving entry with stage `gate` renders the stage suffix
      before the marker; a shipped member with a project renders
      `"[$fg-subtle]✓[/] sl [$fg-muted]\\[cai][/]"`; the existing
      `_bare_card` outputs are unchanged. Run the class and observe the new
      tests fail.
- [x] 2.2 [req: board-card-project-marker] In
      `plugins/s/skills/build/scripts/dashboard.py`, add
      `TaskCard._card_project(self)` returning `self.epic_project or
      self.member.get("project")`. Restructure `_card_text` so every branch
      assigns its text to one variable, then append
      `" [$fg-muted]\\[%s][/]" % project` once when `_card_project()` is
      non-null before returning. Update the class docstring, naming
      requirement `board-card-project-marker`. Confirm 2.1 passes.
- [x] 2.3 [req: board-card-project-marker] In the same test file, class
      `FilterStripLaneTest` (the class holding
      `test_lane_signature_differs_when_only_filters_differ`), add a test
      that two contents equal except one `standalone` spec's
      `member["project"]` produce different signatures. In `dashboard.py`,
      `_lane_signature`, append `member.get("project")` to each card tuple
      and note it in the docstring. Confirm the test passes.
- [x] 2.4 [req: board-card-project-marker] In `test_dashboard.py`, class
      `SpecDetailModalTest`, add two tests: opening the detail modal for a
      card whose epic project is `cai` finds a `.modal-badge` whose text is
      `project: cai` as the last badge in `.modal-badge-row`; opening it for a
      root-universe card finds no badge starting with `project:`. Build the
      fixture with the module's `_detail_board` helper, then set
      `board["epics"][0]["project"] = "cai"` on its result inside the
      `board_fn` lambda for the project case. Run and observe both fail.
- [x] 2.5 [req: board-card-project-marker] In `dashboard.py`,
      `MemberDetailScreen.__init__`, add a `project=None` keyword stored as
      `self.project`; in `compose`, after the `epic:` badge, yield
      `Static("project: %s" % self.project, classes="modal-badge
      badge-muted", markup=False)` when `self.project` is set. In
      `TaskCard.action_select`, pass `project=self._card_project()`. Confirm
      2.4 passes.
- [x] 2.6 [req: board-card-project-marker] In `test_dashboard.py`, class
      `TaskCardRowMountedTest`, add one async test mounting a board with a
      project epic member through `board_fn`, pressing `g` to cycle grouping
      through `initiative` and `none`, and asserting the member's card
      `_card_text()` carries the project marker in each mode. Confirm it
      passes without further code change.

## 3. Project filter chip

- [x] 3.1 [req: board-filter-strip] In `test_dashboard.py`, class
      `FilterMatchesTest`, add tests: `_filter_matches([("project", "cai")],
      "ep", None, member, project="cai")` is true, with `project="shipd"` is
      false, and with `project=None` is false; existing calls without the
      keyword still pass. In class `FilterOptionsTest`, add a test that a
      board with epics from `cai` and `shipd` plus a standalone row from
      `shipd` yields `("project", "cai")` and `("project", "shipd")` once
      each, after every initiative option, and that a null project
      contributes none. In class `FilterPickerTest`, add a test that the
      picker lists a `project: cai` option. Run and observe the new tests
      fail.
- [x] 3.2 [req: board-filter-strip] In `dashboard.py`: give
      `_filter_matches` a `project=None` keyword and add `"project": project`
      to `field_for`; in `_filter_options`, after the initiative loop, walk
      `board["epics"]` then `board["standalone"]` appending
      `("project", slug)` for each distinct non-null `project`; in
      `BoardApp._filtered_lane_contents`, pass `project=project or
      member.get("project")`. Update the three docstrings to name the
      `project` kind. Confirm 3.1 passes.
- [x] 3.3 [req: board-filter-strip] In `test_dashboard.py`, class
      `FilterStripLaneTest`, add an async test that selecting `project: cai`
      on a board holding `cai`, `shipd`, and root-universe members mounts only
      the `cai` cards. Confirm it passes.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `"version"` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.242` to `0.6.243`.
- [x] 4.2 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests_textual -v`
      from the repository root; confirm both exit 0.
- [x] 4.3 [req: *] Run the worktree's `plugins/s/bin/shipd board text --json
      --root /Users/mikkelbergmann/projects/workspaces/shipd` and confirm
      every epic's `project` is `shipd` and no `cai` or `fresh-careers` epic
      appears.
