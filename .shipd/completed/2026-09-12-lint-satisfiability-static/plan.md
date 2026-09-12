# lint-satisfiability-static
Status: verified
Theme: reliability

## Idea

Make the linter's task-group satisfiability check read the tag configuration
alone, so a build in progress stops reporting a structural error that is not
there.

### Motivation

`check_task_satisfiability` drains from the tasks file's current checkbox
states, and its drain only ever advances pending tasks — so an in-progress
`[~]` claim blocks every barrier after it and the linter reports a task that
"can never become ready" while the build that claimed it is running normally.

### Details

- Normalize every task state to pending before the drain, so the check
  answers a question about the `[P<n>]` configuration rather than about how
  far the build has got.
- Keep `ready_task_ordinals` untouched: it mirrors the coordinator's runtime
  rule and is pinned to it by an existing test.

Affected capabilities: `shipd-spec-lint` (modified). Impact:
`plugins/s/skills/build/scripts/spec_lint.py` and a test under
`plugins/s/skills/build/tests/`. No new dependencies; the engine stays
stdlib-only.

### Non-goals

- No change to the coordinator's readiness rule, to `ready_task_ordinals`, or
  to the existing test that pins the two implementations together.
- No change to which configurations count as broken — only to whether
  progress through a sound configuration can fake a broken one.
- No new lint finding, flag, or severity level.

## Implementation

- **Normalize to all-pending before draining.** In `check_task_satisfiability`,
  build the working list as `[(" ", group) for _state, group in states]`
  before the fixpoint loop. The drain then reports exactly the tasks whose
  group configuration makes them unreachable from a fresh start.

  Rejected: mapping only `"~"` to pending and leaving `"x"` done. It fixes the
  reported symptom but keeps the check progress-dependent — a fully completed
  tasks file whose configuration is broken would report nothing at all,
  because no task is pending to report. Normalizing everything makes the
  finding independent of when the linter runs, which is the property the
  check needs.

  Verified premise: draining the four state shapes through the current
  `ready_task_ordinals` gives `all pending -> stuck: none`,
  `one in progress -> stuck: [3]`, `all done -> stuck: none`,
  `genuinely broken config -> stuck: [1, 2, 3]` — the same `[P1]`/`[P2]`/
  barrier configuration reported as sound at emit time and broken mid-build.

- **`ready_task_ordinals` is deliberately not touched.** It encodes the
  coordinator's own readiness rule, which is genuinely state-dependent — a
  claimed task is not available to another worker. The defect is in what
  `check_task_satisfiability` feeds it, not in the rule.

Risk: a tasks file whose configuration is broken only for the tasks already
completed now reports a finding it previously stayed silent about. That is
the intended strengthening, and such a file is malformed either way.
