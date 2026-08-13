# shipd-spec-lint — delta

## MODIFIED Requirements

### Requirement: Plan header and section validation
id: proposal-header-validation
base: 8dc02f4b3fac

When linting a change, the linter SHALL report an error when the change's
`plan.md` is missing; when its first line is not a `# <change-name>` title
matching the change's directory slug; when no `Status:` line appears among the
first five non-blank lines; when the status value is not one of `draft`,
`ready`, `active`, `complete`, `verified`; when the document lacks a level-2
`## Idea` section or a level-2 `## Implementation` section; or when it lacks a
level-3 `### Non-goals` heading. Master-library linting SHALL be unaffected.

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

#### Scenario: Missing non-goals heading fails lint
- **WHEN** a change's `plan.md` has both level-2 sections but no
  `### Non-goals` heading
- **THEN** change lint reports an error naming the missing `### Non-goals`
  subsection
