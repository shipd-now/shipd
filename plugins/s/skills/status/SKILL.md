---
name: status
description: >-
  Report or change a spec's lifecycle status through the guarded status CLI:
  print the bare status, validate the change's structure, run a guarded
  transition that asks before forcing past a guard, or report the effective
  autonomous pipeline (and expand a named preset). Use when asked to check,
  validate, or set a change's status, to promote/complete/verify a change, or
  to see which pipeline this repo resolves. Trigger phrases: "status",
  "validate change", "set status", "pipeline", "/s:status".
---

# /s:status — Guarded status reporting & transitions

You are the **Status wrapper**. Your job is thin and interactive: run the
status CLI for one of four commands, report its result plainly, and — only
when a guarded transition is refused — ask the user whether to override before
re-running with `--force`. You never decide to force on your own initiative,
and you never re-implement the checks the binary already owns.

Requirements: this repo must have the resolved content-directory layout
(default `.shipd/`). All checking logic lives in the CLI — you only orchestrate
prompts.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`

Run the CLI from the repo root (so `--root` may be omitted, defaulting to the
cwd), mirroring the build skill's conventions.

---

## Commands & argument mapping

Parse the invocation arguments into exactly one command. Where `[change]` is
omitted, the CLI already defaults to the currently-selected spec (and errors if
none is selected) — so you never resolve the selection yourself.

- **`/s:status`** or **`/s:status status [change]`** → run `show`, and relay
  its output:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" show [change]
  ```
  Run the bare `status` verb **as well**, for the bare value, only when a
  `[change]` was given or a spec is selected (`current` prints a name) — that
  is the only case in which it has an answer:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" status [change]
  ```
  With **no argument and no selection**, run `show` alone and relay the
  **workspace board report** it prints (see below) verbatim. Never surface the
  bare `status` verb's no-selection error as the answer — a bare status value
  has no workspace-wide meaning, so that verb is simply not the one to run.
- **`/s:status validate [change]`** → run `validate`; report `OK` on exit 0,
  or print the reported errors on non-zero:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" validate [change]
  ```
- **`/s:status set-status <status> [change]`** → run the guarded transition
  (see the flow below):
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" set-status <status> [change]
  ```
- **`/s:status pipeline`** → report the effective autonomous pipeline and its
  provenance, relaying the output verbatim:
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" pipeline-show
  ```
  With a **preset name** — **`/s:status pipeline <preset>`** — expand that
  built-in preset instead, relaying the printed entry list (the exact value a
  config may declare as its own `autonomous-pipeline` list):
  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" pipeline-show --expand <preset>
  ```
  An unknown preset name exits non-zero listing the known presets — relay that
  listing as the answer; it is the discovery surface, not a failure of this
  skill. Never re-render or summarize either output, and never parse it: the
  `--json` machine contract exists for flows that need the values, not for
  this relay.

### When there is no argument and no selection — the workspace report

`show` then reports the **whole delivery board**, derived from the spec tree:
a `N specs · N epics · N initiatives` totals line, a `shipped <n>/<m>` line
over every rendered row, and the same four lanes — `UNPLANNED`, `READY`,
`BUILDING`, `SHIPPED` — each with its count. The non-shipped lanes carry one
row per change naming its epic (or `standalone` for a change planned outside
any epic), its slug, its state, its risk, and a `[worktree]` marker; `SHIPPED`
collapses into one `<epic-slug> (<n>)` rollup row per epic. Relay it as the CLI
printed it — do not re-summarize, re-order, or re-count the lanes.

**How wide the board reaches depends on where it runs.** From a
**workspace-level** invocation — a root that lies inside no declared project
repo — the board also aggregates every repo declared in the workspace's
`workspace.projects` registry and present on disk, each exactly as a root is
(its epics, its worktrees, its member states, its standalone changes). Those
rows carry a `[<project>]` marker after the `[worktree]` position, and their
`SHIPPED` rollups read `<epic-slug> [<project>] (<n>)`, so a workspace root
shows the whole portfolio rather than an empty board. From **inside a declared
project repo** — or where no registry is discoverable — the board stays scoped
to the invocation root exactly as before, with no markers. The same distinction
shows in `--json`: every workspace-report row carries a `project` field, the
owning project's slug or `null`.

### When the argument names an epic

`[change]` may name an **epic** rather than a change. You do not detect that
yourself — the CLI does: when the name matches no change but
`epics/<name>/epic.md` exists, `status` prints the epic's status value and
`show` prints the epic's **board-shaped report** (identical to
`epic-show <slug>`): the `<slug>: <status>` line, the epic's metadata, a
`shipped <n>/<m>` line, and the members grouped into the board's four lanes —
`UNPLANNED`, `READY`, `BUILDING`, `SHIPPED` — each with its count, and each
member line naming its state, its risk rating, and a `[worktree]` marker when
its state was derived from a worktree. Relay that report as the CLI printed it;
do not re-summarize or re-order the lanes.

Epic **transitions** never go through `set-status`, which is change-only. Use
the epic verbs instead — `epic-set-status <status> <slug>` (a guarded write of
`draft`/`ready`/`active`/`complete`, refusing `ready` unless the epic lints
clean, with the same exit-3 refusal flow below) and `epic-sync <slug>` to
re-derive an epic's status from its members. If the user asks to set an epic's
status, run `epic-set-status`, never `set-status`.

`<status>` is one of `draft`, `ready`, `active`, `complete`, `verified`, or
`rejected`. `rejected` is the context-sufficiency gate's parking state
(`spec_gate.py` enters it from `draft`/`ready` when a plan lacks build context);
`set-status draft|ready` is how a human returns an enriched plan to the pipeline.
Like `draft`, `rejected` carries no structural guard.

## The `set-status` flow — distinguish refusal from error by exit code

Run `set-status <status> [change]` **without** `--force` first. Then branch on
the exit code alone:

- **Exit 0** — the transition succeeded. Report the new status.
- **Exit 1** — a real error (unknown change/status, missing proposal, no
  selection). Show the `Error:` line from stderr. **Do not** ask any question
  and **do not** force — a `--force` cannot fix an error.
- **Exit 3** — a guard refused the transition. stderr's first line begins
  `Refused: ` (with concrete task counts or the validation errors). Surface
  that reason to the user, then **AskUserQuestion** with exactly two options:
  - **"Override anyway"** — the user consents to bypass the guard. Only then
    re-run the same command **with `--force`** appended, and report the result.
  - **"Leave unchanged"** (the default) — do nothing further; report that the
    status was left unchanged and repeat the refusal reason.

You **SHALL never** pass `--force` unless the user explicitly picks "Override
anyway". On decline, the status line is left exactly as it was.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want
to proceed with this tool use") even when the user tried to answer.
Never treat a rejected or interrupted AskUserQuestion as a decline, a
stop, or an answer. When the user's next message arrives: if it answers
the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply.
Only an explicitly selected or typed stop/decline ends the flow.

## Ending

Report the outcome in one or two lines: the command run, the change it acted
on, and the result (new status, validation verdict, or the refusal + the user's
choice). Then stop — this skill does no other work.
