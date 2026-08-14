#!/usr/bin/env python3
"""heartbeat.py — the autopilot's live run heartbeat writer, stdlib only.

:class:`RunHeartbeat` is the writer the autopilot threads through a run. Each
transition (run start, member start, stage attempt, member outcome, run end)
mutates one state dict and rewrites
``<content-dir>/autopilot/<epic>-heartbeat.json`` atomically (temp file +
``os.replace``) with a monotonic ``seq`` and an epoch ``updated_at``. A write
failure never fails the run: it warns once through ``out`` and disables
further writes.

Kept separate from ``dashboard.py`` (which imports ``textual`` for its board
rendering) so importing the delivery engine (``autopilot``) never requires a
third-party package.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import spec_common as sc  # noqa: E402


def _noop(*_args, **_kwargs):
    pass


# Map a MemberResult outcome to its live roster state (hyphenated for display).
_OUTCOME_STATE = {
    "shipped": "shipped",
    "rejected": "rejected",
    "needs_human": "needs-human",
}


def heartbeat_path(root, epic):
    """The heartbeat file for ``epic`` under ``root``'s content directory."""
    return os.path.join(sc.specs_dir(root), "autopilot",
                        "%s-heartbeat.json" % epic)


def build_heartbeat_path(root, slug):
    """The interactive build heartbeat file for change ``slug`` under ``root``'s
    content directory: ``<content-dir>/autopilot/<slug>-build-heartbeat.json``.

    The ``-build-heartbeat`` suffix keeps it distinct from an epic's
    ``<epic>-heartbeat.json`` in the same (git-ignored) ``autopilot/``
    directory, so an interactive build and its epic never collide."""
    return os.path.join(sc.specs_dir(root), "autopilot",
                        "%s-build-heartbeat.json" % slug)


class RunHeartbeat:
    """Live run state, rewritten atomically on every transition.

    Constructed by ``autopilot.run`` for a real (not ``--dry-run``) run and
    threaded into ``drive_member``. Every write is guarded: the first failure
    warns once through ``out`` and disables further writes so a heartbeat
    problem never fails the run.
    """

    def __init__(self, root, epic, out=None):
        self.root = root
        self.epic = epic
        self._out = out or _noop
        self._seq = 0
        self._disabled = False
        self._warned = False
        self._state = {
            "epic": epic,
            "state": "running",
            "provenance": None,
            "seq": 0,
            "updated_at": 0.0,
            "report": None,
            "roster": [],
            "pid": os.getpid(),
            "host": socket.gethostname(),
        }

    # -- roster mutation --------------------------------------------------

    def _entry(self, slug):
        for entry in self._state["roster"]:
            if entry["slug"] == slug:
                return entry
        return None

    def run_started(self, to_drive, skipped, provenance):
        """Seed the roster: every ``to_drive`` member ``pending``, every
        ``skipped`` member carrying the state that excluded it."""
        roster = [
            {"slug": m.slug, "risk": m.risk, "state": "pending"}
            for m in to_drive]
        roster += [
            {"slug": m.slug, "risk": m.risk, "state": "skipped",
             "skipped_state": m.state}
            for m in skipped]
        self._state["roster"] = roster
        self._state["provenance"] = provenance
        self._state["state"] = "running"
        self._write()

    def member_started(self, slug):
        entry = self._entry(slug)
        if entry is not None:
            entry["state"] = "driving"
            # Stamp the start timestamp once, left unchanged on later stage
            # re-attempts, so elapsed reflects the member's first start.
            if "started_at" not in entry:
                entry["started_at"] = time.time()
        self._write()

    def stage_started(self, slug, stage, attempt):
        entry = self._entry(slug)
        if entry is not None:
            entry["state"] = "driving"
            entry["stage"] = stage
            entry["attempt"] = attempt
        self._write()

    def member_session(self, slug, session_id):
        """Record ``session_id`` on the member's roster entry as soon as a
        driven turn first yields one — before any terminal outcome — so a
        `driving` card already carries a resume handle. A falsy id is ignored."""
        if not session_id:
            return
        entry = self._entry(slug)
        if entry is not None:
            entry["session_id"] = session_id
        self._write()

    def member_finished(self, slug, result):
        entry = self._entry(slug)
        if entry is not None:
            entry["state"] = _OUTCOME_STATE.get(result.outcome, result.outcome)
            # A terminal outcome supersedes the mid-drive stage/attempt.
            entry.pop("stage", None)
            entry.pop("attempt", None)
            if getattr(result, "stage", None):
                entry["stage"] = result.stage
            if getattr(result, "reason", None):
                entry["reason"] = result.reason
            if getattr(result, "session_id", None):
                entry["session_id"] = result.session_id
            if getattr(result, "pr_url", None):
                entry["pr_url"] = result.pr_url
        self._write()

    def run_finished(self, report_path):
        self._state["state"] = "finished"
        self._state["report"] = report_path
        self._write()

    def run_aborted(self):
        """Write a terminal ``aborted`` run state — mirrors ``run_finished``
        but with no report, for a catchably-terminated run (a raised
        ``AutopilotError`` or a received ``SIGTERM``/``SIGINT``) that never
        reaches the clean run-end write."""
        self._state["state"] = "aborted"
        self._write()

    # -- atomic write -----------------------------------------------------

    def _write(self):
        if self._disabled:
            return
        self._seq += 1
        self._state["seq"] = self._seq
        self._state["updated_at"] = time.time()
        try:
            path = heartbeat_path(self.root, self.epic)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = "%s.tmp.%d" % (path, os.getpid())
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._state, fh, indent=2, sort_keys=True)
            os.replace(tmp, path)
        except OSError as exc:
            self._disabled = True
            if not self._warned:
                self._warned = True
                self._out(
                    "Warning: heartbeat write failed (%s); disabling further "
                    "heartbeat writes for this run." % exc)


