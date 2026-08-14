#!/usr/bin/env python3
"""build_report.py — token telemetry for /s:build (stdlib only, no network).

Reads the live Claude Code session transcript for this project (plus every
subagent transcript spawned during the session) and aggregates token usage
per model, split into non-cached input, output, cache-write, and cache-read
buckets — the exact Anthropic billing buckets, so no estimation is needed.

Transcript layout (verified):
  ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/<slug>/<session-id>.jsonl
  ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/<slug>/<session-id>/subagents/agent-*.jsonl
where slug = re.sub(r'[^A-Za-z0-9]', '-', os.path.abspath(project_dir)).

Usage:
  build_report.py --since <ISO> [--project-dir <path>] [--session <id>]
                  [--transcript <path>] [--json] [--summary-only]
  build_report.py --since <ISO> --change <name> --schema <s> --tasks-done <d>
                  --tasks-total <t> --status <st> --commit <hash> --log

Never fails a build: on any transcript/telemetry problem it prints a
best-effort message and exits 0.
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_common as sc  # noqa: E402

EMPTY_BUCKETS = {
    "non_cached_input": 0,
    "output": 0,
    "cache_write": 0,
    "cache_read": 0,
}

# Harness-generated assistant records carry this literal model marker (with
# all-zero usage). They are not a real model doing work, so they are excluded
# from both the per-model usage map and the timing timeline.
SYNTHETIC_MODEL = "<synthetic>"


def human(n):
    """Short human-readable number: 999 -> '999', 1500 -> '1.5k', etc."""
    n = float(n)
    if n < 1000:
        return str(int(n))
    if n < 1_000_000:
        return f"{n / 1e3:.1f}k"
    if n < 1_000_000_000:
        return f"{n / 1e6:.1f}M"
    return f"{n / 1e9:.1f}B"


def human_duration(seconds):
    """Short human-readable duration: 45 -> '45s', 417 -> '6m57s',
    3840 -> '1h04m'."""
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m{s:02d}s"
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    return f"{h}h{m:02d}m"


def project_slug(project_dir):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project_dir))


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude"
    )


def resolve_project_root(project_dir):
    """Resolve a linked git worktree to its main checkout root.

    A linked worktree's ``.git`` is a *file* whose first line reads
    ``gitdir: <main>/.git/worktrees/<name>``. We read it (stdlib only, no
    ``git`` subprocess) and return ``<main>`` when the gitdir path has the
    shape ``.../.git/worktrees/<name>`` — i.e. its last two parents are
    ``worktrees`` inside ``.git``. A relative ``gitdir:`` path is resolved
    against ``project_dir``. On any other shape (e.g. a submodule's
    ``.git/modules/...``), an unreadable ``.git`` file, or a normal ``.git``
    directory, the absolute ``project_dir`` is returned unchanged.
    """
    abs_dir = os.path.abspath(project_dir)
    git_path = os.path.join(abs_dir, ".git")
    if not os.path.isfile(git_path):
        return abs_dir
    try:
        with open(git_path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
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
    # Expect .../<main>/.git/worktrees/<name>: the two parents of <name> must
    # be "worktrees" and ".git". This rules out submodule .git/modules/... .
    parent = os.path.dirname(gitdir)          # .../.git/worktrees
    grandparent = os.path.dirname(parent)     # .../.git
    if os.path.basename(parent) != "worktrees":
        return abs_dir
    if os.path.basename(grandparent) != ".git":
        return abs_dir
    return os.path.dirname(grandparent)       # .../<main>


def transcript_dir(project_dir):
    """Locate the session transcript directory for ``project_dir``.

    Prefers the directory's own path slug (a session launched inside the
    worktree keeps working as before). Only when that directory is absent and
    ``project_dir`` is a linked worktree does it fall back to the main
    checkout's slug directory. When neither exists, the own (nonexistent) path
    is returned so discovery degrades gracefully via the usual sentinel.
    """
    own = os.path.join(config_dir(), "projects", project_slug(project_dir))
    if os.path.isdir(own):
        return own
    root = resolve_project_root(project_dir)
    if root != os.path.abspath(project_dir):
        main = os.path.join(config_dir(), "projects", project_slug(root))
        if os.path.isdir(main):
            return main
    return own


def find_active_session(tdir, session=None):
    """Return (session_id, main_transcript_path) or (None, None)."""
    if not os.path.isdir(tdir):
        return None, None
    candidates = []
    for name in os.listdir(tdir):
        if name.endswith(".jsonl") and os.path.isfile(os.path.join(tdir, name)):
            candidates.append(name)
    if session is not None:
        target = f"{session}.jsonl"
        if target in candidates:
            return session, os.path.join(tdir, target)
        return None, None
    if not candidates:
        return None, None
    candidates.sort(key=lambda n: os.path.getmtime(os.path.join(tdir, n)), reverse=True)
    newest = candidates[0]
    return newest[: -len(".jsonl")], os.path.join(tdir, newest)


def subagent_transcripts(tdir, session_id):
    d = os.path.join(tdir, session_id, "subagents")
    if not os.path.isdir(d):
        return []
    return sorted(
        os.path.join(d, name)
        for name in os.listdir(d)
        if name.startswith("agent-") and name.endswith(".jsonl")
    )


# ---------------------------------------------------------------------------
# Live session-activity sampling (stdlib-only) — the board TUI's chart data
# layer lives here, in the module that already owns transcript location, so it
# stays importable and unit-testable without ``textual`` (session-activity-
# sampling).
# ---------------------------------------------------------------------------


# The generation-interval spread is capped so a long idle gap never smears a
# response's tokens back across minutes of history (session-activity-sampling).
ACTIVITY_SPREAD_CAP_SECONDS = 120


class ActivityTail:
    """An offset-keeping tail over one session's transcripts — its main
    ``<tdir>/<session_id>.jsonl`` plus every ``subagents/agent-*.jsonl`` — that
    on each :meth:`poll` re-discovers the subagent files, reads only the bytes
    appended since the previous poll, defers a torn trailing line until it is
    completed, dedupes each assistant response by ``message.id`` across polls
    and files, skips synthetic records, and yields one
    ``(start_epoch, end_epoch, output_tokens)`` interval event per response.

    ``end_epoch`` is the response's timestamp; ``start_epoch`` reaches back to
    the previous event's end in this same tail, capped at
    :data:`ACTIVITY_SPREAD_CAP_SECONDS` seconds, so the tokens spread over the
    interval they were generated over instead of landing in a single bucket.
    The first-ever event is zero-length (``start == end``).

    Best-effort like the rest of the module: an unreadable file or an
    unparseable line is skipped, never raised."""

    def __init__(self, tdir, session_id):
        self.tdir = tdir
        self.session_id = session_id
        self.main_path = os.path.join(tdir, "%s.jsonl" % session_id)
        self._offsets = {}
        self._seen_ids = set()
        # The end epoch of the previous event emitted by this tail (across
        # every file and poll); ``None`` until the first event, which is then
        # zero-length.
        self._prev_end = None

    def _files(self):
        # The main transcript first, then subagents re-discovered every poll so
        # a mid-run agent-*.jsonl is picked up as soon as it appears.
        return [self.main_path] + subagent_transcripts(self.tdir,
                                                        self.session_id)

    def _event(self, record):
        if record.get("type") != "assistant":
            return None
        message = record.get("message") or {}
        usage = message.get("usage")
        model = message.get("model")
        if not isinstance(usage, dict) or not model:
            return None
        if model == SYNTHETIC_MODEL:
            return None
        msg_id = message.get("id")
        if msg_id is not None:
            if msg_id in self._seen_ids:
                return None
            self._seen_ids.add(msg_id)
        ts = record.get("timestamp")
        if not ts:
            return None
        try:
            ts_dt = parse_timestamp(ts)
        except ValueError:
            return None
        end = ts_dt.timestamp()
        if self._prev_end is None:
            start = end  # first event: zero-length span
        else:
            span = min(end - self._prev_end, ACTIVITY_SPREAD_CAP_SECONDS)
            span = span if span > 0 else 0.0  # never span forward
            start = end - span
        self._prev_end = end
        return (start, end, usage.get("output_tokens") or 0)

    def poll(self):
        """Return the new ``(start_epoch, end_epoch, output_tokens)`` events
        across all of the session's transcripts since the previous poll, in
        file order."""
        events = []
        for path in self._files():
            try:
                with open(path, "rb") as fh:
                    fh.seek(self._offsets.get(path, 0))
                    data = fh.read()
            except OSError:
                continue
            if not data:
                continue
            nl = data.rfind(b"\n")
            if nl < 0:
                # The whole unread chunk is a torn (newline-less) line; defer
                # it entirely, leaving the offset unchanged, so a later poll
                # re-reads and yields it exactly once when completed.
                continue
            complete = data[: nl + 1]
            self._offsets[path] = self._offsets.get(path, 0) + len(complete)
            for raw in complete.split(b"\n"):
                if not raw.strip():
                    continue
                try:
                    record = json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    continue
                event = self._event(record)
                if event is not None:
                    events.append(event)
        return events


class MultiTail:
    """Several :class:`ActivityTail` instances keyed by ``(tdir, session_id)``,
    summing a set of sessions into one merged event stream. :meth:`sync` adds
    tails for newly-driving sessions and drops those that stopped driving
    (preserving the offset of every tail that persists across the sync);
    :meth:`poll` polls every current tail and merges their events
    (session-activity-sampling)."""

    def __init__(self):
        self._tails = {}

    def sync(self, keys):
        """Reconcile the live set of ``(tdir, session_id)`` keys: create a tail
        for each new key and drop tails whose key is gone; keys already present
        keep their existing tail (and its byte offsets)."""
        wanted = set(keys)
        for key in list(self._tails):
            if key not in wanted:
                del self._tails[key]
        for key in wanted:
            if key not in self._tails:
                tdir, session_id = key
                self._tails[key] = ActivityTail(tdir, session_id)

    def poll(self):
        """Merge the new events across every current tail (in key order)."""
        events = []
        for key in sorted(self._tails):
            events.extend(self._tails[key].poll())
        return events


def bucket_events(events, bucket_seconds):
    """Fold ``(start_epoch, end_epoch, output_tokens)`` interval events into
    buckets of ``bucket_seconds``: ``{bucket_start_epoch: token_sum}`` where a
    bucket start is ``epoch // bucket_seconds * bucket_seconds``.

    Each event's tokens are distributed across the buckets its ``[start, end]``
    span overlaps, proportional to the overlap length, so a response spreads as
    continuous throughput rather than landing in a single bucket. A zero-length
    span (a first event) lands wholly in the bucket of its timestamp.
    Distribution preserves the token total exactly — the remainder from integer
    division is assigned to the last overlapped bucket — so re-bucketing the
    same accumulated events at a different size is lossless
    (session-activity-sampling)."""
    buckets = {}

    def _add(bstart, tokens):
        buckets[bstart] = buckets.get(bstart, 0) + tokens

    for start_epoch, end_epoch, output_tokens in events:
        tokens = output_tokens or 0
        span = end_epoch - start_epoch
        if span <= 0:
            # Zero-length (or degenerate) span: all tokens in one bucket.
            _add(int(start_epoch // bucket_seconds) * bucket_seconds, tokens)
            continue
        # Enumerate the buckets the [start, end] span overlaps, with the
        # overlap length of each.
        overlaps = []
        b = int(start_epoch // bucket_seconds) * bucket_seconds
        while b < end_epoch:
            lo = start_epoch if start_epoch > b else b
            hi = end_epoch if end_epoch < b + bucket_seconds else b + bucket_seconds
            if hi > lo:
                overlaps.append((b, hi - lo))
            b += bucket_seconds
        # Distribute proportional to overlap; the last bucket takes whatever is
        # left so the token total is preserved exactly (no float drift).
        assigned = 0
        for i, (bstart, overlap) in enumerate(overlaps):
            if i == len(overlaps) - 1:
                share = tokens - assigned
            else:
                share = int(tokens * overlap / span)
                assigned += share
            _add(bstart, share)
    return buckets


# The chart cell ramp: index 0 is blank, indices 1..8 the eighth-block ramp,
# so ``CHART_BLOCKS[ceil(fill * 8)]`` maps a 0..1 fill straight to a cell glyph.
CHART_BLOCKS = " ▁▂▃▄▅▆▇█"


def render_chart(series, rows, floor, ceiling):
    """Render ``series`` as ``rows`` strings of eighth-block cells between
    ``floor`` and ``ceiling`` (block-chart-rendering). Per cell, the value's
    fraction ``frac = clamp((v - floor) / (ceiling - floor))`` drives a
    per-row fill ``clamp(frac * rows - (rows - 1 - r))`` quantized to 8 levels
    (``ceil(fill * 8)`` into :data:`CHART_BLOCKS`), so row ``0`` is the top and
    a value at the ceiling paints a full-height column of ``█`` while a value
    at or below the floor is blank."""
    span = (ceiling - floor) or 1
    out = []
    for r in range(rows):
        chars = []
        for v in series:
            frac = (v - floor) / span
            frac = 0.0 if frac < 0 else 1.0 if frac > 1 else frac
            fill = frac * rows - (rows - 1 - r)
            fill = 0.0 if fill < 0 else 1.0 if fill > 1 else fill
            chars.append(CHART_BLOCKS[math.ceil(fill * 8)])
        out.append("".join(chars))
    return out


def scale_bounds(series, mode):
    """The ``(floor, ceiling)`` a chart renders against (block-chart-rendering).
    ``fixed`` pins ``(0, 12000)``; ``auto`` clips the baseline to
    ``max(0, min * 0.75)`` and rounds the ceiling up to the next 500 above
    ``peak * 1.1`` (minimum 500), so a mostly-flat high series still shows
    movement. Safe for an empty or all-zero series."""
    if mode == "fixed":
        return (0, 12000)
    values = list(series) or [0]
    floor = max(0, int(min(values) * 0.75))
    ceiling = max(500, int(math.ceil(max(values) * 1.1 / 500) * 500))
    return (floor, ceiling)


def fmt_tokens(v):
    """A compact token count: values under 1000 as-is, larger ones as a
    ``5.6K`` style string (block-chart-rendering)."""
    v = int(v)
    if v < 1000:
        return str(v)
    return "%.1fK" % (v / 1000)


def parse_since(since_str):
    if since_str is None:
        return None
    s = since_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_timestamp(ts):
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def aggregate(paths, since_dt):
    """Sum usage per model across the given transcript files.

    Returns (by_model, timeline) where timeline is the list of (ts, model)
    tuples — one per in-window assistant record with a parseable
    timestamp — used for elapsed-time computation (see compute_timing).

    Each assistant API response is counted exactly once, keyed by its
    ``message.id``: a multi-record response (several transcript records
    repeating the same usage under one id) adds its usage only on the first
    record seen (build-reporting usage-dedup). Records with no id keep the
    prior behaviour (always counted). The timeline still records every
    timestamped record so elapsed-time attribution is unchanged.
    """
    by_model = {}
    timeline = []
    seen_ids = set()
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except (ValueError, TypeError):
                        continue
                    if record.get("type") != "assistant":
                        continue
                    message = record.get("message") or {}
                    usage = message.get("usage")
                    model = message.get("model")
                    if not isinstance(usage, dict) or not model:
                        continue
                    if model == SYNTHETIC_MODEL:
                        # Skip harness-generated records entirely: no usage
                        # accumulation and no timeline entry, so the preceding
                        # interval folds into the next real record.
                        continue
                    ts = record.get("timestamp")
                    ts_dt = None
                    if ts:
                        try:
                            ts_dt = parse_timestamp(ts)
                        except ValueError:
                            ts_dt = None
                    if since_dt is not None:
                        if ts_dt is None or ts_dt < since_dt:
                            continue
                    bucket = by_model.setdefault(model, dict(EMPTY_BUCKETS))
                    # Count each response once: skip usage accumulation for a
                    # message id already seen, but still ensure the model row
                    # exists (above) and always record the timeline entry
                    # (below) so timing attribution stays per-record.
                    msg_id = message.get("id")
                    counted = msg_id is not None and msg_id in seen_ids
                    if not counted:
                        if msg_id is not None:
                            seen_ids.add(msg_id)
                        bucket["non_cached_input"] += usage.get("input_tokens") or 0
                        bucket["output"] += usage.get("output_tokens") or 0
                        bucket["cache_write"] += usage.get("cache_creation_input_tokens") or 0
                        bucket["cache_read"] += usage.get("cache_read_input_tokens") or 0
                    if ts_dt is not None:
                        timeline.append((ts_dt, model))
        except OSError:
            continue
    return by_model, timeline


def compute_timing(timeline, since_dt):
    """Compute total elapsed time and per-model attributed time (seconds)
    from a timeline of (ts, model) tuples, per the archived build-report design §1.

    Walks the timeline in timestamp order, attributing the interval
    preceding each record to that record's model (clamped to >= 0), so
    per-model times always sum to total_time. Returns
    (total_time, by_model_time), or (None, None) if timing is unavailable
    (no timestamped records).
    """
    if not timeline:
        return None, None
    ordered = sorted(timeline, key=lambda pair: pair[0])
    start = since_dt if since_dt is not None else ordered[0][0]
    by_model_time = {}
    prev = start
    for ts, model in ordered:
        interval = max(0.0, (ts - prev).total_seconds())
        by_model_time[model] = by_model_time.get(model, 0.0) + interval
        prev = ts
    total_time = sum(by_model_time.values())
    return total_time, by_model_time


def totals_of(by_model):
    totals = dict(EMPTY_BUCKETS)
    for bucket in by_model.values():
        for k in EMPTY_BUCKETS:
            totals[k] += bucket[k]
    return totals


def summary_line(totals, number_format="short"):
    fmt = human if number_format != "raw" else (lambda n: str(int(n)))
    return (
        f"Tokens: {fmt(totals['non_cached_input'])}↑ {fmt(totals['output'])}↓ "
        f"(cache: {fmt(totals['cache_write'])}↑, {fmt(totals['cache_read'])}↓)"
    )


def parse_merge_warnings(text):
    """Parse spec_merge.py's ``--json`` warning summary (one JSON object per
    line, each carrying at least ``id`` and ``kind``) into a list of dicts.

    Best-effort: blank lines and unparseable lines are skipped, and anything
    that is not a dict with an ``id``/``kind`` is ignored, so a malformed
    summary never raises."""
    warnings = []
    if not text:
        return warnings
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict) and obj.get("id") and obj.get("kind"):
            warnings.append(obj)
    return warnings


def load_merge_warnings(source):
    """Load the merge warning summary from ``source`` — a file path, or ``-``
    to read stdin. Returns a list of warning dicts. Never raises: on any I/O or
    parse problem it returns an empty list (telemetry is best-effort)."""
    if not source:
        return []
    try:
        if source == "-":
            text = sys.stdin.read()
        else:
            with open(source, "r", encoding="utf-8") as f:
                text = f.read()
    except OSError:
        return []
    return parse_merge_warnings(text)


def render_warnings(warnings):
    """Render the spec-merge warnings block: one ``⚠ spec:`` line per warning
    naming the requirement ``id`` and the warning ``kind``. Returns an empty
    string when there are no warnings, so the caller omits the block entirely."""
    if not warnings:
        return ""
    return "\n".join(
        "⚠ spec: %s — %s" % (w.get("id"), w.get("kind"))
        for w in warnings
    )


def render_table(by_model, totals, total_time, by_model_time):
    """Render the per-model markdown table (+ Total row, + Total time
    line) per the archived build-report design D1/D2. Columns are
    ``Model | Tokens ↑ | Tokens ↓ | Token % | Time``: Token % is the model's
    share of the build's total non-cached output tokens as a whole percent
    (Total row 100%; all rows 0% when total output is zero). Assumes tokens
    are available (caller checks). Degrades gracefully by dropping the Time
    column and the total-time line when timing is unavailable
    (total_time is None).
    """
    have_time = total_time is not None and by_model_time is not None
    models = list(by_model.keys())
    if have_time:
        models.sort(key=lambda m: by_model_time.get(m, 0.0), reverse=True)
    else:
        # No timing signal to sort by; fall back to total token volume
        # (largest contribution first), mirroring the time-descending intent.
        models.sort(key=lambda m: sum(by_model[m].values()), reverse=True)

    total_output = totals["output"]

    def token_pct(output):
        return round(100 * output / total_output) if total_output else 0

    if have_time:
        header = "| Model | Tokens ↑ | Tokens ↓ | Token % | Time |"
        sep = "| --- | --- | --- | --- | --- |"
    else:
        header = "| Model | Tokens ↑ | Tokens ↓ | Token % |"
        sep = "| --- | --- | --- | --- |"

    lines = [header, sep]
    for m in models:
        b = by_model[m]
        row = [
            m,
            human(b["non_cached_input"]),
            human(b["output"]),
            f"{token_pct(b['output'])}%",
        ]
        if have_time:
            t = by_model_time.get(m, 0.0)
            row.append(human_duration(t))
        lines.append("| " + " | ".join(row) + " |")

    total_row = [
        "**Total**",
        human(totals["non_cached_input"]),
        human(totals["output"]),
        "100%" if total_output else "0%",
    ]
    if have_time:
        total_row.append(human_duration(total_time))
    lines.append("| " + " | ".join(total_row) + " |")

    rendered = "\n".join(lines)
    if have_time:
        rendered += f"\n\nTotal time: {human_duration(total_time)}"
    return rendered


# --- build config (the `build` key of the resolved layered configuration,
#     typically declared in ~/.shipd-config.json) ----------------------------

DEFAULT_BUILD_CONFIG = {
    "logging_enabled": True,
    "log_dir": "~/.shipd/builds",
    "number_format": "short",
    "parallelism": 3,
}


def build_config(project_dir="."):
    """Return the effective build settings: the resolved layered
    configuration's ``build`` key merged over the documented defaults
    (build-reporting user-configuration-file).

    Read-only — a missing config, a missing ``build`` key, or an unreadable
    config yields the defaults, so the build always proceeds."""
    settings = dict(DEFAULT_BUILD_CONFIG)
    try:
        config, _prov = sc.resolve_config(os.path.abspath(project_dir))
    except sc.ConfigError:
        return settings
    build = config.get("build")
    if isinstance(build, dict):
        settings.update(build)
    return settings


def build_log_dir(config):
    """Return the resolved build log directory (default ``~/.shipd/builds``),
    home-expanded (build-reporting persistent-build-log)."""
    return os.path.expanduser(
        config.get("log_dir") or DEFAULT_BUILD_CONFIG["log_dir"])


def write_log_entry(entry, config):
    """Write the per-build JSON file and append to ``builds.jsonl``, both under
    the resolved build log directory (created on demand). No ``~/.am/`` or
    ``~/.automikk/`` path is read or written (build-reporting
    persistent-build-log)."""
    log_dir = build_log_dir(config)
    os.makedirs(log_dir, exist_ok=True)
    ts_compact = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    change = entry.get("change") or "build"
    per_build_path = os.path.join(log_dir, f"{ts_compact}-{change}.json")
    with open(per_build_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)
        f.write("\n")
    jsonl_path = os.path.join(log_dir, "builds.jsonl")
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build token telemetry for /s:build.")
    parser.add_argument("--since", help="ISO8601 timestamp; only count records at/after this time")
    parser.add_argument("--project-dir", default=".", help="project root (default: cwd)")
    parser.add_argument("--session", help="override: use this session id instead of the newest")
    parser.add_argument("--transcript", help="override: use this main transcript path directly")
    parser.add_argument("--json", action="store_true", help="print full JSON structure")
    parser.add_argument("--summary-only", action="store_true", help="print just the Tokens: line")
    parser.add_argument(
        "--table",
        action="store_true",
        help="print the per-model token+time markdown table and Total time line",
    )
    parser.add_argument(
        "--merge-warnings",
        help="path to spec_merge.py --json warning summary (- for stdin); "
             "rendered as ⚠ spec: lines and recorded in the --log entry",
    )
    parser.add_argument(
        "--warnings",
        action="store_true",
        help="print the ⚠ spec: merge-warnings block from --merge-warnings "
             "(nothing when there are no warnings)",
    )
    # --log mode metadata
    parser.add_argument("--log", action="store_true", help="write a persistent build log entry")
    parser.add_argument("--change", help="change name (for --log)")
    parser.add_argument("--schema", help="schema/version label (for --log)")
    parser.add_argument("--tasks-done", type=int, help="tasks completed (for --log)")
    parser.add_argument("--tasks-total", type=int, help="tasks total (for --log)")
    parser.add_argument("--status", help="build status (for --log)")
    parser.add_argument("--commit", help="commit hash (for --log)")
    args = parser.parse_args()

    try:
        since_dt = parse_since(args.since)
    except ValueError:
        print(f"Warning: could not parse --since {args.since!r}; ignoring.", file=sys.stderr)
        since_dt = None

    # Merge warnings are independent of transcripts; load best-effort so a bad
    # summary never blocks the report.
    merge_warnings = load_merge_warnings(args.merge_warnings)

    by_model = None
    session_id = None
    total_time = None
    by_model_time = None
    try:
        if args.transcript:
            main_path = args.transcript
            session_id = args.session or os.path.basename(main_path).removesuffix(".jsonl")
            paths = [main_path] if os.path.isfile(main_path) else []
            tdir = transcript_dir(args.project_dir)
            if session_id:
                paths += subagent_transcripts(tdir, session_id)
        else:
            tdir = transcript_dir(args.project_dir)
            session_id, main_path = find_active_session(tdir, args.session)
            paths = []
            if main_path and os.path.isfile(main_path):
                paths.append(main_path)
            if session_id:
                paths += subagent_transcripts(tdir, session_id)

        if paths:
            by_model, timeline = aggregate(paths, since_dt)
            total_time, by_model_time = compute_timing(timeline, since_dt)
    except Exception as exc:  # never fail the build on telemetry errors
        print(f"Warning: telemetry collection failed: {exc}", file=sys.stderr)
        by_model = None
        total_time = None
        by_model_time = None

    # by_model is None when no transcript files were found (or collection
    # failed); it is {} (falsy but not None) when transcripts exist but no
    # record matched the --since window — that's a legitimate zero, not
    # "unavailable".
    unavailable = by_model is None
    totals = totals_of(by_model) if by_model is not None else None

    number_format = "short"
    config = None
    if args.log:
        try:
            config = build_config(args.project_dir)
            number_format = config.get("number_format", "short")
        except Exception as exc:
            print(f"Warning: could not resolve build configuration: {exc}", file=sys.stderr)
            config = dict(DEFAULT_BUILD_CONFIG)

    if args.json:
        out = {
            "totals": totals,
            "by_model": by_model or {},
            "since": args.since,
            "session": session_id,
            "time": {
                "total_seconds": total_time,
                "by_model": by_model_time or {},
            },
            "merge_warnings": merge_warnings,
        }
        print(json.dumps(out, indent=2))
    elif args.warnings:
        # Print the ⚠ spec: block, or nothing at all when the merge was clean.
        block = render_warnings(merge_warnings)
        if block:
            print(block)
    elif args.table:
        if unavailable:
            print("Tokens: unavailable (transcripts not found)")
        else:
            try:
                print(render_table(by_model, totals, total_time, by_model_time))
            except Exception as exc:  # never fail the build on rendering errors
                print(f"Warning: table rendering failed: {exc}", file=sys.stderr)
                print(summary_line(totals, number_format))
    else:
        if unavailable:
            print("Tokens: unavailable (transcripts not found)")
        else:
            print(summary_line(totals, number_format))

    if args.log:
        try:
            if config is None:
                config = build_config(args.project_dir)
            if config.get("logging_enabled", True):
                entry = {
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "change": args.change,
                    "schema": args.schema,
                    "tasks": {"done": args.tasks_done, "total": args.tasks_total},
                    "status": args.status,
                    "commit": args.commit,
                    "tokens": {
                        "totals": totals,
                        "by_model": by_model or {},
                    },
                    "time": {
                        "total_seconds": total_time,
                        "by_model": by_model_time or {},
                    },
                    "merge_warnings": merge_warnings,
                    "since": args.since,
                }
                write_log_entry(entry, config)
        except Exception as exc:
            print(f"Warning: could not write build log: {exc}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
