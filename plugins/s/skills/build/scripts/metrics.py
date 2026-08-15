#!/usr/bin/env python3
"""metrics.py — the delivery-metrics derivation engine (stdlib only, no network).

Computes the delivery metrics every later surface consumes — throughput, change
lead time, cycle time with 50/85/95 percentiles, WIP and work-item aging,
outcome distribution, and cost — **purely from the event sources the pipeline
already emits**: the config-resolved build log (``builds.jsonl``), the dated
``completed/<date>-<slug>/`` archives, the ``.shipd/autopilot/<epic>-report.json``
run reports, the epic tables, and git merge/first-commit timestamps.

The derivation API is a **Python API, not a CLI** — its single entry point,
:func:`derive`, returns one JSON-serializable dict; nothing in the derivation
path prints or writes. The module's only user-facing surface is the thin
``summary`` verb (``python3 metrics.py summary [--root <root>] [--json]``), which
derives the metrics for a root and prints a human-readable, team-level delivery
summary composed by the pure :func:`render_summary_lines` renderer (or the raw
derive dict under ``--json``); importing the module never executes it. Every
derivation function
is pure and deterministic: ``root``, ``config`` (a build-config override so no
test touches ``~``), and ``now`` are injectable, timestamps are UTC, and a
malformed build-log line is skipped rather than fatal. No metric is ever
attributed to an individual (the SPACE guardrail).

It is **dependency-free** — it imports only the stdlib plus the sibling
stdlib-only engine modules (:mod:`spec_common`, :mod:`spec_status`,
:mod:`heartbeat`); it never imports ``textual`` and never imports ``dashboard``
(the WIP walk goes through the same ``spec_common``/``spec_status`` path the
dashboard's data layer uses, directly). This keeps it — and its tests in the
dependency-free ``tests/`` suite — runnable under a plain ``python3`` where
``textual`` is absent.
"""

import argparse
import datetime as _dt
import glob
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402
import spec_status as ss  # noqa: E402

UTC = _dt.timezone.utc

# Default build-log directory (mirrors build_report.DEFAULT_BUILD_CONFIG so the
# two stay in lockstep without importing build_report — keeps the engine to the
# sc/ss/heartbeat import allowlist).
DEFAULT_LOG_DIR = "~/.shipd/builds"

# The standard delivery percentiles (Vacanti's 50/85/95 scatterplot lines).
DEFAULT_PERCENTILES = (50, 85, 95)

# The lifecycle states that count as in-flight WIP: a member that has *entered*
# the process (has a plan) but not *exited* it. ``unplanned`` has not entered;
# ``archived`` has shipped/exited. Everything between (draft/ready/active/
# complete/verified/rejected) is work-in-progress.
_WIP_EXCLUDED_STATES = frozenset({"unplanned", "archived"})

_ARCHIVE_DIR_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")


# ---------------------------------------------------------------------------
# Pure derivation core: percentiles, DORA band, result-shape builders
# ---------------------------------------------------------------------------

def percentiles(values, ps=DEFAULT_PERCENTILES):
    """Nearest-rank percentiles of ``values`` (unsorted input is sorted first).

    Returns ``{"p<n>": value}`` for each ``n`` in ``ps``. The nearest-rank
    method (no interpolation) takes, for a sample of ``k`` sorted values, the
    ``ceil(n/100 * k)``-th value (1-indexed) — outlier-robust, unlike a mean.
    An empty sample yields ``None`` for every percentile.
    """
    ordered = sorted(values)
    k = len(ordered)
    out = {}
    for n in ps:
        key = "p%d" % n
        if k == 0:
            out[key] = None
            continue
        rank = math.ceil(n / 100.0 * k)
        rank = min(max(rank, 1), k)
        out[key] = ordered[rank - 1]
    return out


def stat_block(values, ps=DEFAULT_PERCENTILES):
    """A percentile summary of ``values`` — ``{"median", "p50", "p85", "p95",
    "n"}`` — carrying the sample count and **never a bare mean** (outliers
    distort the mean; the median/percentiles are the reported aggregate, per the
    cited DORA/flow canon). ``median`` is the classic middle value; the ``p*``
    keys are nearest-rank (see :func:`percentiles`). An empty sample reports
    ``n=0`` and ``None`` for every statistic.
    """
    seq = list(values)
    block = {"n": len(seq)}
    block.update(percentiles(seq, ps))
    block["median"] = statistics.median(seq) if seq else None
    return block


def dora_band(weekly_deploy_days):
    """Map a series of per-week deployment-day counts to the DORA
    deployment-frequency band (Google Four Keys recipe).

    ``weekly_deploy_days`` is one count per week over the observation window (a
    *deployment-day* is a day with at least one ship — four ships in one day
    still count once). The band follows the median weekly deployment-days:
    ``daily`` at a median ≥ 3, ``weekly`` at a median ≥ 1; below that the
    average monthly deployment-day rate decides ``monthly`` (≥ 1/month) vs
    ``yearly``. An empty series is ``yearly``.
    """
    weeks = list(weekly_deploy_days)
    if not weeks:
        return "yearly"
    median = statistics.median(weeks)
    if median >= 3:
        return "daily"
    if median >= 1:
        return "weekly"
    # Median < 1: distinguish an occasional cadence from a near-dormant one by
    # the average deployment-days per month (~52/12 weeks per month).
    per_month = (sum(weeks) / len(weeks)) * (52.0 / 12.0)
    if per_month >= 1:
        return "monthly"
    return "yearly"


# Lead-time DORA-tier boundaries, in seconds: the published DORA/Accelerate
# performance clusters — elite ships a change in under a day, high under a week,
# medium under a month, low beyond. A boundary value lands in the lower tier
# (the comparisons are strict ``<``), so exactly one day is ``high``.
_LEAD_TIER_ELITE_MAX = 86400        # 1 day
_LEAD_TIER_HIGH_MAX = 604800        # 7 days
_LEAD_TIER_MEDIUM_MAX = 2592000     # 30 days


def lead_time_dora_band(median_seconds):
    """Map a change-lead-time median (seconds) onto the DORA performance tier:
    ``elite`` below one day, ``high`` below seven days, ``medium`` below thirty
    days, else ``low``.

    The thresholds are the published DORA/Accelerate performance clusters (the
    research report gives only the deployment-frequency recipe, so the lead-time
    tier boundaries are the standard clusters, documented here). The comparisons
    are strict, so a boundary value lands in the lower tier — exactly one day is
    ``high``, not ``elite``. ``None`` in → ``None`` out (no sample, no tier).
    """
    if median_seconds is None:
        return None
    if median_seconds < _LEAD_TIER_ELITE_MAX:
        return "elite"
    if median_seconds < _LEAD_TIER_HIGH_MAX:
        return "high"
    if median_seconds < _LEAD_TIER_MEDIUM_MAX:
        return "medium"
    return "low"


def throughput_trend(counts):
    """The throughput trend from a series of per-week ship counts: ``"up"`` /
    ``"down"`` / ``"flat"`` comparing the four most recent weeks' sum against the
    preceding four, or ``None`` under five weeks of history.

    Fewer than five weekly observations is too little history for a
    4-vs-preceding-4 comparison, so the trend is ``None`` (the summary renderer
    omits the segment). At five or more weeks the last four weeks' sum is
    compared against the immediately preceding window: greater is ``"up"``, less
    is ``"down"``, equal is ``"flat"``.
    """
    if len(counts) < 5:
        return None
    recent = sum(counts[-4:])
    preceding = sum(counts[-8:-4])
    if recent > preceding:
        return "up"
    if recent < preceding:
        return "down"
    return "flat"


# ---------------------------------------------------------------------------
# Timestamp + config helpers
# ---------------------------------------------------------------------------

def _parse_ts(value):
    """Parse an ISO-8601 timestamp (``Z`` accepted) into an aware UTC
    ``datetime``, or ``None`` on any problem. A naive timestamp is assumed UTC.
    """
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        parsed = _dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def resolve_log_dir(root, config=None):
    """Resolve the build-log directory (home-expanded).

    An explicit ``config`` dict wins: its ``log_dir`` is used verbatim (the test
    seam that keeps every test off of ``~``). Otherwise the value is read from
    ``root``'s layered configuration's ``build.log_dir`` key, defaulting to
    ``~/.shipd/builds`` — the same resolution ``build_report.py`` performs, kept
    local here so the engine imports only sc/ss/heartbeat.
    """
    log_dir = None
    if isinstance(config, dict):
        log_dir = config.get("log_dir")
    if not log_dir:
        try:
            resolved, _prov = sc.resolve_config(os.path.abspath(root))
        except sc.ConfigError:
            resolved = {}
        build = resolved.get("build")
        if isinstance(build, dict):
            log_dir = build.get("log_dir")
    return os.path.expanduser(log_dir or DEFAULT_LOG_DIR)


# ---------------------------------------------------------------------------
# Event collection: ship events (log ∪ archives), outcomes, WIP
# ---------------------------------------------------------------------------

