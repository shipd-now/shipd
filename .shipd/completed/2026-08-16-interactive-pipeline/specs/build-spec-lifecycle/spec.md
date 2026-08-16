## ADDED Requirements

### Requirement: Interactive pipeline resolution
id: interactive-pipeline-resolution

When the interactive `/s:build` flow starts, it SHALL resolve the
effective autonomous pipeline exactly once by running the status CLI's
`pipeline-show` verb and SHALL read each entry's declared options from
the rendered labels, never re-deriving them from configuration files. If
the resolution exits non-zero (a validation error or missing pydantic),
then the flow SHALL report the engine's error text and stop before any
spec work — a declared pipeline never half-runs. Where the resolved
`build` entry declares `subagent_model`, build SHALL spawn `s:sub-agent`
and `s:validator` workers with the Agent tool's model parameter set to
the tier resolved relative to the session's own model — `session` omits
the parameter; `tier-below`/`tier-two-below` step one/two below the
session's model on the ladder `fable`, `opus`, `sonnet`, `haiku`,
clamped at the bottom; any other value passes verbatim as a concrete id.
Where the resolved `build` entry declares `parallelism`, that value SHALL
cap concurrent execution sub-agents, taking precedence over the
`parallelism` configuration key and the default of three. Where the
resolved `build` entry declares `telemetry` false, build SHALL NOT
persist the per-tool token breakdown into the change's `tasks.md`. The
interactive flow SHALL ignore `autopilot` blocks, `replace` bindings,
custom steps, the build entry's own `model` option, and a `skip` on the
stage the user explicitly invoked — an explicit invocation always runs.
When a driving invoker's prompt conveys stage-option instructions, those
SHALL supersede self-resolution.

#### Scenario: Eco build options are honored interactively
- **GIVEN** a repo whose resolved pipeline is the `eco` preset
- **WHEN** a user runs `/s:build` on a planned change
- **THEN** execution sub-agents spawn on the tier two below the session,
  no validator is spawned, and no per-tool token breakdown is persisted

#### Scenario: Malformed pipeline stops the build before spec work
- **GIVEN** a declared pipeline entry carrying an unknown key
- **WHEN** `/s:build` resolves the pipeline at flow start
- **THEN** the flow reports the resolution error naming the entry and
  field and stops without authoring artifacts or spawning sub-agents

#### Scenario: Autopilot blocks are ignored interactively
- **GIVEN** a resolved build entry carrying `autopilot.attempts` 1
- **WHEN** an interactive build stage fails
- **THEN** no retry budget is enforced from it — the flow stops and asks
  the user exactly as before

#### Scenario: Conveyed options supersede self-resolution
- **GIVEN** a driving session's prompt conveying a concrete sub-agent
  model resolved against a detached anchor
- **WHEN** the interactive flow's self-resolved tier would differ
- **THEN** the conveyed concrete value is used for the spawns

## MODIFIED Requirements

### Requirement: Adversarial validation gates verified
id: adversarial-validation-gates-verified
base: 4e506292c029

When the task list is complete and the test suite passes, build SHALL spawn an
independent validator sub-agent — on the same tier as the execution
sub-agents, using the `s:validator` agent type whose definition carries the
validator's full role contract — that reads the change's delta specs, the
relevant masters, the code, and, when `plan.md` names a design scratch directory,
that directory as a read-only reference, and attempts to refute each
`#### Scenario:` by exercising the real behavior. The validator's spawn message
SHALL carry only the change name; it SHALL receive neither the builders'
summaries nor the orchestrator's conversation. The build SHALL NOT set the status
to `verified` while any scenario verdict is `refuted`; a refutation returns the
build to the fix loop before validation runs again. Where the resolved
pipeline's `build` entry declares `validator` false, build SHALL NOT spawn
the validator sub-agent, and passing mechanical verification (all tasks
complete, the suite green, the spec re-linting clean) alone SHALL allow
`set-status verified`.

#### Scenario: Validator runs before verified
- **WHEN** all tasks are done and the suite is green
- **THEN** an `s:validator` sub-agent reports a per-scenario verdict, and
  only a fully confirmed report allows `set-status verified`

#### Scenario: Refutation blocks the merge
- **WHEN** the validator refutes a scenario with evidence
- **THEN** the orchestrator routes the finding through the fix loop and
  re-validates; the change is not merged in the meantime

#### Scenario: Validator is isolated from the builders
- **WHEN** the validator sub-agent is spawned
- **THEN** its spawn message carries the change name only — no builder
  summaries and no orchestrator history — and its role contract comes from
  the `s:validator` definition

#### Scenario: Validator exercises design fidelity against the design
- **WHEN** a change carries a design and its delta specs include design-fidelity
  scenarios
- **THEN** the validator reads the plan-named design scratch directory and
  refutes or confirms those scenarios against the real design

#### Scenario: Pipeline validator opt-out skips the gate
- **GIVEN** a resolved build entry declaring `validator` false
- **WHEN** all tasks are done, the suite is green, and the spec re-lints
  clean
- **THEN** no `s:validator` sub-agent is spawned and the status advances
  to `verified` on mechanical verification alone

