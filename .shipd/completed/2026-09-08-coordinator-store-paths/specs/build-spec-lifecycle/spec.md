## MODIFIED Requirements

### Requirement: Worktree guard content-dir resolution
id: worktree-guard-content-dir
base: 15acc21e759e

When `remove <change>` evaluates its unshipped-change and task-claim guards,
the worktree helper SHALL resolve the worktree's content directory from its
layered configuration through the engine (`spec_status.py --root <worktree>
config-show`, reading the `content-dir:` line) and SHALL scan
`<worktree>/<content-dir>/planned/`. If that resolution fails or prints no
content directory, then the helper SHALL fall back to the literal `.shipd`, so
the guard never scans less than it does under the default configuration and
the helper keeps working in repositories with nothing but git. Refusal reasons
SHALL name the resolved directory.

Where the same `config-show` output additionally prints a `store:` line (a
declared `store_root` resolving the content directory into an external
store), the two guards SHALL also check the store's `planned/<change>`
directory for the change under removal — and only that change, never the
store's other planned changes, since the store is shared by every worktree
of the repository: an existing `planned/<change>` directory SHALL refuse as
an unshipped change, a `- [~]` mark in its `tasks.md` SHALL refuse as an
in-progress claim, and a `.tasks.lock` beside it SHALL refuse as live
coordination, each reason naming the store path. The in-worktree scan SHALL
be unchanged, and the base-content carve-out SHALL NOT apply to the store
check — a change present in the store's `planned/` is in-flight by
definition.

#### Scenario: Nested configured dir guards removal
- **GIVEN** a worktree whose config declares `dir: ".agents/specs/.shipd"`
  carrying an unshipped change under `.agents/specs/.shipd/planned/`
- **WHEN** `remove <change>` runs without `--force`
- **THEN** nothing is removed, the refusal lists the unshipped-change reason
  naming that directory, and the exit code is 2

#### Scenario: Resolution failure falls back to .shipd
- **GIVEN** a worktree whose `.shipd-config.json` is malformed JSON and which
  carries an unshipped change under `.shipd/planned/`
- **WHEN** `remove <change>` runs without `--force`
- **THEN** the refusal lists the unshipped-change reason and the exit code is 2

#### Scenario: A store-resident unshipped change refuses removal
- **GIVEN** a worktree for change `x` whose configuration resolves a store
  holding `planned/x/`
- **WHEN** `remove x` runs without `--force`
- **THEN** nothing is removed, the refusal names the store's `planned/x`
  path, and the exit code is 2

#### Scenario: Live store coordination refuses removal
- **GIVEN** the store's `planned/x/tasks.md` carrying a `- [~]` claim or a
  `.tasks.lock` beside it
- **WHEN** `remove x` runs without `--force`
- **THEN** the refusal lists the claim or lock reason naming the store path
  and the exit code is 2

#### Scenario: Another change in the store never blocks
- **GIVEN** a clean worktree for change `x` and a store whose `planned/`
  holds only an unrelated change `y`
- **WHEN** `remove x` runs
- **THEN** the worktree is removed and the exit code is zero
