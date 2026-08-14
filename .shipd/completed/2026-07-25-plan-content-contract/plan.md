# plan-content-contract
Status: verified

## Idea

**Why.** The lean-format cutover collapsed proposal+design into `plan.md` but
thinned the content contract to two one-line clauses, and an audit against the
SDD research ("Lean SDD Spec Recommendations") shows what fell out: the *why*
has no reserved leading slot (recent plans open with the what), scope
**non-goals** are required by the readiness gate but never written down, the
design-side element menu (files, interfaces, data shapes, ADR-style decisions)
vanished, and two workflow disciplines — a self-review pass before lint, and
failing-test-before-implementation task ordering — were never carried over.
Content quality currently rides on author habit instead of the format.

**What.** Restore the missing pieces as an explicit content contract:

- `## Idea` gets a fixed element order — it opens with the **why** (problem
  and motivation), then the concrete changes, then a `### Non-goals`
  subsection (scope exclusions, now lint-enforced), then affected
  capabilities and impact.
- "Goals" is deliberately not a section anywhere: the Idea *is* the goals,
  and the how-level negative space lives in Implementation's per-decision
  rejected alternatives — eliminating the goals/implementation duplication.
- `## Implementation` gains a "look for these decision kinds" menu in the
  emission guide (files/components touched; interfaces and data shapes when
  relevant; each decision ADR-style with rationale and rejected alternative;
  risks).
- The plan flow gains a self-review step (placeholders, contradictions,
  unresolved decisions) before the lint gate.
- Task discipline gains TDD ordering: where a task has a testable surface,
  the failing-test task precedes the implementation task.

### Non-goals

- No new top-level sections — `## Idea` and `## Implementation` remain the
  only required level-2 headers; Non-goals is a level-3 element inside Idea.
- No EARS lint enforcement, no change to the delta grammar or merge engine.
- No rewriting of archived plans in `am/completed/` (immutable).
- No constitution changes.

Affected capabilities (modified): `shipd-spec-format` (plan section contract),
`shipd-spec-lint` (non-goals check), `shipd-plan` (self-review + task ordering).
Impact: `plugins/s/skills/plan/references/emission.md`,
`plugins/s/skills/plan/SKILL.md`, `am/README.md`,
`plugins/s/skills/build/scripts/spec_lint.py`, its tests and the sample
fixture, and a plugin bump to 0.1.4.

## Implementation

- **Non-goals is lint-enforced as `### Non-goals`.** A bolded inline label
  would be cheaper but ungreppable and easy to skip; a level-3 heading inside
  Idea is machine-checkable without adding a required level-2 section. Lint
  errors when `plan.md` has no `### Non-goals` heading. Rejected: making it
  advisory — the readiness gate already proves advisory scope-bounding
  doesn't reach the page.
- **The why-leads rule is contract, not lint.** Lint cannot judge whether
  prose opens with a problem statement; the requirement text and emission
  guide fix the element *order*, and the self-review step is the enforcement
  point. Rejected: a lint heuristic (first paragraph must precede any list) —
  brittle, false positives.
- **Element menus are guidance in `emission.md` only** — the master spec
  states the required elements; the "decision kinds to look for" list would
  rot if duplicated into `am/README.md`. `am/README.md` gets the element
  order one-liner only.
- **Self-review lands in the plan SKILL.md flow** as a named step between
  emission and lint (re-read artifacts for placeholders, contradictions,
  decisions left to the executor), and as an ADDED `shipd-plan` requirement so
  it survives future skill rewrites.
- **TDD ordering amends the existing task-discipline requirement**
  (`silent-lean-emission`) rather than adding a new one — it is a property of
  the emitted task list, same as smallness and file-naming. Applies "where a
  task has a testable surface": docs-only tasks are exempt.
- **Self-hosting:** this change's own `plan.md` is authored to the new
  contract, since the new lint check gates its own completion statuses.
- Risk: the non-goals check makes older un-archived plans invalid — none are
  in flight, so the flip is safe; fixtures are updated in the same change.
