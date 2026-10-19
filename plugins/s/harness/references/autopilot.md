# /s:autopilot — entry forms, grading, and the failure contract

The long form the router points at. Read it when interpreting a parked member,
or when the resolved pipeline carries anything beyond the four built-in
stages.

## Which members are driven, and where they enter

A member's on-disk state decides both whether it is driven and which pipeline
stage it enters at:

| member state | entry stage |
| --- | --- |
| `unplanned` | `plan` |
| `ready` | `build` |
| anything else | not driven — named in the summary with its state |

The drive's grouping and order come from the driver's `--waves` mode: its
`waves` array, in order, is the drive's script over members, and each wave's
`members` run together. The mode lists only the members drivable now and
reports every other member in `skipped: <member> (<state>)`. Never re-derive
the order from the dry run or the roster — the dry run is the detached mode's
preview, and a `ready` member that does not appear in a plan wave enters a
build wave on a later call.

Each driven member gets its own worktree, and every stage for that member runs
with that worktree as its working directory. The worktree helper is
idempotent: it reuses an existing worktree or re-attaches an existing branch
rather than erroring, so an interrupted run's resume needs no guard.

## Walking the pipeline

The pipeline's machine contract is the `entries` array of
`pipeline-show --json` — one object per entry, each carrying exactly the
options it declares. Read it once per run and never re-derive it from
configuration files, and never read the pipeline off the dry run's rendered
labels, which are human-facing only.

For each member, slice that array to start at the first entry whose `stage`
equals the member's entry stage, and run from there in list order. Everything
before the slice point — custom entries included — is already satisfied and is
not run. When no entry carries the member's entry stage, walk the whole list.

Each entry is then dispatched by its **form**, tested in exactly this order:

| form | handling |
| --- | --- |
| `custom` | run its `command` in the member's worktree, at its position in the list |
| `skip: true` | announce it as skipped and run nothing |
| stage `research` or `epic` | a pre-approval stage — note it and ignore it |
| `replace` declaring a `command` | run that command **in place of** the built-in stage |
| `replace` naming only a `tool` | announce that the replacement has no command and skip it — the built-in behaviour does **not** run |
| a built-in stage with none of the above | its built-in behaviour |

Command entries — custom steps and replacements alike — run directly, never
through a delegated session. A skipped entry carries no other option by
schema, so no option handling applies to it.

## Grading a stage — from the repository, never from a report

| stage | passes when |
| --- | --- |
| `plan` | the member's status reads `ready` **and** its lint exits 0 |
| `build` | a `completed/` entry ending in `-<member>` exists **and** the member's branch has a pull request URL |
| `review` | the pull request head's `semantic-review` status is `success` **and** the resolver reports `unresolved=0` |
| `custom`, or a `replace` carrying a command | that command exited 0 |

A session reporting success over a stage that has not met its grade does
**not** advance the drive; only a passing grade does. The report is context
for the grade, never a substitute for it.

## Stage options the resolved entry declares

Options are read from the same `entries` dicts, never re-derived:

- **`model`** — the tier that stage runs on, resolved relative to the acting
  session: `session` inherits it, `high`, `medium`, and `low` are effort
  levels resolved against the stage's built-in default or the entry's own
  declaration, and anything else is a concrete id passed through verbatim. The
  harness expresses a level with its own knob: `--effort` for Claude Code,
  `--model <base>#<level>` for OpenCode.
- **`tools`** — a preferred-tool binding appended to the stage's instruction as
  one `<name> (fallback: <fallback>)` per binding, joined by `; `.
- **build options** — `validator` false skips the adversarial validation pass
  (the mechanical verification still runs), `telemetry` false skips the token
  breakdown and report, `parallelism` caps concurrent execution, and
  `subagent_model` picks the executors' tier. Each appends one line to the
  build instruction; an entry declaring none leaves it unchanged.
- **review options** — `disposition` narrows how much per-finding judgement
  the review spends (`all`, `high-only`, `none`) and `model` is recorded as
  provenance. The grade is unchanged in every scope.
