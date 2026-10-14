# autopilot-preflight
Status: ready
Theme: reliability

## Introduction

`/s:autopilot` promises an unattended run, but it often stops partway and
asks questions. You only find out when you check back and see it waiting.
Two gaps cause this. First, the launch never checks whether the run has
what it needs. Unplanned members get planned mid-run, and the plan-stage
prompt never says that no human is present. Second, a plan reflects the
code at planning time. Once the code moves, whether through other work or
an earlier member of the same run, the plan rests on assumptions nobody
re-checked. The build then stops to ask, or builds the wrong thing.

The ordering strategy has gaps too. Build waves ignore the epic's `After`
column, so a member can build alongside the member it depends on.
Dependency cycles collapse silently into waves of one. And the in-session
failure contract stops the whole drive on any single failed grade.

This epic adds a deterministic launch preflight and deterministic drift
detection. A model is consulted only where judgment is unavoidable.
The preflight is a rubric of `ok|warn|fail` checks run before launch, and
any `fail` blocks the launch. Drift detection compares git history since
each plan was gated against the files and symbols the plan cites. The
`/s:drift` skill asks a model to judge only the members that actually
drifted. The run itself becomes unattended for real: the launch
confirmation is the last question, and a failing member is parked
while independent members carry on.

Success criteria:

- An epic that passes the preflight runs to its end without asking a
  question; problems surface as parked members in the final report.
- A plan with no commit touching its cited files since it was gated
  reports no drift, and no model runs for it.
- A member never builds before every member its `After` cell names has
  merged into `main`.
- A dependency cycle in `After` fails the epic lint and the preflight.

### Non-goals

- No change to how `/s:plan` or `/s:epic-grill` ask their questions;
  this epic checks their output, it does not redesign them.
- No file-timestamp (mtime) comparison anywhere; checkouts rewrite mtimes.
- No preflight check that needs a model; semantic consistency between
  plans stays with the grill's consistency pass.
- No new pipeline stages or presets; the drift step runs inside the
  existing build entry.

## Decisions

- **Deterministic first.** Every preflight check and every drift
  detection is an engine verb. Each is stdlib-only Python, runs no model,
  and makes no call beyond the `git` and `gh` the engine already uses.
  A model runs only in `/s:drift`'s judgment of flagged members and in
  the re-plan that follows drift.
- **Commits, not timestamps.** Drift is measured by git ancestry from the
  plan's stamp to `main`. A plan has no file drift exactly when
  `git log <stamp>..main` over its cited files is empty.
- **The plan stamp.** `spec_gate.py` writes two header lines into
  `plan.md` on every pass: `Planned-at: <sha>` (the `main` commit the plan
  was gated against) and `Gated-hash: <hash>` (the plan's content hash,
  excluding these two lines and the `Status:` line, which lifecycle moves
  rewrite). A plan without a stamp falls back to the last commit that
  touched its `plan.md`.
- **Cited files and symbols.** Cited files are the path-shaped backticked
  tokens in `plan.md`, `tasks.md`, and the delta specs. Drift reuses the
  path-token pattern of the gate's task file references check, which today
  reads `tasks.md` alone, and widens it to `plan.md` and the delta specs.
  A cited symbol is a backticked identifier or `--flag`.
  It counts as drifted only when `git grep` finds it at the stamp and not
  on `main`. That rule keeps symbols the plan itself introduces from
  being flagged.
- **Preflight output.** `autopilot.py <epic> --preflight` prints one
  `ok|warn|fail <check> — <detail>` line per check, matching
  `shipd doctor`. It exits non-zero when any line is `fail`, and `--json`
  emits the same rubric as one object.
- **Unplanned members fail the preflight.** Launch needs every driven
  member at `ready`. An `unplanned` or `draft` member is a `fail` that
  names `/s:epic-grill <epic>` as the remedy.
- **Edited-after-gate fails the preflight.** A `ready` plan whose content
  no longer matches its `Gated-hash` fails. Re-gating is the remedy.
- **`After` is the single source of order.** Build waves honor it. A
  dependency is satisfied only once its PR has merged into `main`, and the
  dependent's worktree syncs `main` before its drift check. A cycle is an
  epic lint error and a preflight `fail`.
