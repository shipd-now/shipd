# plan-brief-hardening
Status: verified

## Idea

Two live `/s:plan` sessions in a row violated the specced `context-brief`
requirement: investigation ran, and then the AskUserQuestion dialog appeared
with no findings report, no context brief, and — despite the user's request
explicitly asking for one — no diagram. The second run also skipped the
depth-gate announcement. Separately, the first run discovered the target repo
had no `am/` layout and simply carried on planning toward an emission that had
nowhere to land.

The `context-brief` requirement already exists in `am/verified/shipd-plan/spec.md`
and the behavior is described in the skill — but only inside contract sections
and reference files loaded mid-flight, not in the numbered flow the planner
actually follows, and with nothing marking the brief as a precondition of the
question call. This change hardens the skill text so the specced behavior
survives contact with a real session:

- A mandatory, user-visible **investigation findings digest** as its own
  numbered flow step, before the depth-gate verdict and before any question.
- The **context brief as a hard precondition** of every decision-resolving
  AskUserQuestion call, stated where the call is specified: a question whose
  turn did not first present the visible brief is a protocol violation.
- An **explicit-request override for visuals**: when the user's request asks
  for a diagram, that request satisfies the carries-a-decision bar by itself
  and the solution diagram appears no later than the first context brief.
- A **missing-layout guard**: when the repo lacks the `am/` layout, the skill
  stops and asks whether to scaffold the minimal layout or abort — it never
  continues as though the layout existed.

### Non-goals

- No engine or CLI changes: the fix is entirely skill/reference prose; no
  script under `plugins/s/skills/build/scripts/` changes, so no new tests.
- No repo-init verb or README template shipping: the layout guard scaffolds
  only the three empty directories; a full bootstrap capability (format
  README, config) stays future work.
- No change to the depth-gate signals, the grill-loop protocol, the readiness
  checklist, or emission.
- No relaxation of the decorative-visual prohibition beyond the explicit
  user-request override.

Affected capabilities: `shipd-plan` (modified — `context-brief`,
`visualization-on-demand`; added — `investigation-findings-digest`,
`missing-layout-guard`). Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/plan/references/dialogue.md`,
`plugins/s/skills/plan/references/visualization.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **The digest is a numbered flow step, not contract prose.** SKILL.md's Flow
  gains a step between investigation and the depth gate: print a short
  user-visible findings digest (affected files/capabilities, relevant existing
  behavior and patterns, anything surprising) as plain response text.
  Rationale: both failing sessions followed the numbered flow faithfully and
  skipped everything that lived outside it — behavior that must happen belongs
  in the flow. Rejected: leaving the digest implied by the brief contract;
  that is the arrangement that just failed twice.
- **Precondition phrasing at the call sites.** Both the fast-path question
  contract (SKILL.md) and the depth-path round protocol (dialogue.md) state
  that the visible brief is a precondition of the AskUserQuestion call — a
  call without it is a protocol violation — and that the brief must be
  user-visible response text, never only internal reasoning. The existing
  brief content (accumulated understanding, decision-carrying diagram, open
  decisions) is unchanged.
- **Override lives in visualization.md's prohibition paragraph.** The
  prohibition gains its one exception in place: an explicit user request for a
  diagram/visual satisfies the carries-a-decision bar by itself, and the
  requested solution diagram appears no later than the first context brief
  (in the digest when no questions are needed). SKILL.md's visualization
  pointer names the override so it is visible before the reference loads.
- **Layout guard at the top of the flow.** SKILL.md's requirements line grows
  a defined miss behavior: when the `am/` layout is absent, report it, and ask
  one AskUserQuestion — scaffold the minimal layout (`am/verified/`,
  `am/planned/`, `am/completed/`) and continue (recommended), or stop. Never
  proceed implicitly. Rejected: silent auto-scaffold (creates directories the
  user may not want in a repo that was opened by mistake).
- **Version bump to 0.2.10** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md.

Risks: prompt hardening is empirical — the next session is the real test; the
mitigations are precondition phrasing at the exact call sites and flow-step
placement, the two strongest levers available in skill text. A stale plugin
snapshot keeps sessions on the old skill — guarded by the version bump plus
the `claude plugin update` convention.