def _ship_event_from_log(record):
    """Build a ship-event dict from one build-log entry, or ``None`` when it
    carries no usable change slug / timestamp."""
    slug = record.get("change")
    ship_ts = _parse_ts(record.get("timestamp"))
    if not slug or ship_ts is None:
        return None
    tasks = record.get("tasks")
    done = tasks.get("done") if isinstance(tasks, dict) else None
    tokens = record.get("tokens")
    totals = tokens.get("totals") if isinstance(tokens, dict) else None
    tokens_output = totals.get("output") if isinstance(totals, dict) else None
    time_block = record.get("time")
    seconds = (time_block.get("total_seconds")
               if isinstance(time_block, dict) else None)
    return {
        "slug": slug,
        "ship_ts": ship_ts,
        "tasks": done,
        "status": record.get("status"),
        "tokens_output": tokens_output,
        "seconds": seconds,
        "source": "log",
    }


def collect_ship_events(root, config=None):
    """Collect per-change ship events, unioning the build log with the dated
    ``completed/`` archives.

    The build log (``<log_dir>/builds.jsonl``) is read line by line; a malformed
    line is skipped, never fatal. Each entry becomes ``{slug, ship_ts (aware UTC
    datetime), tasks, status, tokens_output, seconds, source}``. Then every
    ``completed/<YYYY-MM-DD>-<slug>/`` archive contributes a **ship-date
    fallback** (midnight UTC of the dir's date prefix) for any change the log
    missed — so a change absent from the log still counts, **the log entry
    winning** when both exist. Returns the events as a list sorted by slug.
    """
    by_slug = {}
    log_path = os.path.join(resolve_log_dir(root, config), "builds.jsonl")
    try:
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(record, dict):
                    continue
                event = _ship_event_from_log(record)
                if event is not None:
                    # Last log entry for a slug wins over an earlier one.
                    by_slug[event["slug"]] = event
    except OSError:
        pass

    completed_dir = os.path.join(sc.specs_dir(root), "completed")
    try:
        names = sorted(os.listdir(completed_dir))
    except OSError:
        names = []
    for name in names:
        if not os.path.isdir(os.path.join(completed_dir, name)):
            continue
        m = _ARCHIVE_DIR_RE.match(name)
        if not m:
            continue
        year, month, day, slug = m.groups()
        if slug in by_slug:
            continue  # the log entry wins
        try:
            ship_ts = _dt.datetime(int(year), int(month), int(day), tzinfo=UTC)
        except ValueError:
            continue
        by_slug[slug] = {
            "slug": slug,
            "ship_ts": ship_ts,
            "tasks": None,
            "status": None,
            "tokens_output": None,
            "seconds": None,
            "source": "archive",
        }

    return [by_slug[slug] for slug in sorted(by_slug)]


_OUTCOME_BUCKETS = ("shipped", "rejected", "needs_human", "skipped")


def collect_outcomes(root):
    """Fold every ``.shipd/autopilot/*-report.json`` run report into the outcome
    distribution — the pre-merge rework proxy (a true DORA change-fail rate is
    the ``change-failure-signal`` member's seam).

    Returns ``{"counts": {bucket: n}, <bucket>: [member, ...]}`` for the four
    buckets ``shipped`` / ``rejected`` / ``needs_human`` / ``skipped``, in
    filename order. A torn or unreadable report is skipped, never fatal.
    """
    members = {bucket: [] for bucket in _OUTCOME_BUCKETS}
    autopilot_dir = os.path.join(sc.specs_dir(root), "autopilot")
    for path in sorted(glob.glob(os.path.join(autopilot_dir, "*-report.json"))):
        report = _read_json(path)
        if not isinstance(report, dict):
            continue
        for bucket in _OUTCOME_BUCKETS:
            entries = report.get(bucket)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and entry.get("member"):
                    members[bucket].append(entry["member"])
    result = {"counts": {b: len(members[b]) for b in _OUTCOME_BUCKETS}}
    result.update(members)
    return result