- **Overlap rules.** Two members modifying the same master requirement
  without an `After` edge between them is a preflight `fail`. Two members
  citing the same file without an edge is a `warn`. Every member edits
  `plugin.json` for the version bump, so that file is exempt.
- **Mid-run drift is re-planned, not asked.** Before each build stage, the
  drive runs the drift verb. When it finds drift and `/s:drift` judges the
  plan affected, a re-plan revises the plan under the no-human rule and
  re-gates it. The member is parked only when the revision contradicts a
  `USER` ledger answer or an epic Decision.
- **The launch confirmation is the last question.** After Phase 2, the
  in-session drive never asks. A failed grade, gate rejection, or drift
  conflict parks the member and the drive carries on with every member
  that does not depend on it. Parked members and their resume pointers
  appear in the final report.
- **Drift packaging.** The engine verb is `spec_status.py drift <change>`,
  with `--epic <slug>` and `--json`. It exits `0` when clean and `4` on
  drift, matching `check-base`. `/s:drift` is a thin skill over the verb.
- **Version bump per member.** Every member touching `plugins/s/` bumps
  `plugins/s/.claude-plugin/plugin.json` in its own PR, per `AGENTS.md`.

## Design

The pieces form three layers.

**Stamp layer.** `spec_gate.py` writes `Planned-at` and `Gated-hash` on
every pass. `spec_gate.py --check` runs every gate check read-only: it
writes nothing, changes no status, and exits as the gate would. The
linter accepts both header lines.

**Detection layer.** `spec_status.py drift` reads the stamp, extracts
cited files and symbols, and reports three findings:

- `file-drift <path> <commits>`: a commit since the stamp touched a cited
  file.
- `symbol-gone <name>`: a symbol present at the stamp is missing from
  `main`.
- `stale-base`: reused from `check-base`.

`/s:drift` runs the verb and gives the model only the flagged members'
diffs since their stamps. The model returns one verdict per member:
`holds`, `revise`, or `conflict`.

**Orchestration layer.**

- `compute_waves` orders build waves by `After` and merged state.
- `autopilot.py --preflight` composes the rubric from the epic lint,
  `epic-show`, `spec_gate.py --check`, `drift`, and the overlap and cycle
  checks. It also uses `pipeline-show` and `shipd doctor`.
- `/s:autopilot` runs the preflight in Phase 1, and any `fail` stops
  before Phase 2. It adds a pre-build drift step and switches to
  park-and-continue.
- The detached driver gains the same pre-build drift step, using its
  existing enrichment-session machinery for the re-plan.
- `/s:epic-grill` ends by running the preflight. It hands off to
  `/s:autopilot` only on a green rubric, and otherwise lists the failing
  lines.

The `After` column below orders the members along those layers.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk | After |
| --- | --- | --- | --- | --- | --- | --- |
| gate-plan-stamp | Gate writes `Planned-at` and `Gated-hash` into plan.md on every pass; lint accepts both; add read-only `spec_gate.py --check` | low | medium | low | low | |
| wave-dependency-order | Build waves honor `After` and wait for a dependency's merge into main; `After` cycles become an epic lint error | medium | medium | low | medium | |
| drift-verb | `spec_status.py drift` reports file, symbol, and base drift since the plan stamp, per change or `--epic`, with `--json` | medium | medium | medium | medium | gate-plan-stamp |
| drift-skill | `/s:drift` runs the verb and asks a model for a holds/revise/conflict verdict on flagged members only | low | medium | medium | low | drift-verb |
| autopilot-preflight-verb | `autopilot.py --preflight` prints the ok/warn/fail launch rubric and exits non-zero on any fail | medium | high | medium | medium | drift-verb, wave-dependency-order |
| autopilot-unattended-run | `/s:autopilot` runs the preflight, adds the pre-build drift step, parks and continues, and tells plan stages no human is present | medium | high | medium | high | autopilot-preflight-verb, drift-skill |
| detached-drift-replan | The detached driver runs the pre-build drift step with a re-plan session and parks on conflict | medium | high | medium | medium | drift-verb |
| grill-preflight-handoff | `/s:epic-grill` ends by running the preflight and hands off only on a green rubric | low | low | low | low | autopilot-preflight-verb |
