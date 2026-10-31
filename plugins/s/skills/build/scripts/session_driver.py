#!/usr/bin/env python3
"""session_driver.py — a shared, grade-gated headless-session resume loop.

One driving idiom, two consumers: the eval harness (``evals/run.py``) and the
epic autopilot (``autopilot.py``). Both drive a headless ``claude -p`` session
in a working directory and, while a supplied grade has not yet passed, resume
the same session with a canned reply — bounded by a resume budget.

Entry points:

* :func:`run_turn` runs a single headless turn, returning ``(ok, failure,
  session_id)``. The session id is parsed from the turn's JSON transcript so a
  human can later reopen the exact conversation with ``claude --resume <id>``.
* :func:`run_turn_result` is :func:`run_turn` plus the turn's ``result`` text
  as a fourth element (``""`` on any failure); ``run_turn`` returns the first
  three unchanged.
* :func:`preflight` probes that a harness is signed in with one minimal
  turn, returning ``(ok, failure)``.
* :func:`drive` runs the grade-gated loop over an injectable turn ``runner``
  (default :func:`run_turn`), returning ``(ok, session_id, failure)``. The
  ``runner`` seam makes the loop unit-testable without a live session.

Standard library only — no third-party imports, no network beyond the
``claude`` subprocess :func:`run_turn` spawns.
"""

from __future__ import annotations

import json
import os
import re
import subprocess


# Default resume budget: how many resumed turns a run may spend answering a
# session's stops before the grade decides the outcome.
MAX_RESUMES_DEFAULT = 4

# Default per-turn wall-clock budget (seconds).
TIMEOUT_DEFAULT = 1800

# The sign-in probe: one tiny prompt and a short wall-clock budget.
PREFLIGHT_PROMPT = "Reply with the single word ok."
PREFLIGHT_TIMEOUT = 120


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


def result_text_from_transcript(text):
    """Return the string ``result`` field of a turn's JSON transcript, or
    ``""`` when the text is not JSON or carries no string ``result``."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return ""
    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, str):
            return result
    return ""


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


# The harness runner registry: one record per supported harness, each carrying
# its default binary, an ``argv`` builder, a transcript ``parse``, and a prompt
# ``rewrite``. A harness is data here, never a branch in the resume loop, so a
# new harness is one record.
#
# ``argv(binary, prompt, resume_id, model, plugin_dir, extra_args)`` returns the
# full command line; ``parse(stdout)`` returns ``(session_id, result_text)``;
# ``rewrite(prompt)`` maps the ``/s:`` command vocabulary to the harness's own
# command names.

# The ``/s:`` command vocabulary a stage prompt carries, e.g. ``/s:plan``.
_S_COMMAND_RE = re.compile(r"/s:([a-z0-9-]+)")

DEFAULT_HARNESS = "claude"


# The effort levels a runner expresses with its harness's own knob. Mirrors
# ``spec_common.EFFORT_LEVELS``; declared here so the driver stays importable
# with no engine module beside it.
EFFORT_LEVELS = ("high", "medium", "low")


def _effort_args(effort, model_base, variant):
    """The model/effort flags a harness takes for ``effort``.

    A concrete model id (any non-empty string that is not an effort level and
    not ``session``) becomes ``--model <id>``. An effort level becomes
    ``--effort <level>`` when ``variant`` is False, or ``--model
    <base>#<level>`` when it is True and a base is declared. ``session`` and
    ``None`` yield no flag, so the harness's own default decides."""
    if not effort or effort == "session":
        return []
    if effort not in EFFORT_LEVELS:
        return ["--model", effort]
    if variant:
        return ["--model", "%s#%s" % (model_base, effort)] if model_base else []
    return ["--effort", effort]


def _claude_argv(binary, prompt, resume_id, effort, model_base, plugin_dir,
                 extra_args):
    cmd = [binary, "-p", prompt, "--output-format", "json"]
    if plugin_dir:
        cmd += ["--plugin-dir", plugin_dir]
    cmd += ["--permission-mode", "bypassPermissions"]
    cmd += _effort_args(effort, model_base, variant=False)
    if resume_id is not None:
        cmd += ["--resume", resume_id]
    if extra_args:
        cmd += list(extra_args)
    return cmd


def _claude_parse(stdout):
    """The Claude transcript: one JSON object carrying ``session_id`` and
    ``result``."""
    return (session_id_from_transcript(stdout),
            result_text_from_transcript(stdout))


def _identity(prompt):
    return prompt


def _opencode_argv(binary, prompt, resume_id, effort, model_base, plugin_dir,
                   extra_args):
    cmd = [binary, "run", "--format", "json", "--auto"]
    cmd += _effort_args(effort, model_base, variant=True)
    if resume_id is not None:
        cmd += ["--session", resume_id]
    if extra_args:
        cmd += list(extra_args)
    cmd.append(prompt)
    return cmd


def _opencode_parse(stdout):
    """OpenCode's JSONL transcript: the last top-level ``sessionID``, and the
    concatenated ``part.text`` of every ``type == "text"`` line."""
    session_id = None
    texts = []
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        sid = data.get("sessionID")
        if isinstance(sid, str) and sid:
            session_id = sid
        part = data.get("part")
        if (data.get("type") == "text" and isinstance(part, dict)
                and isinstance(part.get("text"), str)):
            texts.append(part["text"])
    return session_id, "".join(texts)


