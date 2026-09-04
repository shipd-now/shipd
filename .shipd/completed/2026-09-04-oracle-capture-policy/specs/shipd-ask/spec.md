## ADDED Requirements

### Requirement: Capture durability rubric
id: capture-rubric

The plugin SHALL provide a capture durability rubric reference at
`plugins/s/skills/ask/references/capture-rubric.md` defining three tiers for
classifying a user's typed answer before any queue capture: **include**
(durable engineering positions — captured immediately as binding knowledge),
**exclude** (self-evidencing or explicitly one-off answers — the pending
queue block is discarded via `wiki-queue-discard`), and **consent-gated**
(workflow workarounds, process habits, and personal preferences — captured
only on the user's express affirmative to an explicit record-this question,
and always as advisory via `wiki-queue-answer --advisory`). The rubric SHALL
carry calibrated worked examples covering at least: a clean package
preference, a data-modeling pattern, a naming convention, an error-handling
philosophy, and a testing strategy classified include; an explicitly one-off
decision and a repo-self-evidencing version pin classified exclude; and a
workflow workaround stated in annoyance, tooling-enforced process etiquette,
and a personal presentation preference classified consent-gated. The rubric
SHALL state that borderline cases lean toward the less-capturing tier and
that user-personal (non-workspace) preferences are recommended to the
personal memory store instead.

#### Scenario: Rubric reference exists with three tiers
- **WHEN** `plugins/s/skills/ask/references/capture-rubric.md` is inspected
- **THEN** it defines the include, exclude, and consent-gated tiers, the
  express-instruction rule for consent-gated capture, and the advisory
  capture mechanics

#### Scenario: Calibrated examples are present
- **WHEN** the rubric's examples are inspected
- **THEN** each named example category appears with its tier and a short
  rationale

## MODIFIED Requirements

### Requirement: Ask skill entry
id: ask-skill
base: d68dd48c5d0c

The plugin SHALL provide `/s:ask` at `plugins/s/skills/ask/SKILL.md`: it
SHALL announce the running plugin version, shape the user's request into a
compact question without an interview round, spawn `s:oracle` via the Agent
tool with the question and the repo root, and relay the verdict. If the
verdict's first line is `ANSWER` but its body lacks a `Cited:` line or an
`Evidence:` line, then the skill SHALL treat the verdict as `INSUFFICIENT`.
Where an `ANSWER` carries an `Authority: advisory` line, the skill SHALL
relay it as a recommendation rather than a settlement: it SHALL still put
the decision to the user with the oracle's advisory position as the
recommended first option, naming its citation. When the verdict is
`INSUFFICIENT`, the skill SHALL put the compact question to the user through
a single AskUserQuestion dialog with the recommendation listed first, distill
the user's reply into a concise durable answer, and classify that answer
against the capture rubric
(`plugins/s/skills/ask/references/capture-rubric.md`) before any queue
write: an include-tier answer is written through
`spec_status.py wiki-queue-answer` against the filed `q-<slug>`; an
exclude-tier answer discards the block through
`spec_status.py wiki-queue-discard` with a one-line reason; a
consent-gated-tier answer is captured with `wiki-queue-answer --advisory`
only when the user expressly affirms an explicit record-this question, and
is otherwise discarded. Where the verdict reported `Queued: none`, the skill
SHALL relay the answer for the session only and state that nothing durable
was captured. A failed capture or discard write SHALL be reported and SHALL
never block the reply.

#### Scenario: Skill relays the oracle verdict
- **WHEN** `plugins/s/skills/ask/SKILL.md` is inspected
- **THEN** it directs shaping a compact question, spawning agent type
  `s:oracle`, relaying `ANSWER` citations, and demoting an `ANSWER` missing
  `Cited:` or `Evidence:` to `INSUFFICIENT`

#### Scenario: Advisory answer recommends instead of settling
- **WHEN** the SKILL.md's handling of an `ANSWER` carrying
  `Authority: advisory` is inspected
- **THEN** it directs putting the decision to the user with the oracle's
  advisory position as the recommended first option, cited, rather than
  relaying it as settled

