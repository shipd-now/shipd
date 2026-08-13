# shipd-spec-lint — delta

## ADDED Requirements

### Requirement: Context-economy warning
id: context-economy-warning

When linting a change, the linter SHALL emit a warning — never an error, and
never affecting the exit code — when the change's `plan.md` or any single
delta spec exceeds a context-economy budget of approximately 2,000 tokens,
estimated stdlib-only as one token per four characters. The warning SHALL name
the oversized file and recommend decomposing the change.

#### Scenario: Oversized plan warns but passes
- **WHEN** a change's `plan.md` is 12,000 characters and otherwise valid
- **THEN** the linter prints a warning naming `plan.md` and still exits zero

#### Scenario: Lean artifacts stay silent
- **WHEN** every artifact in a change is under the budget
- **THEN** the linter emits no context-economy warning

## MODIFIED Requirements

### Requirement: Plan header and section validation
id: proposal-header-validation
base: 8ace5c68e04a

When linting a change, the linter SHALL report an error when the change's
`plan.md` is missing; when its first line is not a `# <change-name>` title
matching the change's directory slug; when no `Status:` line appears among the
first five non-blank lines; when the status value is not one of `draft`,
`ready`, `active`, `complete`, `verified`; or when the document lacks a
level-2 `## Idea` section or a level-2 `## Implementation` section.
Master-library linting SHALL be unaffected.

#### Scenario: Missing status line fails lint
- **WHEN** a change's `plan.md` has no `Status:` line in its first five
  non-blank lines
- **THEN** change lint reports an error and exits non-zero

#### Scenario: Invalid status value fails lint
- **WHEN** the plan's status line reads `Status: in-progress`
- **THEN** change lint reports an error naming the invalid value

#### Scenario: Title must match the change slug
- **WHEN** change `dark-mode-toggle`'s plan begins `# dark-mode`
- **THEN** change lint reports an error

#### Scenario: Missing required section fails lint
- **WHEN** a change's `plan.md` has no `## Implementation` section
- **THEN** change lint reports an error naming the missing section
