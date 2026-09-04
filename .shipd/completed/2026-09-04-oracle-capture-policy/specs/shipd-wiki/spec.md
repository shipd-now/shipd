## ADDED Requirements

### Requirement: Queue discard verb
id: wiki-queue-discard-verb

`spec_status.py` SHALL provide a `wiki-queue-discard <slug> --reason "<text>"`
verb that resolves the workspace store exactly as `wiki-queue-add` does,
accepts the bare slug (prefixing `q-` itself), locates the `## q-<slug>`
block in `queue.md`, and — when the block's `Answer:` line is `pending` —
removes the entire block, printing the `q-<slug>` and exiting 0. The
`--reason` text SHALL be required and non-empty; it is echoed to the caller,
not stored. If the store or the block is missing, or the block's `Answer:`
line is not `pending`, then the verb SHALL write nothing and exit non-zero
naming the reason — an answered block is owned by the `/s:teach` drain and is
never discarded. The verb SHALL use only the Python standard library, and
every other queue block SHALL be preserved verbatim.

#### Scenario: Pending block is discarded
- **GIVEN** a queue block `## q-framework-pick` whose answer line is
  `- Answer: pending`
- **WHEN** `wiki-queue-discard framework-pick --reason "self-evidencing"`
  runs
- **THEN** the block is removed from `queue.md`, other blocks are unchanged,
  and the verb prints `q-framework-pick` and exits 0

#### Scenario: Answered block is refused
- **GIVEN** a queue block whose `Answer:` line is not `pending`
- **WHEN** `wiki-queue-discard` targets that block
- **THEN** nothing is written and the verb exits non-zero naming the
  answered state

#### Scenario: Missing block errors
- **WHEN** `wiki-queue-discard no-such-entry --reason "x"` runs against a
  queue with no `## q-no-such-entry` block
- **THEN** nothing is written and the verb exits non-zero naming the missing
  block

## MODIFIED Requirements

### Requirement: Queue answer verb
id: wiki-queue-answer-verb
base: 715581109c2b

`spec_status.py` SHALL provide a `wiki-queue-answer <slug> --answer "<text>"`
verb that resolves the workspace store exactly as `wiki-queue-add` does,
accepts the bare slug (prefixing `q-` itself), locates the `## q-<slug>` block
in `queue.md`, and replaces its `- Answer: pending` line with
`- Answer: <text>`, printing the `q-<slug>` and exiting 0. Where the verb is
invoked with an `--advisory` flag, it SHALL store the answer with an
`advisory: ` prefix — `- Answer: advisory: <text>` — marking the captured
knowledge as advisory rather than binding; without the flag the answer is
stored unprefixed as before. If the store or the block is missing, or the
block's `Answer:` line is not `pending`, then the verb SHALL write nothing
and exit non-zero naming the reason — an answered block is owned by the
`/s:teach` drain and is never overwritten. The verb SHALL use only the Python
standard library.

#### Scenario: Pending block is answered
- **GIVEN** a queue block `## q-retention` whose answer line is
  `- Answer: pending`
- **WHEN** `wiki-queue-answer retention --answer "prune after one release"`
  runs
- **THEN** the block's answer line reads
  `- Answer: prune after one release`, and the verb prints `q-retention` and
  exits 0

#### Scenario: Advisory flag prefixes the stored answer
- **GIVEN** a pending queue block `## q-pr-unlock`
- **WHEN** `wiki-queue-answer pr-unlock --advisory --answer "always run the
  unlock"` runs
- **THEN** the block's answer line reads
  `- Answer: advisory: always run the unlock` and the verb exits 0

#### Scenario: Missing block errors
- **WHEN** `wiki-queue-answer no-such-entry --answer "x"` runs against a queue
  with no `## q-no-such-entry` block
- **THEN** nothing is written and the verb exits non-zero naming the missing
  block

#### Scenario: Already-answered block is refused
- **GIVEN** a queue block whose `Answer:` line is not `pending`
- **WHEN** `wiki-queue-answer` targets that block
- **THEN** nothing is written and the verb exits non-zero naming the
  already-answered state

### Requirement: Wiki auto-commit
id: wiki-autocommit
base: aa95ef020cb1

When an engine wiki write succeeds — a staged `wiki` emission installing
its file set, `wiki-queue-add` appending a valid block, `wiki-queue-answer`
writing an answer into a block, or `wiki-queue-discard` removing a pending
block — and the store directory sits inside a git work tree, the engine SHALL
make a local git commit scoped to exactly the files the write touched,
sweeping in no other staged or modified content. While the store is not
inside a git work tree, the write SHALL succeed unchanged with no commit
attempted. If the commit fails or the write changed no bytes, then the write
SHALL still exit zero, with a stderr warning for a failed commit. The engine
SHALL run only local git (`status`, `add`, `commit`) and SHALL never push,
pull, or fetch. A failed write SHALL produce no commit.

#### Scenario: Successful emit commits its file set
- **GIVEN** a workspace repo under git with a configured identity
- **WHEN** `spec_emit.py wiki --from <staging>` installs a page and
  `index.md`
- **THEN** a new commit exists containing exactly the installed store files

#### Scenario: Queue append commits queue.md
- **WHEN** `wiki-queue-add stale-cache …` appends a block in a
  git-initialized workspace with a configured identity
- **THEN** a new commit with subject `shipd-wiki: queue-add q-stale-cache`
  contains only `queue.md`

#### Scenario: Queue answer commits queue.md
- **WHEN** `wiki-queue-answer stale-cache --answer "…"` succeeds in a
  git-initialized workspace with a configured identity
- **THEN** a new commit contains only `queue.md`

#### Scenario: Queue discard commits queue.md
- **WHEN** `wiki-queue-discard stale-cache --reason "…"` succeeds in a
  git-initialized workspace with a configured identity
- **THEN** a new commit with subject
  `shipd-wiki: queue-discard q-stale-cache` contains only `queue.md`

#### Scenario: Non-git store writes without committing
- **WHEN** a wiki emit runs in a workspace that is not inside a git work
  tree
- **THEN** the content installs, the exit code is zero, and no commit is
  attempted

#### Scenario: Commit failure never fails the write
- **WHEN** the scoped commit cannot be made (e.g. no git identity)
- **THEN** the write still exits zero with the content installed and a
  warning on stderr

#### Scenario: Unrelated staged state is not swept
- **GIVEN** an unrelated file staged in the workspace repo's index
- **WHEN** a wiki emit auto-commits
- **THEN** the resulting commit omits the unrelated file, which remains
  staged and uncommitted
