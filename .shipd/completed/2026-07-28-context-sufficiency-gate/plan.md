# context-sufficiency-gate
Status: verified
Epic: autonomous-delivery

## Idea

The autonomous pipeline has no automated way to decide whether a freshly
planned member has enough context to build against the codebase, and no
status that means "bounced for insufficient context". Today a plan goes
`draft → ready` on the planner's own say-so, and a context-starved plan
would sail into an unattended build and force the executor to guess — the
exact failure the epic forbids.

This change delivers the gate and the parking state:

- A deterministic, stdlib `spec_gate.py <change>` verb: structural lint
  plus context checks the linter doesn't do — stale `base:` hashes against
  current masters, placeholder markers, task file-references that resolve
  nowhere, delta operations targeting nonexistent capabilities.
- Pass → any `## Context insufficient` section is removed and the plan is
  promoted `draft → ready`. Fail → status becomes the new `rejected` and
  the findings are written into `plan.md` itself as a `## Context
  insufficient` section at the very top, before `## Idea` — impossible for
  the enriching engineer/PM to miss, gone again once context suffices.
- `rejected` joins the lifecycle everywhere: `STATUSES`, guards (targeting
  it requires nothing), `sync` never touches it, lint accepts it, the
  statusline renders it, docs list it.

### Non-goals

- No LLM judgment pass — the gate is deterministic and CI-safe; the
  autopilot member layers model-driven judgment later.
- No forced exit-via-gate: a human may `set-status draft|ready` after
  enrichment without re-gating (re-gating is encouraged, never required).
- No epic- or initiative-level gating; the gate targets member/standalone
  change plans only.
- No changes to the epic statuses (`rejected` is change-level only).

Affected capabilities: `context-gate` (added); modified: `spec-status`,
`shipd-spec-lint`, `shipd-spec-format`. Impact:
`plugins/s/skills/build/scripts/spec_gate.py` (new), `spec_status.py`,
`spec_lint.py`, `statusline.sh`, their tests, `README.md`, `.shipd/README.md`,
`docs/onboarding/02-artifacts.md`, plugin version bump.

## Implementation

- **Gate = lint + four context checks.** (1) Stale base: every
  `base:` hash on MODIFIED/REMOVED entries must equal the current master's
  content hash (`spec_common.content_hash`). (2) Placeholders: `TBD`,
  `TODO`, `FIXME`, `XXX`, `???`, `OPEN QUESTION` (case-insensitive, word
  boundaries) anywhere in plan.md, deltas, or tasks.md. (3) Task file
  references: backticked tokens in tasks.md containing `/` and shaped like
  paths must exist, or their parent directory must exist (the new-file
  case) — bounded deliberately to path-shaped tokens to avoid false
  positives. (4) Delta targets: MODIFIED/REMOVED/RENAMED operations require
  the target capability master to exist; ADDED-only new capabilities pass.
  Rejected: an LLM pass (spend + nondeterminism in an engine verb).
- **Exit codes.** 0 = pass (promoted to `ready`), 2 = rejected (findings
  written, status set), 1 = general error. Distinct from `set-status`'s
  refusal code 3, which the gate never uses.
- **Ephemeral in-plan report.** On fail the gate inserts/replaces
  `## Context insufficient` directly after the header metadata block and
  before `## Idea`: one paragraph summarizing what is missing, then
  dot-points per finding. On pass it removes the section entirely. Writes
  are metadata-preserving (title, `Status:`, `Epic:` lines untouched).
  Rejected: a separate gate-report.md — separable from the plan, easy to
  ignore; the in-plan section confronts the enricher where they work.
- **`rejected` semantics.** Sixth status. Entered by the gate from `draft`
  or `ready`; `set-status rejected` carries no structural guard (a
  rejected plan may be broken — that is the point); `sync` never changes
  `draft`, `verified`, or `rejected`; exit is human `set-status
  draft|ready` (normal guards apply). Statusline renders it in red
  (`\033[31m`).
- **Section legality.** `plan-document-sections` gains the gate-owned
  optional `## Context insufficient` section, permitted only before
  `## Idea`; lint tolerates its presence in any status (a force-promoted
  plan may still carry it — human-visible, gate-removable).
- **Script layout.** `spec_gate.py` is a sibling engine script importing
  `spec_common` and `spec_lint`'s check functions in-process (the
  spec_emit.py precedent); status writes go through `spec_status`'s
  metadata-preserving writer, not ad-hoc file edits.

Risk: file-reference false positives rejecting good plans — guarded by the
path-shape bound, the parent-dir rule, and tests over real task phrasing
from this repo's archived changes; worst case is a human glance at an
over-cautious report, never a lost plan.
