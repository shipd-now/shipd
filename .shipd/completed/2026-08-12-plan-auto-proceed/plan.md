# plan-auto-proceed
Status: verified
Theme: developer-experience

## Idea

Replace `am:plan`'s mandatory go-ahead confirmation with an evidenced readiness
attestation and a deterministic gate promotion, so a plan that already has
enough context emits without asking the user for permission.

### Motivation

`am:plan` hands the turn back for "We have enough details — shall I write the
plan now?" even when investigation left nothing open, costing a round-trip on
every plan. Meanwhile the repository's one deterministic context-sufficiency
check, `spec_gate.py`, is never run on a fresh plan — the flow ends with a bare
`spec_status.py set-status ready`.

### Details

- Drop the go-ahead question. A digest whose readiness attestation holds
  continues in the same turn through the depth gate to emission.
- Add an **evidenced readiness attestation**: each of the four checklist items
  is discharged with a concrete citation (capability, `file:line`, requirement
  id) printed before emission; an uncitable item is unmet and blocks.
- Pull the ask-mikk rung into the investigation turn, so open questions are
  consulted and the `INSUFFICIENT` remainder is asked once, in that same turn.
- Promote through `spec_gate.py` instead of `set-status ready`, so hand-off is
  gated on the deterministic context checks; a rejection enters the skill's
  existing enrichment loop.

Affected capabilities: `shipd-plan` (modified). Impact: the plan skill's
`SKILL.md` and its `references/readiness.md`, the plugin manifest's version,
and the eval runner's stale checkpoint comment. No engine script changes and
no new dependencies.

### Non-goals

- No change to `spec_gate.py`, `spec_emit.py`, `spec_status.py`, or any other
  engine script — the gate's four context checks are used exactly as they are.
- The depth path's shared-understanding confirmation is **retained**; only a
  depth path whose grill agenda is empty skips it.
- Enrichment mode (rejected-change recovery) keeps its current flow.
- No new lint rules and no new gate checks.

## Implementation

- **Files touched.** The plan skill's `SKILL.md` (flow steps 2–5, the ask-mikk
  rung, the Ending section) and its `references/readiness.md` (the
  attestation); the plugin manifest (0.6.76 → 0.6.77); and `evals/run.py`,
  whose `GOAHEAD_REPLY` comment still describes a checkpoint that no longer
  fires.

- **Confidence comes from evidence plus an exit code, not from a question.**
  The removed confirmation is replaced by two checks the skill cannot fake: a
  printed per-item citation before emission, and `spec_gate.py`'s exit code
  after installation. Rejected: adding a new heuristic self-score — the gate
  already encodes the repository's definition of sufficient context (stale
  `base:` hashes, placeholder markers, dangling `tasks.md` paths, deltas
  against missing capabilities) and is model-free and network-free.

- **`spec_gate.py` replaces `set-status ready` on the fresh-plan path.** The
  gate promotes `draft` → `ready` itself on exit 0, so the swap is behavior-
  preserving on the happy path and strictly stronger otherwise. On exit 2 the
  change sits at `rejected` carrying a `## Context insufficient` section, which
  is exactly the agenda the skill's enrichment loop already consumes — so the
  failure path needs no new machinery. Rejected: running the gate on the
  staging directory before install — the gate resolves a change under
  `planned/`, and pre-install gating would duplicate `spec_emit.py`'s own lint.

- **The oracle rung moves into the investigation turn.** With the go-ahead gone
  there is no post-gate turn boundary to defer it to, and deferring would cost
  the user an extra interruption for decisions the wiki can already settle. The
  `OPEN QUESTIONS` header survives as the digest's naming of what is open; the
  turn now ends on the typed round for the `INSUFFICIENT` remainder instead of
  on the bare list. AskUserQuestion is still never issued in that turn, so
  `shipd-interaction`'s dialog/prose separation is untouched.

- **Stops are enumerated, not implied.** SKILL.md gains an explicit list of the
  conditions that still end a turn — missing content-directory layout, the
  depth path's grill loop, an `INSUFFICIENT` oracle verdict, an uncitable
  readiness item, and a gate rejection whose finding is a true gap. Anything
  not on that list proceeds.

- Risk: the model asserts readiness it does not have, now that no human
  confirms it. Guarded on both sides — the citation requirement makes an
  unfounded item visible in the transcript before emission, and the gate
  refuses the promotion afterwards. Residual risk is a plan that is
  gate-clean but semantically wrong, which the go-ahead question did not
  reliably catch either.

- Risk: the eval harness resumes sessions with a generic go-ahead reply
  (`evals/run.py`), which will now go unused on clean runs. That degrades
  safely — fewer resumed turns, not failures — but the run is the regression
  check for this change, so it is a task.
