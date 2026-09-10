# workspace-reverse-lookup
Status: verified

## Idea

Workspace discovery gains two fallback rungs below the ancestor search — an
explicit repo-local pointer, then an origin-URL match against the workspaces
under `workspaces_root` — so a checkout living anywhere on disk resolves the
workspace that declares it.

### Motivation

`workspace_chain` is ancestor-only, so a checkout outside the workspace tree
resolves no workspace no matter what the registry declares — which is how
eight taught wiki pages landed in a repo-local fallback store instead of the
workspace wiki. The registry already carries every member's clone `url`, so
membership is derivable without a single new declaration.

### Details

- `workspace_chain(start)` keeps its upward search unchanged and, only when
  that yields an empty chain, descends two new rungs: a `workspace_root`
  pointer in the starting repo's own `.shipd-workspace.local.json`, then a
  normalized origin-URL match against each workspace directly under the
  declared `workspaces_root`.
- A unique match resolves the chain as `workspace_chain(matched-root)`, so
  enclosing workspaces above the matched root still chain; an ambiguous
  match resolves nothing and warns once on stderr, naming the candidates
  and the pointer remedy.
- Every existing consumer (wiki resolution, registry root, initiative
  resolution, universe discovery) inherits the fallback through the one
  seam, untouched.

Affected capabilities: `shipd-workspace` (one modified requirement, one
added). Impact: `plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/tests/test_spec_common.py`, `docs/workspaces.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump). Stdlib + local git
probes only — never the network.

### Non-goals

- No writing of the pointer or the member map by any engine verb — that is
  the `workspace-map-verb` change.
- No change to `member_dest`, the member map's shape, or the sync planner.
- No new config key — the scan anchors on the existing `workspaces_root`
  (shipd-config workspaces-root-key); when it is undeclared the scan rung
  simply does not exist.
- No behavior change for any start that already resolves an ancestor
  workspace, and none in bare checkouts with no home config (CI).

## Implementation

- **Ladder order: ancestor > pointer > URL scan.** The explicit beats the
  inferred: a pointer names one root deliberately; the scan derives one.
  Rejected: scan before pointer — an ambiguous scan would then shadow an
  explicit, unambiguous declaration.
- **The pointer reuses the machine-local dotfile family.** A repo-root
  `.shipd-workspace.local.json` carrying `workspace_root` (a path, `~`
  expanded, resolved against the file's directory when relative) — the
  same `REPO_MAP_FILENAME`, disjoint keys: `repos` at a workspace root,
  `workspace_root` at a member repo root. One filename to gitignore and
  document. Rejected: a second dotfile name — two files with identical
  never-commit semantics is one file too many.
- **Pointer semantics.** The pointed directory must itself declare
  `workspace` in its `.shipd-config.json`; when it does not, the rung
  resolves nothing and warns once naming the pointer file and the target —
  report, never repair. A valid pointer resolves the chain as
  `workspace_chain(pointed-root)`.
- **Scan rung.** Requires `workspaces_root` declared (layered config from
  `start`) and expanding to an existing directory, and `start` to lie
  inside a git work tree whose `origin` URL is readable (one local
  `git -C <start> remote get-url origin` probe; any failure disables the
  rung silently). Candidates are the immediate children of
  `workspaces_root` whose own `.shipd-config.json` declares `workspace`;
  a candidate matches when any declared member `url` normalizes equal to
  the origin URL. Normalization: strip a `<scheme>://` prefix or
  `<user>@` prefix, convert `host:path` to `host/path`, strip one
  trailing `.git` and trailing slashes, case-fold — so
  `git@github.com:acme/repo.git` equals `https://github.com/Acme/Repo`.
  Stated once in a small helper with its own tests; the shipd-app sync's
  `workspace_id` normalization is the precedent.
- **Ambiguity and absence.** Zero matching candidates → empty chain,
  silent (today's behavior). Two or more → empty chain plus exactly one
  stderr warning naming every matching root and the pointer remedy
  ("declare `workspace_root` in `<repo>/.shipd-workspace.local.json`");
  never an exception, so no consuming verb changes its exit behavior.
- **Recursion guard.** The fallback computes `workspace_chain` of the
  resolved root; that call starts *at* a declaring directory, so its
  ancestor search is non-empty and the fallback cannot recurse. Guarded
  by construction, asserted by a test.
- **Performance.** The rungs run only on an empty chain: one git probe
  plus one config read per immediate child of `workspaces_root` (single
  digits). No caching — same per-call read policy as `load_repo_map`,
  and the empty-chain path was already the cold path.
- **Docs.** `docs/workspaces.md` gains a "Resolving from outside the
  workspace" section: the ladder, the pointer key, normalization, and the
  ambiguity remedy.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` `0.6.199` →
  `0.6.200` (reconciled against main at build time if it moved).
- **Risk.** A slow or hung git probe would tax every no-workspace verb
  call; guarded with the same short timeout idiom the repo's other git
  probes use, failure reading as "rung disabled".
