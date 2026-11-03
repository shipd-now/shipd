## ADDED Requirements

### Requirement: Sandbox config key
id: sandbox-config-key

The engine SHALL recognize a top-level `sandbox` key, listed in
`spec_common.RECOGNIZED_CONFIG_KEYS` and in `config_registry.REGISTRY` with
default layer `repo` and no owner. Its value SHALL be an object whose only
members are an optional `fake_bin`, a non-empty relative path with no `..`
segment, and an optional `env`, an object mapping names matching
`^[A-Z_][A-Z0-9_]*$` to non-empty relative paths with no `..` segment. If a
value breaks that shape, then `config-check` and `config-set` SHALL report an
error naming `sandbox`. The example config SHALL document `// sandbox`, and
`docs/customise.md` SHALL list the key.

#### Scenario: A well-formed sandbox key validates
- **WHEN** `config-check` reads `"sandbox": {"fake_bin": "tests/fake-bin", "env": {"REVIEW_BOT_HOME": "review-bot"}}`
- **THEN** it reports no finding for `sandbox`

#### Scenario: An escaping path is rejected
- **WHEN** the `sandbox` validator runs on `{"env": {"X": "../outside"}}`
- **THEN** it reports an error naming `sandbox`

#### Scenario: An unknown member is rejected
- **WHEN** the `sandbox` validator runs on `{"fakebin": "x"}`
- **THEN** it reports an error naming `sandbox`

#### Scenario: The example documents the key
- **WHEN** the sample-coverage test compares the registry with the example
  config
- **THEN** `sandbox` appears on both sides
