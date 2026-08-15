## ADDED Requirements

### Requirement: Epic video link validation
id: epic-video-link-validation

When an epic under lint (single-epic mode or library linting) carries a
`## Video` section, the linter SHALL resolve each list entry's link target
first relative to the epic's directory and then relative to the repository
root, and SHALL error — naming the link — when neither resolution is an
existing file under the content directory's `video/` folder. A `## Video`
section containing no link entries SHALL be an error. Epics without the section
SHALL produce no video-related finding, and the linter SHALL NOT walk the
`video/` folder itself. The findings the linter reports for a `## Research`
section SHALL be unchanged in wording and in resolution order.

#### Scenario: Resolvable links pass in both forms
- **GIVEN** `.shipd/video/kickoff-call/brief.md` exists
- **WHEN** one epic's `## Video` entry links it as
  `../../video/kickoff-call/brief.md` and another epic links it as
  `.shipd/video/kickoff-call/brief.md`
- **THEN** both epics lint clean

#### Scenario: Dead video link errors
- **WHEN** an epic's `## Video` entry links `../../video/missing/brief.md` and
  no such file exists
- **THEN** the linter reports an error naming that link and exits non-zero

#### Scenario: Link outside the video folder errors
- **WHEN** an epic's `## Video` entry links an existing file that does not live
  under the content directory's `video/` folder
- **THEN** the linter reports an error naming that link

#### Scenario: Empty video section errors
- **WHEN** an epic carries a `## Video` section with no `- [title](path)` entry
- **THEN** the linter reports the section as having no link entries and exits
  non-zero

#### Scenario: Unlinked brief files are ignored
- **GIVEN** a malformed file under `.shipd/video/` that no epic links
- **WHEN** library linting runs
- **THEN** no finding is produced for it

#### Scenario: Research findings are unchanged
- **WHEN** an epic with a dead `## Research` link is linted
- **THEN** the reported finding is identical to the one reported before video
  link validation existed
