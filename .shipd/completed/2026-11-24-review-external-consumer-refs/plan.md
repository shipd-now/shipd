# review-external-consumer-refs
Status: verified
Planned-at: f255df52c8b6835760efca58d16c4494d5aaa5a2
Gated-hash: 398348e947f3

## Idea

Make `/s:review` read a consumer in another repository at a named ref, linked
pull request heads first, before it reports that consumer as un-updated.

### Motivation

Authors of coordinated cross-repository changes cannot trust a blocking
verdict: a reviewer read a consumer at its default branch and requested
changes while the migration pull request was already open. The review prompt
gives a cross-repository lookup no ref procedure, so the reviewer improvised a
read with no `ref`.

### Details

- Add a read-only `review_gate.py linked <pr>` verb. It lists the pull requests
  linked to the reviewed one, each with its repository, state and head commit.
- Add a "Consumers in another repository" check to the review skill: its name
  inline in `SKILL.md`, its procedure in `references/call-site-tracing.md`.
- Point the named-PR posting flow at the verb.
- State the same rule on the two parallel rubric surfaces, the Copilot skill
  and the harness review body.
- Pin the verb with a fake-`gh` test that replays the incident, and pin the
  text with structure tests.
- Document the verb and the rule, and bump the plugin version.

Affected capabilities: `semantic-review` (three requirements added),
`copilot-review-skill` (one added). Impact:
`plugins/s/skills/review/scripts/review_gate.py`, the review skill's
`SKILL.md`, `references/call-site-tracing.md` and `references/posting.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/harness/bodies/review.md`, two test modules, two docs pages, and
`plugins/s/.claude-plugin/plugin.json`. No new dependency.

### Non-goals

- No poster-side check that a finding carries ref evidence; `post` keeps
  deriving the verdict from severity and category alone.
- No headless eval case and no new grader; no test exercises the reviewer's
  own judgement.
- No change to the severity rubric's levels or to the status mapping.
- No clone or fetch of another repository; reads go through `gh api`.
- No ReviewBench run as part of this change.

## Implementation

- **The verb lives in `review_gate.py`, not `semdiff.py`.** `semdiff` never
  touches the network (`SKILL.md:25-28`); `review_gate.py` already owns every
  `gh` call and has the `FakeGh` seam. Rejected: a `semdiff` subcommand, which
  would break that guarantee.
- **Verb shape.** `linked <pr> [--repo <owner>/<repo>] [--search <terms>]`
  prints one JSON array and exits 0, mutating nothing. Each entry holds
  `repo`, `number`, `url`, `state` (`open`, `closed`, `merged` or `unknown`),
  `head_sha` and `source`. `--search` needs `--repo`; argparse rejects it
  alone.
- **Three sources, in this order, first source wins on a duplicate.**
  1. `cross-reference` — `gh api repos/<repo>/issues/<n>/timeline --paginate`,
     keeping `cross-referenced` events whose `source.issue.pull_request` is
     set.
  2. `body` — every `https://github.com/<owner>/<repo>/pull/<n>` URL in the
     reviewed pull request's body, read with `gh pr view <pr> --json body`.
  3. `search` — only with `--repo`:
     `gh pr list --repo <repo> --state open --search <terms> --json
     number,url,headRefOid`, with `--search` omitted when no terms are given.
  The reviewed pull request itself is never listed. With `--repo`, entries
  from sources 1 and 2 in other repositories are dropped.
- **Head commits for sources 1 and 2** come from
  `gh api repos/<repo>/pulls/<n>`: `head.sha`, and `state` set to `merged`
  where `merged` is true. A failed read keeps the entry with `head_sha` null,
  `state` `unknown`, and an `error` field holding the first stderr line. The
  reviewer then knows a linked pull request exists that it could not read.
- **A failed timeline read fails the verb**: exit 1, a `review_gate.py:` line
  on stderr, nothing on stdout. The reviewer records a could-not-verify entry.
- **The rule is a procedure with an exit, never a bare prohibition.**
  `test_skill_references.py:461-466` records that a prohibition the reviewer
  cannot satisfy makes it drop the whole finding. Every branch therefore names
  what to do: no finding, a finding with refs, or a could-not-verify entry.
- **Outcomes.** A linked or open head that migrates the consumer: no
  un-updated-consumer finding, and the walkthrough names that pull request.
  No ref migrates it: the finding stands at its rubric severity and its `why`
  names every ref read. A failed lookup: a could-not-verify entry, and no
  `high` or `medium` finding from a default-branch read alone.
- **Text placement.** `SKILL.md` holds 336 lines under a tested ceiling of 340
  (`test_skill_references.py:478`), so it gains one line, the check's name.
  The procedure goes in `call-site-tracing.md`, which shipd-factory already
  loads whole (`plugins/s/external-loaders.json`); no manifest change.
