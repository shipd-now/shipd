## ADDED Requirements

### Requirement: Fallback store serves a bare repo
id: oracle-fallback-store

Where no workspace is discoverable from the asking repo and the repo's
resolved content directory exists, the oracle's wiki rung SHALL operate on
the repo-local fallback store reported by `wiki-show` — through the same
engine reads (`cat wiki index`, `cat wiki <slug>`, `cat wiki queue`) and
read-only grep under the reported store directory — and
answered-but-undrained queue blocks found there SHALL be citable exactly as
chain-store blocks are (`Cited: queue q-<slug>`).

#### Scenario: Fallback page answers the question
- **GIVEN** a bare repo whose fallback store holds a page settling the
  decision
- **WHEN** the oracle is spawned
- **THEN** it returns `ANSWER` citing that page before widening to the
  repo's spec surfaces

#### Scenario: Fallback answered queue block is citable
- **GIVEN** a bare repo whose fallback store's queue holds a `## q-<slug>`
  block with a non-`pending` answer settling the decision
- **WHEN** the oracle is spawned
- **THEN** it returns `ANSWER` cited as `queue q-<slug>`

## MODIFIED Requirements

### Requirement: Insufficient queues the question
id: oracle-insufficient-queue
base: d26f12969429

If neither the wiki nor the asking repo's spec surfaces answer the question,
then the oracle SHALL return `INSUFFICIENT` with the compact question block
and SHALL append the question to the wiki queue via
`spec_status.py wiki-queue-add` with an `--origin` naming the asking repo,
reporting the slug on a `Queued: q-<slug>` line. The queue write — and any
`wiki-init` scaffolding — SHALL target the asking workspace's own store,
never the base store, which is read-only to the oracle. Before queueing, the
oracle SHALL read the existing queue and cite an equivalent pending question
instead of duplicating it. If the resolved store does not exist yet, then the
oracle SHALL scaffold it with `wiki-init` before queueing. Where no workspace
is discoverable but the asking repo's resolved content directory exists, the
queue write SHALL land in the repo-local fallback store through the same
verbs, which resolve and scaffold it on demand. Only where the asking repo
has neither a discoverable workspace nor a content directory SHALL the
oracle still return its verdict and report `Queued: none` naming the missing
prerequisites instead of failing.

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

#### Scenario: Bare repo queues into the fallback store
- **GIVEN** an asking repo with a content directory and no discoverable
  workspace
- **WHEN** the oracle cannot answer the question
- **THEN** the block lands in `<root>/<content-dir>/wiki/queue.md` and the
  verdict reports `Queued: q-<slug>`, not `Queued: none`

#### Scenario: Uninitialized repo still yields a verdict
- **WHEN** the oracle runs for an asking repo with no discoverable workspace
  and no content directory
- **THEN** it answers from what it can reach or returns `INSUFFICIENT` with
  `Queued: none` naming the missing prerequisites, and does not exit in
  error
