## ADDED Requirements

### Requirement: Agent surface documentation
id: agent-surface-docs

The documentation SHALL describe the harness agent surface.
`docs/customise.md`'s harness section SHALL name the agent files a harness
receives beside its commands and link to the reference.
`docs/harness-agents-reference.md` SHALL record, for each harness that declares
`subagents`, its agent files' repository and user-global locations and the
frontmatter those files carry, the `shipd-<role>` agent ids, and the steps to
add a harness.

#### Scenario: The reference records each harness's agent surface
- **WHEN** `docs/harness-agents-reference.md` is read
- **THEN** it names `claude-code`, `opencode`, `agy`, and `oh-my-pi` with each
  one's agent repository and user-global location and frontmatter, and states
  the `shipd-sub-agent`, `shipd-oracle`, and `shipd-validator` ids

#### Scenario: Customise points at the reference
- **WHEN** `docs/customise.md`'s harness section is read
- **THEN** it names the agent files written beside the commands and links to
  `harness-agents-reference.md`
