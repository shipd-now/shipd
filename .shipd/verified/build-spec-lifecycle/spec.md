# build-spec-lifecycle

### Requirement: Lint gates execution
id: lint-gates-execution

`/s:build` SHALL run `spec_lint.py` on the change and require a zero exit
status before spawning any execution sub-agent. Lint errors SHALL be fixed in the
artifacts (not waived) and lint re-run until clean.

#### Scenario: Sub-agents only spawn on clean lint
- **WHEN** `spec_lint.py` exits non-zero for the change
- **THEN** build fixes the artifacts and re-lints; no sub-agent is spawned until
  the exit status is zero

### Requirement: Merge and archive replace OpenSpec archiving
id: merge-and-archive-replace-openspec-archiving

After all tasks are complete and verification passes, build SHALL apply the
change with `spec_merge.py` — merging the delta specs into `am/verified/` and
moving the change directory to `am/completed/` — instead of `openspec archive`.
Build SHALL NOT invoke the OpenSpec CLI at any phase.

#### Scenario: Completed build merges via the engine
- **WHEN** verification passes for a completed change
- **THEN** build runs `spec_merge.py`, the master library reflects the deltas,
  and the change moves to `am/completed/`

#### Scenario: No OpenSpec dependency
- **WHEN** `/s:build` runs end-to-end in a repo without the OpenSpec CLI
  installed
- **THEN** every phase completes using only the plugin's own scripts

### Requirement: Merge warnings propagate to the orchestrator
id: merge-warnings-propagate-to-the-orchestrator

Build SHALL capture the merge engine's machine-readable warning summary and
carry every warning (stale base-hash overwrites, id collisions, missing
targets) through to the end-of-build report. Warnings SHALL never be dropped or
demoted to log output only.

#### Scenario: Stale-base overwrite reaches the report
- **WHEN** the merge applies a modification whose `base:` hash was stale
- **THEN** the warning naming the requirement `id` appears in the final build
  report

### Requirement: Build updates spec status at phase boundaries
id: build-updates-spec-status

The build flow SHALL select the change it is building (`use`) when execution
begins, and SHALL update the change's status via the status CLI at phase
boundaries: `active` when sub-agents are spawned, `complete` when the task
coordinator reports nothing pending or in progress, and `verified` when
verification passes — all before the change is merged and archived.

#### Scenario: Spawning marks the spec active
- **WHEN** build spawns its first execution sub-agent for a change
- **THEN** the change is the current selection and its status is `active`

#### Scenario: Verification marks the spec verified
- **WHEN** Phase 5 verification passes for a completed change
- **THEN** the plan's status line reads `Status: verified` before merge
  and archive

### Requirement: One change per worktree and branch
id: change-worktree-isolation

Every change SHALL be developed in its own git worktree at
`.worktrees/<change>` on a branch named `change/<change>`, created via the
plugin's worktree helper (`worktree.sh` among the plugin's engine
scripts), and the entire lifecycle — planning artifacts, implementation,
verification, and the spec merge/archive — SHALL run inside that worktree
so the change's artifacts, code, and applied specs travel in a single PR.
The main checkout SHALL be used only for launching sessions, reviewing,
post-merge pulls, and the plugin snapshot refresh.

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

### Requirement: Ship changes as auto-merging PRs
id: ship-changes-as-prs

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

### Requirement: Adversarial validation gates verified
id: adversarial-validation-gates-verified

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

### Requirement: Epic derivation in the build close-out
id: epic-close-out-derivation

When a shipped change's plan carried an `Epic:` line, the build flow's
close-out SHALL, after the PR merges and main is pulled, run `epic-sync`
for that epic from a fresh `epic-close-<slug>` worktree — never from the
main checkout — and, only when the derivation changes the epic's status
line, commit and ship the advance as an auto-merging PR; when the status is
unchanged, the worktree is removed with no PR. The close-out SHALL NOT run
the derivation pre-merge, because member archives reach main only after the
squash merge.

#### Scenario: Member merge advances the epic via a PR
- **GIVEN** a shipped change whose plan carried `Epic: reporting-overhaul`
  and whose merge archived the epic's last member
- **WHEN** the build close-out runs
- **THEN** `epic-sync` runs in an `epic-close-reporting-overhaul` worktree
  and the status advance ships as an auto-merging PR

#### Scenario: Unchanged derivation ships nothing
- **WHEN** the close-out's `epic-sync` derives the status the epic already
  carries
- **THEN** no commit or PR is created and the worktree is removed

### Requirement: Plugin-owned worktree helper
id: plugin-worktree-helper

