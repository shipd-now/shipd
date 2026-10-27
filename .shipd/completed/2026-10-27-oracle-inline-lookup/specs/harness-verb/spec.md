## MODIFIED Requirements

### Requirement: Agent rendering
id: agent-rendering
base: 414105e91fce

The generation SHALL render each harness's agent files from the neutral agent
source under `plugins/s/harness/agents/`, one file per `AGENT_ROLES` member, for
every harness whose registry entry carries an `agent` member. The rendered file
SHALL be the entry's agent dialect's frontmatter block, then the ownership
marker, then the source's body.

The frontmatter SHALL carry exactly the entry's declared agent `frontmatter`
fields, in order — `name` rendered as `shipd-<role>`, `description` as the
source's declared description — followed by each `extra` field emitted verbatim,
every value escaped for YAML. The render SHALL resolve the surface paths from
the entry's agent `repo_pattern` and `user_dir`, and `render_agent` and every
agent path helper SHALL resolve to `None` for a harness whose `agent` member is
`None`.

#### Scenario: The claude-code agent renders with its declared fields
- **WHEN** `claude-code`'s `sub-agent` agent is rendered
- **THEN** the file opens with a `---` block carrying `name: shipd-sub-agent`
  and the source's description, then the ownership marker, then the source body

#### Scenario: Extra fields render verbatim
- **WHEN** `opencode`'s `sub-agent` agent and `agy`'s `validator` agent are
  rendered
- **THEN** opencode's frontmatter carries `mode: subagent` and agy's carries
  `subagent: true`, each after the fields its entry declares

#### Scenario: The render pins the plugin agent prose
- **WHEN** the neutral source is rendered for `claude-code` and compared with
  `plugins/s/agents/<role>.md`
- **THEN** the rendered description and body equal the plugin agent's
  description and body, for every `AGENT_ROLES` member

#### Scenario: Agent surface paths come from the registry
- **WHEN** `claude-code`'s and `oh-my-pi`'s agent surfaces are resolved
- **THEN** their repo-relative paths are `.claude/agents/shipd-sub-agent.md` and
  `.omp/agents/shipd-sub-agent.md`, and their user paths sit under
  `~/.claude/agents/` and `~/.omp/agent/agents/`

#### Scenario: A harness with no agent surface renders nothing
- **WHEN** `cursor`'s agent surface is rendered and its paths resolved
- **THEN** each resolves to `None`

#### Scenario: A source file without a description marker is refused
- **WHEN** a role's source file lacks its opening `<!-- description: ... -->`
  marker
- **THEN** reading it raises a `ValueError` naming the file
