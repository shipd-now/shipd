# tree-chrome
Status: verified

## Idea

Declutter the hierarchy panel: hide the `textual` tree's synthetic "hierarchy"
root node and tighten the per-level indent, so the initiative groups sit at the
top level with a single-character indent per nesting level.

### Motivation

The hierarchy `Tree` is built as `HierarchyTree("hierarchy", …)`, so its root
renders as a redundant "hierarchy" header line and pushes everything one level
deeper; combined with `Tree`'s default `guide_depth` of 4, each level indents by
two characters, wasting the narrow panel's width.

### Details

- Set `show_root = False` on `HierarchyTree` so the root "hierarchy" line is
  hidden and the initiative groups (`workspace-wide` / `initiative …`) become the
  top visible level (also removing the indent level the root added).
- Set `guide_depth` on `HierarchyTree` to the minimal value `textual` allows so
  each nesting level indents by a single guide character.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact:
`plugins/s/skills/build/scripts/dashboard.py` (the `HierarchyTree` class), a test
in `plugins/s/skills/build/tests_textual/`; plugin version bump.

### Non-goals

- No change to node contents, per-node collapse/expand, the `r` epic-run binding,
  the panel-toggle, or the lanes.
- No custom guide glyphs or `show_guides` change beyond the `guide_depth`
  reduction.

## Implementation

- **Both settings live on `HierarchyTree`.** `show_root` and `guide_depth` are
  `Tree` reactives; set them on the instance (in an `on_mount`, or `__init__`
  after `super().__init__`) — `self.show_root = False` and `self.guide_depth =
  <min>`. Use the smallest `guide_depth` `textual` accepts (it clamps very small
  values; 2 yields one guide char + space per level). The `"hierarchy"` label
  passed at construction is harmless once `show_root` is False, but may also be
  dropped. Rejected: rebuilding the tree without a root node — `Tree` always has a
  root; `show_root=False` is the supported way to hide it.
- **`_render_tree` is unchanged.** It still adds initiative → epic → member under
  `tree.root`; with the root hidden, those initiative nodes simply render at the
  top. The diff-aware `_tree_signature` guard is unaffected (content is
  identical).

Risk: none material — hiding the root is a display-only reactive and does not
change the node data the collapse/run bindings operate on.
