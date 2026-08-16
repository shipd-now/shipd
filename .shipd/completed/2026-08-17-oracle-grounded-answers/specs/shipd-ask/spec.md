## MODIFIED Requirements

### Requirement: Oracle agent contract
id: oracle-agent-contract
base: 93d1f0a38c69

The plugin SHALL provide an oracle agent definition at
`plugins/s/agents/oracle.md` (frontmatter `name: oracle`, resolving as agent
type `s:oracle`) that is non-interactive by contract: it never asks the user
anything and never blocks its caller. When spawned with one compact question
and the asking repo's root, the oracle SHALL search the personal memory store
first — via the `--personal` wiki reads (`cat wiki index --personal`, `cat wiki
<slug> --personal`, and read-only grep under the store directory reported by
`wiki-show --personal`, all with `--root` at the asking repo) — skipping this
rung when no personal store exists; then it SHALL search the workspace wiki
(index, then pages, via engine reads and read-only grep), and within this rung,
after the pages, it SHALL read the queue (`cat wiki queue`) and treat
answered-but-undrained blocks — `## q-<slug>` entries whose `Answer:` line is
not `pending` — as citable sources; where `wiki-show` reports a present base
store on its `base:` line, the oracle SHALL then search the base wiki, through
the same engine verbs and read-only grep invoked with `--root` at the reported
base store path; and it SHALL then widen to the asking repo's spec surfaces
(verified capability masters, epic Decisions/Design, research reports, project
context — via `spec_status.py` reads). Where the workspace declares a `focus`
project (reported by `workspace-show`), the oracle SHALL consult that
project's surfaces (via `project-show`) first within the repo-surface rung.
The oracle SHALL take the first durable position the ladder yields. The
oracle's default verdict SHALL be `INSUFFICIENT`: it SHALL NOT answer from
model knowledge, returning `ANSWER` only when a consulted source states a
position on the specific decision asked — topical relevance alone SHALL NOT
suffice. The oracle's reply SHALL begin with a first non-blank line of exactly
`ANSWER` or `INSUFFICIENT`.

#### Scenario: Definition carries the contract
- **WHEN** `plugins/s/agents/oracle.md` is inspected
- **THEN** it declares `name: oracle` frontmatter, the
  personal-then-job-then-base-then-repo search ladder with engine-mediated
  reads including the answered-queue read after the job store's pages, the
  focus-first repo-surface rung, the non-interactive rule, the
  default-`INSUFFICIENT` grounding bar, and the two-verdict first-line
  contract

#### Scenario: Verdict is machine-branchable
- **WHEN** the oracle is spawned with a compact question
- **THEN** the first non-blank line of its reply is exactly `ANSWER` or
  `INSUFFICIENT`

#### Scenario: Personal store answers first
- **GIVEN** a personal memory store holding a page that answers the decision
- **WHEN** the oracle is spawned
- **THEN** it returns `ANSWER` from the personal rung without searching the
  job wiki, base wiki, or repo surfaces

#### Scenario: Absent personal store is skipped
- **WHEN** the oracle runs where `wiki-show --personal` reports no personal
  store
- **THEN** it skips the personal rung without error and searches the job wiki
  next

#### Scenario: Answered queue entry answers before teach drains it
- **GIVEN** a job store whose queue holds a `## q-<slug>` block with a
  non-`pending` answer settling the decision and no page covering it
- **WHEN** the oracle is spawned
- **THEN** it returns `ANSWER` from that block, cited as `queue q-<slug>`

#### Scenario: Topical sources without a position yield INSUFFICIENT
- **WHEN** every consulted source merely touches the decision's topic without
  stating a position on the decision itself
- **THEN** the oracle returns `INSUFFICIENT` rather than answering from model
  knowledge

#### Scenario: Base rung answers when the job wiki is silent
- **GIVEN** a workspace whose `wiki-show` reports a present base store
- **WHEN** the personal store and job wiki lack the answer and a base wiki page
  holds it
- **THEN** the oracle returns `ANSWER` from the base rung before widening to
  the repo's spec surfaces

#### Scenario: Focus project weighted first
- **GIVEN** a workspace declaring `focus` on a project
- **WHEN** the oracle widens to the repo-surface rung
- **THEN** it consults the focus project's surfaces before the others

### Requirement: Cited opinionated answers
id: oracle-cited-answers
base: dde8759c2c12

