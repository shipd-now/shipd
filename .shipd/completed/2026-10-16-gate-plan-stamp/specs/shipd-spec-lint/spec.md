## MODIFIED Requirements

### Requirement: Plan metadata validation
id: plan-metadata-validation
base: 1e4c19b3a03a

When linting a change, the linter SHALL validate the plan's header metadata
block: it SHALL error on an unrecognized key in the block, on a slug-valued
key whose value is not a kebab-case slug, on a `Planned-at:` value that is
not 7–40 lowercase hex characters, on a `Gated-hash:` value that is not 12
lowercase hex characters, on a `Profile:` value other than `full` or `lite`,
on a plan carrying both `Epic:` and `Initiative:` lines, and on a `Theme:`
value outside `valid_themes` when the resolved layered configuration
declares a non-empty vocabulary. The linter SHALL NOT recompute or compare
the stamped hash. A plan with no metadata block SHALL lint exactly as it did
before this feature.

#### Scenario: Unrecognized key errors
- **WHEN** a plan's metadata block contains `Them: reliability`
- **THEN** the linter reports an error naming the unrecognized key and
  exits non-zero

#### Scenario: Stamp lines lint clean
- **WHEN** a plan's metadata block carries
  `Planned-at: 076a9effc1acd6acbf99b2c2209d1998fe5ab9fe` and
  `Gated-hash: 9851e28d228d`
- **THEN** the linter reports no error for either line

#### Scenario: Malformed stamp value errors
- **WHEN** a plan carries `Gated-hash: not-a-hash`
- **THEN** the linter reports an error naming the value and the expected
  hex shape

#### Scenario: Theme outside declared vocabulary errors
- **GIVEN** the repo's `.shipd-config.json` declares
  `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: speed`
- **THEN** the linter reports an error naming the invalid theme

#### Scenario: Epic with initiative errors
- **WHEN** a plan carries both `Epic:` and `Initiative:` lines
- **THEN** the linter reports an error stating the initiative must attach
  to the epic
