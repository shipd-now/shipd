# shipd-ask

### Requirement: Oracle agent contract
id: oracle-agent-contract

The plugin SHALL provide an oracle agent definition at
`plugins/s/agents/oracle.md` (frontmatter `name: oracle`, resolving as agent
type `s:oracle`) that is non-interactive by contract: it never asks the user
anything and never blocks its caller. When spawned with one compact question
and the asking repo's root, the oracle SHALL search the personal memory store
first — via the `--personal` wiki reads (`cat wiki index --personal`, `cat wiki
<slug> --personal`, and read-only grep under the store directory reported by
`wiki-show --personal`, all with `--root` at the asking repo) — skipping this
rung when no personal store exists; then it SHALL search the workspace wiki
(index, then pages, via engine reads and read-only grep); where `wiki-show`
reports a present base store on its `base:` line, the oracle SHALL then search
the base wiki, through the same engine verbs and read-only grep invoked with
`--root` at the reported base store path; and it SHALL then widen to the asking
repo's spec surfaces (verified capability masters, epic Decisions/Design,
research reports, project context — via `spec_status.py` reads). Where the
workspace declares a `focus` project (reported by `workspace-show`), the oracle
SHALL consult that project's surfaces (via `project-show`) first within the
repo-surface rung. The oracle SHALL take the first durable position the ladder
yields. The oracle's reply SHALL begin with a first non-blank line of exactly
`ANSWER` or `INSUFFICIENT`.

#### Scenario: Definition carries the contract
- **WHEN** `plugins/s/agents/oracle.md` is inspected
- **THEN** it declares `name: oracle` frontmatter, the
  personal-then-job-then-base-then-repo search ladder with engine-mediated
  reads, the focus-first repo-surface rung, the non-interactive rule, and the
  two-verdict first-line contract

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

Where the personal memory store, the wiki, or the asking repo's spec surfaces
hold the answer, the oracle SHALL return `ANSWER` with a single recommended
position (never an uncommitted list of alternatives) and SHALL name the wiki
page(s) or repo artifact(s) behind it on `Cited:` line(s). A citation of a
personal-store wiki page SHALL carry a personal marker — `Cited: [[slug]]
(personal)` — and a citation of a base-store wiki page SHALL carry a base
marker — `Cited: [[slug]] (base)` — so the caller can tell which store answered.

#### Scenario: Wiki-backed answer is cited
- **WHEN** the oracle is asked a question whose answer a wiki page holds
- **THEN** it returns `ANSWER`, takes a position, and a `Cited:` line names
  that page

#### Scenario: Personal-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the personal memory
  store
- **THEN** the citation reads `Cited: [[slug]] (personal)`

#### Scenario: Base-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the base store
- **THEN** the citation reads `Cited: [[slug]] (base)`

### Requirement: Insufficient queues the question
id: oracle-insufficient-queue

If neither the wiki nor the asking repo's spec surfaces answer the question,
then the oracle SHALL return `INSUFFICIENT` with the compact question block
and SHALL append the question to the wiki queue via
`spec_status.py wiki-queue-add` with an `--origin` naming the asking repo,
reporting the slug on a `Queued: q-<slug>` line. The queue write — and any
`wiki-init` scaffolding — SHALL target the asking workspace's own store,
never the base store, which is read-only to the oracle. Before queueing, the
oracle SHALL read the existing queue and cite an equivalent pending question
instead of duplicating it. If the workspace has no wiki store, then the
oracle SHALL scaffold it with `wiki-init` before queueing; if no workspace is
discoverable at all, then the oracle SHALL still return its verdict and
report `Queued: none` naming the missing workspace instead of failing.

#### Scenario: Unanswerable question is queued
- **WHEN** the oracle cannot answer from the wiki or repo surfaces in a
  workspace with a wiki store
- **THEN** it returns `INSUFFICIENT` and `queue.md` gains a `## q-<slug>`
  block with the question, options, recommendation, and `Answer: pending`

#### Scenario: Queue lands in the job store, not the base
- **GIVEN** a workspace whose `wiki-show` reports a present base store
- **WHEN** the oracle queues an unanswerable question
- **THEN** the block lands in the job store's `queue.md` and the base store
  is unmodified

#### Scenario: Missing store is scaffolded, not fatal
- **WHEN** the oracle must queue a question in a workspace with no wiki store
- **THEN** it runs `wiki-init` and then queues, and the verdict reports the
  `q-<slug>`

#### Scenario: No workspace still yields a verdict
- **WHEN** the oracle runs for an asking repo with no discoverable workspace
- **THEN** it answers from the repo's spec surfaces alone or returns
  `INSUFFICIENT` with `Queued: none`, and does not exit in error

### Requirement: Ask skill entry
id: ask-skill

The plugin SHALL provide `/s:ask` at `plugins/s/skills/ask/SKILL.md`: it
SHALL announce the running plugin version, shape the user's request into a
compact question without an interview round, spawn `s:oracle` via the Agent
tool with the question and the repo root, and relay the verdict — the cited
answer, or the queued `q-<slug>` and how its answer later reaches the wiki.

#### Scenario: Skill relays the oracle verdict
- **WHEN** `plugins/s/skills/ask/SKILL.md` is inspected
- **THEN** it directs shaping a compact question, spawning agent type
  `s:oracle`, and relaying `ANSWER` citations or the `INSUFFICIENT` queue
  slug to the user

### Requirement: Compact question contract
id: compact-question-contract

Every question put to the oracle — and every question the oracle queues —
SHALL be one decision-ready unit carrying the decision, concrete options, and
the asker's recommendation, never a raw trace or an open-ended essay prompt.
Both `plugins/s/agents/oracle.md` and `plugins/s/skills/ask/SKILL.md` SHALL
state this contract.

#### Scenario: Both surfaces carry the contract
- **WHEN** the oracle agent definition and the ask SKILL.md are inspected
- **THEN** each states the decision/options/recommendation compact-question
  shape
