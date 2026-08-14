## ADDED Requirements

### Requirement: Oracle agent contract
id: oracle-agent-contract

The plugin SHALL provide an oracle agent definition at
`plugins/s/agents/oracle.md` (frontmatter `name: oracle`, resolving as agent
type `s:oracle`) that is non-interactive by contract: it never asks the user
anything and never blocks its caller. When spawned with one compact question
and the asking repo's root, the oracle SHALL search the workspace wiki first
(index, then pages, via engine reads and read-only grep) and then widen to the
asking repo's spec surfaces (verified capability masters, epic
Decisions/Design, research reports, project context — via `spec_status.py`
reads), and its reply SHALL begin with a first non-blank line of exactly
`ANSWER` or `INSUFFICIENT`.

#### Scenario: Definition carries the contract
- **WHEN** `plugins/s/agents/oracle.md` is inspected
- **THEN** it declares `name: oracle` frontmatter, the wiki-first-then-repo
  search ladder with engine-mediated reads, the non-interactive rule, and the
  two-verdict first-line contract

#### Scenario: Verdict is machine-branchable
- **WHEN** the oracle is spawned with a compact question
- **THEN** the first non-blank line of its reply is exactly `ANSWER` or
  `INSUFFICIENT`

### Requirement: Cited opinionated answers
id: oracle-cited-answers

Where the wiki or the asking repo's spec surfaces hold the answer, the oracle
SHALL return `ANSWER` with a single recommended position (never an
uncommitted list of alternatives) and SHALL name the wiki page(s) or repo
artifact(s) behind it on `Cited:` line(s).

#### Scenario: Wiki-backed answer is cited
- **WHEN** the oracle is asked a question whose answer a wiki page holds
- **THEN** it returns `ANSWER`, takes a position, and a `Cited:` line names
  that page

### Requirement: Insufficient queues the question
id: oracle-insufficient-queue

If neither the wiki nor the asking repo's spec surfaces answer the question,
then the oracle SHALL return `INSUFFICIENT` with the compact question block
and SHALL append the question to the wiki queue via
`spec_status.py wiki-queue-add` with an `--origin` naming the asking repo,
reporting the slug on a `Queued: q-<slug>` line. Before queueing, the oracle
SHALL read the existing queue and cite an equivalent pending question instead
of duplicating it. If the workspace has no wiki store, then the oracle SHALL
scaffold it with `wiki-init` before queueing; if no workspace is discoverable
at all, then the oracle SHALL still return its verdict and report
`Queued: none` naming the missing workspace instead of failing.

#### Scenario: Unanswerable question is queued
- **WHEN** the oracle cannot answer from the wiki or repo surfaces in a
  workspace with a wiki store
- **THEN** it returns `INSUFFICIENT` and `queue.md` gains a `## q-<slug>`
  block with the question, options, recommendation, and `Answer: pending`

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
