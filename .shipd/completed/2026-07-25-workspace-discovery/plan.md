# workspace-discovery
Status: verified
Epic: workspace-projects
Theme: spec-engine

## Idea

The `workspace-projects` epic needs its foundation: nothing in the engine can
locate a workspace today, so initiative briefs, projects, and cross-repo
references have no ground to stand on. Per the epic's Decisions, the workspace
root is the nearest ancestor directory containing `.shipd/workspace.json`,
and that same file is the registry — but no code implements the search or the
load.

This change lands the two discovery primitives every later member consumes:

- `find_workspace_root(start)` in `spec_common.py` — upward search from
  `start` to the filesystem root for the nearest ancestor containing
  `.shipd/workspace.json`; `None` when no marker exists.
- `load_workspace(ws_root)` in `spec_common.py` — parse the registry with
  stdlib `json`, returning the dict; a clear error naming the file on
  malformed JSON or a non-object top level; unknown keys tolerated for
  forward compatibility.
- A brief Workspace subsection in `am/README.md` and the plugin version bump
  (0.2.1 → 0.2.2).

### Non-goals

- No project semantics: validating `projects` entries, repo lists, and the
  implicit default project belongs to the `project-groups` member change —
  this change loads the registry as a tolerant dict and interprets nothing.
- No consumers: no lint, status, or skill behavior changes — `Initiative:`
  resolution and initiative verbs arrive with the `initiative-briefs` member.
- No workspace creation/scaffolding command.

Affected capabilities: `shipd-workspace` (new). Impact:
`plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/tests/test_spec_common.py`, `am/README.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

## Implementation

- **Both primitives live in `spec_common.py`** beside `load_config`, per the
  epic's Design ("everything else consumes these two calls; nothing else
  touches the filesystem above the repo"). New module constant
  `WORKSPACE_MARKER = os.path.join(".shipd", "workspace.json")`.
- **Search semantics.** `find_workspace_root(start)` walks from
  `os.path.abspath(start)` upward via `os.path.dirname` until the path stops
  changing (filesystem root), returning the first directory whose
  `WORKSPACE_MARKER` is a file — `start` itself included, nearest ancestor
  wins. It makes no git assumptions: any directory works as `start`.
  Rejected: requiring a git repo — the workspace root itself is not a repo.
- **Load semantics.** `load_workspace(ws_root)` reads
  `<ws_root>/.shipd/workspace.json` and raises the existing `ConfigError`
  (same class `load_config` uses — one config-parse error type) naming the
  file when the file is missing, unparseable, or not a JSON object. It
  returns the parsed dict unchanged — unknown keys pass through untouched,
  honoring the epic's "room for future workspace state". Rejected: a schema
  whitelist now — it would force the `project-groups` member to relax it.
- **Risk:** an unbounded upward search crossing into `$HOME` or `/` and
  finding an unintended stray marker. Accepted per the epic (nearest-ancestor
  is the contract); the README documents that a marker should sit at the
  intended workspace root and nowhere else.
