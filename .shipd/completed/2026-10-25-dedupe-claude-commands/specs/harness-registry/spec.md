## ADDED Requirements

### Requirement: Plugin-provided surfaces
id: registry-plugin-provided

The registry module SHALL declare a data map `PLUGIN_PROVIDED` from a
harness id to the Claude Code plugin id that already provides that
harness's user-global surface, holding exactly `{"claude-code": "s@shipd"}`.
Every key SHALL be a registry id.

#### Scenario: Claude Code is provided by the shipd plugin
- **WHEN** the test suite reads `harness_registry.PLUGIN_PROVIDED`
- **THEN** it equals `{"claude-code": "s@shipd"}` and every key is in `ids()`
