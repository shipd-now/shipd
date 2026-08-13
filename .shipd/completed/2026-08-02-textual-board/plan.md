# textual-board
Status: verified
Theme: developer-experience

## Idea

Rewrite the board `tui` from stdlib `curses` into a polished `textual`
application — a left collapsible hierarchy tree beside five bordered kanban lanes
of focusable task cards, with a modal detail view — keeping full feature parity
(live refresh, collapse, RUN/PLAN/OPEN actions) and adding `textual` as the
plugin's first, explicitly-carved-out third-party dependency.

### Motivation

The curses board is functional but visually flat — no real boxing, spacing, or
card affordances — and every refinement fights curses' primitives; the user wants
a modern, structured Kanban UI, which `textual` provides natively. That requires
lifting the stdlib-only constraint for the dashboard's rendering, so this change
also amends the constitution and adds a managed dependency.

### Details

- **Amend the constitution** to permit `textual` for `dashboard.py`'s `tui`
  rendering only; every other engine script stays stdlib-only, import-safe
  without any third-party package.
- **Add `requirements.txt`** pinning a compatible `textual` version, and a CI
  step that installs it before a `textual`-only test suite; the stdlib suites
  keep running dependency-free.
- **Keep the delivery engine textual-free.** Move `RunHeartbeat` + `heartbeat_path`
  from `dashboard.py` into a new stdlib `heartbeat.py`; `autopilot.py` imports
  that, so importing the autopilot never pulls `textual`.
- **Rewrite `tui` as a `textual` App** in `dashboard.py`: `Header`/`Footer`, a
  left collapsible hierarchy `Tree` (initiative → epic → change, per-node
  collapse), a horizontal board of five bordered `Lane` (VerticalScroll) columns
  (`unplanned`…`shipped`) holding focusable `TaskCard` widgets (risk accent bar,
  focus highlight), collapsible per-epic groups in the `shipped` lane, arrow-key
  spatial focus, `Enter` → a `ModalScreen` detail view, live auto-refresh on the
  `--interval`, and the RUN/PLAN/OPEN actions (reusing the existing pure launch
  builders). **Delete the curses board** (`layout_board`, `_place_card`,
  `region_at`, the `_tui_*` helpers) and its tests.

Affected capability: `delivery-dashboard` (modified `board-tui`, `board-actions`).
Impact: `plugins/s/skills/build/scripts/dashboard.py` (rewrite), new
`heartbeat.py`, `autopilot.py` (import move), `.github/workflows/ci.yml`, new
`requirements.txt`, `.shipd/constitution.md`, `AGENTS.md`; tests move to a new
`tests_textual/` suite; plugin version bump.

### Non-goals

- No change to the board's **data** layer semantics — `build_board`,
  `member_actions`, aggregation, and the launch-argv builders keep their
  contracts; only their rendering and home (heartbeat) change.
- No auto-install of `textual` at runtime — it is a documented prerequisite
  (`pip install -r requirements.txt`); the `tui` verb prints a clear install hint
  when it is missing.
- No change to `am:deliver`/autopilot behavior, the `board`/`html` verbs, or the
  heartbeat JSON format.
- This is a full-parity single change (not phased); no feature is dropped.

## Implementation

- **Module topology (honoring fold-in + a textual-free engine).** `dashboard.py`
  top-imports `textual` and defines the App and its `Lane`/`TaskCard`/modal
  widget classes at module scope (so the textual test suite can import and drive
  them with `App.run_test`/`Pilot`). Because that makes `import dashboard`
  require `textual`, `RunHeartbeat`/`heartbeat_path` move to a new stdlib
  `heartbeat.py` that `autopilot.py` imports instead — keeping the delivery engine
  and its suites dependency-free. Rejected: lazily defining the App inside the
  `tui` verb — it would leave the App un-importable and thus un-testable by
  Pilot.
- **Constitution carve-out is tight.** The amended rule names exactly
  `dashboard.py`'s `tui` rendering as the sole third-party exception; the
  `heartbeat.py` split is what lets the amendment keep "every other engine script
  stdlib-only" literally true.
- **Test split mirrors the dependency boundary.** Suites that import `dashboard`
  (the moved data-layer tests plus new `Pilot` App tests) live in a new
  `plugins/s/skills/build/tests_textual/`; CI runs `tests/` dependency-free,
  then `pip install -r requirements.txt`, then `tests_textual/`. `test_autopilot`
  updates its `RunHeartbeat` import to `heartbeat`.
- **Actions reuse the pure builders.** `TaskCard` actions call the unchanged
  `member_actions`/`resolve_action_launch`/`build_*_launch`; a detached `run`
  spawns via `Popen`, and interactive `plan`/`open` use `tmux new-window` when
  `$TMUX` is set, else `App.suspend()` (textual's context manager) in place of
  the old curses `endwin()` dance.
- **Version pin.** `textual` is pinned to the latest stable release available at
  build time (the builder resolves the exact version via `pip`), as a range, in
  `requirements.txt`.

Risk: `textual`'s API evolves across releases; the pinned range plus a CI suite
that mounts the App guard against silent breakage. Risk: this change supersedes
the pending curses-only `shipped-column-polish` change — that one should be
abandoned rather than built, since its target code is deleted here.
