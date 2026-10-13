# epic-grill-amend-recheck
Status: verified
Theme: reliability

## Idea

Make `/s:epic-grill` re-check the plans an overturned default touched before
it gates them, and have each planner record which earlier defaults it built
on so that re-check knows where to look.

### Motivation

Someone grilling an epic who overturns a planner default in the final round
gets every member gated even when later plans still build on the rejected
default. They cannot trust that a gated epic's plans agree with each other
after they answer.

### Details

- A `PLANNER` ledger entry may carry `**Relied on by:**`, naming the later
  members whose plans built on its default. The later member's planner
  writes it onto the earlier member's installed `plan.md`.
- After amending, when any answer overturned a default, the grill re-runs
  the consistency pass on the affected members before gating.
- Surfaces: the skill, its harness body, the plan emission guide, the
  `.shipd/README.md` ledger grammar, the contract test, the plugin version.

Affected capabilities: `shipd-epic-grill` and `shipd-spec-format`
(modified).

### Non-goals

- No engine, linter, or gate code change; the linter already accepts an
  extra ledger field.
- No change to `/s:plan`, `/s:autopilot`, or the final round's shape.
- No re-check when every default is accepted.

## Implementation

- **Who writes the field.** The later planner writes its own slug into the
  earlier entry's `**Relied on by:**` (user, Q1). It knows what it built on;
  the plan on disk stays the record. The grill re-lints every earlier member
  after each planner, so a damaged edit stops the run. Rejected: the grill
  judging reliance afterwards (misses what it cannot see); copying from the
  `DEFERRED:` report (breaks grading from disk).
- **Field placement.** `- **Relied on by:** <slug>, <slug>` is the entry's
  last field, comma-separated, only on `PLANNER` entries, and kept when the
  entry is rewritten to `USER`.
- **Re-check trigger and scope.** Runs only when at least one answer chose a
  non-default option. It covers each overturned entry's own member plus every
  member its `**Relied on by:**` names; an overturned entry without the field
  (a draft from an older grill) widens the re-check to every selected member.
- **Re-check outcome.** Repository-settled mismatches are fixed in place and
  re-linted, as in the first pass. A conflict only a human can settle is
  asked in one further dialog before gating, matching the gate's exit-2 rule.
- **Planner instruction addition**, appended after the `**Queued:**`
  sentence of the verbatim block in `plugins/s/skills/epic-grill/SKILL.md`:

  ```
  Where your plan builds on a PLANNER default in an earlier member's
  ledger, append your slug to that entry's `**Relied on by:**` field
  (adding the field as the entry's last line if absent) in the earlier
  member's installed plan.md. Edit nothing else in another member's plan.
  ```
- **Harness body.** Same rules in steps 3, 4, and 6 of
  `plugins/s/harness/bodies/epic-grill.md`, in-session wording, without the
  tokens `subagent`, `sub-agent`, or `AskUserQuestion`.

Risk: a planner may miss a reliance it had. The full-pass fallback covers
only entries with no field, so the consistency pass's own reading remains
the backstop.

## Questions and answers

### Q1: Who writes the Relied on by field?
- **Question:** The later member's planner writes it onto the earlier
  member's plan, the grill judges it during the consistency pass, or the
  grill copies it from the planner's `DEFERRED:` report? Recommendation: the
  later planner.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** The later member's planner writes it directly onto the earlier
  member's installed `plan.md`; the grill re-lints the edited member.
- **Queued:** q-epic-grill-relied-on-by-writer

## Readiness attestation

### Problem and motivation

An overturned default can leave later plans contradicting it, and nothing
re-checks them before the gate.

Evidence:

- `plugins/s/skills/epic-grill/SKILL.md:160-182` amends, then gates, with no
  second consistency pass.
- Requirement `epic-grill-amend-gate` (`shipd-epic-grill`) names no re-check.

### Scope and non-goals

The grill's prose contract and the ledger grammar; no engine code.

Evidence:

- `plugins/s/skills/build/scripts/spec_lint.py:133` requires only three
  ledger fields, so an extra field needs no linter change.

### Affected capabilities and files

Two capabilities and six files change.

Evidence:

- `shipd-epic-grill`: `epic-grill-planner-contract` (base 9b685c44dab5),
  `epic-grill-amend-gate` (base e1feaf440283); `shipd-spec-format`:
  `plan-document-sections` (base 56440706848a), from `spec_status.py
  base-hash`.
- Files: `plugins/s/skills/epic-grill/SKILL.md:70-100,109-182`,
  `plugins/s/harness/bodies/epic-grill.md:28-56`,
  `plugins/s/skills/plan/references/emission.md:229-240`,
  `.shipd/README.md:186-195`,
  `plugins/s/skills/build/tests/test_epic_grill_contract.py`,
  `plugins/s/.claude-plugin/plugin.json` (0.6.282).
- Runnable premise: `spec_lint.py` on a probe change whose `PLANNER` entry
  carried `**Relied on by:**` reported the same single unrelated finding as
  without the field, so the field adds no lint error.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Field writer: settled by the user, Q1.
- Re-check trigger, scope, fallback, and follow-up dialog: settled by
  investigation of the existing consistency pass and gate exit-2 rule in
  `plugins/s/skills/epic-grill/SKILL.md`.
- Personal memory store: absent, so no preference applied.
