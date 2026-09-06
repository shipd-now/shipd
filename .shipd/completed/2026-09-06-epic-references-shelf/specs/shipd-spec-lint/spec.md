## ADDED Requirements

### Requirement: Epic References section links
id: epic-references-link-lint

If an epic under lint carries a `## References` section, the linter SHALL
resolve each list entry's link target — first relative to the epic's own
directory, then relative to the repository root — and SHALL report an error
naming each link that does not resolve to an existing file under the content
directory's `research/`, `video/`, or `docs/` folder. A `## References`
section containing no link entries SHALL be an error; an absent section SHALL
produce no finding and SHALL NOT cause any folder walk. The findings the
linter reports for `## Research` and `## Video` sections SHALL be unchanged
by the presence or absence of a `## References` section.

#### Scenario: A docs entry resolves
- **WHEN** an epic's `## References` entry links
  `../../docs/strategy-notes/doc.md` and that file exists
- **THEN** the epic lint reports no References finding

#### Scenario: All three kinds resolve in one section
- **WHEN** an epic's `## References` section links one existing file under
  each of `research/`, `video/`, and `docs/`
- **THEN** the epic lint reports no References finding

#### Scenario: A dead References link is an error
- **WHEN** an epic's `## References` entry links
  `../../docs/missing/doc.md` and no such file exists
- **THEN** the epic lint reports an error naming that link

#### Scenario: A link outside the reference folders is an error
- **WHEN** an epic's `## References` entry links an existing file that lives
  under none of the content directory's `research/`, `video/`, or `docs/`
  folders
- **THEN** the epic lint reports an error naming that link

#### Scenario: An empty References section is an error
- **WHEN** an epic carries a `## References` section with no
  `- [title](path)` entry
- **THEN** the epic lint reports the section as empty

#### Scenario: Absent section produces no finding
- **WHEN** an epic carries no `## References` section
- **THEN** no References finding is produced and no reference folder is
  walked for it

#### Scenario: Legacy section findings are unchanged
- **WHEN** an epic with a dead `## Research` link and a resolving
  `## References` section is linted
- **THEN** the `## Research` finding is reported exactly as it is without a
  `## References` section
