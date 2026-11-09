## MODIFIED Requirements

### Requirement: Neutral agent source
id: registry-agent-source
base: 20ffb2d916f0

The plugin SHALL ship a neutral agent-definition source under
`plugins/s/harness/agents/`, one file per `AGENT_ROLES` member
(`sub-agent.md`, `validator.md`, `teacher.md`), each opening with a
`<!-- description: <one line> -->` marker followed by that role's
system-prompt prose, and carrying no harness-specific frontmatter. Each file's
prose SHALL be the plugin's existing agent prose for that role, re-homed
verbatim rather than rewritten. `AGENT_ROLES` SHALL equal
`("sub-agent", "validator", "teacher")`, so the generator renders a
`shipd-teacher` agent file for every harness that carries an `agent` member.

#### Scenario: One source file per role
- **WHEN** the test suite reads `plugins/s/harness/agents/`
- **THEN** it holds exactly one file per `AGENT_ROLES` member, each opening
  with a non-empty `<!-- description: ... -->` marker

#### Scenario: The source matches the plugin agent prose
- **WHEN** a role's source file and the plugin's `plugins/s/agents/<role>.md`
  are read
- **THEN** the source's body after the description marker equals the plugin
  agent's body after its frontmatter

#### Scenario: The teacher role is generated beside the others
- **WHEN** a harness declaring `subagents` is added for the user
- **THEN** its agent location receives `shipd-teacher` alongside
  `shipd-sub-agent` and `shipd-validator`