# ---------------------------------------------------------------------------
# Interactive build heartbeat — stateless read-modify-write CLI verbs
# ---------------------------------------------------------------------------
#
# An interactive `/s:build` session is an LLM, not a resident process, so its
# heartbeat is maintained by three stateless CLI verbs the build skill invokes
# at build start, at each stage transition, and on completion. Each verb loads
# the existing file (when present), applies its transition, bumps the monotonic
# `seq`, stamps `updated_at`, and atomically replaces the file with the same
# temp-file + `os.replace` shape as `RunHeartbeat._write`. Every verb is
# fail-soft: a write failure warns on stderr and still exits zero — a heartbeat
# problem never blocks a build.


def _load_build_state(path):
    """The existing build-heartbeat dict at ``path``, or ``{}`` when it is
    absent or unreadable — a corrupt or missing file simply starts fresh
    rather than raising."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_build_heartbeat(root, slug, mutate, location, session_id, out):
    """Read-modify-write the build heartbeat for ``slug``: load the existing
    state, let ``mutate`` apply the verb's transition, re-stamp the invariant
    identity fields (slug, ``kind: build``, location, session id), bump ``seq``
    and ``updated_at``, and atomically replace the file. Any ``OSError`` — and
    a ``ConfigError`` from a malformed layered config while resolving the
    path — warns through ``out`` and returns without raising (the caller still
    exits zero)."""
    try:
        path = build_heartbeat_path(root, slug)
    except sc.ConfigError as exc:
        out("Warning: build heartbeat write failed (%s); the build continues."
            % exc)
        return
    state = _load_build_state(path)
    mutate(state)
    state["slug"] = slug
    state["kind"] = "build"
    state["location"] = location
    if session_id:
        state["session_id"] = session_id
    else:
        state.pop("session_id", None)
    state["seq"] = int(state.get("seq") or 0) + 1
    state["updated_at"] = time.time()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.tmp.%d" % (path, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        os.replace(tmp, path)
    except OSError as exc:
        out("Warning: build heartbeat write failed (%s); the build continues."
            % exc)


def _build_start(state):
    state["state"] = "running"
    state.pop("stage", None)
    state.pop("outcome", None)
    # Stamp the start timestamp once, so elapsed time is measured from the
    # build's first start and survives a repeated build-start.
    if "started_at" not in state:
        state["started_at"] = time.time()


def main(argv=None):
    """The build-heartbeat CLI: ``build-start``/``build-stage``/``build-finish``
    verbs writing ``<content-dir>/autopilot/<slug>-build-heartbeat.json``.
    Always exits zero — a heartbeat failure never blocks a build."""
    parser = argparse.ArgumentParser(
        description="Interactive build heartbeat writer (fail-soft).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("build-start", "build-stage", "build-finish"):
        p = sub.add_parser(name)
        p.add_argument("slug")
        p.add_argument("--root", default=None,
                       help="content-dir root (default: cwd)")
        p.add_argument("--location", default=None,
                       help="session location (default: cwd abspath)")
        p.add_argument(
            "--session-id",
            default=os.environ.get("CLAUDE_CODE_SESSION_ID"),
            help="session id (default: $CLAUDE_CODE_SESSION_ID)")
        if name == "build-stage":
            p.add_argument("--stage", required=True)
        if name == "build-finish":
            p.add_argument("--outcome", default=None)
    args = parser.parse_args(argv)

    root = args.root or os.getcwd()
    location = args.location or os.path.abspath(os.getcwd())
    session_id = args.session_id

    def out(msg):
        print(msg, file=sys.stderr)

    if args.cmd == "build-start":
        mutate = _build_start
    elif args.cmd == "build-stage":
        def mutate(state):
            state["state"] = "running"
            state["stage"] = args.stage
    else:  # build-finish
        def mutate(state):
            state["state"] = "finished"
            if args.outcome:
                state["outcome"] = args.outcome

    _write_build_heartbeat(root, args.slug, mutate, location, session_id, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