def _read_json(path):
    """Parse a JSON file, returning ``None`` when missing or unparseable — a
    torn or absent artifact never fails a collector."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _member_state_and_location(root, slug):
    """Return ``(state, location)`` for one epic stub member — the same
    worktree-aware resolution the dashboard's data layer performs, replicated
    here (never importing ``dashboard``): delegates to
    :func:`spec_status._member_state_with_root`, which probes the invocation
    ``root`` first, then each ``.worktrees/<name>`` directory under it in
    sorted name order, so a member parked in its worktree is still visible.
    ``location`` is the absolute directory hosting the change (``root`` or the
    hosting worktree).
    """
    state, hosting_root = ss._member_state_with_root(root, slug)
    return state, os.path.abspath(hosting_root)


def _member_age_days(location, slug, now):
    """Work-item age in days from the member's ``plan.md`` mtime at
    ``location``, or ``None`` when no such artifact exists — age is **never
    fabricated** when evidence is absent (delivery-metrics metrics-engine).
    """
    try:
        plan_path = os.path.join(sc.specs_dir(location), "planned", slug,
                                 "plan.md")
    except sc.ConfigError:
        return None
    try:
        mtime = os.path.getmtime(plan_path)
    except OSError:
        return None
    born = _dt.datetime.fromtimestamp(mtime, tz=UTC)
    return max(0.0, (now - born).total_seconds() / 86400.0)


def collect_wip(root, now):
    """Collect the live WIP snapshot from the epic tables.

    Walks every ``.shipd/epics/*/epic.md``'s ``## Changes`` stub table (via
    :func:`spec_common.parse_epic_changes`), resolves each member's
    worktree-aware lifecycle state, and keeps only the **in-flight** members —
    those that have entered the process (have a plan) but not exited it
    (``unplanned`` has not entered; ``archived`` has shipped). Each in-flight
    member yields ``{slug, state, age_days}`` where age is the plan.md mtime age
    (``None`` when no artifact evidence exists). A slug seen in more than one
    epic is counted once.

    Returns ``{"by_state": {state: count}, "items": [...], "aging": stat_block}``
    where ``aging`` summarizes the non-``None`` ages.
    """
    items = []
    seen = set()
    epics_dir = os.path.join(sc.specs_dir(root), "epics")
    try:
        epic_names = sorted(os.listdir(epics_dir))
    except OSError:
        epic_names = []
    for epic_name in epic_names:
        epic_path = os.path.join(epics_dir, epic_name, "epic.md")
        try:
            with open(epic_path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        _header, rows = sc.parse_epic_changes(text)
        for slug, _description, _ratings in rows:
            if not slug or slug in seen:
                continue
            seen.add(slug)
            state, location = _member_state_and_location(root, slug)
            if state in _WIP_EXCLUDED_STATES:
                continue
            items.append({
                "slug": slug,
                "state": state,
                "age_days": _member_age_days(location, slug, now),
            })

    by_state = {}
    for item in items:
        by_state[item["state"]] = by_state.get(item["state"], 0) + 1
    ages = [item["age_days"] for item in items if item["age_days"] is not None]
    return {"by_state": by_state, "items": items, "aging": stat_block(ages)}


# ---------------------------------------------------------------------------
# Flow time-series capture (delivery-metrics flow-timeseries): a full-band
# lifecycle snapshot recorded append-only to <log_dir>/flow.jsonl, the history a
# cumulative-flow diagram and work-item aging need. The capture API is the
# module's one *writing* surface (derive() never calls it).
# ---------------------------------------------------------------------------

# The env var that redirects (or, when empty, disables) flow recording — the
# test seam that keeps every suite off the real ~/.shipd/builds/.
FLOW_LOG_ENV = "AM_FLOW_LOG_DIR"

FLOW_LOG_FILE = "flow.jsonl"


def _resolve_project_root(root):
    """Resolve a linked git worktree ``root`` to its main checkout — a local
    mirror of ``build_report.resolve_project_root`` (stdlib only, no ``git``
    subprocess), kept here to preserve ``metrics.py``'s sc/ss/heartbeat import
    allowlist.

    A linked worktree's ``.git`` is a *file* whose first line reads
    ``gitdir: <main>/.git/worktrees/<name>``; when it has that shape the main
    checkout ``<main>`` is returned. On any other shape (a submodule's
    ``.git/modules/...``, an unreadable ``.git`` file, or a normal ``.git``
    directory) the absolute ``root`` is returned unchanged.
    """
    abs_dir = os.path.abspath(root)
    git_path = os.path.join(abs_dir, ".git")
    if not os.path.isfile(git_path):
        return abs_dir
    try:
        with open(git_path, encoding="utf-8") as fh:
            first = fh.readline().strip()
    except OSError:
        return abs_dir
    prefix = "gitdir:"
    if not first.startswith(prefix):
        return abs_dir
    gitdir = first[len(prefix):].strip()
    if not gitdir:
        return abs_dir
    if not os.path.isabs(gitdir):
        gitdir = os.path.join(abs_dir, gitdir)
    gitdir = os.path.normpath(gitdir)
    parent = os.path.dirname(gitdir)          # .../.git/worktrees
    grandparent = os.path.dirname(parent)     # .../.git
    if os.path.basename(parent) != "worktrees":
        return abs_dir
    if os.path.basename(grandparent) != ".git":
        return abs_dir
    return os.path.dirname(grandparent)       # .../<main>


def flow_snapshot(root):
    """The board's full-band lifecycle membership: ``{state: [slug, ...]}`` with
    every state's slug list sorted and deduplicated.

    Walks every ``.shipd/epics/*/epic.md``'s ``## Changes`` stub table (the same
    :func:`spec_common.parse_epic_changes` + :func:`_member_state_and_location`
    resolution :func:`collect_wip` uses) but keeps **every** band — including
    ``unplanned`` (the backlog band) and ``archived`` (the cumulative-done band)
    that :func:`collect_wip` excludes, since a cumulative-flow diagram needs
    them. A slug seen in more than one epic is attributed to its first-seen
    state and counted once; no member is attributed to an individual.
    """
    by_state = {}
    seen = set()
    epics_dir = os.path.join(sc.specs_dir(root), "epics")
    try:
        epic_names = sorted(os.listdir(epics_dir))
    except OSError:
        epic_names = []
    for epic_name in epic_names:
        epic_path = os.path.join(epics_dir, epic_name, "epic.md")
        try:
            with open(epic_path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        _header, rows = sc.parse_epic_changes(text)
        for slug, _description, _ratings in rows:
            if not slug or slug in seen:
                continue
            seen.add(slug)
            state, _location = _member_state_and_location(root, slug)
            by_state.setdefault(state, []).append(slug)
    return {state: sorted(slugs) for state, slugs in by_state.items()}


def resolve_flow_log_dir(root, config=None):
    """Resolve the flow-log directory, or ``None`` when recording is disabled.

    The ``AM_FLOW_LOG_DIR`` environment variable wins over all other resolution:
    a non-empty value is the directory (home-expanded); the **empty string**
    disables recording entirely (``None``). Absent the env var, resolution falls
    through to :func:`resolve_log_dir` (explicit ``config`` ``log_dir`` → layered
    ``build.log_dir`` → ``~/.shipd/builds``) — flow records live beside
    ``builds.jsonl``.
    """
    env = os.environ.get(FLOW_LOG_ENV)
    if env is not None:
        if env == "":
            return None
        return os.path.expanduser(env)
    return resolve_log_dir(root, config)


def _last_flow_record(path, root):
    """The last flow record for ``root`` in ``path``, or ``None`` — malformed
    lines skipped, a missing file → ``None``. Used for dedup."""
    last = None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if isinstance(record, dict) and record.get("root") == root:
                    last = record
    except OSError:
        return None
    return last


def record_flow(root, config=None, now=None):
    """Append a full-band lifecycle snapshot for ``root`` to
    ``<log_dir>/flow.jsonl`` — the append-only capture entry point.

    Resolves ``root`` to its main checkout (:func:`_resolve_project_root`, so a
    linked worktree records under the shared main path), takes a
    :func:`flow_snapshot` there, and appends one JSON line
    ``{"ts": <ISO-8601 UTC>, "root": <abs main path>, "states": {...}}``. When
    the same root's latest record already carries an equal ``states`` map the
    append is **skipped** — the series is a compact step function readers
    forward-fill. Returns the appended record, or ``None`` when the snapshot is
    unchanged or recording is disabled (empty ``AM_FLOW_LOG_DIR``). A capture
    failure raises; the lifecycle hooks that call it swallow the exception so a
    mutation is never blocked.
    """
    log_dir = resolve_flow_log_dir(root, config)
    if log_dir is None:
        return None
    main_root = _resolve_project_root(root)
    states = flow_snapshot(main_root)
    path = os.path.join(log_dir, FLOW_LOG_FILE)
    last = _last_flow_record(path, main_root)
    if last is not None and last.get("states") == states:
        return None
    record = {"ts": _as_utc(now).isoformat(), "root": main_root,
              "states": states}
    os.makedirs(log_dir, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def collect_flow(root, config=None):
    """Read the recorded flow time-series for ``root`` — the read-only reader
    counterpart to :func:`record_flow`.

    Filters ``<log_dir>/flow.jsonl`` to the resolved main-checkout root (so a
    worktree reads the same shared series it wrote), skips malformed lines
    (mirroring :func:`collect_ship_events`), and returns the records sorted by
    ``ts``. Each record carries its ``states`` slug map plus a derived
    ``by_state`` count map (``{state: len(slugs)}``). A missing file, a disabled
    env seam, or a resolution miss degrades to an empty list — never fatal.
    """
    log_dir = resolve_flow_log_dir(root, config)
    if log_dir is None:
        return []
    main_root = _resolve_project_root(root)
    path = os.path.join(log_dir, FLOW_LOG_FILE)
    records = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(record, dict):
                    continue
                if record.get("root") != main_root:
                    continue
                states = record.get("states")
                if not isinstance(states, dict):
                    states = {}
                records.append({
                    "ts": record.get("ts"),
                    "states": states,
                    # Count only list values: a corrupted record whose states
                    # map holds a non-sized value must be tolerated, never
                    # fatal (the "malformed lines skipped" clause).
                    "by_state": {state: len(slugs)
                                 for state, slugs in states.items()
                                 if isinstance(slugs, list)},
                })
    except OSError:
        return []
    # str-coerced key: a corrupted record with a non-string ts must not make
    # the sort raise on a mixed-type comparison (the never-fatal clause).
    records.sort(key=lambda r: str(r.get("ts") or ""))
    return records


# ---------------------------------------------------------------------------
# Git timestamps: change lead time (merge − first-commit)
# ---------------------------------------------------------------------------

# A record separator that cannot appear in a commit subject (%s is single-line),
# so the format fields split cleanly.
_GIT_SEP = "\x1f"


def _epoch_to_utc(epoch):
    """A UTC ``datetime`` from a git epoch string, or ``None`` on any problem."""
    try:
        return _dt.datetime.fromtimestamp(int(epoch), tz=UTC)
    except (ValueError, OverflowError, OSError):
        return None


def git_change_times(root, slug, base_ref=None):
    """Resolve ``(first_commit, merge)`` UTC timestamps for ``slug`` from git.

    A change's **merge commit** is the ``git log`` commit reachable from
    ``base_ref`` (default: ``HEAD``) whose squash subject starts with
    ``"<slug>:"`` — the newest such commit wins. Its **committer date** is the
    merge timestamp; the **first-commit timestamp** is the committer date of
    that commit's **first parent** (the commit it landed on top of). On this
    serial, one-change-per-PR pipeline the span ``merge − first_parent`` is the
    change's wall-clock lead time — the honest v1 proxy derivable from the
    squash history, since a squash-and-merge collapses a change's own author and
    committer dates onto the merge moment (documented as a v1 definition later
    members can refine). Change lead time is then ``merge − first_commit``.

    Returns ``(None, None)`` on any miss — no matching subject, the matched
    commit being a parentless root, a shallow clone with the parent absent, no
    git repo, or a ``git`` failure — so :func:`derive` computes lead time only
    over changes where **both** timestamps resolve, and never fails on an
    unresolvable one.
    """
    ref = base_ref or "HEAD"
    fmt = _GIT_SEP.join(["%H", "%ct", "%P", "%s"])
    try:
        proc = subprocess.run(
            ["git", "-C", os.path.abspath(root), "log",
             "--format=" + fmt, ref],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=False, text=True)
    except (OSError, ValueError):
        return None, None
    if proc.returncode != 0 or not proc.stdout:
        return None, None

    ts_by_hash = {}
    commits = []  # (hash, committer_epoch, [parent_hashes], subject) in log order
    for line in proc.stdout.splitlines():
        parts = line.split(_GIT_SEP, 3)
        if len(parts) != 4:
            continue
        sha, committer_epoch, parents, subject = parts
        ts_by_hash[sha] = committer_epoch
        commits.append((sha, committer_epoch, parents.split(), subject))

    prefix = slug + ":"
    for _sha, committer_epoch, parent_hashes, subject in commits:
        if not subject.startswith(prefix):
            continue
        merge = _epoch_to_utc(committer_epoch)
        first_commit = None
        if parent_hashes:
            first_commit = _epoch_to_utc(ts_by_hash.get(parent_hashes[0]))
        if merge is None or first_commit is None:
            return None, None
        return first_commit, merge
    return None, None


# ---------------------------------------------------------------------------
# Change-failure signal sources (delivery-metrics change-failure-signal): the
# post-merge remediation evidence a shipped change has failed — a base-branch
# revert derived from git, or a later shipped change declaring `Fixes:`. Both
# are pure derivations over sources the pipeline already emits (git history and
# the dated archives) — no new capture verb, no new event file.
# ---------------------------------------------------------------------------

# A git revert commit's subject opens with this literal (``git revert`` default).
_REVERT_SUBJECT_PREFIX = 'Revert "'


def git_revert_signals(root, base_ref=None):
    """Scan git for post-merge **revert** signals: ``{slug: [iso-utc-ts, ...]}``.

    Follows the :func:`git_change_times` idiom — one ``git log --format`` scan
    over ``base_ref or "HEAD"`` via stdlib subprocess (stderr devnulled); any
    failure or non-repository degrades to ``{}``, never an error. A commit
    signals a revert of ``<slug>`` when its subject starts ``Revert "`` and the
    quoted text begins ``<slug>:`` (the ``<slug>:``-prefixed squash subject the
    revert names); the value is the revert commit's UTC ISO committer timestamp,
    and multiple reverts of one slug accrete in ``git log`` order. A
    revert-of-revert — whose quoted text itself starts ``Revert `` — re-lands the
    change and so **never** counts.
    """
    ref = base_ref or "HEAD"
    fmt = _GIT_SEP.join(["%ct", "%s"])
    try:
        proc = subprocess.run(
            ["git", "-C", os.path.abspath(root), "log",
             "--format=" + fmt, ref],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=False, text=True)
    except (OSError, ValueError):
        return {}
    if proc.returncode != 0 or not proc.stdout:
        return {}

    signals = {}
    for line in proc.stdout.splitlines():
        parts = line.split(_GIT_SEP, 1)
        if len(parts) != 2:
            continue
        committer_epoch, subject = parts
        if not subject.startswith(_REVERT_SUBJECT_PREFIX):
            continue
        quoted = subject[len(_REVERT_SUBJECT_PREFIX):]
        if quoted.startswith("Revert "):
            continue  # a revert-of-revert re-lands the change
        colon = quoted.find(":")
        if colon <= 0:
            continue
        slug = quoted[:colon]
        ts = _epoch_to_utc(committer_epoch)
        if ts is None:
            continue
        signals.setdefault(slug, []).append(ts.isoformat())
    return signals


def collect_fix_links(root):
    """Collect declared post-merge **fix** links from the dated archives:
    ``{fixed_slug: [fixing_slug, ...]}``.

    Walks every ``completed/<YYYY-MM-DD>-<slug>/plan.md`` (dir names matched by
    :data:`_ARCHIVE_DIR_RE`), parses the plan header with
    :func:`spec_common.parse_plan_metadata`, and records each ``Fixes: <slug>``
    line as an edge from the fixed slug to the archive's own (fixing) slug. Only
    **shipped** fixes count — a dated archive exists exactly for a merged change,
    so a log-only shipped change cannot declare a fix (an accepted limitation). A
    missing/unreadable ``plan.md`` or an archive with no ``Fixes`` line
    contributes nothing.
    """
    links = {}
    completed_dir = os.path.join(sc.specs_dir(root), "completed")
    try:
        names = sorted(os.listdir(completed_dir))
    except OSError:
        return links
    for name in names:
        m = _ARCHIVE_DIR_RE.match(name)
        if not m:
            continue
        fixing_slug = m.group(4)
        plan_path = os.path.join(completed_dir, name, "plan.md")
        try:
            with open(plan_path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        for key, value in sc.parse_plan_metadata(text):
            if key == "Fixes" and value:
                links.setdefault(value, []).append(fixing_slug)
    return links


def collect_change_failures(root, ship_events, base_ref=None):
    """Join the revert and declared-fix signals over the shipped changes into the
    post-merge change-failure block (delivery-metrics change-failure-signal).

    A shipped change has **failed** when post-merge remediation exists for it — a
    base-branch revert (:func:`git_revert_signals`, looked up as a module
    attribute at call time so a test may monkeypatch it) or a later shipped
    change declaring ``Fixes: <slug>`` (:func:`collect_fix_links`). Both signal
    maps are joined over the distinct shipped slugs from ``ship_events``; a
    signal naming a slug that was never shipped is ignored. Returns
    ``{rate, n_failed, n_shipped, failed}`` where ``failed`` lists
    ``{slug, signals}`` sorted by slug, each ``signals`` list carrying
    ``{kind: "revert", ts}`` per revert (committer timestamp) followed by
    ``{kind: "fix", by}`` per fixing change — a change counting **once** in
    ``n_failed`` however many signals it accrues. ``rate = n_failed / n_shipped``,
    or ``None`` when there are no ship events.
    """
    shipped = sorted({e["slug"] for e in ship_events if e.get("slug")})
    revert_signals = git_revert_signals(root, base_ref)
    fix_links = collect_fix_links(root)
    failed = []
    for slug in shipped:
        signals = [{"kind": "revert", "ts": ts}
                   for ts in revert_signals.get(slug, [])]
        signals.extend({"kind": "fix", "by": by}
                       for by in fix_links.get(slug, []))
        if signals:
            failed.append({"slug": slug, "signals": signals})
    n_shipped = len(shipped)
    n_failed = len(failed)
    return {
        "rate": (n_failed / n_shipped) if n_shipped else None,
        "n_failed": n_failed,
        "n_shipped": n_shipped,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# Humanizing formatters + the pure summary renderer (delivery-metrics
# metrics-cli). Each formatter is None-tolerant → "n/a"; the renderer reads only
# median/p85/n from the stat blocks — never a bare mean — and attributes nothing
# to an individual (the SPACE guardrail).
# ---------------------------------------------------------------------------

def _fmt_duration(seconds):
    """Humanize a duration in seconds: ``42s`` / ``12m`` / ``3.4h`` / ``2.1d``
    (whole seconds and minutes; one decimal for hours and days). ``None`` →
    ``"n/a"``."""
    if seconds is None:
        return "n/a"
    seconds = float(seconds)
    if seconds < 60:
        return "%ds" % int(seconds)
    if seconds < 3600:
        return "%dm" % int(seconds / 60)
    if seconds < 86400:
        return "%.1fh" % (seconds / 3600.0)
    return "%.1fd" % (seconds / 86400.0)


def _trim_decimal(value):
    """Format ``value`` with one decimal, dropping a trailing ``.0`` — so
    ``85.0`` → ``"85"`` but ``1.2`` stays ``"1.2"``."""
    text = "%.1f" % value
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _fmt_tokens(n):
    """Humanize a token count: ``950`` / ``85k`` / ``1.2M`` (raw under 1k, then
    thousands / millions with a trailing-zero-trimmed decimal). ``None`` →
    ``"n/a"``."""
    if n is None:
        return "n/a"
    n = float(n)
    if abs(n) < 1000:
        return "%d" % int(n)
    if abs(n) < 1_000_000:
        return _trim_decimal(n / 1000.0) + "k"
    return _trim_decimal(n / 1_000_000.0) + "M"


def _fmt_pct(rate):
    """A fractional rate (``0.18``) as a whole percentage (``"18%"``). ``None``
    → ``"n/a"``."""
    if rate is None:
        return "n/a"
    return "%d%%" % round(rate * 100)


def _last_four(counts):
    """The last up-to-four per-week counts joined for display, or ``"n/a"`` when
    no weeks exist."""
    tail = counts[-4:]
    return " ".join(str(c) for c in tail) if tail else "n/a"


def render_summary_lines(metrics):
    """Render a ``derive`` dict as a human-readable, team-level delivery summary
    — derive-dict in, list of lines out, **no I/O** (mirroring
    :func:`dashboard.render_board_lines`) so tests assert on lines without stdout
    capture. Absent statistics render ``"n/a"``; the trend segment is omitted
    under five weeks of history; empty sources never raise. Reads only
    ``median``/``p85``/``n`` from the stat blocks — never a mean — per the epic's
    canon.
    """
    lines = []

    generated_at = metrics.get("generated_at") or ""
    date = generated_at.split("T", 1)[0] or "n/a"
    lines.append("delivery metrics — %s" % date)

    # Throughput: total, the last four ISO weeks, and a 4-vs-preceding-4 trend
    # (omitted under five weeks of history).
    throughput = metrics.get("throughput") or {}
    counts = [w.get("count", 0) for w in (throughput.get("per_week") or [])]
    line = "throughput: %d shipped · last 4 weeks: %s" % (
        throughput.get("total", 0) or 0, _last_four(counts))
    trend = throughput_trend(counts)
    if trend is not None:
        arrow = {"up": "↑", "down": "↓", "flat": "→"}[trend]
        line += " · trend %s" % arrow
    lines.append(line)

    # Deployment frequency: the DORA band + recent deployment-day counts.
    deployment = metrics.get("deployment_days") or {}
    dep_counts = [w.get("count", 0)
                  for w in (deployment.get("per_week") or [])]
    lines.append(
        "deployment frequency: %s · deployment-days last 4 weeks: %s" % (
            deployment.get("dora_band") or "n/a", _last_four(dep_counts)))

    # Lead / cycle time: median + p85 + sample count, humanized.
    for label, key in (("lead time", "lead_time"), ("cycle time", "cycle_time")):
        block = metrics.get(key) or {}
        lines.append("%s: median %s · p85 %s (n=%d)" % (
            label, _fmt_duration(block.get("median")),
            _fmt_duration(block.get("p85")), block.get("n", 0) or 0))

    # Rework rate: the pre-merge outcome proxy as a whole percentage.
    outcomes = metrics.get("outcomes") or {}
    lines.append("rework rate: %s (pre-merge proxy: rejected + needs-human)"
                 % _fmt_pct(outcomes.get("rework_rate")))

    # Change-fail rate: the post-merge signal, labelled beside the proxy.
    change_failures = metrics.get("change_failures") or {}
    lines.append(
        "change-fail rate: %s (post-merge: reverts + declared fixes)"
        % _fmt_pct(change_failures.get("rate")))

    # WIP: in-flight count, then states sorted by count descending, then name.
    by_state = (metrics.get("wip") or {}).get("by_state") or {}
    if by_state:
        ordered = sorted(by_state.items(), key=lambda kv: (-kv[1], kv[0]))
        parts = " · ".join("%s %d" % (state, n) for state, n in ordered)
        lines.append("wip: %d in flight — %s" % (sum(by_state.values()), parts))
    else:
        lines.append("wip: none")

    # Cost: token-output and wall-clock totals with per-change medians.
    cost = metrics.get("cost") or {}
    tokens = cost.get("tokens_output") or {}
    seconds = cost.get("seconds") or {}
    lines.append(
        "cost: %s output tokens (median %s/change) · "
        "%s wall-clock (median %s/change)" % (
            _fmt_tokens(tokens.get("total")), _fmt_tokens(tokens.get("median")),
            _fmt_duration(seconds.get("total")),
            _fmt_duration(seconds.get("median"))))

    return lines


# ---------------------------------------------------------------------------
# The derive() entry point
# ---------------------------------------------------------------------------

def _as_utc(now):
    """Coerce ``now`` to an aware UTC ``datetime`` (a naive value is assumed
    UTC), defaulting to the current UTC time when ``None`` — the one wall-clock
    read, injectable for determinism."""
    if now is None:
        return _dt.datetime.now(UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now.astimezone(UTC)


def _week_start(when):
    """The Monday (UTC date) of ``when``'s ISO week."""
    date = when.date() if isinstance(when, _dt.datetime) else when
    return date - _dt.timedelta(days=date.weekday())


