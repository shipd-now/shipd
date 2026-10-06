## MODIFIED Requirements

### Requirement: Semantic review skill
id: review-skill
base: 687d64523303

The plugin SHALL provide an `/s:review` skill that reviews local changes
against a base ref (default `main`, or a named base/head pair) by mapping
cohorts foundational-first, reasoning over the semdiff structural diff
rather than raw file dumps, chasing changed signatures through `semdiff
context`, and reporting findings by cohort, each with one or more locations,
what, why, a concrete fix, and a severity of high, medium, or low. The
rendered report SHALL carry an effort score (1–5), a findings header reading
`## Findings: ✅ Ship it` when no finding is high or medium and
`## Findings: ❌ Fix required` otherwise, a summary table rating findings
with 🔴/🟠/🟡 severity dots, a collapsible walkthrough, and an explicit
list of what could not be verified.

A finding's location SHALL name the line its own fix would change — never a
caller or symptom site the fix does not touch. Where the same defect recurs
at more than one call site, the skill SHALL report one finding whose
locations name every recurring site, rather than one finding per site.

Emoji SHALL appear at four sanctioned sites and nowhere else: the ✅/❌ verdict
marker, the 🔴/🟠/🟡 severity dots of the summary table, the ☕ of the posted
summary comment's `**☕ shipd** semantic review` brand line, and the 🔴/🟠/🟡
dot that prefixes a severity wherever a posted finding names its own severity —
the leading marker of an anchored inline comment, and each bullet of the summary
comment's folded-findings section. Both posting surfaces — `review_gate.py` and
the vendored review-gate workflow at
`plugins/s/integrations/copilot/copilot-review-gate.yml` — SHALL render that
dot, so one finding reads the same whichever surface posted it. The `--json`
payload SHALL stay free of emoji: the dot is added when a finding is rendered,
never carried in the machine object. Branding is shipd-only, and the skill SHALL
NOT modify the repo.

The skill SHALL additionally carry three judgement passes. It SHALL treat a
changed limit, bound, timeout, retry count, buffer size or threshold as a
contract change and chase its consumers through `semdiff context`, and it
SHALL compare two or more parallel implementations the diff touches against
each other, naming any hardening applied to one and not the other. It SHALL
judge every function, class, guard or helper the diff introduces against its
own stated purpose — whether it measures the quantity its limit governs,
whether an escape hatch lapses its guarantee, whether it terminates cheaply
on hostile input, and whether its boundaries and its doc comment agree. It
SHALL run a test-coverage check over each finding it writes, at every
severity, asking whether an existing test would fail if that defect
regressed, and SHALL raise any gap as its own finding in the `test-coverage`
category, which the `--json` finding shape SHALL accept.

The `--json` finding shape's taxonomy field SHALL be named `category`. The
name `cohort` SHALL denote only the architectural grouping `semdiff files`
emits, and the name `kind` SHALL denote only a file's added, deleted or
modified state in `semdiff diff`; no surface SHALL use either word for the
finding taxonomy.

The skill SHALL review an added file's inlined `content` with the rigour it
applies to a hunk, and SHALL NOT pass such a file on its path and line count
alone. Where `content_truncated` is true, it SHALL read the remainder.

The skill SHALL bind its rendered report and its posted summary comment to
the shipd documentation standard, referencing that standard by path rather
than restating any rule, and SHALL name one finding a "finding" throughout.
The harness command body for the review SHALL carry the same three
judgement passes as the skill, so the two surfaces do not drift.

#### Scenario: Blocking verdict matches severities
- **WHEN** a review yields one medium and one low finding
- **THEN** the header reads `## Findings: ❌ Fix required` and the summary
  table rates them 🟠 and 🟡

#### Scenario: A posted finding names its severity with its dot
- **WHEN** `review_gate.py post` renders an anchored inline comment for a high
  finding
- **THEN** the comment's leading severity marker carries 🔴 directly before the
  word `high`

#### Scenario: A folded finding carries the dot too
- **WHEN** the summary comment's folded-findings section renders a medium
  finding
- **THEN** that bullet's severity is prefixed with 🟠

#### Scenario: Both posting surfaces render the dot
- **WHEN** `plugins/s/skills/review/scripts/review_gate.py` and
  `plugins/s/integrations/copilot/copilot-review-gate.yml` are inspected
- **THEN** each renders an inline finding comment whose severity carries the
  matching 🔴/🟠/🟡 dot

#### Scenario: Machine mode for the gate
- **WHEN** the skill is invoked with `--json`
- **THEN** it emits only a JSON object — verdict `changes-requested` iff
  any finding is high or medium, else `pass`, with findings, optional
  spec_coverage, and could_not_verify arrays — and no emoji or prose

#### Scenario: The taxonomy field is named category
- **WHEN** a `--json` review emits a finding
- **THEN** the finding's taxonomy is carried on a `category` key, and no
  finding carries a `cohort` or `kind` key

#### Scenario: The architectural cohort keeps its name
- **WHEN** `semdiff files` output and the skill's reporting instructions are
  inspected
- **THEN** both still name the architectural grouping `cohort`, unchanged by
  the finding-taxonomy rename

#### Scenario: The skill binds the standard by reference
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names `skills/document/references/standard.md` by path and
  restates none of that file's numbered core rules

#### Scenario: The harness body carries the same passes
- **WHEN** `plugins/s/harness/bodies/review.md` is inspected
- **THEN** it instructs the reviewer to chase changed constants, to compare
  parallel sites against each other, to judge newly added code on its own
  terms, and to check test coverage per finding

#### Scenario: A finding anchors at its fix site
- **WHEN** a defect's symptom is observable at a caller but the fix changes a
  different line
- **THEN** the finding's location names the line the fix would change, not
  the caller

#### Scenario: A recurring defect is one finding with every site
- **WHEN** the same defect recurs at more than one call site in the diff
- **THEN** the review reports one finding whose locations name every
  recurring site, not one finding per site

### Requirement: PR posting of a review verdict
id: gate-poster
base: d8d8f12c1059

`review_gate.py post <pr> --from <json|->` SHALL publish a `/s:review --json`
object to the named pull request via `gh`: upserting a single summary comment
identified by the hidden marker `<!-- shipd-semantic-review -->` (editing the
existing marker comment in place on re-runs, and recognizing the legacy marker
`<!-- am-semantic-review -->` on lookup while writing only the current one),
posting one inline comment for every location, across every finding's
`locations` array, that anchors to a RIGHT-side commentable line of the pull
request diff, folding into the summary any finding none of whose locations
anchor, retrying once with no inline comments if the review POST is rejected,
submitting that review with the event `COMMENT`, and setting a commit status
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

#### Scenario: The review is submitted as a comment
- **WHEN** the poster publishes a review for any verdict
- **THEN** the submitted event is `COMMENT`

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
