## ADDED Requirements

### Requirement: Workspace map verbs
id: workspace-map-verbs

The status CLI SHALL provide a `workspace-map` verb resolving the workspace
from the invocation directory (failing with the standard no-workspace error
otherwise). The bare form SHALL list each map entry with its stored value
and resolved absolute destination, plus the unknown-key note. The `set`
form SHALL take a member path and a local path, SHALL error naming the
declared member paths when the member path matches no manifest entry, SHALL
store the local path verbatim, SHALL preserve every other top-level key of
the map file byte-for-byte (a `workspace_root` key included), and SHALL
ensure the workspace root's `.gitignore` carries a
`.shipd-workspace.local.json` line outside the marked member block —
idempotently, creating the file when absent. If the target path does not
exist or is not a git work tree, then `set` SHALL warn and still write. The
`remove` form SHALL delete the member's entry, erroring when no entry
exists. A malformed existing map file SHALL fail `set` and `remove` with
the load's own error, never repaired.

#### Scenario: Set writes a validated entry and ignores the file

- **GIVEN** a workspace declaring member path `shipd` and no map file
- **WHEN** `workspace-map set shipd ~/projects/shipd` runs from the root
- **THEN** the map file's `repos` maps `shipd` to `~/projects/shipd`
  verbatim and the root `.gitignore` contains a
  `.shipd-workspace.local.json` line outside the marked member block

#### Scenario: Set refuses an undeclared member path

- **GIVEN** a workspace declaring only member path `shipd`
- **WHEN** `workspace-map set web ../web` runs
- **THEN** the verb exits non-zero naming the declared member paths and
  writes nothing

#### Scenario: Set preserves foreign keys

- **GIVEN** a map file carrying a `workspace_root` key beside `repos`
- **WHEN** `set` adds an entry
- **THEN** the `workspace_root` key survives unchanged

#### Scenario: Missing target warns but writes

- **WHEN** `set` maps a member to a path that does not exist
- **THEN** the entry is written and a warning names the missing target

#### Scenario: Remove deletes exactly one entry

- **GIVEN** a map holding entries for `shipd` and `web`
- **WHEN** `workspace-map remove shipd` runs
- **THEN** only the `web` entry remains, and a second identical remove
  exits non-zero

## MODIFIED Requirements

### Requirement: Workspace setup skill
id: workspace-setup-skill
base: 45c7fe71afcb

An `/s:workspace` skill SHALL provide, selected by argument: `init` — guided
workspace creation that, when a workspace root is already discoverable,
reports that root and stops; otherwise asks the user in a single question
round to choose the target root (the repository's parent directory offered
as the recommended default, the repository root as the alternative) and
whether to seed the root as a portable git workspace (plain init the
recommended default), then drives the status CLI's `workspace-init` verb —
with `--git` when seeding was chosen — reporting the created root; `show` —
the workspace roster via the status CLI's `workspace-show` verb, reading
only; `clone <url> [dest]` — bootstrap a job workspace from its repository
URL; `sync` — materialize the workspace's members by executing the
engine's plan; and `map` — a guided mapping round that reads the sync
plan, proposes for each unmapped member an existing local checkout
candidate (the plan's matching clone-source when one exists) or a
user-supplied path, asks in a single round, drives the status CLI's
`workspace-map set` verb per accepted member, and finishes by reporting
the map listing; already-mapped members SHALL be reported, never re-asked,
and `sync` and `clone` SHALL remain question-free. The skill SHALL NOT
write the workspace declaration, the gitignore member block, or the member
map file by hand — all go through the CLI verbs. Where the resolved
configuration declares `workspaces_root` (shipd-config
workspaces-root-key), the `init` round SHALL name the declared root and offer
target candidates inside it — substituting `<workspaces_root>/<repo-name>`
for a natural candidate that lies outside the root — and SHALL pass a chosen
bare name through to the verb unchanged, the engine resolving it into the
root.

#### Scenario: Init on an existing workspace reports and stops

- **WHEN** the skill's `init` verb runs where a workspace root is
  discoverable
- **THEN** the skill reports that root, creates nothing, and stops

#### Scenario: Init creates through the CLI verb

- **WHEN** the user confirms a target root during `init` where no workspace
  is discoverable
- **THEN** the skill runs `workspace-init` against that root and reports
  the root the verb printed

#### Scenario: Init seeds git when the portable option is chosen

- **WHEN** the user chooses git seeding in the `init` round
- **THEN** the skill runs `workspace-init <path> --git` and reports the
  created root

#### Scenario: Show reports the roster

- **WHEN** the skill's `show` verb runs in a discoverable workspace
- **THEN** the workspace root, projects, and initiatives are reported and
  nothing is changed

#### Scenario: Init round names the declared root

- **GIVEN** a resolved configuration declaring `workspaces_root`
- **WHEN** the skill's `init` round is presented
- **THEN** the declared root is named and every offered target candidate
  lies inside it

#### Scenario: Map verb drives the engine writer

- **GIVEN** a workspace with an unmapped member whose checkout exists
  locally
- **WHEN** `/s:workspace map` runs and the user accepts the candidate
- **THEN** the skill runs `workspace-map set` for that member and reports
  the resulting map listing, having edited no file by hand