def _week_key(monday):
    """The ISO ``<year>-W<week>`` label for a week's Monday date."""
    iso = monday.isocalendar()
    return "%04d-W%02d" % (iso[0], iso[1])


def _week_timeline(ship_events, now):
    """The contiguous list of week-Monday dates from the earliest ship to
    ``now`` (inclusive), so per-week series carry **zero-filled gaps** and the
    DORA-band median is not biased by dropping empty weeks. Empty when there are
    no dated ships."""
    dates = [e["ship_ts"] for e in ship_events if e.get("ship_ts") is not None]
    if not dates:
        return []
    start = _week_start(min(dates))
    end = max(start, _week_start(now))
    weeks = []
    cur = start
    while cur <= end:
        weeks.append(cur)
        cur += _dt.timedelta(days=7)
    return weeks


def derive(root, now=None, config=None):
    """Derive the full delivery-metrics dict for ``root`` — the engine's single
    entry point.

    Composes the collectors and derivation helpers into one **JSON-serializable**
    dict; it is pure and deterministic (``now`` and ``config`` are injectable,
    every timestamp is UTC) and it **writes nothing and prints nothing**. The
    returned blocks:

    - ``throughput``: ``{per_week: [{week, count}], total}`` — completed-count
      per ISO week (zero-filled) and overall.
    - ``deployment_days``: ``{per_week: [{week, count}], dora_band}`` — distinct
      deployment-days per week and the DORA frequency band.
    - ``lead_time`` / ``cycle_time``: percentile :func:`stat_block`s (median,
      p50/p85/p95, n — never a bare mean). Lead time is ``merge − first_commit``
      over changes whose git timestamps both resolve; cycle time (v1) is the
      per-change build elapsed recorded in the log, in seconds.
    - ``wip``: ``{by_state, items, aging}`` from :func:`collect_wip`.
    - ``outcomes``: :func:`collect_outcomes` plus a ``rework_rate`` — the
      pre-merge rework proxy ``(rejected + needs_human) / (shipped + rejected +
      needs_human)``, kept separate from the post-merge change-fail rate.
    - ``change_failures``: :func:`collect_change_failures` — the post-merge
      change-failure block (``rate``, ``n_failed``, ``n_shipped``, ``failed``)
      derived from base-branch reverts and declared ``Fixes:`` links.
    - ``cost``: token-output and wall-clock (seconds) totals and per-change
      medians.

    ``git_change_times`` is looked up as a module attribute at call time, so a
    test may monkeypatch it to avoid touching a real repository.
    """
    now = _as_utc(now)
    ship_events = collect_ship_events(root, config)

    # Throughput + deployment-days per week (zero-filled over the timeline).
    weeks = _week_timeline(ship_events, now)
    ships_by_week = {}
    depdays_by_week = {}
    for event in ship_events:
        ts = event.get("ship_ts")
        if ts is None:
            continue
        wk = _week_start(ts)
        ships_by_week[wk] = ships_by_week.get(wk, 0) + 1
        depdays_by_week.setdefault(wk, set()).add(ts.date())
    throughput_per_week = [
        {"week": _week_key(w), "count": ships_by_week.get(w, 0)}
        for w in weeks]
    deployment_per_week = [
        {"week": _week_key(w), "count": len(depdays_by_week.get(w, set()))}
        for w in weeks]
    dated_total = sum(ships_by_week.values())

    throughput = {"per_week": throughput_per_week, "total": dated_total}
    deployment_days = {
        "per_week": deployment_per_week,
        "dora_band": dora_band([item["count"] for item in deployment_per_week]),
    }

    # Lead time: only over changes whose git timestamps both resolve.
    lead_values = []
    for event in ship_events:
        first_commit, merge = git_change_times(root, event["slug"])
        if first_commit is not None and merge is not None:
            lead_values.append((merge - first_commit).total_seconds())
    lead_time = stat_block(lead_values)

    # Cycle time v1 = per-change build elapsed (seconds) from the log.
    cycle_values = [event["seconds"] for event in ship_events
                    if event.get("seconds") is not None]
    cycle_time = stat_block(cycle_values)

    wip = collect_wip(root, now)

    outcomes = collect_outcomes(root)
    counts = outcomes["counts"]
    denom = counts["shipped"] + counts["rejected"] + counts["needs_human"]
    outcomes["rework_rate"] = (
        (counts["rejected"] + counts["needs_human"]) / denom
        if denom else None)

    # Post-merge change-failure block: reverts + declared fixes over the shipped
    # changes (kept separate from the pre-merge rework proxy above).
    change_failures = collect_change_failures(root, ship_events)

    tokens = [event["tokens_output"] for event in ship_events
              if event.get("tokens_output") is not None]
    seconds = [event["seconds"] for event in ship_events
               if event.get("seconds") is not None]
    cost = {
        "tokens_output": {
            "total": sum(tokens),
            "median": statistics.median(tokens) if tokens else None,
        },
        "seconds": {
            "total": sum(seconds),
            "median": statistics.median(seconds) if seconds else None,
        },
    }

    # Flow time-series: the recorded lifecycle history as a read-only,
    # counts-only series (later members needing slugs call collect_flow
    # directly). derive stays write-free — it never calls record_flow.
    flow_records = collect_flow(root, config)
    flow = {
        "series": [{"ts": r["ts"], "by_state": r["by_state"]}
                   for r in flow_records],
        "n": len(flow_records),
    }

    return {
        "generated_at": now.isoformat(),
        "throughput": throughput,
        "deployment_days": deployment_days,
        "lead_time": lead_time,
        "cycle_time": cycle_time,
        "wip": wip,
        "outcomes": outcomes,
        "change_failures": change_failures,
        "cost": cost,
        "flow": flow,
    }


