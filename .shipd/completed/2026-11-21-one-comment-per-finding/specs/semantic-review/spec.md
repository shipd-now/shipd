## MODIFIED Requirements

### Requirement: PR posting of a review verdict
id: gate-poster
base: c4d268a334db
Dropped: A multi-location finding posts one comment per anchorable site

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting exactly one inline comment for every `high`- or `medium`-severity
finding any of whose `locations` anchors to a RIGHT-side commentable line of
the pull request diff, anchored at the first such location in `locations`
order, folding into the summary every
`low` finding and any finding none of whose locations anchor, retrying once with no inline comments if the review POST is rejected,
submitting that review with the event the `gate-review-event` requirement selects, and setting a commit status
with context `semantic-review` on the pull request's head SHA.

A finding declaring more than one location SHALL post no second inline
comment, and its one inline comment SHALL name every other location of the
finding on an `Also recurs at:` line, so a reader reaches the full recurrence
from the one posted comment and the room holds one task per finding. That
comment SHALL carry the identity the per-location scheme gives its anchored
site — the location's path and `what`, plus the location's index when the
finding declares more than one location — so a finding declaring exactly one
location, or anchored at `locations[0]`, keeps the identity it carried before.
Where `--room-agent` is passed, the comment's room task data SHALL carry the
finding's full `locations` list beside the anchored `path` and `line`.

Where a multi-location finding is folded into the summary's "Additional
findings" or "Already there, reached by this change" section, its bullet SHALL
name `locations[0]` and then every other location on an `Also recurs at:`
line, so every location appears somewhere in the posted text. The summary
table row MAY keep the compact `(+N more)` form.

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
whose one inline comment anchors at a location other than `locations[0]`
SHALL render as prose instead. Emitting a
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

#### Scenario: A multi-location finding posts one comment
- **WHEN** a `medium` finding's `locations` array names
  `public/js/ui/progress.js:90` and `public/js/ui/progress.js:92`, both on
  RIGHT-side commentable lines
- **THEN** the poster submits one inline comment for the finding, anchored at
  line 90, whose body carries `Also recurs at: public/js/ui/progress.js:92`
  and the identity marker a single-location finding at that path and `what`
  would carry

#### Scenario: An off-diff first location anchors at the next site
- **WHEN** a confident finding's `locations[0]` does not anchor and its
  `locations[1]` does
- **THEN** one inline comment is posted at `locations[1]`, its
  `Also recurs at:` line names `locations[0]`, and it carries no suggestion
  block

#### Scenario: One room task per finding
- **WHEN** `post --room-agent <name>` publishes a finding with two anchorable
  locations
- **THEN** exactly one inline comment carries a room Message, and its data
  part's `locations` lists both sites

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

#### Scenario: A folded finding names every location
- **WHEN** a finding with locations `z.py:99`, `y.py:88` and `x.py:77` is
  folded into "Additional findings"
- **THEN** its bullet names `z.py:99` and carries
  `Also recurs at: y.py:88, x.py:77`

#### Scenario: A low finding on a diff line folds into the summary
- **WHEN** `post` publishes a `low` finding whose location anchors to a
  RIGHT-side commentable line
- **THEN** no inline comment is posted for it and it appears in the summary's
  "Additional findings" section with its 🟡 dot

### Requirement: Incremental gate review
id: review-incremental
base: 2362742d864e

Each inline finding comment the poster renders SHALL carry a hidden identity
marker of the form `<!-- shipd-finding <hash> -->`, where `<hash>` is the first
twelve hexadecimal characters of the SHA-256 of the finding's `location` path,
a newline, and its `what` text lowercased with whitespace runs collapsed to a
single space. The marker SHALL be the body's last element, never its first, so
the severity marker stays the opening token `parse_severity` reads. The hash
SHALL NOT incorporate a line number, so a finding whose line moved still
matches. A finding declaring more than one location SHALL additionally add
the location's index to the hashed text for every location after
`locations[0]`, and the finding's identities SHALL be the hashes of all its
locations so computed, which includes the hash of every per-location thread
posted before one comment per finding.

