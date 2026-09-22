## 1. Project registry writer

- [x] 1.1 [req: workspace-project-verbs] Create
      `plugins/s/skills/build/tests/test_workspace_team.py` with a
      `WorkspaceProjectVerbTests` case driving `spec_status.py
      workspace-project` in a tmpdir workspace: bare listing (including the
      `(no projects)` line), `add` creating a project, `add --url/--branch`
      storing both verbatim, `remove --repo` dropping one entry, `remove`
      dropping the project, the ambiguous-repo-path refusal leaving the file
      byte-identical, and an unrelated `dir` key surviving a write. Run it and
      observe every test fail — the verb does not exist yet.
- [x] 1.2 [req: workspace-project-verbs] Implement `cmd_workspace_project(root,
      action, project, path, url, branch, remove_repo)` in
      `plugins/s/skills/build/scripts/spec_status.py`, beside
      `cmd_workspace_map`. Resolve the workspace with `_resolve_workspace`,
      load the registry, apply the mutation, run
      `sc.validate_workspace_registry` on the result and raise `StatusError`
      with its message when it reports errors, then write the config back
      preserving every other key.
- [x] 1.3 [req: workspace-project-verbs] Wire the `workspace-project`
      subparser into `spec_status.py`'s argparse setup and add its line to the
      module usage banner, matching the shape of the existing
      `workspace-map` entry. Run task 1.1's tests until they pass.

## 2. Team wizard

- [x] 2.1 [req: workspace-team-wizard] Add a `WorkspaceTeamPlannerTests` case
      to `test_workspace_team.py` covering the pure layer only: a collected
      answer set becomes an ordered action plan; a team name failing
      `PROJECT_NAME_RE` yields no action; a duplicate name yields no second
      action; a team directory already declaring a workspace yields a skip
      action rather than an init action. Run it and observe it fail.
- [x] 2.2 [req: workspace-team-wizard] Create
      `plugins/s/skills/build/scripts/workspace_tui.py`, stdlib-only, in
      `install_tui.py`'s three layers. Layer one: a pure `plan_teams(base,
      answers)` returning an ordered list of action tuples
      (`mkdir`, `init`, `project`, `map`, `skip`). Layer two: pure executors
      that perform one action each by calling `os.makedirs`,
      `cmd_workspace_init(..., nested=True, git=True)`,
      `cmd_workspace_project`, and `cmd_workspace_map`. Layer three is added
      in task 2.4. Run task 2.1's tests until they pass.
- [x] 2.3 [req: workspace-team-wizard] Add an executor test case to
      `test_workspace_team.py`: executing a plan against a real tmpdir base
      workspace creates the team directory, declares a nested workspace whose
      config names the base as its enclosing root, writes the team's own
      `projects` entry while leaving the base registry untouched, and records
      a member map entry — with no network call and no clone. Run it until it
      passes.
- [x] 2.4 [req: workspace-team-wizard] Add layer three to
      `workspace_tui.py`: the interactive loop on `/dev/tty` collecting team
      names and, per team, its repo paths, urls, and any existing local
      checkout, re-asking on a malformed or duplicate name. Restore terminal
      state in a `finally`, exactly as `install_tui.py` does. When
      `sys.stdin.isatty()` is false, print a note naming the verb as
      interactive, write nothing, and return a non-zero code.
- [x] 2.5 [req: workspace-team-wizard] Add `cmd_workspace_team(root)` to
      `spec_status.py` delegating to `workspace_tui`, raising `StatusError`
      naming workspace initialization as the remedy when no workspace
      resolves. Wire its subparser and usage-banner line. Add a headless test
      asserting the verb writes nothing and exits non-zero when stdin is not a
      terminal.
- [x] 2.6 [req: workspace-team-wizard] Make the verb's completion report name
      each team created, each repo declared, each member mapped, and
      `shipd workspace sync` as the way to materialize the rest. Cover the
      report's content in a test against an executed plan.

## 3. Binary dispatch

- [x] 3.1 [req: cli-dispatch] In `plugins/s/bin/shipd`, add the bare word
      `team` to the `workspace` mode mapping so it is consumed and delegates
      to `spec_status.py workspace-team`, leaving `init`, `sync`, and the bare
      roster form unchanged. Add the verb to the module docstring's list of
      declared write exceptions, which becomes ten, and to the usage banner's
      `workspace` line.
- [x] 3.2 [req: cli-dispatch] Add a test to
      `plugins/s/skills/build/tests/test_shipd_cli.py` asserting
      `shipd workspace team --help` produces output identical to
      `spec_status.py workspace-team --help` and exits `0`, matching the
      existing init and sync mode tests.

## 4. Skill mirror

- [x] 4.1 [req: workspace-setup-skill] In
      `plugins/s/skills/workspace/SKILL.md`, add `team` to the frontmatter
      description and to the verb-dispatch list, then add a `## \`team\` —
      guided team workspace setup` section that mirrors the wizard's steps one
      at a time and drives `workspace-team` rather than reimplementing it.
      State that the skill hand-writes no manifest, gitignore block, project
      registry, or map file.
- [x] 4.2 [req: workspace-setup-skill] In the same file's `init` section,
      keep the report-and-stop behavior and add a sentence naming `team` as
      the way to add a nested team workspace beneath a discoverable root.

## 5. Documentation

- [x] 5.1 [req: workspaces-doc-examples] Rewrite
      `docs/workspaces/multi-workspace-repos.md` to document only the
      base-plus-nested shape: one layout diagram marking tracked against
      machine-local content, the storage table for manifest, wiki, queue,
      initiatives, and member repos, setup and day-to-day commands through the
      `shipd` binary with `shipd workspace team` named, the costs (base
      knowledge accumulates only from base writes; a base-queued question is
      answerable only there), plain `git clone` for the repository, and the
      separate-repos isolation warning. Remove every sibling-shape section and
      the A/B comparison. Keep the page within the 150-line how-to cap.
- [x] 5.2 [req: workspaces-doc] Rewrite the `## An enterprise example` section
      of `docs/workspaces/teams.md` so the repository root is itself a
      workspace holding one `--nested` team workspace per team or group.
      State the read-through and write-nearest split, name
      `shipd workspace team`, keep the partial-materialization and member-map
      paragraphs, and keep the per-group-repository isolation remedy. Keep the
      page within the 150-line how-to cap by paying for the additions from the
      replaced text.
