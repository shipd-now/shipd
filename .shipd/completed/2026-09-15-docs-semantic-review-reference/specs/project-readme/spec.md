# project-readme

## ADDED Requirements

### Requirement: Semantic review reference
id: semantic-review-reference-doc

`docs/semantic-review-reference.md` SHALL be a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250 lines or
fewer and passing `docs_lint.py`. It SHALL open by naming
`docs/semantic-review.md` as its concept guide, and SHALL carry three sections:
the `--json` finding payload, the `lint` configuration key, and the `prior`
verb's output.

The payload section SHALL list every field of a finding — `id`, `severity`,
`category`, `location`, `what`, `why`, `fix`, `status`, `note` and the optional
`suggestion` — and SHALL name all ten `category` values: `bug`, `contract`,
`edge-case`, `untouched-caller`, `spec-coverage`, `test-coverage`, `security`,
`performance`, `stability` and `data-integrity`. It SHALL state that `verdict`
is `changes-requested` when any finding is high or medium and `pass` otherwise,
and SHALL state the conditions a `suggestion` must meet to be committed rather
than degraded to prose.

The configuration section SHALL name both members of the `lint` key —
`run_scripts`, a boolean defaulting to false, and `disable`, a list of linter
names — and SHALL state each default.

The `prior` section SHALL list the fields each entry carries — `hash`, `path`,
`severity`, `what`, `thread_id`, `resolved` and `disposition` — and SHALL name
all four dispositions: `replied`, `autoreplied`, `commit-only` and `none`. It
SHALL state which one suppresses a recurrence and that the other three do not.
It SHALL state that a thread posted before the identity marker reports `hash`
as null, and that a null hash matches nothing.

`docs/semantic-review.md` SHALL link to this reference.

#### Scenario: The reference passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review-reference.md` runs
- **THEN** it exits `0`, and the file is 250 lines or fewer opening with the
  reference marker

#### Scenario: Every category value is listed
- **WHEN** the reference's payload section is inspected
- **THEN** it names all ten `category` values

#### Scenario: The verdict rule and the suggestion conditions are stated
- **WHEN** the payload section is inspected
- **THEN** it states that any high or medium finding makes the verdict
  `changes-requested`, and states what a `suggestion` must satisfy to be
  committed

#### Scenario: Both lint members carry their defaults
- **WHEN** the configuration section is inspected
- **THEN** it names `run_scripts` and `disable` with each one's default

#### Scenario: All four dispositions are named with their effect
- **WHEN** the `prior` section is inspected
- **THEN** it names `replied`, `autoreplied`, `commit-only` and `none`, and
  states that only `replied` suppresses a recurrence

#### Scenario: The null hash is explained
- **WHEN** the `prior` section is inspected
- **THEN** it states that a thread predating the identity marker reports `hash`
  as null, and that such an entry matches nothing

#### Scenario: The guide links the reference
- **WHEN** `docs/semantic-review.md` is inspected
- **THEN** it carries a link resolving to `semantic-review-reference.md`
