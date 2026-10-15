# context-gate

### Requirement: Context-sufficiency gate verb
id: context-gate-verb

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

### Requirement: Deterministic context checks
id: context-sufficiency-checks

The gate SHALL run the linter's structural change checks plus exactly these
context checks, all deterministic and repository-local: (1) every `base:`
hash on a MODIFIED or REMOVED delta entry SHALL equal the current master
requirement's content hash — a mismatch is a stale-context finding; (2) the
markers `TBD`, `TODO`, `FIXME`, `XXX`, `???`, and `OPEN QUESTION`
(case-insensitive, word-bounded) SHALL be findings wherever they appear in
`plan.md`, the delta specs, or `tasks.md`; (3) every backticked token in
`tasks.md` that contains a `/` and is shaped like a repository path SHALL
resolve to an existing file or directory, or have an existing parent or
grandparent directory — tolerating one new directory level, the
new-skill/new-test-tree case — and a token whose parent and grandparent
are both missing SHALL be a finding naming the token and both missing
levels; (4) every MODIFIED, REMOVED, or RENAMED delta operation SHALL
target a capability whose master spec exists, while ADDED-only new
capabilities pass. The gate SHALL NOT invoke a model or the network.

#### Scenario: Stale base hash is a finding
- **GIVEN** a delta whose `base:` no longer matches the master requirement
- **WHEN** the gate runs
- **THEN** the findings name the requirement id as stale context

#### Scenario: Placeholder marker is a finding
- **WHEN** a task reads "wire the config (TODO: decide key name)"
- **THEN** the findings name the placeholder and its file

#### Scenario: New file in an existing directory passes
- **WHEN** a task names a new file whose parent directory exists
- **THEN** no file-reference finding is produced for it

#### Scenario: New file one new directory deep passes
- **GIVEN** `plugins/s/skills/` exists and `plugins/s/skills/research/`
  does not
- **WHEN** a task names `plugins/s/skills/research/SKILL.md`
- **THEN** no file-reference finding is produced for it

#### Scenario: Deep dangling path is still a finding
- **WHEN** a task names `src/ghost/nested/missing.py` and neither
  `src/ghost/nested/` nor `src/ghost/` exists
- **THEN** the findings name the token and that both its parent and
  grandparent directories are missing

#### Scenario: Delta against a missing capability is a finding
- **WHEN** a delta carries `## MODIFIED Requirements` for a capability
  with no master spec
- **THEN** the findings name the capability

### Requirement: Ephemeral insufficiency report in the plan
id: ephemeral-insufficiency-report

On a failing gate run the gate SHALL insert or replace a single
`## Context insufficient` section in the change's `plan.md`, placed after
the header metadata block and before `## Idea`, containing one paragraph
summarizing what is missing followed by a dot-point per finding. On a
passing run the gate SHALL remove the section entirely. The write SHALL
preserve the title, `Status:` line, and header metadata unchanged, and
repeated failing runs SHALL replace the section rather than accumulate
copies.

#### Scenario: Report lands before the Idea
- **WHEN** the gate rejects a plan
- **THEN** `## Context insufficient` appears before `## Idea` with a
  summary paragraph and one dot-point per finding

#### Scenario: Re-gate replaces, never accumulates
- **WHEN** the gate rejects a plan that already carries the section
- **THEN** exactly one `## Context insufficient` section exists afterwards,
  reflecting only the latest findings

#### Scenario: Passing run removes the report
- **WHEN** an enriched plan passes a re-gate
- **THEN** the section is absent from `plan.md`

### Requirement: Change-relative artefact references resolve
id: artefact-reference-resolution

Within the gate's task-path check, a backticked token in `tasks.md` that begins
with `artefacts/` SHALL also be resolved against the change's own directory: the
token SHALL produce no finding when it names an existing file or directory
inside `<content-dir>/planned/<change>/`, and SHALL fall through to the check's
existing repository-root resolution otherwise. This change-relative resolution
SHALL apply only to tokens carrying that prefix, so a mistyped repository path
remains a finding, and it SHALL introduce no model call and no network access.

#### Scenario: Change-relative artefact reference resolves
- **GIVEN** the change directory holds `artefacts/policy.md`
- **WHEN** a task names that path change-relatively in backticks
- **THEN** no file-reference finding is produced for it

#### Scenario: Missing artefact reference is still a finding
- **GIVEN** the change directory holds no `artefacts/ghost.md`
- **WHEN** a task names that path change-relatively in backticks
- **THEN** the findings name the token

#### Scenario: A mistyped repository path is unaffected
- **GIVEN** a task names `src/ghost/nested/missing.py` in backticks and neither
  `src/ghost/nested/` nor `src/ghost/` exists
- **WHEN** the gate runs
- **THEN** the findings still name that token

### Requirement: Provisional ledger entries block promotion
id: provisional-entry-check

Alongside its deterministic context checks, the gate SHALL treat every
`## Questions and answers` entry in `plan.md` whose `**Answered by:**` field
holds `PLANNER` as a finding naming the entry, because a provisional default
still awaits a human answer. A plan carrying such an entry SHALL be rejected
like any other finding, and the check SHALL stay deterministic and
repository-local.

#### Scenario: Provisional ledger entry is a finding
- **GIVEN** a plan whose `### Q2:` ledger entry carries
  `**Answered by:** PLANNER`
- **WHEN** the gate runs
- **THEN** the change is rejected and the findings name entry `Q2` as a
  provisional entry awaiting a human answer

#### Scenario: Settled ledger entries pass
- **GIVEN** a plan whose ledger entries carry only `**Answered by:** ORACLE`
  or `**Answered by:** USER`
- **WHEN** the gate runs
- **THEN** no provisional-entry finding is produced

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
