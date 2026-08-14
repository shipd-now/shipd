## ADDED Requirements

### Requirement: Epic research link validation
id: epic-research-link-validation

When an epic under lint (single-epic mode or library linting) carries a
`## Research` section, the linter SHALL resolve each list entry's link
target first relative to the epic's directory and then relative to the
repository root, and SHALL error — naming the link — when neither
resolution is an existing file under the content directory's `research/`
folder. A `## Research` section containing no link entries SHALL be an
error. Epics without the section SHALL produce no research-related
finding, and the linter SHALL NOT walk the `research/` folder itself.

#### Scenario: Resolvable links pass in both forms
- **GIVEN** `.shipd/research/payment-apis/report.md` exists
- **WHEN** an epic's `## Research` entries link it as
  `../../research/payment-apis/report.md` and another epic links it as
  `.shipd/research/payment-apis/report.md`
- **THEN** both epics lint clean

#### Scenario: Dead research link errors
- **WHEN** an epic's `## Research` entry links
  `../../research/missing/report.md` and no such file exists
- **THEN** the linter reports an error naming that link and exits non-zero

#### Scenario: Link outside the research folder errors
- **WHEN** an epic's `## Research` entry links an existing file that does
  not live under the content directory's `research/` folder
- **THEN** the linter reports an error naming that link

#### Scenario: Unlinked research files are ignored
- **GIVEN** a malformed file under `.shipd/research/` that no epic links
- **WHEN** library linting runs
- **THEN** no finding is produced for it
