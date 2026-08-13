# delivery-dashboard
Status: verified
Epic: autonomous-delivery

## Idea

Instrument autopilot runs with a live heartbeat file and add a delivery
board — an aggregator verb, a curses TUI, and an auto-refresh HTML page —
showing runs by epic, worktree-aware member stages, and initiative/theme
context.

### Motivation

An autopilot run is observable only after it ends, and a member parked in its
worktree is invisible from the main checkout because member-state derivation
probes only the root's `planned/`/`completed/` directories. The epic decides
that runs write a live heartbeat consumed by a board (TUI and auto-refresh
HTML) so a parked member is never invisible again.

### Details

- Heartbeat: `autopilot.py` atomically rewrites
  `<content-dir>/autopilot/<epic>-heartbeat.json` on every run transition —
  run start, member start, stage attempt, member outcome, run end
  (delivery-dashboard, added).
- Board verb: `dashboard.py board` aggregates each epic's status/theme/
  initiative context, worktree-aware member states, the live heartbeat, and
  the last run report; `--json` for machines (delivery-dashboard, added).
- Renderers: `dashboard.py tui` (curses, interval refresh) and
  `dashboard.py html` (self-refreshing static page) over the same board
  data (delivery-dashboard, added).
- `/s:deliver` preflight names the TUI as the live view for the run
  (epic-autopilot, modified).

Impact: `plugins/s/skills/build/scripts/dashboard.py` (new),
`plugins/s/skills/build/scripts/autopilot.py`,
`plugins/s/skills/build/tests/test_dashboard.py` (new),
`plugins/s/skills/build/tests/test_autopilot.py`,
`plugins/s/skills/deliver/SKILL.md`, `.gitignore`,
`plugins/s/.claude-plugin/plugin.json` (0.6.3 → 0.6.4). No new
dependencies — stdlib only, `curses` imported lazily.

### Non-goals

- No new `/s:` skill — the TUI and HTML page are human-terminal tools;
  `/s:deliver` advertises them.
- No web server or JS framework — the HTML board is a static
  meta-refreshing file.
- No workspace-wide multi-repo board — scope is the invocation root's
  epics (initiative status is read through the workspace when resolvable).
- No run control from the board (pause, resume, re-drive) — read-only
  observability.
- No statusline changes.

## Implementation

- **Standalone `dashboard.py`** beside the other engine scripts, with
  subcommands `board`, `tui`, `html`; it imports `spec_status`/`spec_common`
  for state derivation so there is one derivation path. Rejected: more verbs
  on the 1233-line `spec_status.py` — the dashboard drags in rendering that
  does not belong in the status CLI.
- **Heartbeat writer is a small class** (`RunHeartbeat(root, epic)`) in
  `dashboard.py` with transition methods `run_started(to_drive, skipped,
  provenance)`, `member_started(slug)`, `stage_started(slug, stage,
  attempt)`, `member_finished(slug, result)`, `run_finished(report_path)`.
  Each mutates one state dict and rewrites the JSON atomically (temp file in
  the same directory + `os.replace`) with a monotonic `seq` and epoch
  `updated_at`. `autopilot.run` constructs it (never on `--dry-run`) and
  threads it into `drive_member` via a `heartbeat=None` keyword seam —
  `None` means no writes, keeping existing tests and callers unchanged, and
  letting tests inject a recorder. Rejected: parsing autopilot stdout — lossy
  and couples the board to log phrasing.
- **Heartbeat failures never fail the run:** every write is wrapped; the
  first failure warns once through `out` and disables further writes
  (build-telemetry's degrade-gracefully precedent).
- **Worktree-aware member state:** `member_board_state(root, slug)` first
  uses `spec_status._member_state` on the root; when that says `unplanned`
  it probes `.worktrees/<slug>` locate-style (content dir resolved per
  candidate root) for a planned change or a `completed/*-<slug>` archive,
  returning `(state, location)` where location is `root` or the worktree.
  Rejected: fixing `_member_state` itself — epic status derivation must keep
  ignoring unmerged worktree state.
- **Board data shape:** `build_board(root, epic=None)` returns
  `{"root", "generated_at", "epics": [{"slug", "status", "theme",
  "initiative": {"slug", "status"}|None, "members": [{"slug",
  "description", "risk", "state", "location"}], "heartbeat": <dict|None>,
  "report": <dict|None>}]}`. Initiative status resolves through the
  workspace brief when `find_workspace_root` succeeds; otherwise the slug is
  shown with status `None` — a missing workspace never errors.
- **Pure renderers, thin shells:** `render_board_lines(board)` (shared by
  `board` text mode and the TUI) and `render_board_html(board, interval)`
  are pure functions unit-tested without a terminal or browser. The TUI
  loop lazy-imports `curses` inside the subcommand (module import stays
  terminal-free), redraws every `--interval` seconds (default 2) using
  `getch` with a timeout, and quits on `q`. The HTML subcommand writes the
  page atomically; default mode rewrites every interval until interrupted,
  `--once` writes a single snapshot. All dynamic HTML content passes
  through `html.escape`; the page carries
  `<meta http-equiv="refresh" content="<interval>">` and inline CSS only.
- **`.gitignore` gains `.shipd/autopilot/`:** heartbeats and run reports are
  runtime state like `.shipd/state.json`; a run must not dirty worktrees or
  ride PRs. Rejected: committing reports — per-run churn with no reader.
- Risks: a crashed run leaves a `running` heartbeat — the board renders
  `updated_at` age ("updated 43s ago") instead of asserting liveness, so
  staleness is visible without a false verdict. Torn reads are prevented by
  `os.replace` atomicity.
