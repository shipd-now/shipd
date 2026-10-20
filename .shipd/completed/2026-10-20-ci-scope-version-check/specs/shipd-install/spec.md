## ADDED Requirements

### Requirement: Main-branch plugin version check
id: plugin-version-main-check

Two pull requests can each pass the pull request version guard against an older `main` and still land the same plugin version. When a commit is pushed to `main`, the repository's CI workflow SHALL run `plugins/s/skills/build/scripts/version_guard.py` with the commit's first parent as the base and the pushed commit as the head, reusing the guard's comparison rather than a second implementation. If the guard reports a finding or cannot read a manifest, then the step SHALL fail, SHALL emit a GitHub error annotation carrying the guard's output, which names the parent's version and the pushed commit's version, and SHALL tell the reader to land a follow-up pull request that bumps `plugins/s/.claude-plugin/plugin.json`. The step SHALL run only on push events and SHALL carry no CI scope guard.

#### Scenario: A duplicate version on main fails loudly
- **GIVEN** a parent commit whose manifest carries `0.6.319`
- **WHEN** a commit that edits `plugins/s/skills/build/scripts/x.py` and keeps `0.6.319` runs the main check step
- **THEN** the step exits non-zero, and its output names `0.6.319` for both commits and asks for a follow-up version bump

#### Scenario: An advanced version on main passes
- **GIVEN** a parent commit whose manifest carries `0.6.319`
- **WHEN** a commit that edits `plugins/s/` and carries `0.6.320` runs the main check step
- **THEN** the step exits 0

#### Scenario: A change outside the plugin passes on main
- **WHEN** a commit that edits only `.shipd/epics/x/epic.md` runs the main check step
- **THEN** the step exits 0

#### Scenario: The check runs on push and ignores the scope
- **WHEN** `.github/workflows/ci.yml` is inspected
- **THEN** the workflow triggers on push to `main`, and a step invoking `version_guard.py` with the parent commit as base is conditioned on the push event and carries no `scope` guard

## MODIFIED Requirements

### Requirement: Plugin version advance guard
id: plugin-version-advance
base: d58075580004
Dropped: CI runs the guard on pull requests only

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
step SHALL fetch enough history for that base ref to resolve. On pushes to
`main` the guard runs against the pushed commit's first parent instead, as the
main-branch plugin version check requires.

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

#### Scenario: CI runs the pull request guard against the base branch
- **WHEN** `.github/workflows/ci.yml` is inspected
- **THEN** it carries a step invoking `version_guard.py` against the pull
  request's base branch, conditioned on the event being a pull request, and its
  checkout step sets `fetch-depth: 0`

#### Scenario: The change bumps the version it guards
- **WHEN** this change's own manifest is inspected
- **THEN** its version exceeds `0.6.222`
