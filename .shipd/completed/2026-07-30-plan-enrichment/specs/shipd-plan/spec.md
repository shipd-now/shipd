## ADDED Requirements

### Requirement: Enrichment mode activation
id: enrichment-mode-activation

When `/s:plan` receives an argument, the skill SHALL run the engine's
`locate` verb on it before any other flow step. When locate reports the change
at status `rejected`, the skill SHALL announce enrichment mode in one sentence
and operate on the located root for the rest of the session, in place of the
fresh-planning flow (no investigation digest, depth gate, or emission). When
locate reports the change at any other status, the skill SHALL report the
change's location and status and stop — it SHALL NOT start a fresh plan under
a colliding name. When locate finds no match, the skill SHALL proceed with the
normal planning flow unchanged.

#### Scenario: Rejected change enters enrichment
- **GIVEN** a member change parked at `rejected` in its worktree
- **WHEN** `/s:plan <change>` runs from the main checkout
- **THEN** the skill announces enrichment mode and works on the located
  worktree's change instead of planning afresh

#### Scenario: Non-rejected existing change is reported, not re-planned
- **WHEN** `/s:plan <change>` locates the change at `active`
- **THEN** the skill reports the location and status and stops without
  planning or editing anything

#### Scenario: Unlocated argument plans normally
- **WHEN** `/s:plan <request>` finds no installed change matching the
  argument
- **THEN** the normal investigate-then-emit flow runs unchanged

### Requirement: Enrichment gap diagnosis
id: enrichment-gap-diagnosis

While in enrichment mode, the skill SHALL read the change's artifacts through
the engine's `cat change` verb and treat the plan's `## Context insufficient`
findings as the work agenda. It SHALL resolve every codebase-answerable
finding directly by editing the installed artifacts in the located change
directory — refreshing stale `base:` hashes against the current master
requirement and reconciling the delta, correcting dangling task file
references, and replacing placeholder markers with decisions grounded in the
repository — and SHALL put to the user only findings the repository cannot
answer, batched under the fast-path typed-round contract with a context brief.
The skill SHALL NOT ask about anything discoverable from the repository.

#### Scenario: Stale hash is refreshed without asking
- **GIVEN** a rejected plan whose finding names a stale `base:` hash
- **WHEN** enrichment runs
- **THEN** the skill re-reads the master requirement, updates the delta's
  base hash and content, and asks the user nothing about it

#### Scenario: True gap goes to the user
- **GIVEN** a finding naming a placeholder that encodes an undecided
  product choice the repository cannot answer
- **WHEN** enrichment reaches it
- **THEN** the skill asks the user in a typed round preceded by a context
  brief, and folds the answer into the artifacts

### Requirement: Enrichment exits through the re-gate
id: enrichment-regate

When the enrichment agenda is resolved, the skill SHALL re-run the gate engine
(`spec_gate.py <change>`) on the located root. On exit 0 the skill SHALL
confirm the change now sits at `ready` and hand off with the motivation-led
summary. On exit 2 the skill SHALL present the remaining findings and continue
enrichment with them as the new agenda. The skill SHALL NOT move an enrichment
change out of `rejected` via `set-status` or `--force` — the gate's verdict is
the only exit to `ready`.

#### Scenario: Passing re-gate hands off ready
- **WHEN** the re-gate exits 0 on an enriched change
- **THEN** the change's status reads `ready`, the findings section is gone,
  and the skill hands off with the motivation-led summary

#### Scenario: Failing re-gate continues enrichment
- **WHEN** the re-gate exits 2 with one remaining finding
- **THEN** the skill presents that finding and keeps enriching rather than
  ending or forcing the status