#### Scenario: Insufficient verdict defers to the user
- **WHEN** the SKILL.md's `INSUFFICIENT` branch is inspected
- **THEN** it directs a single AskUserQuestion dialog carrying the compact
  question's options with the recommendation first

#### Scenario: Include-tier answer is captured
- **WHEN** the SKILL.md's capture step is inspected
- **THEN** it directs classifying the distilled reply against the capture
  rubric and writing an include-tier answer via `wiki-queue-answer` against
  the verdict's filed `q-<slug>`

#### Scenario: Exclude-tier answer discards the block
- **WHEN** the capture step classifies the reply exclude-tier
- **THEN** the SKILL.md directs discarding the filed block via
  `wiki-queue-discard` with a reason instead of capturing

#### Scenario: Consent-gated capture requires express instruction
- **WHEN** the capture step classifies the reply consent-gated
- **THEN** the SKILL.md directs asking an explicit record-this question and
  capturing with `--advisory` only on an express affirmative, discarding
  otherwise

#### Scenario: No workspace relays without capture
- **WHEN** the SKILL.md's `Queued: none` handling is inspected
- **THEN** it directs relaying the answer for the session only and stating
  that nothing durable was captured

### Requirement: Cited opinionated answers
id: oracle-cited-answers
base: bff5920b4ed9

Where the personal memory store, the wiki, or the asking repo's spec surfaces
hold the answer, the oracle SHALL return `ANSWER` with a single recommended
position (never an uncommitted list of alternatives) and SHALL name the wiki
page(s) or repo artifact(s) behind it on `Cited:` line(s). Every `ANSWER`
SHALL additionally carry at least one `Evidence:` line quoting a cited source
verbatim, so the caller can check that the source states a position on the
specific decision rather than merely touching its topic. Where the position's
source carries an advisory marker — a queue block whose `Answer:` value
begins `advisory: `, or a wiki page carrying an `Authority: advisory` line —
the `ANSWER` SHALL carry an `Authority: advisory` line after its position, so
callers surface it as a recommendation rather than a settlement; an `ANSWER`
with no such line is binding, as before. A citation of a
personal-store wiki page SHALL carry a personal marker — `Cited: [[slug]]
(personal)` — a citation of a page read from an inherited chain store SHALL
carry an inherited marker naming that store's workspace root — `Cited:
[[slug]] (inherited <ws-root>)` — a citation of a base-store wiki page SHALL
carry a base marker — `Cited: [[slug]] (base)` — and a citation of an
answered-but-undrained queue block SHALL read `Cited: queue q-<slug>` — so the
caller can tell which store answered.

#### Scenario: Wiki-backed answer is cited
- **WHEN** the oracle is asked a question whose answer a wiki page holds
- **THEN** it returns `ANSWER`, takes a position, and a `Cited:` line names
  that page

#### Scenario: Answer carries verbatim evidence
- **WHEN** the oracle returns `ANSWER`
- **THEN** at least one `Evidence:` line quotes a cited source verbatim

#### Scenario: Advisory source yields an advisory answer
- **WHEN** the oracle's answer rests on a queue block whose `Answer:` value
  begins `advisory: ` or a wiki page carrying `Authority: advisory`
- **THEN** the `ANSWER` carries an `Authority: advisory` line after its
  position

#### Scenario: Binding sources carry no authority line
- **WHEN** the oracle's answer rests only on sources without an advisory
  marker
- **THEN** the `ANSWER` carries no `Authority:` line and is treated as
  binding

#### Scenario: Personal-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the personal memory
  store
- **THEN** the citation reads `Cited: [[slug]] (personal)`

#### Scenario: Inherited-store answer is marked
- **WHEN** the oracle's answer rests on a page read from an enclosing
  workspace's store rather than the nearest one
- **THEN** the citation reads `Cited: [[slug]] (inherited <ws-root>)`

#### Scenario: Base-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the base store
- **THEN** the citation reads `Cited: [[slug]] (base)`

#### Scenario: Queue-backed answer is marked
- **WHEN** the oracle's answer rests on an answered-but-undrained queue block
- **THEN** the citation reads `Cited: queue q-<slug>`
