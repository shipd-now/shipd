## MODIFIED Requirements

### Requirement: Planned-change review bridge
id: change-bridge
base: 8bf1fc0f7172

The system SHALL provide `semdiff change <name>` aggregating a shipd change's
review context as one JSON object: the change status, per-delta entries
(operation, capability, requirement id and text, scenario texts), task
checkbox states with progress counts, the change's lint findings, and
best-effort impact files extracted from `plan.md`. It SHALL resolve the
content directory through the engine's layered configuration and reuse the
engine's parser in-process.

The verb SHALL resolve the change directory as `planned/<name>/` when that
directory exists and otherwise as the newest `completed/<date>-<name>/`
archive, the same order the status CLI's `cat change` uses, and SHALL report
the pick in two top-level JSON keys: `location` (`planned` or `completed`)
and `dir` (the change directory relative to the repo root). While the change
resolves to an archive, the verb SHALL NOT run the change linter and SHALL
report `lint.findings` as an empty list beside a `lint.skipped` sentence
stating why. If the change exists under neither directory, then the verb
SHALL exit non-zero with a message naming the change and both directories.

#### Scenario: Aggregated change context
- **WHEN** `semdiff change my-change` runs against a lint-clean planned
  change with two delta requirements and three tasks, one checked
- **THEN** the JSON lists both requirements with their scenarios, reports
  task progress 1 of 3 with no lint findings, and carries `location`
  `planned` with no `lint.skipped` key

#### Scenario: Archived change resolves
- **WHEN** `semdiff change my-change` runs and `planned/my-change/` is absent
  while `completed/2026-01-01-my-change/` holds the archived change
- **THEN** it exits zero, carries `location` `completed` and a `dir` ending
  in `completed/2026-01-01-my-change`, lists the archive's delta scenarios
  and task counts, and reports empty lint findings with a `lint.skipped`
  sentence

#### Scenario: Newest archive wins
- **WHEN** `semdiff change my-change` runs and both
  `completed/2026-01-01-my-change/` and `completed/2026-02-01-my-change/`
  exist with no planned copy
- **THEN** the JSON `dir` names `completed/2026-02-01-my-change`

#### Scenario: Unknown change fails clearly
- **WHEN** `semdiff change nope` runs and neither `planned/nope/` nor any
  `completed/*-nope/` exists
- **THEN** it exits non-zero naming the missing change and both `planned/`
  and `completed/`

### Requirement: Spec-aware verification
id: spec-aware-review
base: fc88b7c23c3c

Where a change is in scope, the skill SHALL verify the diff against
`semdiff change` output: classify every delta scenario as Met (citing the
satisfying hunk), Unmet, or Can't-tell; report each unmet scenario as a
high-severity spec-coverage finding; flag checked tasks with no supporting
change in the diff; and surface behavioral changes no requirement or task
describes as observations, not blockers.

A change is in scope when the user names one, when exactly one change exists
under `planned/`, or when the diff adds or edits a change directory under
`planned/` or `completed/`; in the last case the skill SHALL read the slug
from the directory name in the `files` output, stripping any leading
`YYYY-MM-DD-` date prefix. The spec-aware reference, the `SKILL.md`
references table, and the gate body under `plugins/s/harness/bodies/` SHALL
each state that three-part trigger.

#### Scenario: Unmet scenario tops the findings
- **WHEN** a delta scenario's behavior is absent from the structural diff
- **THEN** the review reports it as a high-severity spec-coverage finding
  and the verdict is Fix required

#### Scenario: An archived change in the diff is in scope
- **WHEN** a pull request's diff adds `.shipd/completed/2026-09-25-my-change/`
  and nothing sits under `planned/`
- **THEN** the review runs `semdiff change my-change` and reports a Spec
  coverage section for its scenarios

#### Scenario: Every trigger surface agrees
- **WHEN** `plugins/s/skills/review/references/spec-aware.md`,
  `plugins/s/skills/review/SKILL.md`, and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** each names a change directory carried by the diff under
  `planned/` or `completed/` as a trigger, beside the named-change and
  single-planned-change triggers