### Requirement: Ship changes as auto-merging PRs
id: ship-changes-as-prs
base: 692f6d8bad80

When a change is verified and merged/archived on its branch, build SHALL ship
it by pushing the branch (`git push -u origin change/<name>`), opening a PR
(`gh pr create --fill`), and enabling auto-merge with squash and branch
deletion (`gh pr merge --auto --squash --delete-branch`). Build SHALL NOT
commit or push to `main` directly; a `ci` status check on the PR SHALL gate
the merge. When reporting the PR in any status update or completion report,
build SHALL give the full clickable PR URL, never just the number. If
auto-merge is unavailable, build SHALL merge manually only after `ci` is
green and SHALL say so in the report.

Arming auto-merge is not proof of merge. Immediately after arming it, build
SHALL read the PR's `mergeStateStatus` once. `CLEAN` or `UNSTABLE`, and a
`BLOCKED` state on a branch that is neither `BEHIND` nor `DIRTY` (merely
awaiting required checks — in this repo, the `semantic-review` gate not yet
posted or `ci` still running), are on track: build SHALL post the gate and let
the checks run, NOT merge `origin/main`. When posting the gate, build SHALL
pass the resolved pipeline's review entry's declared `disposition` and
`model` through to the `/s:review` post flow and follow that flow's
matching scoped disposition loop; an entry declaring neither leaves the
posting unchanged. Where the resolved pipeline explicitly skips or omits
the `review` stage, build SHALL NOT post the gate, and the PR watch SHALL
surface a PR still blocked on a required check as a blocker. Only a `DIRTY`
or `BEHIND` state (or a
`BLOCKED` caused by a behind/conflicting branch) means the PR cannot merge as
armed; there build SHALL reconcile the branch by merging `origin/main` into it
in the worktree and re-pushing — re-posting the `semantic-review` gate on the
new head, since a new commit invalidates the prior status — or, when the
conflict is non-trivial, surface it as a blocker rather than leaving auto-merge
waiting on a merge that cannot happen. While a build is unattended (an
autopilot-driven member), a non-trivial conflict SHALL park the member rather
than prompt a human.

Build SHALL then watch **its own** PR to a terminal state, polling `state` and
`mergeStateStatus` together on each cycle: a transition to `DIRTY`, `BEHIND`, or
`BLOCKED` SHALL be acted on within a poll cycle (reconcile or surface) exactly as
`MERGED` ends the watch. The close-out SHALL wait for this PR to reach `MERGED`
before pruning the worktree, pulling `main`, and running any epic derivation, so
a subsequent build lands on a `main` that already carries this change. Build
SHALL NOT block one change's close-out on any other PR's state.

Build SHALL NOT open a follow-up PR on a branch whose PR has already
squash-merged. A review finding that arrives after merge SHALL either have
blocked the original PR before merge or be planned as a new change against
current `main`.

#### Scenario: Verified change becomes a PR
- **WHEN** verification passes and the spec merge/archive is committed on
  `change/dark-mode-toggle`
- **THEN** the branch is pushed, a PR is opened with auto-merge (squash)
  enabled, and the completion report links the PR's full URL

#### Scenario: No direct main pushes
- **WHEN** a build finishes while `ci` has not yet passed on its PR
- **THEN** nothing is pushed to `main`; the merge happens only through the
  PR once the check is green

#### Scenario: Un-mergeable PR is reconciled, not awaited
- **GIVEN** auto-merge has just been armed and the PR's `mergeStateStatus`
  reads `DIRTY`
- **WHEN** build checks mergeability after arming
- **THEN** it merges `origin/main` into the branch and re-pushes (re-posting the
  gate on the new head), or surfaces a non-trivial conflict as a blocker —
  never leaving auto-merge to wait indefinitely

#### Scenario: A stuck watched PR is acted on, not awaited forever
- **GIVEN** build is watching its own PR and the PR transitions to `BLOCKED`
- **WHEN** the next poll cycle observes the transition
- **THEN** build reconciles or surfaces it within that cycle rather than waiting
  on a merge that cannot complete

#### Scenario: One stuck PR does not delay another close-out
- **GIVEN** two shipped changes whose PRs are watched independently, one of which
  is stuck `DIRTY`
- **WHEN** the other PR reaches `MERGED`
- **THEN** its close-out runs without waiting on the stuck PR

#### Scenario: No follow-up PR on a squash-merged branch
- **WHEN** a review finding is raised after the change's PR has squash-merged
- **THEN** it is planned as a new change against current `main`, not opened as a
  second PR on the merged branch

#### Scenario: Review entry options reach the gate posting
- **GIVEN** a resolved review entry declaring `disposition` `high-only`
  and `model` `tier-below`
- **WHEN** build posts the semantic-review gate for its PR
- **THEN** the `/s:review` post flow is invoked with
  `disposition=high-only` and `model=tier-below` and its `high-only`
  disposition loop runs

#### Scenario: Skipped review posts no gate
- **GIVEN** a declared pipeline carrying `{"stage": "review", "skip":
  true}`
- **WHEN** build ships the change's PR
- **THEN** no semantic-review gate is posted, and a PR blocked on a
  still-required check is surfaced by the watch as a blocker
