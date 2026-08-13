# run-heartbeat-liveness
Status: verified

## Idea

Make the autopilot run heartbeat tell the truth when a run dies: record the
writer's identity so a reader can detect a vanished writer, write a terminal
state on catchable exits, and stop the board from rendering a dead run as a
live `driving`/BUILDING card.

### Motivation

A run killed by OOM/SIGKILL or reaped by an external signal never reaches
`run_finished`, so its heartbeat freezes at `state:"running"` with a `driving`
roster entry and the board shows the dead run as an actively BUILDING card
indefinitely — the board lies about liveness.

### Details

- **Writer** (`heartbeat.py` + `autopilot.py`): record the writer's `pid` and
  `host` in the run heartbeat at run start; on a catchable abnormal exit (a
  raised `AutopilotError`, or a received `SIGTERM`/`SIGINT`) write a terminal
  `aborted` run state through a `try/finally` plus signal handlers, never
  overwriting a clean `finished`.
- **Reader** (`dashboard.py`): make lane placement staleness-aware via a
  dependency-free liveness probe — a `driving` roster entry whose heartbeat is
  dead (writer `pid` not alive on the reader's `host`, or, cross-host,
  `updated_at` older than the existing 3600s window) renders in the `building`
  lane as a **stale** card carrying its death age, not as active driving.

Affected capability: `delivery-dashboard` (modified). Impact: `heartbeat.py`,
`autopilot.py`, `dashboard.py`; tests under `plugins/s/skills/build/tests/`;
`plugins/s/.claude-plugin/plugin.json` version bump. No new dependencies —
`os.getpid`/`os.kill`/`socket.gethostname`/`signal` are all stdlib.

### Non-goals

- **Not** fixing the OOM root cause (the autopilot's per-member memory
  footprint / concurrent-child capping) — a separate resource-management change.
- **No** watchdog thread re-stamping `updated_at` during long stages — pid
  liveness makes it unnecessary and avoids adding a thread to the sequential
  delivery engine.
- **No** change to the interactive build heartbeat (it already ages out on its
  own 600s window).
- **No** cross-host pid probing — a run observed from a different host falls
  back to the time-window rather than probing a foreign pid.

## Implementation

**Files/components.** `heartbeat.py` (`RunHeartbeat` state dict + a terminal
`aborted` writer), `autopilot.py` (`main`/`run`/`run_member` exit path and
signal handlers), `dashboard.py` (a pure liveness predicate feeding
`_member_column`/`_lane_contents`).

**Data shape.** The run heartbeat JSON gains two top-level fields recorded once
at run start: `pid` (int, `os.getpid()`) and `host` (str, `socket.gethostname()`).
The run-state vocabulary extends `running`/`finished` with `aborted`.

**Decision — liveness signal: pid-probe primary, time-window fallback.** The
reader judges a heartbeat live as: while its `host` matches the reader's host
and it carries a `pid`, alive iff `os.kill(pid, 0)` does not raise
`ProcessLookupError` (a `PermissionError` means the pid exists → alive);
otherwise alive iff `updated_at` is within `AUTOPILOT_FRESH_SECONDS` (3600) of
now. Rejected: time-window only (a killed run reads live for up to ~1h);
pid-only (no cross-host/observer safety).

**Decision — terminal write on catchable exit.** `run`/`run_member` wrap their
drive in `try/finally`, placed **past** the `--dry-run` early return so it is
reached only once the live heartbeat exists (dry runs still write nothing). The
finally writes `state:"aborted"` only when the clean `run_finished` was not
reached (a tracked flag guards against overwriting `finished`). A caught
`AutopilotError` and a `KeyboardInterrupt` (the Python form of `SIGINT`) both ride
this finally; `SIGTERM` has no default exception, so `run`/`run_member` also
install a `SIGTERM` handler (closure over the heartbeat) that routes into the
same abort write and restores the prior handler on exit. SIGKILL/OOM cannot be
caught — pid liveness is the only backstop for it, which is why both halves
exist. Rejected: `atexit` alone (does not fire on a default-disposition signal);
a guard in `main` (the heartbeat is out of scope there and a dry run would
falsely record an abort).

**Decision — dead-card render.** A dead `driving` entry stays in the `building`
lane but its active stage label is replaced by a `stale` marker with the death
age (reuse `_age`), so a human still sees a member needing attention rather than
it vanishing. `_member_column`/`_lane_contents` take the heartbeat (or a
precomputed liveness bool) as input.

**Risk — pid reuse:** a recycled pid could read live; mitigated because the
3600s window still ages the run out — pid-probe only *shortens* detection, never
extends a false-live past the window — and the host-match guards cross-machine
pid collisions. **Risk — signal-handler safety:** the handler does one
already-fail-soft guarded heartbeat write, then re-raises the default
disposition, so it neither loops nor blocks teardown.
