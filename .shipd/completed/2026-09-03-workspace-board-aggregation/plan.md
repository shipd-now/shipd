# workspace-board-aggregation
Status: verified

## Idea

Make the bare `show` workspace board report aggregate every project repo
declared in the workspace's `workspace.projects` registry, so the "workspace
board" name matches its behavior.

### Motivation

Running `spec_status.py show` from a multi-project workspace root prints an
empty board (`0 specs · 0 epics · 0 initiatives`) even when declared member
projects hold real epics and specs, because epic discovery only probes the
invocation root and its own `.worktrees/` — the `workspace.projects` registry
that `workspace-show` reads correctly is never consulted.

### Details

- Extend the bare-`show` board report to aggregate, alongside the invocation
  root's own universe, one universe per project repo declared in the
  discoverable workspace registry — each repo aggregated exactly as a root is
  today (its epics, its worktrees, its member states, its standalone changes).
- Aggregate only for workspace-level invocations: when the invocation root
  lies inside a declared project repo (project resolution names a project),
  or no registry is discoverable, output stays byte-identical to today.
- Label rows from a project universe with the owning project slug — a
  `[<project>]` text marker and a `project` field in `--json`.
- Update the `/s:status` skill doc and the CLI help/docstrings to match.

Affected capabilities: `spec-status` (modified: `workspace-board-report`,
`json-output`). Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/status/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`
(version bump). No new dependencies (stdlib-only per the constitution).

### Non-goals

- No change to the dashboard's `board` verb or the `delivery-dashboard`
  spec's `board-aggregation` — this change touches only the status CLI's
  bare-`show` report.
- No change to `epic-show`, `epic-sync`, `locate`, or any mutating verb —
  `_epic_candidate_roots` and `_member_state_with_root` keep their current
  root+worktrees contract for every existing caller.
- No recursion into a project repo's own nested workspaces, and no
  aggregation of registries above the effective `registry_root`.
- No `--json` shape change for `epic-show` rows — only the bare-`show`
  workspace report's rows gain the `project` field.

## Implementation

- **Aggregation trigger — workspace-level invocations only.** The report
  aggregates project universes iff `sc.registry_root(root)` resolves AND
  `sc.project_of(reg_root, root)` is `None` (the invocation root is not
  inside any declared project repo). This preserves today's per-repo board
  when `show` runs inside a member repo, and fixes the empty board at the
  workspace root. Rejected: aggregating whenever a workspace is discoverable
  — it would change the per-repo view users rely on inside member repos.
  Verified premise (user repro, v0.6.169): from a workspace root declaring
  `ukan-api`/`ukan-frontend`, `show` printed `0 specs · 0 epics ·
  0 initiatives` with all lanes empty; from inside `ukan-api` it printed
  `7 specs · 1 epics · 1 initiatives` correctly.
- **New discovery helper, not a change to the shared seams.** Add
  `_workspace_project_roots(root)` in `spec_status.py` returning
  `[(project_slug, abs_repo_root)]`: projects in slug order via
  `_load_projects(reg_root)`, each project's repos in declaration order via
  `sc.repo_entry_path`, paths resolved `os.path.join(reg_root, rel_path)`;
  skip entries whose path is not a directory, whose realpath duplicates an
  earlier entry, or whose realpath equals the invocation root's. Returns `[]`
  when the trigger above says no aggregation. Rejected: extending
  `_epic_candidate_roots` — it feeds `_epic_hosting_root`, `epic-sync`,
  `locate`, and the dashboard, and must not silently adopt other projects'
  epics into mutating or single-repo verbs.
- **Per-universe aggregation in `_workspace_report_data`.** Iterate universes
  `[(None, root)] + _workspace_project_roots(root)`. Per universe: epics via
  `all_epic_slugs_with_roots(universe_root)`, member state via
  `_member_state_with_root(universe_root, slug)` (worktree flag =
  `hosting_root != universe_root`), standalone via
  `standalone_changes(universe_root, member_slugs_of_that_universe)`
  (worktree flag = `location != abspath(universe_root)`). Member-slug
  exclusion sets are per universe — a slug in one project's epic never
  suppresses another project's standalone change. Row collection keeps the
  global epic-rows-then-standalone-rows grouping the shipped rollup relies
  on: all epic rows (root universe first, then projects in slug order), then
  all standalone rows in the same universe order. Epic slugs are NOT deduped
  across universes — separate projects are separate spec universes; rows are
  distinguished by their `project` field. Totals (`specs`, `epics`) sum
  across universes; `initiatives` counts distinct slugs across universes.
- **Row shape.** Every workspace-report row gains `"project"`: the owning
  project slug, `null`/`None` for invocation-root rows. Text rendering in
  `_workspace_report_lines`: non-shipped rows append a ` [<project>]` marker
  after the existing ` [worktree]` marker position; the SHIPPED rollup keys
  its counts by `(epic, project)` in insertion order, rendering
  `<epic> [<project>] (<n>)` for project rows and today's `<epic> (<n>)`
  otherwise. With no project universes, all rows have `project=None` and the
  rendering is byte-identical to today.
- **Fail-soft everywhere.** Absent repo directories, unreadable project repo
  configs (`sc.ConfigError` already handled inside
  `all_epic_slugs_with_roots`/`standalone_changes`), and an unloadable
  registry all skip silently — display never crashes on an invalid registry
  (matching `_load_projects`' contract).
- **Docs and version.** Update the "whole delivery board" section in
  `plugins/s/skills/status/SKILL.md`, the module docstring/help strings in
  `spec_status.py` that describe the bare-`show` report, and bump
  `plugins/s/.claude-plugin/plugin.json` to `0.6.170` (every `plugins/s/`
  change bumps the version, per AGENTS.md).
- **Tests (constitution: every engine change carries tests).** Extend
  `plugins/s/skills/build/tests/test_spec_status.py` — stdlib-only, no
  `textual` — covering aggregation, the trigger boundary, markers, JSON
  `project`, skip paths, and single-repo byte-identity.

Risk: a huge registry could slow the bare `show`; accepted — discovery is one
`isdir` per declared repo plus the same per-root walk the board already does,
and absent repos short-circuit.
