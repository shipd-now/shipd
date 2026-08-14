#!/usr/bin/env python3
"""session_driver.py — a shared, grade-gated headless-session resume loop.

One driving idiom, two consumers: the eval harness (``evals/run.py``) and the
epic autopilot (``autopilot.py``). Both drive a headless ``claude -p`` session
in a working directory and, while a supplied grade has not yet passed, resume
the same session with a canned reply — bounded by a resume budget.

Two entry points:

* :func:`run_turn` runs a single headless turn, returning ``(ok, failure,
  session_id)``. The session id is parsed from the turn's JSON transcript so a
  human can later reopen the exact conversation with ``claude --resume <id>``.
* :func:`drive` runs the grade-gated loop over an injectable turn ``runner``
  (default :func:`run_turn`), returning ``(ok, session_id, failure)``. The
  ``runner`` seam makes the loop unit-testable without a live session.

Standard library only — no third-party imports, no network beyond the
``claude`` subprocess :func:`run_turn` spawns.
"""

from __future__ import annotations

import json
import subprocess


# Default resume budget: how many resumed turns a run may spend answering a
# session's stops before the grade decides the outcome.
MAX_RESUMES_DEFAULT = 4

# Default per-turn wall-clock budget (seconds).
TIMEOUT_DEFAULT = 1800


def session_id_from_transcript(text):
    """Return the ``session_id`` from a turn's JSON transcript, or ``None``
    when the text is not JSON or carries no such field."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if isinstance(data, dict):
        sid = data.get("session_id")
        if isinstance(sid, str) and sid:
            return sid
    return None


def _failure_detail(stdout, stderr):
    """Best-effort human-readable reason a non-zero ``claude -p`` turn failed.

    The ``claude`` CLI prints transient API/connection faults (e.g. "Connection
    closed mid-response") to *stdout* as the turn's JSON result — its
    ``result``/``error``/``subtype`` fields — leaving stderr empty, so a
    stderr-only reading records a blank. Prefer the last non-empty stderr line;
    otherwise mine the stdout JSON; otherwise name the class of fault rather
    than returning an empty string."""
    err_lines = (stderr or "").strip().splitlines()
    if err_lines:
        return err_lines[-1]
    text = (stdout or "").strip()
    if text:
        try:
            data = json.loads(text.splitlines()[-1])
        except (ValueError, TypeError):
            data = None
        if isinstance(data, dict):
            for key in ("result", "error", "subtype"):
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip().replace("\n", " ")[:200]
        # Non-JSON stdout: surface its tail rather than nothing.
        return text.splitlines()[-1][:200]
    return "no CLI diagnostics (likely a transient API/connection error)"


def run_turn(prompt, cwd, resume_id=None, timeout=TIMEOUT_DEFAULT,
             claude_bin="claude", extra_args=None):
    """Run one headless turn of a ``claude`` conversation inside ``cwd``.

    Launches ``<claude_bin> -p <prompt> --output-format json`` — plus any
    ``extra_args`` (e.g. ``--plugin-dir``, ``--permission-mode``) and
    ``--resume <resume_id>`` when continuing an existing session.

    Returns ``(ok, failure, session_id)``: ``ok`` is True only when the CLI
    exits 0 within ``timeout``; ``session_id`` is parsed from the turn's JSON
    transcript (``None`` when unavailable). ``failure`` names the fault when
    ``ok`` is False, else ``None``.
    """
    cmd = [claude_bin, "-p", prompt, "--output-format", "json"]
    if extra_args:
        cmd += list(extra_args)
    if resume_id is not None:
        cmd += ["--resume", resume_id]
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, timeout=timeout, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        return False, "session timed out after %d s" % timeout, None
    except OSError as exc:
        return False, "working directory missing: %s: %s" % (cwd, exc), None
    if proc.returncode != 0:
        detail = _failure_detail(proc.stdout or "", proc.stderr or "")
        return (False, "session CLI exited %d: %s" % (proc.returncode, detail),
                None)
    return True, None, session_id_from_transcript(proc.stdout or "")


def _default_runner(prompt, cwd, resume_id, turn_index, timeout=TIMEOUT_DEFAULT,
                    claude_bin="claude", extra_args=None):
    """Adapt :func:`run_turn` to the :func:`drive` runner contract, which
    passes a ``turn_index`` the plain turn function does not need."""
    return run_turn(prompt, cwd, resume_id=resume_id, timeout=timeout,
                    claude_bin=claude_bin, extra_args=extra_args)


def drive(prompt, cwd, grade_fn, reply, max_resumes=MAX_RESUMES_DEFAULT,
          timeout=TIMEOUT_DEFAULT, runner=None, on_session=None):
    """Drive a grade-gated headless conversation inside ``cwd``.

    Turn 1 sends ``prompt``. Afterwards, while ``grade_fn()`` has not passed
    and fewer than ``max_resumes`` resumed turns have run, the same session is
    resumed with ``reply``. Resuming stops early when a turn yields no session
    id (nothing left to resume) — the final grade then decides the run.

    ``runner`` is the injectable turn function, contract ``runner(prompt, cwd,
    resume_id, turn_index, **kwargs) -> (ok, failure, session_id)`` (default
    :func:`run_turn` via :func:`_default_runner`).

    ``on_session`` (optional) is a callback fired exactly once, with the session
    id, the first time any turn yields a non-None one — so a caller can record
    the resume handle mid-drive rather than only at the terminal outcome.

    Returns ``(ok, session_id, failure)``: ``ok`` is False only when a turn
    itself failed (timeout / non-zero exit); grading verdicts are the caller's
    job. ``session_id`` is the most recent one seen, so an exhausted run still
    carries an id for interactive resume.
    """
    runner = runner or _default_runner
    notified = False
    ok, failure, session_id = runner(prompt, cwd, None, 1, timeout=timeout)
    if session_id is not None and on_session is not None:
        on_session(session_id)
        notified = True
    if not ok:
        return False, session_id, failure
    for i in range(2, max_resumes + 2):
        if grade_fn():
            break
        if session_id is None:
            break
        ok, failure, next_session_id = runner(
            reply, cwd, session_id, i, timeout=timeout)
        if next_session_id is not None:
            session_id = next_session_id
            if not notified and on_session is not None:
                on_session(session_id)
                notified = True
        if not ok:
            return False, session_id, failure
    return True, session_id, None