The system SHALL provide `review_gate.py prior <pr>`, emitting one JSON entry
per gate-authored review thread carrying the thread's `hash` (or null where the
body has no marker), `path`, `severity`, `what`, `thread_id`, `resolved`, and a
`disposition` of `replied`, `autoreplied`, `commit-only`, or `none`. A thread
whose non-root comments are all exactly one of the canonical `autoreply` bodies
SHALL classify `autoreplied`; a thread carrying any other reply SHALL classify
`replied`; a thread with no reply but a commit landed after its creation SHALL
classify `commit-only`; a thread with neither SHALL classify `none`. Given
`--from <review-json|->`, each entry SHALL also carry `finding`: the `id` of
the first payload finding one of whose identities equals the entry's `hash`,
or null. The verb SHALL decide nothing about suppression and SHALL mutate
nothing.

The `/s:review` skill, **when and only when posting to a pull request**, SHALL
read `prior --from` back before reporting and omit a finding that some
`replied` entry names in `finding`, whichever of the finding's locations that
thread was posted at. It SHALL NOT omit a finding matching any other
classification, and SHALL state in its report how many findings it omitted and
which pull request answered them. A review that is not posting SHALL read
nothing back and omit nothing.

`SKILL.md` SHALL state this trigger in the `Load when` cell of its existing
`posting.md` References row, adding no line.

#### Scenario: A reworded finding is reported again
- **WHEN** a prior thread was answered with a reasoned reply and the new review
  produces a finding at the same path whose `what` text differs
- **THEN** the hashes differ and the new finding is reported

#### Scenario: A dismissed finding is omitted on the next head
- **WHEN** a prior thread carries a reasoned reply and the new review produces
  a finding whose path and `what` match it
- **THEN** the finding is omitted and the report states one finding was omitted
  and names the pull request

#### Scenario: An implemented finding that recurs is reported
- **WHEN** a prior thread's only disposition evidence is a commit landed after
  its creation, and the same finding recurs
- **THEN** the thread classifies `commit-only` and the finding is reported,
  because a recurrence after a fix is a regression

#### Scenario: An auto-dispositioned finding is reported
- **WHEN** a prior thread's only replies are the canonical `autoreply` body
- **THEN** the thread classifies `autoreplied` and the finding is reported

#### Scenario: An old per-location thread maps to its finding
- **WHEN** a pull request carries two gate threads posted per location for
  one finding with locations `a.py:5` and `b.py:9`, and `prior --from` reads a
  payload holding that finding with id `f1`
- **THEN** both entries carry `finding` `f1`

#### Scenario: A reply on a later site suppresses the finding
- **WHEN** only the old thread at the finding's second location carries a
  reasoned reply
- **THEN** that entry classifies `replied` with `finding` naming the finding,
  so the finding is omitted rather than posted again

#### Scenario: Old sibling threads resolve unchanged
- **WHEN** `resolve` runs on a pull request whose old per-location threads for
  one finding each carry a later commit
- **THEN** each of those threads is resolved and none is reported
  undispositioned

#### Scenario: A moved line still matches
- **WHEN** a dismissed finding recurs at the same path with identical `what`
  text but a different line number
- **THEN** the hashes match and the finding is omitted

#### Scenario: The severity marker survives the identity marker
- **WHEN** a body rendered with an identity marker is passed to
  `parse_severity`
- **THEN** it returns the finding's severity, unchanged by the marker

#### Scenario: A pre-push review reads nothing back
- **WHEN** a review runs without a posting request
- **THEN** no `prior` call is made and no finding is omitted

#### Scenario: The trigger costs no line
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured and its References
  table inspected
- **THEN** the file is within the line ceiling
  `review-skill-references` owns and the `posting.md` row's `Load when`
  cell states the read-back trigger
