# shipd-spec-lint

### Requirement: Requirement structural validation
id: requirement-structural-validation

The linter SHALL verify that every content-bearing requirement block — in master
specs and in delta `ADDED`/`MODIFIED` sections — has an `id:` slug, at least one
normative statement using SHALL or MUST, and at least one `#### Scenario:` block.
A block missing any of these SHALL be reported as an error. Entries under
`REMOVED` and `RENAMED` are metadata-only references to existing requirements
and are exempt from the SHALL/scenario checks; they are validated by their own
metadata rules instead.

#### Scenario: Requirement without a scenario fails
- **WHEN** a requirement block has an `id` and a SHALL statement but no
  `#### Scenario:` block
- **THEN** the linter reports an error for that requirement

#### Scenario: Well-formed requirement passes
- **WHEN** a requirement block has an `id`, a SHALL/MUST statement, and at least
  one scenario
- **THEN** the linter reports no error for that requirement

### Requirement: Unique identifiers
id: unique-identifiers

The linter SHALL verify that `id:` slugs are unique within each capability's
master spec and within each delta file. Duplicate ids SHALL be reported as
errors.

#### Scenario: Duplicate id fails
- **WHEN** two requirement blocks in the same capability share the `id`
  `enforce-sso-timeout`
- **THEN** the linter reports a duplicate-id error

### Requirement: Delta header and scenario validity
id: delta-header-and-scenario-validity

The linter SHALL verify that delta specs use only the operation headers
`## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`,
and `## RENAMED Requirements`, and that every scenario uses exactly four
hashtags (`####`). Unknown operation headers or mis-leveled scenarios SHALL be
reported as errors.

#### Scenario: Unknown operation header fails
- **WHEN** a delta file contains a `## CHANGED Requirements` header
- **THEN** the linter reports an error for the unrecognized operation header

#### Scenario: Mis-leveled scenario fails
- **WHEN** a scenario is written with three hashtags (`###`) instead of four
- **THEN** the linter reports an error so the scenario is not silently ignored

### Requirement: Base-hash presence on edits
id: base-hash-presence-on-edits

The linter SHALL verify that every entry under `## MODIFIED Requirements` or
`## REMOVED Requirements` carries a `base:` line, so the merge engine's
concurrency check can run. A missing `base:` SHALL be reported as an error.

#### Scenario: Modified entry without a base hash fails
- **WHEN** a `## MODIFIED Requirements` entry has no `base:` line
- **THEN** the linter reports an error for that entry

### Requirement: Removal metadata
id: removal-metadata

The linter SHALL verify that every `## REMOVED Requirements` entry includes both
a `Reason` and a `Migration` note. A removal missing either SHALL be reported as
an error.

#### Scenario: Removal without migration fails
- **WHEN** a REMOVED entry has a Reason but no Migration note
- **THEN** the linter reports an error for that removal

### Requirement: Rename metadata
id: rename-metadata

The linter SHALL verify that every `## RENAMED Requirements` entry carries both a
`FROM:` id and a `TO:` id, and that the `TO:` id is a valid kebab-case slug. An
entry missing either side SHALL be reported as an error.

#### Scenario: Rename without a target fails
- **WHEN** a RENAMED entry has a `FROM:` id but no `TO:` id
- **THEN** the linter reports an error for that entry

### Requirement: Gating exit code
id: gating-exit-code

The linter SHALL exit with a non-zero status when any error is found and zero
when the specs are valid, so it can gate a build in the same role that
`openspec validate --strict` fills today.

#### Scenario: Errors produce a non-zero exit
- **WHEN** the linter finds at least one error
- **THEN** it exits with a non-zero status code

#### Scenario: Clean specs produce a zero exit
- **WHEN** the linter finds no errors across the target specs
- **THEN** it exits with status zero

### Requirement: Proposal header validation
id: proposal-header-validation

When linting a change, the linter SHALL report an error when the change's
`plan.md` is missing; when its first line is not a `# <change-name>` title
matching the change's directory slug; when no `Status:` line appears among
the first five non-blank lines; when the status value is not one of
`draft`, `ready`, `active`, `complete`, `verified`, `rejected`; when the
document lacks a level-2 `## Idea` section or a level-2 `## Implementation`
section; or when it lacks a level-3 `### Motivation`, `### Details`, or
`### Non-goals` heading. A gate-owned `## Context insufficient` section
SHALL be tolerated in any status. Master-library linting SHALL be
unaffected.

