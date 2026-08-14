## 1. Engine: workspace initialization

- [x] 1.1 [req: workspace-initialization] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add tests for
      `init_workspace`: it creates `.shipd/workspace.json` containing `{}`
      under an existing directory with no discoverable workspace and returns
      the root; it raises an error naming the existing root (writing nothing)
      when a workspace is already discoverable from the target; it raises when
      the target is not an existing directory. Run them and observe them fail
      — the helper does not exist yet.
- [x] 1.2 [req: workspace-initialization] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `init_workspace(path)` next to the workspace-discovery helpers: refuse
      via `find_workspace_root(path)` (error naming the existing root), error
      when `path` is not an existing directory, else create the `.shipd/`
      subdirectory and write `workspace.json` containing `{}` plus a trailing
      newline, returning the absolute root. Stdlib only. Confirm the 1.1 tests
      pass.

## 2. CLI: workspace-init verb

- [x] 2.1 [req: workspace-init-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add tests for the
      `workspace-init <path>` verb: on a bare directory it exits zero and
      prints the created root; where a workspace is already discoverable from
      the target it exits non-zero with an error naming the existing root.
      Run them and observe them fail — the verb does not exist yet.
- [x] 2.2 [req: workspace-init-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, register the
      `workspace-init` subcommand (positional `path`) alongside
      `workspace-show`, add `cmd_workspace_init` calling
      `spec_common.init_workspace` and printing the created root, and extend
      the module docstring's verb table. `workspace-init` must not call
      `_resolve_workspace` — it runs precisely when none exists. Confirm the
      2.1 tests pass.

## 3. Skills: /s:workspace and the initiative pointer

- [x] 3.1 [P3] [req: workspace-setup-skill] Create
      `plugins/s/skills/workspace/SKILL.md` with frontmatter (`name:
      workspace`; a description covering init/show with trigger phrases like
      "set up a workspace", "workspace init", "/s:workspace") and the flow
      from plan.md: `init` — report-and-stop when a workspace is discoverable,
      else one AskUserQuestion for the target root (repo parent recommended
      first, repo root alternative) then drive `workspace-init` and report;
      `show` — wrap `workspace-show`, read-only. Model the document's tone and
      structure on `plugins/s/skills/initiative/SKILL.md`, including resolved
      CLI paths and an ending-and-stop section.
- [x] 3.2 [P3] [req: initiative-workflow-skill] In
      `plugins/s/skills/initiative/SKILL.md`, update the "No workspace →
      stop" rule in the workspace-first section: still report the CLI error
      verbatim and write nothing, now also pointing the user at
      `/s:workspace init` as the setup path.

## 4. Roster, docs, version

- [x] 4.1 [P4] [req: workspace-setup-skill] In `AGENTS.md` (repo root), add
      `/s:workspace` to the skill sentence in "Spec layout and lifecycle"
      (workspace setup and roster).
- [x] 4.2 [P4] [req: workspace-setup-skill] In `docs/onboarding/05-scaling.md`,
      after the sentence that no workspace is a normal state, add one line
      that `/s:workspace init` (the CLI's `workspace-init` verb) creates one
      when initiatives are wanted.
- [x] 4.3 [P4] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.2.8 to 0.2.9 (plugin content changed: new skill, edited skill, new
      CLI verb).
- [x] 4.4 [req: *] Run the full engine test suite under
      `plugins/s/skills/build/tests/` and observe every test pass.
