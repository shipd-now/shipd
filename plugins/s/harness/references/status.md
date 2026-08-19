# /s:status — the status vocabulary and its guards

The long form the router points at. Read it when a transition is refused and
the refusal reason alone does not tell you what to do.

## The six statuses

| status | meaning |
| --- | --- |
| `draft` | emitted and installed, not yet approved for building |
| `ready` | approved by the context gate; no task started |
| `active` | a build is running against it |
| `complete` | every task is checked off |
| `verified` | the code was exercised against the delta scenarios and passed |
| `rejected` | the context gate parked it — `plan.md` carries a `## Context insufficient` section listing what is missing |

`rejected` is the context-sufficiency gate's parking state, not a failure
state. `set-status draft` or `set-status ready` is how a human returns an
enriched plan to the pipeline; re-running `spec_gate.py` is how the gate
itself does it.

## What each guard requires

`draft` and `rejected` carry **no guard** — a parked plan may legitimately be
structurally broken, which is the point of parking it.

- `ready` and `active` require the change to **validate**. A refusal prints
  `setting <status> requires the change to validate`, followed by one `ERROR:`
  line per structural problem. Fix the artifacts rather than forcing.
- `complete` and `verified` require validation **and a finished checklist**.
  The refusal names the counts: `setting <status> requires all tasks done
  (<done>/<total> done, <n> in progress)`. A missing `tasks.md`, or one with
  no checkbox lines at all, is refused the same way.

`ready` has one further rule the guard cannot express: it is the **context
gate's** verdict to give. Reaching `ready` by `set-status`, forced or not,
bypasses `spec_gate.py` and is a protocol violation — run the gate instead.

## Exit codes

| code | meaning | what to do |
| --- | --- | --- |
| 0 | the transition succeeded | report the new status |
| 1 | a real error — unknown change or status, no selection | show the `Error:` line; never force |
| 3 | a guard refused | surface the `Refused:` reason, ask the user, force only on an explicit override |

`--force` skips the guard, not the error. It can only ever change the outcome
of an exit-3 refusal.

## Epics are not changes

`set-status` writes change statuses only. An epic's status is either derived
from its members with `epic-sync <slug>` or written directly with
`epic-set-status <status> <slug>`, whose vocabulary is `draft`, `ready`,
`active`, and `complete`. `epic-set-status ready` refuses unless the epic
lints clean, and refuses with the same exit-3 contract as above.

## The board report

With no argument and no selected change, the status report is the whole
delivery board derived from the spec tree: a `N specs · N epics · N
initiatives` totals line, a `shipped <n>/<m>` line over every rendered row,
and four lanes — `UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each with its
count. Non-shipped lanes carry one row per change naming its epic (or
`standalone`), its slug, state, risk, and a `[worktree]` marker; `SHIPPED`
collapses to one `<epic-slug> (<n>)` rollup row per epic. Relay it exactly as
printed — re-counting or re-ordering the lanes makes the report wrong.
