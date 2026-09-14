# semantic-review

## ADDED Requirements

### Requirement: Incremental gate review
id: review-incremental

Each inline finding comment the poster renders SHALL carry a hidden identity
marker of the form `<!-- shipd-finding <hash> -->`, where `<hash>` is the first
twelve hexadecimal characters of the SHA-256 of the finding's `location` path,
a newline, and its `what` text lowercased with whitespace runs collapsed to a
single space. The marker SHALL be the body's last element, never its first, so
the severity marker stays the opening token `parse_severity` reads. The hash
SHALL NOT incorporate a line number, so a finding whose line moved still
matches.

The system SHALL provide `review_gate.py prior <pr>`, emitting one JSON entry
per gate-authored review thread carrying the thread's `hash` (or null where the
body has no marker), `path`, `severity`, `what`, `thread_id`, `resolved`, and a
`disposition` of `replied`, `autoreplied`, `commit-only`, or `none`. A thread
whose non-root comments are all exactly one of the canonical `autoreply` bodies
SHALL classify `autoreplied`; a thread carrying any other reply SHALL classify
`replied`; a thread with no reply but a commit landed after its creation SHALL
classify `commit-only`; a thread with neither SHALL classify `none`. The verb
SHALL decide nothing about suppression and SHALL mutate nothing.

The `/s:review` skill, **when and only when posting to a pull request**, SHALL
read `prior` back before reporting and omit a finding whose hash matches a
thread classified `replied`. It SHALL NOT omit a finding matching any other
classification, and SHALL state in its report how many findings it omitted and
which pull request answered them. A review that is not posting SHALL read
nothing back and omit nothing.

`SKILL.md` SHALL state this trigger in the `Load when` cell of its existing
`posting.md` References row, adding no line, and SHALL stay under 300 lines.

#### Scenario: A reworded finding is reported again
- **WHEN** a prior thread was answered with a reasoned reply and the new review
  produces a finding at the same path whose `what` text differs
- **THEN** the hashes differ and the new finding is reported

#### Scenario: A dismissed finding is omitted on the next head
- **WHEN** a prior thread carries a reasoned reply and the new review produces
  a finding whose path and `what` match it
- **THEN** the finding is omitted and the report states one finding was omitted
  and names the pull request

#### Scenario: An implemented finding that recurs is reported
- **WHEN** a prior thread's only disposition evidence is a commit landed after
  its creation, and the same finding recurs
- **THEN** the thread classifies `commit-only` and the finding is reported,
  because a recurrence after a fix is a regression

#### Scenario: An auto-dispositioned finding is reported
- **WHEN** a prior thread's only replies are the canonical `autoreply` body
- **THEN** the thread classifies `autoreplied` and the finding is reported

#### Scenario: A moved line still matches
- **WHEN** a dismissed finding recurs at the same path with identical `what`
  text but a different line number
- **THEN** the hashes match and the finding is omitted

#### Scenario: The severity marker survives the identity marker
- **WHEN** a body rendered with an identity marker is passed to
  `parse_severity`
- **THEN** it returns the finding's severity, unchanged by the marker

#### Scenario: A pre-push review reads nothing back
- **WHEN** a review runs without a posting request
- **THEN** no `prior` call is made and no finding is omitted

#### Scenario: The trigger costs no line
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured and its References
  table inspected
- **THEN** the file is under 300 lines and the `posting.md` row's `Load when`
  cell states the read-back trigger
