## ADDED Requirements

### Requirement: Plugin version advance guard
id: plugin-version-advance

The plugin's cache snapshot is keyed by the version in
`plugins/s/.claude-plugin/plugin.json`, so a change that edits `plugins/s/`
without advancing that version leaves `claude plugin update` a no-op and every
session running the superseded snapshot. The repository SHALL therefore carry a
guard that refuses such a change rather than relying on the convention being
remembered.

The engine SHALL provide a stdlib-only script at
`plugins/s/skills/build/scripts/version_guard.py` exposing a comparison that
takes a base version, a head version, and the paths a change touched, and
reports a finding when both of these hold: at least one touched path lies under
`plugins/s/` other than `plugins/s/.claude-plugin/plugin.json` itself, and the
head version does not exceed the base version. A change touching nothing under
`plugins/s/` SHALL report no finding whatever the versions are, and a change
whose only `plugins/s/` path is the manifest SHALL likewise report none.

Version comparison SHALL split each value on `.` and compare components
pairwise as integers where both parse as integers, and as strings otherwise, so
that `0.6.10` ranks above `0.6.9`. Comparison SHALL NOT coerce a version to a
float.

Invoked as `version_guard.py --base <ref> --head <ref>`, the script SHALL
resolve each version from that ref's copy of the manifest and the touched paths
from the diff between the two refs, SHALL exit `0` with no output when there is
no finding, SHALL exit `1` printing the finding when there is one, and SHALL
exit `2` naming the ref whose manifest it could not read or parse.

The repository's CI workflow (`.github/workflows/ci.yml`) SHALL run the guard
on pull request events against the pull request's base branch, and its checkout
step SHALL fetch enough history for that base ref to resolve. The workflow SHALL
NOT run the guard on pushes to `main`, where a squash merge leaves no base
version to compare.

#### Scenario: A plugin change without a bump fails
- **GIVEN** a change touching `plugins/s/skills/build/tests/test_thing.py`
- **WHEN** the guard compares a base version of `0.6.222` against a head
  version of `0.6.222`
- **THEN** it reports a finding

#### Scenario: A plugin change with a bump passes
- **GIVEN** the same touched path
- **WHEN** the guard compares a base version of `0.6.222` against a head
  version of `0.6.223`
- **THEN** it reports no finding

#### Scenario: A change outside the plugin is exempt
- **GIVEN** a change touching only `docs/customise.md`
- **WHEN** the guard compares a base and head version that are equal
- **THEN** it reports no finding

#### Scenario: A version-only change is exempt
- **GIVEN** a change whose only touched path under `plugins/s/` is
  `plugins/s/.claude-plugin/plugin.json`
- **WHEN** the guard runs
- **THEN** it reports no finding

#### Scenario: Numeric components rank above string length
- **WHEN** the guard compares a base version of `0.6.9` against a head version
  of `0.6.10` for a change touching `plugins/s/`
- **THEN** it reports no finding, because `0.6.10` exceeds `0.6.9`

#### Scenario: A decrease fails
- **WHEN** the guard compares a base version of `0.6.223` against a head
  version of `0.6.222` for a change touching `plugins/s/`
- **THEN** it reports a finding

#### Scenario: An unreadable manifest exits two
- **WHEN** the script cannot read or parse the manifest at a named ref
- **THEN** it exits `2` and its message names that ref

#### Scenario: CI runs the guard on pull requests only
- **WHEN** `.github/workflows/ci.yml` is inspected
- **THEN** it carries a step invoking `version_guard.py` conditioned on the
  event being a pull request, and its checkout step sets `fetch-depth: 0`

#### Scenario: The change bumps the version it guards
- **WHEN** this change's own manifest is inspected
- **THEN** its version exceeds `0.6.222`
