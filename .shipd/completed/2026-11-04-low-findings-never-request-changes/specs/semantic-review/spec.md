## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: 15f9d6c1afc2

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting one inline comment for every location, across the `locations` array
of every `high`- or `medium`-severity finding, that anchors to a RIGHT-side
commentable line of the pull request diff, folding into the summary every
`low` finding and any finding none of whose locations anchor, retrying once with no inline comments if the review POST is rejected,
submitting that review with the event the `gate-review-event` requirement selects, and setting a commit status
with context `semantic-review` on the pull request's head SHA.

A finding declaring more than one location SHALL carry a stable identity per
location — so each recurring site is dispositioned independently of its
siblings — while a finding declaring exactly one location SHALL keep the same
identity it carried before this requirement's locations array existed, so
prior disposition continuity is unaffected. An inline comment for a location
other than `locations[0]` SHALL additionally name the finding's other
locations, so a reader reaches the full recurrence from any one posted
comment.

An anchored inline comment's leading severity marker SHALL carry the severity's
🔴/🟠/🟡 dot directly before the severity word, and each bullet of the summary
comment's folded-findings section SHALL carry that same dot before its severity.
The marker's literal format SHALL live in exactly one place, shared by the body
renderer and by `parse_severity`, so the pair cannot drift. `parse_severity`
SHALL read a severity whether or not the marker carries the dot, so a finding
comment posted before this change is still classified rather than reported as
unparseable.

A `low` finding SHALL NOT be posted as an inline comment, whatever its
locations: an inline comment opens a review thread that a repository requiring
conversation resolution would let block a merge the rubric says a `low` never
blocks, so the poster folds it into the summary as the CI gate workflow does.

Where a `high`- or `medium`-severity finding declares its fix confident and supplies a replacement covering
one or more contiguous whole lines that anchor `locations[0]` to a RIGHT-side
commentable line, that location's inline comment SHALL carry the replacement
as a committable `suggestion` block so the fix can be applied without
retyping. A suggestion SHALL NOT attach to any location other than
`locations[0]` — a suggestion is a single-range edit that cannot replay
identically across sites whose surrounding code differs. A finding whose
replacement is absent, covers part of a line, spans a discontiguous range, or
whose `locations[0]` does not anchor SHALL render as prose instead. Emitting a
suggestion SHALL NOT change the comment's leading severity marker, and the
`--json` mode SHALL stay free of emoji and prose.

#### Scenario: The marker round-trips with its dot
- **WHEN** an inline body is rendered for each of `high`, `medium` and `low` and
  read back with `parse_severity`
- **THEN** each body's marker carries the matching dot and each parse returns
  the severity it was rendered from

#### Scenario: A dotless marker still parses
- **WHEN** `parse_severity` reads an inline comment body whose marker carries no
  dot, as posted before this change
- **THEN** it returns that body's severity rather than nothing

#### Scenario: A confident whole-line fix becomes committable
- **WHEN** a `medium` finding declares its fix confident with a replacement covering
  contiguous whole lines that anchor `locations[0]` to the diff
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: A multi-line replacement is supported
- **WHEN** a confident finding's replacement covers more than one contiguous
  whole line
- **THEN** the suggestion block carries every one of those lines

#### Scenario: An unanchorable fix stays prose
- **WHEN** a finding declares its fix confident but none of its locations
  anchor to a RIGHT-side commentable line
- **THEN** it is folded into the summary and carries no suggestion block

#### Scenario: A partial-line fix stays prose
- **WHEN** a confident finding's replacement covers part of a line rather than
  whole lines
- **THEN** its comment carries no suggestion block

#### Scenario: The severity marker is unchanged by a suggestion
- **WHEN** an inline comment carries a suggestion block
- **THEN** its body still opens with the shared severity marker that
  `parse_severity` reads

#### Scenario: Pass verdict posts green
- **WHEN** `post` publishes a `pass` verdict to a pull request that carries no
  marker comment yet
- **THEN** a summary comment carrying the marker is created and the head SHA's
  `semantic-review` status state is `success`

