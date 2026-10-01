## ADDED Requirements

### Requirement: Card project marker
id: board-card-project-marker

The `tui` board's task card SHALL derive its **project** as the card's epic
project when non-null, else the member row's own `project` field, else null.
While that project is non-null, the card SHALL close its single-row text with
a muted `[<project>]` marker — the same escaped, `$fg-muted` markup the epic
group header uses — after the slug and after any live stage or signal label,
in every grouping mode (`epic`, `initiative`, and `none`) and in every card
branch (risk glyph, shipped `✓`, signalling, driving, live build). While the
project is null, the card text SHALL be byte-identical to its pre-marker
form. The lane signature SHALL fold each member row's own `project` field in
addition to the epic project it already carries, so a standalone row whose
project changes repaints its lane. When a card opens the member detail modal,
it SHALL pass its project, and the modal's badge row SHALL end with a muted
`project: <slug>` badge while the project is non-null and carry no project
badge otherwise.

#### Scenario: A project epic member's card carries the marker
- **GIVEN** a card for a member of an epic whose project is `cai`
- **WHEN** the card text renders
- **THEN** it ends with the escaped muted `[cai]` marker after the slug

#### Scenario: A root-universe card is unchanged
- **GIVEN** a card whose epic project is null and whose member row carries no
  project
- **WHEN** the card text renders
- **THEN** it is byte-identical to the text rendered before this requirement

#### Scenario: A project standalone row carries the marker
- **GIVEN** a standalone row aggregated from project `shipd`
- **WHEN** its card renders under the `standalone` group
- **THEN** the card text ends with the escaped muted `[shipd]` marker

#### Scenario: The marker follows the stage suffix
- **GIVEN** a driving member of a project epic whose roster entry names stage
  `gate`
- **WHEN** the card text renders
- **THEN** the muted stage suffix precedes the project marker

#### Scenario: Flat and initiative modes keep the marker
- **GIVEN** a mounted board with a project epic member, in grouping mode
  `none` and again in `initiative`
- **WHEN** the lanes render
- **THEN** the member's card text carries the project marker in both modes

#### Scenario: A standalone row's project change repaints
- **GIVEN** two lane contents identical except for one standalone row's
  `project` field
- **WHEN** their lane signatures are computed
- **THEN** the signatures differ

#### Scenario: The modal names the project
- **GIVEN** a project epic member's card
- **WHEN** the card opens the member detail modal
- **THEN** the badge row ends with a muted `project: <slug>` badge

#### Scenario: A root member's modal has no project badge
- **GIVEN** a root-universe member's card
- **WHEN** the card opens the member detail modal
- **THEN** no badge in the badge row starts with `project:`

## MODIFIED Requirements

### Requirement: Board filter strip
id: board-filter-strip
base: 95bbdec877e9

