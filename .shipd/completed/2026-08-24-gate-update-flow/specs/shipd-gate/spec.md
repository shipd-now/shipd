## ADDED Requirements

### Requirement: Gate update flow
id: gate-update-flow

When invoked with the argument `update`, the `/s:gate` skill SHALL run a
refresh-only flow in the current repository: announce the running plugin
version, run the same three preflight checks as setup (a git repository,
`gh` authenticated, a GitHub remote — stopping with the hand-off on any
failure), and read the per-file managed states from the bare `shipd copilot`
report. Where all four managed files are `installed` at the running version,
the skill SHALL report the repository as already current and stop without
writing, committing, or pushing. Otherwise it SHALL refresh with
`shipd copilot add` — refusing when the verb reports a foreign managed path,
never passing `--force` on its own judgment — commit exactly the four
managed paths, and push the current branch without a further consent round,
the invocation itself being the consent for this scoped refresh. Where the
push is rejected, the skill SHALL fall back to a `shipd-gate-update` branch
shipped as a pull request, attempt to arm auto-merge on it, and report the
full pull-request URL, stating that the pull request awaits a human merge
where arming is rejected. The update flow SHALL touch no repository
setting — no branch-protection write, no auto-merge PATCH, no Actions
variable, no secret hand-off — and SHALL close by relaying the verb's
post-refresh per-file state lines.

#### Scenario: An already-current repository is untouched
- **WHEN** `/s:gate update` runs and the bare report shows all four managed
  files `installed` at the running plugin version
- **THEN** the skill reports the repository as current and performs no
  write, no commit, and no push

#### Scenario: Stale files are refreshed and shipped
- **WHEN** any managed file is `stale` or `absent`
- **THEN** the skill runs `shipd copilot add`, commits the four managed
  paths, pushes, and closes with the post-refresh state lines

#### Scenario: A rejected push becomes an auto-merging pull request
- **WHEN** the push is rejected
- **THEN** the refresh ships from a `shipd-gate-update` branch as a pull
  request with auto-merge attempted, and the report carries the full
  pull-request URL

#### Scenario: A foreign file still refuses
- **WHEN** the verb reports a managed path as foreign
- **THEN** the update flow stops without `--force`, naming the file

#### Scenario: No repository setting is touched
- **WHEN** the update flow completes on any path
- **THEN** no branch-protection write, no auto-merge PATCH, no variable
  set, and no secret storage has been performed
