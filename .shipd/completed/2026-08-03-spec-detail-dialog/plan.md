# spec-detail-dialog
Status: verified

## Idea

Turn the board's sparse member popup into a real **spec-detail dialog**: a large,
click-to-close modal that references the change's epic at the top, a horizontal
rule, and — below it — the change's actual spec files (`plan.md`, the
`specs/<capability>/spec.md` deltas, and `tasks.md`) in a **tabset** the user can
switch between, each rendered as Markdown.

### Motivation

Today `MemberDetailScreen` is a small fixed 60-wide box showing only slug, epic,
state, stage, session, and actions — no plan, no tasks, no way to read the spec
the change is about, and only `Escape` closes it. A user clicking a change wants
to *read the change*: its plan and its task list. The artifacts already exist on
disk (`.shipd/planned/<slug>/` while in-flight, `.shipd/completed/<date>-<slug>/` once
archived); the dialog just never surfaced them.

### Details

- **Bigger modal.** The screen occupies most of the viewport (≈80% width/height)
  instead of the fixed 60-column box.
- **Clickable close control.** A `✕` button in the modal dismisses it; `Escape`
  still works too.
- **Epic reference header.** Above a horizontal `Rule`, show the change's slug
  with its risk and board state, and `epic: <slug> [<status>]`. This needs the
  epic's *status* threaded to the card (the card only carries the epic slug
  today).
- **Tabset of spec files.** Below the rule, a `TabbedContent` with one `TabPane`
  per file discovered for the change — Plan (`plan.md`), a Spec tab per
  `specs/<cap>/spec.md`, and Tasks (`tasks.md`) — each rendering the file text via
  the `Markdown` widget inside a scroll container.
- **Unplanned changes.** A change with no artifact directory shows a short
  "not yet planned — no spec files" notice instead of the tabset.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact:
`plugins/s/skills/build/scripts/dashboard.py` (a new stdlib artifact-locator
helper; `MemberDetailScreen`; `TaskCard` gains `epic_status`; the two lane
builders pass it through), a new **stdlib** test in
`plugins/s/skills/build/tests/` for the locator, and **textual** tests in
`plugins/s/skills/build/tests_textual/`; plugin version bump.

### Non-goals

- **No epic-detail dialog.** Epic nodes in the tree and shipped-lane group
  headers stay non-clickable; the header's epic reference is a label, not a
  navigable link. (A separate follow-up may add epic detail.)
- No change to the lanes, the hierarchy tree, focus movement, the `r`/`l`/`o`
  action keys, or the `Enter`/click open paths (they keep opening the modal — now
  the richer one).
- No editing of spec files from the dialog — it is read-only.
- No syntax highlighting beyond what the `Markdown` widget provides.

## Implementation

- **Split the file logic (stdlib) from the rendering (textual).** Add a
  dependency-free module-level helper — e.g. `change_artifacts(root, slug)` — that
  resolves the change's directory and returns an **ordered list** of
  `{"label", "path", "text"}` dicts in tab order (Plan, then each Spec by
  capability name, then Tasks), or an **empty list** when no directory exists. It
  uses only `os`/`glob`/file reads (no `textual`), so it lives with the other
  stdlib helpers near the top of `dashboard.py` and is unit-tested in
  `tests/` without `textual`. Resolution order: `<contentdir>/planned/<slug>/`
  first (in-flight), else the newest matching `<contentdir>/completed/*-<slug>/`
  (archived). Use `sc.specs_dir(root)` / the existing content-dir resolution
  already imported as `sc` — do not hardcode `.am`. Tab order within a dir: `plan.md`,
  then `sorted(specs/*/spec.md)` labelled `Spec: <cap>` (or just `Spec` when
  there is one), then `tasks.md`; include only files that exist.
- **Thread the epic status to the card.** `_lane_contents` already yields
  `(epic_slug, epic_status, member, entry)` per card but the status is dropped at
  construction. Add an `epic_status` parameter to `TaskCard.__init__` and pass it
  at both construction sites (`_render_lanes` non-shipped branch and
  `_mount_shipped_group`, which already unpacks `status`). Carry it onto the card
  (`self.epic_status`) and into the modal.
- **`MemberDetailScreen` becomes the spec-detail screen.** Keep the class name
  (its `Enter`/click callers and tests reference it) but rebuild `compose`:
  - CSS: the container is `width: 80%; height: 80%` (was `width: 60; height:
    auto`), still `align: center middle`.
  - Header region: a `Static` (or `Label`) line with `slug [risk · state]` and a
    second line `epic: <epic_slug> [<epic_status>]`. The screen already receives
    `epic_slug`, `member`, `entry`; also pass `epic_status` in (default `None` →
    render `?`). Read `self.app.root` for the artifact lookup — `BoardApp` stores
    `self.root`.
  - A **close control**: a `Button("✕", id="close-detail")` (or a small clickable
    `Static`) positioned top-right; handle it (`on_button_pressed` →
    `self.dismiss()`, matching `action_dismiss_detail`). Keep the `Escape`
    binding.
  - A horizontal `Rule` between the header and the body.
  - Body: call `change_artifacts(self.app.root, member["slug"])`. If non-empty,
    build a `TabbedContent` with a `TabPane(label, VerticalScroll(Markdown(text)))`
    per artifact; if empty, a single `Static` with the not-yet-planned notice.
  - Import the new widgets (`TabbedContent`, `TabPane`, `Markdown`, `Rule`,
    `Button`) alongside the other guarded `textual` imports so the module still
    imports without `textual` (verified present in the pinned `textual` 8.2.8).
- **Keep the open paths intact.** `TaskCard.action_select` still pushes
  `MemberDetailScreen(...)` — just extend its argument list with `epic_status`.
  `on_click` (click-to-open) and the `Enter` binding are unchanged.

### Test seams

- **Stdlib (`tests/`).** Build a temp content dir with a `planned/<slug>/` (and a
  separate `completed/<date>-<slug>/`) holding `plan.md`, `specs/<cap>/spec.md`,
  `tasks.md`; assert `change_artifacts` returns the right ordered labels/paths/
  text, prefers `planned` over `completed`, and returns `[]` for an unknown slug —
  all without importing `textual`.
- **Textual (`tests_textual/`).** Mount the app, open a card's modal (via
  `action_select`/click), and assert: the container is larger than the old fixed
  size, the header names the epic and its status, a `TabbedContent` exists with
  the expected tab labels for a change whose fixture has artifacts, clicking the
  `✕` control dismisses the screen, and an unplanned change shows the notice (no
  `TabbedContent`). The board fixture may need a member slug that maps to a real
  on-disk change dir, or the test can point `root` at a temp content dir it
  populates.

Risk: moderate — this reshapes one screen and adds a stdlib helper, but the data
layer, lanes, tree, and open paths are untouched; the helper is pure stdlib and
independently tested, and the widgets used are all in the pinned `textual`.
