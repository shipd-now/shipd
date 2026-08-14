# epic-detail-dialog
Status: verified

## Idea

Add an **open control** to every epic group header on the board and an
**epic-detail modal** it opens — the epic counterpart to the change spec-detail
dialog. Clicking the open control shows the epic's status/theme/initiative, a list
of its member specs (each with board state and risk), and the epic's own
`epic.md` rendered as Markdown.

### Motivation

The board shows an epic's member changes as cards, and clicking a card opens that
change's spec-detail dialog — but there is no way to open the **epic** itself. The
`spec-detail-dialog` change deliberately scoped epic detail out as a follow-up;
this is that follow-up. A user looking at an epic group wants to read the epic
(its introduction, decisions, design) and see its specs at a glance without
leaving the board.

### Details

- **Open control on every epic header.** Alongside the (runnable-gated) ▶ run
  control, every epic group header gets an unconditional open control (e.g. `☰`) —
  a sibling `Button`, distinct from the run control and the collapse toggle.
- **Epic-detail modal.** Clicking it opens a large modal (≈80%×80%, like the
  change spec-detail modal) with a ✕ close control (Escape also dismisses),
  showing: the epic slug + status, its theme and initiative when set, a **list of
  member specs** (each `<slug>  [<risk>]  <state>`, live from the board), and the
  epic's overview rendered as Markdown from `epics/<slug>/epic.md`.
- **Dependency-free artifact read.** A stdlib helper reads the epic.md text, so
  the file logic is testable without `textual` (mirrors `change_artifacts`).

Affected capability: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py` (a stdlib `epic_markdown`
helper; the open button in `_mount_epic_groups`; button routing in
`BoardApp.on_button_pressed`; a new `EpicDetailScreen`), a **stdlib** test for the
helper in `tests/`, **textual** tests in `tests_textual/`; plugin version bump.

### Non-goals

- No change to the run control, the confirmation modal, grouping visuals, the
  toggle, the collapse behavior, the lanes, or the card spec-detail modal.
- The member-spec list in the modal is a **display** list — clicking a listed
  member does not (in this change) drill into that member's own spec-detail modal.
  (A possible follow-up.)
- No epic editing from the dialog — it is read-only.
- No change to the board's data layer or the epic-run launch builder.

## Implementation

- **Stdlib artifact helper.** Add `epic_markdown(root, slug)` — a pure,
  stdlib-only module-level helper (place before the module's `textual` import, as
  `change_artifacts`/`epic_is_runnable` are) that returns the text of
  `<contentdir>/epics/<slug>/epic.md` (via `sc.specs_dir(root)` — do not hardcode
  `.am`) or `None` when it does not exist. No `textual`; unit-tested in `tests/`.
- **Open control in `_mount_epic_groups`.** In `_flush`, after the conditional run
  button, always append an open `Button("☰", id="open-epic-<lane>-<slug>",
  classes="epic-open-button")` to `row_children`, carrying a distinct marker
  attribute — set `open_button.epic_open_slug = group_slug` (NOT `epic_slug`, which
  the run button uses). It is a sibling of the `Collapsible` (like the run button)
  so a click never reaches the collapse toggle.
- **Route the open button.** In `BoardApp.on_button_pressed`, branch on the marker
  attributes: a button carrying `epic_open_slug` → `self.push_screen(
  EpicDetailScreen(slug))`; a button carrying `epic_slug` → the existing
  `EpicRunConfirmScreen(slug)` path. Check `epic_open_slug` first; keep the run
  path unchanged. (The confirm/detail modals handle their own buttons because they
  sit on top of the screen stack.)
- **`EpicDetailScreen(ModalScreen)`.** Constructed with the epic slug. `compose`:
  read the live epic dict via `_find_epic(self.app.board, self.epic_slug)` for
  status/theme/initiative/members, and `epic_markdown(self.app.root,
  self.epic_slug)` for the overview. Render inside a `Container` (CSS `width:80%;
  height:80%`, `align: center middle`, mirroring `MemberDetailScreen`):
  - a header row with `Static("<slug> [<status>]" + theme/initiative)` and a
    top-right `Button("✕", id="epic-detail-close")` (matching `MemberDetailScreen`'s
    close pattern);
  - a `Rule`;
  - a **specs list**: for each member in the epic dict, a line
    `<slug>  [<risk>]  <state>` (a `Static`, or one line per member); when the epic
    has no members, a short "no specs" note;
  - a `Rule`;
  - the overview: `Markdown(text)` inside a `VerticalScroll` when `epic_markdown`
    returned text, else a `Static("epic file not found")` notice.
  - `BINDINGS = [Binding("escape", "dismiss_detail", ...)]`; `on_button_pressed`
    dismisses on `epic-detail-close`.
  - Import any not-yet-imported widget names in the guarded `textual` block
    (`Button`, `Static`, `Container`, `VerticalScroll`, `Markdown`, `Rule`,
    `ModalScreen`, `Binding` are already imported — no new import expected).

### Test seams

- **Stdlib (`tests/`).** `epic_markdown` returns the file text for an existing
  `epics/<slug>/epic.md` and `None` for an unknown slug — under system `python3`
  with `textual` absent (same exec-and-swallow-ImportError load as
  `tests/test_change_artifacts.py`).
- **Textual (`tests_textual/`).** With grouping on: every epic header (runnable
  and non-runnable) has an `.epic-open-button`. Clicking it pushes
  `EpicDetailScreen` and leaves the group's `collapsed` unchanged; the modal's
  text names the epic slug/status and lists its members with state+risk; a
  `Markdown` widget is present when the epic.md exists; clicking ✕ (and pressing
  Escape) dismisses back to the board. Point `root`/`board_fn` at a fixture whose
  epic has an on-disk `epics/<slug>/epic.md` (or write one into a temp content
  dir) so the overview renders.

Risk: low-to-moderate — additive open button + one new modal + a stdlib helper +
a routing branch; the run control, confirmation modal, grouping, and data layer
are untouched, and it closely mirrors the existing `spec-detail-dialog` and
`epic-run-confirm` patterns already in the file.