# ---------------------------------------------------------------------------
# Monte-Carlo delivery forecast (delivery-metrics delivery-forecast): pure
# throughput-sampling simulators over the daily ship history, deterministic for
# a given seed, answering "how many by date D" and "when will N ship" with
# explicit 50/85/95 confidence bands. No estimates or story points ever feed the
# simulation — only observed throughput (the research's Monte-Carlo canon).
# ---------------------------------------------------------------------------

def daily_throughput(ship_events, now):
    """The zero-filled per-UTC-calendar-day ship counts from the first dated
    ship event through ``now`` (inclusive) — the simulators' sampling input.

    Each event's ``ship_ts`` (an aware UTC datetime; ``None`` is ignored) is
    bucketed by its UTC calendar date. The returned list runs one entry per day
    from the earliest ship date through ``now``'s UTC date, **zero-filling the
    gaps** — a zero-ship day is a real observation the Monte-Carlo draw must be
    able to sample, not an absence to drop. Returns an empty list when no event
    carries a date.
    """
    now = _as_utc(now)
    dates = [e["ship_ts"].date() for e in ship_events
             if e.get("ship_ts") is not None]
    if not dates:
        return []
    start = min(dates)
    end = max(start, now.date())
    counts_by_date = {}
    for d in dates:
        counts_by_date[d] = counts_by_date.get(d, 0) + 1
    span = (end - start).days
    return [counts_by_date.get(start + _dt.timedelta(days=i), 0)
            for i in range(span + 1)]


_EMPTY_BANDS = {"p50": None, "p85": None, "p95": None}


