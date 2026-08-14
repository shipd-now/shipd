## ADDED Requirements

### Requirement: Proposal header validation
id: proposal-header-validation

When linting a change, the linter SHALL report an error when the change's
`proposal.md` is missing; when its first line is not a `# <change-name>`
title matching the change's directory slug; when no `Status:` line appears
among the first five non-blank lines; or when the status value is not one of
`draft`, `ready`, `active`, `complete`, `verified`. Master-library linting
SHALL be unaffected.

#### Scenario: Missing status line fails lint
- **WHEN** a change's `proposal.md` has no `Status:` line in its first five
  non-blank lines
- **THEN** change lint reports an error and exits non-zero

#### Scenario: Invalid status value fails lint
- **WHEN** the proposal's status line reads `Status: in-progress`
- **THEN** change lint reports an error naming the invalid value

#### Scenario: Title must match the change slug
- **WHEN** change `dark-mode-toggle`'s proposal begins `# dark-mode`
- **THEN** change lint reports an error
