## ADDED Requirements

### Requirement: Video brief lint mode
id: video-brief-validation

`spec_lint.py` SHALL provide video brief checks callable in-process
(`lint_video(root, slug, errors)`) enforcing the video intent brief format — the
title line, the required `Video:` header line, the `## Speakers`, `## Intents`,
and `## Sources` sections, the per-intent citation rule, the timestamped
source-entry rule, and citation-marker resolution with fenced code blocks
skipped — with every finding naming the brief file. The checks SHALL reuse the
existing citation-marker, section, and numbered-source helpers rather than
re-implementing them. Library linting SHALL NOT walk the content directory's
`video/` folder on its own, and no `spec_lint.py` command-line mode SHALL expose
these checks; they run only when the emit engine installs a brief.

#### Scenario: Clean brief passes
- **WHEN** the video brief checks run on a brief with a title, a `Video:`
  header, a speaker entry, cited intents, and timestamped numbered sources
- **THEN** no findings are produced

#### Scenario: Uncited intent is a named finding
- **WHEN** the video brief checks run on a brief whose second intent carries no
  citation marker
- **THEN** a finding names the brief file and that intent

#### Scenario: Untimestamped source is a named finding
- **WHEN** the video brief checks run on a brief whose source entry carries no
  bracketed timestamp
- **THEN** a finding names the brief file and that entry

#### Scenario: Unresolved marker is a named finding
- **WHEN** the video brief checks run on a brief citing `[4]` over three listed
  sources
- **THEN** a finding names the brief file and the `[4]` marker

#### Scenario: Library lint ignores video briefs
- **WHEN** `spec_lint.py` lints the library while an invalid file sits under the
  content directory's `video/` folder
- **THEN** no video brief finding is produced