The plugin SHALL ship the worktree helper as an engine script
(`worktree.sh` beside the other engine scripts), invocable by plugin path
in any git repository. Given a change name and run from a repository
root, the helper SHALL ensure a worktree exists at `.worktrees/<change>`
on branch `change/<change>` and print where to continue working, exiting
zero — creating the worktree and branch when neither exists, creating the
worktree from the existing branch when only the branch exists, and
reusing the worktree unchanged when it already exists on that branch. It
SHALL refuse — exiting non-zero and changing nothing — when
`.worktrees/<change>` exists but is checked out on a different branch,
and SHALL error when not run from a repository root. The helper SHALL
also provide `remove <change>`, which SHALL refuse — exit
code 2, listing every applicable reason — while the worktree shows work
in progress: uncommitted or untracked files, any change still under its
`.shipd/planned/`, task-claim marks (`[~]`) or a coordination lock in its
planned checklists, or any file modified within the idle window (default
30 minutes, overridable via `SHIPD_WORKTREE_IDLE_MINUTES`). When no guard
fires, `remove` SHALL remove the worktree and prune, exiting zero; a
`--force` flag SHALL override the guards but SHALL print each guard it
overrode. Workflow documentation SHALL instruct removal through this verb,
never raw `git worktree remove`. Callers SHALL NOT need to test for an
existing worktree before invoking the helper. The helper SHALL make no
assumption about the repository beyond git itself.

#### Scenario: Helper works in a fresh repo
- **GIVEN** a brand-new git repository with one commit and no am layout
- **WHEN** the plugin's `worktree.sh my-change` runs from its root
- **THEN** `.worktrees/my-change` exists on branch `change/my-change` and
  the exit code is zero

#### Scenario: Second invocation reuses the worktree
- **GIVEN** a repository where `worktree.sh my-change` has already run and
  `.worktrees/my-change` is checked out on `change/my-change`
- **WHEN** `worktree.sh my-change` runs again
- **THEN** the exit code is zero, the worktree is still present on that
  branch, and its working tree is unchanged

#### Scenario: Existing branch without a worktree is re-attached
- **GIVEN** a repository where branch `change/my-change` exists but
  `.worktrees/my-change` does not
- **WHEN** `worktree.sh my-change` runs
- **THEN** `.worktrees/my-change` is created on that existing branch and
  the exit code is zero

#### Scenario: A worktree on a different branch is refused
- **GIVEN** a repository where `.worktrees/my-change` exists but is
  checked out on a branch other than `change/my-change`
- **WHEN** `worktree.sh my-change` runs
- **THEN** it exits non-zero and neither the worktree nor any branch is
  changed

#### Scenario: Clean cold worktree removes
- **GIVEN** a worktree with a clean tree, nothing under `.shipd/planned/`,
  no claims, and no file touched inside the idle window
- **WHEN** `remove my-change` runs
- **THEN** the worktree is gone and the exit code is zero

#### Scenario: In-progress work refuses removal
- **GIVEN** a worktree carrying an unshipped change under `.shipd/planned/`
  and a `[~]` claim in its tasks.md
- **WHEN** `remove my-change` runs without `--force`
- **THEN** nothing is removed, both reasons are listed, and the exit code
  is 2

#### Scenario: Fresh activity refuses removal
- **GIVEN** an otherwise clean worktree with a file modified two minutes
  ago
- **WHEN** `remove my-change` runs
- **THEN** the refusal names the recent-activity guard and nothing is
  removed

#### Scenario: Force overrides audibly
- **WHEN** `remove my-change --force` runs against a worktree with a
  dirty tree
- **THEN** the worktree is removed and the output names the dirty-tree
  guard as overridden

#### Scenario: Re-entry after removal succeeds
- **GIVEN** a change whose worktree was removed by `remove my-change`
  while its branch `change/my-change` remains
- **WHEN** `worktree.sh my-change` runs again
- **THEN** the worktree is recreated on that branch and the exit code is
  zero

### Requirement: Interactive pipeline resolution
id: interactive-pipeline-resolution

When the interactive `/s:build` flow starts, it SHALL resolve the
effective autonomous pipeline exactly once by running the status CLI's
`pipeline-show --json` verb and SHALL read each entry's declared options
from the emitted JSON object's `entries` dicts and the provenance from its
`source` field, never re-deriving them from configuration files and never
parsing the human-rendered label lines, which carry no contract status. If
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

#### Scenario: Options are read from the JSON entries
- **GIVEN** a resolved build entry declaring `subagent_model` and
  `parallelism`
- **WHEN** `/s:build` resolves the pipeline at flow start
- **THEN** the options are taken from the `--json` object's entry dicts,
  not parsed out of rendered label lines

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
