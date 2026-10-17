## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: cef9c0c5d9b0
Dropped: The review is submitted as a comment

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting one inline comment for every location, across every finding's
`locations` array, that anchors to a RIGHT-side commentable line of the pull
request diff, folding into the summary any finding none of whose locations
anchor, retrying once with no inline comments if the review POST is rejected,
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

Where a finding declares its fix confident and supplies a replacement covering
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
- **WHEN** a finding declares its fix confident with a replacement covering
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
- **WHEN** `post` publishes a `changes-requested` verdict whose findings each
  name one location that anchors to the diff
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

### Requirement: Branded review submission body
id: gate-review-submission-body
base: 1b9595a0aa29

`review_gate.py post` SHALL submit its pull request review with a body that
opens with the speaker heading `### ☕ shipd · semantic-review · reviewer (for
@<login>)`, where `<login>` is read once per post from `gh api user`, followed
on the next line by one plain sentence pointing at the summary comment. The
body SHALL no longer read `Semantic review — see the summary comment for the
full report.`. If the login read fails, the heading SHALL drop the `(for @<login>)`
segment and the post SHALL proceed. The review event follows the `gate-review-event` requirement; inline comments, summary
comment, and commit status SHALL be unchanged.

#### Scenario: Submission body carries the heading
- **WHEN** the poster submits a review with inline comments and `gh api user`
  returns login `mikkel`
- **THEN** the submitted body's first line is
  `### ☕ shipd · semantic-review · reviewer (for @mikkel)` and the old
  sentence is absent

#### Scenario: A failed login read still submits
- **WHEN** `gh api user` fails during `post`
- **THEN** the review is still submitted, its heading is
  `### ☕ shipd · semantic-review · reviewer`, and the event is `COMMENT` because the acting login is unknown
