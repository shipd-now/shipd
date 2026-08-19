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

The dry run's **`Member order (risk ascending):`** block lists only the
`unplanned` members. Every other member, `ready` included, appears instead
among the summary's `skipped: <member> (<state>)` lines. So a drive that also
covers `ready` members reads **both** sections: the ordered block first, then
the `skipped:` entries whose state is `ready`, in printed order. Never
re-derive the order, and never conclude a `ready` member was excluded merely
because the ordered block does not carry it — that block never carries `ready`
members at all.

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
  session: `session` inherits it, `tier-below` and `tier-two-below` step one or
  two rungs down the ladder and clamp at the bottom, and anything else is a
  concrete id passed through verbatim.
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
  detached driver's budgets. A run with a human present ignores them — the
  human is the retry loop.

## Failure contract

A detached run parks; a run with a human present asks. With a human present:

- a **failed stage grade** stops the drive and puts the situation to the user,
  naming the member and the stage;
- a **gate rejection** is raised to the user rather than parking the member as
  `rejected`;
- a **command entry exiting non-zero** stops the drive the same way, naming
  the member, the entry, the exit code, and the output — never retried on an
  attempt budget.

In every case no further member starts while the stop is unanswered, and the
drive resumes at the same member and stage once the user answers.

## Resuming

An interrupted run needs no run-state file: member state already lives on disk
as the spec status, the lint result, the pull request, and the review gate.
Re-invoking the command for the same epic re-reads that state and re-enters
each member at the stage its current state maps to, so members that already
advanced pick up where they stopped.
