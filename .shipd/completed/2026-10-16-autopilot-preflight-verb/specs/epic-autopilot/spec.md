## ADDED Requirements

### Requirement: Launch preflight rubric
id: launch-preflight

The autopilot driver SHALL provide a read-only `--preflight` mode
(`autopilot.py <epic> --preflight [--json]`) that composes a launch rubric
from on-disk state, local git, and the engine's own verbs, drives nothing,
and prints one `ok|warn|fail <check> — <detail>` line per check in the
`shipd doctor` format followed by a `preflight: ok` or `preflight: <n>
problem(s)` summary, exiting non-zero exactly when at least one line is
`fail`. The checks, in order, SHALL be: `epic-lint` (the single-epic lint,
`fail` on any error); `epic-status` (`ok` at `ready` or `active`, `fail`
otherwise naming the remedy); `after-cycle` (`fail` naming the cycle's
slugs as `a -> b -> a`); `members` (`fail` when any member is `unplanned`,
`draft`, or `rejected`, naming the members per state and `/s:epic-grill
<epic>` for the first two and `/s:plan <member>` for a rejected one; `warn`
naming members mid-build; `ok` when every member is `ready` or `archived`);
`gate-check` (one `spec_gate.py <member> --check` run per `ready` member
from its hosting root, `fail` naming the member and its first finding on a
non-zero exit other than a `gated-hash mismatch`); `gated-hash` (`fail`
naming the member and `spec_gate.py <member>` when its check reported a
`gated-hash mismatch`, `warn` when a `ready` plan carries no `Gated-hash`
stamp); `drift` (one `spec_status.py drift --epic <epic> --json` run, `warn`
naming each drifted member with its finding counts and `/s:drift <epic>`
on exit 4, `fail` on any other non-zero exit); `overlap-requirements`
(`fail` naming each pair of planned members whose delta specs modify,
remove, or rename the same master requirement while neither reaches the
other through the `After` graph); `overlap-files` (`warn` naming each such
unordered pair citing the same path in `plan.md`, `tasks.md`, or a delta
spec, with `artefacts/` references and the version-bump exempt paths
ignored); `pipeline` (`ok` with the entry count and provenance, `fail` when
the pipeline does not resolve); then every `shipd doctor` line relayed with
its level and detail unchanged and its check name prefixed `doctor:`, the
doctor's own summary line dropped. With `--json` the mode SHALL print one
object `{"epic", "checks": [{"level", "check", "detail"}], "problems",
"failed"}` carrying the same rubric. The mode SHALL never call the
cycle-refusing member ordering, so a cyclic epic still prints its full
rubric. An epic with no `epic.md` SHALL be an error exit as `--waves`
reports one, and combining `--preflight` with `--waves`, `--dry-run`, or
`--member` SHALL be a usage error. Every external verb SHALL run through
the driver's injectable command seam.

#### Scenario: A green rubric exits zero
- **GIVEN** a lint-clean `ready` epic whose members are all stamped `ready`
  with disjoint master requirements and cited files, whose gate checks,
  drift verb, and doctor all report clean
- **WHEN** `--preflight` runs
- **THEN** every line is `ok`, the summary reads `preflight: ok`, the exit
  code is 0, and no session, gate write, worktree, or heartbeat action
  occurs

#### Scenario: An unplanned member fails naming the grill
- **GIVEN** an epic with one `unplanned` member
- **WHEN** `--preflight` runs
- **THEN** a `fail members —` line names that member under `unplanned` and
  `/s:epic-grill <epic>`, and the exit code is 1

#### Scenario: Edited after gate fails the preflight
- **GIVEN** a `ready` member whose `--check` run exits 2 with a `gated-hash
  mismatch` finding
- **WHEN** `--preflight` runs
- **THEN** a `fail gated-hash —` line names the member and `spec_gate.py
  <member>`, and the `gate-check` line does not repeat that finding

#### Scenario: A dependency cycle fails but the rubric still prints
- **GIVEN** an epic whose `After` column holds `x -> y -> x`
- **WHEN** `--preflight` runs
- **THEN** a `fail after-cycle —` line names `x -> y -> x`, every other
  check line still prints, and the exit code is 1

#### Scenario: Shared master requirement without an edge fails
- **GIVEN** `ready` members `a` and `b` whose deltas both modify
  `cap/req-one`, with no `After` relation between them
- **WHEN** `--preflight` runs
- **THEN** a `fail overlap-requirements —` line names `a & b` and
  `cap/req-one`

#### Scenario: A transitive After path orders two members
- **GIVEN** `c` after `b`, `b` after `a`, and `a` and `c` both modifying
  the same master requirement and citing the same file
- **WHEN** `--preflight` runs
- **THEN** the `overlap-requirements` and `overlap-files` lines are `ok`

#### Scenario: Shared cited file without an edge warns
- **GIVEN** unordered `ready` members `a` and `b` both citing
  `src/engine.py` in their tasks
- **WHEN** `--preflight` runs
- **THEN** a `warn overlap-files —` line names `a & b` and `src/engine.py`,
  and that line alone does not make the exit code non-zero

#### Scenario: The version-bump file never overlaps
- **GIVEN** unordered members both citing
  `plugins/s/.claude-plugin/plugin.json` and nothing else in common
- **WHEN** `--preflight` runs
- **THEN** the `overlap-files` line is `ok`

#### Scenario: Drift warns and names the judgment step
- **GIVEN** a drift verb run exiting 4 with one member carrying two
  `file-drift` findings
- **WHEN** `--preflight` runs
- **THEN** a `warn drift —` line names that member, `file-drift 2`, and
  `/s:drift <epic>`

#### Scenario: Doctor lines are relayed under a prefix
- **GIVEN** a doctor run printing `ok git — found`, `warn protection —
  unprotected`, and `doctor: 1 problem(s)`
- **WHEN** `--preflight` runs
- **THEN** the rubric carries `ok doctor:git — found` and `warn
  doctor:protection — unprotected` and no line for the summary

#### Scenario: JSON is one object
- **WHEN** `--preflight --json` runs on an epic with one failing check
- **THEN** stdout parses as one object whose `checks` list holds every line
  as `{"level", "check", "detail"}`, `failed` is true, and the exit code
  is 1

#### Scenario: Preflight is exclusive with the driving modes
- **WHEN** `--preflight` is combined with `--waves`, `--dry-run`, or
  `--member`
- **THEN** the driver exits 2 with a usage error and prints no rubric
