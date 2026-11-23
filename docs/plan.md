<!-- doc-type: how-to -->

# Plan a change

Planning turns a request into a **change**: a lean artifact set under the
content directory's `planned/<change>/`. The set holds `plan.md` (the idea and
the binding implementation decisions), one delta spec per affected
capability, and `tasks.md` (the checklist a build executes).

`/s:plan` writes that set inside the change's worktree, `.worktrees/<change>`,
on branch `change/<change>`. The artifacts then travel with the code in one
pull request. `/s:plan` stops before anyone writes code.

## When to use it

- **`/s:plan`** — for one buildable change, scoped and understood.
- **`/s:plan-deep`** — for a planned change, or an epic's members, whose
  riskiest pieces you want to walk one step at a time before the build.
- **[`/s:epic`](epics.md)** — for a feature that spans several independent changes.

Unsure the idea holds up? Talk it through with the [rubber duck](duck.md)
first. Still unsure of the problem or its users? Write a [PRD](prd.md) first.

## How to run it

### Plan a change

Pass the request as the argument:

```sh
/s:plan add a --json flag to shipd locate
```

The skill runs these steps:

1. **Investigate.** It reads the code, the spec library, and the in-flight
   changes before it asks anything. It never asks what the repository answers.
2. **Consult before asking.** It reads your personal memory store, then asks
   the [oracle](oracle.md) about each open decision.
3. **Ask once.** Decisions the oracle leaves open reach you in one typed
   question round, each with concrete options.
4. **Pick a path.** The depth gate counts risk signals. A simple change takes
   the fast path; an open-ended one takes the depth path, a grill loop of
   grouped rounds.
5. **Attest readiness.** It prints a four-item readiness attestation, and
   writes the evidence into `plan.md`.
6. **Install.** The engine validates the staged artifacts and installs the
   change at `draft`, or installs nothing.
7. **Gate.** The context gate checks that the plan holds enough context to
   build. A pass promotes the change to `ready`. A failure parks it at
   `rejected`.
8. **Hand off.** It summarizes the change, motivation first, and prints
   [`/s:build`](build.md) alone on its last line.

The argument can also carry input beyond a text request:

- **A recording** — a `.mov`, `.mp4`, `.m4v`, `.webm`, or `.mkv` path. The
  skill runs [video ingest](video-ingest.md) first and plans from the brief.
- **A bundle slug** — the slug of an existing ingest bundle, read without a
  new ingest.
- **A supplied document** — the engine installs it under `docs/` in the
  content directory, and the plan cites it.

A brief whose intents span several changes stops the flow; the skill
recommends `/s:epic` instead. The skill does not run `/s:build` itself.

### Enrich a rejected change

A rejected change carries a `## Context insufficient` section in `plan.md`.
Re-run the skill on the change's name:

```sh
/s:plan add-locate-json
```

The skill edits the installed artifacts in place. It resolves every finding
the repository answers, and asks you only the true gaps. It then runs the
context gate again. The skill never forces the status: a gate pass is its only
exit to `ready`.

### Walk a risky plan

```sh
/s:plan-deep <change>
/s:plan-deep <epic> [<member> ...]
```

The skill walks a change only at `draft`, `ready`, or `rejected`. For an epic
with no named members, it scores each member against the risk rubric. It then
walks the `medium` and `high` members, in risk order.

Each flagged piece gets one step: keep it, change it, research it with
[`/s:research`](research.md), or cut it. The skill edits that change's
`plan.md`, delta specs, and `tasks.md` in place, then re-gates the change.

A single change ends with `/s:build`. An epic ends with the launch preflight,
and prints [`/s:autopilot <epic>`](autopilot.md) only when the preflight passes.

## Reference

### Statuses

| status | meaning |
| --- | --- |
| `draft` | the artifacts are written; no guards apply |
| `ready` | the artifacts validate, and the build may start |
| `active` | build agents are working through `tasks.md` |
| `complete` | every task in `tasks.md` is done |
| `verified` | verification passed; the change can merge and archive |
| `rejected` | the context gate parked the plan for enrichment |

The main line runs `draft → ready → active → complete → verified`. The gate
enters `rejected` from `draft` or `ready`. After enrichment, a person can also
return the plan to `draft` or `ready` through `/s:status`.

### Transition guards

- `ready`, `active`, `complete`, and `verified` require the change to
  validate.
- `complete` and `verified` also require a finished checklist.
- `draft` and `rejected` carry no structural guard.
- A refused transition states its reason. `--force` bypasses the guards, but
  never the check on the status name.

`/s:status` reports a status, or changes one through a guarded transition. It
runs as `/s:status [change]`, `/s:status validate [change]`, or
`/s:status set-status <status> [change]`. It asks before it ever forces.

### Lifecycle verbs

| verb | what it prints |
| --- | --- |
| `shipd status [change]` | a change's status and progress |
| `shipd lint [change]` | validation of the master library, or of one change |
| `shipd list [kind] [--all]` | changes, epics, verified, research, video, or docs |
| `shipd locate [change]` | where a change lives: `change:`, `root:`, `dir:`, `status:` |

Each verb accepts `--json`. The [content directory README](../.shipd/README.md)
owns the requirement and delta grammar.
