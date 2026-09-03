# workspace-universe-seam
Status: verified

## Idea

One shared workspace-universe discovery seam in `spec_common`, consumed by
every board-shaped read surface — bare `show`, the dashboard board/TUI,
`epic-show`, `locate`, and metrics' epic discovery — so they can never
disagree about which epics exist or where they live.

### Motivation

Three discovery implementations coexist: `spec_status._workspace_project_roots`
(private, project-aware, bare `show` only), `all_epic_slugs_with_roots`
(root+worktrees, status CLI + dashboard), and metrics' direct `.shipd/epics/*`
walks (root only) — so the delivery board, `epic-show`, `locate`, and metrics
all miss declared workspace projects that bare `show` now reports.

### Details

- Move project-universe discovery into `spec_common`: `workspace_project_roots(root)`
  and `aggregation_universes(root)`, with the shipped trigger rule (registry
  discoverable AND root inside no declared project repo) and fail-soft skips.
- Bare `show` consumes the shared seam (behavior unchanged; the private
  `_workspace_project_roots` is deleted).
- `dashboard` `board`/TUI aggregate per universe: project epics join the board
  with `[<project>]` markers and fully live actions rooted at their repo.
- `epic-show`, `show <epic>` fallback, and `locate` resolve across universes
  (root, its worktrees, then project universes in slug order), annotating
  project-hosted results; JSON gains `project` fields.
- `metrics.py` swaps its direct epic walks for the shared worktree-aware
  discovery — per-repo scope, no project universes.

Affected capabilities: `shipd-workspace` (added:
`workspace-universe-discovery`), `spec-status` (modified:
`workspace-board-report`, `epic-status-verbs`, `locate-verb`, `json-output`),
`delivery-dashboard` (modified: `board-aggregation`), `delivery-metrics`
(modified: `metrics-engine`). Impact:
`plugins/s/skills/build/scripts/{spec_common,spec_status,dashboard,metrics}.py`,
`tests/{test_spec_common,test_spec_status,test_metrics}.py`,
`tests_textual/test_dashboard.py`, `plugins/s/skills/status/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json` (→ 0.6.171). Stdlib-only throughout.

### Non-goals

- Mutating verbs (`epic-sync`, `epic-set-status`, `set-status`, `use`) stay
  invocation-root-only — no verb writes into another project's repo.
- No cross-project metric aggregation: metric semantics (git timestamps,
  build log, run reports) stay per-repo; only metrics' *discovery code* is
  unified.
- Autopilot untouched — it drives one epic inside one repo.
- No recursion into a project repo's own nested workspaces, and no change to
  the trigger rule shipped in workspace-board-aggregation.

## Implementation

- **Seam home: `spec_common.py`** (shipd-workspace workspace-universe-discovery),
  beside `registry_root`/`project_of`. `workspace_project_roots(root)` returns
  `[(project_slug, repo_root)]` — implemented on `load_workspace` +
  `repo_entry_path` directly (not on `spec_status`'s display helpers): trigger
  `registry_root(root)` resolves AND `project_of(reg_root, root) is None`;
  projects in slug order, repos in declaration order, paths joined to the
  registry root; skip non-dict projects/repo entries, non-directories,
  real-path duplicates, and the invocation root's own real path; any
  `ConfigError` → `[]`. `aggregation_universes(root)` returns
  `[(None, root)] + workspace_project_roots(root)`. Rejected: keeping the seam
  in `spec_status` — registry logic would stay split across modules and
  `dashboard` would depend on a status-CLI private.
  Verified premise: bare `show` run in this repo (`workspace: none
  discoverable` per `config-show`) prints the single-universe board — the
  no-registry trigger arm is today's observed behavior and must stay
  byte-identical.
- **`spec_status.py`**: delete `_workspace_project_roots`;
  `_workspace_report_data` builds its universes from
  `sc.aggregation_universes(root)` (rendering unchanged). New helper
  `_epic_hosting_universe(root, slug)` → `(project, universe_root,
  hosting_root)` or `None`: probes each universe in seam order with the
  existing `_epic_hosting_root(universe_root, slug)` (so each universe keeps
  its own root-then-worktrees precedence, the invocation root's universe
  winning overall). `cmd_epic_show` and `show`'s epic fallback resolve
  through it: report data comes from `_epic_report_data(universe_root, slug)`
  so member states and `[worktree]` markers derive relative to the owning
  universe; the data gains `"project"` (slug or `None`), text prints a
  `project: <slug>` line directly after the metadata lines (after any
  `worktree:` line) only for project-hosted epics. `cmd_locate` iterates the
  universes in order, probing each with its existing root+worktrees walk;
  match blocks from a project universe append a `project: <slug>` line, and
  JSON locate rows always carry `project` (slug or `null`).
- **`dashboard.py`**: `build_board(root, epic=None)` iterates
  `sc.aggregation_universes(root)`; per universe it runs today's pipeline
  (`_epic_slugs(universe_root)`, `_epic_board(universe_root, slug,
  hosting_root)`, `standalone_changes(universe_root, per-universe exclusion
  set)`). Each epic dict and standalone row gains `"project"` (slug or
  `None`) and each epic dict gains `"universe_root"` (absolute) — heartbeats
  and run reports already read from the hosting root, which now lives inside
  the owning universe. An explicit `--epic` resolves against the universes in
  seam order, first hosting universe wins. The human board and the TUI epic
  group header render ` [<project>]` after the `[worktree]` marker; TUI
  action dispatch passes `epic["universe_root"]` (not the board root) to
  `build_plan_launch`/`build_run_launch`/`build_epic_run_launch`/
  `build_open_launch`, so a project member's worktree, autopilot `--root`,
  and session cwd land in that project's repo. Rejected: display-only
  project rows — half-consistent, and the launch builders already take a
  root parameter.
- **`metrics.py`**: replace the direct `epics_dir` listings (the WIP snapshot
  walk, the outcome-attribution walk, and the epics block, metrics.py:423/
  526/1519) with `ss.all_epic_slugs_with_roots(root)`, reading each epic from
  its hosting root; resolve single-epic paths (metrics.py:1291/1482) through
  `ss._epic_hosting_root(root, epic)` with the current root-relative path as
  the not-found fallback. Explicitly per-repo: never `aggregation_universes`.
  Derivation stays pure/deterministic; only discovery breadth changes
  (worktree-hosted epics now count, matching the board).
- **Ordering and precedence everywhere**: the invocation root's universe
  first, then project universes in slug order; within a universe, root before
  its worktrees (existing seam); epic slugs never dedup across universes —
  name-scoped verbs take the *first* hosting universe.
- **Docs and version**: `/s:status` SKILL.md gains the universe behavior for
  `epic-show`/`locate` and the board section's project markers;
  `plugin.json` → `0.6.171`.
- Risk: TUI launch call sites are spread through the textual app — the task
  names the four builders; the executor greps their call sites and threads
  `universe_root` through each, and the textual suite pins the behavior.
