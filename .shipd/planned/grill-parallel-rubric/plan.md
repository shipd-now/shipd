# grill-parallel-rubric
Status: ready
Theme: developer-experience

## Idea

Let `/s:epic-grill` plan independent epic members concurrently, in waves
computed from dependencies the epic declares, instead of one at a time.

### Motivation

Anyone grilling a multi-member epic waits through one planner run per member
because the grill has no dependency facts to parallelise on; the `pr-room`
grill had to be hand-parallelised and its couplings surfaced only in the
consistency pass.

### Details

- An optional seventh `After` column on the epic `## Changes` stub table
  holds comma-separated sibling slugs a member must be planned after.
- `spec_common.parse_epic_changes` keeps its three-tuple shape (ratings
  truncated to the four rating cells) and gains `parse_epic_after(text)`.
- The linter accepts six columns or six plus `After`, validating every
  `After` slug names another row.
- `autopilot.py --waves` computes plan waves as dependency layers when the
  column is present; build waves are untouched.
- `/s:epic-grill` reads those waves and spawns one planner per member of a
  wave concurrently; with no column it stays serial.
- `/s:epic` authors the column for new epics.

Research: `.shipd/research/parallel-planning-rubric/report.md` — a summed
parallelizability score is the wrong tool; declared yes/no dependency facts
plus deterministic DSM-style partitioning is the recommended hybrid.

Affected capabilities: `shipd-spec-format`, `shipd-spec-lint`,
`epic-autopilot`, `shipd-epic-grill`, `shipd-epic` (all modified). Files:
`plugins/s/skills/build/scripts/{spec_common,spec_lint,autopilot}.py`,
`plugins/s/skills/{epic-grill,epic}/SKILL.md`,
`plugins/s/harness/bodies/{epic-grill,epic}.md`, four test files, and
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No scored or weighted parallelizability rubric; no per-member score.
- No change to build-wave scheduling (capability disjointness stays).
- No edit to existing epics; a table without `After` behaves as today.
- No change to `spec_gate.py`'s directory rule.
- No new config key; the wave cap is `--parallel` (default 3) as today.

## Implementation

- **Column grammar.** Header is `EPIC_CHANGES_COLUMNS` optionally followed
  by `After` (`EPIC_AFTER_COLUMN = "After"` in `spec_common.py`). An `After`
  cell is empty or a comma-separated list of kebab-case slugs; whitespace
  around commas is ignored. Rejected: a `## Dependencies` section — a second
  parser and a second protected region for one fact per row.
- **Parser.** `parse_epic_changes` slices ratings to
  `cells[2:2 + len(EPIC_CHANGES_COLUMNS) - 2]` so every `ratings[-1]`
  consumer (`spec_status.py:1943`, `:2077`, `dashboard.py:999`,
  `autopilot.py:131`) still reads Risk. New `parse_epic_after(text)` returns
  `{slug: [after, ...]}` for every data row (empty lists when the column is
  absent).
- **Lint.** `_check_epic_changes` accepts either header; with `After` it
  errors on a slug that is not kebab-case, names no other row, or names the
  row itself. Cycles are not a lint error — waves serialise them.
- **Plan waves (`compute_waves`).** When `parse_epic_after` yields any
  non-empty list: edges run from each unplanned member to its `After` slugs
  that are themselves unplanned (a planned, ready, or shipped dependency is
  satisfied). Layers come from Kahn's algorithm; within a layer members sort
  by risk ascending then table order and are chunked to `parallel`. Members
  left when no in-degree-zero node remains (a cycle) each form a wave of one
  in table order after every acyclic layer. Each wave member entry gains
  `"after": [...]`. With no non-empty `After`, today's risk chunks stand so
  the in-session autopilot is unchanged. Rejected: LLM-judged dependency
  order — not deterministic and not checkable.
- **Grill.** Preflight runs
  `autopilot.py <epic> --waves --parallel N --json` (N from an optional
  `--parallel N` argument, default 3) only when the table carries `After`
  with at least one non-empty cell; it prints each plan wave with the
  `after` reasons, then spawns one general-purpose sub-agent per member of
  a wave in a single message, each briefed with every root from earlier
  waves, waits for the whole wave, grades each member from disk, and re-lints
  every earlier member before the next wave. A wave of one is the serial
  path. With no `After` the grill plans one at a time exactly as before (Q2).
- **Epic authoring.** `/s:epic` emits the `After` column on every new epic,
  filling it from the Design's seams; an empty cell means no dependency.
  `epic-amend-check` already protects `## Changes`, so the column cannot
  drift by amendment.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` one patch above
  `main`'s value at build time.

Risk: a planner briefed with stale sibling plans when a wave's members are
read before an earlier wave re-lints; guarded by grading and re-linting
before the next wave starts.

## Questions and answers

### Q1: Where do planning dependencies live?
- **Question:** Options: (1) optional `After` column in the `## Changes`
  stub table; (2) a `## Dependencies` epic section; (3) no epic change, the
  grill judges from prose. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — the `After` column, scoped to planning order; build
  waves stay capability-derived, so `q-autopilot-parallel-member-scheduling`
  is not reversed.
- **Queued:** q-epic-member-planning-dependency-declaration

### Q2: What does the grill do with no `After` column?
- **Question:** Options: (1) stay serial as today; (2) treat every member as
  independent; (3) refuse until the column is added. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1 — serial; parallel waves require declared
  dependencies, never assumed independence.
- **Queued:** q-epic-grill-missing-after-column-waves

## Readiness attestation

### Problem and motivation

The grill plans members one at a time because nothing declares dependencies.

Evidence:

- `shipd-epic-grill#epic-grill-planner-contract` mandates "one at a time".
- `autopilot.py:197-201` chunks plan waves by risk with no dependency input.

### Scope and non-goals

The change adds one optional column and the code that reads it; build waves,
existing epics, and the gate stay untouched.

Evidence:

- In scope: `spec_common.py:106-107`, `spec_lint.py:590-627`,
  `autopilot.py:174-230`, `skills/epic-grill/SKILL.md:58-116`.
- Out of scope: `autopilot.py:203-216` (build waves) is not edited.

### Affected capabilities and files

Six requirements across five capabilities and eight source or skill files.

Evidence:

- `shipd-spec-format#epic-artifact-layout` (base b29b8c90ab0a),
  `shipd-spec-lint#epic-structural-validation` (base c2e05edc9421),
  `epic-autopilot#member-wave-scheduling` (base efbd24b07b92),
  `shipd-epic-grill#epic-grill-preflight-order` (base 25382aaf45ec),
  `shipd-epic-grill#epic-grill-planner-contract` (base 8b7da10bb91b),
  `shipd-epic#epic-interview-skill` (base 10e7c82022e6), all from
  `spec_status.py base-hash`.
- Runnable premise: `autopilot.py pr-room --waves --parallel 3 --json` →
  exit 0, two plan waves `[room-schema, room-skill, room-cli-verb]` and
  `[room-watch, room-action-wake, room-gate-adoption]` — risk order, no
  dependency.
- Runnable premise: `spec_lint.py --epic pr-room` → exit 0 with the
  six-column table.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Dependency location: user, Q1. No-column fallback: user, Q2.
- Rubric versus matrix: the research report's recommendation.
- Column parsing, lint rules, wave algorithm, grill wave loop: investigation
  of the files cited above.
