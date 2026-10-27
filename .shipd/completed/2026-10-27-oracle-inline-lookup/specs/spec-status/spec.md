## ADDED Requirements

### Requirement: Oracle lookup verb
id: oracle-lookup-verb

The status CLI SHALL provide `oracle-lookup <term> [<term>...]`, a read-only
verb that runs the oracle's whole search ladder in one call and prints compact
matching snippets. It SHALL search in this ladder order: (1) the personal
memory store's pages, skipped when no personal store exists; (2) the workspace
chain's stores nearest first — or the repo-local fallback store where no
workspace is discoverable — each store's pages, then its answered queue
blocks (a `## q-<slug>` block whose `Answer:` value is not `pending`); (3) the
base store named on `wiki-show`'s `base:` line, its pages then its answered
queue blocks, only when that store is present; (4) the spec surfaces —
verified capability specs, the `## Decisions` and `## Design` sections of
epics, and research reports — of the focus project's present repos first
where the registry declares a `focus` project, then of the invocation root.

The matching unit SHALL be a paragraph (a blank-line-separated block) of a
page or spec surface, or a whole queue block. A unit SHALL match when it
contains, case-insensitively, at least two distinct terms, or the one term
when only one is given. Within a rung, matches SHALL rank by distinct terms
hit, then by total hits.

Each printed page or spec snippet SHALL be a verbatim substring of its unit
with runs of whitespace collapsed to one space, clipped to at most 400
characters around the first term hit. A queue-block snippet SHALL instead
read `Question: <question> Answer: <answer>`, each field verbatim, clipped the
same way, so the position survives the clip. Each snippet SHALL carry the citation an oracle answer
uses: `[[slug]] (personal)` for a personal page; `[[slug]]` for a page from
the nearest store; `[[slug]] (inherited <ws-root>)` for a page from an
enclosing chain store; `[[slug]] (base)` for a base page; `queue q-<slug>`
for an answered queue block, with the same `(inherited <ws-root>)` or
`(base)` suffix where it applies; and `verified/<capability>
(<requirement-id>)`, `epic/<slug>`, or `research/<slug>` for a spec surface.
A snippet whose source carries an advisory marker — a queue `Answer:` value
beginning `advisory: `, or a page holding an `Authority: advisory` line —
SHALL be tagged `[advisory]`.

The verb SHALL print at most four snippets per rung and SHALL stop adding
snippets once its output reaches 6000 characters, ending with one line that
counts the matches it omitted. It SHALL also print, under a heading marked as
not evidence, the id and question of the pending queue blocks in the nearest
store that match the terms — at most four, best-ranked first — so the caller can check for a duplicate before
queueing. Where no rung yields a match, the verb SHALL end its output with a
line stating that no evidence was found and the verdict is `INSUFFICIENT`. A
missing store, an unreadable file, or an unresolvable workspace SHALL skip
that surface silently and be named as skipped on the header line. The verb
SHALL exit 0 whenever its arguments parse, and SHALL write nothing.

#### Scenario: Personal page prints first with its marker
- **GIVEN** a personal store page and a workspace page that both match
- **WHEN** `oracle-lookup` runs
- **THEN** the personal snippet prints first, cited `[[slug]] (personal)`

#### Scenario: Absent personal store is skipped
- **WHEN** `oracle-lookup` runs where no personal store exists
- **THEN** the header line names the personal rung as skipped and the verb
  exits 0

#### Scenario: Inherited page carries the inherited marker
- **GIVEN** nested workspaces where only the outer store holds a matching
  page
- **WHEN** `oracle-lookup` runs from a repo under the inner workspace
- **THEN** the snippet is cited `[[slug]] (inherited <outer-ws-root>)`

#### Scenario: Answered queue block is evidence and pending is listed apart
- **GIVEN** a store queue holding one answered and one pending block that
  both match
- **WHEN** `oracle-lookup` runs
- **THEN** the answered block prints as a snippet cited `queue q-<slug>`, and
  the pending block appears only under the not-evidence heading

#### Scenario: Advisory source is tagged
- **WHEN** a matching queue block's `Answer:` value begins `advisory: `
- **THEN** its snippet carries the `[advisory]` tag

#### Scenario: Present base store is searched and marked
- **GIVEN** a workspace whose `wiki-show` reports a present base store
  holding a matching page
- **WHEN** `oracle-lookup` runs
- **THEN** the snippet prints under the base rung cited `[[slug]] (base)`

#### Scenario: Verified requirement is cited by capability and id
- **WHEN** a matching paragraph sits inside a verified spec's requirement
  `foo-bar` of capability `widgets`
- **THEN** its snippet is cited `verified/widgets (foo-bar)`

#### Scenario: Bare repo searches the fallback store
- **GIVEN** a repo with a content directory and no discoverable workspace,
  whose fallback store holds a matching page
- **WHEN** `oracle-lookup` runs
- **THEN** the page's snippet prints under the workspace rung cited
  `[[slug]]`

#### Scenario: No match names the INSUFFICIENT verdict
- **WHEN** `oracle-lookup zzz-none qqq-none` runs and nothing matches
- **THEN** the last line states that no evidence was found and the verdict
  is `INSUFFICIENT`, and the exit code is 0

#### Scenario: Output stays within its cap
- **WHEN** more than twenty units match
- **THEN** each rung prints at most four snippets, the output stays near
  6000 characters, and a final line counts the omitted matches