def forecast_when(daily_counts, items, runs=10000, seed=0, max_days=3650):
    """Monte-Carlo forecast of **how many days until ``items`` complete**, as
    ``{p50, p85, p95}`` day-counts.

    Each of ``runs`` simulated runs draws daily throughput samples **with
    replacement** from ``daily_counts`` (via ``random.Random(seed)`` — the same
    seed gives identical output) and counts the days until the cumulative sample
    reaches ``items``, capping each run at ``max_days`` (the termination guard: a
    run that has not finished by then records ``max_days``). The day-count at
    confidence ``c`` is the nearest-rank ``c``-th percentile of the run
    day-counts — **later at higher confidence**, so ``p50 ≤ p85 ≤ p95``. When
    the history is empty or every day is a zero (no throughput to sample), the
    bands are all ``None`` — the simulation is short-circuited rather than run to
    the cap on a distribution that can never finish.
    """
    if not daily_counts or sum(daily_counts) == 0:
        return dict(_EMPTY_BANDS)
    rng = random.Random(seed)
    day_counts = []
    for _run in range(runs):
        cumulative = 0
        days = 0
        while cumulative < items and days < max_days:
            cumulative += rng.choice(daily_counts)
            days += 1
        day_counts.append(days)
    pct = percentiles(day_counts, ps=(50, 85, 95))
    return {"p50": pct["p50"], "p85": pct["p85"], "p95": pct["p95"]}


def forecast_how_many(daily_counts, days, runs=10000, seed=0):
    """Monte-Carlo forecast of **how many items complete within ``days``**, as
    ``{p50, p85, p95}`` counts.

    Each of ``runs`` simulated runs sums ``days`` daily throughput samples drawn
    **with replacement** from ``daily_counts`` (via ``random.Random(seed)``). The
    count at confidence ``c`` is the nearest-rank ``(100 − c)``-th percentile of
    the run totals — the count achieved or exceeded in at least ``c%`` of runs,
    so it is **non-increasing as confidence rises**: ``p95 ≤ p85 ≤ p50``. An
    empty or all-zero history yields all-``None`` bands (short-circuited).
    """
    if not daily_counts or sum(daily_counts) == 0:
        return dict(_EMPTY_BANDS)
    rng = random.Random(seed)
    totals = []
    for _run in range(runs):
        totals.append(sum(rng.choice(daily_counts) for _ in range(days)))
    # Confidence c reads the (100 − c)th percentile: the count achieved or
    # exceeded in at least c% of runs.
    pct = percentiles(totals, ps=(50, 15, 5))
    return {"p50": pct["p50"], "p85": pct["p15"], "p95": pct["p5"]}


