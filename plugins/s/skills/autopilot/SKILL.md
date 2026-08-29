---
name: autopilot
description: >-
  Drive an approved epic's unplanned members to shipped PRs unattended: plan →
  gate → build → auto-merging PR per member over the configured pipeline, in
  risk-ascending order, one worktree/branch each. Preflights the epic, confirms
  the run controls, runs the autopilot in the foreground, and relays its report
  with resume pointers for any parked members. Use when asked to "autopilot an
  epic", "deliver an epic", "ship the epic's members", or "/s:autopilot".
  Trigger phrases: "autopilot", "deliver", "ship the epic", "/s:autopilot".
---

# /s:autopilot — Autonomous epic delivery

You are the **Autopilot wrapper**. Your job is thin: preflight one epic, confirm
the run controls with the user, run the autopilot **in the foreground**, and
relay its report. You **never plan, build, gate, review, or answer a driven
session's questions yourself** — the autopilot drives real headless sessions and
owns every stage decision. You only orchestrate the launch and relay the result.

Requirements: this repo must have the resolved content-directory layout
(default `.shipd/`) and the named epic must exist and be **approved**
(`ready` or `active`). The epic approval is the last human gate; everything
after it is the autopilot's job.

## Mode selection

The skill drives the epic one of two ways:

- **In-session drive (default).** The skill itself loops over the epic's
  members inside this Claude Code session, spawning one general-purpose
  sub-agent per pipeline stage. Use this mode unless the invocation asks for a
  detached run.
- **Detached run (opt-in).** The existing headless `claude -p` driver
  (`autopilot.py`), run in the foreground. Use this mode only when the
  invocation asks for it — e.g. `/s:autopilot <epic> detached`, or the user
  asking in words for a detached or unattended run.

Decide the mode before Phase 1 and carry it through the confirmation in Phase 2.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Autopilot driver: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py`
- Status CLI (for preflight views): `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
- Delivery board (live run view): `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/dashboard.py`

