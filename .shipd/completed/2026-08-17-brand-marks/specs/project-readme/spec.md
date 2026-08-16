## ADDED Requirements

### Requirement: README carries the brand marks
id: readme-brand-marks

The repository SHALL keep the coffee-cup vector brand as `icon.svg` at the repository root, and `README.md` SHALL display it via an `img` element referencing that file, placed after the fenced ASCII banner so the banner remains the first rendered block. The README introduction SHALL present the product name with the ☕ brand mark directly before it, and the linked `docs/what-is-shipd.md` SHALL open its level-1 title with the same mark.

#### Scenario: Icon is displayed without displacing the banner
- **WHEN** `README.md` is rendered
- **THEN** the fenced ASCII banner is still the first rendered block, and an `img` element referencing the repo-root `icon.svg` floats beside the top content

#### Scenario: Intro carries the mark
- **WHEN** a reader reaches the README introduction
- **THEN** the bold product name is directly preceded by `☕`

#### Scenario: What-is doc opens branded
- **WHEN** `docs/what-is-shipd.md` is rendered
- **THEN** its level-1 title opens with `☕` before the question naming the product