#### Scenario: Red verdict anchors findings inline
- **WHEN** `post` publishes a `changes-requested` verdict whose `high` and
  `medium` findings each name one location that anchors to the diff
- **THEN** one inline comment is posted per finding at its anchored location

#### Scenario: Re-post updates instead of stacking
- **WHEN** `post` runs twice for the same pull request
- **THEN** the second run edits the existing marker summary comment rather
  than creating a second one

#### Scenario: Legacy-marker summary is updated, not duplicated
- **WHEN** a pull request already carries a summary comment with the legacy
  marker
- **THEN** `post` edits that comment in place and writes only the current
  marker

#### Scenario: High-only greens over mediums
- **WHEN** `post` runs with `--disposition high-only` over a review carrying
  only medium and low findings
- **THEN** the commit status is `success`

#### Scenario: High-only stays red on a high
- **WHEN** `post` runs with `--disposition high-only` over a review carrying
  one high finding
- **THEN** the commit status is `failure`

#### Scenario: None is always green and stays honest
- **WHEN** `post` runs with `--disposition none` over a review carrying a
  `changes-requested` verdict
- **THEN** the commit status is `success` and the findings still render in
  full

#### Scenario: A multi-location finding posts one comment per anchorable site
- **WHEN** a finding's `locations` array names two sites that both anchor to
  RIGHT-side commentable lines in two different files
- **THEN** the poster submits one inline comment for each site, each carrying
  the finding's what/why/fix and each carrying its own distinct identity
  marker

#### Scenario: A partly-anchorable multi-location finding keeps its anchorable site
- **WHEN** a finding's `locations` array names one site that anchors and one
  that does not
- **THEN** the poster posts an inline comment for the anchorable site alone,
  and the finding is not folded into the summary's "Additional findings"
  section

#### Scenario: A fully off-diff multi-location finding is folded whole
- **WHEN** none of a finding's `locations` anchor to a RIGHT-side commentable
  line
- **THEN** the finding is folded into the summary's "Additional findings"
  section and no inline comment is posted for it

#### Scenario: A low finding on a diff line folds into the summary
- **WHEN** `post` publishes a `low` finding whose location anchors to a
  RIGHT-side commentable line
- **THEN** no inline comment is posted for it and it appears in the summary's
  "Additional findings" section with its 🟡 dot

## ADDED Requirements

### Requirement: The poster derives the verdict from counted findings
id: gate-verdict-from-severity

`review_gate.py post` SHALL derive the review's effective verdict from the
payload and the pull request's diff rather than trusting the payload's
`verdict` field. A finding SHALL be *already there* when it carries a
`category` other than `untouched-caller` or `spec-coverage`, every one of its
`locations` parses to a path and a line, and no location is touched; a
location SHALL be touched when its path is in the pull request's file list
and either that file carries no readable patch or the line is a RIGHT-side
line inside one of the file's diff hunks (an added or context line). Every other finding SHALL be *counted*. The effective verdict SHALL be
`changes-requested` when any counted finding's severity is `high` or
`medium`, or is present and not one of `high`, `medium`, `low`, or when any
`spec_coverage` entry's state is `unmet`, and `pass` otherwise; a finding
with no severity SHALL count as `low`. The blocking severities SHALL be
declared in exactly one place in the poster. The commit status (under every
disposition scope), the review event, the summary's `## Findings` header,
the status description, and fast-pass eligibility SHALL all read the
effective verdict and the counted findings only. When the effective verdict
differs from the payload's `verdict`, the poster SHALL print one line naming
both.

The summary SHALL list already-there findings under a `### Already there,
reached by this change` section, each with its severity dot, location, what,
why and fix, SHALL NOT repeat them under "Additional findings", SHALL suffix
each one's summary-table row with `(already there)`, and the status
description SHALL count them separately as `N already there`.

#### Scenario: Low-only findings approve
- **WHEN** `post` publishes a `changes-requested` payload whose only findings
  are `low`, under the default scope, to a pull request authored by another
  login