Run every command **from the repository root** (so `--root` defaults to the cwd
and the plugin's worktree helper resolves the repo). The epic slug is the sole
required argument to `/s:autopilot <epic>`.

---

## Phase 1 — Preflight (read-only; drives nothing)

1. **Confirm the epic is approved.** Run `epic-show` and read the status line:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" epic-show <epic>
   ```
   - If the epic is missing, or its status is `draft` or `complete` (anything
     other than `ready`/`active`), **stop here**: report that the epic is not
     approved for delivery (a `draft` epic still needs `epic-set-status ready`;
     a `complete` epic has nothing left to drive) and drive nothing. Do not run
     the autopilot.
2. **Show the roster.** The `epic-show` output already lists every member and
   its derived state — relay it. What gets driven depends on the mode decided
   above: the **detached** run drives only the members shown as `unplanned`, in
   risk-ascending order, and reports every other state (`ready`, `rejected`,
   `active`, `archived`, …) without touching them. The **in-session** drive
   additionally drives members shown as `ready` (entering at the `build`
   stage — see Entry stage per member below), so only states other than
   `unplanned` and `ready` are left undriven and merely reported.
3. **Show the resolved pipeline** the run will honor:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" pipeline-show
   ```
4. **Dry-run for the exact plan.** Print the member order and resolved pipeline
   the run will use, driving nothing:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py" <epic> --dry-run
   ```

## Phase 2 — Confirm the run controls

The autopilot spends real model time and opens real PRs. Before launching,
**AskUserQuestion** to confirm scope with these controls (surface the dry-run's
member list so the choice is informed), **naming which mode the run will use**
(in-session, unless a detached run was requested — see Mode selection above):

- **`--max-members N`** — cap how many members this run drives (default:
  unlimited; every `unplanned` member).
- **`--timeout` seconds** — per-session wall-clock budget (default: 1800).
- **`--max-resumes`** — resumed turns a driven session may spend before its
  grade decides the stage (default: 4).

Offer at least: **"Deliver all members"** (the recommended default, unlimited),
**"Deliver one member first"** (`--max-members 1`, a cautious single-member
trial), and **"Cancel"** (drive nothing). Honor a typed override of any knob. On
**Cancel**, stop without running the autopilot.

Before launching, **name the live view**: the run writes a heartbeat the
delivery board reads, so from another terminal the user can watch stages land
live with
```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/dashboard.py" tui --epic <epic>
```
(press `q` to quit; the board is read-only and never touches the run). Surface
this command as part of the confirmation so the user can open it before the run
starts.

## In-session drive (default mode)

This phase applies only to the **in-session** mode (see Mode selection above).
In the detached mode, skip this phase and go to Phase 3 (detached run) instead.

### Member order and pipeline

Obtain the member order and the resolved pipeline by running the driver's dry
run — the order is **never re-derived in the skill**, it is taken exactly as
the dry run prints it, and the dry run itself performs no session, gate, or
worktree action:
```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py" <epic> --dry-run
```
The dry run's **`Member order (risk ascending):`** block lists only
`unplanned` members — it does not include `ready` members. Every other
member, `ready` included, instead appears among the `skipped:` lines the
run's summary prints, one per member, as:
```
skipped:    <member>  (<state>)
```
Parse **both** sections and select members from them: first the members in
the printed `Member order` block, in that order; then, appended after them,
the `skipped:` entries whose `(<state>)` is `ready`, in the order they are
printed. This selection is the full drive order over the resolved pipeline —
never re-derive it, and never skip a `ready` member for being absent from the
`Member order` block, since that block never carries `ready` members at all.

### Entry stage per member

Each member's current state maps to the pipeline stage it enters at — this
mirrors `_ENTRY_STAGE` in
`plugins/s/skills/build/scripts/autopilot.py`:

| member state | entry stage |
| --- | --- |
| `unplanned` | `plan` |
| `ready` | `build` |
| anything else | skipped — name the member and its state in the run summary |

A member reaches this table only once **Member order and pipeline** (above)
has selected it. `unplanned` members arrive via the printed `Member order`
block; `ready` members arrive via the `skipped:` lines, filtered to `(ready)`
— never via the `Member order` block, which never lists them. So the
`ready` → `build` row is reached in practice through that skipped-list
selection, not by a `ready` member ever appearing in the dry run's ordered
list. Only member states other than `unplanned` and `ready` are left
undriven; every `unplanned` and every `ready` member is selected and driven.

### The entry walk

The resolved **entry list** is the drive's script. Obtain it **once per run**
from the status CLI's machine contract — never re-derive it in the skill, and
never read it off the dry run's rendered labels:
```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" pipeline-show --json
```
It emits `{"source": "<source>", "entries": [...]}`; the `entries` array, in
order, is the pipeline every driven member walks, and each entry dict carries
exactly the options it declares.

For each driven member, walk that array starting at the member's **entry
stage** (the table above): slice the list to start at the first entry whose
`stage` equals that stage — `unplanned` → the first `plan` entry, `ready` → the
first `build` entry — and run the entries from there in list order. This
mirrors `_pipeline_from_stage` in
`plugins/s/skills/build/scripts/autopilot.py`. Every entry **before** the slice
point — custom entries included — is already satisfied and is **not** run. If
no entry carries the member's entry stage, walk the whole list unchanged.

The dry run remains the source of the **member order** only (see Member order
and pipeline above); its rendered entry labels are human-facing and carry no
contract status. Each entry is then handled by its form (see Entry forms
below), and a sub-agent is spawned only for a built-in stage entry the forms
leave to its built-in behavior.

### Per-member setup

`worktree.sh` is idempotent: it reuses a member's existing worktree (or
re-attaches its existing branch) instead of erroring, so an interrupted run's
resume needs no guard. For each member being driven, invoke it unconditionally:
```
"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/worktree.sh" <member>
```
Run every stage for that member with that worktree (`.worktrees/<member>`) as
the working directory.

### Entry forms

Every entry in the walked slice is dispatched by its **form**, mirroring the
detached driver's `drive_member` in
`plugins/s/skills/build/scripts/autopilot.py`:

| entry form | in-session handling |
| --- | --- |
| `custom` | run its `command` via Bash in the member's worktree, at its position in the list |
| `skip: true` | announce the entry as skipped and run nothing for it |
| `stage` of `research` or `epic` | note it as a pre-approval stage and ignore it |
| `replace` declaring a `command` | run that command via Bash in the member's worktree **in place of** the built-in stage — spawn no stage sub-agent |
| `replace` naming only a `tool` | announce that the replacement has no command, and skip the entry — the built-in behavior does **not** run |
| a built-in `stage` (`plan`, `gate`, `build`, `review`) with none of the above | its built-in behavior, below |

The rows are tested **in that order**, exactly as the driver tests them: a
`custom` entry first (it carries no `stage`), then `skip`, then the
pre-approval stages, then a `replace`, and only then the built-in behavior.

Command entries — custom steps and replacements alike — run **directly via
Bash** with the member's worktree as the working directory, never through a
sub-agent; this is the same precedent as the `gate` entry, which the drive
already runs directly. By schema a skipped entry carries no other option, so no
option handling applies to it.

### Running a stage

Each `plan`, `build`, or `review` stage is run by spawning one
**general-purpose** sub-agent via the Agent tool, with that stage's working
directory set to the member's worktree. The sub-agent's message is that
stage's instruction — the same shape `_stage_prompt` produces in
`plugins/s/skills/build/scripts/autopilot.py` — given verbatim below with
`<member>` substituted for the member's slug:

**Plan stage instruction:**
```
Run /s:plan for the change `<member>` — a member of an approved epic.
Investigate, spec it, and promote it to Status: ready.
```

**Build stage instruction:**
```
Run /s:build for the change `<member>`: implement every task, then merge
and archive it and open its auto-merging PR.

If a sub-agent escalates a QUESTION: that the spec artifacts and code cannot
answer, consult the oracle (spawn agent `s:oracle` with a compact
question) before answering on your own authority; on INSUFFICIENT, answer
with your own recommendation — never leave the sub-agent blocked.
```

**Review stage instruction:**
```
Post the semantic-review gate for the change `<member>` and disposition its
findings. Run /s:review on branch `change/<member>` against `main`
(merge-base semantics), then publish the verdict to the member's PR with the
poster: emit the `--json` object to a temp file and run
  python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/review_gate.py" post
  change/<member> --from <that file>
so the summary comment, anchored inline comments, and the `semantic-review`
commit status all land on the PR's head SHA.
Then run the disposition loop over every posted finding, low included:
implement the suggestion (edit, commit, push, and re-review so the status
tracks the new head) when it is correct, otherwise reply on the finding's
thread with the concrete reason via `review_gate.py reply change/<member>
<comment-id> --body <reason>` — never leave a finding with neither. Finish
with `review_gate.py resolve change/<member>` so every gate thread resolves;
the stage is graded on the `semantic-review` status being green AND
`resolve --check` reporting `unresolved=0`.
```

### Stage options declared by the resolved entry

Read each entry's options from the `entries` dicts of the same
`pipeline-show --json` object the walk consumes (The entry walk above — one
call per run) — e.g. `{"stage": "build", "subagent_model": "tier-two-below",
"validator": false, "telemetry": false}` — and never re-derive them from the
config.

**A declared `model` picks the stage sub-agent's model.** When the entry
declares `model`, spawn that stage's sub-agent with the Agent tool's `model`
parameter set to the tier resolved **relative to this session**:

| declared `model` | Agent tool `model` |
| --- | --- |
| `session` | omit the parameter — the sub-agent inherits this session's model |
| `tier-below` / `tier-two-below` | the alias one / two steps below this session's own model on the ladder `fable` → `opus` → `sonnet` → `haiku`, clamped at `haiku` |
| anything else | a concrete model id — pass it verbatim |

**A declared `tools` binding decorates the stage instruction.** When the entry
declares `tools`, append to that stage's instruction a blank line and then this
line, verbatim per `_stage_prompt` in
`plugins/s/skills/build/scripts/autopilot.py`:
```
Preferred tools for this stage, use when available: <name> (fallback: <fallback>); <name> (fallback: <fallback>).
```
— one `<name> (fallback: <fallback>)` per binding in the entry's declared
order, joined by `; `, and the line ends with a period. A `gate` entry spawns
no sub-agent in-session, so its `tools` have no instruction to decorate —
exactly as in the detached driver, where only stage prompts carry the suffix.

**`autopilot` blocks are ignored in-session.** An entry's `autopilot.attempts`,
`autopilot.timeout`, and `autopilot.max_resumes` are the detached driver's
retry and session budgets. Interactively the human is the retry loop, so
enforce no budget from them: a failed stage stops and asks the user exactly as
the failure contract below prescribes.

**Declared build options append one line each** to the build instruction above
(an entry declaring none leaves that block unchanged), mirroring the detached
driver's prompt verbatim:
```
Stage options for this build, overriding the skill's defaults:
- Skip the adversarial validator phase: do not spawn the `s:validator`
  sub-agent; the mechanical verification still runs.
- Skip the token telemetry: do not persist the per-tool token breakdown and
  do not render the token report.
- Cap concurrent execution sub-agents at <parallelism>.
- Spawn execution sub-agents with the Agent tool's `model` set to
  `<resolved>` (the pipeline's `<subagent_model>`).
```
Include the validator line only when the entry declares `validator` false, the
telemetry line only when it declares `telemetry` false, the cap line only when
it declares `parallelism`, and the sub-agent-model line only when it declares
`subagent_model` — resolved by the table above, anchored on this stage's own
model.

**Declared review options** change the review instruction in two places. The
poster invocation gains ` --disposition <scope>` when the entry declares
`disposition` and ` --model <tier>` (the symbolic tier verbatim — the poster
records it in the summary comment) when it declares `model`. The disposition
paragraph then matches the scope: `all` keeps the paragraph above, while
`high-only` and `none` replace it with, respectively:
```
Then run the disposition loop under the `high-only` scope: implement every
high-severity finding (edit, commit, push, and re-review so the status tracks
the new head), then dispose of the rest in one call — `review_gate.py
autoreply change/<member> --disposition high-only` — which posts the canonical
policy reply onto every medium and low gate thread.
```
```
Then dispose of every posted finding by policy rather than by judgement: run
`review_gate.py autoreply change/<member> --disposition none`, which posts the
canonical policy reply onto every gate thread; implement nothing.
```
The grade is unchanged in every scope — the `semantic-review` status green
**and** `resolve --check` reporting `unresolved=0`; `autoreply` is what gets a
cheapened scope there.

A `gate` entry in the resolved pipeline is run directly (`spec_gate.py
<member>` in the member's worktree), not via a sub-agent; see the failure
contract below for what happens on a rejection.

Members are driven **one at a time**, in the dry run's order — no member's
entries start before the previous member finishes or stops. No headless
`claude -p` process is started anywhere in this mode: every built-in stage the
entry forms leave to its built-in behavior runs as an Agent-tool sub-agent
inside this session, and the `gate` and command entries run directly from this
session via Bash.

### Grading a stage

| stage | passes when |
| --- | --- |
| `plan` | `spec_status.py status <member>` prints `ready` **and** `spec_lint.py <member>` exits 0 |
| `build` | a `completed/` entry ending in `-<member>` exists **and** `gh pr view change/<member> --json url` yields a URL |
| `review` | the PR head's `semantic-review` commit status is `success` **and** `review_gate.py resolve --check` reports `unresolved=0` |
| a `custom` entry | the `command` the drive ran in the member's worktree exited 0 |
| a `replace` entry declaring a `command` | that command, run by the drive in the member's worktree in place of the built-in stage, exited 0 |

A stage is graded **by reading the repository through these public CLIs — never
by trusting the sub-agent's own summary.** A sub-agent reporting success over a
stage that has not actually met its grade — an ungraded stage — does not
advance the drive; only a passing grade from the table above does.

A **command entry** (custom or replacement) is graded on the exit code the
drive itself observed from its own Bash run — never on a sub-agent summary,
since no sub-agent is spawned for it. Exit 0 passes the entry and the walk
continues to the next one.

### The sub-agent reporting contract

A stage sub-agent **cannot message this orchestrator mid-run**: its report
reaches you only as the **final text of its turn**. So a stage sub-agent runs
its stage to a terminal state within its own turn and ends that turn with its
report; nothing it leaves running in its own context — a background process, a
`gh pr` watch, a poll loop — is ever observed here, because no one resumes a
sub-agent to collect it.

The orchestrator therefore **grades from the repository** (the table above) the
moment a stage sub-agent's turn ends, and **never waits** on a process or watch
a sub-agent left running. The report is context for the grade, never a
substitute for it.

### Failure contract: ask, never park

The in-session drive has a human present, so it never parks a member as
`needs-human` or `rejected` the way the detached driver does. Instead:

- **A failed stage grade** — the sub-agent's turn ends but the stage's grade
  (above) does not pass — **stops the drive** and puts the situation to the
  user, naming the member and the stage that failed.
- **A gate rejection** — `spec_gate.py <member>` exits rejecting the plan's
  context — is likewise **raised to the user**, not parked as `rejected`.
- **A command entry exiting non-zero** — a custom step's command, or a
  replacement's — **stops the drive** the same way, naming both the member and
  the entry that failed (`custom:<name>` for a custom step, the replaced stage
  for a replacement) along with the command's exit code and output. It is never
  retried on an attempt budget (the detached driver's `attempts` are ignored
  in-session) and the member is never parked.

In every case, **no further member is started** while the stop is unanswered;
the drive resumes with the same member and stage once the user responds.

### Resuming an interrupted run

An interrupted in-session run needs **no run-state file**: member state already
lives on disk (spec status, lint, PR, review gate). Re-invoking the skill for
the same epic re-reads that state and re-enters each member at the stage its
current state maps to (see Entry stage per member above) — members already
advanced pick up where they left off.

### Board liveness

Emit the per-member build heartbeat around each member:
```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/heartbeat.py" build-start <member>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/heartbeat.py" build-stage <member> --stage <stage>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/heartbeat.py" build-finish <member> --outcome <outcome>
```
Run `build-start` when the member begins, `build-stage` as each entry is
entered, and `build-finish` with the member's outcome when it ends. The
`--stage` label mirrors the detached driver's: the entry's stage name for a
built-in or replaced stage entry, and `custom:<name>` for a custom entry. These
verbs are **fail-soft** — a heartbeat write failure never stops the drive.

This heartbeat only makes the board's **activity indicator** report the run
as building rather than idle. It does **not** move the driven member's
**card** into the building lane: card placement reads the member's on-disk
lifecycle state, plus the epic-level *run* heartbeat — a different heartbeat
that only the detached driver (`autopilot.py`'s own run) writes, never this
per-member one. Concretely, a member driven from `unplanned` keeps its
`unplanned` card in place until its plan sub-agent's first artifact write
changes that on-disk state — the per-member heartbeat above does not move it
sooner.

### The in-session run summary

When the drive ends (all members done, or stopped for the user), report:

- **Shipped** members with their full PR URLs (never just a number).
- **Stopped for the user**: the member and the stage that stopped the drive
  (a failed grade or a gate rejection).
- **Skipped** members with their state (the non-`unplanned`/`ready` states
  from Entry stage per member above).

## Phase 3 — Detached run: drive the autopilot in the foreground

This phase applies only to the **detached** mode (see Mode selection above). In
the default in-session mode, skip this phase and go to the in-session drive
phase instead.

Run the driver with the confirmed knobs and **wait for it to finish** — never
background it:
```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/autopilot.py" <epic> [--max-members N] [--timeout S] [--max-resumes R] [--session-model MODEL]
```
A detached run cannot see this session's model, so the symbolic tiers in the
pipeline (`session`, `tier-below`, `tier-two-below`) resolve against an
**anchor**: the ladder top (`fable`) unless `--session-model` names another.
The dry run prints the acting anchor as its `Model tier anchor:` line and the
run report records it as `tier_anchor` — surface that line when confirming the
run, and pass `--session-model <alias>` when the user wants the stages
anchored on a weaker model than the ladder top.
The autopilot creates a worktree per member, drives plan → gate → build (honoring
skips, replacements, custom steps, and tool bindings), and — on a gate context
rejection — drives a single oracle-backed enrichment session and re-runs the gate
before parking the member as `rejected` only if that attempt still does not pass;
it parks otherwise-failing members, writes a JSON report, and — when any member PR
merged — runs the epic-sync close-out. You do not intervene in any driven session.

## Phase 4 — Detached run: relay the report

This phase applies only to the **detached** mode. Relay the autopilot's report
verbatim, then add human-readable pointers:

- **Shipped** members with their PR URLs (full clickable URLs, never just a
  number).
- **Parked — rejected** (gate found the plan's context insufficient): note that
  the autopilot's automatic oracle-backed enrichment attempt already ran and
  still did not clear the gate. Name the member and point at `/s:plan <member>`
  (run from the repo root) as the manual recovery entry point — that invocation
  locates the parked worktree and runs enrichment through to the re-gate, which
  is the only path back to `ready`. When the report entry carries an enrichment
  `session_id`, also print the exact resume command for that session:
  ```
  claude --resume <session-id>
  ```
- **Parked — needs-human**: for **each** such member, print the exact resume
  command so a human can reopen the precise conversation:
  ```
  claude --resume <session-id>
  ```
- **Skipped** members with their state, and **unreached** members (cut by
  `--max-members`).

Then stop — this skill does no other work. It never edits code, never plans or
builds, and never answers a driven session on the user's behalf.

## Question rejection recovery

A known Claude Code bug can deliver an AskUserQuestion interaction as a tool
rejection ("The user doesn't want to proceed with this tool use") even when the
user tried to answer. Never treat a rejected or interrupted AskUserQuestion as a
decline or a stop. When the user's next message arrives: if it answers the
pending question, fold it in and continue; otherwise re-offer the same choices
as a plain-text numbered list and wait for a typed reply. Only an explicitly
selected or typed cancel ends the flow.
