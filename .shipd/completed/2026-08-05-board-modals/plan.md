# board-modals
Status: verified
Epic: update-ui-look-feel

## Idea

Restyle the board's three modals — spec-detail, epic-detail, and epic-run
confirm — to the Shipd mock: accent title bars with inline close, badge meta
rows, a themed tab strip, per-modal footer key hints, lane badges on epic
member rows, and the modal key map (`⇥` tabs, `j`/`k` scroll, `y` copy slug,
`o` open in `$EDITOR`).

### Motivation

The `update-ui-look-feel` epic ports the Shipd design language to the board,
and the modal layer is the last spec'd chrome still rendering as stacked plain
text with default tabs and no key affordances. The epic's modal-layer design
(accent-bar style, badges, footer hints) and its modal key map are decided but
not yet implemented.

### Details

- Accent title bar on all three modals: a one-row accent band naming the
  modal's subject, with the compact `✕` close inline at its right edge (the
  run-confirm `✕` moves there from its current top-left row).
- Badge meta row of theme-tinted chips — spec-detail: risk, lane, live stage,
  and the epic reference; epic-detail: status, theme, initiative.
- Accent-themed artifact tab strip on the spec-detail modal.
- A one-row muted footer key-hint line per modal.
- Lane badges on epic-detail member rows, colored by each member's derived
  lane.
- Modal keys: `y` copy subject slug, `o` open artifact in `$EDITOR` (suspend
  launch), `⇥` next artifact tab (spec-detail), `j`/`k` scroll.

Affected capabilities: `delivery-dashboard` (modified). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No restyle of `MetricsScreen` or `GraphConfigScreen` — the epic's change
  table scopes this member to the three modals.
- No change to modal behaviors already spec'd: the live-artifact swap,
  worktree-aware artifact resolution, the activity panel, the stall banner,
  and the run-confirm dispatch semantics all survive unchanged.
- No custom Markdown renderer — modal bodies stay `textual`'s `Markdown`
  widget, themed only.
- No new metadata or ID scheme; kebab-case slugs remain the identity `y`
  copies.

## Implementation

- **Title bar as a restyled header row.** Each modal's existing header
  `Horizontal` becomes a one-row `.modal-title-bar` (accent background,
  contrasting foreground) holding the subject title (`width: 1fr`) and the
  existing compact `✕` button inline at the right edge — same widgets and
  wiring, new CSS — so the close-control behavior and the 1-row/3-cell close
  scenarios hold verbatim. Rejected: a custom title-bar widget — nothing
  needs one.
- **Badges are enumerable CSS classes, not computed styles.** Chips are small
  `Static`s classed per value (`badge-risk-high|medium|low`,
  `badge-lane-<lane>`, `badge-muted` for stage/epic/theme/initiative chips)
  with tinted backgrounds through theme variables (the `$risk-*`/`$lane-*`
  variable at 25% as background, the variable itself as text color) — CSS
  cannot parametrize by value and both vocabularies are closed (3 risks, 5
  lanes). Session/actions details stay muted header lines under the badge
  row. Rejected: inline `styles.*` assignment from Python — it bypasses the
  no-hex CSS hygiene test's surface.
- **Lane badge derivation reuses `_member_column`.** `EpicMemberRow` derives
  the member's lane with the exact function the lanes use, so a badge never
  disagrees with the board. Rejected: mapping `state` directly — it diverges
  for driving/parked members.
- **Tab strip themed through variables only.** `TabbedContent`/`Tab` CSS on
  `MemberDetailScreen` colors the active tab and underline with `$accent`
  and inactive tabs with `$fg-muted`, keeping the CSS hygiene test green.
- **Footer hints are per-modal `Static` lines** docked at the container
  bottom, class `modal-footer-hints`, muted tier. Exact strings —
  spec-detail: `⇥ tabs · j/k scroll · o editor · y copy · esc close`;
  epic-detail: `j/k scroll · o editor · y copy · esc close`; run-confirm:
  `esc close`. Rejected: a second `textual` `Footer` — heavier, and styled
  for the app screen rather than a modal.
- **Key bindings live on the modal screens.** `MemberDetailScreen` adds
  `tab` → next artifact tab (wrapping; no-op while the notice shows),
  `j`/`k` → scroll the active tab pane's `VerticalScroll`, `y` → copy the
  member slug, `o` → open the active tab's artifact. `EpicDetailScreen` adds
  `j`/`k` (overview scroll), `y` (epic slug), `o` (its `epic.md`). `y` calls
  `App.copy_to_clipboard`, honoring the epic's slug-identity decision.
  Accepted trade-off: `tab` on the spec-detail screen shadows focus
  traversal there — the epic's key map pins `⇥` to tab cycling, and
  `Escape`/click still dismiss.
- **Editor launch is a pure builder plus the existing suspend executor.**
  `build_editor_launch(path, editor=None)`, defined beside the other launch
  builders, returns `{"mode": "suspend", "argv": [<editor>, <path>], "cwd":
  <dirname(path)>}` with the editor resolved from the `editor` argument,
  else `$EDITOR`, else `vi`; the modals hand it to `App._spawn_launch`,
  whose suspend branch already wraps `App.suspend()`. Always a suspend
  launch, never a tmux window: the epic's key-map decision pins suspend, and
  an editor view is ephemeral (unlike a resumed session). With no artifact
  on disk (spec-detail notice showing, or no `epic.md`), `o` is a no-op.
- **Spec surface.** One ADDED requirement (`board-modal-chrome`) carries the
  new chrome and keys; `board-epic-grouping` is restated MODIFIED solely to
  move the run-confirm `✕` wording from "top-left" into the accent title
  bar. Risk: the restatement drifting from the master — guarded by the
  `base:` hash and by copying the master text verbatim apart from that one
  phrase.
- **Tests.** New `tests_textual` cases per scenario: `run_test` pilot key
  presses for `y`/`⇥`/`j`/`k`/`o` (patching `copy_to_clipboard` and
  `_spawn_launch`), structural queries for the title bars, badge rows, lane
  badges, and hint lines, and CSS assertions on the new classes; the
  existing no-hex hygiene test already scans all three modals' CSS blocks,
  so the new CSS is covered automatically. `build_editor_launch` is asserted
  in the existing launch-builder test group. The stdlib-only `tests/` suite
  is untouched and must keep passing without `textual`.