- **`autopilot` blocks** (`attempts`, `timeout`, `max_resumes`) are the
  detached driver's budgets. An in-session run ignores them too: a failed stage
  parks, it is never retried on a budget.

## Pre-build drift step

Once per member, when its walk reaches an entry whose `stage` is `build`, sync
and measure the member before that entry runs. In `.worktrees/<member>` run
`git fetch origin main`, then `git merge --no-edit origin/main`; a non-zero
merge runs `git merge --abort` and parks the member as `sync-conflict`.

Measure with `spec_status.py --root .worktrees/<member> drift <member> --base
origin/main --json`:

| exit | what happens |
| --- | --- |
| 0 | build — no model is spawned |
| 4 | judge with one `/s:drift <member> --base origin/main --json` sub-agent |
| anything else | park as `drift-error`, naming the command's `Error:` line |

The judge reads `verdicts[0].verdict` from the sub-agent's final text; a
missing or unparseable object parks as `drift-error`. `holds` builds, `conflict`
parks as `drift-conflict` naming the verdict's `contradicts`, and `revise` runs
one re-plan sub-agent in the worktree — naming the verdict's `revise:` pointer
and reason, staying inside the plan's `**Answered by:** USER` entries and the
epic's Decisions, and ending with `spec_gate.py <member> --base origin/main`.
Grade the revision from disk: status `ready`, `spec_lint.py` exit 0, and
`spec_gate.py <member> --check` exit 0; anything else parks as `replan-failed`.
The step never repeats for a member in one run.

### Resume pointers

| parked reason | resume pointer |
| --- | --- |
| `gate-rejected`, `replan-failed` at `rejected` | `/s:plan <member>` |
| `grade-failed build`, `command-failed`, `sync-conflict` | `/s:build <member>` in `.worktrees/<member>`, or re-run `/s:autopilot <epic>` |
| `grade-failed review` | the review instruction's post flow on the member's pull request URL |
| `drift-conflict` | settle the named `Q<n>` (`/s:epic <epic> amend` for a Decision), re-gate, then re-run `/s:autopilot <epic>` |
| `drift-error` | `/s:drift <member>` in the worktree, then re-run `/s:autopilot <epic>` |

## Failure contract: park and continue

After the launch confirmation no human is present, so the in-session drive
never asks. A failed stage grade (`grade-failed <stage>`), a gate rejection
(`gate-rejected`), a command entry exiting non-zero (`command-failed <entry>
exit <rc>`), and the pre-build step's `sync-conflict`, `drift-error`,
`drift-conflict`, and `replan-failed` each park the member: record the reason in
the session, emit `heartbeat.py build-finish <member> --outcome parked`, and
start no further entry for it. The parked set lives in the session only — no
plan status is written for a parked member.

Inside a wave, the other in-flight sub-agents run to their end and are graded,
and the drive continues with the next round and wave. Before every `--waves`
re-run, `git fetch origin main`; drop parked members, mark as held every
`blocked` entry whose `waiting_on` names a parked or held member (to a
fixpoint), and skip a wave emptied that way.

When no runnable wave remains but `blocked` holds entries that are not held,
poll `gh pr view change/<dep> --json state` for each `waiting_on` every 60
seconds, up to `--timeout` seconds in total. Once every dependency reports
`MERGED`, fetch and re-run `--waves`; when the bound expires or a dependency
reports `CLOSED`, end the run and list those members as blocked — `held by
<parked>` for a dependent of a parked member, `waiting on <dep>` for a
dependency that never merged. A dependent of a parked or held member is never
waited for.

## Resuming

An interrupted run needs no run-state file: member state already lives on disk
as the spec status, the lint result, the pull request, and the review gate.
Re-invoking the command for the same epic re-reads that state and re-enters
each member at the stage its current state maps to, so members that already
advanced pick up where they stopped. A parked member is re-driven the same way
once the remedy its resume pointer names is done.
