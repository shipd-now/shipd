## MODIFIED Requirements

### Requirement: List in-flight changes
id: cli-list
base: 590a611a6134

When invoked as `shipd list [kind]`, the binary SHALL enumerate spec-library
artifacts of the given kind — `changes` (the default when the kind word is
omitted), `epics`, `verified`, `research`, or `video` — obtaining the rows
from the engine's shared discovery seam (`spec_status.list_rows`), never from
a private re-walk of the tree, and printing one line per row with the name,
its location, and its status.

For `changes`, the binary SHALL probe the invocation root's
`<content-dir>/planned/` and, for each `.worktrees/<name>` directory that has
a `<content-dir>/planned/`, that worktree's planned changes, printing each
change's lifecycle status as read by the engine's status reader, deduping by
change name with the worktree occurrence winning. The binary SHALL exclude
completed changes unless `--all` is given, in which case entries from
`<content-dir>/completed/` are appended with status `archived`. If no
in-flight change exists, the binary SHALL print `no changes in flight` and
exit `0`.

For `epics`, the rows SHALL be the epics the engine's epic-discovery seam
yields — the invocation root's epics first, then epics hosted only under a
worktree, a contested slug appearing once with the invocation root winning —
each with the status read from its hosting root. For `verified`, `research`,
and `video`, the rows SHALL be the slug directories of that kind under each
candidate root, deduped root-first, with no status value (rendered `-` in
text). If `--all` is combined with a kind other than `changes`, then the
binary SHALL exit non-zero with an error saying `--all` applies to changes
only.

Locations SHALL render `root` or `worktree:<name>`. At a workspace-level
invocation the listing SHALL additionally span each declared project universe
in slug order, a foreign universe's location prefixed with its project slug
(`<project>:<location>`). When `--root DIR` is passed explicitly, the listing
SHALL scope to that root's own universe (the root and its worktrees) and skip
workspace spanning. Invoked without an explicit `--root` from inside a member
repo, the listing resolves the single own universe, leaving the historical
output unchanged.

#### Scenario: Worktree change is listed with its status
- **WHEN** `shipd list --root <repo>` runs and `<repo>/.worktrees/foo` holds a
  planned change `foo` with `Status: ready`
- **THEN** the output contains one line naming `foo`, `worktree:foo`, and
  `ready`

#### Scenario: Duplicate change deduped, worktree wins
- **WHEN** a change `foo` exists under both the root's `planned/` and
  `.worktrees/foo`'s `planned/` and `shipd list --root <repo>` runs
- **THEN** exactly one `foo` line is printed and its location is
  `worktree:foo`

#### Scenario: Completed changes only under --all
- **WHEN** `<content-dir>/completed/` holds an archived change and
  `shipd list --root <repo>` runs without and then with `--all`
- **THEN** the archived entry appears only in the `--all` output, with status
  `archived`

#### Scenario: Empty tree
- **WHEN** `shipd list --root <repo>` runs against a repo with no planned
  changes and no worktrees
- **THEN** the binary prints `no changes in flight` and exits `0`

#### Scenario: Worktree-hosted epic is listed
- **WHEN** `shipd list epics --root <repo>` runs and only
  `<repo>/.worktrees/wt` hosts `epics/foo/epic.md` with `Status: active`
- **THEN** the output contains one line naming `foo`, `worktree:wt`, and
  `active`

#### Scenario: Contested epic slug is listed once, root winning
- **WHEN** an epic slug exists under both the root and a worktree and
  `shipd list epics --root <repo>` runs
- **THEN** exactly one line prints for it with location `root`

#### Scenario: Verified capabilities list without status
- **WHEN** `shipd list verified --root <repo>` runs on a repo with installed
  masters
- **THEN** one line prints per capability slug with location `root` and
  status `-`

#### Scenario: --all refuses a non-changes kind
- **WHEN** `shipd list epics --all` runs
- **THEN** the binary exits non-zero with an error saying `--all` applies to
  changes only

### Requirement: List JSON output
id: list-json
base: adde189ca7b8

The `shipd list` verb SHALL accept a `--json` flag that emits the listing as
a JSON array on stdout — one object per row with `name`, `location`,
`status` (`null` for a kind without status values), and `project` (the owning
declared project's slug, `null` in the invocation root's own universe), in
the same order and with the same rows as the text mode, including the
archived rows under `--all` — and nothing else. An empty listing SHALL emit
an empty JSON array. Without the flag the text output SHALL stay
byte-identical for the `changes` kind in a non-workspace repo, and delegated
verbs SHALL keep passing `--json` through to their engine scripts verbatim.

#### Scenario: List rows are machine-readable
- **WHEN** `shipd list --json` runs in a repo with an in-flight change in a
  worktree
- **THEN** stdout parses as a JSON array whose entry carries the change
  name, its `worktree:<name>` location, its status, and `project` `null`

#### Scenario: Epic rows are machine-readable
- **WHEN** `shipd list epics --json` runs in a repo hosting one epic at the
  root
- **THEN** stdout parses as a JSON array whose entry carries the epic slug,
  location `root`, its status value, and `project` `null`

#### Scenario: Empty listing is an empty array
- **WHEN** `shipd list --json` runs with no changes in flight
- **THEN** stdout is an empty JSON array, not the text placeholder

#### Scenario: Delegated verbs pass the flag through
- **WHEN** `shipd epic <slug> --json` runs
- **THEN** the output is exactly `spec_status.py epic-show <slug> --json`'s
  output
