#!/usr/bin/env python3
"""room_run_repo — ``shipd room run --repo``: one local loop over a repository.

With no pull request, ``room run`` polls the repository's open pull requests
(a single ``gh pr list`` call, no model spend) and runs one resumed headless
``/s:room`` turn on each pull request that holds a task addressed to this
agent, one turn at a time, until it is interrupted. Each pull request's
cursor and session id live in a locked JSON state file, so a restart resumes
every conversation. It prints one JSON summary line on stdout; progress goes
to stderr.

``room_run.cmd_run`` imports this module lazily, because the Actions wake
bundles ``room.py`` without ``session_driver``.
"""

import argparse
import contextlib
import fcntl
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))
if BUILD_SCRIPTS not in sys.path:
    sys.path.insert(0, BUILD_SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cli_common  # noqa: E402
import room  # noqa: E402
import room_claim  # noqa: E402
import room_run  # noqa: E402
import session_driver  # noqa: E402

STATE_VERSION = 1
BACKOFF_CAP = 900
LIST_FIELDS = "number,url,author,updatedAt"


def default_state_path(repo, agent):
    """The default state file of ``agent`` in ``repo`` (``owner/name``)."""
    owner, _sep, name = repo.partition("/")
    return os.path.expanduser(os.path.join(
        "~", ".shipd", "room-run", owner, name,
        agent.replace("/", "_") + ".json"))


def _empty_state(repo, agent):
    return {"version": STATE_VERSION, "repo": repo, "agent": agent,
            "prs": {}}


def load_state(path, repo, agent):
    """The state stored at ``path``; an absent file is an empty state, and an
    unreadable or malformed one warns once on stderr and is empty too."""
    state = _empty_state(repo, agent)
    try:
        with open(path) as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return state
    except (OSError, ValueError) as exc:
        sys.stderr.write("warning: could not read the state file %s: %s; "
                         "starting empty\n" % (path, exc))
        return state
    prs = data.get("prs") if isinstance(data, dict) else None
    if not isinstance(prs, dict):
        sys.stderr.write("warning: the state file %s is malformed; "
                         "starting empty\n" % path)
        return state
    state["prs"] = {str(k): dict(v) for k, v in prs.items()
                    if isinstance(v, dict)}
    return state


def save_state(path, state):
    """Write ``state`` to ``path`` atomically: a temporary file in the same
    directory, then a rename."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".room-run-", suffix=".tmp",
                               dir=directory)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def agent_lock_path(repo, agent):
    """The lock every runner of ``agent`` in ``repo`` takes, whatever its
    ``--state``. GitHub names are case-insensitive, so the repository is
    lowercased."""
    return default_state_path(repo.lower(), agent) + ".lock"


def pr_lock_path(repo, agent, number):
    """The lock a PR-mode runner of ``agent`` takes on PR ``number``."""
    return os.path.join(os.path.dirname(agent_lock_path(repo, agent)),
                        "%s.pr-%d.lock" % (agent.replace("/", "_"), number))


def _refusal(repo, agent, path):
    return ("another room run already serves agent %s on %s (lock %s); "
            "stop it first" % (agent, repo, path))


def hold_lock(path, refusal, shared=False):
    """Hold a non-blocking ``flock`` on ``path``, shared or exclusive;
    returns the open handle. A held lock raises ``RoomError(refusal)``."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    handle = open(path, "a")
    try:
        fcntl.flock(handle, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
                    | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise room.RoomError(refusal)
    return handle


def lock_pr_run(repo, agent, number):
    """Hold the shared agent lock and the exclusive PR lock of a PR-mode
    run; returns both handles. A repo-mode runner of the same agent, or a
    PR runner of it on the same PR, makes this raise ``RoomError``."""
    path = agent_lock_path(repo, agent)
    shared = hold_lock(path, _refusal(repo, agent, path), shared=True)
    try:
        pr_path = pr_lock_path(repo, agent, number)
        return [shared, hold_lock(pr_path, _refusal(repo, agent, pr_path))]
    except BaseException:
        shared.close()
        raise


def _list_open(gh, repo):
    """The open pull requests of ``repo`` as dicts, ``number`` ascending."""
    data = room._gh_json(
        gh, ["pr", "list", "--repo", repo, "--state", "open", "--json",
             LIST_FIELDS, "--limit", "100"],
        what="gh pr list")
    if not isinstance(data, list):
        raise room.RoomError("gh pr list returned an unexpected shape")
    prs = [p for p in data
           if isinstance(p, dict) and isinstance(p.get("number"), int)]
    return sorted(prs, key=lambda p: p["number"])


def _visit(gh, opts, agent, parser, number, cursor):
    """Run ``watch`` once on pull request ``number`` from ``cursor``;
    returns ``(task_lines, closed)``. The idle watch line is dropped from
    the forwarded stderr."""
    watch_ns = argparse.Namespace(
        pr=str(number), agent=agent, root=opts.root, repo=opts.repo,
        max_rounds=opts.max_rounds, since=cursor, interval=opts.interval,
        timeout=None, once=True)
    captured, quiet = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(captured), \
                contextlib.redirect_stderr(quiet):
            room.cmd_watch(watch_ns, gh, lambda _s: None, lambda: 0.0,
                           parser)
    finally:
        for text in quiet.getvalue().splitlines():
            if not text.startswith(room_run.IDLE_WATCH_LINE):
                sys.stderr.write(text + "\n")
    lines = []
    for text in captured.getvalue().splitlines():
        try:
            obj = json.loads(text)
        except ValueError:
            continue
        if isinstance(obj, dict):
            lines.append(obj)
    closed = any("closed" in line for line in lines)
    return [l for l in lines if "closed" not in l], closed


def _stored_cursor(entry):
    try:
        return room._cursor(entry["cursor"])
    except (KeyError, TypeError, argparse.ArgumentTypeError):
        return (0, 0)


def cmd_run_repo(opts, parser, gh, runner, sleep, clock, preflight=None):
    if not opts.repo:
        parser.error("repo mode (no pull request) needs --repo")
    if opts.role == "author":
        parser.error("repo mode takes --role reviewer or ci, not author")
    if opts.since is not None:
        parser.error("--since needs a pull request")
    if opts.request_review:
        parser.error("--request-review needs a pull request")
    login = room._login(gh, {})
    if not login:
        raise room.RoomError(
            "could not read the acting GitHub login (gh api user failed); "
            "an approval needs a readable account")
    root = room._root(opts)
    agent = room._agent_name(opts, parser, root)
    model_base = None
    if runner is None or preflight is None:
        model_base = room_run._model_base(root)
    if preflight is None:
        def preflight(cwd):
            return session_driver.preflight(
                cwd, harness=opts.harness, effort=opts.model,
                model_base=model_base)
    ready, why = preflight(root)
    if not ready:
        raise room.RoomError(
            "harness %s is not ready: %s; sign in with `%s` and rerun"
            % (opts.harness, why, session_driver.login_hint(opts.harness)))
    os.environ[room.AGENT_ENV] = agent
    if runner is None:
        runner = room_run._default_runner(opts, root, model_base)
    sys.stderr.write("room run: acting as @%s (%s)\n" % (
        login, room._credential_source(os.environ, room._room_host(
            opts.repo, os.environ))))

    path = opts.state or default_state_path(opts.repo, agent)
    agent_lock = agent_lock_path(opts.repo, agent)
    locks = [hold_lock(agent_lock, _refusal(opts.repo, agent, agent_lock))]
    try:
        room_claim.require_push(gh, opts.repo, login)
        state_lock = path + ".lock"
        if not (os.path.exists(state_lock)
                and os.path.samefile(state_lock, agent_lock)):
            locks.append(hold_lock(state_lock,
                                   "another room run holds %s" % path))
        return _run_loop(opts, parser, gh, runner, sleep, clock, preflight,
                         login, root, agent, path)
    finally:
        for lock in locks:
            lock.close()


def _run_loop(opts, parser, gh, runner, sleep, clock, preflight, login,
              root, agent, path):
    state = load_state(path, opts.repo, agent)
    prs = state["prs"]
    skills = tuple(opts.skill) or room_run.DEFAULT_SKILLS
    seen, parked, warned, joined = {}, set(), set(), set()
    head_warned = set()
    per_pr = {}
    visited = {}
    total = 0
    backoff = 0
    reason = failure = None
    start = clock()
    save_warned = []

    def save():
        try:
            save_state(path, state)
        except OSError as exc:
            if not save_warned:
                save_warned.append(True)
                sys.stderr.write("warning: could not write the state file "
                                 "%s: %s\n" % (path, exc))

    def note(number):
        entry = prs.get(str(number)) or {}
        visited[str(number)] = {
            "turns": per_pr.get(number, 0),
            "session_id": entry.get("session_id"),
            "cursor": room._cursor_text(_stored_cursor(entry))}

    try:
        while reason is None:
            if opts.budget is not None and clock() - start >= opts.budget:
                reason = "budget"
                break
            try:
                listing = _list_open(gh, opts.repo)
            except room.RoomError as exc:
                backoff = _warn_error(exc, backoff, opts.interval,
                                      "listing the open pull requests")
                sleep(backoff or opts.interval)
                continue
            backoff = 0
            open_keys = {str(p["number"]) for p in listing}
            stale = [k for k in prs if k not in open_keys]
            for key in stale:
                del prs[key]
                try:
                    room_claim.delete_pr_claims(gh, opts.repo, int(key))
                except (room.RoomError, ValueError) as exc:
                    sys.stderr.write("warning: could not delete the claims "
                                     "of #%s: %s\n" % (key, exc))
            if stale:
                save()
            for pr in listing:
                number = pr["number"]
                if number in parked:
                    continue
                who = (pr.get("author") or {}).get("login") \
                    if isinstance(pr.get("author"), dict) else None
                if not isinstance(who, str) or not who or \
                        who.lower() == login.lower():
                    if number not in warned:
                        warned.add(number)
                        sys.stderr.write(
                            "room run: skipping #%d: %s\n" % (
                                number, "its author is unreadable"
                                if not who else "authored by the acting "
                                "login @%s" % login))
                    continue
                updated = pr.get("updatedAt")
                if isinstance(updated, str) and seen.get(number) == updated:
                    continue
                entry = prs.get(str(number)) or {}
                try:
                    tasks, closed = _visit(gh, opts, agent, parser, number,
                                           _stored_cursor(entry))
                    note(number)
                    if not tasks:
                        if isinstance(updated, str):
                            seen[number] = updated
                        continue
                    if number not in joined:
                        join_ns = argparse.Namespace(
                            pr=str(number), agent=agent, root=opts.root,
                            repo=opts.repo, skill=list(skills),
                            description=opts.description,
                            harness=opts.harness, role=opts.role,
                            max_rounds=opts.max_rounds)
                        with contextlib.redirect_stdout(io.StringIO()):
                            room.cmd_join(join_ns, parser, gh)
                        joined.add(number)
                except room.RoomError as exc:
                    backoff = _warn_error(exc, backoff, opts.interval,
                                          "reading #%d" % number)
                    if backoff:
                        break
                    continue
                prompt = "/s:room %s role %s, skills %s" % (
                    pr.get("url") or "%s#%d" % (opts.repo, number),
                    opts.role, ", ".join(skills))

                def turn_once(number=number, entry=entry, tasks=tasks,
                              prompt=prompt):
                    nonlocal total
                    total += 1
                    turn = per_pr.get(number, 0)
                    per_pr[number] = turn + 1
                    sys.stderr.write(
                        "room run: turn %d on #%d, task(s) %s\n" % (
                            total, number, ", ".join(
                                "#%s" % t.get("task") for t in tasks)))
                    return runner(prompt, root, entry.get("session_id"),
                                  turn)

                try:
                    if any(t.get("opener") != agent for t in tasks):
                        outcome, result = room_claim.claimed_turn(
                            gh, opts.repo, number, agent,
                            room_run._head(gh, number, opts.repo,
                                           head_warned), turn_once)
                    else:
                        # Replies on the agent's own tasks need no claim.
                        outcome, result = "ran", turn_once()
                except room.RoomError as exc:
                    backoff = _warn_error(exc, backoff, opts.interval,
                                          "claiming #%d" % number)
                    if backoff:
                        break
                    continue
                if outcome == "held":
                    continue
                if outcome == "done":
                    entry = prs.setdefault(str(number), {})
                    entry["cursor"] = room._cursor_text(
                        room_run._line_cursor(tasks[-1],
                                              _stored_cursor(entry)))
                    save()
                    note(number)
                    continue
                ok, why, new_id = result
                entry = prs.setdefault(str(number), {})
                if new_id:
                    entry["session_id"] = new_id
                entry["cursor"] = room._cursor_text(room_run._line_cursor(
                    tasks[-1], _stored_cursor(entry)))
                save()
                note(number)
                if not ok:
                    sys.stderr.write(
                        "room run: turn on #%d failed: %s; parked\n"
                        % (number, why))
                    parked.add(number)
                    ready, why_not = preflight(root)
                    if not ready:
                        reason, failure = "preflight-failed", why_not
                        break
                elif per_pr[number] >= opts.max_turns:
                    sys.stderr.write(
                        "room run: #%d reached --max-turns; parked\n"
                        % number)
                    parked.add(number)
            if reason is None:
                sleep(backoff or opts.interval)
    except KeyboardInterrupt:
        reason = "interrupted"
    save()
    summary = {"mode": "repo", "repo": opts.repo, "turns": total,
               "reason": reason, "prs": visited}
    if reason == "preflight-failed":
        summary["failure"] = failure
    sys.stdout.write(json.dumps(summary) + "\n")
    sys.stdout.flush()
    if reason == "preflight-failed":
        cli_common.err(
            "preflight-failed: %s; sign in with `%s` and rerun"
            % (failure, session_driver.login_hint(opts.harness)))
        return 1
    return 130 if reason == "interrupted" else 0


def _warn_error(exc, backoff, interval, what):
    """Warn about a ``RoomError`` while ``what``; returns the backoff to
    sleep (``0`` unless the error names a rate limit)."""
    if "rate limit" in str(exc).lower():
        backoff = min(max(2 * backoff, 2 * interval), BACKOFF_CAP)
        sys.stderr.write("warning: rate limited while %s: %s; backing off "
                         "%ds\n" % (what, exc, backoff))
        return backoff
    sys.stderr.write("warning: %s failed: %s\n" % (what, exc))
    return 0
