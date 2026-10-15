## ADDED Requirements

### Requirement: Plan stamp on a passing gate
id: plan-stamp-write

When the gate passes a change, it SHALL write two header metadata lines into
the plan — `Planned-at: <sha>`, the full commit id of `git merge-base HEAD
<base>` resolved from the plan's own directory with `--base` defaulting to
`main`, and `Gated-hash: <hash>`, the engine's normalized content hash of the
plan text with the `Status:` line and both stamp lines excluded — replacing
existing stamp lines in place and otherwise appending them, `Planned-at`
first, as the last lines of the header metadata block. If the base cannot be
resolved (git absent, no work tree, unresolvable ref), then the gate SHALL
write no `Planned-at` line, remove a stale one, print one `note:` line on
stderr, and still pass. A rejecting run SHALL leave existing stamp lines
untouched. The stamp SHALL be written through stdlib code and local `git`
only.

#### Scenario: Pass writes both stamp lines after existing metadata
- **GIVEN** a clean draft plan whose header carries `Epic: e` under
  `Status:` in a git work tree whose `main` is an ancestor of `HEAD`
- **WHEN** `spec_gate.py <change>` runs
- **THEN** the header reads `Status: ready`, `Epic: e`, `Planned-at: <40-hex
  sha of merge-base HEAD main>`, `Gated-hash: <12-hex>` in that order, and
  `parse_plan_metadata` returns all three metadata pairs

#### Scenario: Re-gate replaces the stamp in place
- **GIVEN** a stamped `ready` plan whose `## Idea` was edited
- **WHEN** the gate passes it again
- **THEN** exactly one `Planned-at` and one `Gated-hash` line exist and the
  `Gated-hash` value differs from the earlier one

#### Scenario: Unresolvable base omits Planned-at
- **GIVEN** a clean draft plan in a root that is not a git work tree
- **WHEN** the gate runs
- **THEN** it exits 0 with `Gated-hash` written, no `Planned-at` line, and a
  `note:` line on stderr

#### Scenario: Whitespace edits keep the hash
- **WHEN** a stamped plan gains trailing spaces and an extra blank line
- **THEN** recomputing the plan hash yields the stamped value

### Requirement: Read-only check mode
id: gate-check-mode

`spec_gate.py <change> --check` SHALL run the linter and every gate check and,
when the plan carries a `Gated-hash`, SHALL add a finding when the recomputed
plan hash differs from it, naming both values and `spec_gate.py <change>` as
the remedy. It SHALL print `PASS (check): ...` and exit 0 when no finding
exists, or `REJECTED (check): ...` with one dot-point per finding and exit 2;
a general error SHALL exit 1 as the gate does. The mode SHALL write no file,
change no status, run no store autocommit, and record no flow snapshot. A
plan with no stamp SHALL produce no mismatch finding.

#### Scenario: Clean draft stays draft under check
- **GIVEN** a clean draft plan
- **WHEN** `spec_gate.py <change> --check` runs
- **THEN** it exits 0 and the plan still reads `Status: draft` byte-for-byte

#### Scenario: Findings print without being written
- **GIVEN** a draft plan whose tasks carry one of the gate's placeholder
  markers
- **WHEN** `--check` runs
- **THEN** it exits 2 naming the placeholder, and the plan gains no
  `## Context insufficient` section and keeps `Status: draft`

#### Scenario: Edited-after-gate is a check finding
- **GIVEN** a `ready` plan stamped by a passing gate whose `## Implementation`
  was then edited
- **WHEN** `--check` runs
- **THEN** it exits 2 with a `gated-hash mismatch` finding naming the stamped
  and recomputed hashes, and the plan is unchanged

#### Scenario: Unstamped ready plan checks clean
- **GIVEN** a clean `ready` plan with no stamp lines
- **WHEN** `--check` runs
- **THEN** it exits 0

## MODIFIED Requirements

### Requirement: Context-sufficiency gate verb
id: context-gate-verb
base: 9851e28d228d

A stdlib-Python `spec_gate.py <change>` SHALL evaluate a planned change and
settle its status: when every check passes it SHALL remove any
`## Context insufficient` section from the change's `plan.md`, write the plan
stamp (per the plan-stamp requirement, with the base ref taken from `--base`,
default `main`), and promote a `draft` (or leave a `ready`) plan to `ready`,
printing a pass line and a `stamp:` line and exiting 0; when any check fails
it SHALL write the findings into `plan.md` (per the ephemeral report
requirement), set the change's status to `rejected`, print the findings, and
exit 2. A general error (unknown change, unreadable tree) SHALL exit 1.
Status writes SHALL go through the engine's metadata-preserving status
machinery.

#### Scenario: Passing gate promotes and cleans
- **GIVEN** a lint-clean draft change with no context findings and a stale
  `## Context insufficient` section from an earlier run
- **WHEN** `spec_gate.py <change>` runs
- **THEN** the section is gone, the status line reads `ready`, a
  `Gated-hash` line is present, and the exit code is 0

#### Scenario: Failing gate rejects with findings
- **WHEN** the gate finds a placeholder marker in a draft plan
- **THEN** `plan.md` gains a `## Context insufficient` section naming it,
  the status line reads `rejected`, and the exit code is 2

#### Scenario: Unknown change is a general error
- **WHEN** `spec_gate.py no-such-change` runs
- **THEN** the CLI exits 1 and writes nothing
