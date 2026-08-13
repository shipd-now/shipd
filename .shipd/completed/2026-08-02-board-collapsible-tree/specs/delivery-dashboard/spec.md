## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: 1061d7bbc763

The dashboard CLI SHALL provide a `tui` verb rendering the board full-screen with
`curses` as an interactive portfolio board: a collapsible left hierarchy panel
grouping changes under their initiative → epic (the epic's `Theme` shown as a
colour-coded label, never a grouping level) beside a right kanban whose columns
are the lifecycle states (`unplanned`, `ready`, `building`, `review`, `shipped`)
holding colour-coded, risk-chipped member cards. Each initiative and epic node in
the hierarchy panel SHALL be individually collapsible, carrying an
expand/collapse marker (`▾` expanded, `▸` collapsed) and starting expanded: a
collapsed initiative hides its epics and their members, and a collapsed epic
hides its theme and members. The `shipped` column SHALL group its cards under
collapsible per-epic headers — each header carrying the same marker, a collapsed
group hiding its cards — while the other four columns remain flat. Hierarchy-node
collapse and shipped-group collapse SHALL be independent states. The verb SHALL
support keyboard control (arrow-key navigation, Enter to act or expand/collapse
the focused node, a key to toggle the whole hierarchy panel, `q` to quit) and
mouse control (clickable regions for the `[<]`/`[>]` panel toggle, node and
shipped-group expand/collapse toggles, tree rows, and card action buttons),
re-aggregating and redrawing every `--interval` seconds (default 2). The board
layout — its positioned lines and its clickable regions — SHALL be computed by a
pure function testable without a terminal, taking the panel-open, collapsed-node,
and collapsed-shipped-group state as inputs; `curses` SHALL be imported lazily
inside the verb so importing the dashboard module needs no terminal. Where the
terminal reports no mouse events, the board SHALL run keyboard-only rather than
fail.

#### Scenario: Collapsing an initiative hides its epics
- **GIVEN** a board with an initiative group holding an epic
- **WHEN** the layout runs with that initiative's node key in the collapsed set
- **THEN** the initiative row is emitted with a `▸` marker and none of its epics
  or their members appear in the panel

#### Scenario: Collapsing an epic hides its members
- **WHEN** the layout runs with an epic's node key in the collapsed set
- **THEN** the epic row is emitted with a `▸` marker and none of that epic's
  theme or member rows appear, while its sibling epics still render expanded

#### Scenario: Shipped column groups under collapsible epic headers
- **GIVEN** two epics each with a shipped member
- **WHEN** the layout runs
- **THEN** the `shipped` column shows a per-epic header region (action
  `toggle_shipped_group`) with a `▾` marker above that epic's shipped cards, and
  the other columns carry no such headers

#### Scenario: A collapsed shipped group hides its cards
- **WHEN** the layout runs with an epic's slug in the collapsed-shipped set
- **THEN** that epic's `shipped` header shows a `▸` marker and none of its
  shipped cards are placed, while another epic's shipped cards still render

#### Scenario: Panel and shipped collapse are independent
- **GIVEN** an epic collapsed in the hierarchy panel's collapsed-node set but not
  in the collapsed-shipped set
- **WHEN** the layout runs
- **THEN** the epic's panel members are hidden but its `shipped` group's cards
  are still placed

#### Scenario: Layout is pure and takes collapse state
- **WHEN** the pure layout function runs with explicit panel-open, collapsed-node,
  and collapsed-shipped-group inputs
- **THEN** it returns positioned lines and clickable regions — including
  `toggle_node` and `toggle_shipped_group` regions — with no terminal interaction

#### Scenario: Module import needs no curses
- **WHEN** the dashboard module is imported
- **THEN** no `curses` import occurs until the `tui` verb runs