The `tui` board SHALL mount a **filter strip** row between the header bar and
the lanes, carrying: a totals label, the active filter chips with a
`+ filter` control, a shipped-this-week label, and a synced-ago label. The
totals label SHALL report the **full** board aggregation — the member count,
the epic count, and the distinct-initiative count — and SHALL NOT shrink
while search or filters narrow the visible board. When `f` is pressed on the
board (or the `+ filter` control is activated), the app SHALL push a modal
**filter picker** listing the available filter options — the risk tiers
`high`/`medium`/`low`, each epic slug, each initiative slug, and each distinct
project slug on the board (epics in board order, then standalone rows; a null
project contributes none), excluding already-active chips — and SHALL dismiss
it without effect on `escape`; while a modal screen is already open, `f`
SHALL be inert. When a picker option is selected, the app SHALL add a
removable chip for it to the strip; when a chip is activated, the app SHALL
remove it and restore the members it excluded. While chips are active, each
lane SHALL mount only the members passing **every** active filter kind, where
a member passes a kind when it matches **at least one** of that kind's chip
values (`risk` against the member's risk rating, `epic` against its epic's
slug, `initiative` against its epic's initiative slug, `project` against the
member's project as the card derives it — a null project never matches),
composed with the live search query (both must keep a member); a group none
of whose members pass SHALL mount no group header, and a lane left empty
SHALL show its empty-state text. The filter set SHALL be view-level state
only — `build_board` aggregation and the launch builders are unchanged, chips
never persist — and SHALL fold into the diff-aware lane signatures, so a chip
change always repaints and an unchanged refresh under steady chips repaints
nothing. The strip SHALL also show `▲ N shipped this week` — N derived from
the delivery-metrics ship events as the count shipped since the Monday (UTC)
of the current ISO week, via a **dependency-free** helper (no `textual`)
defined ahead of the module's `textual` import — and a synced-ago label
derived from the time of the last interval refresh, both re-evaluated on
every refresh.

#### Scenario: The strip mounts with totals and stats
- **WHEN** the app is mounted
- **THEN** the filter strip sits between the header bar and the lanes,
  showing the full-board totals, the `+ filter` control, the
  shipped-this-week label, and the synced-ago label

#### Scenario: f opens the filter picker
- **WHEN** `f` is pressed on the mounted board
- **THEN** the filter picker modal is pushed, listing risk tiers, epic slugs,
  and initiative slugs as selectable options

#### Scenario: The picker offers project slugs
- **GIVEN** a board with epics from projects `cai` and `shipd` and a
  standalone row from `shipd`
- **WHEN** the filter picker opens
- **THEN** it lists `project: cai` and `project: shipd` once each, after the
  initiative options

#### Scenario: Already-active options are not offered
- **GIVEN** an active `risk:high` chip
- **WHEN** the filter picker opens
- **THEN** the `risk high` option is absent while the other options remain

#### Scenario: Escape cancels the picker
- **GIVEN** the open filter picker
- **WHEN** `escape` is pressed
- **THEN** the picker is dismissed and no chip is added

#### Scenario: Selecting an option adds a filtering chip
- **GIVEN** a board with members of differing risk ratings
- **WHEN** the `risk high` option is selected in the picker
- **THEN** a removable `risk:high` chip appears in the strip and the lanes
  mount only high-risk members

#### Scenario: A project chip keeps only that project's members
- **GIVEN** an active `project:cai` chip on a board holding `cai` members,
  `shipd` members, and root-universe members
- **WHEN** the lanes render
- **THEN** only the `cai` members are mounted

#### Scenario: A root-universe member never matches a project chip
- **GIVEN** an active `project` chip of any value
- **WHEN** a member whose project is null is tested
- **THEN** it is excluded

#### Scenario: Same-kind chips widen the filter
- **GIVEN** active `risk:high` and `risk:medium` chips
- **WHEN** the lanes render
- **THEN** members matching either rating are mounted

#### Scenario: Cross-kind chips narrow the filter
- **GIVEN** an active `risk:high` chip and an active `epic` chip
- **WHEN** the lanes render
- **THEN** only high-risk members of that epic are mounted

#### Scenario: Chips compose with the live search
- **GIVEN** an active chip and an active search query
- **WHEN** the lanes render
- **THEN** only members kept by both the chip and the query are mounted

#### Scenario: Removing a chip restores its members
- **GIVEN** an active chip excluding some members
- **WHEN** the chip is activated
- **THEN** the chip leaves the strip and the excluded members remount

#### Scenario: A fully filtered group mounts no header
- **GIVEN** a grouping mode is active and chips exclude every member of one
  group
- **WHEN** the lanes render
- **THEN** no group header for that group is mounted in any lane

#### Scenario: An unchanged refresh under steady chips repaints nothing
- **GIVEN** active chips and a board whose aggregation is unchanged
- **WHEN** the interval refresh runs
- **THEN** the lanes retain their existing card widget instances and the
  chips stay applied

#### Scenario: Totals stay full-board while narrowed
- **GIVEN** chips or a query narrowing the visible board
- **WHEN** the strip renders
- **THEN** the totals label still reports the full board's member, epic, and
  initiative counts

#### Scenario: Shipped-this-week counts the current ISO week
- **GIVEN** ship events inside and before the current ISO week (Monday, UTC)
- **WHEN** the dependency-free counter runs with an injected now
- **THEN** it counts only the events on/after that Monday, without `textual`

#### Scenario: The synced label reflects the last refresh
- **WHEN** an interval refresh completes
- **THEN** the synced-ago label reports the age of that refresh
