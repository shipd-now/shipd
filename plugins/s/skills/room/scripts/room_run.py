#!/usr/bin/env python3
"""room_run — ``shipd room run``: a local loop over one pull request's room.

The run joins this agent's card once, then waits with ``watch`` (no model
call) and runs one resumed headless ``/s:room`` turn per task addressed to
it, until the pull request closes or a cap is hit. It prints one JSON summary
line on stdout; progress goes to stderr.

``room.py`` imports this module lazily for the ``run`` verb only, because the
Actions wake bundles ``room.py`` without ``session_driver``.
"""

import argparse
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))
if BUILD_SCRIPTS not in sys.path:
    sys.path.insert(0, BUILD_SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cli_common  # noqa: E402
import room  # noqa: E402
import session_driver  # noqa: E402
import spec_common  # noqa: E402

PLUGIN_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_SKILLS = ("review-finding", "question", "status")
FAILURE_REASONS = ("turn-failed", "watch-failed")


def _default_runner(opts, root):
    """The turn runner wrapping ``session_driver.run_turn``; no ``env`` is
    passed, so the process environment reaches the spawned session."""
    try:
        model_base = spec_common.resolve_model_base(
            spec_common.resolve_config(root)[0])
    except spec_common.ConfigError as exc:
        raise room.RoomError(str(exc))

    def runner(prompt, cwd, resume_id, turn_index):
        return session_driver.run_turn(
            prompt, cwd, resume_id=resume_id, timeout=opts.turn_timeout,
            harness=opts.harness, effort=opts.model, model_base=model_base,
            plugin_dir=PLUGIN_DIR)

    return runner


def _check_identity(gh, number, repo, role):
    """Read the acting login and the PR author; refuse a reviewer or ci on
    the author's own account. Returns the login."""
    login = room._login(gh, {})
    author = room._pr_author(gh, number, repo)
    if not login:
        raise room.RoomError(
            "could not read the acting GitHub login (gh api user failed); "
            "an approval needs a readable account")
    if role in ("reviewer", "ci"):
        if not author:
            raise room.RoomError(
                "could not read the author of %s#%d; an approval needs a "
                "known author" % (repo, number))
        if login.lower() == author.lower():
            raise room.RoomError(
                "acting as @%s, who authored %s#%d; an author cannot "
                "approve their own pull request" % (login, repo, number))
    elif author and login.lower() != author.lower():
        sys.stderr.write(
            "warning: acting as @%s, but %s#%d was authored by @%s\n"
            % (login, repo, number, author))
    return login


def _summary(turns, session_id, reason, context, cursor, closed=None,
             failure=None):
    out = {"turns": turns, "session_id": session_id, "reason": reason,
           "context": context, "cursor": room._cursor_text(cursor)}
    if reason == "closed":
        out["closed"] = closed
    if reason in FAILURE_REASONS:
        out["failure"] = failure
    return out


def cmd_run(opts, parser, gh, runner, sleep, clock):
    # The parser leaves these unset so ``room.py`` never imports
    # ``session_driver`` itself.
    opts.harness = opts.harness or session_driver.DEFAULT_HARNESS
    if opts.turn_timeout is None:
        opts.turn_timeout = session_driver.TIMEOUT_DEFAULT
    try:
        session_driver.runner_for(opts.harness)
    except session_driver.UnknownHarnessError as exc:
        parser.error(str(exc))
    if not opts.interval > 0:
        parser.error("--interval must be greater than 0, got %s"
                     % opts.interval)
    root = room._root(opts)
    agent = room._agent_name(opts, parser, root)
    repo, number, context = room._resolve_room(gh, opts.pr, opts.repo)
    login = _check_identity(gh, number, repo, opts.role)
    sys.stderr.write("room run: acting as @%s (%s)\n" % (
        login, room._credential_source(os.environ)))
    url = room._gh_json(
        gh, ["pr", "view", str(number), "--json", "url", "--repo", repo],
        what="gh pr view %s" % number)
    try:
        url = url["url"]
    except (KeyError, TypeError):
        raise room.RoomError("could not read the url of %s" % context)
    skills = tuple(opts.skill) or DEFAULT_SKILLS
    join_ns = argparse.Namespace(
        pr=opts.pr, agent=agent, root=opts.root, repo=opts.repo,
        skill=list(skills), description=opts.description,
        harness=opts.harness, role=opts.role, max_rounds=opts.max_rounds)
    with contextlib.redirect_stdout(io.StringIO()):
        room.cmd_join(join_ns, parser, gh)

    if runner is None:
        runner = _default_runner(opts, root)
    prompt = "/s:room %s role %s, skills %s" % (
        url, opts.role, ", ".join(skills))
    os.environ[room.AGENT_ENV] = agent

    cursor = opts.since
    turns = 0
    session_id = None
    start = clock()
    reason = None
    closed = None
    failure = None
    while reason is None:
        remaining = opts.budget - (clock() - start)
        if remaining <= 0:
            reason = "budget"
            break
        watch_ns = argparse.Namespace(
            pr=opts.pr, agent=agent, root=opts.root, repo=opts.repo,
            max_rounds=opts.max_rounds, since=cursor,
            interval=opts.interval, timeout=remaining, once=False)
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                room.cmd_watch(watch_ns, gh, sleep, clock, parser)
        except room.RoomError as exc:
            reason, failure = "watch-failed", str(exc)
            break
        lines = []
        for text in captured.getvalue().splitlines():
            try:
                obj = json.loads(text)
            except ValueError:
                continue
            if isinstance(obj, dict):
                lines.append(obj)
        closed_line = next((l for l in lines if "closed" in l), None)
        tasks = [l for l in lines if "closed" not in l]
        if closed_line is not None:
            reason, closed = "closed", closed_line["closed"]
            cursor = _line_cursor(closed_line, cursor)
            break
        if not tasks:
            reason = "budget"
            break
        turns += 1
        sys.stderr.write("room run: turn %d on task(s) %s\n" % (
            turns, ", ".join("#%s" % t.get("task") for t in tasks)))
        ok, why, new_id = runner(prompt, root, session_id, turns - 1)
        if new_id:
            session_id = new_id
        cursor = _line_cursor(tasks[-1], cursor)
        if not ok:
            reason, failure = "turn-failed", why
        elif turns >= opts.max_turns:
            reason = "turn-cap"

    sys.stdout.write(json.dumps(_summary(
        turns, session_id, reason, context, cursor, closed, failure)) + "\n")
    sys.stdout.flush()
    if reason in FAILURE_REASONS:
        cli_common.err("%s: %s" % (reason, failure))
        return 1
    return 0


def _line_cursor(line, default):
    try:
        return room._cursor(line["cursor"])
    except (KeyError, TypeError, argparse.ArgumentTypeError):
        return default
