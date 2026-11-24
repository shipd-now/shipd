## MODIFIED Requirements

### Requirement: Linked pull requests verb
id: linked-prs-verb
base: 782d753461e0

`review_gate.py` SHALL provide a read-only verb
`linked <pr> [--repo <owner>/<repo>] [--search <terms>]` that prints one JSON
array to stdout and exits 0. Each entry SHALL carry `repo`, `number`, `url`,
`state`, `head_sha` and `source`. The verb SHALL mutate nothing on GitHub.

The verb SHALL take the reviewed pull request's repository from the URL that
resolving `<pr>` returns, never from the current checkout. It SHALL read the
timeline of that repository.

The verb SHALL gather entries from three sources in this order: pull requests
GitHub cross-references on the reviewed pull request's timeline (`source`
`cross-reference`); pull requests the reviewed pull request's body names, by
URL or by `<owner>/<repo>#<number>` shorthand (`source` `body`); and, where
`--repo` is given, that repository's open pull requests, narrowed to those
matching `--search` where it is given (`source` `search`). Where one pull
request arrives from two sources, the verb SHALL list it once under the
earlier source. The verb SHALL NOT list the reviewed pull request itself.
Where `--repo` is given, the verb SHALL list only pull requests in that
repository. Where `--search` is given without `--repo`, the verb SHALL exit
non-zero.

The search source SHALL request up to 200 open pull requests. If the listing
returns 200, then the verb SHALL write one warning line to stderr naming the
limit and the repository, and SHALL still print the array and exit 0.

For a cross-referenced or body-named pull request, the verb SHALL read its
head commit and state from GitHub; `state` SHALL be `merged` for a merged pull
request, else `open` or `closed`. If that read fails, then the entry SHALL
carry a null `head_sha`, a `state` of `unknown`, and an `error` field. If the
timeline read fails, then the verb SHALL exit 1, write an error line to
stderr, and print nothing to stdout.

#### Scenario: A cross-referenced migration is listed with its head
- **WHEN** an open pull request `acme/consumer#406` cross-references the
  reviewed pull request and `linked <pr> --repo acme/consumer` runs
- **THEN** the output holds an entry with `repo` `acme/consumer`, `number`
  406, `state` `open`, `source` `cross-reference`, and that pull request's
  head commit as `head_sha`

#### Scenario: A body link is listed
- **WHEN** the reviewed pull request's body holds the URL of a pull request
  that no timeline event names
- **THEN** the output lists that pull request with `source` `body`

#### Scenario: A body shorthand reference is listed
- **WHEN** the reviewed pull request's body holds `acme/consumer#407` and no
  timeline event names that pull request
- **THEN** the output lists `acme/consumer` number 407 with `source` `body`

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
- **THEN** the output lists it with `source` `search` and its head commit,
  and the listing call carries `--search expectedRevision` and `--limit 200`

#### Scenario: A repository with no search terms lists its open pull requests
- **WHEN** `linked <pr> --repo acme/consumer` runs with no `--search`
- **THEN** the listing call carries `--limit 200` and no `--search`, and each
  open pull request it returns is listed with `source` `search`

#### Scenario: A full listing warns
- **WHEN** the listing call returns 200 pull requests
- **THEN** stderr holds one warning line naming 200 and `acme/consumer`, the
  array prints, and the verb exits 0

#### Scenario: A short listing stays silent
- **WHEN** the listing call returns fewer than 200 pull requests
- **THEN** stderr is empty

#### Scenario: A URL in another repository reads that repository
- **WHEN** `<pr>` resolves to `https://github.com/other/repo/pull/7` and the
  current checkout is a different repository
- **THEN** the verb reads the timeline at `repos/other/repo/issues/7/timeline`
  and makes no `gh repo view` call

#### Scenario: A timeline spanning two pages is read whole
- **WHEN** the timeline read prints two JSON arrays back to back, each
  holding one cross-reference
- **THEN** the output lists both pull requests

#### Scenario: A merged pull request reads as merged
- **WHEN** a cross-referenced pull request's read returns `merged` true
- **THEN** its entry carries `state` `merged`

#### Scenario: An unreadable linked pull request stays visible
- **WHEN** the read of a cross-referenced pull request fails
- **THEN** its entry carries a null `head_sha`, `state` `unknown`, and an
  `error` field, and the verb exits 0

#### Scenario: A failed timeline read fails the verb
- **WHEN** the timeline read returns a non-zero exit
- **THEN** the verb exits 1 with an error line on stderr and an empty stdout

#### Scenario: Nothing linked prints an empty array
- **WHEN** the timeline holds no cross-reference, the body names no pull
  request, and no `--repo` is given
- **THEN** the verb prints `[]` and exits 0

#### Scenario: Search without a repository is refused
- **WHEN** `linked <pr> --search foo` runs with no `--repo`
- **THEN** the verb exits non-zero and calls `gh` zero times

## ADDED Requirements

### Requirement: Linked verb hardening ships tests, docs, and a version bump
id: linked-hardening-ships

Each scenario of `linked-prs-verb` SHALL be covered by a test in
`plugins/s/skills/review/tests/test_review_gate.py` that injects the fake `gh`
seam and performs no network access. The `## The linked verb` section of
`docs/semantic-review-reference.md` SHALL state that `--repo` alone lists
every open pull request in that repository, that `--search` narrows the
listing, that the listing stops at 200 with a warning, and that the body
source reads URLs and `<owner>/<repo>#<number>` shorthand; the page SHALL stay
at 250 lines or fewer. The posting reference's `linked` call SHALL carry
`--search <symbol>`. `references/call-site-tracing.md` SHALL tell the reviewer
what to do when the verb warns of a full listing. The plugin version SHALL be
bumped.

#### Scenario: The suites pass
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/review/tests` and
  `python3 -m unittest discover -s plugins/s/skills/build/tests` run
- **THEN** both report `OK`

#### Scenario: The reference page describes the search source truthfully
- **WHEN** the `## The linked verb` section is read
- **THEN** it names the 200 limit and its warning, the unfiltered listing
  under `--repo` alone, and the shorthand form, and `docs_lint.py` exits 0 on
  the page

#### Scenario: The posting call narrows the search
- **WHEN** `references/posting.md` is read
- **THEN** its `review_gate.py linked` call carries `--search <symbol>`

#### Scenario: The reviewer is told how to treat the warning
- **WHEN** `references/call-site-tracing.md` is read
- **THEN** its `## Consumers in another repository` section names the full
  listing warning and directs a narrower `--search`

#### Scenario: The version moves
- **WHEN** the change's diff against `main` is read
- **THEN** `plugins/s/.claude-plugin/plugin.json` carries a higher `version`