#### Scenario: Invalid status value fails lint
- **WHEN** the plan's status line reads `Status: in-progress`
- **THEN** change lint reports an error naming the invalid value

#### Scenario: Rejected status lints as valid
- **WHEN** a change's plan carries `Status: rejected` and a
  `## Context insufficient` section
- **THEN** neither produces a lint error

#### Scenario: Missing required section fails lint
- **WHEN** a change's `plan.md` has no `## Implementation` section
- **THEN** change lint reports an error naming the missing section

#### Scenario: Missing Idea subsection fails lint
- **WHEN** a change's `plan.md` has both level-2 sections and a
  `### Non-goals` heading but no `### Motivation` heading
- **THEN** change lint reports an error naming the missing `### Motivation`
  subsection

#### Scenario: Missing non-goals heading fails lint
- **WHEN** a change's `plan.md` has both level-2 sections but no
  `### Non-goals` heading
- **THEN** change lint reports an error naming the missing `### Non-goals`
  subsection

### Requirement: Context-economy warning
id: context-economy-warning

When linting a change, the linter SHALL emit a warning — never an error, and
never affecting the exit code — when the change's `plan.md` or any single
delta spec exceeds a context-economy budget of approximately 2,000 tokens,
estimated stdlib-only as one token per four characters. The warning SHALL name
the oversized file and recommend decomposing the change.

#### Scenario: Oversized plan warns but passes
- **WHEN** a change's `plan.md` is 12,000 characters and otherwise valid
- **THEN** the linter prints a warning naming `plan.md` and still exits zero

#### Scenario: Lean artifacts stay silent
- **WHEN** every artifact in a change is under the budget
- **THEN** the linter emits no context-economy warning

### Requirement: Task traceability tag enforcement
id: traceability-tag-enforcement

The linter SHALL error — not warn — for every checkbox task in a change's
`tasks.md` that lacks a well-formed `[req: ...]` traceability tag, carries more
than one tag, combines the wildcard `*` with requirement ids, or references an
id that does not resolve to a requirement id present in the change's own delta
specs (any operation header, any capability). Each violating task SHALL
produce its own error naming the task's ordinal position. A checkbox task is
a line whose content begins — after optional leading blanks — with the
`- [<state>]` marker (state space, `~`, or `x`): the same anchored grammar
the coordinator's ordinal ids count, so a checkbox-shaped literal appearing
mid-line inside a task's wrapped prose SHALL be neither counted as a task nor
required to carry a tag, and the linter's ordinals SHALL always match the
coordinator's.

#### Scenario: Missing tag is an error
- **WHEN** a task line has no `[req: ...]` tag
- **THEN** the linter reports an error for that task and exits non-zero

#### Scenario: Unresolvable id is an error
- **WHEN** a task carries `[req: no-such-requirement]` and no delta spec in
  the change declares that id
- **THEN** the linter reports an error naming the unresolvable id

#### Scenario: Well-tagged change lints clean
- **WHEN** every task carries either resolvable ids or a lone wildcard tag
- **THEN** the linter reports no traceability errors

#### Scenario: A checkbox literal in task prose is not a task
- **GIVEN** a tagged task whose wrapped description contains a backticked
  checkbox-marker literal on a continuation line
- **WHEN** the linter runs
- **THEN** no traceability error is reported for the literal, and the
  ordinals in any real errors still name the real tasks

### Requirement: Plan metadata validation
id: plan-metadata-validation

When linting a change, the linter SHALL validate the plan's header metadata
block: it SHALL error on an unrecognized key in the block, on a value that
is not a kebab-case slug, on a `Profile:` value other than `full` or `lite`,
on a plan carrying both `Epic:` and `Initiative:` lines, and on a `Theme:`
value outside `valid_themes` when the resolved layered configuration
declares a non-empty vocabulary. A plan with no metadata block SHALL lint
exactly as it did before this feature.

#### Scenario: Unrecognized key errors
- **WHEN** a plan's metadata block contains `Them: reliability`
- **THEN** the linter reports an error naming the unrecognized key and
  exits non-zero

#### Scenario: Theme outside declared vocabulary errors
- **GIVEN** the repo's `.shipd-config.json` declares
  `valid_themes: ["reliability"]`
- **WHEN** a plan carries `Theme: speed`
- **THEN** the linter reports an error naming the invalid theme

#### Scenario: Epic with initiative errors
- **WHEN** a plan carries both `Epic:` and `Initiative:` lines
- **THEN** the linter reports an error stating the initiative must attach
  to the epic

