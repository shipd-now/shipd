## MODIFIED Requirements

### Requirement: Step navigation
id: onboard-step-navigation
base: fdd6d557da91

The `/s:onboard` skill SHALL run as a nine-step sequence driven by explicit
navigation arguments: with no argument it SHALL start at step 1 (scaffolding
first) when no state exists, or resume at the persisted current step; `next`
SHALL advance one step; `back` SHALL return to the previous step, clamped at
step 1 and offered on the explainer steps. The skill SHALL persist the
current step and sandbox path in `~/.shipd/onboarding/state.json`, with the
sandbox at the stable path `~/.shipd/onboarding/sandbox/`, so navigation
survives across sessions. Mutating steps SHALL be idempotent on re-entry:
when step 8's build has already merged in the sandbox, re-entering step 8
SHALL re-show the built summary rather than re-running the build. The
`workspaces` argument SHALL route to the workspaces side-track and SHALL
NOT read or write that state file.

#### Scenario: Fresh start scaffolds and records step 1
- **WHEN** `/s:onboard` runs with no argument and no state file exists
- **THEN** the sandbox is scaffolded at the stable path, the state file
  records step 1, and step 1 renders

#### Scenario: Next advances and persists
- **WHEN** `/s:onboard next` runs
- **THEN** the state file's step increments by one and the new step renders

#### Scenario: Back returns without restarting
- **WHEN** `/s:onboard back` runs on an explainer step
- **THEN** the state file's step decrements — never below 1 — and that step
  renders again

#### Scenario: Resume across sessions
- **WHEN** `/s:onboard` runs with no argument in a new session and a state
  file exists
- **THEN** the walkthrough resumes at the recorded step without restarting

#### Scenario: The side-track leaves the tour state alone
- **WHEN** `/s:onboard workspaces` runs while the tour sits at step 5
- **THEN** the tour's state file still records step 5 afterward

## ADDED Requirements

### Requirement: Workspaces side-track
id: onboard-workspaces-side-track

The `/s:onboard` skill SHALL offer an optional side-track, invoked as
`/s:onboard workspaces` with `next` and `back` navigation, that teaches
workspace configuration in five parts: the manifest and the chain;
nearest-wins reads with no registry merge; writes landing in the nearest
store; overlapping team workspaces that declare the same shared repo; and
isolation through separate repositories, with pointers to the `store_root`
and sync guides. The side-track SHALL build a throwaway base workspace with
several nested team workspaces by running the engine's workspace verbs and
SHALL show their real output. It SHALL keep its sandbox at
`~/.shipd/onboarding/workspaces-sandbox/` and its progress in
`~/.shipd/onboarding/workspaces.json`, and SHALL NOT write a file outside
`~/.shipd/onboarding/`. Re-entering it SHALL reuse an existing sandbox
rather than re-initialize it. The tour's step 9 SHALL name the side-track.

#### Scenario: The lesson builds overlapping teams with real verbs
- **WHEN** part 4 of the side-track renders
- **THEN** two nested teams each declare the same shared repo path and the
  real `workspace-show` output for each is shown

#### Scenario: A team without projects inherits the base's registry
- **WHEN** part 2 renders
- **THEN** `workspace-show` inside a team declaring no projects prints the
  base workspace as the registry's source

#### Scenario: Writes land in the nearest store
- **WHEN** part 3 renders
- **THEN** `wiki-init` run inside a team creates that team's own store and
  the base's store stays unchanged

#### Scenario: Re-entry reuses the sandbox
- **WHEN** `/s:onboard workspaces` runs and the sandbox already exists
- **THEN** no workspace-init verb re-runs and the recorded part renders

#### Scenario: The real repository is untouched
- **WHEN** any side-track part runs
- **THEN** every write lands under `~/.shipd/onboarding/`
