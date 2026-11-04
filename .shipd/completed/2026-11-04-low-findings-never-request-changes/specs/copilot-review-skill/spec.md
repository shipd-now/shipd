## ADDED Requirements

### Requirement: A fix-required review with no counted blocking finding passes
id: gate-nonblocking-fix-required-greens

The review-gate workflow SHALL classify each entry of its reviewer's findings
file (`$RUNNER_TEMP/shipd-copilot-review-findings.json`) against the diff it
read itself. An entry SHALL be *already there* when it carries a `category`
other than `untouched-caller` or `spec-coverage`, a string `path` and integer
`start_line`/`end_line`, and no line of that range is touched; a line SHALL be
touched when the path is one of the pull request's files and either that file
carries no readable patch or the line is a RIGHT-side line inside one of its
hunks. Where the diff could not be read, no entry SHALL be already there.

If the reviewer ends a grounded review with the `fix-required` marker, the
findings file is a non-empty JSON array, every entry is `low` or already
there, and the number of review-body lines containing `🔴 high` or `🟠 med`
does not exceed the number of `high` or `medium` already-there entries, then
the workflow SHALL post the `semantic-review` status `success` with the
description `Copilot code review: ship it (only low or already-there
findings).`, SHALL submit `APPROVE` where it would otherwise have submitted
`REQUEST_CHANGES`, and SHALL open the posted body, below its brand line, with
a gate note saying the fix-required verdict does not block because every
finding is low or already there, reached by this change. In every other case
the marker's `failure` SHALL stand. The workflow SHALL NOT turn a `ship-it`
marker into `failure`. The body SHALL be read from a workspace file, never
through a pipe.

The posting step SHALL fold already-there entries into a `### Already there,
reached by this change` body section, each with its severity dot, and SHALL
NOT list them under "Findings not anchored to the diff". The Copilot review
contract (`integrations/copilot/SKILL.md`) SHALL add `category` to the
findings file's fields, state the already-there rule in its verdict rule, and
state this exception where it says which signal gates the merge.

#### Scenario: Only low findings greens a fix-required marker
- **WHEN** the reviewer ends with the fix-required marker, its findings file
  lists two `low` findings, and its summary table rates both low
- **THEN** the status is `success` with the new description and the review
  event is `APPROVE`

#### Scenario: A high finding in an untouched file greens with the note
- **WHEN** the reviewer ends with the fix-required marker for a docs-only pull
  request, and its findings file lists one `high` `security` finding in a
  script the pull request does not change, with one `🔴 high` table row
- **THEN** the status is `success`, the posted body carries the gate note,
  and the finding is listed under `Already there, reached by this change`

#### Scenario: A medium on a changed line keeps the failure
- **WHEN** the reviewer ends with the fix-required marker and its findings
  file lists one `low` finding and one `medium` finding inside a hunk
- **THEN** the status is `failure`

#### Scenario: An uncategorized off-diff finding keeps the failure
- **WHEN** the only blocking entry lies in an untouched file but carries no
  `category`
- **THEN** the status is `failure`

#### Scenario: A broken untouched caller keeps the failure
- **WHEN** the only blocking entry lies in an untouched file with category
  `untouched-caller`
- **THEN** the status is `failure`

#### Scenario: A missing findings file keeps the failure
- **WHEN** the reviewer ends with the fix-required marker and wrote no
  findings file
- **THEN** the status is `failure`

#### Scenario: A body rating more blocking findings keeps the failure
- **WHEN** the findings file lists only `low` findings but the body's summary
  table carries a `🟠 med` row
- **THEN** the status is `failure`

#### Scenario: An ungrounded review is never reclassified
- **WHEN** the review is ungrounded and its findings file lists only `low`
  findings
- **THEN** the status stays `pending`