- [x] 5.3 [req: workspaces-doc] Update `docs/workspaces.md`'s entries for the
      teams and practical-examples parts to describe the single blessed team
      shape, and update the `teams.md` cross-link in
      `docs/workspaces/getting-started.md` if its wording implies two shapes.
      Confirm no page presents the sibling shape as supported.
- [x] 5.4 [req: workspaces-doc] Run `python3
      plugins/s/skills/document/scripts/docs_lint.py docs/workspaces.md
      docs/workspaces/*.md` and fix every finding until it exits `0`.

## 6. Drift guards and simulation

- [x] 6.1 [req: workspaces-doc] Add a `WorkspaceGuideDriftTests` case to
      `test_workspace_team.py` reading the guide pages from the repo: assert
      no page presents the sibling shape (no "Shape A", no "sibling
      workspaces", no plain-container-repo layout), assert `teams.md` and
      `multi-workspace-repos.md` each name `shipd workspace team`, and assert
      every guide page stays within its doc-type line cap.
- [x] 6.2 [req: workspace-team-wizard] Add a `NestedTeamLayoutTests` case to
      `test_workspace_team.py` that builds the blessed layout with the real
      verbs and simulates usage across it: a base page reads from a team
      workspace and is reported as inherited; a page written from the team
      lands in the team's own store and not the base's; a team declaring its
      own `projects` shadows the base registry while one declaring none
      inherits it; the sync plan from a team lists only that team's members;
      and `wiki-queue-answer` for a base-filed question exits non-zero from
      the team workspace and zero from the base.

## 7. Release and verification

- [x] 7.1 [req: workspace-team-wizard] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` to the next patch version, as the
      cache-snapshot rule in `AGENTS.md` requires for any change touching
      `plugins/s/`.
- [x] 7.2 [req: workspace-team-wizard] Run `python3 -m unittest discover -s plugins/s/skills/build/tests`
      and the docs lint from task 5.4, and fix anything that fails until both
      are clean.
