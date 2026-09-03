## MODIFIED Requirements

### Requirement: One change per worktree and branch
id: change-worktree-isolation
base: 2fe91408bb9e

Every change SHALL be developed in its own git worktree at
`.worktrees/<change>` on a branch named `change/<change>`, created via the
engine's worktree create path — the `shipd worktree <change>` verb
delegating to `worktree.py` among the plugin's engine scripts, which drives
the git mechanics through `worktree.sh` and then runs any configured
`post-worktree-scripts` — and the entire lifecycle — planning artifacts,
implementation, verification, and the spec merge/archive — SHALL run inside
that worktree so the change's artifacts, code, and applied specs travel in a
single PR. The main checkout SHALL be used only for launching sessions,
reviewing, post-merge pulls, and the plugin snapshot refresh.

#### Scenario: Lifecycle stays in the worktree
- **WHEN** a change `dark-mode-toggle` is planned and built
- **THEN** its artifacts, implementation, verification, and merge/
  archive happen under `.worktrees/dark-mode-toggle` on branch
  `change/dark-mode-toggle`, and the main checkout's working tree is
  untouched

#### Scenario: Parallel sessions do not collide
- **WHEN** two sessions develop two different changes concurrently
- **THEN** each works in its own worktree and branch, and neither
  session's uncommitted state appears in the other's commits

#### Scenario: Creation goes through the engine verb
- **WHEN** a build flow creates the worktree for a change in a repo with
  configured `post-worktree-scripts`
- **THEN** it invokes the engine's worktree create path rather than raw
  `git worktree add`, so the configured setup scripts run before any task
  executes in the worktree
