## ADDED Requirements

### Requirement: Board brand mark
id: board-brand-mark

The `tui` board's header-bar brand block SHALL open with the ☕ coffee-cup brand mark directly before the accent-styled `shipd` label, keeping the muted `delivery board` label beside it and every other header-bar zone unchanged.

#### Scenario: Header brand block carries the mark
- **WHEN** the `tui` app mounts its header bar
- **THEN** the brand block's content begins with `☕` followed by the accent-styled `shipd`