Where the personal memory store, the wiki, or the asking repo's spec surfaces
hold the answer, the oracle SHALL return `ANSWER` with a single recommended
position (never an uncommitted list of alternatives) and SHALL name the wiki
page(s) or repo artifact(s) behind it on `Cited:` line(s). Every `ANSWER`
SHALL additionally carry at least one `Evidence:` line quoting a cited source
verbatim, so the caller can check that the source states a position on the
specific decision rather than merely touching its topic. A citation of a
personal-store wiki page SHALL carry a personal marker — `Cited: [[slug]]
(personal)` — a citation of a base-store wiki page SHALL carry a base marker —
`Cited: [[slug]] (base)` — and a citation of an answered-but-undrained queue
block SHALL read `Cited: queue q-<slug>` — so the caller can tell which store
answered.

#### Scenario: Wiki-backed answer is cited
- **WHEN** the oracle is asked a question whose answer a wiki page holds
- **THEN** it returns `ANSWER`, takes a position, and a `Cited:` line names
  that page

#### Scenario: Answer carries verbatim evidence
- **WHEN** the oracle returns `ANSWER`
- **THEN** at least one `Evidence:` line quotes a cited source verbatim

#### Scenario: Personal-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the personal memory
  store
- **THEN** the citation reads `Cited: [[slug]] (personal)`

#### Scenario: Base-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the base store
- **THEN** the citation reads `Cited: [[slug]] (base)`

#### Scenario: Queue-backed answer is marked
- **WHEN** the oracle's answer rests on an answered-but-undrained queue block
- **THEN** the citation reads `Cited: queue q-<slug>`

### Requirement: Ask skill entry
id: ask-skill
base: 1d252104226b

The plugin SHALL provide `/s:ask` at `plugins/s/skills/ask/SKILL.md`: it
SHALL announce the running plugin version, shape the user's request into a
compact question without an interview round, spawn `s:oracle` via the Agent
tool with the question and the repo root, and relay the verdict. If the
verdict's first line is `ANSWER` but its body lacks a `Cited:` line or an
`Evidence:` line, then the skill SHALL treat the verdict as `INSUFFICIENT`.
When the verdict is `INSUFFICIENT`, the skill SHALL put the compact question
to the user through a single AskUserQuestion dialog with the recommendation
listed first, distill the user's reply into a concise durable answer, and,
where the verdict reported a filed `q-<slug>`, SHALL write that answer through
`spec_status.py wiki-queue-answer`; where the verdict reported `Queued: none`,
the skill SHALL relay the answer for the session only and state that nothing
durable was captured.

#### Scenario: Skill relays the oracle verdict
- **WHEN** `plugins/s/skills/ask/SKILL.md` is inspected
- **THEN** it directs shaping a compact question, spawning agent type
  `s:oracle`, relaying `ANSWER` citations, and demoting an `ANSWER` missing
  `Cited:` or `Evidence:` to `INSUFFICIENT`

#### Scenario: Insufficient verdict defers to the user
- **WHEN** the SKILL.md's `INSUFFICIENT` branch is inspected
- **THEN** it directs a single AskUserQuestion dialog carrying the compact
  question's options with the recommendation first

#### Scenario: The user's answer is captured for the oracle
- **WHEN** the SKILL.md's capture step is inspected
- **THEN** it directs distilling the user's reply and writing it via
  `wiki-queue-answer` against the verdict's filed `q-<slug>`

#### Scenario: No workspace relays without capture
- **WHEN** the SKILL.md's `Queued: none` handling is inspected
- **THEN** it directs relaying the answer for the session only and stating
  that nothing durable was captured

## ADDED Requirements

### Requirement: Oracle user documentation
id: oracle-user-docs

The repository SHALL provide `docs/oracle.md`, a user-facing guide to the
ask-mikk oracle that includes a diagram of the read → ask-mikk → human ladder
with the answer-capture loop, the two verdicts each shown with an example
(`ANSWER` with `Cited:` and `Evidence:` lines; `INSUFFICIENT` with its queued
question), the definitive-evidence answering bar, and the correction path via
`/s:teach`.

#### Scenario: Guide covers the loop
- **WHEN** `docs/oracle.md` is inspected
- **THEN** it holds a ladder-and-capture-loop diagram, an `ANSWER` example
  with `Cited:` and `Evidence:` lines, an `INSUFFICIENT` example, and names
  `/s:teach` as the correction path
