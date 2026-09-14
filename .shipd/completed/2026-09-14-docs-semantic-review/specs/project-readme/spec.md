# project-readme

## ADDED Requirements

### Requirement: Semantic review guide
id: semantic-review-doc

`docs/semantic-review.md` SHALL be a concept guide opening with a
`<!-- doc-type: concept -->` comment on its first line, totalling 100 lines or
fewer and passing `docs_lint.py`. It SHALL explain what the semantic review
reads and how it rates what it finds, and SHALL list no command flag and no
JSON field — that lookup material belongs to a reference doc.

The guide SHALL name every `semdiff` subcommand the review uses — `files`,
`diff`, `context`, `change`, `lint` and `doctor` — with one line stating what
each returns. It SHALL state that the engine supplies the facts and the
reviewer supplies the judgement.

The guide SHALL describe the three passes that look past the changed lines:
downstream impact on a changed contract, the values each call site passes, and
the five risk-lens triggers. It SHALL name all five triggers. It SHALL state
that a linter finding is corroboration the reviewer weighs rather than a
review finding in itself.

The guide SHALL state the blocking rule: `high` and `medium` block, and `low`
never does. It SHALL state the exposure floor — an exposed secret, and an
authorization boundary reached without a scope check, always rate `high`.

The guide SHALL describe both paths a review takes: a local run that ends at
the report, and a posting run that reads prior dispositions back before
reporting. It SHALL state that the review omits a finding answered with a
reasoned reply, that it keeps a finding only a commit cleared, and that a
finding's identity excludes its line number.

The guide SHALL carry exactly one mermaid diagram, of those two paths, and
SHALL state that the review degrades rather than stops when a tool is missing.

`docs/copilot-review.md` SHALL link `/s:review` to this guide rather than to a
README anchor.

#### Scenario: The guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/semantic-review.md` runs
- **THEN** it exits `0`, and the file is 100 lines or fewer opening with the
  concept marker

#### Scenario: Every subcommand is named
- **WHEN** the guide is inspected
- **THEN** it names `files`, `diff`, `context`, `change`, `lint` and `doctor`,
  each with what it returns

#### Scenario: The blocking rule and the floor are stated
- **WHEN** the guide is inspected
- **THEN** it states that `high` and `medium` block while `low` does not, and
  that an exposed secret and an unguarded authorization boundary always rate
  `high`

#### Scenario: The five triggers are named
- **WHEN** the guide is inspected
- **THEN** it names secret or credential exposure, authorization boundary,
  unbounded work, resource release, and migration reversibility

#### Scenario: The suppression rule is stated honestly
- **WHEN** the guide is inspected
- **THEN** it states that a reasoned reply suppresses a recurrence, that a
  commit-cleared finding is kept, and that the identity excludes the line
  number

#### Scenario: The guide carries one diagram
- **WHEN** the guide's mermaid fences are counted
- **THEN** exactly one is present, and it shows the local path ending at the
  report and the posting path looping back

#### Scenario: The how-to points at the guide
- **WHEN** `docs/copilot-review.md` is inspected
- **THEN** its `/s:review` link resolves to `semantic-review.md`, and its link
  to `docs/copilot-review-reference.md` is unchanged
