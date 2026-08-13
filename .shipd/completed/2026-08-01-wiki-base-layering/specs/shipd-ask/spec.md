## MODIFIED Requirements

### Requirement: Oracle agent contract
id: oracle-agent-contract
base: 8d8f95b54a20

The plugin SHALL provide an oracle agent definition at
`plugins/s/agents/oracle.md` (frontmatter `name: oracle`, resolving as agent
type `s:oracle`) that is non-interactive by contract: it never asks the user
anything and never blocks its caller. When spawned with one compact question
and the asking repo's root, the oracle SHALL search the workspace wiki first
(index, then pages, via engine reads and read-only grep); where `wiki-show`
reports a present base store on its `base:` line, the oracle SHALL then search
the base wiki second, through the same engine verbs and read-only grep invoked
with `--root` at the reported base store path; and it SHALL then widen to the
asking repo's spec surfaces (verified capability masters, epic
Decisions/Design, research reports, project context — via `spec_status.py`
reads). Where the workspace declares a `focus` project (reported by
`workspace-show`), the oracle SHALL consult that project's surfaces (via
`project-show`) first within the repo-surface rung. The oracle's reply SHALL
begin with a first non-blank line of exactly `ANSWER` or `INSUFFICIENT`.

#### Scenario: Definition carries the contract
- **WHEN** `plugins/s/agents/oracle.md` is inspected
- **THEN** it declares `name: oracle` frontmatter, the
  job-wiki-then-base-then-repo search ladder with engine-mediated reads, the
  focus-first repo-surface rung, the non-interactive rule, and the
  two-verdict first-line contract

#### Scenario: Verdict is machine-branchable
- **WHEN** the oracle is spawned with a compact question
- **THEN** the first non-blank line of its reply is exactly `ANSWER` or
  `INSUFFICIENT`

#### Scenario: Base rung answers when the job wiki is silent
- **GIVEN** a workspace whose `wiki-show` reports a present base store
- **WHEN** the job wiki lacks the answer and a base wiki page holds it
- **THEN** the oracle returns `ANSWER` from the base rung before widening to
  the repo's spec surfaces

#### Scenario: Focus project weighted first
- **GIVEN** a workspace declaring `focus` on a project
- **WHEN** the oracle widens to the repo-surface rung
- **THEN** it consults the focus project's surfaces before the others

### Requirement: Cited opinionated answers
id: oracle-cited-answers
base: 930b42f6ca53

Where the wiki or the asking repo's spec surfaces hold the answer, the oracle
SHALL return `ANSWER` with a single recommended position (never an
uncommitted list of alternatives) and SHALL name the wiki page(s) or repo
artifact(s) behind it on `Cited:` line(s). A citation of a base-store wiki
page SHALL carry a base marker — `Cited: [[slug]] (base)` — so the caller can
tell which store answered.

#### Scenario: Wiki-backed answer is cited
- **WHEN** the oracle is asked a question whose answer a wiki page holds
- **THEN** it returns `ANSWER`, takes a position, and a `Cited:` line names
  that page

#### Scenario: Base-backed answer is marked
- **WHEN** the oracle's answer rests on a page read from the base store
- **THEN** the citation reads `Cited: [[slug]] (base)`

### Requirement: Insufficient queues the question
id: oracle-insufficient-queue
base: a08dd8ef94ca

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
