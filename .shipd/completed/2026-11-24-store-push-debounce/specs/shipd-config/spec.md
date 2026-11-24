## ADDED Requirements

### Requirement: Store push delay key
id: store-push-delay-key

The engine SHALL recognize a top-level `store_push_delay` config key: a
non-negative integer of seconds the delayed store push waits after the last
store commit, resolved through the layered loader with a built-in default of
60. A value of 0 SHALL mean the push runs with no wait. If a declared value
is not a non-negative integer, then the engine SHALL treat the key as
undeclared and fall back to 60 rather than raising. The key SHALL resolve
from the same anchor as `store_autocommit`, SHALL appear in the engine's
registry of recognized top-level keys with scope `repo`, and SHALL be
documented in the plugin's copyable config reference.

#### Scenario: The delay defaults to 60
- **WHEN** the key is resolved from a repo whose layers do not declare it
- **THEN** the effective value is 60

#### Scenario: A declared value is used
- **GIVEN** a repo layer declaring `store_push_delay` as 5
- **WHEN** the key is resolved from that repo
- **THEN** the effective value is 5

#### Scenario: A malformed value falls back to the default
- **GIVEN** a repo layer declaring `store_push_delay` as the string "soon",
  as -1, or as `true`
- **WHEN** the key is resolved from that repo
- **THEN** the effective value is 60 and no error is raised

#### Scenario: The key is registered and documented
- **WHEN** the config-sample agreement check runs
- **THEN** `store_push_delay` appears in the recognized-keys registry and in
  the copyable config reference

#### Scenario: The config verb rejects a bad value
- **WHEN** the registry validates `store_push_delay` with the value "soon"
- **THEN** it reports the value invalid, naming a non-negative integer
