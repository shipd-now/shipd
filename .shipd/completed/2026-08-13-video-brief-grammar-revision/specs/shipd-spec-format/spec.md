## MODIFIED Requirements

### Requirement: Video brief format
id: video-brief-format
base: e317089758c7

A video intent brief installed at `<content-dir>/video/<slug>/brief.md` SHALL
open with a non-empty level-1 title on its first line and SHALL carry a `Video:`
header line naming the source recording in the `Key: value` header block
immediately following the title; `Bundle:` and `Project:` header lines are
optional. Where a `Project:` line is present its value SHALL name a project slug
declared in the workspace registry; where it is absent the registry SHALL NOT be
consulted. The brief SHALL carry an `## Intents` section holding at least one
level-3 intent heading, and a `## Sources` section holding at least one numbered
entry (`N. …`) whose text opens with a bracketed timestamp (`[HH:MM:SS]`,
fractional seconds permitted). A source entry SHALL NOT be required to name a
speaker. Every level-3 intent SHALL carry at least one inline citation marker
`[n]`, and every citation marker outside fenced code blocks SHALL reference a
number present in the sources list (a bracketed number immediately followed by
`(` is a markdown link, not a marker). The brief SHALL NOT be required to carry
a `## Speakers` section. Where the brief carries `## Open questions` or
`## Gaps & caveats` sections they are optional and unvalidated, and an
unrecognized level-2 section SHALL NOT be an error. This format is enforced at
engine install time.

#### Scenario: Conforming brief is accepted
- **WHEN** a brief with a title line, a `Video:` header, one cited intent, and a
  timestamped source entry is checked
- **THEN** tooling reports no findings

#### Scenario: Missing Video header is rejected
- **WHEN** a brief carries a title and all required sections but no `Video:`
  header line
- **THEN** tooling reports the missing header as an error

#### Scenario: A brief with no Speakers section is accepted
- **WHEN** an otherwise conforming brief carries no `## Speakers` section
- **THEN** tooling reports no findings

#### Scenario: A speaker-free source entry is accepted
- **WHEN** a source entry opens with a bracketed timestamp followed only by what
  was said, naming no speaker
- **THEN** tooling reports no findings for that entry

#### Scenario: A brief without a Project line stays valid
- **WHEN** an otherwise conforming brief carries no `Project:` header line
- **THEN** tooling reports no findings and the workspace registry is not
  consulted

#### Scenario: An undeclared project is rejected
- **WHEN** a brief carries `Project:` naming a slug the workspace registry does
  not declare
- **THEN** tooling reports an error naming that value

#### Scenario: Uncited intent is rejected
- **WHEN** a brief carries a level-3 intent holding no `[n]` citation marker
- **THEN** tooling reports an error naming that intent

#### Scenario: Untimestamped source entry is rejected
- **WHEN** a brief's `## Sources` entry opens with no bracketed timestamp
- **THEN** tooling reports an error naming that entry

#### Scenario: Unresolved citation marker is rejected
- **WHEN** a brief cites `[4]` while its sources list holds three entries
- **THEN** tooling reports the unresolved marker as an error naming it

#### Scenario: Code blocks never trip the marker check
- **WHEN** a brief's fenced code block contains `items[0]` and its prose
  citations all resolve
- **THEN** tooling reports no findings

#### Scenario: A retained Speakers section is not an error
- **WHEN** a previously installed brief still carries a `## Speakers` section
- **THEN** tooling treats it as an unrecognized level-2 section and reports no
  findings
