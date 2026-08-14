## ADDED Requirements

### Requirement: Metadata-aware emission
id: metadata-aware-emission

When the user's request supplies a profile, theme, epic, or initiative for
the change, the plan flow SHALL record it as the corresponding header
metadata line in the emitted `plan.md`, honoring the initiative-through-epic
rule. When the request supplies none, emission SHALL write no metadata lines,
leaving the change at the implied `full` profile.

#### Scenario: Requested lite profile is recorded
- **WHEN** the user asks for a quick, low-ceremony change and the plan flow
  emits it as lite
- **THEN** the emitted `plan.md` header carries `Profile: lite`

#### Scenario: Default emission stays bare
- **WHEN** the request names no profile, theme, epic, or initiative
- **THEN** the emitted header contains only the title and `Status:` line
