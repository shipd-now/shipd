## ADDED Requirements

### Requirement: Task group satisfiability
id: task-group-satisfiability

The linter SHALL refuse a change whose `tasks.md` carries a `[P<n>]` group
configuration under which some pending task can never become claimable. It
SHALL determine this by applying the coordinator's own readiness rule —
a barrier (untagged) task becomes ready only once every task before it in
file order is done, and a grouped task only once every barrier before it is
done and every task in a strictly-lower-numbered group anywhere in the file
is done — repeatedly marking every ready pending task done until no further
task becomes ready. Any task still pending when that drain stalls SHALL be
reported as an error naming the task by its checkbox ordinal, the same
stable id the coordinator hands out. A tasks file that drains completely
SHALL produce no finding, and a change with no `tasks.md` SHALL be a no-op
for this check. The linter's readiness rule SHALL be pinned to the
coordinator's by a test that compares the two implementations' ready sets
over a corpus of tag configurations, so the authoring-time check and the
runtime claiming can never disagree.

#### Scenario: A readiness cycle is refused
- **GIVEN** a tasks file in which a `[P3]` task precedes an untagged barrier
  that itself precedes a `[P2]` task
- **WHEN** the linter runs on that change
- **THEN** it reports an error naming the tasks that can never become ready
  and exits non-zero

#### Scenario: The barrier idiom still passes
- **GIVEN** a tasks file whose untagged barrier sits between `[P1]` and
  `[P2]` tasks
- **WHEN** the linter runs
- **THEN** it reports no satisfiability finding

#### Scenario: Monotonic grouping passes
- **GIVEN** a tasks file in which every task carries a group tag and the
  group numbers never decrease down the file
- **WHEN** the linter runs
- **THEN** it reports no satisfiability finding

#### Scenario: A fully sequential file passes
- **GIVEN** a tasks file in which no task carries a group tag
- **WHEN** the linter runs
- **THEN** it reports no satisfiability finding

#### Scenario: Already-done tasks do not mask a cycle
- **GIVEN** a tasks file whose earlier tasks are marked done and whose
  remaining pending tasks form a readiness cycle
- **WHEN** the linter runs
- **THEN** it still reports the cycle, since the drain starts from the file's
  recorded box states

#### Scenario: The two readiness implementations agree
- **WHEN** the parity test runs each configuration in its corpus through both
  the linter's readiness rule and the coordinator's
- **THEN** the two report the same ready set for every configuration
