# spec-status-statusline
Status: verified

## Why

Once a build is running, nothing tells you at a glance which spec you are
working on or how far along it is — you have to open `am/spec/changes/` and
read checkboxes. Specs also have no explicit lifecycle: "is this planned,
in-flight, done, or checked?" lives in people's heads. We want a visible
pipeline (draft → ready → active → complete → verified) stamped on each spec,
a way to explicitly select the spec being worked on, and a Claude Code
statusline that surfaces both — the way the shipd statusline surfaced OpenSpec
changes, but for the homegrown engine and with a ☢️ prefix.

## What Changes

- Every change's `proposal.md` gains a mandatory header: a `# <change-name>`
  title with a `Status: <status>` line directly below it. Statuses:
  `draft`, `ready`, `active`, `complete`, `verified`.
- A new stdlib-Python CLI, `spec_status.py`, reads and writes the Status line,
  records the currently-selected spec in repo-local `.shipd/state.json`
  (git-ignored), and derives `active`/`complete` from `tasks.md` checkboxes.
- A new bash statusline script for Claude Code's `statusLine` setting renders
  `☢️ <change> · <status> · <done>/<total>` for the selected spec.
- `spec_lint.py` validates the proposal header (title + valid Status) for
  in-flight changes.
- The plan and build skills drive the pipeline: plan emits `draft` and
  promotes to `ready` at approval; build sets `active` when execution starts,
  `complete` when all tasks are done, and `verified` when verification passes.
- The master library `am/spec/specs/` is seeded from the frozen bootstrap
  specs (one-time pre-step, already applied as part of this change).

## Capabilities

### New Capabilities
- `spec-status`: the status lifecycle — header format, stage semantics,
  pipeline transitions, and the status CLI.
- `statusline`: current-spec selection and the Claude Code statusline
  rendering/integration.

### Modified Capabilities
- `shipd-spec-lint`: gains proposal-header validation (title + Status line).
- `shipd-plan`: emission includes the proposal header with `Status: draft`;
  promotion to `ready` at approval.
- `build-spec-lifecycle`: build updates the spec status at phase boundaries
  and selects the spec it is building.

## Impact

- New: `plugins/s/skills/build/scripts/spec_status.py`,
  `plugins/s/integrations/statusline.sh`, tests for both,
  `.claude/settings.json` (statusLine registration).
- Modified: `plugins/s/skills/build/scripts/spec_lint.py` (+ its tests and
  the sample fixture), `plugins/s/skills/plan/references/emission.md`,
  `plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/build/SKILL.md`,
  `.gitignore` (ignore `.shipd/`).
- Seeded: `am/spec/specs/<capability>/spec.md` for the 10 bootstrap
  capabilities (51 requirements), lint-clean.
