# workspace-sync-plan
Status: verified
Epic: portable-workspaces

## Idea

Add the network-free materialization planner: a `workspace-sync` engine verb
that reads the manifest and local disk and emits the per-member
materialization/drift plan the clone skill will execute.

### Motivation

A cloned job workspace carries a manifest full of URLs but no member repos,
and nothing can tell a machine how to materialize them cheaply or whether the
on-disk state has drifted from the manifest.

### Details

- `spec_common.py` gains the planning function and local-git probes;
  `spec_status.py` gains the `workspace-sync` verb (keyed blocks, `--json`
  lines, opt-in `--write-gitignore`).
- A new `clone_sources` config key lists directories probed for local
  candidate clones (origin-URL match).
- Actions follow the epic's ladder: none/drift for present members;
  worktree → reference-clone → full clone → unmaterializable for absent ones.

Affected capabilities: `shipd-workspace`, `spec-status`, `shipd-config`
(modified/added requirements). Impact: `spec_common.py`, `spec_status.py`,
their tests, plugin version. Reuses `repo_entry_path` and the marked
gitignore block from `workspace-repo-manifest`.

### Non-goals

- No cloning, fetching, or any network git — execution is the
  `workspace-clone-skill` member's job; this verb only plans (plus the
  opt-in local gitignore-block write).
- No materialization-preference keys (e.g. forcing a clone over a worktree):
  the ladder is fixed cheapest-first per the epic.
- No automatic drift repair: a mismatched origin URL or an occupied non-git
  path is reported, never modified.
- No implicit base-workspace probing when `clone_sources` is undeclared —
  the candidate set is simply empty (oracle-settled).

## Implementation

- **Planner as a pure function.** `plan_workspace_sync(ws_root, config)` in
  `spec_common.py` returns one record per manifest repo entry plus a
  gitignore record — a function of (manifest, config, local disk), fully
  unit-testable. Probes are local subprocess git only:
  `git rev-parse --is-inside-work-tree`, `git remote get-url origin`,
  bare-repo detection via `git rev-parse --is-bare-repository`. Never the
  network (constitution).
- **The ladder, concretely.** Dest present and a git work tree → action
  `none`; additionally a `drift` note when its origin URL differs from the
  manifest `url`. Dest present but not git → state `occupied`, action
  `none`, drift note. Dest absent: probe each `clone_sources` directory's
  immediate children for a git repo whose origin equals the manifest `url` —
  first match wins in list order; a work-tree candidate → action `worktree`
  (suggested command `git -C <src> worktree add <dest> -b
  job/<ws-basename> [<branch>]`, start point the manifest `branch` when
  declared); a bare candidate → action `reference-clone` (`git clone
  --reference <src> [--branch <branch>] <url> <dest>`); no candidate but a
  `url` → action `clone`; no `url` → action `unmaterializable` with reason.
  Suggested commands are advisory strings for the executor; the planner
  never runs them.
- **`clone_sources` (oracle-settled).** Optional config key, any layer, a
  list of directory path strings (`~` expanded); undeclared resolves to an
  empty candidate list; a malformed value is a verb error naming the key.
  Rejected: implicit base-workspace registry probing — hidden coupling and
  machine-dependent plans.
- **Gitignore maintenance (oracle-settled posture).** The planner compares
  the marked member block (`GITIGNORE_MEMBERS_BEGIN/END`) against the
  manifest's member paths and reports missing/stale lines; the verb is
  plan-only by default, and `--write-gitignore` rewrites just the block
  content idempotently — the same write the init verb already owns.
- **Verb contract.** `workspace-sync` requires a discoverable workspace and
  a registry that passes `validate_workspace` (errors exit non-zero
  printing the findings). A computed plan always exits 0 — drift and
  unmaterializable entries are informational records, not failures. Output:
  one keyed block per member (`member:`, `path:`, `state:`, `action:`, and
  `source:`/`url:`/`command:`/`drift:` as applicable) then a `gitignore:`
  section; `--json` emits one JSON object per record (`kind`:
  `member`/`gitignore`), the `spec_merge --json` lines precedent, for the
  clone skill to parse.
- **Risks.** Probe cost on large source dirs — bounded to immediate
  children with at most two git calls per child. Worktree branch-name
  collisions (`job/<ws-basename>` already existing in the source) surface
  at execution, not planning; the command is advisory and the executor owns
  failure handling.
