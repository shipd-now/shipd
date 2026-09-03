# worktree-hooks

### Requirement: Engine worktree create path
id: engine-worktree-create

The engine SHALL provide a stdlib-only `worktree.py` script whose first
argument dispatches: `remove`, `prune-branches`, and `hooks` select those
verbs, and any other first argument is a change name for the create path with
an optional `--fresh` flag. The `remove` and `prune-branches` verbs SHALL
re-execute `worktree.sh` with the arguments passed through verbatim,
preserving its output and exit code. When the create path runs, the engine
SHALL invoke `worktree.sh`'s create path for the git mechanics from the repo
root with output inherited, and, when `worktree.sh` succeeds and
`.worktrees/<name>` did not exist before the invocation, SHALL execute the
resolved `post-worktree-scripts`; while the worktree already existed
(a reuse), the engine SHALL skip the scripts.

#### Scenario: Fresh create runs the configured scripts
- **GIVEN** a repo config declaring two `post-worktree-scripts`
- **WHEN** `worktree.py my-change` runs and `.worktrees/my-change` does not
  yet exist
- **THEN** the worktree is created and both scripts run in declaration order
  with the new worktree as working directory

#### Scenario: Reused worktree skips the scripts
- **GIVEN** an existing `.worktrees/my-change` on branch `change/my-change`
- **WHEN** `worktree.py my-change` runs
- **THEN** the reuse notice is printed and no post-worktree script runs

#### Scenario: Remove passes through to the guarded helper
- **WHEN** `worktree.py remove my-change` runs against a dirty worktree
- **THEN** `worktree.sh`'s refusal report is printed and the exit code is `2`,
  exactly as invoking `worktree.sh remove my-change` directly

### Requirement: Post-worktree script execution
id: post-worktree-execution

The engine SHALL validate the resolved `post-worktree-scripts` value before
any git mutation, so an invalid declaration fails the create path with no
worktree created. Each item SHALL run as a shell command line with the new
worktree as working directory and the parent environment extended with
`SHIPD_WORKTREE` (the absolute worktree path), `SHIPD_ROOT` (the repo root),
and `SHIPD_CHANGE` (the change name), and the engine SHALL print an announce
line naming each item before running it. If an item exits non-zero, then the
engine SHALL stop the chain, report the failing item and its exit code, and
exit `3`, leaving the created worktree in place.

#### Scenario: Invalid config fails before creation
- **GIVEN** a repo config declaring `post-worktree-scripts: 42`
- **WHEN** `worktree.py my-change` runs
- **THEN** the command fails naming `post-worktree-scripts` and
  `.worktrees/my-change` is not created

#### Scenario: Failing script stops the chain
- **GIVEN** three configured scripts of which the second exits `1`
- **WHEN** the create path runs the scripts
- **THEN** the third script does not run, the failure names the second item,
  the exit code is `3`, and the worktree remains on disk

#### Scenario: Scripts see the shipd environment
- **GIVEN** a configured script that prints `$SHIPD_CHANGE` from
  `$SHIPD_WORKTREE`
- **WHEN** the create path runs it for change `my-change`
- **THEN** it observes `SHIPD_CHANGE=my-change` and a `SHIPD_WORKTREE` ending
  in `.worktrees/my-change`

### Requirement: Hooks management verbs
id: worktree-hooks-verbs

The engine's `worktree.py hooks` family SHALL manage the
`post-worktree-scripts` declaration without hand-editing: `hooks list`
SHALL print the effective resolved list with each item's index and the
declaring config file's path, emitting JSON under `--json`; `hooks add <item>`
SHALL append the item to the root's `.shipd-config.json` list, creating the
file or key as needed, preserving unrelated keys, and refusing an exact
duplicate; `hooks remove <item-or-index>` SHALL delete the matching entry from
the root file's list; and `hooks run` SHALL execute the effective list with
the invocation root as working directory using the same execution semantics
as the create path.

#### Scenario: Add creates the key and list reports it
- **GIVEN** a repo whose `.shipd-config.json` lacks `post-worktree-scripts`
- **WHEN** `worktree.py hooks add "cp .env.example .env"` then
  `worktree.py hooks list` run
- **THEN** the config file carries the one-item list, other keys are
  unchanged, and the listing shows the item at index `0` with that file's
  path

#### Scenario: Exact duplicate is refused
- **GIVEN** a registered item `cp .env.example .env`
- **WHEN** `worktree.py hooks add "cp .env.example .env"` runs again
- **THEN** the command exits non-zero naming the duplicate and the list is
  unchanged

#### Scenario: Remove by index deletes one entry
- **GIVEN** a two-item registered list
- **WHEN** `worktree.py hooks remove 0` runs
- **THEN** only the second item remains in the config file

#### Scenario: Hooks run executes in place
- **GIVEN** a configured script list and a current directory inside an
  existing worktree
- **WHEN** `worktree.py hooks run` runs
- **THEN** the items execute in order against that directory, stopping on the
  first failure with exit `3`
