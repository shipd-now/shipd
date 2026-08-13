# epic-grouped-board
Status: verified

## Idea

Replace the board's left hierarchy tree with an in-board **group-by-epic** mode:
remove the panel, and — via a toggle in a new controls strip above the lanes
(default **on**) — group every lifecycle lane's cards under collapsible per-epic
headers. Each header names the epic (slug, status, and its initiative) over a
plain gray band with black separator lines, and carries a clickable run control
that fires the epic-level autopilot — the affordance the tree's `r` key used to
own.

### Motivation

The hierarchy panel was a passive, redundant index: every change already appears
in a lane, clicking a tree node did nothing, and it cost 34 columns. Its only
unique value was structural grouping (initiative → epic) and epic-level run. This
change folds both of those *into the board itself* — epics become collapsible,
labelled, runnable groups inside the lanes — so the structure and the run action
live where the work is, and the redundant tree goes away.

### Details

- **Remove the hierarchy panel:** delete `HierarchyTree`, `_render_tree`, the
  `#hierarchy-panel` from `compose`, the `_tree_sig` diff state, and the `p`
  panel-toggle binding/action.
- **Controls strip + toggle:** a thin strip above the lanes holds a
  **group-by-epic** toggle control (default on), also toggled by a footer-bound
  key. App state `group_by_epic` drives rendering.
- **Group within lanes:** when on, each lane groups its cards under a collapsible
  per-epic header (one group per epic, board order); when off, flat lanes as
  today. This **generalises** the existing shipped-lane-only grouping to all five
  lanes.
- **Header content:** epic slug + status + initiative (when the epic has one).
- **Visual:** plain gray group background with black separator lines between
  groups — no per-status colour (drop the `Collapsible.status-*` title colours).
- **Epic run via header:** a clickable run control in each epic header fires the
  epic-level run; it must not also toggle collapse.

Affected capability: `delivery-dashboard` — modified `board-tui` (panel removed,
controls strip added), new `board-epic-grouping`. Impact:
`plugins/s/skills/build/scripts/dashboard.py` (compose/CSS, lane rendering,
the shipped-group generalisation, remove the tree), the textual tests in
`tests_textual/`; plugin version bump. Data layer (`build_board`, aggregation,
`build_epic_run_launch`) unchanged.

### Non-goals

- No epic-**detail** dialog and no change to the card spec-detail modal (Enter/
  click still opens it; `board-tui`'s modal behavior is untouched).
- No change to the `board`/`html` verbs or `board-actions`' launch builders — the
  epic-run launch function is reused as-is; only its trigger moves.
- No per-epic distinct colours; no reordering of lanes or the lifecycle model.
- No filtering/collapsing-all controls beyond the single group-by-epic toggle.

## Implementation

- **Toggle + strip.** Add a `group_by_epic` bool on `BoardApp` (default `True`).
  Mount a controls strip above the `Horizontal` of lanes holding a toggle widget
  (a `Checkbox`/`Switch` labelled "group by epic") whose change handler flips
  `group_by_epic` and repaints the lanes; also bind a footer key (the freed `p`
  is available, or `g`) to the same toggle. Reflect the current state in the
  widget.
- **Generalise the grouping.** `_render_lanes` currently special-cases the
  `shipped` lane through `_mount_shipped_group` (per-epic `Collapsible`s) and
  mounts every other lane flat. Refactor so that **when `group_by_epic` is on**,
  *every* lane mounts through a shared per-epic grouping path (the generalised
  `_mount_shipped_group`), and **when off**, every lane mounts flat. `shipped`
  loses its always-grouped special case — it now follows the global toggle like
  the others.
- **Group header.** Extend the per-epic `Collapsible` title to include the epic's
  initiative when present — the epic's initiative is available in the aggregated
  board (`epic["initiative"]`); thread it into the grouping path alongside the
  epic slug/status already there (`_lane_contents` yields `(epic_slug,
  epic_status, member, entry)` — extend it to also carry the initiative, or look
  it up from the board by epic slug at mount time). Add a clickable **run
  control** inside the header: reuse the in-header `Button` pattern from the
  spec-detail modal's `✕` (a `Button` with a distinct id, e.g. `run-epic-<slug>`)
  handled in `on_button_pressed` → `self.dispatch_epic_run(slug)`; keep it
  separate from the `Collapsible`'s own collapse toggle so a run click does not
  collapse the group.
- **Visual.** Replace the `Collapsible.status-*` title-colour CSS with a uniform
  gray group background and a black separator (e.g. a bottom border / `Rule`
  between groups). The gray should read like the reference banding
  (subtle panel-gray, black divider lines).
- **Diff-aware refresh.** Fold `group_by_epic` into the per-lane signature
  (`_lane_signature`) so toggling the mode (and any group-membership change)
  repaints the affected lanes, while an idle board with unchanged grouping still
  does not repaint and collapsed groups stay collapsed. Remove `_tree_sig` and
  the tree repaint from `refresh_board`.
- **Remove the tree.** Delete `HierarchyTree`, `_render_tree`, `action_toggle_
  panel`, the `#hierarchy-panel` CSS/compose, and the `p`→panel binding. The
  epic-run dispatch (`dispatch_epic_run`) stays — it just gets called from the
  header run control instead of the tree's `r` action.

### Test seams (tests_textual)

- Mount the app: assert no hierarchy panel is present, the controls strip + toggle
  are, and grouping is on by default (lanes render per-epic `Collapsible`s).
- A lane with two epics renders two epic groups, each header naming its epic and
  (for an epic with an initiative) its initiative.
- Toggling the control (or key) off re-renders lanes flat (no `Collapsible`s);
  on re-groups.
- Clicking a header's run control dispatches the epic run (assert via the
  injectable launch/dispatch seam) and leaves the group's `collapsed` unchanged.
- A collapsed group hides its cards; an unchanged-board refresh keeps it collapsed
  (diff-aware).
- Removing the tree does not touch the data layer: `build_board` and the
  dependency-free suites stay green (`autopilot` still imports without textual).

Risk: moderate-to-high for a UI change — it removes a whole widget subtree and
reshapes lane rendering — but the data layer, the spec-detail modal, and the
epic-run launch builder are all untouched, and the grouping generalises code
(`_mount_shipped_group`) that already exists and is tested.
