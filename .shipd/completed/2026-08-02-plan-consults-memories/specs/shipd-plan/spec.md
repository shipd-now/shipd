## ADDED Requirements

### Requirement: Personal memory consultation during investigation
id: memory-consultation

During investigation and before any user question round, the `am:plan` skill
SHALL read the personal memory store directly — resolving it with
`spec_status.py wiki-show --personal` and reading its catalogue with `cat wiki
index --personal` — and SHALL perform this as a direct store read that spawns no
`s:oracle` agent, so the investigation turn stays oracle-free. Where the
personal store is absent or holds no page relevant to the change, the skill
SHALL skip the consultation silently and SHALL NOT block planning. Where one or
more relevant `memory-*` pages exist — matched by index and read-only grep over
the change's subject terms — the skill SHALL read each and apply it to its plan
decisions and to its output and expression (including diagram style and tone),
and SHALL report each applied memory in user-visible text with its source slug.
If the user's typed reply contradicts an applied memory, then the user's choice
SHALL govern.

#### Scenario: Relevant memory shapes the plan and is reported
- **WHEN** a captured `memory-*` page is relevant to the change under
  investigation
- **THEN** the skill reads it, applies it to a plan decision or the plan's
  output, and reports it in user-visible text with its source slug

#### Scenario: Output-style preference applies with no open decision
- **WHEN** a relevant memory expresses an output/style preference (e.g. ASCII
  diagrams) and no un-inferrable decision would open a user question round
- **THEN** the skill still applies the preference to the plan's output, even
  though the oracle rung never fires

#### Scenario: Absent store is skipped silently
- **WHEN** no personal store exists, or none of its pages is relevant to the
  change
- **THEN** the skill skips the consultation without error and planning proceeds
  unchanged

#### Scenario: User override beats an applied memory
- **WHEN** the user's typed reply contradicts a memory the skill applied
- **THEN** the plan follows the user's choice, not the memory

#### Scenario: The consultation keeps the investigation turn oracle-free
- **WHEN** the skill consults personal memories during investigation
- **THEN** it does so by a direct store read and spawns no `s:oracle` agent in
  that turn
