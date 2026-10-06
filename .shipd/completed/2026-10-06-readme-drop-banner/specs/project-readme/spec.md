## MODIFIED Requirements

### Requirement: README opens with the shipd brand and introduction
id: readme-displays-the-shipd-banner
base: 563c1698c0cc
Dropped: Banner is the first content
Dropped: Banner is preformatted
Dropped: What-it-is precedes mechanics

The `README.md` at the repository root SHALL open with the brand icon and a
short what-it-is introduction (at most a few sentences) before any
installation or mechanics content, and SHALL NOT carry a fenced ASCII-art
banner above that introduction.

#### Scenario: No banner precedes the introduction
- **WHEN** a reader opens `README.md`
- **THEN** no fenced code block appears before the introduction paragraph

#### Scenario: Introduction precedes mechanics
- **WHEN** a reader opens `README.md`
- **THEN** a short prose introduction states what shipd is before any install
  or engine documentation appears

### Requirement: README carries the brand marks
id: readme-brand-marks
base: dfdf2dbd9321
Dropped: Icon is displayed without displacing the banner

The repository SHALL keep the coffee-cup vector brand as `icon.svg` at the repository root, and `README.md` SHALL display it via an `img` element referencing that file as its first rendered element. The README introduction SHALL present the product name with the ☕ brand mark directly before it, and the linked `docs/what-is-shipd.md` SHALL open its level-1 title with the same mark.

#### Scenario: Icon opens the README
- **WHEN** `README.md` is rendered
- **THEN** its first element is an `img` element referencing the repo-root `icon.svg`, floating beside the introduction

#### Scenario: Intro carries the mark
- **WHEN** a reader reaches the README introduction
- **THEN** the bold product name is directly preceded by `☕`

#### Scenario: What-is doc opens branded
- **WHEN** `docs/what-is-shipd.md` is rendered
- **THEN** its level-1 title opens with `☕` before the question naming the product
