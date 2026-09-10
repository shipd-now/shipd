## ADDED Requirements

### Requirement: Workspace reverse lookup
id: workspace-reverse-lookup

When the upward search yields an empty chain, the engine SHALL attempt two
fallback rungs in order, using local probes only and never the network.
First, where the starting repo's root carries a `.shipd-workspace.local.json`
declaring `workspace_root`, the engine SHALL resolve the chain from that
pointed directory when it declares `workspace` in its own
`.shipd-config.json`, and otherwise SHALL resolve nothing and warn once on
stderr naming the pointer file and the target. Second, where the layered
configuration declares `workspaces_root` naming an existing directory and
the starting directory lies in a git work tree with a readable `origin` URL,
the engine SHALL match that URL — normalized with scheme, user prefix, and
one trailing `.git` stripped, `host:path` read as `host/path`, trailing
slashes dropped, case-folded — against the declared member `url`s of each
immediate child of `workspaces_root` whose config declares `workspace`:
exactly one matching child SHALL resolve the chain from that child; two or
more SHALL resolve nothing and warn once on stderr naming every matching
root and the pointer remedy. If neither rung resolves — no pointer, no
`workspaces_root`, no readable origin, or no match — then the chain SHALL
stay empty with no warning, exactly as before.

#### Scenario: Origin URL resolves the owning workspace

- **GIVEN** a checkout outside any workspace whose origin URL matches one
  member `url` (differing only by scheme and a `.git` suffix) declared by
  exactly one workspace under the declared `workspaces_root`
- **WHEN** workspace discovery runs from inside the checkout
- **THEN** the resolved workspace root is that workspace

#### Scenario: Pointer beats the scan

- **GIVEN** a checkout whose repo root's `.shipd-workspace.local.json`
  declares `workspace_root` naming workspace A, while the URL scan would
  match workspace B
- **WHEN** discovery runs from the checkout
- **THEN** the resolved root is A

#### Scenario: Ambiguous match resolves nothing and names the remedy

- **GIVEN** two workspaces under `workspaces_root` each declaring a member
  `url` matching the checkout's origin
- **WHEN** discovery runs from the checkout
- **THEN** no workspace resolves and one stderr warning names both roots
  and the `workspace_root` pointer remedy

#### Scenario: Bare checkout stays silent and unresolved

- **GIVEN** a checkout with no pointer file, in an environment declaring no
  `workspaces_root`
- **WHEN** discovery runs from the checkout
- **THEN** the chain is empty with no warning, exactly as before

## MODIFIED Requirements

### Requirement: Workspace root discovery
id: workspace-root-discovery
base: 8fa0cbe8e336

The engine SHALL locate the workspace chain by upward search: starting from a
given directory and walking parent-by-parent to the filesystem root, every
directory whose own `.shipd-config.json` declares a `workspace` key SHALL be a
member of the chain, ordered nearest first, the starting directory itself
included. The workspace root SHALL be the chain's first member, so the nearest
declaring ancestor still wins for every root-scoped consumer. If no ancestor
declares one, the engine SHALL attempt the reverse-lookup fallback rungs
(workspace-reverse-lookup); where those also resolve nothing, the chain SHALL
be empty and the search SHALL report that no workspace exists rather than
erroring. A chain resolved through a fallback rung SHALL be the full upward
chain computed from the resolved root, so enclosing workspaces above it are
still members. The search SHALL NOT require the starting directory or any
chain member to be a git repository, and SHALL NOT consult any `.shipd/`
marker; only the fallback rungs MAY probe git, locally.

#### Scenario: Nearest declaring ancestor is the root
- **GIVEN** `.shipd-config.json` files declaring `workspace` at `/ws/` and
  `/ws/nested/`
- **WHEN** discovery starts from `/ws/nested/repo`
- **THEN** the workspace root resolved is `/ws/nested`

#### Scenario: Chain carries every enclosing workspace
- **GIVEN** the same two declaring directories
- **WHEN** the chain is resolved from `/ws/nested/repo`
- **THEN** it is `/ws/nested` then `/ws`, in that order

#### Scenario: Config without a workspace key is not a member
- **GIVEN** `/repo/.shipd-config.json` declaring only `dir` and no ancestor
  declaring `workspace`, with no fallback rung resolving
- **WHEN** discovery starts from `/repo`
- **THEN** the chain is empty, the search returns no workspace root, and it
  raises no error

#### Scenario: Fallback-resolved chain carries enclosing workspaces

- **GIVEN** a checkout whose origin URL uniquely matches a workspace that
  itself sits under an enclosing declaring directory
- **WHEN** the chain is resolved from the checkout
- **THEN** it lists the matched workspace first, then its enclosing
  workspace
