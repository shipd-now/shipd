## ADDED Requirements

### Requirement: Context-sufficiency gate verb
id: context-gate-verb

A stdlib-Python `spec_gate.py <change>` SHALL evaluate a planned change and
settle its status: when every check passes it SHALL remove any
`## Context insufficient` section from the change's `plan.md` and promote a
`draft` (or leave a `ready`) plan to `ready`, printing a pass line and
exiting 0; when any check fails it SHALL write the findings into `plan.md`
(per the ephemeral report requirement), set the change's status to
`rejected`, print the findings, and exit 2. A general error (unknown
change, unreadable tree) SHALL exit 1. Status writes SHALL go through the
engine's metadata-preserving status machinery.

#### Scenario: Passing gate promotes and cleans
- **GIVEN** a lint-clean draft change with no context findings and a stale
  `## Context insufficient` section from an earlier run
- **WHEN** `spec_gate.py <change>` runs
- **THEN** the section is gone, the status line reads `ready`, and the
  exit code is 0

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
resolve to an existing file or directory, or have an existing parent
directory (the new-file case) — anything else is a finding naming the
token; (4) every MODIFIED, REMOVED, or RENAMED delta operation SHALL target
a capability whose master spec exists, while ADDED-only new capabilities
pass. The gate SHALL NOT invoke a model or the network.

#### Scenario: Stale base hash is a finding
- **GIVEN** a delta whose `base:` no longer matches the master requirement
- **WHEN** the gate runs
- **THEN** the findings name the requirement id as stale context

#### Scenario: Placeholder marker is a finding
- **WHEN** a task reads "wire the config (TODO: decide key name)"
- **THEN** the findings name the placeholder and its file

#### Scenario: Unresolvable task path is a finding
- **WHEN** a task names `src/engine/missing.py` and neither it nor
  `src/engine/` exists
- **THEN** the findings name the token

#### Scenario: New file in an existing directory passes
- **WHEN** a task names a new file whose parent directory exists
- **THEN** no file-reference finding is produced for it

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
