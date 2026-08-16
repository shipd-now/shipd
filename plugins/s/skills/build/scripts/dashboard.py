#!/usr/bin/env python3
"""dashboard.py — the delivery board: aggregation, rendering, and the `tui`.

``build_board`` aggregates each epic's status, theme, initiative context,
worktree-aware member states, live heartbeat, and last run report;
``render_board_lines`` is a pure renderer; the ``board`` verb is a thin shell
over it. The ``tui`` verb renders the board full-screen as a ``textual``
application (:class:`BoardApp`) — the one third-party dependency the spec
engine carves out for this module (see ``.shipd/constitution.md``); every
other engine script, including the delivery engine ``autopilot.py``, stays
stdlib-only.

This module top-imports ``textual`` and defines the App and its widget
classes at module scope so the ``tests_textual`` suite can import and drive
them headless with ``App.run_test``/``Pilot``. That makes ``import dashboard``
itself require ``textual`` — the run-heartbeat writer (:class:`heartbeat.
RunHeartbeat`) and its path helper live in the separate stdlib-only
``heartbeat`` module precisely so importing the delivery engine
(``autopilot``) never requires a third-party package.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
import shlex
import socket
import subprocess
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402
import spec_status as ss  # noqa: E402
import build_report as br  # noqa: E402
import metrics as mtr  # noqa: E402
from heartbeat import heartbeat_path, build_heartbeat_path  # noqa: E402
import tui_bootstrap  # noqa: E402


def change_artifacts(root, slug):
    """Resolve ``slug``'s on-disk spec artifacts for the spec-detail modal:
    an ordered list of ``{"label", "path", "text"}`` dicts in tab order —
    Plan (``plan.md``), one Spec tab per ``specs/<capability>/spec.md``
    (sorted by capability, labelled ``Spec: <capability>``, or just ``Spec``
    when there is exactly one), then Tasks (``tasks.md``) — including only
    the files that exist. Prefers the in-flight ``<contentdir>/planned/
    <slug>/`` directory, falling back to the newest matching
    ``<contentdir>/completed/<date>-<slug>/`` archive; ``[]`` when neither
    exists. Deliberately placed here, ahead of this module's own
    module-scope ``textual`` import below, and kept stdlib-only (``os``/
    ``glob``/file reads, no ``textual``) so it stays usable — and
    unit-tested in ``tests/`` — without the TUI dependency (delivery-
    dashboard board-tui spec: "Locating a change's artifacts is
    dependency-free")."""
    content_dir = sc.specs_dir(root)
    change_dir = os.path.join(content_dir, "planned", slug)
    if not os.path.isdir(change_dir):
        candidates = sorted(
            glob.glob(os.path.join(content_dir, "completed", "*-" + slug)))
        change_dir = candidates[-1] if candidates else None
    if not change_dir or not os.path.isdir(change_dir):
        return []

    def _read(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    artifacts = []
    plan_path = os.path.join(change_dir, "plan.md")
    if os.path.isfile(plan_path):
        artifacts.append(
            {"label": "Plan", "path": plan_path, "text": _read(plan_path)})

    spec_paths = sorted(
        glob.glob(os.path.join(change_dir, "specs", "*", "spec.md")))
    for spec_path in spec_paths:
        cap = os.path.basename(os.path.dirname(spec_path))
        label = "Spec" if len(spec_paths) == 1 else "Spec: %s" % cap
        artifacts.append(
            {"label": label, "path": spec_path, "text": _read(spec_path)})

    tasks_path = os.path.join(change_dir, "tasks.md")
    if os.path.isfile(tasks_path):
        artifacts.append(
            {"label": "Tasks", "path": tasks_path, "text": _read(tasks_path)})

    return artifacts


def artifact_notice(entry):
    """The empty-artifacts notice the spec-detail modal shows for a member
    with no resolvable spec files (delivery-dashboard modal-live-artifacts
    spec). When ``entry`` (the member's live heartbeat entry) carries a
    ``stage``, name the in-flight stage — with ``#<attempt>`` when an attempt
    is recorded, mirroring the header's ``stage#attempt`` formatting — so a
    member mid-plan reads e.g. ``plan in progress (plan#1) — spec files appear
    once emitted`` rather than the idle text. With no live stage, fall back to
    the existing idle ``not yet planned — no spec files``. Deliberately placed
    here, ahead of this module's own module-scope ``textual`` import below, and
    kept stdlib-only (pure string formatting) so it stays usable — and
    unit-tested in ``tests/`` — without the TUI dependency (mirrors
    :func:`change_artifacts` above)."""
    stage = (entry or {}).get("stage")
    if not stage:
        return "not yet planned — no spec files"
    attempt = entry.get("attempt")
    label = "%s#%s" % (stage, attempt) if attempt else stage
    return "%s in progress (%s) — spec files appear once emitted" % (
        stage, label)


def epic_is_runnable(epic):
    """Whether ``epic``'s action menu offers a Run item on the board (delivery-
    dashboard board-epic-grouping spec): its status is ``ready`` or ``active`` **and**
    at least one member is in a drivable state (``unplanned``/``ready`` —
    something for the autopilot to actually run). Mirrors what
    ``autopilot.run`` accepts (the status guard) and what it drives (the
    unplanned/ready members), so a closed epic — or a live one with nothing
    left to drive — shows no control. Deliberately placed here, ahead of
    this module's own module-scope ``textual`` import below, and kept
    stdlib-only so it stays usable — and unit-tested in ``tests/`` —
    without the TUI dependency (mirrors :func:`change_artifacts` above)."""
    if epic.get("status") not in ("ready", "active"):
        return False
    return any(m.get("state") in ("unplanned", "ready")
               for m in epic.get("members", []))


def epic_markdown(root, slug):
    """The text of ``<contentdir>/epics/<slug>/epic.md``, or ``None`` when it
    does not exist — the epic-detail modal's overview source (delivery-
    dashboard board-epic-grouping spec: "Reading that epic artifact SHALL be
    a dependency-free operation"). Deliberately placed here, ahead of this
    module's own module-scope ``textual`` import below, and kept stdlib-only
    so it stays usable — and unit-tested in ``tests/`` — without the TUI
    dependency (mirrors :func:`change_artifacts`/:func:`epic_is_runnable`
    above)."""
    epic_path = os.path.join(sc.specs_dir(root), "epics", slug, "epic.md")
    if not os.path.isfile(epic_path):
        return None
    with open(epic_path, encoding="utf-8") as fh:
        return fh.read()


def _standalone_plan_path(content_dir, slug):
    """Delegate to :func:`spec_status._standalone_plan_path` — the single
    implementation, relocated there so the status CLI's workspace report and
    the board resolve a standalone change's plan identically."""
    return ss._standalone_plan_path(content_dir, slug)


def standalone_changes(root, epic_member_slugs):
    """Discover **standalone changes** — those planned outside any epic — for
    the board (delivery-dashboard board-standalone-changes spec).

    A thin wrapper over :func:`spec_status.standalone_changes`, which holds the
    single discovery implementation (see its docstring for the contract) so the
    board's standalone group and the status CLI's workspace board report cannot
    drift. The name and signature stay here for every existing board caller.
    Deliberately placed here, ahead of this module's own module-scope
    ``textual`` import below, and kept stdlib-only so it stays usable — and
    unit-tested in ``tests/`` — without the TUI dependency (mirrors
    :func:`change_artifacts` above)."""
    return ss.standalone_changes(root, epic_member_slugs)


# ---------------------------------------------------------------------------
# Delivery-metrics view: the dependency-free data assembler and the four pure
# renderers behind the board's `m`-key metrics screen (delivery-dashboard
# board-metrics-view spec). Deliberately placed here, ahead of this module's
# own module-scope `textual` import below, and kept stdlib-only (they read a
# `metrics.derive`/`collect_ship_events` result and return plain/markup text,
# no `textual`, no I/O beyond `metrics_view_data`'s reads) so they stay
# usable — and unit-tested in `tests/test_metrics_view.py` — without the TUI
# dependency (mirrors `change_artifacts`/`epic_is_runnable` above). Durations,
# percentages, and the recent-weeks helper are reused from `metrics`, never
# re-derived; no mean appears anywhere (the epic's SPACE guardrail).
# ---------------------------------------------------------------------------

# The lane stacking order of a CFD column, bottom-up, and the fixed board
# lanes a lifecycle state maps onto (mirrors `_member_column`'s state-only
# branch: archived→shipped, ready→ready, unplanned→unplanned, else building).
_CFD_LANE_ORDER = ("shipped", "building", "ready", "unplanned")


def flow_lane(state):
    """Map a lifecycle ``state`` onto its board lane for the CFD — the
    state-only projection of :func:`_member_column` (which also folds in the
    live heartbeat): ``archived``→``shipped``, ``ready``→``ready``,
    ``unplanned``→``unplanned``, everything else (``draft``/``active``/
    ``rejected``/…)→``building``. Pure.

    Delegates to :func:`spec_status.board_lane`, the single shared projection
    the epic report also groups its members with, so the board and the report
    cannot drift."""
    return ss.board_lane(state)


def dora_tiles(metrics):
    """The DORA tile row for the metrics screen: an ordered list of
    ``(label, value)`` pairs — the deployment-frequency band with the recent
    weekly deployment-day counts, the lead-time DORA tier from
    :func:`metrics.lead_time_dora_band` over the lead-time median, the
    post-merge change-fail rate labelled post-merge beside the pre-merge
    rework proxy, and the lead- and cycle-time medians (with p85) humanized
    via ``metrics._fmt_duration``. Every absent statistic renders ``n/a``; no
    mean appears (the SPACE guardrail). Pure — no ``textual``, no I/O."""
    metrics = metrics or {}
    deployment = metrics.get("deployment_days") or {}
    dep_counts = [w.get("count", 0) for w in (deployment.get("per_week") or [])]
    band = deployment.get("dora_band") or "n/a"
    lead = metrics.get("lead_time") or {}
    cycle = metrics.get("cycle_time") or {}
    tier = mtr.lead_time_dora_band(lead.get("median")) or "n/a"
    change_failures = metrics.get("change_failures") or {}
    outcomes = metrics.get("outcomes") or {}

    def _stat(block):
        return "median %s · p85 %s" % (
            mtr._fmt_duration(block.get("median")),
            mtr._fmt_duration(block.get("p85")))

    return [
        ("deployment frequency",
         "%s · deployment-days last 4 weeks: %s"
         % (band, mtr._last_four(dep_counts))),
        ("lead-time tier", tier),
        ("change-fail rate (post-merge)",
         mtr._fmt_pct(change_failures.get("rate"))),
        ("rework rate (pre-merge proxy)",
         mtr._fmt_pct(outcomes.get("rework_rate"))),
        ("lead time", _stat(lead)),
        ("cycle time", _stat(cycle)),
    ]


def run_chart_rows(per_week, cols, rows):
    """The throughput run chart: ``(chart_rows, label)`` — the newest ``cols``
    weeks' ship counts rendered as ``rows`` eighth-block rows via
    :func:`build_report.render_chart` over bounds ``(0, max(counts) or 1)``
    (so the peak week paints a full-height column and a zero week is blank),
    plus a label carrying the overall total and the newest ISO week.
    ``build_report.scale_bounds`` is deliberately *not* used — its 500-token
    minimum ceiling flattens single-digit weekly counts to nothing. Pure — no
    ``textual``."""
    per_week = list(per_week or [])
    window = per_week[-cols:] if cols else per_week
    counts = [w.get("count", 0) for w in window]
    ceiling = (max(counts) if counts else 0) or 1
    chart_rows = br.render_chart(counts, rows, 0, ceiling)
    total = sum(w.get("count", 0) for w in per_week)
    newest_week = per_week[-1].get("week") if per_week else "n/a"
    label = "throughput: %d shipped · newest week %s" % (total, newest_week)
    return chart_rows, label


def _scatter_epoch(ts):
    """A ship timestamp as a float epoch — a ``datetime`` (``collect_ship_events``
    yields aware UTC ``datetime``s) via ``.timestamp()``, or a bare number
    coerced. Used only to place a point on the scatter's x-axis."""
    if hasattr(ts, "timestamp"):
        return ts.timestamp()
    return float(ts)


def scatter_rows(ship_events, cycle_time, cols, rows):
    """The cycle-time scatterplot (Vacanti): ``(plot_rows, label)``. Each
    shippable event plots as a ``•`` cell — x maps ``ship_ts`` linearly over
    the observed span, y maps ``seconds`` linearly from 0 to the max — with
    the ``cycle_time`` stat block's p50/p85/p95 overlaid as ``─`` lines
    labelled at the right edge with humanized durations; a point wins a
    contested cell. Events missing ``ship_ts`` or ``seconds`` are skipped; the
    label carries the plotted sample count (``n=…``, never a mean). Empty →
    blank rows and an ``n/a`` label. Pure — no ``textual``."""
    cycle_time = cycle_time or {}
    points = []
    for event in ship_events or []:
        ts = event.get("ship_ts")
        secs = event.get("seconds")
        if ts is None or secs is None:
            continue
        points.append((_scatter_epoch(ts), float(secs)))
    n = len(points)
    if not points:
        return [" " * cols for _ in range(rows)], "cycle-time scatter: n/a"

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    xspan = (xmax - xmin) or 1.0
    ymax = max(ys) or 1.0

    def _col(x):
        c = int(round((x - xmin) / xspan * (cols - 1)))
        return min(max(c, 0), cols - 1)

    def _row(y):
        # Row 0 is the top (the y-max); rows-1 is the baseline (y=0).
        r = int(round((1 - y / ymax) * (rows - 1)))
        return min(max(r, 0), rows - 1)

    grid = [[" "] * cols for _ in range(rows)]
    # Percentile overlay lines, each labelled at the right edge (a row shared
    # by two percentiles carries both labels).
    row_labels = {}
    for pname in ("p50", "p85", "p95"):
        val = cycle_time.get(pname)
        if val is None:
            continue
        r = _row(float(val))
        for c in range(cols):
            grid[r][c] = "─"
        row_labels.setdefault(r, []).append(
            "%s %s" % (pname, mtr._fmt_duration(val)))
    # Points win a contested cell (drawn after the lines).
    for x, y in points:
        grid[_row(y)][_col(x)] = "•"

    out = []
    for r in range(rows):
        line = "".join(grid[r])
        if r in row_labels:
            line += "  " + " ".join(row_labels[r])
        out.append(line)
    return out, "cycle-time scatter (n=%d)" % n


def cfd_rows(series, cols, rows):
    """The cumulative flow diagram: ``(cfd_rows, label)``. The newest ``cols``
    flow records become columns (oldest→newest); each column stacks its
    :func:`flow_lane`-mapped counts bottom-up in the order shipped, building,
    ready, unplanned as ``[$lane-<name>]█[/]`` markup cells, scaled against the
    series' peak stacked total — a nonzero lane always paints at least one
    cell, so a small band never vanishes. The label is a lane-colored legend
    line plus the record count, noting the shown window when the series
    outgrows the columns. An empty series returns blank rows and a
    no-flow-history notice. Pure — no ``textual`` (the markup is content-markup
    theme variables, resolved at render time)."""
    records = list(series or [])
    if not records:
        return ([" " * cols for _ in range(rows)],
                "no flow history recorded yet")
    window = records[-cols:] if cols else records
    columns = []
    for record in window:
        by_state = record.get("by_state") or {}
        lane_counts = {}
        for state, count in by_state.items():
            lane = flow_lane(state)
            lane_counts[lane] = lane_counts.get(lane, 0) + count
        columns.append(lane_counts)
    max_total = max((sum(c.values()) for c in columns), default=0) or 1
    ncols = len(columns)
    grid = [[" "] * ncols for _ in range(rows)]
    for ci, lane_counts in enumerate(columns):
        counts = [lane_counts.get(lane, 0) for lane in _CFD_LANE_ORDER]
        cells = [int(round(count * rows / max_total)) for count in counts]
        # A nonzero lane paints at least one cell — a sliver beats vanishing —
        # with the excess trimmed from the tallest bands so the stack never
        # outgrows its rows.
        cells = [max(1, n) if count else 0
                 for count, n in zip(counts, cells)]
        while sum(cells) > rows:
            cells[cells.index(max(cells))] -= 1
        y = rows - 1  # fill from the bottom row up
        for lane, n in zip(_CFD_LANE_ORDER, cells):
            for _ in range(n):
                grid[y][ci] = "[$lane-%s]█[/]" % lane
                y -= 1
    out = ["".join(grid[r]) for r in range(rows)]
    legend = "  ".join("[$lane-%s]█[/] %s" % (lane, lane)
                       for lane in _CFD_LANE_ORDER)
    label = "%s · %d records" % (legend, len(records))
    if len(window) < len(records):
        label += " (newest %d shown)" % len(window)
    return out, label


def metrics_view_data(root, now=None):
    """Assemble the metrics screen's data off the UI thread — the
    dependency-free callable the screen's thread worker runs (an injectable
    seam on the screen, defaulting here). Returns ``{"metrics":
    metrics.derive(root, now), "ship_events": metrics.collect_ship_events(
    root)}``: ``derive`` shells out to git per shipped change (far too slow for
    the board tick, hence the worker), and ``collect_ship_events`` yields the
    per-item scatter points. Writes nothing. No ``textual``."""
    return {
        "metrics": mtr.derive(root, now),
        "ship_events": mtr.collect_ship_events(root),
    }


def shipped_this_week(ship_events, now=None):
    """Count the ship events that landed in the current ISO week — the
    ``▲ N shipped this week`` strip stat.

    ``now`` is coerced to an aware UTC ``datetime`` (a naive value is assumed
    UTC), defaulting to the current UTC time when ``None`` — injectable for
    determinism. An event counts when its ``ship_ts`` (an aware UTC
    ``datetime``) falls on or after the Monday (UTC) of ``now``'s ISO week; a
    ``ship_ts``-less event is skipped, never fatal. Defined ahead of this
    module's ``textual`` import and kept stdlib-only (``datetime`` only) so the
    strip stat stays testable without the TUI dependency."""
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_dt.timezone.utc)
    else:
        now = now.astimezone(_dt.timezone.utc)
    monday = now.date() - _dt.timedelta(days=now.weekday())
    boundary = _dt.datetime(monday.year, monday.month, monday.day,
                            tzinfo=_dt.timezone.utc)
    return sum(1 for e in ship_events
               if e.get("ship_ts") is not None and e["ship_ts"] >= boundary)


# ---------------------------------------------------------------------------
# Live-activity aggregation and the header-bar activity predicates
#
# These are dependency-free (no ``textual``, only stdlib + the stdlib
# ``build_report``/``heartbeat`` helpers) and defined ahead of this module's
# module-scope ``textual`` import so ``tests/`` can exercise them without
# ``textual`` installed. Two signal sources feed the board: an epic's autopilot
# run heartbeat (``<epic>-heartbeat.json``, aggregated by ``_epic_board``) and a
# member's interactive build heartbeat (``<slug>-build-heartbeat.json``,
# attached here). The window predicates stay pure over the aggregated board —
# aggregation does the transcript ``stat``, the predicates do no I/O.
# ---------------------------------------------------------------------------

# The liveness window for a live autopilot run — the same 3600-second window the
# statusline uses, so a long silent stage keeps the light while a crashed run
# loses it (delivery-dashboard board-tui spec).
AUTOPILOT_FRESH_SECONDS = 3600

# The (shorter) liveness window for an interactive build heartbeat: it ages out
# a heartbeat orphaned by a killed session that never wrote `build-finish`
# (delivery-dashboard board-tui spec).
BUILD_FRESH_SECONDS = 600


def _read_json(path):
    """Parse a JSON file, returning ``None`` when it is missing or unparseable —
    a torn or absent run artifact never fails the board."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _resolve_member_transcript(location, session_id):
    """Resolve ``location`` (a member's or a build heartbeat's) to its live
    transcript as ``(tdir, session_id, path)``, or ``None`` when none resolves:
    the explicit ``session_id`` first (only when its transcript file is on
    disk), else the newest transcript for ``location``. Dependency-free — reuses
    the build-report resolvers, whose worktree→main-checkout fallback means a
    build launched from the main checkout still resolves."""
    if not location:
        return None
    try:
        tdir = br.transcript_dir(location)
        sid, path = br.find_active_session(tdir, session_id or None)
    except OSError:
        return None
    if sid and path:
        return (tdir, sid, path)
    return None


def _resolve_member_session(location, session_id):
    """The ``(tdir, session_id)`` tail key for ``location`` (or ``None``) — the
    :class:`~build_report.MultiTail` sync key, dropping the transcript path
    :func:`_resolve_member_transcript` also returns."""
    resolved = _resolve_member_transcript(location, session_id)
    if resolved is None:
        return None
    tdir, sid, _path = resolved
    return (tdir, sid)


def _all_board_members(board):
    """Every member dict on ``board`` — each epic's members followed by the
    standalone changes — so a predicate walks the whole board uniformly."""
    members = []
    for epic in board.get("epics", []):
        members.extend(epic.get("members", []))
    members.extend(board.get("standalone", []))
    return members


def _roster_by_slug(heartbeat):
    """Index a heartbeat's roster by member slug (empty when no heartbeat)."""
    if not heartbeat:
        return {}
    return {e.get("slug"): e for e in heartbeat.get("roster", [])}


def _discover_build_heartbeats(root):
    """Every interactive build heartbeat under ``root``'s
    ``autopilot/*-build-heartbeat.json`` **and** each
    ``<root>/.worktrees/<name>/`` content dir's ``autopilot/`` — a build runs in
    its change's worktree, so the heartbeat lands there while the board
    aggregates from the main checkout. Keyed by recorded change slug; a missing
    or unparseable file contributes nothing, and a slug contested between roots
    is won by the newest ``updated_at`` (an absent stamp treated as oldest).
    Each worktree's content dir is resolved the way :func:`standalone_changes`
    does (``sc.specs_dir`` of the worktree)."""
    roots = [root]
    worktrees_dir = os.path.join(root, ".worktrees")
    try:
        wt_names = sorted(os.listdir(worktrees_dir))
    except OSError:
        wt_names = []
    for name in wt_names:
        wt = os.path.join(worktrees_dir, name)
        if os.path.isdir(wt):
            roots.append(wt)

    result = {}
    for hosting_root in roots:
        try:
            autopilot_dir = os.path.join(sc.specs_dir(hosting_root), "autopilot")
        except sc.ConfigError:
            continue
        pattern = os.path.join(autopilot_dir, "*-build-heartbeat.json")
        for path in glob.glob(pattern):
            data = _read_json(path)
            if not (isinstance(data, dict) and data.get("slug")):
                continue
            slug = data["slug"]
            existing = result.get(slug)
            if existing is None or (data.get("updated_at") or 0) >= (
                    existing.get("updated_at") or 0):
                result[slug] = data
    return result


def attach_build_heartbeats(root, board):
    """Attach each discovered interactive build heartbeat to its slug-matching
    board member (epic member and standalone change alike) as
    ``member["build_heartbeat"]``, stamping the resolved transcript's mtime as
    ``transcript_mtime`` when one resolves — the newer of that stamp and the
    heartbeat's own ``updated_at`` is the liveness the count predicates read, so
    a long quiet stage that stops writing the file still reads as live while its
    transcript keeps moving. Mutates and returns ``board``. Dependency-free (the
    only I/O is the discovery glob and a transcript ``stat``)."""
    heartbeats = _discover_build_heartbeats(root)
    if not heartbeats:
        return board
    for member in _all_board_members(board):
        hb = heartbeats.get(member.get("slug"))
        if hb is None:
            continue
        stamped = dict(hb)
        resolved = _resolve_member_transcript(
            hb.get("location") or member.get("location"),
            hb.get("session_id"))
        if resolved is not None:
            try:
                stamped["transcript_mtime"] = os.path.getmtime(resolved[2])
            except OSError:
                pass
        member["build_heartbeat"] = stamped
    return board


def _build_liveness_stamp(hb):
    """The freshest liveness stamp for a build heartbeat: the newer of its
    ``updated_at`` and the aggregation-stamped ``transcript_mtime`` (either may
    be absent), or ``None`` when neither is present."""
    stamps = [s for s in (hb.get("updated_at"), hb.get("transcript_mtime"))
              if s]
    return max(stamps) if stamps else None


def _build_is_live(hb, now=None):
    """Whether a member's build heartbeat is a live interactive build: state
    ``running`` with a liveness stamp within :data:`BUILD_FRESH_SECONDS` of
    ``now``."""
    if not hb or hb.get("state") != "running":
        return False
    if now is None:
        now = time.time()
    stamp = _build_liveness_stamp(hb)
    return stamp is not None and now - stamp <= BUILD_FRESH_SECONDS


def run_is_dead(heartbeat, now=None, host=None):
    """Whether an autopilot run's writer is dead (delivery-dashboard board-
    dead-run-detection spec) — dependency-free, no ``textual``: while
    ``heartbeat``'s recorded ``host`` matches the reader's host (``host``, or
    :func:`socket.gethostname` when ``None``) and it carries a ``pid``, the
    writer is alive iff probing that pid with ``os.kill(pid, 0)`` does not
    raise ``ProcessLookupError`` (a ``PermissionError`` means the pid exists,
    so it counts as alive too); otherwise — a cross-host heartbeat, or one
    missing a ``pid`` — liveness falls back to whether ``updated_at`` is
    within :data:`AUTOPILOT_FRESH_SECONDS` of ``now``. Returns ``True`` when
    dead, ``False`` when live."""
    reader_host = host if host is not None else socket.gethostname()
    pid = heartbeat.get("pid")
    if heartbeat.get("host") == reader_host and pid:
        try:
            os.kill(pid, 0)
            return False
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
    if now is None:
        now = time.time()
    updated_at = heartbeat.get("updated_at")
    if updated_at is None:
        return True
    return now - updated_at > AUTOPILOT_FRESH_SECONDS


def activity_counts(board, now=None):
    """The board's live-activity counts as ``(live_runs, live_builds)`` (pure,
    no ``textual``, no I/O): ``live_runs`` is the number of epics whose autopilot
    heartbeat records run state ``running`` with an ``updated_at`` within
    :data:`AUTOPILOT_FRESH_SECONDS` of ``now`` (a missing ``updated_at`` is never
    live); ``live_builds`` is the number of members whose attached build
    heartbeat is live per :func:`_build_is_live`. ``now`` defaults to the current
    time."""
    if now is None:
        now = time.time()
    live_runs = 0
    for epic in board.get("epics", []):
        hb = epic.get("heartbeat")
        if not hb or hb.get("state") != "running":
            continue
        updated_at = hb.get("updated_at")
        if updated_at is None:
            continue
        if now - updated_at <= AUTOPILOT_FRESH_SECONDS:
            live_runs += 1
    live_builds = sum(
        1 for member in _all_board_members(board)
        if _build_is_live(member.get("build_heartbeat"), now))
    return (live_runs, live_builds)


def autopilot_live(board, now=None):
    """Whether some autopilot run is live — the boolean the statusline-parity
    callers want, delegating to :func:`activity_counts`'s run count (delivery-
    dashboard board-tui spec). Pure, no ``textual``."""
    return activity_counts(board, now)[0] > 0


def indicator_marker(board, now=None):
    """The header-bar activity indicator markup for ``board`` by the precedence
    autopilot > building > idle (delivery-dashboard board-tui spec): while a run
    is live a theme-success ``●`` with ``autopilot on`` (``autopilot (N)`` when
    more than one); otherwise while a build is live a ``●`` in the building
    lane's theme colour with ``building`` (``building (N)`` for more than one);
    otherwise a subtle-tier idle marker. Pure, no ``textual``."""
    live_runs, live_builds = activity_counts(board, now)
    if live_runs > 0:
        label = "autopilot on" if live_runs == 1 else "autopilot (%d)" % live_runs
        return "[$success]●[/] %s" % label
    if live_builds > 0:
        label = "building" if live_builds == 1 else "building (%d)" % live_builds
        return "[$lane-building]●[/] %s" % label
    return "[$fg-subtle]○ idle[/]"


def driving_session_keys(board):
    """The ``(tdir, session_id)`` keys the header chart's
    :class:`~build_report.MultiTail` syncs to (board-throughput-chart): every
    member whose live autopilot heartbeat state is ``driving`` plus every member
    with a live interactive build heartbeat (:func:`_build_is_live`), each
    resolved through :func:`_resolve_member_session` — the explicit session id
    first, else the newest transcript for the member's or the heartbeat's
    location — and deduplicated so a session is tailed once. Pure — no
    ``textual``."""
    keys = []
    seen = set()

    def _add(key):
        if key is not None and key not in seen:
            seen.add(key)
            keys.append(key)

    for epic in board.get("epics", []):
        roster = _roster_by_slug(epic.get("heartbeat"))
        for member in epic.get("members", []):
            entry = roster.get(member["slug"], {})
            if entry.get("state") != "driving":
                continue
            session_id = member.get("session_id") or entry.get("session_id")
            _add(_resolve_member_session(member.get("location"), session_id))
    for member in _all_board_members(board):
        hb = member.get("build_heartbeat")
        if not _build_is_live(hb):
            continue
        location = hb.get("location") or member.get("location")
        _add(_resolve_member_session(location, hb.get("session_id")))
    return keys


def _age(updated_at, verb="updated"):
    """A human age for an epoch timestamp — ``updated 5s ago`` — so a crashed
    run's staleness is visible without asserting liveness (design: risks). The
    ``verb`` prefix lets a caller reframe the same age (e.g. ``parked 5s
    ago``); it defaults to ``updated`` so every existing call site is
    unchanged."""
    if not updated_at:
        return "%s ?" % verb
    delta = max(0, int(time.time() - updated_at))
    if delta < 60:
        return "%s %ds ago" % (verb, delta)
    if delta < 3600:
        return "%s %dm ago" % (verb, delta // 60)
    return "%s %dh ago" % (verb, delta // 3600)


# ---------------------------------------------------------------------------
# Lane resolution — shared by the App's card placement. Placed here, ahead of
# this module's own module-scope `textual` import below, and kept stdlib-only
# so it stays usable — and unit-testable under the system `python3` without
# `textual` installed — for a plain `import dashboard`.
# ---------------------------------------------------------------------------

# The five lifecycle lanes, left to right.
LANES = ("unplanned", "ready", "building", "review", "shipped")

# The per-lane text shown when a lane mounts no member rows — an empty board
# region or a search that filters every member out (delivery-dashboard
# board-tui spec).
LANE_EMPTY_TEXTS = {
    "unplanned": "nothing unplanned",
    "ready": "nothing ready",
    "building": "nothing building",
    "review": "nothing in review",
    "shipped": "nothing shipped yet",
}

# The three-state lane grouping mode, cycled in this order by the "g" key and
# the header-bar segmented control (delivery-dashboard board-epic-grouping
# spec): per-epic headers, per-initiative headers, or flat lanes.
GROUP_MODES = ("epic", "initiative", "none")


def _member_column(member, entry, dead=False, now=None):
    """The lane a member's card belongs in, from its live heartbeat entry and
    worktree-aware board state. A member being driven lands in ``building``
    (or ``review`` while its review stage runs) — unless its run is ``dead``
    (delivery-dashboard board-dead-run-detection spec), in which case it
    lands in ``building`` regardless of stage; a member whose attached
    interactive build heartbeat is live per :func:`_build_is_live` (as of
    ``now``) is placed by that heartbeat's stage instead — ``review`` while
    the stage is ``review``, else ``building`` — overriding the state mapping
    below, since an interactive build archives its change before the review
    stage runs (delivery-dashboard board-live-build-lane spec); a
    shipped/archived member in ``shipped``; a parked (needs-human/rejected)
    member stays in ``building`` where it needs attention; otherwise its
    lifecycle state maps straight through. A stale (aged-out or finished)
    build heartbeat is simply ignored — no stale treatment, which stays
    autopilot-roster-only."""
    entry = entry or {}
    live = entry.get("state")
    stage = entry.get("stage")
    state = member.get("state")
    if live == "driving":
        if dead:
            return "building"
        return "review" if stage == "review" else "building"
    build_hb = member.get("build_heartbeat")
    if _build_is_live(build_hb, now):
        return "review" if build_hb.get("stage") == "review" else "building"
    if live == "shipped" or state == "archived":
        return "shipped"
    if live in ("needs-human", "rejected") or state == "rejected":
        return "building"
    if state == "ready":
        return "ready"
    if state == "unplanned":
        return "unplanned"
    return "building"


def member_signal(member, entry):
    """The parked-signal predicate (delivery-dashboard board-parked-member-
    signal spec): ``{"kind", "glyph", "label", "reason"}`` for a member the
    delivery pipeline could not carry forward, or ``None`` for one
    progressing normally. Checked in this order: a roster entry dead-run
    detection marked ``stale`` (``_lane_contents`` overwrites its ``stage``
    with the death age via :func:`_age`) yields ``†``/``stale (<stage>)``;
    otherwise the entry's live ``state`` (falling back to the member's own
    worktree-derived ``state`` when the entry carries none) of ``rejected``
    yields ``⚠``/``rejected`` and ``needs-human`` yields ``⛔``/``needs-human``.
    The entry's ``reason`` (when present) rides along unmodified. Pure and
    dependency-free — no ``textual`` — so it is unit-testable without the
    TUI (design: a single predicate feeds both the card and the modal)."""
    entry = entry or {}
    reason = entry.get("reason")
    if entry.get("stale"):
        return {"kind": "stale", "glyph": "†",
                "label": "stale (%s)" % entry.get("stage"), "reason": reason}
    state = entry.get("state") or member.get("state")
    if state == "rejected":
        return {"kind": "rejected", "glyph": "⚠", "label": "rejected",
                "reason": reason}
    if state == "needs-human":
        return {"kind": "needs-human", "glyph": "⛔", "label": "needs-human",
                "reason": reason}
    return None


def _lane_contents(board, now=None):
    """The exact per-lane data ``_render_lanes`` mounts, derived purely from
    ``board``: for every lane in :data:`LANES`, the ordered list of card
    specs ``(epic_slug, epic_status, member, entry)``. The ``shipped`` lane's
    cards stay grouped per epic implicitly — since epics are walked in board
    order, one epic's shipped members are always contiguous in its list — so
    ``_render_lanes`` can fold consecutive same-epic runs into one
    ``Collapsible`` group titled from ``epic_status``. A ``driving`` roster
    member whose epic heartbeat is judged dead by :func:`run_is_dead`
    (delivery-dashboard board-dead-run-detection spec) is placed in
    ``building`` as a stale card instead: its returned ``entry`` is a copy
    carrying ``stale: True`` and its ``stage`` overwritten with the run's
    death age (via :func:`_age`) in place of the live stage. A live run's
    ``driving`` member is unaffected. ``now`` is threaded into
    :func:`_member_column` so a member's live build heartbeat is judged
    against the same clock (delivery-dashboard board-live-build-lane
    spec)."""
    contents = {name: [] for name in LANES}
    for epic in board.get("epics", []):
        hb = epic.get("heartbeat")
        roster = _roster_by_slug(hb)
        status = epic.get("status") or "unknown"
        run_dead = bool(hb) and hb.get("state") == "running" \
            and run_is_dead(hb, now=now)
        for member in epic.get("members", []):
            entry = roster.get(member["slug"], {})
            stale = run_dead and entry.get("state") == "driving"
            lane_name = _member_column(member, entry, dead=stale, now=now)
            if stale:
                entry = dict(entry)
                entry["stale"] = True
                entry["stage"] = _age(hb.get("updated_at"), verb="died")
            contents[lane_name].append((epic["slug"], status, member, entry))
    # Standalone changes (planned outside any epic) fold in under the pseudo-
    # epic slug `standalone` (status None) with an empty heartbeat entry, so the
    # same `_member_column` state→lane mapping epic members use places them and
    # they fold into the diff-aware lane signatures exactly like member rows
    # (delivery-dashboard board-standalone-changes spec).
    for member in board.get("standalone", []):
        entry = {}
        lane_name = _member_column(member, entry, now=now)
        contents[lane_name].append(("standalone", None, member, entry))
    return contents


if __name__ == "__main__":
    # Self-provision `textual` before it is imported below: on a missing
    # `textual`, this creates/reuses the cached venv, installs the pinned
    # dependency, and re-execs into it — so every verb (`tui`/`board`)
    # just works with no manual `pip install`. A no-op when `textual` is
    # already importable. Only reached for a script invocation, not a plain
    # `import dashboard`.
    tui_bootstrap.ensure_textual(sys.argv, __file__)

try:
    from textual import on  # noqa: E402
    from textual.app import App, ComposeResult, SystemCommand  # noqa: E402
    from textual.binding import Binding  # noqa: E402
    from textual.containers import (  # noqa: E402
        Container, Horizontal, Vertical, VerticalScroll)
    from textual.events import Click  # noqa: E402
    from textual.message import Message  # noqa: E402
    from textual.screen import ModalScreen  # noqa: E402
    from textual.theme import Theme  # noqa: E402
    from textual.widgets import (  # noqa: E402
        Button, Collapsible, Footer, Input, Markdown, Rule,
        Static, TabbedContent, TabPane)
    from textual.widgets.collapsible import CollapsibleTitle  # noqa: E402
except ImportError:
    # The `__main__` bootstrap above provisions `textual` before this import
    # runs for a script invocation, so a missing `textual` here only reaches
    # a plain `import dashboard` (e.g. from a test) — a normal ImportError.
    raise


# ---------------------------------------------------------------------------
# Worktree-aware member state
# ---------------------------------------------------------------------------

def member_board_state(root, slug):
    """Return ``(state, location)`` for one epic stub member.

    Delegates to ``spec_status._member_state_with_root``, which probes the
    invocation ``root`` first, then each ``.worktrees/<name>`` directory under
    it in sorted name order, and reports both the derived state and the
    candidate root that produced it — so a member parked inside its worktree
    (a rejected plan, a completed archive) is visible, and located, from the
    main checkout. ``location`` is the absolute directory hosting the change:
    ``root`` when nothing hosts the member (state stays ``unplanned``), else
    the hosting candidate."""
    state, hosting_root = ss._member_state_with_root(root, slug)
    return state, os.path.abspath(hosting_root)


# ---------------------------------------------------------------------------
# Board aggregation
# ---------------------------------------------------------------------------

def _epic_slugs(root):
    """Every discoverable epic as ``(slug, hosting_root)`` pairs — the
    invocation root's own epics in sorted order first, then the epics hosted
    only under a ``.worktrees/<name>`` worktree in sorted order, each paired
    with the first worktree hosting it (delivery-dashboard board-aggregation).

    Delegates to ``ss.all_epic_slugs_with_roots``, the single discovery seam
    the status CLI's epic surfaces share, so the board and the CLI can never
    disagree about which epics exist or where they live."""
    return ss.all_epic_slugs_with_roots(root)


def _initiative_context(root, slug):
    """Resolve an epic's ``Initiative:`` slug to ``{"slug", "status"}``: the
    status is read through the workspace brief when a workspace is discoverable,
    otherwise ``None`` — a missing workspace degrades to slug-only, never an
    error."""
    status = None
    try:
        ws_root = sc.find_workspace_root(root)
    except sc.ConfigError:
        ws_root = None
    if ws_root is not None:
        status = ss.read_initiative_status(
            sc.initiative_brief_path(ws_root, slug))
    return {"slug": slug, "status": status}


def _member_rows(root, header, rows):
    """Build each member's board row, reading Risk from the labelled column
    (falling back to the last rating) and deriving the worktree-aware state."""
    risk_idx = None
    if header:
        for i, cell in enumerate(header):
            if cell.strip().lower() == "risk":
                # Ratings are the cells after slug + description (columns 2+).
                risk_idx = i - 2
                break
    members = []
    for slug, description, ratings in rows:
        if risk_idx is not None and 0 <= risk_idx < len(ratings):
            risk = ratings[risk_idx].strip().lower()
        elif ratings:
            risk = ratings[-1].strip().lower()
        else:
            risk = ""
        state, location = member_board_state(root, slug)
        members.append({"slug": slug, "description": description, "risk": risk,
                        "state": state, "location": location})
    return members


def member_actions(member, heartbeat_entry):
    """Return the board actions eligible for ``member`` given its live heartbeat
    roster entry: ``plan`` for an ``unplanned`` member, ``run`` for a ``ready``
    (planned, lint-clean) member, and ``open`` for a parked or shipped member
    carrying a resumable ``session_id`` — never while the member is mid-drive
    (``driving``). Pure — no I/O (design: board actions)."""
    entry = heartbeat_entry or {}
    live_state = entry.get("state")
    session_id = member.get("session_id") or entry.get("session_id")
    actions = []
    state = member.get("state")
    if state == "unplanned":
        actions.append("plan")
    elif state == "ready":
        actions.append("run")
    if session_id and live_state != "driving":
        actions.append("open")
    return actions


def _report_session_ids(report):
    """Index a run report's parked/shipped members by slug -> ``session_id``, so
    a member whose live heartbeat entry has none can still carry a resume handle
    from the last run report."""
    ids = {}
    if not report:
        return ids
    for bucket in ("needs_human", "rejected", "shipped"):
        for entry in report.get(bucket, []) or []:
            sid = entry.get("session_id")
            if sid:
                ids[entry.get("member")] = sid
    return ids


def _annotate_member_actions(members, heartbeat, report):
    """Attach each member's resumable ``session_id`` (from the heartbeat roster,
    falling back to the last run report) and its eligible ``actions``."""
    roster = _roster_by_slug(heartbeat)
    report_ids = _report_session_ids(report)
    for m in members:
        entry = roster.get(m["slug"], {})
        m["session_id"] = entry.get("session_id") or report_ids.get(m["slug"])
        m["actions"] = member_actions(m, entry)


def _epic_board(root, slug, hosting_root=None):
    """Aggregate one epic: status, theme, initiative context, worktree-aware
    members, and the run context merged from the live heartbeat and last
    report.

    ``hosting_root`` is the root the epic itself lives under (defaulting to
    ``root``): its file, status, heartbeat, and run report are all read from
    there, so an epic authored inside a ``.worktrees/<name>`` worktree — where
    a worktree-run autopilot also writes its heartbeat — aggregates with its
    real run context. Member states keep deriving from the invocation ``root``,
    whose own worktree probe already reaches every checkout. The hosting root
    rides the row as ``location``, mirroring a member's."""
    epic_root = hosting_root or root
    with open(ss._epic_path(epic_root, slug), encoding="utf-8") as fh:
        text = fh.read()
    meta = dict(ss._epic_metadata(text))
    initiative = None
    if meta.get("Initiative"):
        initiative = _initiative_context(root, meta["Initiative"])
    header, rows = sc.parse_epic_changes(text)
    report_path = os.path.join(sc.specs_dir(epic_root), "autopilot",
                               "%s-report.json" % slug)
    heartbeat = _read_json(heartbeat_path(epic_root, slug))
    report = _read_json(report_path)
    members = _member_rows(root, header, rows)
    _annotate_member_actions(members, heartbeat, report)
    return {
        "slug": slug,
        "status": ss.read_epic_status(epic_root, slug),
        "theme": meta.get("Theme"),
        "initiative": initiative,
        "location": os.path.abspath(epic_root),
        "members": members,
        "heartbeat": heartbeat,
        "report": report,
    }


def _group_epics(epics):
    """Group aggregated epic dicts under their initiative, preserving encounter
    order. Each group is ``{"initiative": {"slug", "status"} | None, "epics":
    [...]}``; epics carrying no ``Initiative:`` collect under a single
    workspace-wide group whose ``initiative`` is ``None`` (design: initiative
    grouping)."""
    groups = []
    by_slug = {}
    workspace_wide = None
    for epic in epics:
        init = epic.get("initiative")
        slug = init.get("slug") if init else None
        if slug:
            grp = by_slug.get(slug)
            if grp is None:
                grp = {"initiative": {"slug": slug,
                                      "status": init.get("status")},
                       "epics": []}
                by_slug[slug] = grp
                groups.append(grp)
            grp["epics"].append(epic)
        else:
            if workspace_wide is None:
                workspace_wide = {"initiative": None, "epics": []}
                groups.append(workspace_wide)
            workspace_wide["epics"].append(epic)
    return groups


def _all_epic_member_slugs(root):
    """Every slug appearing in any epic's ``## Changes`` stub table discoverable
    from ``root`` — every epic under the invocation root **or** a
    ``.worktrees/<name>`` worktree, independent of a ``--epic`` scope — the
    exclusion set :func:`standalone_changes` uses so a change adopted into an
    epic never also lists as standalone, whether that epic has merged yet or
    not. A missing or unreadable epic file contributes nothing rather than
    raising."""
    slugs = set()
    for eslug, epic_root in _epic_slugs(root):
        try:
            with open(ss._epic_path(epic_root, eslug), encoding="utf-8") as fh:
                _header, rows = sc.parse_epic_changes(fh.read())
        except (OSError, sc.ConfigError):
            continue
        for mslug, _desc, _ratings in rows:
            slugs.add(mslug)
    return slugs


def build_board(root, epic=None):
    """Aggregate the delivery board for ``root`` (every epic, or only ``epic``).

    Returns ``{"root", "generated_at", "epics": [...], "groups": [...],
    "standalone": [...]}`` where each epic carries its status, theme, initiative
    context, hosting ``location``, worktree-aware member states, live heartbeat,
    and last run report (design: board data shape). Epics are discovered
    through :func:`_epic_slugs` — the invocation root's own first, then those
    hosted only under a ``.worktrees/<name>`` worktree, each aggregated exactly
    once from its hosting root — so an epic authored in its own worktree is on
    the board before its PR merges. The flat ``epics`` list is preserved;
    ``groups`` buckets those same epic dicts under their initiative (a
    workspace-wide group for epics carrying no ``Initiative:``);
    ``standalone`` holds the changes planned outside any epic
    (:func:`standalone_changes`, empty when none), each with empty board
    ``actions`` (run/open are epic-scoped). An explicit ``epic`` no candidate
    hosts raises ``ValueError`` — the CLI turns it into a one-line error rather
    than a raw FileNotFoundError from ``_epic_board``."""
    if epic is not None:
        hosting_root = ss._epic_hosting_root(root, epic)
        if hosting_root is None:
            raise ValueError(
                "epic '%s' not found under %s" % (epic, sc.specs_dir(root)))
        pairs = [(epic, hosting_root)]
    else:
        pairs = _epic_slugs(root)
    epics = [_epic_board(root, s, hosting_root=r) for s, r in pairs]
    standalone = standalone_changes(root, _all_epic_member_slugs(root))
    for row in standalone:
        row["actions"] = []
    board = {
        "root": os.path.abspath(root),
        "generated_at": time.time(),
        "epics": epics,
        "groups": _group_epics(epics),
        "standalone": standalone,
    }
    # Attach each interactive build heartbeat to its slug-matching member so the
    # activity predicates and the throughput chart see hand-driven builds too
    # (delivery-dashboard board-tui / board-throughput-chart specs).
    attach_build_heartbeats(root, board)
    return board


# ---------------------------------------------------------------------------
# Pure renderers
# ---------------------------------------------------------------------------

def _render_epic_lines(epic, board_root):
    """Render one epic's header, run line, and member rows (the shared body of
    the text board, indented under its initiative group header)."""
    lines = []
    header = "  epic %s [%s]" % (epic["slug"], epic.get("status") or "?")
    if epic.get("theme"):
        header += "  theme: %s" % epic["theme"]
    # An epic authored inside a worktree (its `location` is not the board root)
    # is marked exactly as a worktree-derived member row is (delivery-dashboard
    # board-aggregation). A fixture carrying no `location` stays unmarked.
    location = epic.get("location")
    if location and location != board_root:
        header += "  [worktree]"
    lines.append(header)

    hb = epic.get("heartbeat")
    if hb:
        lines.append("    run: %s  seq %s  %s" % (
            hb.get("state") or "?", hb.get("seq") or "?",
            _age(hb.get("updated_at"))))
    else:
        lines.append("    run: (no live heartbeat)")

    roster = _roster_by_slug(hb)
    for m in epic.get("members", []):
        entry = roster.get(m["slug"], {})
        stage = entry.get("stage") or ""
        if stage and entry.get("attempt"):
            stage = "%s#%s" % (stage, entry["attempt"])
        loc = " [worktree]" if m.get("location") != board_root else ""
        acts = m.get("actions") or []
        act = " (%s)" % "/".join(acts) if acts else ""
        lines.append("      %-22s %-12s %-10s risk %-6s%s%s" % (
            m["slug"], m.get("state") or "?", stage,
            m.get("risk") or "?", loc, act))
    lines.append("")
    return lines


def render_board_lines(board):
    """Render ``board`` as a list of aligned text lines — the pure renderer
    shared by the ``board`` verb's text mode and the ``tui`` verb. Epics are
    printed under their initiative group header (a workspace-wide header for
    epics carrying no ``Initiative:``); each epic names its status/theme and run
    age; each member names its worktree-aware state, its live stage (joined from
    the heartbeat roster), its risk, and its eligible actions. No terminal
    interaction."""
    lines = []
    board_root = board.get("root")
    groups = board.get("groups")
    if groups is None:
        # A board without pre-computed groups (e.g. a hand-built fixture) still
        # renders under a single workspace-wide header.
        groups = [{"initiative": None, "epics": board.get("epics", [])}]
    for group in groups:
        init = group.get("initiative")
        if init:
            lines.append("initiative %s (%s)" % (
                init.get("slug"), init.get("status") or "?"))
        else:
            lines.append("initiative (workspace-wide)")
        for epic in group.get("epics", []):
            lines.extend(_render_epic_lines(epic, board_root))
    return lines


# ---------------------------------------------------------------------------
# Diff-aware refresh — pure content/signature helpers
# ---------------------------------------------------------------------------

def _lane_signature(cards, group_mode, search_query, initiative_by_epic=None,
                    filters=()):
    """A hashable, order-sensitive signature of one lane's card specs (as
    returned per-lane by :func:`_lane_contents`), folding in the active
    grouping mode (``epic``/``initiative``/``none``), the active
    ``search_query``, and the active ``filters`` (an ordered tuple of
    ``(kind, value)`` chips) — equal when every card's epic slug/status, member
    slug/state, live stage (from the roster entry and from a live build
    heartbeat), and eligible actions match in the same order *and*
    ``group_mode``, the query, and the filter chips are unchanged; differs
    otherwise. Folding the query in means a query edit always repaints (the
    highlight span changes even when the filtered set does not), while an idle
    refresh under a steady query repaints nothing; folding the chips in means a
    chip change always repaints and an idle refresh under steady chips repaints
    nothing. While a grouping mode is active (``epic`` or
    ``initiative``) each card also folds in its epic's initiative identity
    from ``initiative_by_epic`` (epic slug → ``(slug, status)`` or ``None``) —
    the group headers render it, so re-tagging an epic to another initiative
    or an initiative status change repaints the lane; flat ``none`` lanes
    render no initiative, so there it is ignored. Depends solely on
    board-derived content plus the grouping mode and query, never on other
    transient UI state (e.g. a collapsed epic group), so such state survives
    an unchanged refresh while changing the mode always repaints."""
    initiative_by_epic = initiative_by_epic or {}
    sig = [group_mode, search_query, tuple(filters)]
    for epic_slug, status, member, entry in cards:
        entry = entry or {}
        initiative = (initiative_by_epic.get(epic_slug)
                      if group_mode != "none" else None)
        # A live interactive build heartbeat drives both the card's lane and
        # its stage suffix, so its stage folds in too — a stage transition
        # that keeps the member in one lane, or a heartbeat ageing past
        # `BUILD_FRESH_SECONDS` into the same lane, still repaints
        # (delivery-dashboard board-live-build-lane spec). Judged against the
        # wall clock: this is the render path, which has no injected clock.
        build_hb = member.get("build_heartbeat")
        build_stage = build_hb.get("stage") if _build_is_live(build_hb) \
            else None
        sig.append((epic_slug, status, initiative,
                    member.get("slug"), member.get("state"),
                    entry.get("stage"), entry.get("state"), build_stage,
                    tuple(member.get("actions") or ())))
    return tuple(sig)


def _search_matches(query, epic_slug, initiative, member_slug):
    """Whether a member is kept by the board's live search (delivery-dashboard
    board-search spec): a case-insensitive substring hit of ``query`` in the
    member's slug, its epic's slug, or its epic's initiative slug. An empty or
    whitespace-only query matches everything; a ``None`` initiative contributes
    no field (so it never matches on its own). Pure — no ``textual``."""
    q = (query or "").strip().lower()
    if not q:
        return True
    init_slug = initiative.get("slug") if initiative else None
    for field in (member_slug, epic_slug, init_slug):
        if field and q in field.lower():
            return True
    return False


_RISK_TIERS = ("high", "medium", "low")


def _filter_matches(filters, epic_slug, initiative, member):
    """Whether a member is kept by the active filter chips (delivery-dashboard
    board-filter-strip spec) — **faceted**: chips are grouped by kind
    (``risk``/``epic``/``initiative``) and the member passes when, for **every**
    kind present, it matches **at least one** of that kind's values (same-kind
    OR, cross-kind AND). ``risk`` tests the member's ``risk`` rating, ``epic``
    the member's epic slug, ``initiative`` the epic's initiative slug (a
    ``None`` initiative contributes no slug, so it never matches). Empty filters
    match everything. Pure — no ``textual``."""
    by_kind = {}
    for kind, value in filters:
        by_kind.setdefault(kind, set()).add(value)
    init_slug = initiative.get("slug") if initiative else None
    field_for = {
        "risk": member.get("risk"),
        "epic": epic_slug,
        "initiative": init_slug,
    }
    for kind, values in by_kind.items():
        field = field_for.get(kind)
        if field is None or field not in values:
            return False
    return True


def _filter_options(board, active):
    """The filter picker's available ``(kind, value)`` options in a fixed order
    (delivery-dashboard board-filter-strip spec): the risk tiers
    ``high``/``medium``/``low``, then each epic slug in board order, then each
    distinct initiative slug in group order (the no-initiative bucket
    contributes none), minus any chip already in ``active``. Pure — no
    ``textual``."""
    active = set(active)
    options = [("risk", tier) for tier in _RISK_TIERS]
    for epic in board.get("epics", []):
        slug = epic.get("slug")
        if slug:
            options.append(("epic", slug))
    seen = set()
    for group in board.get("groups", []):
        initiative = group.get("initiative")
        slug = initiative.get("slug") if initiative else None
        if slug and slug not in seen:
            seen.add(slug)
            options.append(("initiative", slug))
    return [opt for opt in options if opt not in active]


def _board_totals_text(board):
    """The filter strip's full-board totals label (delivery-dashboard
    board-filter-strip spec): ``N specs · N epics · N initiatives`` from the
    **whole** board — members summed across every epic, the epic count, and the
    distinct-initiative count (groups carrying an initiative, deduped by slug).
    Never the narrowed view. Pure — no ``textual``."""
    epics = board.get("epics", []) if board else []
    specs = sum(len(epic.get("members") or []) for epic in epics)
    initiatives = set()
    for group in (board.get("groups", []) if board else []):
        initiative = group.get("initiative")
        slug = initiative.get("slug") if initiative else None
        if slug:
            initiatives.add(slug)
    return "%d specs · %d epics · %d initiatives" % (
        specs, len(epics), len(initiatives))


def _sync_label(last_sync, now=None):
    """The synced-ago strip stat for the epoch time of the last interval
    refresh (delivery-dashboard board-filter-strip spec): ``synced Ns ago``
    with the ``_age``-style s/m/h tiers, or ``synced ?`` when never synced.
    ``now`` (an epoch float) is injectable for determinism, defaulting to the
    wall clock. Pure — no ``textual``."""
    if not last_sync:
        return "synced ?"
    if now is None:
        now = time.time()
    delta = max(0, int(now - last_sync))
    if delta < 60:
        return "synced %ds ago" % delta
    if delta < 3600:
        return "synced %dm ago" % (delta // 60)
    return "synced %dh ago" % (delta // 3600)


def _highlight_slug(slug, query):
    """``slug`` with its first case-insensitive match of ``query`` wrapped in
    ``[$accent]…[/]`` content markup (``$accent`` is a theme variable, so the
    span picks up the active palette). The slug is returned unchanged for an
    empty/whitespace query or when it holds no match. Pure — no ``textual``."""
    q = (query or "").strip().lower()
    if not q:
        return slug
    idx = slug.lower().find(q)
    if idx < 0:
        return slug
    end = idx + len(q)
    return "%s[$accent]%s[/]%s" % (slug[:idx], slug[idx:end], slug[end:])


# ---------------------------------------------------------------------------
# Board action launchers (pure argv builders)
# ---------------------------------------------------------------------------

_AUTOPILOT_PY = os.path.join(SCRIPTS_DIR, "autopilot.py")


def _member_worktree(root, slug):
    """The member's worktree directory (where its change lives / will live)."""
    return os.path.join(root, ".worktrees", slug)


def _tmux_window(cwd, inner):
    """Wrap an interactive ``inner`` argv as a ``tmux new-window`` opening in
    ``cwd`` — the inner command is passed as a single shell string."""
    return ["tmux", "new-window", "-c", cwd, shlex.join(inner)]


def _interactive_launch(root, slug, inner, tmux):
    """Build an interactive launch from ``inner``: a ``tmux new-window`` in the
    member's worktree when ``$TMUX`` is set, else a ``suspend`` launch the App
    runs via ``App.suspend()``. ``tmux`` None reads ``$TMUX``."""
    if tmux is None:
        tmux = bool(os.environ.get("TMUX"))
    cwd = _member_worktree(root, slug)
    if tmux:
        return {"mode": "tmux", "argv": _tmux_window(cwd, inner), "cwd": root}
    return {"mode": "suspend", "argv": list(inner), "cwd": cwd}


def build_plan_launch(root, epic, member, *, tmux=None):
    """The launch for the ``plan`` action: an interactive ``/s:plan <member>``
    session in the member's worktree (tmux window under ``$TMUX``, else a
    suspend launch). Pure — returns ``{"mode", "argv", "cwd"}``."""
    inner = ["claude", "/s:plan %s" % member["slug"]]
    return _interactive_launch(root, member["slug"], inner, tmux)


def build_run_launch(root, epic, member, *, tmux=None):
    """The launch for the ``run`` action: a detached single-member driver that
    writes the heartbeat the board tails — spawned in the background regardless
    of ``$TMUX`` so the board never blocks. Returns ``{"mode": "detach", ...}``."""
    argv = [sys.executable, _AUTOPILOT_PY, epic, "--member", member["slug"],
            "--root", root]
    return {"mode": "detach", "argv": argv, "cwd": root}


def build_epic_run_launch(root, epic):
    """The launch for the epic-level ``run``: a detached full-autopilot
    driver over every unplanned/ready member of ``epic``, writing the same
    heartbeat the board tails. Returns ``{"mode": "detach", ...}``."""
    argv = [sys.executable, _AUTOPILOT_PY, epic, "--root", root]
    return {"mode": "detach", "argv": argv, "cwd": root}


def build_open_launch(root, epic, member, *, tmux=None):
    """The launch for the ``open`` action: resume the member's exact session via
    ``claude --resume <id>`` (tmux window under ``$TMUX``, else suspend). Returns
    ``None`` when the member carries no session id (nothing to resume)."""
    sid = member.get("session_id")
    if not sid:
        return None
    inner = ["claude", "--resume", sid]
    return _interactive_launch(root, member["slug"], inner, tmux)


def build_editor_launch(path, editor=None):
    """The launch for a detail modal's ``o`` key: open ``path`` in the user's
    editor as a **suspend** launch the App runs via ``App.suspend()`` (an
    editor view is ephemeral, so — unlike a resumed session — it never opens a
    tmux window). The editor is resolved from the ``editor`` argument, else
    ``$EDITOR``, else ``vi``. Pure — returns ``{"mode", "argv", "cwd"}`` with
    ``cwd`` the artifact's own directory (delivery-dashboard board-modal-chrome
    spec)."""
    editor = editor or os.environ.get("EDITOR") or "vi"
    return {"mode": "suspend", "argv": [editor, path],
            "cwd": os.path.dirname(path)}


# The action slug -> its pure launch builder.
_LAUNCH_BUILDERS = {
    "plan": build_plan_launch,
    "run": build_run_launch,
    "open": build_open_launch,
}


def _find_member(board, epic_slug, member_slug):
    """The member row for ``member_slug`` under ``epic_slug`` in ``board``, or
    ``None`` — the resolution a click/keypress on a card button runs to reach the
    member's session id and worktree."""
    for epic in board.get("epics", []):
        if epic.get("slug") != epic_slug:
            continue
        for m in epic.get("members", []):
            if m.get("slug") == member_slug:
                return m
    return None


def _find_epic(board, epic_slug):
    """The epic dict for ``epic_slug`` in ``board``, or ``None`` — the lookup
    an epic group header runs to read its initiative at mount time (rather
    than threading it through :func:`_lane_contents`)."""
    for epic in board.get("epics", []):
        if epic.get("slug") == epic_slug:
            return epic
    return None


def epic_stalled(epic):
    """Whether ``epic`` (a board dict as built by :func:`build_board`) is
    stalled: its live heartbeat's run finished, yet at least one roster entry is
    parked ``needs-human``. Gate ``rejected`` members do not stall — rejection
    is the normal enrichment park. Pure — reads only ``epic["heartbeat"]``, no
    ``textual`` and no I/O."""
    return bool(stalled_entries(epic))


def stalled_entries(epic):
    """The ``needs-human`` roster entries (each carrying ``slug``/``stage``/
    ``reason``) of a stalled ``epic`` — empty when the run has not finished or
    no member is parked ``needs-human``. Pure companion to :func:`epic_stalled`."""
    hb = epic.get("heartbeat")
    if not hb or hb.get("state") != "finished":
        return []
    return [e for e in hb.get("roster", [])
            if e.get("state") == "needs-human"]


def _count_suffix(count):
    """The per-lane card-count suffix for a group header title: a muted
    ` (N)` in the theme's ``$fg-muted`` foreground (markup), or ``""`` when
    ``count`` is ``None``. Shared by every group header — epic, standalone, and
    initiative — so the count reads identically across grouping modes
    (delivery-dashboard board-epic-grouping spec). The muted markup rides the
    same rendering path the title's ``[status]``/``✗`` markup already proves.
    Pure — no ``textual``."""
    if count is None:
        return ""
    return " [$fg-muted](%d)[/]" % count


def epic_group_title(epic_slug, epic_status, initiative, stalled=False,
                     count=None, worktree=False):
    """The label text for one epic's group header: slug + status, plus the
    initiative's slug when the epic belongs to one (delivery-dashboard
    board-epic-grouping spec) — re-homing the initiative -> epic structure
    the removed hierarchy panel used to carry, and — when ``count`` is given —
    the count of that epic's cards in the lane as a muted ` (N)` suffix (theme
    ``$fg-muted`` markup) after the initiative segment. ``count=None`` keeps
    the output byte-identical to before the per-lane count. When ``stalled`` is
    set the title is prefixed with a theme-error-colored ``✗`` marker. When
    ``worktree`` is set — the epic is hosted under a ``.worktrees/<name>``
    root rather than the board's own (delivery-dashboard board-aggregation) —
    a muted ``[worktree]`` marker closes the title; its brackets are
    **escaped** (``\\[``) so content markup paints them literally instead of
    swallowing the word as a style tag. ``worktree=False`` keeps the output
    byte-identical to before the marker. Pure — no ``textual``."""
    title = "%s [%s]" % (epic_slug, epic_status)
    if initiative:
        title += " · %s" % initiative.get("slug")
    title += _count_suffix(count)
    if worktree:
        title += " [$fg-muted]\\[worktree][/]"
    if stalled:
        title = "[$text-error]✗[/] " + title
    return title


def initiative_group_title(initiative):
    """The label text for one initiative-mode lane group (delivery-dashboard
    board-epic-grouping spec): ``<slug> [<status>]`` for a real initiative, or
    ``workspace`` for the ``None`` bucket that collects epics carrying no
    ``Initiative:``. Pure — no ``textual``."""
    if not initiative:
        return "workspace"
    return "%s [%s]" % (initiative.get("slug"), initiative.get("status"))


def resolve_action_launch(board, root, region):
    """Resolve a card-button ``region`` to its launch spec (or ``None``): the
    builder lookup plus member resolution, without spawning anything. Pure — the
    testable core of the tui's launch dispatch."""
    builder = _LAUNCH_BUILDERS.get(region.get("action"))
    if builder is None:
        return None
    member = _find_member(board, region.get("epic"), region.get("member"))
    if member is None:
        return None
    return builder(root, region.get("epic"), member)


# ---------------------------------------------------------------------------
# Session-activity charts — dependency-free resolution/shaping helpers
# ---------------------------------------------------------------------------

# The header throughput chart is a fixed 15 columns wide; the window length is
# that column count times the bucket size (session-activity-view design).
HEADER_CHART_COLUMNS = 15

# The default in-app chart state, shared by every chart on the board and reset
# on each relaunch (graph-config-dialog: settings are not persisted).
DEFAULT_CHART_STATE = {"bucket_seconds": 3, "rows": 3, "scale": "auto"}

# Window-length label per bucket size, and the reverse map the config dialog's
# window row cycles through (45s/90s/3m → 3/6/12-second buckets).
WINDOW_LABELS = {3: "45s", 6: "90s", 12: "3m"}
WINDOW_BUCKETS = [3, 6, 12]


def _window_label(bucket_seconds):
    """The window-length label (``45s``/``90s``/``3m``) for a bucket size."""
    return WINDOW_LABELS.get(bucket_seconds, "%ds" % (bucket_seconds * 15))


def _newest_series(buckets, bucket_seconds, cols):
    """The newest ``cols`` bucket totals as a contiguous series (oldest first,
    newest last), zero-filling empty buckets, anchored on the latest bucket
    present — ``[0] * cols`` when there are none. Pure."""
    if not buckets:
        return [0] * cols
    last = max(buckets)
    return [buckets.get(last - (cols - 1 - i) * bucket_seconds, 0)
            for i in range(cols)]


def chart_lines_and_stats(events, chart_state, cols, rows):
    """Fold accumulated ``(start, end, tokens)`` interval events into a ``cols``-wide,
    ``rows``-high eighth-block chart under ``chart_state``, returning
    ``(chart_rows, newest, peak)`` — the row strings plus the newest bucket's
    value and the window peak. The shared pure core every chart on the board
    renders through (header, config dialog, and member modal). No ``textual``."""
    bucket_seconds = chart_state["bucket_seconds"]
    buckets = br.bucket_events(events, bucket_seconds)
    series = _newest_series(buckets, bucket_seconds, cols)
    floor, ceiling = br.scale_bounds(series, chart_state["scale"])
    chart_rows = br.render_chart(series, rows, floor, ceiling)
    newest = series[-1] if series else 0
    peak = max(series) if series else 0
    return chart_rows, newest, peak


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_board(args):
    board = build_board(os.path.abspath(args.root), epic=args.epic)
    if args.json:
        print(json.dumps(board, indent=2, sort_keys=True))
    else:
        for line in render_board_lines(board):
            print(line)
    return 0


# ---------------------------------------------------------------------------
# The textual App: lifecycle lanes, focusable task cards
# ---------------------------------------------------------------------------

# The one-row muted footer key-hint line each board modal docks at its bottom
# (delivery-dashboard board-modal-chrome spec) — the exact strings the modals
# render and the spec's scenarios pin.
_SPEC_MODAL_HINTS = "⇥ tabs · j/k scroll · o editor · y copy · esc close"
_EPIC_MODAL_HINTS = "j/k scroll · o editor · y copy · esc close"
_RUN_CONFIRM_HINTS = "esc close"

# The muted reassurance line the stall banner carries above its Retry control
# (delivery-dashboard board-stall-signal spec): a retry is safe because the
# autopilot re-enters each member at its first unsatisfied stage and skips
# non-unplanned members, so nothing already durable runs a second time.
_STALL_NOTE = ("Safe to retry — every step is checkpointed, so the run "
               "resumes from the last durable state. Nothing runs twice.")


def _risk_badge(risk):
    """A ``modal-badge`` chip for a member's ``risk``, classed
    ``badge-risk-<risk>`` when the risk is one of the closed vocabulary
    (``low``/``medium``/``high``) so its CSS tints it through the ``$risk-*``
    theme variable, else the muted tier (board-modal-chrome spec)."""
    value = (risk or "").lower()
    cls = ("badge-risk-%s" % value if value in ("low", "medium", "high")
           else "badge-muted")
    return Static(risk or "?", classes="modal-badge %s" % cls, markup=False)


def _lane_badge(lane):
    """A ``modal-badge`` chip for a member's derived ``lane``, classed
    ``badge-lane-<lane>`` so its CSS tints it through that lane's ``$lane-*``
    theme variable (board-modal-chrome spec). ``lane`` comes from
    :func:`_member_column`, so the chip never disagrees with the board."""
    return Static(lane, classes="modal-badge badge-lane-%s" % lane,
                  markup=False)


class MemberDetailScreen(ModalScreen):
    """The spec-detail modal a focused :class:`TaskCard` pushes on ``Enter``
    (or click): a header naming the change (slug, risk, state) and a
    reference to its epic's status, a horizontal rule, then — resolved via
    the dependency-free :func:`change_artifacts` — a tabbed view of the
    change's on-disk spec files (Plan / Spec / Tasks) rendered as Markdown,
    or a not-yet-planned notice when it has none. Dismissed by ``Escape`` or
    a click on the ``✕`` close control."""

    BINDINGS = [
        Binding("escape", "dismiss_detail", "Close", show=False),
        Binding("tab", "next_tab", "Next tab", show=False),
        Binding("j", "scroll_content_down", "Scroll down", show=False),
        Binding("k", "scroll_content_up", "Scroll up", show=False),
        Binding("y", "copy_slug", "Copy slug", show=False),
        Binding("o", "open_editor", "Open in editor", show=False),
    ]

    CSS = """
    MemberDetailScreen {
        align: center middle;
    }
    MemberDetailScreen > Container {
        width: 80%;
        height: 80%;
        border: solid $shipd-border-strong;
        padding: 1 2;
        background: $surface;
    }
    MemberDetailScreen .modal-title-bar {
        height: 1;
        background: $accent;
        color: $background;
    }
    MemberDetailScreen .modal-title-bar .compact-button {
        background: $accent;
        color: $background;
    }
    MemberDetailScreen .modal-title-bar .compact-button:hover {
        background: $accent-dim;
    }
    MemberDetailScreen .modal-title-bar .compact-button:focus {
        background: $accent-dim;
        color: $background;
    }
    MemberDetailScreen TabbedContent {
        height: 1fr;
    }
    MemberDetailScreen Tab {
        color: $fg-muted;
    }
    MemberDetailScreen Tab.-active {
        color: $accent;
        text-style: bold;
    }
    MemberDetailScreen Underline > .underline--bar {
        color: $accent;
    }
    MemberDetailScreen #member-activity-progress {
        height: auto;
        text-align: left;
        color: $fg-muted;
    }
    MemberDetailScreen #member-activity-chart {
        height: 3;
    }
    MemberDetailScreen #member-activity-detail {
        height: auto;
        color: $fg-muted;
        margin-bottom: 1;
    }
    #member-signal-callout {
        background: $error 10%;
        height: auto;
        margin: 0 0 1 0;
    }
    #member-signal-callout .signal-accent-bar {
        width: 1;
        height: 100%;
        background: $error;
    }
    #member-signal-callout .signal-reason {
        width: 1fr;
        height: auto;
        color: $warning;
        padding: 0 1;
    }
    """

    def __init__(self, epic_slug, member, entry=None, epic_status=None):
        super().__init__()
        self.epic_slug = epic_slug
        self.member = member
        self.entry = entry or {}
        self.epic_status = epic_status
        # Resolve this member's own session and, when it does, prepare a single-
        # session tail plus its accumulated events for the activity panel
        # (session-activity-timeline). No resolvable session -> no panel.
        self._tail = None
        self._events = []
        self._session_total = 0
        # The active-tab-order artifact list `compose` resolves (and the live
        # notice→tabs swap replaces), kept on the instance so the `tab`/`o`
        # actions can resolve the active tab's on-disk `path`; `[]` while the
        # not-yet-planned notice shows, so those keys are no-ops (board-modal-
        # chrome).
        self._artifacts = []
        key = self._resolve_session()
        if key is not None:
            self._tail = br.ActivityTail(*key)

    def _resolve_session(self):
        """The ``(tdir, session_id)`` key of the member's own transcript, or
        ``None``: the recorded session id when present, else the newest
        transcript for the member's location while its live state is
        ``driving`` (session-activity-timeline)."""
        m, entry = self.member, self.entry
        location = m.get("location")
        session_id = m.get("session_id") or entry.get("session_id")
        if session_id:
            return _resolve_member_session(location, session_id)
        if entry.get("state") == "driving":
            return _resolve_member_session(location, None)
        return None

    def compose(self) -> ComposeResult:
        m, entry = self.member, self.entry
        stage = entry.get("stage")
        session_id = m.get("session_id") or entry.get("session_id")
        actions = m.get("actions") or []
        meta = []
        if session_id:
            meta.append("session: %s" % session_id)
        if actions:
            meta.append("actions: %s" % ", ".join(actions))
        # A parked member (delivery-dashboard board-parked-member-signal spec)
        # swaps the muted live-stage chip for an honest error-tier state chip
        # — the stage is a stale leftover, not a live signal — and, when its
        # entry carries a reason, surfaces it in a tinted callout above the
        # artifact tabs.
        signal = member_signal(m, entry)
        # A member carried by a live interactive build heartbeat surfaces that
        # heartbeat's stage instead, so the chip matches the lane
        # `_member_column` placed it in (delivery-dashboard
        # board-live-build-lane spec).
        build_hb = m.get("build_heartbeat")
        build_stage = build_hb.get("stage") if _build_is_live(build_hb) \
            else None

        with Container():
            # Accent title bar naming the member's slug with the inline `✕`
            # close (board-modal-chrome): same button and wiring, new chrome.
            with Horizontal(classes="modal-title-bar"):
                yield Static(m["slug"], classes="modal-title-text",
                             markup=False)
                yield Button("✕", id="close-detail", classes="compact-button")
            # Badge meta row of theme-tinted chips: a risk chip only when the
            # member carries a rating (an unrated member's row starts at the
            # lane chip, no `?` placeholder), a lane chip (via `_member_column`,
            # so it never disagrees with the board), a muted live-stage chip
            # while actually being driven (never for a parked member whose
            # stage is a stale leftover) or, failing that, from a live build
            # heartbeat, an error-tier state chip for a parked member, and the
            # muted epic ref.
            with Horizontal(classes="modal-badge-row"):
                if m.get("risk"):
                    yield _risk_badge(m.get("risk"))
                yield _lane_badge(_member_column(m, entry))
                if signal is not None:
                    yield Static(signal["label"],
                                 classes="modal-badge badge-error",
                                 markup=False)
                elif stage and entry.get("state") == "driving":
                    attempt = entry.get("attempt")
                    stage_text = ("%s#%s" % (stage, attempt) if attempt
                                  else stage)
                    yield Static("stage: %s" % stage_text,
                                 classes="modal-badge badge-muted",
                                 markup=False)
                elif build_stage:
                    yield Static("stage: %s" % build_stage,
                                 classes="modal-badge badge-muted",
                                 markup=False)
                yield Static(
                    "epic: %s [%s]" % (self.epic_slug, self.epic_status or "?"),
                    classes="modal-badge badge-muted", markup=False)
            if meta:
                yield Static("\n".join(meta), classes="modal-meta-lines",
                             markup=False)
            yield Rule()
            if signal is not None and signal.get("reason"):
                # The member-level analogue of the epic stall banner: a
                # tinted accent-bar callout surfacing the validation output
                # that parked this member, above the artifact tabs.
                with Horizontal(id="member-signal-callout"):
                    yield Static("", classes="signal-accent-bar")
                    yield Static(signal["reason"], classes="signal-reason",
                                 markup=False)
            if self._tail is not None:
                # The live activity panel sits between the header and the tabs
                # (session-activity-timeline): a left-aligned build-progress
                # line (elapsed since build start + completed-task progress),
                # then a width-adaptive 3-row chart of this session's own
                # output tokens plus a detail line.
                yield Static("", id="member-activity-progress", markup=False)
                yield ActivityChart(
                    lambda: self._events, on_repaint=self._on_chart,
                    id="member-activity-chart")
                yield Static("", id="member-activity-detail")
            # Resolve artifacts from the member's worktree-aware hosting
            # directory (the `location` the board aggregation derived),
            # falling back to the invocation root when none was recorded —
            # so a change planned or archived inside its own worktree shows
            # its Plan/Spec/Tasks tabs (delivery-dashboard: worktree-aware
            # modal artifacts). `change_artifacts` returns [] for a missing
            # directory, so a stale location degrades to the notice.
            artifacts = change_artifacts(
                m.get("location") or self.app.root, m["slug"])
            self._artifacts = artifacts
            if artifacts:
                yield self._artifact_tabs(artifacts)
            else:
                yield Static(artifact_notice(entry), id="artifact-notice")
            yield Static(_SPEC_MODAL_HINTS, classes="modal-footer-hints",
                         markup=False)

    def _artifact_tabs(self, artifacts):
        """The tabbed artifact view (one Plan/Spec/Tasks pane per resolved
        artifact) as a single ready-to-mount widget, so ``compose`` and the
        live notice→tabs swap (modal-live-artifacts) build an identical
        structure. Appending to ``_tab_content`` is exactly what
        ``TabbedContent``'s own ``compose_add_child`` does for the
        ``with TabbedContent(): with TabPane(): …`` context syntax — which is
        only available inside ``compose`` — so this reproduces it for the
        post-compose mount."""
        tabs = TabbedContent()
        for artifact in artifacts:
            tabs._tab_content.append(
                TabPane(artifact["label"],
                        VerticalScroll(Markdown(artifact["text"]))))
        return tabs

    def on_mount(self) -> None:
        # Poll once so the activity panel is populated on open, then refresh on
        # a 3-second interval without the modal being reopened
        # (session-activity-timeline). The interval runs unconditionally — even
        # with no resolvable session — so the empty-artifacts notice can be
        # swapped for the tabbed view the moment artifacts appear
        # (modal-live-artifacts); the activity poll inside is a no-op when no
        # session resolved.
        self._refresh_activity()
        self.set_interval(3.0, self._refresh_activity)

    def _refresh_activity(self) -> None:
        """The 3-second refresh handler the interval timer and tests invoke.
        Polls this session's tail (when one resolved), accumulates its new
        events and running token total, and repaints the panel chart (which
        refreshes the detail line); then, while the empty-artifacts notice is
        still showing, re-resolves the member's artifacts and swaps in the
        tabbed view once they appear (modal-live-artifacts)."""
        if self._tail is not None:
            try:
                new = self._tail.poll()
            except Exception:
                new = []
            self._events.extend(new)
            self._session_total += sum(tok for _s, _e, tok in new)
            for chart in self.query("#member-activity-chart"):
                chart._repaint()
            # Refresh the build-progress line so its elapsed token advances
            # without the modal being reopened (session-activity-timeline).
            progress = self._progress_text()
            for w in self.query("#member-activity-progress"):
                w.update(progress)
        self._mount_artifacts_if_ready()

    def _mount_artifacts_if_ready(self) -> None:
        """While the empty-artifacts notice is mounted, re-run the same
        worktree-aware ``change_artifacts`` resolution ``compose`` used and, on
        a non-empty result, replace the notice with the tabbed artifact view in
        the slot it occupied — so artifacts emitted while the modal is open
        appear without it being closed and reopened (modal-live-artifacts).
        Returns immediately once the notice is gone, so already-mounted tabs are
        never remounted or reset."""
        notices = list(self.query("#artifact-notice"))
        if not notices:
            return
        m = self.member
        artifacts = change_artifacts(
            m.get("location") or self.app.root, m["slug"])
        if not artifacts:
            return
        self._artifacts = artifacts
        notice = notices[0]
        # The notice is the last child of its container, so mounting the tabs
        # after it and then removing it lands them in the notice's slot.
        notice.parent.mount(self._artifact_tabs(artifacts))
        notice.remove()

    def _progress_text(self) -> str:
        """The activity panel's top progress line: elapsed since the build
        started and completed-task progress (session-activity-timeline). The
        elapsed token resolves ``started_at`` from the roster entry first, else
        the member's build heartbeat, and is omitted when neither yields one;
        the tasks token derives from the member's ``tasks.md`` checkbox counts
        and is omitted when the member has no ``tasks.md``."""
        m = self.member
        location = m.get("location") or self.app.root
        slug = m["slug"]
        tokens = []
        started_at = self.entry.get("started_at")
        if started_at is None:
            hb = _read_json(build_heartbeat_path(location, slug))
            if isinstance(hb, dict):
                started_at = hb.get("started_at")
        if started_at:
            tokens.append(
                "elapsed %s"
                % br.human_duration(max(0, time.time() - started_at)))
        counts = ss.count_tasks(location, slug)
        if counts is not None:
            done, _in_progress, total = counts
            tokens.append("tasks %d/%d" % (done, total))
        return " · ".join(tokens)

    def _on_chart(self, newest, peak) -> None:
        state = self.app.chart_state
        detail = "peak %s · now %s · window %s · session %s" % (
            br.fmt_tokens(peak), br.fmt_tokens(newest),
            _window_label(state["bucket_seconds"]),
            br.fmt_tokens(self._session_total))
        for w in self.query("#member-activity-detail"):
            w.update(detail)

    def action_dismiss_detail(self):
        self.dismiss()

    def _tabbed(self):
        """The mounted :class:`TabbedContent`, or ``None`` while the
        not-yet-planned notice shows instead."""
        found = list(self.query(TabbedContent))
        return found[0] if found else None

    def _active_index(self, tabs):
        """The index — into ``_artifacts`` and the tab strip's document order —
        of the currently active artifact tab, or ``None``."""
        ids = [pane.id for pane in tabs.query(TabPane)]
        if tabs.active not in ids:
            return None
        return ids.index(tabs.active)

    def action_next_tab(self):
        # Advance to the next artifact tab, wrapping past the last; a no-op
        # while the notice (no TabbedContent) shows (board-modal-chrome).
        tabs = self._tabbed()
        if tabs is None:
            return
        ids = [pane.id for pane in tabs.query(TabPane)]
        if not ids:
            return
        idx = self._active_index(tabs) or 0
        tabs.active = ids[(idx + 1) % len(ids)]

    def _active_scroll(self):
        """The active artifact pane's :class:`VerticalScroll`, or ``None`` —
        also while no tab is active yet (``get_pane`` would raise)."""
        tabs = self._tabbed()
        if tabs is None or self._active_index(tabs) is None:
            return None
        pane = tabs.get_pane(tabs.active)
        scrolls = list(pane.query(VerticalScroll))
        return scrolls[0] if scrolls else None

    def action_scroll_content_down(self):
        scroll = self._active_scroll()
        if scroll is not None:
            scroll.scroll_down(animate=False)

    def action_scroll_content_up(self):
        scroll = self._active_scroll()
        if scroll is not None:
            scroll.scroll_up(animate=False)

    def action_copy_slug(self):
        self.app.copy_to_clipboard(self.member["slug"])

    def action_open_editor(self):
        # Open the active tab's artifact in `$EDITOR` as a suspend launch; a
        # no-op while the notice shows (no artifact on disk) (board-modal-
        # chrome).
        tabs = self._tabbed()
        if tabs is None or not self._artifacts:
            return
        idx = self._active_index(tabs)
        if idx is None or idx >= len(self._artifacts):
            return
        self.app._spawn_launch(
            build_editor_launch(self._artifacts[idx]["path"]))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-detail":
            self.dismiss()


class EpicRunConfirmScreen(ModalScreen):
    """The confirmation modal the epic-detail modal's **Run epic** control
    pushes (delivery-dashboard board-epic-grouping spec) — choosing Run no
    longer dispatches the epic-level run directly; it opens this small
    centred box whose top row is an **accent title bar** naming the epic slug
    with the compact ``✕`` close control inline at the bar's right edge
    (board-modal-chrome), the exact prompt "This will deliver the full epic,
    are you sure you want to continue?", a Yes/No control pair, and a muted
    footer key-hint line. The epic-level run — the same autopilot launch the
    removed hierarchy panel used to trigger — fires only on Yes; No, ✕, or
    ``Escape`` dismiss without dispatching anything (mirrors
    ``MemberDetailScreen``'s ``Escape``-dismiss binding)."""

    BINDINGS = [Binding("escape", "dismiss_confirm", "Close", show=False)]

    CSS = """
    EpicRunConfirmScreen {
        align: center middle;
    }
    EpicRunConfirmScreen > Container {
        width: auto;
        height: auto;
        max-width: 60;
        border: solid $shipd-border-strong;
        padding: 1 2;
        background: $surface;
    }
    EpicRunConfirmScreen .modal-title-bar {
        height: 1;
        background: $accent;
        color: $background;
    }
    EpicRunConfirmScreen .modal-title-bar .compact-button {
        background: $accent;
        color: $background;
    }
    EpicRunConfirmScreen .modal-title-bar .compact-button:hover {
        background: $accent-dim;
    }
    EpicRunConfirmScreen .modal-title-bar .compact-button:focus {
        background: $accent-dim;
        color: $background;
    }
    EpicRunConfirmScreen .confirm-prompt {
        width: 100%;
        margin: 1 0;
    }
    EpicRunConfirmScreen .confirm-buttons {
        height: auto;
        align: center middle;
    }
    EpicRunConfirmScreen .confirm-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, epic_slug):
        super().__init__()
        self.epic_slug = epic_slug

    def compose(self) -> ComposeResult:
        with Container():
            # Accent title bar naming the epic slug with the inline `✕` close
            # at its right edge (board-modal-chrome): same button and wiring,
            # moved off its former top-left row into the accent band.
            with Horizontal(classes="modal-title-bar"):
                yield Static(self.epic_slug, classes="modal-title-text",
                             markup=False)
                yield Button("✕", id="epic-run-close", classes="compact-button")
            yield Static(
                "This will deliver the full epic, are you sure you want "
                "to continue?", classes="confirm-prompt")
            with Horizontal(classes="confirm-buttons"):
                yield Button("Yes", id="epic-run-yes",
                             classes="button-primary")
                yield Button("No", id="epic-run-no",
                             classes="button-secondary")
            yield Static(_RUN_CONFIRM_HINTS, classes="modal-footer-hints",
                         markup=False)

    def action_dismiss_confirm(self):
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "epic-run-yes":
            self.app.dispatch_epic_run(self.epic_slug)
            self.dismiss()
        elif event.button.id in ("epic-run-no", "epic-run-close"):
            self.dismiss()


class EpicMemberRow(Horizontal):
    """One member row in the :class:`EpicDetailScreen`'s member list
    (epic-detail-drilldown change): a clickable, focusable row carrying a
    **lane badge** (board-modal-chrome spec) — a ``badge-lane-<lane>`` chip
    derived by the same :func:`_member_column` the board's lanes use, so it
    never disagrees with the board — ahead of the ``<slug>  [<risk>]
    <state>`` text (``markup=False`` so the bracketed risk is not swallowed as
    Rich markup). Clicking the row pushes that member's
    :class:`MemberDetailScreen`, mirroring :meth:`TaskCard.on_click`'s exact
    push. Carries ``epic_slug``/``member``/``entry``/``epic_status`` so the
    pushed modal has everything ``MemberDetailScreen`` needs, unchanged."""

    can_focus = True

    def __init__(self, epic_slug, member, entry, epic_status, **kwargs):
        self.epic_slug = epic_slug
        self.member = member
        self.entry = entry or {}
        self.epic_status = epic_status
        super().__init__(classes="epic-member-row", **kwargs)

    def compose(self) -> ComposeResult:
        yield _lane_badge(_member_column(self.member, self.entry))
        yield Static(
            "%s  [%s]  %s" % (
                self.member.get("slug"), self.member.get("risk") or "?",
                self.member.get("state") or "?"),
            markup=False, classes="epic-member-text")

    def on_click(self, event: Click) -> None:
        self.focus()
        self.app.push_screen(
            MemberDetailScreen(self.epic_slug, self.member, self.entry,
                               self.epic_status))


class EpicDetailScreen(ModalScreen):
    """The epic-detail modal a click on the epic group header's title (off
    the collapse arrow) pushes (delivery-dashboard board-epic-grouping spec)
    — the epic counterpart to :class:`MemberDetailScreen`'s spec-detail
    modal. A large, centred ``Container`` (mirroring ``MemberDetailScreen``'s
    ``80%``×``80%`` box) shows a header naming the epic's slug, status,
    theme, and initiative (resolved live via :func:`_find_epic`), a **Run
    epic** control when the epic is runnable and not stalled, a horizontal
    rule, a list of the epic's member specs — each ``<slug>  [<risk>]
    <state>`` — another rule, and the epic's own ``epics/<slug>/epic.md``
    overview rendered as Markdown (resolved via the dependency-free
    :func:`epic_markdown`), or a not-found notice when it has none.
    Dismissed by ``Escape`` or a click on the ``✕`` close control, matching
    ``MemberDetailScreen``'s top-right close pattern."""

    BINDINGS = [
        Binding("escape", "dismiss_detail", "Close", show=False),
        Binding("j", "scroll_content_down", "Scroll down", show=False),
        Binding("k", "scroll_content_up", "Scroll up", show=False),
        Binding("y", "copy_slug", "Copy slug", show=False),
        Binding("o", "open_editor", "Open in editor", show=False),
    ]

    CSS = """
    EpicDetailScreen {
        align: center middle;
    }
    EpicDetailScreen > Container {
        width: 80%;
        height: 80%;
        border: solid $shipd-border-strong;
        padding: 1 2;
        background: $surface;
    }
    EpicDetailScreen .modal-title-bar {
        height: 1;
        background: $accent;
        color: $background;
    }
    EpicDetailScreen .modal-title-bar .compact-button {
        background: $accent;
        color: $background;
    }
    EpicDetailScreen .modal-title-bar .compact-button:hover {
        background: $accent-dim;
    }
    EpicDetailScreen .modal-title-bar .compact-button:focus {
        background: $accent-dim;
        color: $background;
    }
    EpicDetailScreen VerticalScroll {
        height: 1fr;
    }
    .epic-detail-actions {
        height: auto;
        margin: 0 0 1 0;
    }
    #epic-stall-banner {
        background: $error 10%;
        height: auto;
        margin: 0 0 1 0;
    }
    #epic-stall-banner .stall-accent-bar {
        width: 1;
        height: 100%;
        background: $error;
    }
    #epic-stall-banner .stall-body {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }
    #epic-stall-banner .stall-header {
        height: auto;
    }
    #epic-stall-banner .stall-action-row {
        height: auto;
    }
    #epic-stall-banner .stall-title {
        color: $text-error;
        text-style: bold;
        width: auto;
    }
    #epic-stall-banner .stall-summary {
        width: 1fr;
        text-align: right;
        color: $fg-muted;
    }
    #epic-stall-banner .stall-member-row {
        height: auto;
    }
    #epic-stall-banner .stall-stage {
        color: $fg-muted;
        margin: 0 0 0 2;
        width: auto;
    }
    #epic-stall-banner .stall-reason-chip {
        color: $warning;
        background: $warning 10%;
        padding: 0 1;
        margin: 0 0 0 2;
        width: auto;
    }
    #epic-stall-banner .stall-slug {
        width: auto;
    }
    #epic-stall-banner .stall-note {
        color: $fg-muted;
    }
    #epic-stall-banner .stall-age {
        width: 1fr;
        text-align: right;
        color: $fg-subtle;
    }
    """

    def __init__(self, epic_slug):
        super().__init__()
        self.epic_slug = epic_slug

    def compose(self) -> ComposeResult:
        epic = _find_epic(self.app.board, self.epic_slug) or {}
        theme = epic.get("theme")
        initiative = epic.get("initiative")

        with Container():
            # Accent title bar naming the epic slug with the inline `✕` close;
            # status/theme/initiative move into the badge row below
            # (board-modal-chrome).
            with Horizontal(classes="modal-title-bar"):
                yield Static(self.epic_slug, classes="modal-title-text",
                             markup=False)
                yield Button("✕", id="epic-detail-close",
                             classes="compact-button")
            with Horizontal(classes="modal-badge-row"):
                yield Static(epic.get("status") or "?",
                             classes="modal-badge badge-muted", markup=False)
                if theme:
                    yield Static("theme: %s" % theme,
                                 classes="modal-badge badge-muted",
                                 markup=False)
                if initiative:
                    yield Static("initiative: %s" % initiative.get("slug"),
                                 classes="modal-badge badge-muted",
                                 markup=False)
            stalled = epic_stalled(epic)
            if epic_is_runnable(epic) and not stalled:
                # Run epic moved here from the removed header ``≡`` menu
                # (delivery-dashboard board-epic-grouping spec) — gated off
                # while the stall banner's own Retry is showing, so the modal
                # never offers two ways to launch the same run.
                with Horizontal(classes="epic-detail-actions"):
                    yield Button("Run epic", id="epic-run",
                                 classes="button-primary")
            yield Rule()
            if stalled:
                # A finished run left members parked needs-human with no live
                # session to resume — a tinted accent-bar banner warns per
                # parked member and offers a primary Retry that re-runs the
                # epic-level autopilot (board-stall-signal). The one-cell
                # `.stall-accent-bar` is a background-filled Static (not an
                # edge border, which would draw box glyphs).
                parked = stalled_entries(epic)
                hb = epic.get("heartbeat") or {}
                with Horizontal(id="epic-stall-banner"):
                    yield Static("", classes="stall-accent-bar")
                    with Vertical(classes="stall-body"):
                        with Horizontal(classes="stall-header"):
                            yield Static("STALLED", classes="stall-title")
                            yield Static(
                                "%d member(s) parked · needs-human"
                                % len(parked), classes="stall-summary")
                        for e in parked:
                            with Horizontal(classes="stall-member-row"):
                                yield Static(e.get("slug") or "",
                                             classes="stall-slug",
                                             markup=False)
                                yield Static(e.get("stage") or "?",
                                             classes="stall-stage",
                                             markup=False)
                                yield Static(e.get("reason") or "",
                                             classes="stall-reason-chip",
                                             markup=False)
                        yield Static(_STALL_NOTE, classes="stall-note")
                        with Horizontal(classes="stall-action-row"):
                            yield Button("Retry run", id="epic-retry",
                                         classes="button-primary")
                            yield Static(
                                _age(hb.get("updated_at"), verb="parked"),
                                classes="stall-age")
            members = epic.get("members") or []
            if members:
                roster = _roster_by_slug(epic.get("heartbeat"))
                for m in members:
                    yield EpicMemberRow(
                        self.epic_slug, m, roster.get(m["slug"], {}),
                        epic.get("status"))
            else:
                yield Static("no specs")
            yield Rule()
            # The overview reads the epic artifact from the root that hosts it
            # — a worktree's when the epic was authored there and has not
            # merged yet (delivery-dashboard board-aggregation).
            text = epic_markdown(epic.get("location") or self.app.root,
                                 self.epic_slug)
            if text is not None:
                with VerticalScroll():
                    yield Markdown(text)
            else:
                yield Static("epic file not found")
            yield Static(_EPIC_MODAL_HINTS, classes="modal-footer-hints",
                         markup=False)

    def action_dismiss_detail(self):
        self.dismiss()

    def _overview_scroll(self):
        """The overview :class:`VerticalScroll`, or ``None`` while the epic
        file is missing (no scroller mounted)."""
        scrolls = list(self.query(VerticalScroll))
        return scrolls[0] if scrolls else None

    def action_scroll_content_down(self):
        scroll = self._overview_scroll()
        if scroll is not None:
            scroll.scroll_down(animate=False)

    def action_scroll_content_up(self):
        scroll = self._overview_scroll()
        if scroll is not None:
            scroll.scroll_up(animate=False)

    def action_copy_slug(self):
        self.app.copy_to_clipboard(self.epic_slug)

    def action_open_editor(self):
        # Open the epic's own `epics/<slug>/epic.md` in `$EDITOR` as a suspend
        # launch, resolving the content dir exactly as `epic_markdown` does —
        # from the epic's hosting root, so a worktree-authored epic opens the
        # file the overview above is showing (delivery-dashboard
        # board-aggregation); a no-op when the epic file is absent
        # (board-modal-chrome).
        epic = _find_epic(self.app.board, self.epic_slug) or {}
        epic_root = epic.get("location") or self.app.root
        epic_path = os.path.join(
            sc.specs_dir(epic_root), "epics", self.epic_slug, "epic.md")
        if not os.path.isfile(epic_path):
            return
        self.app._spawn_launch(build_editor_launch(epic_path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "epic-detail-close":
            self.dismiss()
        elif event.button.id == "epic-retry":
            # Re-run the epic-level autopilot directly — the stall banner's
            # own Retry, unchanged (delivery-dashboard board-epic-grouping
            # spec) — then close the modal.
            self.app.dispatch_epic_run(self.epic_slug)
            self.dismiss()
        elif event.button.id == "epic-run":
            # Run epic opens the confirmation modal — the epic-level run
            # dispatches only from that modal's Yes, exactly as before
            # (delivery-dashboard board-epic-grouping spec).
            self.app.push_screen(EpicRunConfirmScreen(self.epic_slug))


class TaskCard(Static):
    """One member's card in its lifecycle lane — a single terminal row: a
    risk-coloured ``●`` glyph (a subtle ``✓`` in the shipped lane), the slug,
    and (while driving) its current stage in the muted tier. The focus
    highlight comes from ``CSS`` (``TaskCard:focus``).
    Carries ``epic_slug``/``member``/``entry`` so RUN/PLAN/OPEN dispatch
    resolves the underlying member via the unchanged pure launch builders
    (design: actions reuse the pure builders) — ``r``/``l``/``o`` fire
    ``run``/``plan``/``open`` through :meth:`BoardApp.dispatch_card_action`,
    a no-op when that action is not among the member's eligible ``actions``.
    Also carries ``epic_status`` — the change's epic status, unused for
    rendering the card itself but threaded into the detail modal it opens.
    ``Enter`` pushes the member detail modal; the arrow keys move focus
    spatially across cards and lanes via :meth:`BoardApp.move_card_focus`."""

    can_focus = True

    BINDINGS = [
        Binding("enter", "select", "Open detail", show=False),
        Binding("up", "focus_up", "Focus up", show=False),
        Binding("down", "focus_down", "Focus down", show=False),
        Binding("left", "focus_left", "Focus left", show=False),
        Binding("right", "focus_right", "Focus right", show=False),
        Binding("r", "run_action", "Run", show=False),
        Binding("l", "plan_action", "Plan", show=False),
        Binding("o", "open_action", "Open", show=False),
    ]

    def __init__(self, epic_slug, member, entry, epic_status, search_query="",
                 **kwargs):
        self.epic_slug = epic_slug
        self.member = member
        self.entry = entry or {}
        self.epic_status = epic_status
        self.search_query = search_query
        super().__init__(self._card_text(), **kwargs)

    def _card_text(self):
        # The slug's matched span is wrapped in `[$accent]…[/]` under an active
        # query (delivery-dashboard board-search spec); an empty query or a
        # non-slug (epic/initiative) match leaves the slug plain.
        slug = _highlight_slug(self.member["slug"], self.search_query)
        # A shipped row swaps the risk glyph for a subtle-tier ✓ (no stage);
        # the theme-variable markup resolves through the same merged-variables
        # path as the `[$text-error]✗` stall marker (delivery-dashboard
        # board-tui / board-shipd-theme spec).
        if _member_column(self.member, self.entry) == "shipped":
            return "[$fg-subtle]✓[/] %s" % slug
        # A parked member (delivery-dashboard board-parked-member-signal spec)
        # renders its error-tier glyph and muted state label in place of the
        # risk glyph and live stage, so it is never mistaken for an idle or
        # actively-driving card.
        signal = member_signal(self.member, self.entry)
        if signal is not None:
            return "[$text-error]%s[/] %s[$fg-muted] · %s[/]" % (
                signal["glyph"], slug, signal["label"])
        # A risk-coloured ● glyph precedes the slug; a missing or unknown risk
        # renders the glyph in the muted foreground tier.
        risk = (self.member.get("risk") or "").lower()
        glyph_var = "$risk-%s" % risk if risk in ("low", "medium", "high") \
            else "$fg-muted"
        text = "[%s]●[/] %s" % (glyph_var, slug)
        # While the member is being driven its live stage is appended in the
        # muted tier after the slug; failing that, a live interactive build
        # heartbeat — the lane placement `_member_column` already honours —
        # appends its own stage the same way (delivery-dashboard
        # board-live-build-lane spec).
        if self.entry.get("state") == "driving":
            stage = self.entry.get("stage")
            if stage:
                text += "[$fg-muted] · %s[/]" % stage
            return text
        build_hb = self.member.get("build_heartbeat")
        if _build_is_live(build_hb):
            stage = build_hb.get("stage")
            if stage:
                text += "[$fg-muted] · %s[/]" % stage
        return text

    def action_select(self):
        self.app.push_screen(
            MemberDetailScreen(self.epic_slug, self.member, self.entry,
                               self.epic_status))

    def on_click(self, event: Click) -> None:
        self.focus()
        self.action_select()

    def action_focus_up(self):
        self.app.move_card_focus(self, "up")

    def action_focus_down(self):
        self.app.move_card_focus(self, "down")

    def action_focus_left(self):
        self.app.move_card_focus(self, "left")

    def action_focus_right(self):
        self.app.move_card_focus(self, "right")

    def action_run_action(self):
        self.app.dispatch_card_action(self, "run")

    def action_plan_action(self):
        self.app.dispatch_card_action(self, "plan")

    def action_open_action(self):
        self.app.dispatch_card_action(self, "open")


class Lane(VerticalScroll):
    """One bordered, vertically-scrolling lifecycle lane holding its
    members' focusable :class:`TaskCard` widgets. A one-row ``.lane-header``
    band, docked at the top and tinted with the lane's ``$lane-<name>`` theme
    variable, labels the lane — replacing the former border title and, being
    docked, staying pinned above the scroll region and surviving every lane
    repaint (delivery-dashboard board-tui spec)."""

    def __init__(self, name, **kwargs):
        self.lane_name = name
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Static(self.lane_name.upper(), classes="lane-header")


class EpicCollapsibleTitle(CollapsibleTitle):
    """The epic group header's title widget (delivery-dashboard board-epic-
    grouping spec): a click on the **leading collapse-arrow cell** toggles the
    group, and a click **anywhere else on the title** opens the epic-detail
    modal instead — the header carries no separate menu control, so the title
    itself must split the click. ``CollapsibleTitle`` renders
    ``<pad-left><arrow> <label>`` under its default ``padding: 0 1``, so the
    left pad occupies column 0 and the arrow glyph sits at widget column
    **1** — ``event.offset.x <= 1`` covers exactly that pad+arrow cell.
    Overrides ``_on_click`` (rather than leaving the inherited toggle-on-any-
    click behaviour) to ``event.stop()`` and ``event.prevent_default()`` —
    Textual's dispatch walks the MRO and invokes every class's own
    ``_on_click``, so without suppressing the default action the inherited
    ``CollapsibleTitle._on_click`` would *also* fire and unconditionally post
    its own ``Toggle`` right after ours — then post exactly one message: the
    inherited ``Toggle`` when the click lands on the pad/arrow, otherwise the
    new :class:`OpenEpic` carrying ``epic_slug`` for the board to route to
    :class:`EpicDetailScreen`."""

    class OpenEpic(Message):
        """Posted when the title is clicked off the collapse arrow — carries
        the epic slug so the board app can push its detail modal."""

        def __init__(self, epic_slug):
            self.epic_slug = epic_slug
            super().__init__()

    def __init__(self, *args, epic_slug=None, **kwargs):
        self.epic_slug = epic_slug
        super().__init__(*args, **kwargs)

    def _on_click(self, event) -> None:
        event.stop()
        event.prevent_default()
        if event.offset.x <= 1:
            self.post_message(self.Toggle())
        else:
            self.post_message(self.OpenEpic(self.epic_slug))


class EpicCollapsible(Collapsible):
    """The epic group header's collapsible container (delivery-dashboard
    board-epic-grouping spec): identical to :class:`Collapsible` except its
    title widget is :class:`EpicCollapsibleTitle` instead of the stock
    ``CollapsibleTitle``, so the header can split a click between the
    collapse arrow and opening the epic-detail modal. ``Collapsible.compose``
    yields ``self._title`` and ``_update_collapsed``/``_watch_title`` both
    drive ``self._title``, so swapping it right after the base ``__init__``
    keeps every existing toggle/label wire-up — including
    ``Collapsible._on_collapsible_title_toggle``, which still handles the
    inherited ``Toggle`` message the new title still posts on an arrow
    click."""

    def __init__(self, *children, epic_slug=None, title="Toggle",
                 collapsed=True, **kwargs):
        super().__init__(*children, title=title, collapsed=collapsed,
                          **kwargs)
        self._title = EpicCollapsibleTitle(
            label=title, collapsed_symbol="▶", expanded_symbol="▼",
            collapsed=collapsed, epic_slug=epic_slug)


class EpicGroupRow(Horizontal):
    """One epic group's header row, wrapping a single child: the group's
    :class:`Collapsible` (or :class:`EpicCollapsible` for a real epic group)
    at ``width: 1fr``, so it — and every member card inside it — keeps the
    lane's whole content width. The header carries **no menu control and no
    other trailing control** (delivery-dashboard board-epic-grouping spec):
    the title row holds only the collapse arrow and the title text, and for
    an epic group the title itself (:class:`EpicCollapsibleTitle`) splits the
    click between toggling the arrow cell and opening the epic-detail modal,
    so there is nothing left to float on a second layer. The per-lane card
    count rides the title as a muted ` (N)` suffix, not a trailing element.
    The row carries the ``$panel`` band across its full box so the surface
    reaches the divider with no lane-background gap."""


class SearchInput(Input):
    """The controls-strip live-search field (delivery-dashboard board-search
    spec). A thin :class:`Input` subclass so it can carry an ``escape`` binding
    that clears-and-refocuses the board — while it holds focus the board's
    card/app keys (``q``/``g``/``r``/``l``/``o``) don't fire, the standard
    ``Input`` capture behaviour."""

    BINDINGS = [Binding("escape", "clear_search", "Clear", show=False)]

    async def action_clear_search(self) -> None:
        await self.app._clear_search()


class ActivityChart(Static):
    """A width-adaptive, fixed 3-row eighth-block activity chart shared by the
    graph config dialog and the member modal. Its column count follows the
    widget's own rendered width (falling back to the header's 15 while it is
    unsized); it folds an ``events_provider``'s accumulated
    ``(start, end, output_tokens)`` interval events through :func:`chart_lines_and_stats`
    under the app's shared chart state, refreshing on a 3-second interval and on
    resize. The chart is always 3 rows regardless of the header-height setting;
    its detail line lives in a sibling the owning screen updates through the
    ``on_repaint(newest, peak)`` callback."""

    ROWS = 3

    def __init__(self, events_provider, on_repaint=None, **kwargs):
        super().__init__("\n".join([" "] * self.ROWS), **kwargs)
        self._events_provider = events_provider
        self._on_repaint = on_repaint

    def on_mount(self) -> None:
        self._repaint()
        self.set_interval(3.0, self._repaint)

    def on_resize(self, event) -> None:
        self._repaint()

    def _cols(self) -> int:
        width = self.content_size.width
        return width if width and width > 0 else HEADER_CHART_COLUMNS

    def _repaint(self) -> None:
        try:
            events = self._events_provider() or []
        except Exception:
            events = []
        state = self.app.chart_state
        chart_rows, newest, peak = chart_lines_and_stats(
            events, state, self._cols(), self.ROWS)
        self.update("\n".join(chart_rows))
        if self._on_repaint is not None:
            self._on_repaint(newest, peak)


class GraphOption(Static):
    """One clickable segment of a config-dialog setting row (delivery-dashboard
    graph-config-dialog): carries its setting ``key`` and the ``value`` it
    selects, applied to the app chart state on click. Not focusable, so the
    dialog's screen-level arrow bindings always fire."""

    def __init__(self, key, value, label, **kwargs):
        super().__init__(label, classes="graph-option", **kwargs)
        self.setting_key = key
        self.setting_value = value

    def on_click(self, event: Click) -> None:
        self.screen.apply_option(self.setting_key, self.setting_value)


class GraphConfigScreen(ModalScreen):
    """The graph config dialog the header chart opens (delivery-dashboard
    graph-config-dialog): an accent title, the ``output tokens`` metric label, a
    width-adaptive 3-row throughput chart with a peak/window/now detail line,
    then three segmented setting rows — window (``45s``/``90s``/``3m`` →
    3/6/12-second buckets), height (``3 rows``/``1 row``, the header footprint),
    and scale (``auto``/``fixed 12K``). ``↑``/``↓`` move the selected row,
    ``←``/``→`` step the selected row's value, options are also clickable, and
    ``esc`` closes. Every change applies immediately to the app's in-app chart
    state (never persisted) and repaints every live chart."""

    BINDINGS = [
        # Priority so Escape closes the dialog regardless of which child widget
        # holds focus (graph-config-dialog).
        Binding("escape", "dismiss_config", "Close", show=False, priority=True),
        Binding("up", "row_up", "Up", show=False),
        Binding("down", "row_down", "Down", show=False),
        Binding("left", "value_prev", "Prev", show=False),
        Binding("right", "value_next", "Next", show=False),
    ]

    CSS = """
    GraphConfigScreen {
        align: center middle;
    }
    GraphConfigScreen > Container {
        width: 64;
        height: auto;
        border: solid $shipd-border-strong;
        padding: 1 2;
        background: $surface;
    }
    GraphConfigScreen .graph-config-header {
        height: auto;
    }
    GraphConfigScreen .graph-config-title {
        width: 1fr;
    }
    GraphConfigScreen #graph-dialog-chart {
        height: 3;
    }
    GraphConfigScreen .graph-config-metric {
        color: $fg-muted;
    }
    GraphConfigScreen .graph-setting-row {
        height: auto;
    }
    GraphConfigScreen .graph-setting-row.selected {
        background: $bg-active;
    }
    GraphConfigScreen .graph-setting-label {
        width: 10;
        color: $fg-muted;
    }
    GraphConfigScreen .graph-option {
        width: auto;
        height: 1;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    GraphConfigScreen .graph-option.active {
        background: $accent 25%;
        color: $accent;
    }
    """

    # (chart_state key, row label, [(option label, option value), ...]).
    SETTINGS = [
        ("bucket_seconds", "window", [("45s", 3), ("90s", 6), ("3m", 12)]),
        ("rows", "height", [("3 rows", 3), ("1 row", 1)]),
        ("scale", "scale", [("auto", "auto"), ("fixed 12K", "fixed")]),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected = 0

    def _events(self):
        """The board-throughput events the dialog charts, pulled from the live
        header chart's accumulated history (empty when it is unavailable)."""
        try:
            return self.app.query_one(HeaderChart)._events
        except Exception:
            return []

    def compose(self) -> ComposeResult:
        with Container():
            with Horizontal(classes="graph-config-header"):
                yield Static("[$accent]graph · throughput[/]",
                             classes="graph-config-title")
                yield Button("✕", id="graph-config-close",
                             classes="compact-button")
            yield Static("output tokens", classes="graph-config-metric")
            yield ActivityChart(self._events, on_repaint=self._on_chart,
                                id="graph-dialog-chart")
            yield Static("", id="graph-dialog-detail")
            for key, label, options in self.SETTINGS:
                with Horizontal(classes="graph-setting-row"):
                    yield Static(label, classes="graph-setting-label")
                    for opt_label, opt_value in options:
                        yield GraphOption(key, opt_value, opt_label)

    def on_mount(self) -> None:
        self._refresh_rows()

    def _on_chart(self, newest, peak) -> None:
        state = self.app.chart_state
        detail = "peak %s · window %s · now %s" % (
            br.fmt_tokens(peak), _window_label(state["bucket_seconds"]),
            br.fmt_tokens(newest))
        for w in self.query("#graph-dialog-detail"):
            w.update(detail)

    def _refresh_rows(self) -> None:
        rows = list(self.query(".graph-setting-row"))
        for idx, row in enumerate(rows):
            row.set_class(idx == self.selected, "selected")
            key = self.SETTINGS[idx][0]
            current = self.app.chart_state[key]
            for opt in row.query(GraphOption):
                opt.set_class(opt.setting_value == current, "active")

    def apply_option(self, key, value) -> None:
        """Set ``key`` to ``value`` in the app chart state, select that row, and
        repaint the dialog's own chart plus the header chart immediately."""
        self.app.chart_state[key] = value
        for idx, (k, _label, _opts) in enumerate(self.SETTINGS):
            if k == key:
                self.selected = idx
                break
        self._refresh_rows()
        for chart in self.query(ActivityChart):
            chart._repaint()
        for header in self.app.query(HeaderChart):
            header._repaint()

    def _step(self, delta) -> None:
        key, _label, options = self.SETTINGS[self.selected]
        values = [v for _l, v in options]
        current = self.app.chart_state.get(key)
        try:
            i = values.index(current)
        except ValueError:
            i = 0
        i = max(0, min(len(values) - 1, i + delta))
        self.apply_option(key, values[i])

    def action_row_up(self) -> None:
        self.selected = max(0, self.selected - 1)
        self._refresh_rows()

    def action_row_down(self) -> None:
        self.selected = min(len(self.SETTINGS) - 1, self.selected + 1)
        self._refresh_rows()

    def action_value_prev(self) -> None:
        self._step(-1)

    def action_value_next(self) -> None:
        self._step(1)

    def action_dismiss_config(self) -> None:
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "graph-config-close":
            self.dismiss()


class HeaderChart(Static):
    """The live board-throughput chart in the controls strip (delivery-
    dashboard board-throughput-chart): a fixed 15-column eighth-block chart of
    output tokens per bucket, summed across every driving member's session. It
    owns a :class:`~build_report.MultiTail` and its own accumulated raw-event
    history, re-synced and re-polled on a 3-second interval, and folds that
    history at render time through :func:`chart_lines_and_stats` under the
    app's shared chart state (so a window change re-buckets losslessly). At the
    3-row height it carries a right label column (window peak / window label /
    newest value in the accent colour); at 1-row height it is a flat sparkline
    plus the newest value. With no driving session it renders blank. Clicking
    it opens the graph config dialog."""

    def __init__(self, **kwargs):
        # Start with blank chart rows (never an empty string) so the widget has
        # a real visual before the first poll paints it.
        blank = "\n".join([" " * HEADER_CHART_COLUMNS] * 3)
        super().__init__(blank, id="header-chart", **kwargs)
        self._tail = br.MultiTail()
        self._events = []

    def on_mount(self) -> None:
        self._tick()
        self.set_interval(3.0, self._tick)

    def _tick(self) -> None:
        board = getattr(self.app, "board", None)
        if board is not None:
            try:
                self._tail.sync(driving_session_keys(board))
                self._events.extend(self._tail.poll())
            except Exception:
                # Transcript parsing is best-effort — a bad line/file never
                # breaks the board (session-activity-view risks).
                pass
        self._repaint()

    def _repaint(self) -> None:
        state = self.app.chart_state
        rows = state["rows"]
        chart_rows, newest, peak = chart_lines_and_stats(
            self._events, state, HEADER_CHART_COLUMNS, rows)
        now = "[$accent]%s[/]" % br.fmt_tokens(newest)
        if rows == 3:
            labels = [br.fmt_tokens(peak), _window_label(state["bucket_seconds"]),
                      now]
            lines = ["%s  %s" % (chart_rows[i], labels[i]) for i in range(3)]
        else:
            lines = ["%s  %s" % (chart_rows[0], now)]
        self.update("\n".join(lines))

    def on_click(self, event: Click) -> None:
        # Never stack a second dialog: opening while one is already on screen
        # is a no-op, so repeated clicks leave exactly one (graph-config-dialog).
        if isinstance(self.app.screen, GraphConfigScreen):
            return
        self.app.push_screen(GraphConfigScreen())


class MetricsScreen(ModalScreen):
    """The delivery-metrics modal the board's ``m`` key (and the "Delivery
    metrics" palette command) pushes (delivery-dashboard board-metrics-view
    spec): a near-full-viewport container over ``$surface`` with a flat
    ``$shipd-border-strong`` border, a header row carrying a clickable ``✕``
    close control, and a scrollable body of four sections — the DORA tile row,
    the throughput run chart, the cycle-time scatterplot, and the cumulative
    flow diagram — rendered by the dependency-free prelude helpers.

    ``metrics.derive`` shells out to git per shipped change (far too slow for
    the 2 s board tick), so the assembly runs **off the UI thread**: a thread
    worker calls the injectable :attr:`_data_fn` (defaulting to
    :func:`metrics_view_data`, mirroring :class:`BoardApp`'s ``board_fn``
    seam), then repaints through the :meth:`_apply_data` seam behind a
    "computing metrics…" placeholder, re-deriving on a 30-second interval while
    open. A failing assembly keeps the last rendered content (or shows an
    unavailable notice) and never raises. Dismissed by ``Escape`` or the ``✕``
    control. All CSS is through ``$`` theme variables (board-shipd-theme
    rule)."""

    BINDINGS = [Binding("escape", "dismiss_metrics", "Close", show=False)]

    CSS = """
    MetricsScreen {
        align: center middle;
    }
    MetricsScreen > Container {
        width: 90%;
        height: 90%;
        border: solid $shipd-border-strong;
        padding: 1 2;
        background: $surface;
    }
    MetricsScreen .metrics-header {
        height: auto;
    }
    MetricsScreen .metrics-header-text {
        width: 1fr;
    }
    MetricsScreen #metrics-body {
        height: 1fr;
    }
    MetricsScreen .metrics-section {
        height: auto;
        margin-bottom: 1;
    }
    MetricsScreen .metrics-section-title {
        color: $fg-muted;
    }
    MetricsScreen .metrics-section-label {
        color: $fg-muted;
    }
    """

    # Section chart heights (plan: DORA tiles 1 row per line, run chart 4,
    # scatter 8, CFD 8), inside the scrollable body.
    RUN_CHART_ROWS = 4
    SCATTER_ROWS = 8
    CFD_ROWS = 8
    # derive is git-bound, so a slow cadence is fine — re-derive every 30 s
    # while the screen is open (board-metrics-view spec).
    REFRESH_SECONDS = 30.0

    def __init__(self, root, data_fn=None):
        super().__init__()
        self.root = root
        # The injectable data callable, mirroring BoardApp's board_fn seam:
        # zero-arg, defaulting to the prelude assembler over this root.
        self._data_fn = data_fn or (lambda: metrics_view_data(root))
        # Whether a data payload has painted the sections yet — gates the
        # unavailable-vs-keep-last decision on a failed assembly.
        self._rendered = False
        # Whether the section widgets have been mounted (once); subsequent
        # applies (the 30 s refresh) update them in place rather than remount,
        # so no duplicate ids and no async remove/mount race.
        self._mounted = False
        # The mutable content/label Statics, keyed for in-place updates.
        self._sections = {}

    def compose(self) -> ComposeResult:
        with Container():
            with Horizontal(classes="metrics-header"):
                yield Static("delivery metrics",
                             classes="metrics-header-text")
                yield Button("✕", id="close-metrics",
                             classes="compact-button")
            with VerticalScroll(id="metrics-body"):
                yield Static("computing metrics…", id="metrics-computing")

    def on_mount(self) -> None:
        # Assemble once on open, then re-derive on the slow interval — both
        # off the UI thread (a no-op repaint until the worker returns).
        self._refresh()
        self.set_interval(self.REFRESH_SECONDS, self._refresh)

    def _refresh(self) -> None:
        self.run_worker(self._worker, thread=True, exclusive=True)

    def _worker(self) -> None:
        data = self._compute()
        self.app.call_from_thread(self._apply_data, data)

    def _compute(self):
        """Run the injected data callable, swallowing any failure (derive's git
        subprocesses, a bad log line) to a ``None`` sentinel so a failed
        assembly never raises out of the worker."""
        try:
            return self._data_fn()
        except Exception:
            return None

    def _cols(self) -> int:
        """The chart column count — the body's rendered width, width-adaptive
        like :class:`ActivityChart` (the header's 15 while still unsized)."""
        body = self.query_one("#metrics-body", VerticalScroll)
        width = body.content_size.width
        return width if width and width > 0 else HEADER_CHART_COLUMNS

    def _build_sections(self):
        """Create the four section widgets once, stashing their mutable
        content/label Statics in :attr:`_sections` for later in-place updates.
        Returns the top-level widgets to mount into the body (the DORA tile
        Static plus a titled container per chart)."""
        dora = Static("", id="metrics-dora", classes="metrics-section")
        made = {"dora": dora}

        def _section(title, body_key, label_key, widget_id):
            body = Static("")
            label = Static("", classes="metrics-section-label")
            made[body_key] = body
            made[label_key] = label
            return Vertical(
                Static(title, classes="metrics-section-title"), body, label,
                id=widget_id, classes="metrics-section")

        sections = [
            dora,
            _section("throughput — ships per ISO week",
                     "run_body", "run_label", "metrics-runchart"),
            _section("cycle time — ship date × cycle seconds",
                     "scatter_body", "scatter_label", "metrics-scatter"),
            _section("cumulative flow", "cfd_body", "cfd_label",
                     "metrics-cfd"),
        ]
        self._sections = made
        return sections

    def _apply_data(self, data) -> None:
        """The repaint/test seam: on the first payload, swap the computing
        placeholder for the four rendered sections; on later payloads (the
        30 s refresh) update them in place. A failed assembly (``data is
        None``) keeps the last rendered content, or shows an unavailable
        notice when nothing has rendered yet. Never raises."""
        if data is None:
            if not self._rendered:
                self._show_unavailable()
            return
        metrics = data.get("metrics") or {}
        ship_events = data.get("ship_events") or []
        cols = self._cols()

        if not self._mounted:
            self._mounted = True
            self.query("#metrics-computing").remove()
            self.query_one("#metrics-body", VerticalScroll).mount(
                *self._build_sections())

        s = self._sections
        s["dora"].update("\n".join("%s: %s" % pair
                                   for pair in dora_tiles(metrics)))
        run_rows, run_label = run_chart_rows(
            (metrics.get("throughput") or {}).get("per_week") or [],
            cols, self.RUN_CHART_ROWS)
        s["run_body"].update("\n".join(run_rows))
        s["run_label"].update(run_label)
        sc_rows, sc_label = scatter_rows(
            ship_events, metrics.get("cycle_time") or {}, cols,
            self.SCATTER_ROWS)
        s["scatter_body"].update("\n".join(sc_rows))
        s["scatter_label"].update(sc_label)
        cfd_r, cfd_label = cfd_rows(
            (metrics.get("flow") or {}).get("series") or [], cols,
            self.CFD_ROWS)
        s["cfd_body"].update("\n".join(cfd_r))
        s["cfd_label"].update(cfd_label)
        self._rendered = True

    def _show_unavailable(self) -> None:
        """Report a failed first assembly without a traceback: reuse the
        computing placeholder (or mount a notice if it is already gone)."""
        placeholder = self.query("#metrics-computing")
        if placeholder:
            self.query_one("#metrics-computing", Static).update(
                "metrics unavailable")
        else:
            self.query_one("#metrics-body", VerticalScroll).mount(
                Static("metrics unavailable", classes="metrics-notice"))

    def action_dismiss_metrics(self) -> None:
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-metrics":
            self.dismiss()


# The Shipd design-system palette registered as a custom ``textual`` theme and
# activated on startup (delivery-dashboard board-shipd-theme spec). It is the
# board's single palette source: the lane/risk colors below are exposed as
# named theme variables so the widget CSS references colors only through `$`
# variables — no hex literals anywhere in the TUI CSS. Built from the Shipd
# tokens (`colors_and_type.css`); the constitution confines every `textual`
# import to this module, so the theme lives here rather than in its own module.
SHIPD_THEME = Theme(
    name="shipd",
    primary="#C6FF4E",
    secondary="#4DA6FF",
    accent="#C6FF4E",
    foreground="#F0F0F8",
    background="#0A0A0D",
    surface="#111118",
    panel="#1C1C26",
    success="#3DCC8E",
    warning="#FF8C42",
    error="#FF4D3D",
    dark=True,
    variables={
        "lane-unplanned": "#8888A0",
        "lane-ready": "#4DA6FF",
        "lane-building": "#FF8C42",
        "lane-review": "#9B7FFF",
        "lane-shipped": "#3DCC8E",
        "risk-high": "#FF8C42",
        "risk-medium": "#C6FF4E",
        "risk-low": "#55556A",
        "shipd-border": "#2A2A38",
        "shipd-border-strong": "#3E3E52",
        "bg-hover": "#22222E",
        "bg-active": "#28283A",
        "accent-dim": "#8FBF1A",
        "fg-muted": "#8888A0",
        "fg-subtle": "#55556A",
        # Pin the scrollbar palette to the muted border tones so textual never
        # derives an accent-tinted thumb (board-scrollbar-theme spec): thumb
        # border-strong, hover/active fg-subtle, track/corner the panel tone.
        "scrollbar": "#3E3E52",
        "scrollbar-hover": "#55556A",
        "scrollbar-active": "#55556A",
        "scrollbar-background": "#1C1C26",
        "scrollbar-background-hover": "#1C1C26",
        "scrollbar-background-active": "#1C1C26",
        "scrollbar-corner-color": "#1C1C26",
    },
)


class FilterPickerScreen(ModalScreen):
    """The filter picker modal the board's ``f`` key (and the strip's
    ``+ filter`` control) pushes (delivery-dashboard board-filter-strip spec):
    a small centred box listing one selectable button per available
    ``(kind, value)`` option — computed by the caller from the pure
    :func:`_filter_options` (the risk tiers, each epic slug, and each
    initiative slug, minus the already-active chips). Each option button
    carries its ``chip_kind``/``chip_value`` and is labelled ``"<kind>:
    <value>"``; pressing one dismisses the picker and adds its chip through
    :meth:`BoardApp.apply_filter`. ``Escape`` (or the ``✕`` control) dismisses
    without selecting. All CSS is through ``$`` theme variables
    (board-shipd-theme rule)."""

    BINDINGS = [Binding("escape", "dismiss_picker", "Close", show=False)]

    CSS = """
    FilterPickerScreen {
        align: center middle;
    }
    FilterPickerScreen > Container {
        width: auto;
        height: auto;
        max-width: 60;
        max-height: 80%;
        border: solid $shipd-border-strong;
        padding: 1 2;
        background: $surface;
    }
    FilterPickerScreen .picker-close-row {
        height: auto;
    }
    FilterPickerScreen .picker-title {
        width: 1fr;
    }
    FilterPickerScreen #picker-options {
        height: auto;
    }
    FilterPickerScreen .picker-option {
        width: 100%;
        height: 1;
        border: none;
    }
    FilterPickerScreen .picker-empty {
        color: $fg-muted;
        margin: 1 0;
    }
    """

    def __init__(self, options):
        super().__init__()
        # The available `(kind, value)` options, precomputed by the caller from
        # `_filter_options(board, active)` so the picker stays free of board
        # state.
        self._options = list(options)

    def compose(self) -> ComposeResult:
        with Container():
            with Horizontal(classes="picker-close-row"):
                yield Static("add filter", classes="picker-title")
                yield Button("✕", id="picker-close",
                             classes="compact-button")
            with VerticalScroll(id="picker-options"):
                if not self._options:
                    yield Static("no filters available",
                                 classes="picker-empty")
                for kind, value in self._options:
                    button = Button("%s: %s" % (kind, value),
                                    classes="picker-option")
                    button.chip_kind = kind
                    button.chip_value = value
                    yield button

    def action_dismiss_picker(self) -> None:
        self.dismiss()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        # Handled here and stopped so the option buttons' `chip_kind` marker
        # never reaches `BoardApp.on_button_pressed` (which would read it as a
        # chip removal).
        event.stop()
        if event.button.id == "picker-close":
            self.dismiss()
            return
        kind = getattr(event.button, "chip_kind", None)
        if kind is not None:
            # Dismiss the picker, then add the chip — it lands on the base
            # board and the lanes repaint.
            self.dismiss()
            await self.app.apply_filter(kind, event.button.chip_value)


class BoardApp(App):
    """The delivery board's ``textual`` application: the five bordered
    lifecycle :class:`Lane` columns of focusable :class:`TaskCard` widgets.
    Data comes from :func:`build_board` (via the injectable ``board_fn`` seam,
    mirroring the ``member_driver``/``sync_fn`` seams elsewhere in the
    engine) — only the rendering is ``textual`` (design: module topology)."""

    CSS = """
    #header-bar {
        height: auto;
        background: $surface;
    }
    #brand {
        width: auto;
        padding: 0 1;
    }
    #search-cluster {
        width: 1fr;
        height: auto;
        align-horizontal: center;
    }
    #board-search-input {
        width: 24;
    }
    #board-search-count {
        width: auto;
        padding: 0 1;
    }
    #group-mode {
        width: auto;
        height: auto;
    }
    .mode-button {
        height: 1;
        border: none;
        min-width: 0;
        padding: 0 1;
        background: $bg-hover;
        color: $fg-muted;
    }
    /* Each segment carries a fixed width — its label plus Button's own
       label chrome (the stable auto width: `epic`/`none` 8, `initiative` 14) —
       so the three segments keep fixed positions and widths whatever the active
       mode (delivery-dashboard board-epic-grouping spec: "Mode segments never
       move"). Pinning the geometry here means the active highlight
       (background/bold on `.mode-active`) can never reflow the segmented
       control, and a narrower width would clip the label. */
    #group-mode-epic {
        width: 8;
    }
    #group-mode-initiative {
        width: 14;
    }
    #group-mode-none {
        width: 8;
    }
    .mode-active {
        background: $primary;
        color: $background;
        text-style: bold;
    }
    .button-primary {
        background: $primary;
        color: $background;
        text-style: bold;
        height: 1;
        border: none;
        padding: 0 2;
        width: auto;
        min-width: 0;
    }
    .button-primary:hover {
        background: $accent-dim;
    }
    .button-secondary {
        background: $bg-hover;
        color: $fg-muted;
        height: 1;
        border: none;
        padding: 0 2;
        width: auto;
        min-width: 0;
    }
    .button-secondary:hover {
        background: $bg-active;
    }
    #autopilot-indicator {
        width: auto;
        padding: 0 1;
    }
    #filter-strip {
        height: auto;
        background: $surface;
    }
    #board-totals {
        width: auto;
        padding: 0 1;
    }
    #filter-chips {
        width: 1fr;
        height: auto;
    }
    .filter-chip {
        height: 1;
        border: none;
        width: auto;
        min-width: 0;
        padding: 0 1;
        background: $primary 25%;
    }
    .filter-chip:hover {
        background: $primary 50%;
    }
    #board-shipped {
        width: auto;
        padding: 0 1;
    }
    #board-synced {
        width: auto;
        padding: 0 1;
    }
    #header-chart {
        width: auto;
        height: auto;
        padding: 0 1;
    }
    #body {
        layout: horizontal;
    }
    .epic-group-row {
        height: auto;
        width: 1fr;
        background: $panel;
        border-bottom: solid $shipd-border;
        layers: group;
    }
    .epic-group {
        background: $panel;
        border-top: none;
        padding-bottom: 0;
        padding-left: 1;
        width: 1fr;
    }
    /* Only the epic-mode groups live inside an `EpicGroupRow`, the one parent
       that declares the `group` layer. Initiative-mode and standalone groups
       carry `.epic-group` too but mount straight into the lane, so the layer
       is scoped here rather than on `.epic-group` — naming a layer the parent
       never declared would leave their placement resting on Textual's
       fallback for an unresolvable layer name. Harmless now that there is no
       second layer to separate it from — kept for parity with those other
       mount sites. */
    .epic-group-row .epic-group {
        layer: group;
    }
    .epic-group Contents {
        padding: 0 0 0 2;
    }
    .epic-group CollapsibleTitle {
        width: 1fr;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        padding-right: 1;
    }
    .compact-button {
        height: 1;
        border: none;
        padding: 0 1;
        width: 3;
        min-width: 3;
        background: $bg-hover;
    }
    .compact-button:hover {
        background: $primary 50%;
    }
    .compact-button:focus {
        background: $primary 50%;
    }
    .modal-title-bar .compact-button {
        background: $accent;
        color: $background;
    }
    .modal-title-bar .compact-button:hover {
        background: $accent-dim;
    }
    .modal-title-text {
        width: 1fr;
        color: $background;
        text-style: bold;
        padding: 0 1;
    }
    .modal-badge-row {
        height: auto;
        padding: 1 0 0 0;
    }
    .modal-badge {
        width: auto;
        height: 1;
        margin: 0 1 0 0;
        padding: 0 1;
    }
    .badge-risk-high {
        background: $risk-high 25%;
        color: $risk-high;
    }
    .badge-risk-medium {
        background: $risk-medium 25%;
        color: $risk-medium;
    }
    .badge-risk-low {
        background: $risk-low 25%;
        color: $risk-low;
    }
    .badge-lane-unplanned {
        background: $lane-unplanned 25%;
        color: $lane-unplanned;
    }
    .badge-lane-ready {
        background: $lane-ready 25%;
        color: $lane-ready;
    }
    .badge-lane-building {
        background: $lane-building 25%;
        color: $lane-building;
    }
    .badge-lane-review {
        background: $lane-review 25%;
        color: $lane-review;
    }
    .badge-lane-shipped {
        background: $lane-shipped 25%;
        color: $lane-shipped;
    }
    .badge-muted {
        background: $fg-muted 25%;
        color: $fg-muted;
    }
    .badge-error {
        background: $error 25%;
        color: $text-error;
    }
    .modal-meta-lines {
        height: auto;
        color: $fg-muted;
    }
    .modal-footer-hints {
        dock: bottom;
        height: 1;
        color: $fg-muted;
    }
    .epic-member-row {
        padding: 0 1;
        height: auto;
        text-wrap: nowrap;
        text-overflow: ellipsis;
    }
    .epic-member-row:focus {
        background: $accent 15%;
    }
    Lane {
        border: solid $shipd-border;
        background: $surface;
        border-title-color: $fg-muted;
        width: 1fr;
        margin: 0 1;
        /* Reserve the vertical scrollbar's column permanently so a lane's
           content width is identical whether or not it currently scrolls —
           the scrollbar can never reflow the rows or share their cells
           (delivery-dashboard lane-scrollbar-gutter spec). */
        scrollbar-gutter: stable;
    }
    .lane-header {
        dock: top;
        height: 1;
        padding: 0 1;
        text-style: bold;
    }
    #lane-unplanned .lane-header {
        background: $lane-unplanned 15%;
        color: $lane-unplanned;
    }
    #lane-ready .lane-header {
        background: $lane-ready 15%;
        color: $lane-ready;
    }
    #lane-building .lane-header {
        background: $lane-building 15%;
        color: $lane-building;
    }
    #lane-review .lane-header {
        background: $lane-review 15%;
        color: $lane-review;
    }
    #lane-shipped .lane-header {
        background: $lane-shipped 15%;
        color: $lane-shipped;
    }
    .lane-empty {
        color: $fg-subtle;
        text-style: italic;
        padding: 0 1;
    }
    TaskCard {
        height: 1;
        padding: 0 1;
        text-wrap: nowrap;
        text-overflow: ellipsis;
    }
    TaskCard:focus {
        background: $accent 15%;
    }
    Tabs:focus Tab.-active {
        color: $background;
        background: $accent;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("g", "cycle_grouping", "Group"),
        Binding("m", "show_metrics", "Metrics"),
        Binding("f", "add_filter", "Filter"),
        Binding("slash", "focus_search", "Search", key_display="/"),
        Binding("ctrl+p", "command_palette", "Palette", key_display="^p",
                priority=True),
    ]

    def __init__(self, root, epic=None, interval=2.0, board_fn=None):
        super().__init__()
        # Register and activate the Shipd theme before first paint (design:
        # theme registration) so the custom palette is live under `run_test`
        # and no default-theme frame flashes.
        self.register_theme(SHIPD_THEME)
        self.theme = "shipd"
        self.root = root
        self.epic = epic
        self.interval = interval
        self._board_fn = board_fn or (
            lambda: build_board(self.root, epic=self.epic))
        self.board = None
        # The lane grouping mode (delivery-dashboard board-epic-grouping spec):
        # `epic` (collapsible per-epic headers, the default), `initiative`
        # (collapsible per-initiative headers), or `none` (flat lanes). The
        # header-bar segmented control, the footer-bound "g" key, and the
        # palette's grouping command all cycle it through GROUP_MODES.
        self.group_mode = "epic"
        # The in-app chart state shared by every chart (header, config dialog,
        # member modal): window bucket size, header height, and scale mode.
        # Reset on each relaunch — never persisted (graph-config-dialog).
        self.chart_state = dict(DEFAULT_CHART_STATE)
        # The active live-search query (delivery-dashboard board-search spec) —
        # view-level state only, folded into `_lane_signature` so a query edit
        # repaints and an idle refresh under a steady query does not.
        self.search_query = ""
        # The active filter chips (delivery-dashboard board-filter-strip spec):
        # an ordered, duplicate-free list of `(kind, value)` tuples with kinds
        # `risk`/`epic`/`initiative`. View-level state only — never persisted —
        # folded into `_lane_signature` so a chip change repaints and an idle
        # refresh under steady chips does not.
        self.filters = []
        # The epoch time of the last interval refresh, for the synced-ago strip
        # stat; `None` until the first `refresh_board`.
        self._last_sync = None
        # Diff-aware refresh: the last-rendered signature per lane, empty so
        # the first `refresh_board()` renders everything.
        self._lane_sigs = {}

    def compose(self) -> ComposeResult:
        # The Shipd-style header bar replaces textual's stock `Header` and the
        # previous controls strip, laid out left to right in three zones
        # (delivery-dashboard board-tui spec).
        with Horizontal(id="header-bar"):
            # Brand block: the ☕ mark, then an accent `shipd` beside a muted
            # `delivery board`.
            yield Static(
                "☕ [$accent bold]shipd[/] [$fg-muted]delivery board[/]",
                id="brand")
            # The centered live-search cluster re-homes the search widgets from
            # the removed controls strip unchanged — ids and handlers intact —
            # so the board-search behavior carries over (delivery-dashboard
            # board-search spec).
            with Horizontal(id="search-cluster"):
                yield SearchInput(placeholder="search", id="board-search-input")
                yield Button("✕", id="board-search-clear",
                            classes="compact-button")
                yield Static("", id="board-search-count")
            # The segmented grouping control: one compact button per mode, the
            # active mode carrying `mode-active` (delivery-dashboard
            # board-epic-grouping spec). Each button carries `group_mode_value`
            # so `on_button_pressed` routes it to `_set_group_mode`.
            with Horizontal(id="group-mode"):
                for mode in GROUP_MODES:
                    classes = "mode-button"
                    if mode == self.group_mode:
                        classes += " mode-active"
                    button = Button(mode, id="group-mode-%s" % mode,
                                    classes=classes)
                    button.group_mode_value = mode
                    yield button
            # The autopilot indicator (delivery-dashboard board-tui spec),
            # repainted each refresh from the pure `autopilot_live` predicate.
            yield Static("", id="autopilot-indicator")
            # The live board-throughput chart (board-throughput-chart); clicking
            # it opens the config dialog.
            yield HeaderChart()
        # The Shipd filter strip (delivery-dashboard board-filter-strip spec)
        # between the header bar and the lanes: full-board totals, the active
        # filter chips plus the `+ filter` control, and the read-only
        # shipped-this-week / synced-ago stats. The stat labels start blank and
        # the totals are painted by the first `refresh_board`; the chip row
        # holds only the add control until a chip is applied.
        with Horizontal(id="filter-strip"):
            yield Static("", id="board-totals")
            with Horizontal(id="filter-chips"):
                yield Button("+ filter", id="filter-add",
                             classes="filter-chip")
            yield Static("", id="board-shipped")
            yield Static("", id="board-synced")
        with Horizontal(id="body"):
            for lane in LANES:
                yield Lane(lane, id="lane-%s" % lane)
        yield Footer()

    def get_system_commands(self, screen):
        """Populate the ``ctrl+p`` command palette with the board's own
        commands, replacing textual's stock system commands (no ``super()``
        call, so Theme/Keys/Screenshot never appear — the epic registers one
        theme). On the base board screen (``screen_stack[0]``) yield the
        grouping command, the clear-search command while a query is active,
        the clear-filters command while chips are active, the delivery-metrics
        command, then quit; from a modal screen — whose widgets the
        grouping/clear callbacks cannot reach — yield only quit."""
        if screen is self.screen_stack[0]:
            yield SystemCommand(
                "Cycle grouping",
                "Cycle the lanes' grouping: epic → initiative → none",
                self.action_cycle_grouping)
            if self.search_query:
                yield SystemCommand(
                    "Clear search",
                    "Clear the live search and restore the full board",
                    self._clear_search)
            if self.filters:
                yield SystemCommand(
                    "Clear filters",
                    "Remove every filter chip and restore the full board",
                    self._clear_filters)
            yield SystemCommand(
                "Delivery metrics",
                "Open the delivery-metrics screen",
                self.action_show_metrics)
        yield SystemCommand("Quit", "Quit the delivery board",
                            self.action_quit)

    async def action_cycle_grouping(self) -> None:
        """Advance the grouping mode cyclically — ``epic`` → ``initiative`` →
        ``none`` → ``epic`` — the footer-bound "g" key and the palette's
        grouping command both run this (delivery-dashboard board-epic-grouping
        / board-command-palette specs)."""
        idx = GROUP_MODES.index(self.group_mode)
        await self._set_group_mode(GROUP_MODES[(idx + 1) % len(GROUP_MODES)])

    def action_show_metrics(self) -> None:
        """Open the delivery-metrics screen — the footer-bound ``m`` key and
        the "Delivery metrics" palette command both route here. Inert while
        any modal is already open (``screen_stack`` deeper than the base
        board), so ``m`` from a modal cannot stack screens
        (board-metrics-view spec)."""
        if len(self.screen_stack) == 1:
            self.push_screen(MetricsScreen(self.root))

    def action_add_filter(self) -> None:
        """Open the filter picker — the footer-bound ``f`` key and the strip's
        ``+ filter`` control both route here. Inert while any modal is already
        open (``screen_stack`` deeper than the base board), mirroring
        :meth:`action_show_metrics`, so ``f`` from a modal cannot stack screens
        (board-filter-strip spec)."""
        if len(self.screen_stack) == 1:
            self.push_screen(
                FilterPickerScreen(_filter_options(self.board, self.filters)))

    async def apply_filter(self, kind, value) -> None:
        """Add a ``(kind, value)`` filter chip and repaint (board-filter-strip
        spec): append it (a no-op when already active), remount the
        ``#filter-chips`` row so its removable chip button appears, and repaint
        the lanes — the chips fold into :func:`_lane_signature`, so the narrowed
        board repaints. The picker calls this on selection."""
        if (kind, value) in self.filters:
            return
        self.filters.append((kind, value))
        await self._remount_chips()
        await self._render_lanes()

    async def _remove_filter(self, kind, value) -> None:
        """Remove an active ``(kind, value)`` chip and repaint — a chip button's
        click routes here (board-filter-strip spec). Remounts the chip row so
        the chip's button leaves and repaints the lanes so its excluded members
        remount."""
        if (kind, value) not in self.filters:
            return
        self.filters.remove((kind, value))
        await self._remount_chips()
        await self._render_lanes()

    async def _clear_filters(self) -> None:
        """Remove every filter chip and restore the full board (delivery-
        dashboard board-command-palette spec): empty the filter list, remount
        the now-bare ``#filter-chips`` row, and repaint the lanes. The palette's
        "Clear filters" command routes here, mirroring :meth:`_clear_search`."""
        self.filters = []
        await self._remount_chips()
        await self._render_lanes()

    async def _remount_chips(self) -> None:
        """Rebuild the ``#filter-chips`` row from ``self.filters``: one
        removable chip button per active ``(kind, value)`` (each carrying its
        ``chip_kind``/``chip_value`` for routing, label ``"<kind>:<value> ✕"``)
        ahead of the ``+ filter`` add control. Queried empty-safely so a call
        before the strip mounts (or during teardown) is a no-op. Chips are
        rebuilt only on a filter change, never per refresh tick."""
        for row in self.query("#filter-chips"):
            await row.remove_children()
            chips = []
            for kind, value in self.filters:
                button = Button("%s:%s ✕" % (kind, value),
                                classes="filter-chip")
                button.chip_kind = kind
                button.chip_value = value
                chips.append(button)
            chips.append(Button("+ filter", id="filter-add",
                                classes="filter-chip"))
            await row.mount(*chips)

    async def _set_group_mode(self, mode) -> None:
        """Set the grouping ``mode``, move the segmented control's
        ``mode-active`` highlight to the matching mode button, and repaint the
        lanes — ``group_mode`` folds into :func:`_lane_signature`, so every
        lane's signature now differs from its last-rendered one and repaints.
        The mode buttons are queried empty-safely (the match-count pattern), so
        this is a no-op on the buttons before the header bar mounts them."""
        self.group_mode = mode
        for button in self.query(".mode-button"):
            button.set_class(
                getattr(button, "group_mode_value", None) == mode,
                "mode-active")
        await self._render_lanes()

    def action_focus_search(self) -> None:
        """Focus the header-bar search input (the ``/`` binding) — while it
        holds focus the card/app keys don't fire (standard ``Input`` capture)."""
        self.query_one("#board-search-input", SearchInput).focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "board-search-input":
            return
        # The query folds into `_lane_signature`, so this repaint always
        # re-filters and re-highlights every lane (delivery-dashboard
        # board-search spec).
        self.search_query = event.value
        await self._render_lanes()

    async def _clear_search(self) -> None:
        """Clear the active query and restore the full board (delivery-dashboard
        board-search spec): empty the input's value and repaint, then refocus
        the first :class:`TaskCard` when one exists so arrow-key navigation
        resumes. Shared by the ``✕`` control and the input's ``escape``
        binding."""
        self.search_query = ""
        self.query_one("#board-search-input", SearchInput).value = ""
        await self._render_lanes()
        cards = list(self.query(TaskCard))
        if cards:
            cards[0].focus()

    async def on_mount(self):
        await self.refresh_board()
        # Focus the first card so the board's app-level keys (`g`/`q`/`/`/the
        # arrows) fire on start rather than being captured by the header bar's
        # search input, which would otherwise auto-focus as the first focusable
        # widget (mirrors `_clear_search`'s refocus).
        cards = list(self.query(TaskCard))
        if cards:
            cards[0].focus()
        else:
            # An empty board mounts no card to focus; blur the auto-focused
            # search input so the app-level keys (`g`/`q`/`/`) still fire.
            self.screen.set_focus(None)
        # Live auto-refresh: re-aggregate and repaint every ``interval``
        # seconds so a live run's transitions appear without user input.
        self.set_interval(self.interval, self.refresh_board)

    async def refresh_board(self):
        """Re-run ``board_fn`` and repaint the lanes from the fresh board —
        the seam the live-refresh timer and tests both call. Also repaints the
        header bar's activity indicator from the pure :func:`indicator_marker`
        /:func:`activity_counts` predicates (delivery-dashboard board-tui
        spec) and the filter strip's
        full-board totals plus the read-only shipped-this-week / synced-ago
        stats (board-filter-strip spec)."""
        self.board = self._board_fn()
        # The activity indicator by precedence autopilot > building > idle
        # (delivery-dashboard board-tui spec): a theme-success `●` + `autopilot
        # on`/`autopilot (N)` while a run is live, else a building-lane `●` +
        # `building`/`building (N)` while an interactive build is live, else a
        # subtle-tier idle marker. Queried empty-safely (the match-count
        # pattern) so an interval-timer refresh during teardown, after the
        # indicator has been unmounted, never raises.
        marker = indicator_marker(self.board)
        for indicator in self.query("#autopilot-indicator"):
            indicator.update(marker)
        # The filter strip stats (board-filter-strip spec): the full-board
        # totals, `▲ N shipped this week`, and the synced-ago age. `_last_sync`
        # is stamped now so the synced label ages from this refresh;
        # `collect_ship_events` is one jsonl read + one listdir (cheap at the
        # tick) and never raises. All three labels are queried empty-safely (the
        # autopilot-indicator pattern) so a teardown-time tick never raises.
        self._last_sync = time.time()
        totals_text = _board_totals_text(self.board)
        shipped = shipped_this_week(mtr.collect_ship_events(self.root))
        shipped_text = "▲ %d shipped this week" % shipped
        synced_text = _sync_label(self._last_sync)
        for label in self.query("#board-totals"):
            label.update(totals_text)
        for label in self.query("#board-shipped"):
            label.update(shipped_text)
        for label in self.query("#board-synced"):
            label.update(synced_text)
        await self._render_lanes()

    def _filtered_lane_contents(self):
        """:func:`_lane_contents` narrowed to the members kept by both the
        active search query (delivery-dashboard board-search spec) and the
        active filter chips (board-filter-strip spec): each card spec is tested
        with :func:`_search_matches` **and** :func:`_filter_matches`, its epic's
        initiative resolved via :func:`_find_epic`. An empty query and empty
        chips keep every member."""
        raw = _lane_contents(self.board)
        contents = {}
        for lane_name in LANES:
            kept = []
            for spec in raw[lane_name]:
                epic_slug, _status, member, _entry = spec
                epic = _find_epic(self.board, epic_slug)
                initiative = epic.get("initiative") if epic else None
                if (_search_matches(self.search_query, epic_slug, initiative,
                                    member["slug"])
                        and _filter_matches(self.filters, epic_slug,
                                            initiative, member)):
                    kept.append(spec)
            contents[lane_name] = kept
        return contents

    async def _render_lanes(self):
        """Diff-aware repaint: build the fresh per-lane content (narrowed by the
        active search query), and — inside one ``batch_update`` — remove-
        children-and-remount only the lanes whose signature changed since the
        last render, updating the stored signature as each is rebuilt. An
        unchanged lane is left exactly as it was (no teardown, no flash, any
        collapsed epic group stays collapsed)."""
        contents = self._filtered_lane_contents()
        # The match-count label reports matching members across all lanes while
        # a query is active, and is blank otherwise (delivery-dashboard
        # board-search spec). Queried empty-safely — an interval-timer refresh
        # can fire during app teardown, after the label has been unmounted, so
        # this must not raise (the per-lane loop below likewise no-ops then).
        if self.search_query.strip():
            total = sum(len(contents[name]) for name in LANES)
            count_text = "1 match" if total == 1 else "%d matches" % total
        else:
            count_text = ""
        for count_label in self.query("#board-search-count"):
            count_label.update(count_text)
        # Each epic's initiative identity folds into the lane signatures while
        # a grouping mode is active — the group headers render it, so an
        # initiative re-tag or status change must repaint (delivery-dashboard
        # board-tui spec: repaint the lanes whose board-derived content
        # changed).
        initiative_by_epic = {
            epic.get("slug"): (
                (epic["initiative"].get("slug"),
                 epic["initiative"].get("status"))
                if epic.get("initiative") else None)
            for epic in self.board.get("epics", [])}
        with self.batch_update():
            for lane_name in LANES:
                sig = _lane_signature(contents[lane_name], self.group_mode,
                                      self.search_query, initiative_by_epic,
                                      tuple(self.filters))
                if sig == self._lane_sigs.get(lane_name):
                    continue
                self._lane_sigs[lane_name] = sig
                lane = self.query_one("#lane-%s" % lane_name, Lane)
                # Clear only the repaintable content — everything
                # `_render_lanes`/`_mount_epic_groups`/`_mount_initiative_groups`
                # mounts carries the `lane-item` class — so the docked
                # `.lane-header` band survives every repaint (delivery-dashboard
                # board-tui spec).
                await lane.remove_children(".lane-item")
                if not contents[lane_name]:
                    # An empty lane — no board content, or the query filtered
                    # every member out — shows its per-lane empty-state text
                    # (delivery-dashboard board-tui spec). The empty-lane branch
                    # stays first, ahead of the mode dispatch.
                    await lane.mount(
                        Static(LANE_EMPTY_TEXTS[lane_name],
                               classes="lane-empty lane-item"))
                elif self.group_mode == "epic":
                    await self._mount_epic_groups(
                        lane, lane_name, contents[lane_name])
                elif self.group_mode == "initiative":
                    await self._mount_initiative_groups(
                        lane, lane_name, contents[lane_name])
                else:
                    for epic_slug, status, member, entry in contents[lane_name]:
                        await lane.mount(
                            TaskCard(epic_slug, member, entry, status,
                                     search_query=self.search_query,
                                     classes="lane-item"))

    async def _mount_epic_groups(self, lane, lane_name, cards):
        """Mount ``cards`` grouped under one collapsible per-epic header —
        an :class:`EpicCollapsible` whose title itself routes the click (the
        arrow cell toggles, anywhere else opens the epic-detail modal, no
        separate menu control) — on the theme's flat panel surface separated
        by a theme-variable border divider line — no per-epic-status colour —
        ``cards`` runs are contiguous per epic (see :func:`_lane_contents`),
        so a single pass folding consecutive same-epic specs into one group
        suffices. Used for every lane when ``group_by_epic`` is on
        (generalises the previous shipped-lane-only grouping to the whole
        board)."""
        group_slug = None
        group_status = None
        group_cards = []

        async def _flush():
            if group_cards:
                # The pseudo-epic `standalone` run (changes planned outside any
                # epic) has no epic dict, no menu control — epic actions are
                # epic-scoped — and a bare `standalone` title (delivery-dashboard
                # board-standalone-changes spec).
                is_standalone = group_slug == "standalone"
                epic = _find_epic(self.board, group_slug)
                initiative = epic.get("initiative") if epic else None
                # The per-lane card count rides the title as a muted ` (N)`
                # suffix (delivery-dashboard board-epic-grouping spec) — the
                # standalone group carries the bare `standalone` label plus the
                # same suffix, no separate count element.
                count = len(group_cards)
                # An epic hosted under a worktree carries the `[worktree]`
                # marker its board row does (delivery-dashboard
                # board-aggregation).
                location = epic.get("location") if epic else None
                title = ("standalone" + _count_suffix(count)) if is_standalone \
                    else epic_group_title(
                        group_slug, group_status, initiative,
                        stalled=epic_stalled(epic) if epic else False,
                        count=count,
                        worktree=bool(location
                                      and location != self.board.get("root")))
                # An *epic* group's header title itself splits the click
                # (delivery-dashboard board-epic-grouping spec): the arrow
                # cell toggles, anywhere else opens the epic-detail modal —
                # so only epic groups (not the epic-less standalone
                # pseudo-group) get the click-routing `EpicCollapsibleTitle`
                # via `EpicCollapsible`; standalone keeps the stock
                # `Collapsible` since epic actions are epic-scoped and it has
                # no epic to open.
                group_id = "epic-group-%s-%s" % (lane_name, group_slug)
                if is_standalone:
                    collapsible = Collapsible(
                        *group_cards, title=title, collapsed=False,
                        id=group_id, classes="epic-group")
                else:
                    collapsible = EpicCollapsible(
                        *group_cards, title=title, collapsed=False,
                        id=group_id, classes="epic-group",
                        epic_slug=group_slug)
                await lane.mount(EpicGroupRow(
                    collapsible, classes="epic-group-row lane-item"))

        for epic_slug, status, member, entry in cards:
            if epic_slug != group_slug:
                await _flush()
                group_slug, group_status, group_cards = epic_slug, status, []
            group_cards.append(TaskCard(epic_slug, member, entry, status,
                                        search_query=self.search_query))
        await _flush()

    async def _mount_initiative_groups(self, lane, lane_name, cards):
        """Mount ``cards`` grouped under one collapsible per-initiative header
        (delivery-dashboard board-epic-grouping spec), fed by the board's
        existing initiative ``groups`` buckets. Walks ``self.board["groups"]``
        in order; for each group it keeps that group's epics' card specs from
        the lane's (already search-filtered) ``cards``, preserving lane order,
        and mounts one plain :class:`Collapsible` — no menu control, since epic
        actions are epic-scoped — titled by :func:`initiative_group_title`
        (``workspace`` for the no-initiative bucket). A group with no kept cards
        mounts nothing, satisfying the fully-filtered-group scenario. Standalone
        cards (pseudo-epic ``standalone``, in no initiative bucket) mount under
        their own controls-free ``standalone`` group after the initiative groups
        (delivery-dashboard board-standalone-changes spec). Mirrors
        :meth:`_mount_epic_groups`' ``epic-group lane-item`` classing so the
        repaint's ``remove_children(".lane-item")`` clears it while the docked
        ``.lane-header`` band survives."""
        for group in self.board.get("groups", []):
            initiative = group.get("initiative")
            group_slugs = {e.get("slug") for e in group.get("epics", [])}
            group_cards = [
                TaskCard(epic_slug, member, entry, status,
                         search_query=self.search_query)
                for epic_slug, status, member, entry in cards
                if epic_slug in group_slugs]
            if not group_cards:
                continue
            slug = initiative.get("slug") if initiative else "workspace"
            # The per-lane card count rides the title as a muted ` (N)` suffix,
            # identical to epic mode (delivery-dashboard board-epic-grouping
            # spec).
            await lane.mount(Collapsible(
                *group_cards,
                title=initiative_group_title(initiative)
                + _count_suffix(len(group_cards)),
                collapsed=False,
                id="init-group-%s-%s" % (lane_name, slug),
                classes="epic-group lane-item"))
        standalone_cards = [
            TaskCard(epic_slug, member, entry, status,
                     search_query=self.search_query)
            for epic_slug, status, member, entry in cards
            if epic_slug == "standalone"]
        if standalone_cards:
            await lane.mount(Collapsible(
                *standalone_cards,
                title="standalone" + _count_suffix(len(standalone_cards)),
                collapsed=False,
                id="init-group-%s-standalone" % lane_name,
                classes="epic-group lane-item"))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Route a click on the search ✕ control (clearing the query, checked
        first), a segmented grouping mode button, the filter strip's
        ``+ filter``/chip controls — distinguished by which marker attribute
        the button carries, checked in that order so they never collide
        (delivery-dashboard board-epic-grouping / board-filter-strip specs).
        Opening the epic-detail modal from a header click no longer routes
        through here — it is a :class:`EpicCollapsibleTitle.OpenEpic` message,
        handled by :meth:`_open_epic_detail` below, not a button press."""
        if event.button.id == "board-search-clear":
            await self._clear_search()
            return
        # The segmented grouping control: a `group_mode_value`-carrying button
        # selects its mode directly (delivery-dashboard board-epic-grouping
        # spec).
        mode = getattr(event.button, "group_mode_value", None)
        if mode is not None:
            await self._set_group_mode(mode)
            return
        # The filter strip's `+ filter` control opens the picker; a chip
        # button (carrying `chip_kind`) removes itself (delivery-dashboard
        # board-filter-strip spec).
        if event.button.id == "filter-add":
            self.action_add_filter()
            return
        chip_kind = getattr(event.button, "chip_kind", None)
        if chip_kind is not None:
            await self._remove_filter(chip_kind, event.button.chip_value)

    @on(EpicCollapsibleTitle.OpenEpic)
    def _open_epic_detail(self, event: EpicCollapsibleTitle.OpenEpic) -> None:
        """Push the epic-detail modal for the header title clicked off the
        collapse arrow (delivery-dashboard board-epic-grouping spec) — the
        header itself opens the epic now; there is no separate menu control
        to route through."""
        self.push_screen(EpicDetailScreen(event.epic_slug))

    def move_card_focus(self, card, direction):
        """Move focus from ``card`` one step ``"up"``/``"down"`` within its
        lane or ``"left"``/``"right"`` to the nearest non-empty neighbouring
        lane (clamping the vertical index) — the arrow-key spatial focus a
        focused :class:`TaskCard` delegates to."""
        lane = card.parent
        cards = list(lane.query(TaskCard))
        try:
            idx = cards.index(card)
        except ValueError:
            return
        if direction == "up" and idx > 0:
            cards[idx - 1].focus()
            return
        if direction == "down" and idx < len(cards) - 1:
            cards[idx + 1].focus()
            return
        if direction in ("left", "right"):
            lanes = [self.query_one("#lane-%s" % name, Lane)
                     for name in LANES]
            lane_idx = lanes.index(lane)
            step = -1 if direction == "left" else 1
            ni = lane_idx + step
            while 0 <= ni < len(lanes):
                target_cards = list(lanes[ni].query(TaskCard))
                if target_cards:
                    target_cards[min(idx, len(target_cards) - 1)].focus()
                    return
                ni += step

    def dispatch_card_action(self, card, action):
        """Resolve ``action`` for ``card``'s member against its eligible
        ``actions`` and spawn the launch — the wiring a focused
        :class:`TaskCard`'s RUN/PLAN/OPEN key runs, through the unchanged
        pure launch builders. A ``None`` launch (e.g. ``open`` with no
        session id) or an action the member isn't eligible for is a no-op."""
        if action not in (card.member.get("actions") or []):
            return
        builder = _LAUNCH_BUILDERS.get(action)
        if builder is None:
            return
        launch = builder(self.root, card.epic_slug, card.member)
        if launch is not None:
            self._spawn_launch(launch)

    def dispatch_epic_run(self, epic_slug):
        """Spawn the epic-level ``run`` — the full autopilot over every
        unplanned/ready member of ``epic_slug``."""
        self._spawn_launch(build_epic_run_launch(self.root, epic_slug))

    def _spawn_launch(self, launch):
        """Spawn a resolved launch spec: a ``detach`` run in the background
        (the board keeps rendering, tailing its heartbeat), a ``tmux``
        window returning at once, or a ``suspend`` launch that leaves the
        terminal via ``App.suspend()``, runs to completion, and restores the
        board on return."""
        mode = launch["mode"]
        argv = launch["argv"]
        cwd = launch.get("cwd")
        if mode == "detach":
            try:
                subprocess.Popen(
                    argv, cwd=cwd, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True)
            except OSError:
                pass
        elif mode == "tmux":
            try:
                subprocess.run(argv, cwd=cwd, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            except OSError:
                pass
        elif mode == "suspend":
            with self.suspend():
                try:
                    subprocess.run(argv, cwd=cwd)
                except OSError:
                    pass


def _cmd_tui(args):
    app = BoardApp(os.path.abspath(args.root), epic=args.epic,
                  interval=args.interval)
    app.run()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="The autonomous-delivery board and its run heartbeat.")
    sub = parser.add_subparsers(dest="verb", required=True)

    p_board = sub.add_parser(
        "board", help="aggregate and print the delivery board")
    p_board.add_argument("--root", default=os.getcwd(),
                         help="repository root (default: cwd)")
    p_board.add_argument("--epic", default=None,
                         help="scope the board to one epic slug")
    p_board.add_argument("--json", action="store_true",
                         help="emit the full board object as JSON")
    p_board.set_defaults(func=_cmd_board)

    p_tui = sub.add_parser(
        "tui", help="render the board full-screen, redrawing on an interval")
    p_tui.add_argument("--root", default=os.getcwd(),
                       help="repository root (default: cwd)")
    p_tui.add_argument("--epic", default=None,
                       help="scope the board to one epic slug")
    p_tui.add_argument("--interval", type=float, default=2.0,
                       help="seconds between redraws (default: 2)")
    p_tui.set_defaults(func=_cmd_tui)

    args = parser.parse_args(argv)
    # An unknown --epic slug surfaces from build_board as a ValueError; turn it
    # into a one-line stderr message + exit 1 for every board-backed verb.
    try:
        return args.func(args)
    except ValueError as exc:
        cc.err(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
