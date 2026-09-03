## ADDED Requirements

### Requirement: Post-worktree scripts config key
id: post-worktree-scripts-key

The resolved configuration MAY carry a `post-worktree-scripts` key holding an
ordered JSON list of non-empty strings, each a shell command line the engine's
worktree create path executes in list order after a worktree is created. The
key SHALL merge nearest-wins-wholesale like every other top-level key. If a
layer declares the key with a value that is not a list of non-empty strings,
then resolution of the key SHALL fail with an error naming
`post-worktree-scripts` and the offending value.

#### Scenario: Declared list resolves in order
- **GIVEN** a repo config declaring `post-worktree-scripts:
  ["cp .env.example .env", ".shipd/hooks/seed-db.sh"]`
- **WHEN** the key is resolved from that repo
- **THEN** the effective value is that two-item list in declaration order

#### Scenario: Non-list value is rejected
- **WHEN** a layer declares `post-worktree-scripts: "cp .env.example .env"`
- **THEN** resolving the key fails with an error naming
  `post-worktree-scripts`

#### Scenario: Empty-string item is rejected
- **WHEN** a layer declares `post-worktree-scripts: ["cp a b", ""]`
- **THEN** resolving the key fails with an error naming
  `post-worktree-scripts`

#### Scenario: Nearest layer wins the list wholesale
- **GIVEN** a workspace layer declaring a one-item list and a repo layer
  declaring a different two-item list
- **WHEN** the key is resolved from the repo
- **THEN** the effective value is the repo layer's two-item list, with no
  merging of the workspace layer's item
