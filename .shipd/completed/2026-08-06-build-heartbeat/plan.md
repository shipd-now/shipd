# build-heartbeat
Status: verified

## Idea

Make the delivery board's activity marker and token-throughput chart reflect
every live am build — interactive `/s:build` sessions as well as autopilot
runs — and rename the `/s:deliver` skill to `/s:autopilot`.

### Motivation

The board reads only the autopilot's epic heartbeats, so hand-driven
`/s:build` sessions — currently the dominant way changes are built — render
as `○ idle` with a flat token chart even mid-build. Throughput is the user's
key signal that work is really happening, so every live build must feed it.

### Details

- Interactive build heartbeat: `heartbeat.py` gains stateless CLI verbs
  (`build-start` / `build-stage` / `build-finish`) writing
  `<content-dir>/autopilot/<slug>-build-heartbeat.json`, capturing the session
  id from `CLAUDE_CODE_SESSION_ID`; the build skill invokes them at build
  start, stage transitions, and completion (fail-soft).
- Board aggregation attaches build heartbeats to their members; the header
  indicator becomes three-state with counts (`autopilot on` / `autopilot (N)`
  over `building` / `building (N)` over `idle`), and the throughput chart also
  tails live interactive build sessions.
- Skill rename: `plugins/s/skills/deliver/` → `plugins/s/skills/autopilot/`
  (`/s:autopilot`; "deliver" kept as a trigger phrase), plus a reference
  sweep.

Affected capabilities: `delivery-dashboard` (modified), `epic-autopilot`
(modified). Impact: `plugins/s/skills/build/scripts/heartbeat.py` and
`dashboard.py`, `plugins/s/skills/build/SKILL.md`, the renamed skill
directory, tests under `plugins/s/skills/build/tests/` and `tests_textual/`,
plugin version bump.

### Non-goals

- No liveness or throughput from sessions that never write a heartbeat
  (plan/review/ad-hoc sessions) — only builds following the skill protocol.
- No statusline changes — `statusline.sh` keeps its own heartbeat reading.
- No history or persistence of build heartbeats; they stay git-ignored
  runtime state, and the autopilot's own `RunHeartbeat` semantics are
  untouched.

## Implementation

- **Heartbeat as the uniform telemetry source.** One signal path — heartbeat
  files under `<content-dir>/autopilot/` — for both engines. Rejected:
  board-side transcript inference, which cannot attribute a session to a
  change and misses builds launched from the main checkout.
- **Stateless read-modify-write CLI, not a resident writer.** An interactive
  build is an LLM session, so each verb loads the existing JSON (when
  present), applies its transition, bumps `seq`, stamps `updated_at`, and
  atomically replaces (temp file + `os.replace`, as `RunHeartbeat._write`).
  Verbs exit 0 even on write failure, warning on stderr — a heartbeat problem
  never blocks a build.
- **File name `<slug>-build-heartbeat.json`** beside the epic files — the
  distinct suffix avoids colliding with `<epic>-heartbeat.json`; the
  directory is already git-ignored.
- **Session identity from the environment.** `build-start` records
  `--session-id` (default `$CLAUDE_CODE_SESSION_ID`, exported inside Claude
  Code sessions) and `--location` (default: invoking cwd). Chart resolution
  reuses `_resolve_member_session`; `build_report.transcript_dir` already
  falls back from a worktree to the main checkout's transcript dir, so
  builds launched from the main checkout still resolve. Rejected: hook-based
  id export files — more moving parts for the same datum.
- **Liveness = freshest of heartbeat and transcript, 600-second window.**
  Aggregation stamps each attached build heartbeat with its resolved
  transcript's mtime; a build is live while `state == "running"` and the
  newer of `updated_at` / transcript-mtime is under 600s old. Transcript
  mtime self-heals sparse writes during long tasks; the short window ages out
  heartbeats orphaned by killed sessions (the autopilot's 3600s window is
  unchanged). The indicator predicates stay pure over the aggregated board —
  aggregation does the `stat`, the predicates do no I/O.
- **Indicator precedence: autopilot > building > idle**, with `(N)` appended
  only when N > 1. `building` renders in the building lane's theme colour so
  engine runs (green) and hand-driven builds read differently at a glance.
- **Rename keeps the requirement id.** The epic-autopilot spec's
  `deliver-skill` requirement is MODIFIED (retitled) rather than RENAMED, so
  the merge stays a plain in-place replace; "deliver" remains a trigger
  phrase so the old vocabulary still resolves.

Risks: a session that never writes `build-finish` leaves a `running` file —
bounded by the 600s window (the marker self-clears; the chart drops to zero
once the transcript goes quiet). Skill non-compliance degrades silently to
today's behavior. A missing `CLAUDE_CODE_SESSION_ID` still writes a heartbeat
without a session id; resolution falls back to the newest transcript for the
location.