def epic_remaining(root, epic):
    """The sorted slugs of an epic's **remaining** members — the epic stub-table
    members whose worktree-aware lifecycle state is not ``archived``.

    Reads ``.shipd/epics/<epic>/epic.md``, parses its ``## Changes`` stub table via
    :func:`spec_common.parse_epic_changes`, and resolves each member through the
    same worktree-aware :func:`_member_state_and_location` walk the WIP snapshot
    uses. "Remaining" means *not yet shipped*, so ``unplanned`` and every
    in-flight state count; only ``archived`` (shipped/exited) members are
    dropped. Returns the sorted remaining slugs, or ``None`` when the epic file
    does not exist (an epic typo is user error the verb reports, unlike an empty
    history which degrades to n/a).
    """
    epic_path = os.path.join(sc.specs_dir(root), "epics", epic, "epic.md")
    try:
        with open(epic_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    _header, rows = sc.parse_epic_changes(text)
    remaining = set()
    for slug, _description, _ratings in rows:
        if not slug:
            continue
        state, _location = _member_state_and_location(root, slug)
        if state != "archived":
            remaining.add(slug)
    return sorted(remaining)


# History is "sparse" — the steady-state Monte-Carlo assumption is shaky — below
# either threshold; the caution surfaces it rather than silently over-promising.
_SPARSE_MIN_DAYS = 14
_SPARSE_MIN_SHIPS = 10


def _history_summary(daily_counts):
    """The ``{days, total_shipped}`` summary of a daily-throughput history."""
    return {"days": len(daily_counts), "total_shipped": sum(daily_counts)}


def _sparse_caution(history):
    """A sparse-history caution string, or ``None`` when the history is thick
    enough. The history is thin below :data:`_SPARSE_MIN_DAYS` days **or**
    :data:`_SPARSE_MIN_SHIPS` total ships — too few observations for the
    steady-state Monte-Carlo assumption to hold, so the forecast is flagged
    low-confidence rather than presented as firm."""
    days = history["days"]
    ships = history["total_shipped"]
    if days >= _SPARSE_MIN_DAYS and ships >= _SPARSE_MIN_SHIPS:
        return None
    return ("history is thin — %d ship%s over %d day%s; treat this forecast as "
            "low-confidence, not a commitment" % (
                ships, "" if ships == 1 else "s",
                days, "" if days == 1 else "s"))


def build_forecast_result(daily_counts, now, mode, items=None, epic=None,
                          remaining=None, by_date=None, horizon_days=None,
                          runs=10000, seed=0):
    """Assemble the JSON-serializable forecast result dict from a daily-throughput
    history and a question.

    ``mode`` is ``"when"`` (``--items`` / ``--epic``: days until ``items``
    complete) or ``"how_many"`` (``--by-date``: items completed within
    ``horizon_days``). The dict carries ``generated_at``, ``mode``, the
    ``history`` summary, the question echo (``items`` — plus ``epic`` and
    ``remaining`` in epic mode — or ``by_date`` and ``horizon_days``), ``runs``,
    ``seed``, the ``bands``, and a ``caution``. For ``"when"`` each band is a
    ``{days, date}`` object (``date`` = ``now``'s UTC date plus the day-count),
    or ``None`` on empty history; for ``"how_many"`` each band is a count (or
    ``None``). The simulators are deterministic for ``seed``.
    """
    now = _as_utc(now)
    history = _history_summary(daily_counts)
    result = {
        "generated_at": now.isoformat(),
        "mode": mode,
        "history": history,
        "runs": runs,
        "seed": seed,
        "caution": _sparse_caution(history),
    }
    if mode == "when":
        result["items"] = items
        if epic is not None:
            result["epic"] = epic
            result["remaining"] = remaining
        raw = forecast_when(daily_counts, items, runs=runs, seed=seed)
        base = now.date()
        result["bands"] = {
            key: (None if raw[key] is None else {
                "days": raw[key],
                "date": (base + _dt.timedelta(days=raw[key])).isoformat()})
            for key in ("p50", "p85", "p95")}
    else:  # how_many
        result["by_date"] = by_date
        result["horizon_days"] = horizon_days
        result["bands"] = forecast_how_many(
            daily_counts, horizon_days, runs=runs, seed=seed)
    return result


def render_forecast_lines(result):
    """Render a forecast result dict as human-readable lines — result dict in,
    list of lines out, **no I/O** (mirroring :func:`render_summary_lines`).

    Emits a ``delivery forecast — <date>`` header, a history line, one bands line
    phrased per mode (``when``: ``50% by <date> (<n>d) · …``; ``how_many``:
    ``≥<n> at 50% · …`` under a ``by <date>`` target), and a caution line when
    the result carries one. Absent bands (empty history) render ``n/a``; empty
    sources never raise.
    """
    lines = []

    generated_at = result.get("generated_at") or ""
    date = generated_at.split("T", 1)[0] or "n/a"
    lines.append("delivery forecast — %s" % date)

    history = result.get("history") or {}
    total = history.get("total_shipped", 0) or 0
    days = history.get("days", 0) or 0
    lines.append("history: %d ship%s over %d day%s" % (
        total, "" if total == 1 else "s", days, "" if days == 1 else "s"))

    bands = result.get("bands") or {}
    if result.get("mode") == "when":
        items = result.get("items")
        target = "%d item%s" % (items or 0, "" if items == 1 else "s")
        if bands.get("p50") is None:
            lines.append("forecast (%s): n/a" % target)
        else:
            segs = ["%s%% by %s (%dd)" % (
                key[1:], bands[key]["date"], bands[key]["days"])
                for key in ("p50", "p85", "p95")]
            lines.append("forecast (%s): %s" % (target, " · ".join(segs)))
    else:  # how_many
        by_date = result.get("by_date") or "n/a"
        if bands.get("p50") is None:
            lines.append("forecast by %s: n/a" % by_date)
        else:
            segs = ["≥%d at %s%%" % (bands[key], key[1:])
                    for key in ("p50", "p85", "p95")]
            lines.append("forecast by %s: %s" % (by_date, " · ".join(segs)))

    caution = result.get("caution")
    if caution:
        lines.append("caution: %s" % caution)

    return lines


# ---------------------------------------------------------------------------
# Audience-framed rollups (delivery-metrics stakeholder-rollups): compose the
# derive() output — plus, for the PM view, the deterministic Monte-Carlo
# simulators over each epic's remaining members — into one audience-keyed,
# JSON-serializable rollup dict, rendered as a self-contained markdown document.
# No rollup ever attributes a metric to an individual, and the exec cut carries
# no change slug and no per-item detail (the SPACE guardrail).
# ---------------------------------------------------------------------------

ROLLUP_AUDIENCES = ("exec", "pm", "em")


def _weekly_counts(per_week):
    """The per-week ``count`` series from a ``{per_week: [{week, count}]}``
    block (``deployment_days``/``throughput`` share the shape)."""
    return [w.get("count", 0) for w in (per_week or [])]


def _build_exec_block(metrics_dict):
    """The executive cut: trend direction and bands only — never per-item detail
    or a change slug (the SPACE guardrail)."""
    throughput = metrics_dict.get("throughput") or {}
    deployment = metrics_dict.get("deployment_days") or {}
    lead = metrics_dict.get("lead_time") or {}
    outcomes = metrics_dict.get("outcomes") or {}
    cost = metrics_dict.get("cost") or {}
    tokens = cost.get("tokens_output") or {}
    seconds = cost.get("seconds") or {}
    return {
        "trend": {
            "throughput": throughput_trend(_weekly_counts(
                throughput.get("per_week"))),
        },
        "dora": {
            "deployment_frequency": deployment.get("dora_band"),
            "lead_time_tier": lead_time_dora_band(lead.get("median")),
        },
        "headlines": {
            "shipped_total": throughput.get("total", 0) or 0,
            "rework_rate": outcomes.get("rework_rate"),
            "change_fail_rate": (
                metrics_dict.get("change_failures") or {}).get("rate"),
        },
        "cost": {
            "tokens_output_total": tokens.get("total"),
            "seconds_total": seconds.get("total"),
        },
    }


def _epic_member_total(root, epic):
    """The count of stub-table member rows in an epic (its planned scope)."""
    epic_path = os.path.join(sc.specs_dir(root), "epics", epic, "epic.md")
    try:
        with open(epic_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return 0
    _header, rows = sc.parse_epic_changes(text)
    return sum(1 for slug, _description, _ratings in rows if slug)


def _completion_bands(daily_counts, now, items, runs, seed):
    """The 50/85/95 completion bands as ``{days, date}`` objects (or ``None``
    sub-bands on empty history) from :func:`forecast_when` over ``items``
    remaining members — mirroring :func:`build_forecast_result`'s ``when`` mode.
    """
    raw = forecast_when(daily_counts, items, runs=runs, seed=seed)
    base = now.date()
    return {
        key: (None if raw[key] is None else {
            "days": raw[key],
            "date": (base + _dt.timedelta(days=raw[key])).isoformat()})
        for key in ("p50", "p85", "p95")}


def _build_pm_block(root, metrics_dict, now, config, runs, seed):
    """The PM cut: recent throughput with the trend, and one entry per epic with
    its done/total counts and — when members remain — the deterministic
    completion bands over the remaining count, with the sparse-history caution.
    """
    counts = _weekly_counts((metrics_dict.get("throughput") or {})
                            .get("per_week"))
    pm_throughput = {"last_weeks": counts[-4:], "trend": throughput_trend(counts)}

    daily_counts = daily_throughput(collect_ship_events(root, config), now)
    caution = _sparse_caution(_history_summary(daily_counts))

    epics = []
    epics_dir = os.path.join(sc.specs_dir(root), "epics")
    try:
        epic_names = sorted(os.listdir(epics_dir))
    except OSError:
        epic_names = []
    for epic_name in epic_names:
        remaining = epic_remaining(root, epic_name)
        if remaining is None:
            continue
        total = _epic_member_total(root, epic_name)
        bands = (_completion_bands(daily_counts, now, len(remaining), runs, seed)
                 if remaining else None)
        epics.append({
            "epic": epic_name,
            "done": total - len(remaining),
            "total": total,
            "bands": bands,
            "caution": caution,
        })
    return {"throughput": pm_throughput, "epics": epics}


def _build_em_block(metrics_dict):
    """The EM cut: the lead/cycle-time stat blocks, WIP by state with aging,
    recent deployment-days, the rework rate, and the flow series' record count
    with its latest per-state counts."""
    deployment = metrics_dict.get("deployment_days") or {}
    outcomes = metrics_dict.get("outcomes") or {}
    flow = metrics_dict.get("flow") or {}
    series = flow.get("series") or []
    latest = series[-1].get("by_state", {}) if series else {}
    return {
        "lead_time": metrics_dict.get("lead_time"),
        "cycle_time": metrics_dict.get("cycle_time"),
        "wip": metrics_dict.get("wip"),
        "deployment_days_last_weeks": _weekly_counts(
            deployment.get("per_week"))[-4:],
        "rework_rate": outcomes.get("rework_rate"),
        "change_fail_rate": (
            metrics_dict.get("change_failures") or {}).get("rate"),
        "flow": {"n": flow.get("n", 0) or 0, "latest_by_state": latest},
    }


def build_rollup_result(root, audience, now=None, config=None, runs=10000,
                        seed=0):
    """Compose an audience-framed rollup dict for ``root`` — the builder behind
    the ``rollup`` verb.

    Derives the full delivery-metrics dict (:func:`derive`) and folds it — plus,
    for the ``pm`` view, the deterministic Monte-Carlo simulators over each
    epic's remaining members — into ``{generated_at, audience, <audience
    block>}``, keyed by the audience name (``exec``/``pm``/``em``). The result is
    **JSON-serializable** and pure: ``now`` and ``config`` are injectable and the
    PM forecast draws through the injectable ``runs``/``seed`` (defaults
    10000/0), so the same inputs give byte-identical output. No block attributes
    a metric to an individual, and the exec block carries no change slug (the
    SPACE guardrail). An unrecognized ``audience`` raises ``ValueError`` (the CLI
    rejects one earlier via argparse ``choices``).
    """
    now = _as_utc(now)
    metrics_dict = derive(root, now, config)
    result = {"generated_at": now.isoformat(), "audience": audience}
    if audience == "exec":
        result["exec"] = _build_exec_block(metrics_dict)
    elif audience == "pm":
        result["pm"] = _build_pm_block(
            root, metrics_dict, now, config, runs, seed)
    elif audience == "em":
        result["em"] = _build_em_block(metrics_dict)
    else:
        raise ValueError("unknown rollup audience: %r" % (audience,))
    return result


def _fmt_state_counts(by_state):
    """A ``state N · state N`` string ordered by count descending then name, or
    ``"none"`` when empty (the summary renderer's WIP ordering)."""
    if not by_state:
        return "none"
    ordered = sorted(by_state.items(), key=lambda kv: (-kv[1], kv[0]))
    return " · ".join("%s %d" % (state, n) for state, n in ordered)


def _fmt_stat_line(block):
    """An ``em`` stat block as ``median X · p85 Y · p95 Z (n=N)`` with each
    duration humanized (``n/a`` for an absent statistic — never a mean)."""
    block = block or {}
    return "median %s · p85 %s · p95 %s (n=%d)" % (
        _fmt_duration(block.get("median")), _fmt_duration(block.get("p85")),
        _fmt_duration(block.get("p95")), block.get("n", 0) or 0)


def _rollup_exec_lines(block):
    """The executive markdown sections — trend direction and bands, plain
    business phrasing, never a change slug or per-item detail."""
    lines = []
    trend = (block.get("trend") or {}).get("throughput")
    headlines = block.get("headlines") or {}
    lines.append("## headlines")
    lines.append("- shipped: %d changes" % (headlines.get("shipped_total") or 0))
    lines.append("- rework rate: %s (pre-merge proxy: rejected + needs-human)"
                 % _fmt_pct(headlines.get("rework_rate")))
    lines.append("- change-fail rate: %s (post-merge: reverts + declared fixes)"
                 % _fmt_pct(headlines.get("change_fail_rate")))
    # The trend line is omitted entirely when there is too little history.
    if trend is not None:
        lines.append("- throughput trend: %s" % trend)

    dora = block.get("dora") or {}
    lines.append("## dora bands")
    lines.append("- deployment frequency: %s"
                 % (dora.get("deployment_frequency") or "n/a"))
    lines.append("- lead-time tier: %s" % (dora.get("lead_time_tier") or "n/a"))

    cost = block.get("cost") or {}
    lines.append("## cost")
    lines.append("- output tokens: %s"
                 % _fmt_tokens(cost.get("tokens_output_total")))
    lines.append("- wall-clock: %s" % _fmt_duration(cost.get("seconds_total")))
    return lines


def _rollup_pm_lines(block):
    """The PM markdown sections — recent throughput with the trend and one
    predictability entry per epic (done-of-total plus completion bands)."""
    lines = []
    throughput = block.get("throughput") or {}
    lines.append("## throughput")
    lines.append("- last 4 weeks: %s"
                 % _last_four(throughput.get("last_weeks") or []))
    trend = throughput.get("trend")
    if trend is not None:
        lines.append("- throughput trend: %s" % trend)

    lines.append("## epics")
    epics = block.get("epics") or []
    if not epics:
        lines.append("- none")
    cautions = []
    for epic in epics:
        head = "- %s: %d of %d done" % (
            epic.get("epic"), epic.get("done") or 0, epic.get("total") or 0)
        bands = epic.get("bands")
        if not bands or bands.get("p50") is None:
            lines.append("%s · forecast: n/a" % head)
        else:
            segs = ["%s%% by %s (%dd)" % (
                key[1:], bands[key]["date"], bands[key]["days"])
                for key in ("p50", "p85", "p95")]
            lines.append("%s · %s" % (head, " · ".join(segs)))
        caution = epic.get("caution")
        if caution and caution not in cautions:
            cautions.append(caution)
    if cautions:
        lines.append("## caution")
        for caution in cautions:
            lines.append("- %s" % caution)
    return lines


def _rollup_em_lines(block):
    """The EM markdown sections — the operational flow cut (percentiles, WIP and
    aging, deployment-days, rework, and the flow series), never a mean."""
    lines = []
    lines.append("## flow times")
    lines.append("- lead time: %s" % _fmt_stat_line(block.get("lead_time")))
    lines.append("- cycle time: %s" % _fmt_stat_line(block.get("cycle_time")))

    wip = block.get("wip") or {}
    by_state = wip.get("by_state") or {}
    lines.append("## wip")
    if by_state:
        lines.append("- %d in flight — %s" % (
            sum(by_state.values()), _fmt_state_counts(by_state)))
    else:
        lines.append("- none in flight")
    aging = wip.get("aging") or {}
    lines.append("- aging: median %s · p85 %s (n=%d)" % (
        _fmt_duration_days(aging.get("median")),
        _fmt_duration_days(aging.get("p85")), aging.get("n", 0) or 0))

    lines.append("## deployment")
    lines.append("- deployment-days last 4 weeks: %s"
                 % _last_four(block.get("deployment_days_last_weeks") or []))

    lines.append("## rework")
    lines.append("- rework rate: %s (pre-merge proxy: rejected + needs-human)"
                 % _fmt_pct(block.get("rework_rate")))
    lines.append("- change-fail rate: %s (post-merge: reverts + declared fixes)"
                 % _fmt_pct(block.get("change_fail_rate")))

    flow = block.get("flow") or {}
    n = flow.get("n", 0) or 0
    lines.append("## flow series")
    lines.append("- %d snapshot%s · latest: %s" % (
        n, "" if n == 1 else "s",
        _fmt_state_counts(flow.get("latest_by_state") or {})))
    return lines


def _fmt_duration_days(days):
    """Humanize a work-item age already expressed in **days**: ``n/a`` for
    ``None``, else one decimal (``4.0d``)."""
    if days is None:
        return "n/a"
    return "%.1fd" % float(days)


_ROLLUP_SECTIONS = {
    "exec": _rollup_exec_lines,
    "pm": _rollup_pm_lines,
    "em": _rollup_em_lines,
}


def render_rollup_lines(result):
    """Render an audience-framed rollup dict as a **self-contained markdown
    document** — rollup dict in, list of lines out, **no I/O** (mirroring
    :func:`render_summary_lines`/:func:`render_forecast_lines`).

    Emits a ``# delivery rollup — <audience> — <date>`` title, then the
    audience's ``##`` sections of ``- `` bullets. Absent statistics render
    ``n/a``; the throughput-trend line is omitted under five weeks of history;
    the exec cut is phrased in plain business terms and names no change slug (the
    SPACE guardrail). Empty sources never raise.
    """
    audience = result.get("audience") or "n/a"
    generated_at = result.get("generated_at") or ""
    date = generated_at.split("T", 1)[0] or "n/a"
    lines = ["# delivery rollup — %s — %s" % (audience, date)]
    builder = _ROLLUP_SECTIONS.get(audience)
    if builder is not None:
        lines.extend(builder(result.get(audience) or {}))
    return lines


# ---------------------------------------------------------------------------
# CLI: the thin `summary` verb (delivery-metrics metrics-cli)
# ---------------------------------------------------------------------------

def _cmd_summary(args):
    """Derive the metrics for ``--root`` and print them — the human-readable
    summary lines, or the full derive dict as JSON under ``--json``. The thin
    shell over :func:`derive` and :func:`render_summary_lines`."""
    result = derive(os.path.abspath(args.root))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for line in render_summary_lines(result):
            print(line)
    return 0


def _cmd_record_flow(args):
    """Append a flow-time-series snapshot for ``--root`` and report it — the
    manual/cron capture surface and the observable verification seam
    (delivery-metrics flow-timeseries). Prints the appended record as JSON, or
    ``unchanged`` when the snapshot deduped (or recording is disabled), always
    exiting ``0``."""
    record = record_flow(os.path.abspath(args.root))
    if record is None:
        print("unchanged")
    else:
        print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def _cmd_forecast(args):
    """Wire collection → simulation → renderer/JSON for the ``forecast`` verb
    (delivery-metrics delivery-forecast).

    Collects the root's ship events, derives the daily-throughput history, and
    runs the mode's simulator: ``--by-date`` (how many ship by a horizon) or
    ``--items`` / ``--epic`` (when N — or an epic's remaining members — ship).
    Prints the rendered lines, or the result dict as JSON under ``--json``.
    Exits ``2`` on an unparseable or non-future ``--by-date`` and on an unknown
    epic; otherwise ``0`` — an empty history degrades to ``n/a`` bands, never an
    error.
    """
    root = os.path.abspath(args.root)
    now = _as_utc(None)
    daily_counts = daily_throughput(collect_ship_events(root), now)

    if args.by_date is not None:
        try:
            target = _dt.date.fromisoformat(args.by_date)
        except ValueError:
            cc.err("forecast: --by-date must be YYYY-MM-DD (got %r)"
                   % args.by_date)
            return 2
        horizon_days = (target - now.date()).days
        if horizon_days <= 0:
            cc.err("forecast: --by-date must be after today (%s)"
                   % now.date().isoformat())
            return 2
        result = build_forecast_result(
            daily_counts, now, "how_many", by_date=args.by_date,
            horizon_days=horizon_days, runs=args.runs, seed=args.seed)
    else:
        epic = None
        remaining = None
        if args.epic is not None:
            remaining = epic_remaining(root, args.epic)
            if remaining is None:
                cc.err("forecast: no such epic %r" % args.epic)
                return 2
            epic = args.epic
            items = len(remaining)
        else:
            items = args.items
        result = build_forecast_result(
            daily_counts, now, "when", items=items, epic=epic,
            remaining=remaining, runs=args.runs, seed=args.seed)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for line in render_forecast_lines(result):
            print(line)
    return 0


def _cmd_rollup(args):
    """Wire builder → renderer/JSON for the ``rollup`` verb (delivery-metrics
    stakeholder-rollups).

    Builds the audience-framed rollup for ``--root`` and prints the rendered
    self-contained markdown, or the rollup dict as JSON under ``--json``. Always
    exits ``0`` — an empty source degrades to ``n/a`` bullets, never an error;
    an unrecognized ``--audience`` is argparse's own exit-2 error (the ``rollup``
    verb never reaches this function with one)."""
    result = build_rollup_result(os.path.abspath(args.root), args.audience)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for line in render_rollup_lines(result):
            print(line)
    return 0


def main(argv=None):
    """The stdlib-argparse CLI entry point (subparser-style, so later verbs have
    room). Returns an exit code; importing the module never runs it."""
    parser = argparse.ArgumentParser(
        description="Delivery-metrics summary — the team-level delivery board "
                    "rendered as text.")
    sub = parser.add_subparsers(dest="verb", required=True)

    p_summary = sub.add_parser(
        "summary", help="derive and print the delivery-metrics summary")
    p_summary.add_argument("--root", default=os.getcwd(),
                           help="repository root (default: cwd)")
    p_summary.add_argument("--json", action="store_true",
                           help="emit the full derive dict as JSON")
    p_summary.set_defaults(func=_cmd_summary)

    p_record = sub.add_parser(
        "record-flow",
        help="append a flow-time-series lifecycle snapshot for the root")
    p_record.add_argument("--root", default=os.getcwd(),
                          help="repository root (default: cwd)")
    p_record.set_defaults(func=_cmd_record_flow)

    p_forecast = sub.add_parser(
        "forecast",
        help="Monte-Carlo delivery forecast from observed throughput")
    p_forecast.add_argument("--root", default=os.getcwd(),
                            help="repository root (default: cwd)")
    mode = p_forecast.add_mutually_exclusive_group(required=True)
    mode.add_argument("--items", type=int,
                      help="forecast when this many changes will ship")
    mode.add_argument(
        "--epic",
        help="forecast when an epic's remaining members will ship")
    mode.add_argument("--by-date", dest="by_date", metavar="YYYY-MM-DD",
                      help="forecast how many changes ship by this date")
    p_forecast.add_argument("--runs", type=int, default=10000,
                            help="Monte-Carlo run count (default: 10000)")
    p_forecast.add_argument("--seed", type=int, default=0,
                            help="RNG seed (default: 0)")
    p_forecast.add_argument("--json", action="store_true",
                            help="emit the forecast result dict as JSON")
    p_forecast.set_defaults(func=_cmd_forecast)

    p_rollup = sub.add_parser(
        "rollup",
        help="audience-framed delivery rollup as self-contained markdown")
    p_rollup.add_argument("--audience", required=True,
                          choices=ROLLUP_AUDIENCES,
                          help="the rollup's audience cut")
    p_rollup.add_argument("--root", default=os.getcwd(),
                          help="repository root (default: cwd)")
    p_rollup.add_argument("--json", action="store_true",
                          help="emit the rollup dict as JSON")
    p_rollup.set_defaults(func=_cmd_rollup)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