- **Exact wording is fixed** in `artefacts/review-text.md`, blocks A to E.
  Executors insert each block verbatim.
- **The Copilot skill and the harness body name the raw `gh api` timeline
  call**, not the verb: neither surface ships `review_gate.py`.
- **Test fixtures use invented names** (`acme/consumer`, pull request 406).
  No real organization name enters the repository.

Risk: any new review-prompt text can shift what the reviewer hunts. The guard
is the size of the edit: one inline line, with the detail in a reference that
loads only when a consumer is chased.

Risk: `--search` matches a pull request's title and body, not its diff, so an
unlinked migration with an unrelated title stays invisible. The finding then
names the refs it read, so a reader can see what was checked.

## Questions and answers

### Q1: How is the external-consumer rule pinned by a regression test?
- **Question:** How should shipd pin the rule that the review reads a
  consumer in another repository at a linked pull request's head? Options:
  (1) a new read-only verb unit-tested with the fake `gh`, plus text tests;
  (2) text tests only; (3) a headless eval case with a new grader.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: the new verb plus text tests. It is deterministic,
  runs in CI, and replays the incident without spending tokens.
- **Queued:** q-review-external-consumer-regression-test

### Q2: May an un-migrated external consumer block when no migration exists?
- **Question:** A consumer in another repository is still on the old
  contract and no linked or open pull request migrates it. May the finding
  block? Options: (1) block, stating every ref checked; (2) never block on a
  consumer outside the reviewed repository; (3) block only when a spec or the
  description names the consumer. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: the finding keeps its severity and may request
  changes, and it names every ref it checked.
- **Queued:** q-review-external-consumer-no-migration-severity

## Readiness attestation

### Problem and motivation

A reviewer read a consumer in another repository at its default branch and
blocked a pull request whose migration was already open. Authors of
coordinated cross-repository changes cannot trust a blocking verdict until the
reviewer reads the right commit.

Evidence:

- The request's trace: a `gh api .../contents/...` read with no `ref`, then a
  `high` finding and a changes-requested review.
- `plugins/s/skills/review/SKILL.md:108-116` chases consumers through
  `context` only, which searches the reviewed repository.
- `plugins/s/skills/review/references/call-site-tracing.md:5-13` carries no
  rule for a consumer in another repository.
- `plugins/s/skills/review/references/posting.md:64-90` resolves and fetches
  the target pull request alone.

### Scope and non-goals

The change adds one read-only poster verb, one review rule on three prompt
surfaces, tests, docs, and a version bump. It adds no poster-side evidence
check, no eval case, and no change to how severity maps to the status.

Evidence:

- In scope: capability `semantic-review` (skill, poster, harness body) and
  capability `copilot-review-skill` (the vendored skill template).
- Out of scope: `semantic-review` requirement `gate-verdict-from-severity`
  stays as it is; `evals/` is not edited.

### Affected capabilities and files

Two capabilities gain requirements, and eleven files change: the poster and
its tests, five prompt files, the text tests, two docs pages, and the plugin
manifest.

Evidence:

- Capability `semantic-review`: added `external-consumer-refs`,
  `linked-prs-verb`, `external-consumer-ships`.
- Capability `copilot-review-skill`: added `copilot-external-consumer-refs`.
- Files: `plugins/s/skills/review/scripts/review_gate.py:1809-1876` (verb
  table), `plugins/s/skills/review/tests/test_review_gate.py:96-200`
  (`FakeGh`), `plugins/s/skills/review/tests/test_skill_references.py:106-112`
  and `:478`, `plugins/s/skills/review/SKILL.md:108-116`,
  `references/call-site-tracing.md:5-13`, `references/posting.md:78-90`,
  `plugins/s/integrations/copilot/SKILL.md:59-68`,
  `plugins/s/harness/bodies/review.md:32-39`,
  `docs/semantic-review-reference.md:138`, `docs/semantic-review.md:32-45`,
  `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `gh api repos/shipd-now/shipd/issues/445/timeline
  --paginate` filtered to `cross-referenced` exited 0 and returned an event
  carrying `source.issue.repository.full_name`, `source.issue.number`,
  `source.issue.state` and a non-null `source.issue.pull_request`.
- Runnable premise: `gh api repos/shipd-now/shipd/pulls/445` exited 0 and
  returned `head.sha`, `state` and `merged`.
- Runnable premise: `gh api 'repos/shipd-now/shipd/contents/README.md?ref=f255df52'`
  exited 0 and returned the blob at that commit.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/review/tests` ran 374 tests and printed `OK`.

### No open task-shaping decision

Two decisions existed and the user settled both. The rest came from the
request and the repository.

Evidence:

- Regression-test form (a new verb plus text tests): settled by the user, Q1.
- Blocking when no migration exists (allowed, with refs stated): settled by
  the user, Q2.
- An open migration pull request means no finding: settled by the request.
- Verb home, text placement, and parity surfaces: settled by investigation.