### Requirement: Epic structural validation
id: epic-structural-validation

The linter SHALL validate every epic under `.shipd/epics/` during library linting
and SHALL provide an `--epic <slug>` mode linting a single epic, enforcing the
epic artifact layout and header metadata rules (title, status vocabulary,
recognized keys, required sections, stub table shape). When linting a change
whose plan carries `Epic:`, the linter SHALL error on an unresolvable epic
reference and SHALL warn — never error — when the resolved epic's stub table
lacks the change's slug. A repository with no `.shipd/epics/` directory SHALL
lint exactly as before this feature.

#### Scenario: Library lint covers epics
- **WHEN** library linting runs in a repo whose `.shipd/epics/broken/epic.md` has
  no `## Changes` section
- **THEN** the linter reports the epic's error and exits non-zero

#### Scenario: Single-epic mode
- **WHEN** `--epic reporting-overhaul` runs against a conforming epic
- **THEN** the linter prints OK and exits zero

#### Scenario: Change lint resolves the epic reference
- **WHEN** a linted change carries `Epic: no-such-epic`
- **THEN** the linter reports an unresolvable-reference error and exits
  non-zero

#### Scenario: No epics directory changes nothing
- **WHEN** library linting runs in a repo without `.shipd/epics/`
- **THEN** no epic errors or warnings are emitted and the exit code is
  unaffected

### Requirement: Initiative lint mode
id: initiative-lint-mode

The linter SHALL provide an `--initiative <slug>` mode validating a single
brief's structure per the initiative brief artifact rules at the workspace's
resolved brief path (`<ws>/<content-dir>/initiatives/<slug>/brief.md`),
resolving the workspace from `--root`; when no workspace root is
discoverable, the mode SHALL exit non-zero with an error saying no workspace
was found. Library and change linting SHALL NOT walk the workspace's
initiatives directory — briefs enter repo lint only through the CI-safe
`Initiative:` reference resolution.

#### Scenario: Valid brief lints clean
- **GIVEN** a discoverable workspace with a conforming
  `.shipd/initiatives/mvp-readiness/brief.md`
- **WHEN** `--initiative mvp-readiness` runs
- **THEN** the linter prints OK and exits zero

#### Scenario: No workspace fails the mode
- **WHEN** `--initiative mvp-readiness` runs where no workspace root is
  discoverable
- **THEN** the linter exits non-zero saying no workspace was found

### Requirement: Workspace lint mode
id: workspace-lint-mode

The linter SHALL provide a `--workspace` mode that resolves the workspace
from `--root` and reports the registry-validation findings against the
workspace root's `.shipd-config.json` `workspace` object, exiting zero on a
clean registry and non-zero otherwise; when no workspace root is
discoverable, the mode SHALL exit non-zero saying no workspace was found.
Library and change linting SHALL remain registry-silent except where a
brief's `Project:` line requires the registry.

#### Scenario: Clean registry passes
- **GIVEN** a discoverable workspace whose registry validates clean
- **WHEN** `--workspace` runs
- **THEN** the linter prints OK and exits zero

#### Scenario: Registry findings name the config file
- **WHEN** `--workspace` runs against a registry with a duplicate repo path
- **THEN** the error is reported naming `.shipd-config.json` and the exit code
  is non-zero

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

### Requirement: Research report validation
id: research-report-validation

`spec_lint.py` SHALL provide research report checks callable in-process
(`lint_research(root, slug, errors)`) that always enforce a non-empty
`# <title>` on the report's first line. Where the report carries a citation
signal — a `## Sources` section, or at least one inline `[n]` citation marker
outside fenced code blocks — the checks SHALL additionally enforce the full
citation skeleton: the numbered `## Sources` section, the at-least-one-marker
rule, and citation-marker resolution with fenced code blocks skipped. If the
report carries neither signal, then only the title check SHALL apply and a
titled report SHALL produce no findings. Every finding SHALL name the report
file. Library linting SHALL NOT walk the content directory's `research/`
folder on its own; the checks run only when the emit engine installs a report.

#### Scenario: Uncited titled document passes
- **WHEN** the research checks run on a report whose first line is a
  non-empty `# <title>` and which carries no `## Sources` section and no
  inline `[n]` markers
- **THEN** no findings are produced

#### Scenario: Cited report is still fully checked
- **WHEN** the research checks run on a report citing `[4]` over three listed
  sources
- **THEN** a finding names the report file and the `[4]` marker

