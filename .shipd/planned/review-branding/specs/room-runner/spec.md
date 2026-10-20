## ADDED Requirements

### Requirement: The CI-review read accepts the branded body
id: room-run-ci-branded-review

When an author run reads the CI reviewer's reviews of the head, a review whose body opens with the brand line `**☕ shipd** semantic review` SHALL be classified exactly as the same body without it: the last line equal to a verdict marker decides, so a branded fix-required review starts one turn and a branded ship-it review starts none.

#### Scenario: A branded fix-required review starts one turn
- **WHEN** the CI reviewer's review of the head opens with the brand line, then `## Findings: ❌ Fix required`, and ends with the fix-required marker
- **THEN** the run spends exactly one turn on it with the CI prompt

#### Scenario: A branded ship-it review starts nothing
- **WHEN** the CI reviewer's review of the head opens with the brand line and ends with the ship-it marker
- **THEN** the run spends no turn on it
