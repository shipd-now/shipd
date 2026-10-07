## MODIFIED Requirements

### Requirement: Skill reference loading
id: review-skill-references
base: bbb61d51cda8

The `/s:review` skill SHALL carry its condition-gated guidance in reference
files under `plugins/s/skills/review/references/` rather than inline in its
`SKILL.md`, and `SKILL.md` SHALL name every file in that directory by its
`${CLAUDE_PLUGIN_ROOT}` path beside the condition under which the skill reads
it. The spec-aware verification guidance, the `--json` machine output guidance,
and the PR posting guidance SHALL each occupy one such file, read only when a
planned change is in scope, when `--json` is requested, and when a pull request
is in scope for the review, respectively. The posting reference SHALL carry the
resolution of a named pull request into a base and a head, so `SKILL.md` names
that flow rather than restating it.

Guidance that runs on every review SHALL stay inline in `SKILL.md`: the
workflow steps, the severity rubric, the presentation shape, the review-start
difftastic probe and its degradation ladder, the base-freshness block, and the
guardrails. `SKILL.md` SHALL stay under 330 lines; this requirement owns that
ceiling, and no other requirement SHALL restate the figure.

Each reference file SHALL open with a level-1 title and state its own load
condition, so a file read on its own explains why it was read. Moving guidance
into a reference SHALL NOT change that guidance's substance.

#### Scenario: Every reference is reachable from the skill
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names every file under `plugins/s/skills/review/references/` by
  path, and every reference path it names resolves to an existing file

#### Scenario: The posting reference is loaded on a pull request
- **WHEN** the References table row for `posting.md` is compared with that
  file's own condition sentence
- **THEN** both state that the file is read when a pull request is in scope for
  the review, rather than when posting was explicitly requested

#### Scenario: Conditional guidance left the skill body
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries no `## Machine output mode`, `## Posting to a PR`, or
  `## Spec-aware review` section, and the three reference files carry that
  guidance instead

#### Scenario: Hot-path guidance stayed inline
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the workflow steps, the high/medium/low severity rubric, the
  `command -v difft` probe, and the base-freshness block are present in the file
  itself, behind no reference

#### Scenario: The skill body fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 330 lines

#### Scenario: A reference states its own trigger
- **WHEN** a file under `plugins/s/skills/review/references/` is read on its own
- **THEN** its opening lines give a level-1 title and the condition under which
  the skill loads it

#### Scenario: The other rubric surfaces are untouched
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** neither references a file under `plugins/s/skills/review/references/`,
  since neither runs where `${CLAUDE_PLUGIN_ROOT}` resolves

### Requirement: Risk lenses
id: review-risk-lenses
base: 44b949a44d24

The `/s:review` skill SHALL carry four risk lenses alongside its existing
judgement passes — security, performance, stability, and data integrity —
expressed as five triggers: secret or credential exposure, authorization
boundary, unbounded work, resource release, and migration reversibility. The
triggers SHALL be stated inline in `SKILL.md`, read on every review, and SHALL
NOT be gated on a cohort, a file type, or any other condition. The detailed
guidance and worked examples for the lenses SHALL live in
`plugins/s/skills/review/references/risk-lenses.md`, read when a trigger fires.

A finding of secret or credential exposure, or of an authorization boundary
reached without the caller's scope check, SHALL carry severity `high`
regardless of the reviewer's confidence. Findings from the remaining triggers
SHALL rate on the existing high, medium and low rubric with no floor.

The `--json` finding taxonomy SHALL accept the values `security`,
`performance`, `stability`, and `data-integrity` in addition to those it
already accepts.

Both surfaces that cannot read a reference file — the harness command body at
`plugins/s/harness/bodies/review.md` and the vendored template at
`plugins/s/integrations/copilot/SKILL.md` — SHALL carry the lens guidance and
the exposure severity floor inline.

#### Scenario: Every trigger is inline and ungated
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** all five triggers appear in the workflow itself, and no trigger is
  stated only in the References table or only in a reference file

#### Scenario: A leaked credential is high
- **WHEN** a review finds a new literal, log line, or error message carrying a
  key, token, or personal data
- **THEN** the finding's severity is `high` and the verdict is Fix required

#### Scenario: An unguarded authorization boundary is high
- **WHEN** a review finds a new route, handler, or query reaching data without
  the caller's scope check
- **THEN** the finding's severity is `high`

#### Scenario: The remaining lenses carry no floor
- **WHEN** a review finds an unbounded loop whose cost the reviewer judges
  minor
- **THEN** the finding may rate `low` or `medium`, since only the two exposure
  triggers carry a floor

#### Scenario: The taxonomy accepts the lens values
- **WHEN** a `--json` review emits a finding from the data-integrity trigger
- **THEN** `data-integrity` is a value the finding shape accepts

#### Scenario: The reference-free surfaces carry the lenses inline
- **WHEN** `plugins/s/harness/bodies/review.md` and
  `plugins/s/integrations/copilot/SKILL.md` are inspected
- **THEN** each names all five triggers and the exposure severity floor in its
  own body, referencing no file under `skills/review/references/`

#### Scenario: The new reference is pinned like the others
- **WHEN** the review skill's test suite runs
- **THEN** `risk-lenses.md` is named in the References table, its path
  resolves, and its `Load when` cell and its condition sentence share at least
  the required content words

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is within the line ceiling `review-skill-references` owns

### Requirement: Linter output in the review
id: review-lint-step
base: d82ad034043f

The `/s:review` skill SHALL carry an inline workflow step directing the
reviewer to run `semdiff lint` over the same endpoints as the diff and to read
its output, with the detailed guidance in
`plugins/s/skills/review/references/linters.md` named by its
`${CLAUDE_PLUGIN_ROOT}` path beside its load condition. The inline step SHALL
state that a linter finding is corroboration the reviewer weighs, reported only
where it bears on the change, and never promoted to a review finding
automatically.

#### Scenario: The step is inline and the detail is referenced
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries the `semdiff lint` step in the workflow itself and names
  `linters.md` in the References table with its load condition

#### Scenario: A linter hit is not automatically a finding
- **WHEN** the skill's linter step is read
- **THEN** it states that a linter finding is weighed as corroboration and
  reported only where it bears on the change

#### Scenario: The skill body still fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is within the line ceiling `review-skill-references` owns

### Requirement: Incremental gate review
id: review-incremental
base: ead16f3b6b79

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
`posting.md` References row, adding no line.

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
- **THEN** the file is within the line ceiling
  `review-skill-references` owns and the `posting.md` row's `Load when`
  cell states the read-back trigger
