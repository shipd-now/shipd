## MODIFIED Requirements

### Requirement: Named plugin agent types
id: named-agent-types
base: 7c1cbc7016c5

The plugin SHALL define its worker roles as named agent types under
`plugins/s/agents/`: `sub-agent.md` (execution, registering as
`s:sub-agent`), `validator.md` (validation, registering as `s:validator`), and
`teacher.md` (post-verify teaching, registering as `s:teacher`), each a
frontmatter (`name`, `description`) plus a self-sufficient system-prompt body
carrying that role's full contract. No definition SHALL pin a `model:` in
frontmatter — the orchestrator passes the tier-below model per spawn. Build
SHALL spawn workers with these agent types, with a spawn description of
`builder <n> · <change>` for executors, `validator · <change>` for the
validator, and `teacher · <change>` for the teacher, so the session's agent
list shows the shipd role rather than a generic type.

#### Scenario: Agents pane shows the shipd role
- **WHEN** a build spawns an execution sub-agent
- **THEN** it is spawned with agent type `s:sub-agent` and a description of
  the form `builder <n> · <change>`

#### Scenario: Validator spawns under its own type
- **WHEN** Phase 5 spawns the validator
- **THEN** it is spawned with agent type `s:validator` and description
  `validator · <change>`

#### Scenario: Teacher spawns under its own type
- **WHEN** Phase 5 spawns the teacher after the `verified` stamp
- **THEN** it is spawned with agent type `s:teacher` and description
  `teacher · <change>`

#### Scenario: Tier policy survives the definitions
- **WHEN** any of the three agent definitions is read
- **THEN** its frontmatter contains no `model:` pin, and the spawn-time model
  parameter alone selects the tier
