## ADDED Requirements

### Requirement: External consumers are read at a named ref
id: external-consumer-refs

Where the review checks a consumer of a changed contract in a repository
other than the reviewed one, the `/s:review` skill SHALL read that consumer
only with an explicit ref. Where a pull request is in scope, it SHALL first
list the linked pull requests with `review_gate.py linked`, and SHALL read the
consumer at each listed head before the default branch.

If a listed head migrates the consumer, then the skill SHALL raise no
un-updated-consumer finding and SHALL name that pull request in the
walkthrough. If no ref migrates it, then the finding SHALL keep its rubric
severity and its `why` SHALL name every ref read. If a lookup fails, then the
skill SHALL record a could-not-verify entry naming the consumer, and SHALL NOT
raise a `high` or `medium` finding from a default-branch read alone.

The check's name, "Consumers in another repository", SHALL be stated inline in
`SKILL.md` among the downstream-impact checks. Its procedure SHALL live in
`references/call-site-tracing.md` under a `## Consumers in another repository`
heading. The posting reference's named-pull-request flow SHALL name
`review_gate.py linked`. `plugins/s/harness/bodies/review.md` SHALL state, in
its call-site step, that a consumer in another repository is read with an
explicit `?ref=` at each head the cross-reference timeline call returns, and
that a failed read never blocks. `SKILL.md` SHALL stay under its 340-line
ceiling.

#### Scenario: The check is named inline
- **WHEN** `SKILL.md` is read outside its References table
- **THEN** it names "Consumers in another repository" among the
  downstream-impact checks, and holds fewer than 340 lines

#### Scenario: The reference carries the procedure
- **WHEN** `references/call-site-tracing.md` is read
- **THEN** it holds a `## Consumers in another repository` section naming
  `review_gate.py linked`, the `?ref=` read, the no-finding outcome for a
  migrating head, and the could-not-verify outcome for a failed lookup

#### Scenario: The posting flow names the verb
- **WHEN** `references/posting.md` is read
- **THEN** its fetch step names `review_gate.py linked`

#### Scenario: The harness body carries the rule
- **WHEN** `plugins/s/harness/bodies/review.md` is read
- **THEN** its call-site step names a consumer in another repository, the
  `?ref=` read, and the issue timeline call

### Requirement: Linked pull requests verb
id: linked-prs-verb

`review_gate.py` SHALL provide a read-only verb
`linked <pr> [--repo <owner>/<repo>] [--search <terms>]` that prints one JSON
array to stdout and exits 0. Each entry SHALL carry `repo`, `number`, `url`,
`state`, `head_sha` and `source`. The verb SHALL mutate nothing on GitHub.

The verb SHALL gather entries from three sources in this order: pull requests
GitHub cross-references on the reviewed pull request's timeline (`source`
`cross-reference`); pull request URLs in the reviewed pull request's body
(`source` `body`); and, where `--repo` is given, that repository's open pull
requests matching `--search` (`source` `search`). Where one pull request
arrives from two sources, the verb SHALL list it once under the earlier
source. The verb SHALL NOT list the reviewed pull request itself. Where
`--repo` is given, the verb SHALL list only pull requests in that repository.
Where `--search` is given without `--repo`, the verb SHALL exit non-zero.

For a cross-referenced or body-linked pull request, the verb SHALL read its
head commit and state from GitHub; `state` SHALL be `merged` for a merged pull
request, else `open` or `closed`. If that read fails, then the entry SHALL
carry a null `head_sha`, a `state` of `unknown`, and an `error` field. If the
timeline read fails, then the verb SHALL exit 1, write an error line to
stderr, and print nothing to stdout.

#### Scenario: A cross-referenced migration is listed with its head
- **WHEN** an open pull request `acme/consumer#406` cross-references the
  reviewed pull request and `linked <pr> --repo acme/consumer` runs
- **THEN** the output is one entry with `repo` `acme/consumer`, `number` 406,
  `state` `open`, `source` `cross-reference`, and that pull request's head
  commit as `head_sha`

#### Scenario: A body link is listed
- **WHEN** the reviewed pull request's body holds the URL of a pull request
  that no timeline event names
- **THEN** the output lists that pull request with `source` `body`

#### Scenario: A duplicate is listed once
- **WHEN** one pull request arrives from the timeline and from the body
- **THEN** the output lists it once, with `source` `cross-reference`

#### Scenario: The repository filter drops other repositories
- **WHEN** cross-references arrive from two repositories and `--repo` names
  one of them
- **THEN** the output lists only the pull requests in the named repository

#### Scenario: An open pull request found by search is listed
- **WHEN** `linked <pr> --repo acme/consumer --search expectedRevision` runs
  and the repository holds an open pull request matching the terms that
  nothing links
- **THEN** the output lists it with `source` `search` and its head commit

#### Scenario: An unreadable linked pull request stays visible
- **WHEN** the read of a cross-referenced pull request fails
- **THEN** its entry carries a null `head_sha`, `state` `unknown`, and an
  `error` field, and the verb exits 0

#### Scenario: A failed timeline read fails the verb
- **WHEN** the timeline read returns a non-zero exit
- **THEN** the verb exits 1 with an error line on stderr and an empty stdout

#### Scenario: Nothing linked prints an empty array
- **WHEN** the timeline holds no cross-reference, the body holds no pull
  request URL, and no `--repo` is given
- **THEN** the verb prints `[]` and exits 0

#### Scenario: Search without a repository is refused
- **WHEN** `linked <pr> --search foo` runs with no `--repo`
- **THEN** the verb exits non-zero and calls `gh` zero times

### Requirement: External-consumer change ships tests, docs, and a version bump
id: external-consumer-ships

The `linked` verb SHALL be covered by tests in
`plugins/s/skills/review/tests/test_review_gate.py` that inject the fake `gh`
seam and perform no network access. The review text rule SHALL be pinned by
tests in `plugins/s/skills/review/tests/test_skill_references.py`.
`docs/semantic-review-reference.md` SHALL carry a `## The linked verb` section
listing the verb's flags and entry fields, and SHALL stay at 250 lines or
fewer. `docs/semantic-review.md` SHALL state, under
`## Severity and the blocking rule`, that a consumer in another repository is
read at a named ref before it can block, and SHALL stay at 100 lines or fewer.
The plugin version in `plugins/s/.claude-plugin/plugin.json` SHALL be bumped.

#### Scenario: The suites pass
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/review/tests` and
  `python3 -m unittest discover -s plugins/s/skills/build/tests` run
- **THEN** both report `OK`, and the first includes the `linked` verb tests

#### Scenario: The reference documents the verb
- **WHEN** `docs/semantic-review-reference.md` is read
- **THEN** it holds a `## The linked verb` section naming `--repo`,
  `--search`, and the six entry fields, and `docs_lint.py` passes on it

#### Scenario: The main page states the rule
- **WHEN** `docs/semantic-review.md` is read
- **THEN** its `## Severity and the blocking rule` section states the
  named-ref rule for a consumer in another repository, in 100 lines or fewer
  for the page

#### Scenario: The version moves
- **WHEN** the change's diff against `main` is read
- **THEN** `plugins/s/.claude-plugin/plugin.json` carries a higher `version`
