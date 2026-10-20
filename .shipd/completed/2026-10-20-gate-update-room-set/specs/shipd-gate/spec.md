## MODIFIED Requirements

### Requirement: Gate update flow
id: gate-update-flow
base: c814818dc501

When invoked with the argument `update`, the `/s:gate` skill SHALL run a
refresh-only flow in the current repository: announce the running plugin
version, run the same three preflight checks as setup (a git repository,
`gh` authenticated, a GitHub remote — stopping with the hand-off on any
failure), and read the per-file states of the four gate files and the room
wake set from the bare `shipd copilot` report. Where all four gate files are
`installed` at the running version and the room wake set is either all
`installed` or not shipd-installed (its wake workflow `absent` or `foreign`),
the skill SHALL report the repository as already current and stop without
writing, committing, or pushing. Otherwise it SHALL refresh with
`shipd copilot update` — refusing when the verb reports a foreign gate file,
never passing `--force` on its own judgment — commit exactly the paths the
verb reported writing, so a refreshed room wake set rides the same commit as
the gate files, and push the current branch without a further consent round,
the invocation itself being the consent for this scoped refresh. The skill
SHALL never install the room wake set where the repository does not already
carry it. Where the push is rejected, the skill SHALL fall back to a
`shipd-gate-update` branch shipped as a pull request, attempt to arm
auto-merge on it, and report the full pull-request URL, stating that the
pull request awaits a human merge where arming is rejected. The update flow
SHALL touch no repository setting — no branch-protection write, no
auto-merge PATCH, no Actions variable, no secret hand-off — and SHALL close
by relaying the verb's post-refresh per-file state lines.

#### Scenario: An already-current repository is untouched
- **WHEN** `/s:gate update` runs and the bare report shows all four gate
  files `installed` at the running plugin version and the room wake set
  all `installed` or not shipd-installed
- **THEN** the skill reports the repository as current and performs no
  write, no commit, and no push

#### Scenario: Stale files are refreshed and shipped
- **WHEN** any gate file is `stale` or `absent`, or an installed room wake
  set reports a `stale` file
- **THEN** the skill runs `shipd copilot update`, commits the paths the verb
  wrote, pushes, and closes with the post-refresh state lines

#### Scenario: An installed room wake set ships with the gate files
- **WHEN** the repository carries a shipd-owned room wake set and the
  update flow refreshes
- **THEN** the refreshed wake files are in the same commit, and the same
  fallback pull request, as the gate files

#### Scenario: A rejected push becomes an auto-merging pull request
- **WHEN** the push is rejected
- **THEN** the refresh ships from a `shipd-gate-update` branch as a pull
  request with auto-merge attempted, and the report carries the full
  pull-request URL

#### Scenario: A foreign file still refuses
- **WHEN** the verb reports a gate file as foreign
- **THEN** the update flow stops without `--force`, naming the file

#### Scenario: No repository setting is touched
- **WHEN** the update flow completes on any path
- **THEN** no branch-protection write, no auto-merge PATCH, no variable
  set, and no secret storage has been performed