#### Scenario: Markers without a sources section are still rejected
- **WHEN** the research checks run on a report carrying inline `[n]` markers
  but no `## Sources` section
- **THEN** a finding reports the missing `## Sources` section

#### Scenario: Library lint ignores research files
- **WHEN** `spec_lint.py` lints the library while an invalid file sits under
  the content directory's `research/` folder
- **THEN** no research finding is produced

### Requirement: Wiki lint mode
id: wiki-lint-mode

The linter SHALL provide a `--wiki` mode that validates the workspace wiki
store against the shipd-wiki grammar: layout file presence (`schema.md`,
`index.md`, `log.md`, `queue.md`), reserved page slugs, wikilink resolution
outside fenced code blocks, bidirectional index coverage, log header format,
and queue block fields. When no workspace is discoverable from the lint root,
the mode SHALL exit non-zero explaining that `--wiki` requires a workspace,
mirroring the `--workspace` mode's behavior. Findings and exit codes SHALL
follow the linter's existing gating contract.

#### Scenario: Clean store passes
- **WHEN** `spec_lint.py --wiki` runs against a store satisfying the grammar
- **THEN** it prints an OK line and exits zero

#### Scenario: Violations gate
- **WHEN** the store contains a dead wikilink and an unindexed page
- **THEN** the mode prints one finding per violation and exits non-zero

#### Scenario: No workspace
- **WHEN** `--wiki` runs where no workspace is discoverable
- **THEN** it exits non-zero naming the missing workspace

### Requirement: Video brief lint mode
id: video-brief-validation

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

### Requirement: Questions-and-answers section validation
id: qa-section-validation

When a change's `plan.md` carries a `## Questions and answers` section, the
linter SHALL report an error naming the offending entry for: a section holding
no entries, an entry header not matching `### Q<n>: <summary>`, entry numbers
not sequential starting at `Q1`, and an entry missing a `**Question:**`,
`**Answered by:**`, or `**Answer:**` field. When the section is absent, the
linter SHALL report no finding for it.

#### Scenario: Absent section lints clean
- **WHEN** a plan carries no `## Questions and answers` section
- **THEN** the lint reports no questions-and-answers finding

#### Scenario: Malformed entry is an error
- **WHEN** a plan's `## Questions and answers` section holds an entry headed
  `### Q2:` with no `Q1` entry before it, or an entry lacking an
  `**Answer:**` field
- **THEN** the lint exits non-zero with an error naming the offending entry

#### Scenario: Conforming section passes
- **WHEN** a plan's section holds `### Q1:` and `### Q2:` entries each
  carrying `**Question:**`, `**Answered by:**`, and `**Answer:**` fields
- **THEN** the lint reports no questions-and-answers finding

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

### Requirement: Lint JSON output
id: lint-json

`spec_lint.py` SHALL accept a `--json` flag that emits one JSON object on
stdout — `ok` (boolean), `errors` (array of finding strings), and `warnings`
(array of warning strings), carrying the same texts the flagless mode
prints — and nothing else on stdout. The exit code SHALL be identical to
the flagless mode for the same findings, and without the flag the text
output SHALL stay byte-identical.

#### Scenario: A clean lint is machine-readable
- **WHEN** `spec_lint.py --json` runs over a valid library
- **THEN** stdout parses as `{"ok": true, "errors": [], "warnings": [...]}`
  and the exit code is 0

#### Scenario: Findings land in the errors array
- **WHEN** `spec_lint.py <change> --json` runs on a change with a structural
  error
- **THEN** the object's `ok` is false, the error string appears in
  `errors`, and the exit code is nonzero exactly as without the flag

### Requirement: Artefact reference enforcement
id: artefact-reference-enforcement

Where a change carries an `artefacts/` directory, the linter's change checks
SHALL error — not warn — for every file inside it whose change-relative path
appears in none of `plan.md`, `tasks.md`, or the change's delta specs, naming
the unreferenced artefact and its path. A file is referenced when its
change-relative POSIX path (`artefacts/<file>`, including any nested
directories) occurs anywhere in the text of those artifacts. Because the emit
engine installs only after the change checks pass, an unreferenced artefact
SHALL therefore prevent the change from being installed. A change with no
`artefacts/` directory, or one holding no files, SHALL lint exactly as it does
without this check.

#### Scenario: Unreferenced artefact is an error
- **GIVEN** a change whose `artefacts/policy.md` is named nowhere in its
  artifacts
