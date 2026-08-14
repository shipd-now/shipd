## ADDED Requirements

### Requirement: Plan metadata validation
id: plan-metadata-validation

When linting a change, the linter SHALL validate the plan's header metadata
block: it SHALL error on an unrecognized key in the block, on a value that is
not a kebab-case slug, on a `Profile:` value other than `full` or `lite`, on
a plan carrying both `Epic:` and `Initiative:` lines, and on a `Theme:` value
outside `valid_themes` when `am/config.json` declares a non-empty vocabulary.
A plan with no metadata block SHALL lint exactly as it did before this
feature.

#### Scenario: Unrecognized key errors
- **WHEN** a plan's metadata block contains `Them: reliability`
- **THEN** the linter reports an error naming the unrecognized key and exits
  non-zero

#### Scenario: Invalid profile value errors
- **WHEN** a plan carries `Profile: quick`
- **THEN** the linter reports an error naming the invalid profile value

#### Scenario: Epic with initiative errors
- **WHEN** a plan carries both `Epic:` and `Initiative:` lines
- **THEN** the linter reports an error stating the initiative must attach to
  the epic

#### Scenario: Theme outside declared vocabulary errors
- **GIVEN** `am/config.json` declares `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: speed`
- **THEN** the linter reports an error naming the invalid theme

#### Scenario: Metadata-free plans are unaffected
- **WHEN** a change whose plan has no metadata block is linted
- **THEN** no metadata error is reported and existing checks behave
  unchanged
