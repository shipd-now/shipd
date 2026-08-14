## ADDED Requirements

### Requirement: Video intent brief format
id: video-brief-format

A video intent brief installed at `<content-dir>/video/<slug>/brief.md` SHALL
open with a non-empty level-1 title on its first line and SHALL carry a `Video:`
header line naming the source recording in the `Key: value` header block
immediately following the title; `Bundle:` and `Decider:` header lines are
optional. The brief SHALL carry a `## Speakers` section holding at least one
`- <name> — <label>` entry, an `## Intents` section holding at least one
level-3 intent heading, and a `## Sources` section holding at least one numbered
entry (`N. …`) whose text opens with a bracketed timestamp (`[HH:MM:SS]`,
fractional seconds permitted) followed by a speaker name. Every level-3 intent
SHALL carry at least one inline citation marker `[n]`, and every citation marker
outside fenced code blocks SHALL reference a number present in the sources list
(a bracketed number immediately followed by `(` is a markdown link, not a
marker). Where the brief carries `## Open questions` or `## Gaps & caveats`
sections they are optional and unvalidated, and an unrecognized level-2 section
SHALL NOT be an error. This format is enforced at engine install time.

#### Scenario: Conforming brief is accepted
- **WHEN** a brief with a title line, a `Video:` header, a speaker entry, one
  cited intent, and a timestamped source entry is checked
- **THEN** tooling reports no findings

#### Scenario: Missing Video header is rejected
- **WHEN** a brief carries a title and all required sections but no `Video:`
  header line
- **THEN** tooling reports the missing header as an error

#### Scenario: Uncited intent is rejected
- **WHEN** a brief carries a level-3 intent holding no `[n]` citation marker
- **THEN** tooling reports an error naming that intent

#### Scenario: Untimestamped source entry is rejected
- **WHEN** a brief's `## Sources` entry opens with a speaker name and no
  bracketed timestamp
- **THEN** tooling reports an error naming that entry

#### Scenario: Unresolved citation marker is rejected
- **WHEN** a brief cites `[4]` while its sources list holds three entries
- **THEN** tooling reports the unresolved marker as an error naming it

#### Scenario: Code blocks never trip the marker check
- **WHEN** a brief's fenced code block contains `items[0]` and its prose
  citations all resolve
- **THEN** tooling reports no findings

#### Scenario: Extra sections are permitted
- **WHEN** a brief carries an additional level-2 section beyond the required
  and optional ones
- **THEN** tooling reports no findings for that section