- **WHEN** the change is linted
- **THEN** the linter reports an error naming `artefacts/policy.md` and exits
  non-zero

#### Scenario: Referenced artefact lints clean
- **GIVEN** a change whose `plan.md` names `artefacts/policy.md`
- **WHEN** the change is linted
- **THEN** no artefact finding is reported

#### Scenario: An unreferenced artefact blocks the install
- **WHEN** a staging directory carrying an unreferenced `artefacts/policy.md`
  is installed with `spec_emit.py change`
- **THEN** the finding is printed, the command exits non-zero, and the spec
  tree gains no change directory

#### Scenario: A change without artefacts is unaffected
- **GIVEN** a change with no `artefacts/` directory
- **WHEN** the change is linted
- **THEN** the findings are exactly those the other change checks produce

### Requirement: Docs document validation
id: docs-document-validation

`spec_lint.py` SHALL provide docs document checks callable in-process
(`lint_docs(root, slug, errors)`) that enforce exactly one rule on the
document at `<content-dir>/docs/<slug>/doc.md`: a non-empty `# <title>` on
the document's first line. The checks SHALL NOT demand any citation
skeleton, header metadata, or section structure — an installed document's
body is free-form, so a supplied document never fails on a provenance or
structure grammar it did not claim. Every finding SHALL name the document
file. If the document file is missing, then the checks SHALL report that as
a finding naming the expected path. Library linting SHALL NOT walk the
content directory's `docs/` folder on its own, and the checks SHALL have no
`spec_lint.py` command-line mode; they run only when the emit engine
installs a document.

#### Scenario: Titled free-form document passes
- **WHEN** the docs checks run on a document whose first line is a non-empty
  `# <title>` and whose body is arbitrary markdown, including `[1]`-style
  bracket markers and no `## Sources` section
- **THEN** no findings are produced

#### Scenario: Untitled document is rejected
- **WHEN** the docs checks run on a document whose first line is not a
  non-empty `# <title>`
- **THEN** a finding names the document file and the expected title line

#### Scenario: Library lint ignores docs files
- **WHEN** `spec_lint.py` lints the library while an untitled file sits
  under the content directory's `docs/` folder
- **THEN** no docs finding is produced

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

### Requirement: PRD lint mode
id: prd-lint-mode

The linter SHALL provide a `--prd <slug>` mode validating a single PRD's
structure per the PRD store grammar and its declared tier's section contract
at the workspace's resolved PRD path
(`<ws>/<content-dir>/prds/<slug>/prd.md`), resolving the workspace from
`--root`; when no workspace root is discoverable, the mode SHALL exit
non-zero with an error saying no workspace was found. Library and change
linting SHALL NOT walk the workspace's prds directory.

#### Scenario: Valid PRD lints clean
- **GIVEN** a discoverable workspace whose `prds/mobile-push/prd.md`
  conforms to the grammar and its `Template: basic` section contract
- **WHEN** `spec_lint.py --prd mobile-push` runs
- **THEN** it exits `0` and prints an OK line

#### Scenario: Violations are reported with the PRD path
- **WHEN** `--prd` runs against a PRD missing its tier's `## Non-goals`
  section
- **THEN** the finding names the missing section and the PRD's file path,
  and the exit code is non-zero

#### Scenario: No workspace is an error
- **WHEN** `--prd mobile-push` runs from a root with no discoverable
  workspace
- **THEN** the linter exits non-zero with an error saying no workspace was
  found from that root

#### Scenario: Library lint ignores the prds directory
- **WHEN** a malformed PRD exists in the workspace and the repo's library
  lint runs with no mode flag
- **THEN** the library lint result is unaffected by the PRD

### Requirement: Task group satisfiability
id: task-group-satisfiability

The linter SHALL refuse a change whose `tasks.md` carries a `[P<n>]` group
configuration under which some task can never become claimable. It SHALL
determine this from the group configuration alone, independently of the
tasks' current checkbox states: before applying the readiness rule it SHALL
treat every task as pending, so a task claimed or completed by a build in
progress can neither mask nor manufacture a finding. It SHALL then apply the
coordinator's own readiness rule — a barrier (untagged) task becomes ready
only once every task before it in file order is done, and a grouped task only
once every barrier before it is done and every task in a strictly-lower-
numbered group anywhere in the file is done — repeatedly marking every ready
pending task done until no further task becomes ready. Any task still pending
when that drain stalls SHALL be reported as an error naming the task by its
checkbox ordinal, the same stable id the coordinator hands out. A tasks file
that drains completely SHALL produce no finding, and a change with no
`tasks.md` SHALL be a no-op for this check. The linter's readiness rule SHALL
be pinned to the coordinator's by a test that compares the two
implementations' ready sets over a corpus of tag configurations, so the
authoring-time check and the runtime claiming can never disagree.

