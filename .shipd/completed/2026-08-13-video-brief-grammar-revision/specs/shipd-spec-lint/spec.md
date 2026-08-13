## MODIFIED Requirements

### Requirement: Video brief lint mode
id: video-brief-validation
base: f593a6d7fcbb

`spec_lint.py` SHALL provide video brief checks callable in-process
(`lint_video(root, slug, errors)`) enforcing the video intent brief format — the
title line, the required `Video:` header line, the `## Intents` and
`## Sources` sections, the per-intent citation rule, the timestamped
source-entry rule, and citation-marker resolution with fenced code blocks
skipped — with every finding naming the brief file. The checks SHALL NOT require
a `## Speakers` section, and SHALL NOT require a source entry to name a speaker
after its timestamp. Where the brief's header carries a `Project:` line, the
checks SHALL validate its value against the workspace registry through the same
helper the initiative brief checks use, rather than re-implementing registry
validation; where no `Project:` line is present the registry SHALL NOT be
loaded. The checks SHALL reuse the existing citation-marker, section, and
numbered-source helpers rather than re-implementing them. Library linting SHALL
NOT walk the content directory's `video/` folder on its own, and no
`spec_lint.py` command-line mode SHALL expose these checks; they run only when
the emit engine installs a brief.

#### Scenario: Clean brief passes
- **WHEN** the video brief checks run on a brief with a title, a `Video:`
  header, cited intents, and timestamped numbered sources
- **THEN** no findings are produced

#### Scenario: A brief with no Speakers section produces no finding
- **WHEN** the checks run on a brief carrying no `## Speakers` section
- **THEN** no finding is produced

#### Scenario: A speaker-free source entry produces no finding
- **WHEN** the checks run on a brief whose source entry is a bracketed timestamp
  followed only by what was said
- **THEN** no finding is produced for that entry

#### Scenario: A Project line is validated against the registry
- **WHEN** the checks run on a brief carrying `Project:` naming a slug the
  workspace registry does not declare
- **THEN** a finding names the brief file and that value

#### Scenario: No Project line leaves the registry unread
- **WHEN** the checks run on a brief with no `Project:` line in a workspace
  whose registry declares no projects
- **THEN** no finding is produced and no registry validation is attempted

#### Scenario: Uncited intent is a named finding
- **WHEN** the checks run on a brief whose second intent carries no citation
  marker
- **THEN** a finding names the brief file and that intent

#### Scenario: Untimestamped source is a named finding
- **WHEN** the checks run on a brief whose source entry carries no bracketed
  timestamp
- **THEN** a finding names the brief file and that entry

#### Scenario: Unresolved marker is a named finding
- **WHEN** the checks run on a brief citing `[4]` over three listed sources
- **THEN** a finding names the brief file and the `[4]` marker

#### Scenario: Library lint ignores video briefs
- **WHEN** `spec_lint.py` lints the library while an invalid file sits under the
  content directory's `video/` folder
- **THEN** no video brief finding is produced
