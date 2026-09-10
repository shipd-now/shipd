# workspace-repo-map
Status: verified

## Idea

A machine-local dotfile at the workspace root maps registry members to
existing local checkouts, so a member can live anywhere on disk instead of
being re-cloned under the workspace root.

### Motivation

Workspace member resolution is containment-only — every verb joins
`ws_root + path` — so a developer's existing checkout (e.g.
`~/projects/shipd`) is invisible to the workspace at
`~/workspaces/shipd-now`, forcing a duplicate materialized clone that
silently diverges from the one actually worked in. The map makes the
existing checkout *be* the member on this machine, without touching the
committed registry.

### Details

- New optional file `<workspace-root>/.shipd-workspace.local.json` with a
  `repos` object mapping manifest member paths to local checkout paths —
  machine-local, never committed.
- One new resolution seam in `spec_common` returns the mapped destination
  when present, else `<ws_root>/<path>`; the three join sites route through
  it (`workspace-show`'s present check, `workspace_project_roots`,
  `_plan_member`).
- `project_of` additionally matches containment against mapped paths, so a
  mapped external checkout resolves to its declaring project.
- `workspace-show` annotates mapped members; the sync planner never
  materializes into a mapped path (action `none`, drift note when the
  mapped target is missing or has a mismatched origin).

Affected capabilities: `shipd-workspace` (modified + one added
requirement). Impact: `plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_common.py`,
`plugins/s/skills/build/tests/test_spec_status.py`, `docs/workspaces.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies
(stdlib-only, per the constitution).

### Non-goals

- No reverse lookup (resolving which workspace an outside checkout belongs
  to via origin-URL matching) — a follow-up change; upward discovery is
  untouched.
- No `/s:workspace` interview to author the map — a follow-up change; this
  change ships the engine contract the skill will drive.
- No new `.shipd-config.json` key — the map is a standalone file, so
  `RECOGNIZED_CONFIG_KEYS` and the config-sample coverage stay untouched.
- No writing or repairing of the map by any engine verb — the engine reads
  and reports; humans (and later the skill) write it.
- No doctor check for the map — follow-up territory.

## Implementation

- **File and shape.** `<workspace-root>/.shipd-workspace.local.json`:
  `{"repos": {"<manifest path>": "<local path>"}}`. Values may carry `~`
  (expanded on read) or be relative (resolved against the workspace root);
  stored verbatim, resolved at read time. Rejected: a config key in
  `.shipd-config.json` — the layered merge is per-top-level-key, so a local
  `workspace` object would clobber the committed registry rather than
  overlay it, and the root's config file is committed anyway.
- **Keying.** Map keys are manifest member `path` values — the registry
  validates them unique across projects (ambiguous-ownership error), while
  `url` is optional. Rejected: keying by url.
- **The seam.** `spec_common.member_dest(ws_root, path)` (name final):
  loads the map (module-cached per root is unnecessary — read per call like
  `load_workspace`), returns the mapped absolute destination for `path`
  when an entry exists, else `os.path.join(ws_root, path)`. A second
  helper `load_repo_map(ws_root)` owns the read: absent file → `{}`;
  malformed JSON, a non-object top level, a non-object `repos`, or a
  non-string/empty value → `ConfigError` naming the file (the config
  file's own precedent). Keys matching no manifest path are preserved in
  the load and surfaced by `workspace-show` as a note — never an error, so
  a stale map entry cannot brick every workspace verb.
- **Consumers routed through the seam:**
  - `spec_status.py` show path (`_project_repo_report`, the
    `os.path.join(ws_root, path)` at ~3273): `present` probes the mapped
    destination; the human report appends `[mapped -> <path>]` for mapped
    members; the JSON report gains a `mapped` field carrying the resolved
    destination (absent for unmapped members).
  - `workspace_project_roots` (`spec_common.py` ~1837): `repo_root`
    becomes the seam's result, so board aggregation and `locate` read the
    mapped checkout's epics/changes.
  - `_plan_member` (`spec_common.py` ~1962): a mapped member's `dest` is
    the mapped path and its record carries `"mapped": <dest>`; the ladder
    is bypassed — action is always `none`. Present-as-git keeps the origin
    drift check against the manifest `url`; an absent mapped destination
    records state `absent`, action `none`, and a drift note naming the
    mapped path ("mapped path does not exist; fix or remove the map
    entry"). The planner never emits a command targeting a mapped path —
    materializing into a directory the user owns outside the workspace is
    the one repair this engine must never attempt.
  - `project_of` (`spec_common.py` ~1746): for each repo entry, when a map
    entry exists, additionally test containment of the target against the
    mapped destination's real path (same most-specific-wins scoring,
    specificity measured by the manifest path's part count as today);
    workspace-relative matching for unmapped entries is unchanged.
- **Gitignore block unchanged.** The marked member block keeps listing
  manifest paths — a mapped member's manifest path staying ignored is
  harmless and keeps the block manifest-shaped.
- **Docs.** `docs/workspaces.md` gains a "Mapping members to existing
  checkouts" section: the file, its shape, planner behavior, and the
  never-materialize rule.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` `0.6.198` →
  `0.6.199`, same PR (plugin-cache rule).
- **Risk.** A map pointing two manifest paths at one local checkout would
  double-aggregate a universe; guarded by `workspace_project_roots`'
  existing realpath de-dup (`seen` set), which already collapses duplicate
  real paths silently. A mapped path that is a *descendant* of the
  workspace root is legal and needs no special casing — the seam returns
  it like any other absolute path.

## Verification baselines

The engine suite passes on main via CI's exact invocation
(`python3 -m unittest discover -s plugins/s/skills/build/tests` → `OK`,
observed 2026-09-10), and `workspace-sync --json` against the real
`~/workspaces/shipd-now` workspace emits three `action: none` member
records plus a clean gitignore record — the shapes the new tests extend.
