## ADDED Requirements

### Requirement: Board completed retention
id: board-completed-retention

The board aggregation SHALL, by default, resolve a retention window through
the layered `completed_retention_days` key (shipd-config
completed-retention-key) from the invocation root and hide: each epic whose
status is `complete` and whose completion date is older than the window, and
each standalone change whose state is `archived` and whose archive date is
older than the window. An epic's completion date SHALL derive from the newest
`YYYY-MM-DD-<slug>` archive-directory date stamp among its stub members, each
probed under its hosting location's content directory (a location whose
configuration is unreadable contributing no date); a standalone change's date
SHALL derive from its own newest archive directory. Older-than SHALL compare
local calendar dates — hidden when the date precedes today minus the window.
If a candidate yields no parseable archive date, then it SHALL NOT be hidden.
Hidden epics SHALL be absent from the board's `epics`, its initiative
`groups`, and every rendered lane; a retained epic's members SHALL never be
individually hidden. The board object SHALL carry the hidden count as
`hidden_completed` and the applied window as `retention_days` (null when
disabled), both included under `--json`. When the hidden count is positive,
the text board SHALL end with a one-line note naming the count and the key,
and the TUI's shipped lane header SHALL carry the count. While the board is
scoped by `--epic`, retention SHALL NOT apply. The `board` and `tui` verbs
SHALL accept `--all`, disabling retention for that invocation; with retention
disabled — by `--all`, a `0`/`null` key, or an `--epic` scope — nothing is
hidden and the hidden count is zero. If the invocation root's configuration is
unreadable, then the default resolution SHALL treat retention as disabled —
the board renders unfiltered, hiding nothing and raising no error — rather
than failing the aggregation.

#### Scenario: An old complete epic is hidden with a note
- **GIVEN** a 30-day window and a `complete` epic whose newest member archive
  is stamped 40 days ago
- **WHEN** the text board renders
- **THEN** the epic is absent and the final line notes one older completed
  item hidden, naming `completed_retention_days`

#### Scenario: A recent complete epic is retained
- **GIVEN** a 30-day window and a `complete` epic whose newest member archive
  is stamped 5 days ago
- **WHEN** the board is built
- **THEN** the epic appears and the hidden count is zero

#### Scenario: A live epic keeps its old archived members
- **GIVEN** an `active` epic with one member archived 40 days ago and one
  member still building
- **WHEN** the board is built
- **THEN** the epic and both members appear, the archived member in the
  shipped lane

#### Scenario: An old archived standalone change is hidden
- **GIVEN** a standalone change in state `archived` whose archive directory is
  stamped 40 days ago
- **WHEN** the board is built
- **THEN** the standalone list omits it and the hidden count includes it

#### Scenario: --all shows everything
- **GIVEN** a board that hides an old complete epic by default
- **WHEN** the board verb runs with `--all`
- **THEN** the epic appears and the hidden count is zero

#### Scenario: An epic-scoped board is never filtered
- **GIVEN** a `complete` epic completed 40 days ago
- **WHEN** the board is built scoped to that epic via `--epic`
- **THEN** the epic is aggregated and rendered

#### Scenario: A zero window disables hiding
- **GIVEN** a layer declaring `"completed_retention_days": 0` and an epic
  completed 400 days ago
- **WHEN** the board is built
- **THEN** the epic appears and the hidden count is zero

#### Scenario: An undatable complete epic is retained
- **GIVEN** a `complete` epic none of whose members yields a parseable archive
  date
- **WHEN** the board is built under a 30-day window
- **THEN** the epic appears on the board

#### Scenario: JSON carries the retention fields
- **WHEN** `board --json` runs with one epic hidden under a 30-day window
- **THEN** the document's `hidden_completed` is 1 and `retention_days` is 30

#### Scenario: The shipped lane header carries the count
- **GIVEN** a TUI board whose aggregation hid two older completed items
- **WHEN** the lanes render
- **THEN** the shipped lane's header text includes the count 2

#### Scenario: An unreadable root config fails open
- **GIVEN** an invocation root whose `.shipd-config.json` is malformed JSON
- **WHEN** the board is built with default retention resolution
- **THEN** the board renders with nothing hidden, `retention_days` null, and
  no traceback or error is raised by the resolution
