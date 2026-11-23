## ADDED Requirements

### Requirement: The launcher describes its own verbs correctly
id: cli-self-description

The module docstring of `plugins/s/bin/shipd` SHALL NOT list
`worktree remove` among the verbs kept out of the launcher. It SHALL state
that `worktree` passes through to the guarded `worktree.py`, so
`worktree remove` runs through the launcher under that script's guards. The
docstring and the `harness` entry of the `shipd --help` banner SHALL call
the files `harness add` writes generated command files, with no `/s:` label.

#### Scenario: The docstring agrees with the banner on worktree remove
- **WHEN** the module docstring of `plugins/s/bin/shipd` is read
- **THEN** its list of verbs that stay behind guarded scripts holds no
  `worktree remove`, and it says `worktree remove` runs through the launcher

#### Scenario: The banner names generated command files
- **WHEN** `shipd --help` runs
- **THEN** the `harness` entry reads `the harness registry, and the
  generated command files in a repo or in your home`, and no line of the
  banner holds `generated /s:`
