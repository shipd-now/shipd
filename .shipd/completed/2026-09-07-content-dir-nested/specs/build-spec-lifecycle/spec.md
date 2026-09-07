## ADDED Requirements

### Requirement: Worktree guard content-dir resolution
id: worktree-guard-content-dir

When `remove <change>` evaluates its unshipped-change and task-claim guards,
the worktree helper SHALL resolve the worktree's content directory from its
layered configuration through the engine (`spec_status.py --root <worktree>
config-show`, reading the `content-dir:` line) and SHALL scan
`<worktree>/<content-dir>/planned/`. If that resolution fails or prints no
content directory, then the helper SHALL fall back to the literal `.shipd`, so
the guard never scans less than it does under the default configuration and
the helper keeps working in repositories with nothing but git. Refusal reasons
SHALL name the resolved directory.

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
