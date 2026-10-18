## ADDED Requirements

### Requirement: Delegation names the generated agents
id: delegation-agent-ids

Each body template's `<!-- if:subagents -->` branch SHALL name the generated
agent it directs the harness to spawn, using the neutral agent id that harness
receives: the `build` and `autopilot` bodies SHALL name `shipd-sub-agent`, and
the `ask` body SHALL name `shipd-oracle`. A body rendered for a harness that
declares no `subagents` SHALL name no agent id, and SHALL keep the single-agent
`else` branch it carries today.

#### Scenario: The subagents branch names the generated agent
- **WHEN** the `build`, `ask`, and `autopilot` bodies are rendered for a harness
  declaring `subagents`
- **THEN** the `build` and `autopilot` branches name `shipd-sub-agent` and the
  `ask` branch names `shipd-oracle`

#### Scenario: A harness without subagents names no agent
- **WHEN** the `build` body is rendered for a harness declaring no `subagents`
- **THEN** its text names no `shipd-sub-agent` and carries the single-agent
  branch