#### Scenario: A readiness cycle is refused
- **GIVEN** a tasks file in which a `[P3]` task precedes an untagged barrier
  that itself precedes a `[P2]` task
- **WHEN** the linter runs on that change
- **THEN** it reports an error naming the tasks that can never become ready
  and exits non-zero

#### Scenario: The barrier idiom still passes
- **GIVEN** a tasks file whose untagged barrier sits between `[P1]` and
  `[P2]` tasks
- **WHEN** the linter runs
- **THEN** it reports no satisfiability finding

#### Scenario: Monotonic grouping passes
- **GIVEN** a tasks file in which every task carries a group tag and the
  group numbers never decrease down the file
- **WHEN** the linter runs
- **THEN** it reports no satisfiability finding

#### Scenario: A fully sequential file passes
- **GIVEN** a tasks file in which no task carries a group tag
- **WHEN** the linter runs
- **THEN** it reports no satisfiability finding

#### Scenario: Already-done tasks do not mask a cycle
- **GIVEN** a tasks file whose earlier tasks are marked done and whose
  remaining pending tasks form a readiness cycle
- **WHEN** the linter runs
- **THEN** it still reports the cycle, since the drain normalizes every task
  to pending and so reads the group configuration rather than the file's
  recorded box states

#### Scenario: The two readiness implementations agree
- **WHEN** the parity test runs each configuration in its corpus through both
  the linter's readiness rule and the coordinator's
- **THEN** the two report the same ready set for every configuration

#### Scenario: An in-progress claim reports no finding
- **GIVEN** a sound tasks file whose untagged barrier follows a `[P1]` task
  marked `[x]` and a `[P2]` task marked `[~]` by a running build
- **WHEN** the linter runs on that change
- **THEN** it reports no satisfiability finding

#### Scenario: A broken configuration is refused whatever its progress
- **GIVEN** a tasks file whose `[P3]` task precedes an untagged barrier that
  precedes a `[P2]` task, with every task already marked `[x]`
- **WHEN** the linter runs on that change
- **THEN** it still reports an error naming the tasks that can never become
  ready

### Requirement: MODIFIED scenario retention
id: modified-scenario-retention

The linter SHALL refuse a change whose `## MODIFIED Requirements` entry omits
a `#### Scenario:` title its base master requirement carries, unless the entry
names that title in a `Dropped:` line. Because a MODIFIED entry replaces the
master requirement's content wholesale, an unnamed omission deletes that
scenario on merge, so the linter SHALL report one error per omitted title,
naming the requirement id and each title. The linter SHALL match scenarios by
exact title text, so rewording a scenario's body in place is never reported.
If a `Dropped:` line names a title the base requirement does not carry, then
the linter SHALL report that as an error too, so a stale or misspelled line
never appears to license an omission it does not. Where a MODIFIED entry's
`id` has no matching master requirement, the linter SHALL skip this check for
that entry, since there are no base scenarios to retain.

#### Scenario: A silently dropped scenario is refused
- **GIVEN** a master requirement carrying four scenarios
- **WHEN** a MODIFIED entry for it restates two of them and carries no
  `Dropped:` line
- **THEN** the linter reports an error naming the requirement id and the two
  omitted scenario titles, and exits non-zero

#### Scenario: A named drop is allowed
- **GIVEN** a master requirement carrying four scenarios
- **WHEN** a MODIFIED entry restates three of them and carries a `Dropped:`
  line naming the fourth
- **THEN** the linter reports no retention finding

#### Scenario: Rewording a scenario body is not a drop
- **WHEN** a MODIFIED entry restates every scenario title its base carries but
  changes the WHEN/THEN text of one
- **THEN** the linter reports no retention finding

#### Scenario: A stale Dropped line is refused
- **WHEN** a MODIFIED entry carries a `Dropped:` line naming a title its base
  requirement does not carry
- **THEN** the linter reports an error naming that title and exits non-zero

#### Scenario: A MODIFIED entry with no master is skipped
- **WHEN** a MODIFIED entry's `id` matches no requirement in the master library
- **THEN** the linter reports no retention finding for that entry