def _opencode_rewrite(prompt):
    """Map each ``/s:<command>`` token to the OpenCode command the harness
    installer writes, ``/shipd-<command>``."""
    return _S_COMMAND_RE.sub(lambda m: "/shipd-%s" % m.group(1), prompt)


RUNNERS = {
    "claude": {
        "binary": "claude",
        "argv": _claude_argv,
        "parse": _claude_parse,
        "rewrite": _identity,
        "login": "claude auth login",
    },
    "opencode": {
        "binary": "opencode",
        "argv": _opencode_argv,
        "parse": _opencode_parse,
        "rewrite": _opencode_rewrite,
        "login": "opencode auth login",
    },
}


class UnknownHarnessError(ValueError):
    """Raised by :func:`runner_for` for an id no runner declares."""

    def __init__(self, harness_id):
        super().__init__("unknown harness %r — known: %s"
                         % (harness_id, ", ".join(sorted(RUNNERS))))
        self.harness_id = harness_id


def runner_for(harness_id):
    """The runner record ``harness_id`` names, or raise
    :class:`UnknownHarnessError`."""
    try:
        return RUNNERS[harness_id]
    except KeyError:
        raise UnknownHarnessError(harness_id)


def login_hint(harness):
    """The sign-in command ``harness`` names, for a signed-out failure."""
    return runner_for(harness)["login"]


def run_turn(prompt, cwd, resume_id=None, timeout=TIMEOUT_DEFAULT,
             harness=DEFAULT_HARNESS, binary=None, effort=None,
             model_base=None, plugin_dir=None, extra_args=None, env=None):
    """Run one headless turn; return ``(ok, failure, session_id)``.

    See :func:`run_turn_result`, which this wraps."""
    return run_turn_result(prompt, cwd, resume_id=resume_id, timeout=timeout,
                           harness=harness, binary=binary, effort=effort,
                           model_base=model_base, plugin_dir=plugin_dir,
                           extra_args=extra_args, env=env)[:3]


def run_turn_result(prompt, cwd, resume_id=None, timeout=TIMEOUT_DEFAULT,
                    harness=DEFAULT_HARNESS, binary=None, effort=None,
                    model_base=None, plugin_dir=None, extra_args=None,
                    env=None):
    """Run one headless turn of a ``harness`` conversation inside ``cwd``.

    The runner ``harness`` names builds the argv, parses the transcript, and
    rewrites the ``/s:`` command vocabulary; ``binary`` defaults to that
    runner's own executable.

    Returns ``(ok, failure, session_id, result_text)``: ``ok`` is True only
    when the CLI exits 0 within ``timeout``; ``session_id`` is parsed from the
    turn's transcript (``None`` when unavailable). ``failure`` names the fault
    when ``ok`` is False, else ``None``; ``result_text`` is the transcript's
    result text (``""`` on every failure path).

    ``env`` is an optional mapping overlaid on the current process environment
    for the session subprocess; ``None`` inherits the environment unchanged.
    """
    runner = runner_for(harness)
    argv = runner["argv"](binary or runner["binary"],
                          runner["rewrite"](prompt), resume_id, effort,
                          model_base, plugin_dir, extra_args)
    try:
        proc = subprocess.run(
            argv, cwd=cwd, timeout=timeout, text=True,
            env=None if env is None else {**os.environ, **env},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        return False, "session timed out after %d s" % timeout, None, ""
    except OSError as exc:
        return False, "working directory missing: %s: %s" % (cwd, exc), None, ""
    if proc.returncode != 0:
        detail = _failure_detail(proc.stdout or "", proc.stderr or "")
        return (False, "session CLI exited %d: %s" % (proc.returncode, detail),
                None, "")
    session_id, result_text = runner["parse"](proc.stdout or "")
    return True, None, session_id, result_text


def preflight(cwd, harness=DEFAULT_HARNESS, binary=None, effort=None,
              model_base=None, timeout=PREFLIGHT_TIMEOUT):
    """Probe that ``harness`` is signed in with one minimal turn.

    Returns ``(ok, failure)`` — the first two elements of
    :func:`run_turn_result` on :data:`PREFLIGHT_PROMPT`, with no resume, no
    plugin dir, and no extra arguments."""
    return run_turn_result(PREFLIGHT_PROMPT, cwd, timeout=timeout,
                           harness=harness, binary=binary, effort=effort,
                           model_base=model_base)[:2]


def _default_runner(prompt, cwd, resume_id, turn_index, timeout=TIMEOUT_DEFAULT,
                    harness=DEFAULT_HARNESS, binary=None, effort=None,
                    model_base=None, plugin_dir=None, extra_args=None):
    """Adapt :func:`run_turn` to the :func:`drive` runner contract, which
    passes a ``turn_index`` the plain turn function does not need."""
    return run_turn(prompt, cwd, resume_id=resume_id, timeout=timeout,
                    harness=harness, binary=binary, effort=effort,
                    model_base=model_base, plugin_dir=plugin_dir,
                    extra_args=extra_args)


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
