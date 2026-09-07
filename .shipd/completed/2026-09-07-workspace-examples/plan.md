# workspace-examples
Status: verified

## Idea

Add a "Practical examples: multi-workspace repos" section to
`docs/workspaces.md` that walks the two supported shapes for storing several
workspaces in one repo, with what-is-stored-where tables, usage commands, and
a pros/cons comparison.

### Motivation

The guide documents single-workspace repos (§2–§5), nesting (§6), and team
sharing (§8), but a user asking "can one repo hold several workspaces so
teammates check it out and use only the ones they care about?" has to derive
the answer from three sections and the engine source. The two viable shapes
deserve one worked walkthrough with their trade-offs side by side.

### Details

- One new `## 10. Practical examples: multi-workspace repos` section at the
  end of `docs/workspaces.md`, before nothing (it becomes the last section).
- Two worked examples: **Shape A** — sibling workspaces in a plain repo whose
  root is not a workspace; **Shape B** — the repo root as a base workspace
  with `--nested` job workspaces (building on §6).
- Per shape: a layout diagram with tracked/ignored annotations, a
  what-lives-where table, the setup and day-to-day commands, and a closing
  pros/cons comparison with a when-to-pick-which note.

Affected capabilities: `shipd-workspace` (added `workspaces-doc-examples`).
Impact: `docs/workspaces.md` only — nothing under `plugins/s/`, so no plugin
version bump (AGENTS.md scopes the bump to `plugins/s/` changes).

### Non-goals

- No engine or verb changes — both shapes already work; this is documentation
  of existing behavior.
- No change to the `/s:workspace clone` verb's one-workspace-per-repo
  bootstrap; the section tells multi-workspace users to `git clone` normally.
- No access-control story: the section states plainly that git has no
  per-directory permissions and separate repos are the isolation boundary.
- No renumbering or rewriting of existing sections 1–9.

## Implementation

- **Section structure is binding** (the executor writes prose to this frame):
  1. One intro paragraph naming the goal: one repo, several workspaces,
     clone-once, sync only what you use.
  2. **Shape A — sibling workspaces, plain repo root.** Layout diagram rooted
     at `~/workspaces/company/` (the repo), containing
     `workspace-documents/` and `ws-tasks-management/`, each with
     `.shipd-config.json`, `.shipd/wiki/`, and gitignored member checkouts;
     annotate tracked vs machine-local lines like the §2 diagram does. Setup:
     `git init` (or clone) the repo, then `shipd workspace init
     <repo>/workspace-documents` per workspace — no `--nested`, because the
     repo root declares no workspace, and discovery is nearest-ancestor so
     siblings never interfere. Note that `init --git` inside the repo only
     seeds the members `.gitignore` block (it detects the enclosing work
     tree and never `git init`s a nested repo), and that a plain init gets
     the block seeded on first `shipd workspace sync` anyway.
  3. **Shape B — base workspace root with nested jobs.** Layout diagram
     rooted at `~/workspaces/acme-base/` per §6, extended with two nested
     jobs; setup via `shipd workspace init <base>/<job> --nested --git`;
     one paragraph on inheritance (reads fall through nearest-first to the
     base wiki; writes always land in the nested job's own store — cite §6
     rather than restating its full inheritance list).
  4. **What lives where** — one table per shape (or one shared table with a
     per-shape column) covering: manifest, wiki pages, oracle queue,
     initiatives, member repos, and — Shape B only — the inherited base
     wiki; each cell saying tracked-in-the-shared-repo vs machine-local.
  5. **Using either option** — clone the repo with plain `git clone` (the
     `/s:workspace clone` verb targets one-workspace repos), `cd` into the
     workspace you care about, `shipd workspace sync` there; uninteresting
     workspaces stay a few KB of manifest+wiki; knowledge travels by
     ordinary pull/push exactly as §8 describes (link, don't restate).
  6. **Pros and cons** — a compact table: Shape A = strict isolation,
     simplest mental model, no shared knowledge, per-workspace conventions
     duplicated; Shape B = shared base wiki inherited everywhere,
     deliberate `--nested` opt-in, one more level of indirection, base
     writes need their own discipline. Close with one when-to-pick-which
     sentence and the shared caveat that git offers no per-directory access
     control — separate repos are the isolation boundary.
- **Convention compliance is binding**: every command in the section uses the
  `shipd` binary (`shipd workspace init|sync`), never a `spec_status.py`
  path; examples stay under a `~/workspaces/` parent; the term is
  "workspace" throughout — all three pinned by the existing `workspaces-doc`
  requirement, which this section must not violate.
- **Delta shape**: one ADDED requirement (`workspaces-doc-examples`) rather
  than a MODIFIED restate of the long `workspaces-doc` requirement — the new
  section is additive and the existing requirement's text stays untouched.
  Rejected: MODIFIED restate — a large hand-copied block for zero semantic
  change to the existing contract.
- **Verified premises** (from this session, against the merged engine):
  `shipd workspace init` refuses under an already-discoverable workspace and
  `--nested` is the deliberate override (docs §6 + `init_workspace`);
  `write_members_gitignore_block` seeds the members block on sync when init
  did not (`spec_common.py`); `init --git` skips `git init` inside an
  existing work tree (`spec_common.py` `_inside_git_work_tree` check); wiki
  auto-commits land in the enclosing repo's work tree.
- Risk: the section drifting from §6/§8 phrasing — guarded by linking to
  those sections instead of restating their contracts.