- **THEN** the status is `success`, the review event is `APPROVE`, the header
  reads `✅ Ship it`, and a reconciliation line is printed

#### Scenario: A medium finding still requests changes
- **WHEN** `post` publishes a `pass` payload carrying one `medium` finding on
  a changed line
- **THEN** the status is `failure` and the review event is `REQUEST_CHANGES`

#### Scenario: A high finding in an untouched file never requests changes
- **WHEN** `post` publishes a `changes-requested` payload whose only finding
  is a `high` `security` finding located in a file the pull request does not
  change
- **THEN** the status is `success`, the event is `APPROVE`, and the summary
  lists the finding under `Already there, reached by this change`

#### Scenario: A finding outside the hunks of a changed file is already there
- **WHEN** a `medium` `bug` finding's only location is a line of a changed
  file that lies outside every hunk of that file's patch
- **THEN** it is already there and the status is `success`

#### Scenario: A finding on a context line still counts
- **WHEN** a `medium` finding's location is an unchanged context line inside
  a hunk
- **THEN** it is counted and the status is `failure`

#### Scenario: A broken untouched caller still blocks
- **WHEN** a `high` finding of category `untouched-caller` sits in a file the
  pull request does not change
- **THEN** it is counted and the status is `failure`

#### Scenario: A finding without a parsable line still counts
- **WHEN** a `high` finding's only location names a path with no line
- **THEN** it is counted and the status is `failure`

#### Scenario: An unmet scenario blocks without a finding
- **WHEN** `post` publishes a `pass` payload with no findings and one
  `spec_coverage` entry whose state is `unmet`
- **THEN** the status is `failure`

#### Scenario: An unknown severity blocks
- **WHEN** `post` publishes a payload whose only counted finding has severity
  `critical`
- **THEN** the status is `failure`

#### Scenario: A consistent payload prints no reconciliation
- **WHEN** `post` publishes a `pass` payload whose only findings are `low`
- **THEN** the status is `success` and no reconciliation line is printed

### Requirement: Folded findings carry no per-finding disposition
id: folded-findings-disposition

Under every disposition scope the skill's disposition loop SHALL act only on
findings the poster posted as review threads. A `low` finding and an
already-there finding SHALL carry no thread, so the loop SHALL author no reply
for them, the resolve verb's unresolved count SHALL never include them, and
under `all` the loop MAY implement a folded finding but SHALL NOT be required
to. A thread posted for a `low` finding before this change SHALL keep being
handled by the reply, autoreply, resolve and prior verbs as before.

#### Scenario: A low-only review needs no disposition
- **GIVEN** the invoker asked for the findings to be dispositioned under scope
  `all`
- **WHEN** the posted review carries only `low` findings
- **THEN** no reply is authored and the resolve verb reports an unresolved
  count of zero

#### Scenario: A legacy low thread is still resolvable
- **WHEN** a pull request carries a `low` finding thread posted before this
  change and the autoreply verb runs under `high-only`
- **THEN** that thread receives the canonical reply as before

### Requirement: Low-findings change ships docs, tests, and a version bump
id: low-findings-docs-version

The change SHALL replace the tests pinning a low-only `changes-requested`
payload to `failure` and a `low` finding to an inline comment with tests of
this change's scenarios, update `review/references/posting.md`,
`review/references/json-output.md`, `review/SKILL.md`,
`docs/semantic-review-reference.md`, and `docs/copilot-review-reference.md`
to describe the counted-findings verdict, folded lows, and the already-there
section, and advance the plugin version in
`plugins/s/.claude-plugin/plugin.json` by one patch above the value `main`
carries.

#### Scenario: Docs name the derived verdict
- **WHEN** `review/references/posting.md` is read
- **THEN** it states that the status ignores `low` and already-there findings
  and that `low` findings are folded into the summary rather than threaded

#### Scenario: The version advances
- **WHEN** the change's pull request is compared with `main`
- **THEN** `plugins/s/.claude-plugin/plugin.json` carries a version one patch
  above `main`'s
