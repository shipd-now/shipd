# board-portfolio-tui
Status: verified
Theme: developer-experience

## Idea

Replace the flat, monochrome delivery `tui` with an interactive, colour-coded
portfolio board: a collapsible initiative → epic → change hierarchy panel beside
a lifecycle kanban, navigable by keyboard and mouse, that also launches plan,
run, and open actions per card.

### Motivation

The `tui` verb today (`dashboard.py:462`) just dumps a flat, colourless text
list of epics with no grouping and no interaction beyond `q` — you cannot see
the initiative→epic→change hierarchy at a glance or act on what you see. Runs
are only observable indirectly (headless `claude -p` sessions), so the user
asked for one board that shows the whole tree in colour and lets them start and
enter sessions from it.

### Details

- Reshape `build_board` to group epics under their initiative (a workspace-wide
  bucket for epics with none), keep `Theme:` as a per-epic label, and annotate
  each member with its eligible actions and resumable session id.
- Rewrite the `tui` verb as an interactive `curses` board: a collapsible left
  hierarchy panel (`[<]`/`[>]` toggle) and a right kanban with colour-coded,
  risk-chipped cards across lifecycle columns; full keyboard nav plus mouse,
  degrading to keyboard-only when the terminal reports no mouse.
- Add per-card actions: `[PLAN]` (interactive `/s:plan` on an unplanned
  member), `[RUN]` (detached driver — single member entering at its current
  stage, or the whole epic), `[OPEN]` (resume a parked/shipped session).
- Record each member's `session_id` in the heartbeat as soon as it is first
  captured (turn 1), not only at a terminal outcome, so `[OPEN]` always has a
  correct resume handle.
- Add a targeted single-member drive to the autopilot so `[RUN]` on a `ready`
  card enters the pipeline at `build`.

Affected capabilities: `delivery-dashboard` (modified `board-tui`,
`board-aggregation`, `autopilot-heartbeat`; added `board-actions`),
`epic-autopilot` (added `targeted-member-drive`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`, `autopilot.py`,
`session_driver.py`; tests under `plugins/s/skills/build/tests/`; plugin
version bump. Stdlib-only (`curses`), per the constitution.

### Non-goals

- No macOS/iTerm2 new-tab adapter in v1 — tmux `new-window` when `$TMUX` is set,
  else suspend-and-return. The OS-tab adapter is a follow-up.
- No live-session attach or read-only tail — `[OPEN]` stays disabled while a
  member is mid-drive (the CLI has no attach model; a second `--resume` would
  collide with the driver still writing the session).
- No new theme grouping — `Theme:` remains a label, not a hierarchy level.
- No change to the `board` text verb or the `html` verb contracts.

## Implementation

- **Files.** All board logic stays in `dashboard.py`; the drive entry point and
  the turn-1 session-id hook land in `autopilot.py` / `session_driver.py`.
- **Pure layout, thin curses shell.** A pure function computes the board layout
  as positioned lines *and* clickable regions (panel toggle, tree rows, card
  buttons); the `curses` shell only paints it, reads keys/mouse, and hit-tests
  clicks against those regions. This keeps the whole layout testable without a
  terminal, extending today's "pure renderer shared with `board`" rule. Rejected:
  interleaving hit-testing into the draw loop — untestable and the constitution
  requires tests for every engine change.
- **Colour + mouse degrade gracefully.** `curses` is still imported lazily;
  mouse is enabled via `mousemask` and, when the terminal reports no mouse
  events, the board runs keyboard-only. Colour uses `curses` colour pairs keyed
  by lifecycle state; a terminal without colour falls back to plain attributes.
- **Action launchers are pure argv builders.** Each of PLAN/RUN/OPEN is built by
  a pure function returning the argv (and tmux-vs-suspend choice) it will spawn,
  so launching is unit-testable without spawning. `$TMUX` present →
  `tmux new-window -c <worktree>`; absent → suspend curses (`endwin`), run,
  restore. RUN spawns the driver **detached** (`Popen`) so it writes the same
  heartbeat the board tails — the board stays a viewer of run state; it does not
  block on a run. This makes the board an action surface (a change from today's
  strictly read-only board — a deliberate posture shift recorded here).
- **session_id on turn 1.** `session_driver.drive` gains an on-session callback
  fired the first time a turn yields an id; `autopilot` threads it into the
  heartbeat roster so a parked card resumes the exact conversation. Rejected:
  parsing the id only at the end — a card mid-drive would carry no handle.
- **Targeted drive reuses `drive_member`.** A single-member entry selects by slug
  and computes the pipeline entry stage from the member's current lifecycle
  (`unplanned`→plan, `ready`→build), skipping satisfied stages, then reuses the
  existing graded stage loop, worktree, and park/ship semantics. Rejected:
  overloading epic `member-selection-and-order` — that requirement governs
  risk-ordered auto-selection and must stay untouched.

Risk: mouse escape sequences vary by terminal; guarded by the keyboard path
always being sufficient and mouse being strictly additive. Risk: a detached RUN
outliving the board; guarded because the driver owns its own heartbeat/report
and the board only reads them.
