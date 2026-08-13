## ADDED Requirements

### Requirement: Global design scratch area
id: design-scratch-area

The plugin SHALL provide a stdlib `design.py` engine script under
`plugins/s/skills/build/scripts/` exposing a `path <change>` verb that resolves
and creates the per-change design directory `<designs-root>/<change>`, and a
`clean <change>` verb that removes it. The designs root SHALL default to
`~/.shipd/designs` and SHALL be overridable via the resolved configuration's
`build.design_dir` key, home-expanded — a global location outside the consuming
repository, so a parked design never enters that repo or its PR. The `clean`
verb SHALL be fail-soft: a missing directory or a removal failure warns on
stderr and still exits `0`, so cleanup never blocks a build.

#### Scenario: path resolves and creates the change dir
- **WHEN** `design.py path <change>` runs
- **THEN** it prints the absolute `<designs-root>/<change>` path (default under
  `~/.shipd/designs`) and the directory exists afterward

#### Scenario: design_dir config overrides the root
- **WHEN** the resolved configuration sets `build.design_dir`
- **THEN** `design.py path <change>` resolves the per-change dir under that
  configured root rather than the default

#### Scenario: clean is fail-soft
- **WHEN** `design.py clean <change>` runs against a missing or unremovable
  directory
- **THEN** it warns on stderr and exits `0` rather than failing the build

### Requirement: Design reference consumed from the scratch area
id: design-reference-consumed

Where a change carries a design, `plan.md`'s `## Implementation` section SHALL
name the change's design scratch directory by absolute path, and the execution
sub-agent and the validator SHALL read that directory as a **read-only**
reference and build to match it verbatim. The design SHALL travel by that
plan-named path rather than as prose in the spawn message, so the clean-context
handoff is preserved. Where no design scratch directory is named, build behavior
SHALL be unchanged (consume-if-present).

#### Scenario: Sub-agent reads the plan-named design
- **WHEN** `plan.md`'s `## Implementation` names a design scratch directory
- **THEN** the sub-agent reads that directory as a read-only reference and
  implements to match it, rather than reconstructing the design from a prose
  summary

#### Scenario: No design named leaves the handoff unchanged
- **WHEN** a change's `plan.md` names no design scratch directory
- **THEN** the build proceeds exactly as before, with no design read attempted

### Requirement: Design fidelity encoded as validator scenarios
id: design-fidelity-scenarios

Where a change carries a design, `/s:plan` SHALL author design conformance as
`#### Scenario:` blocks in the change's delta specs — asserting the observable
properties the implementation must match against the plan-named design — and the
validator SHALL refute those scenarios by exercising the real behavior against
the design. A refuted fidelity scenario SHALL block `verified` exactly as any
other refuted scenario does.

#### Scenario: Fidelity scenario is authored and gated
- **WHEN** a change with a design is planned
- **THEN** its delta specs carry `#### Scenario:` blocks asserting design
  conformance, and the validator refuting any of them blocks `set-status
  verified`

### Requirement: Design scratch cleanup at build finish
id: design-scratch-cleanup

At build finish (the `/s:build` close-out), build SHALL remove the change's
design scratch directory via `design.py clean <change>`, so a design never
lingers in the global scratch area or reaches the consuming repository. The
cleanup SHALL be fail-soft — a failure warns and does not block the build's
completion or reporting.

#### Scenario: Finish deletes the scratch dir
- **WHEN** a build reaches its close-out
- **THEN** it runs `design.py clean <change>` and the change's design scratch
  directory no longer exists

#### Scenario: Cleanup failure does not block finish
- **WHEN** the scratch directory cannot be removed at finish
- **THEN** the failure warns on stderr and the build still completes and reports
