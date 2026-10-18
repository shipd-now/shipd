## ADDED Requirements

### Requirement: Model ladder key
id: model-ladder-key

A configuration layer MAY declare a `models` key: a list of non-empty model-id
strings ordered strongest-first, the ladder the symbolic model tiers resolve
against. When no layer declares it, the ladder SHALL be
`spec_common.DEFAULT_MODEL_LADDER`. A `models` value that is not a list of
non-empty strings SHALL raise a `ConfigError` naming `models` and the offending
value.

#### Scenario: A declared ladder is read
- **WHEN** a configuration declares `models` as `["big", "mid", "small"]`
- **THEN** `resolve_model_ladder` returns that list

#### Scenario: An absent key uses the default
- **WHEN** no layer declares `models`
- **THEN** `resolve_model_ladder` returns `DEFAULT_MODEL_LADDER`

#### Scenario: A malformed ladder is refused
- **WHEN** a configuration declares `models` as a string or a list holding an
  empty string
- **THEN** reading the configuration raises a `ConfigError` naming `models` and
  the offending value
