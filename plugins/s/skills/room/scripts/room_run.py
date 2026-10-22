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
import room_claim  # noqa: E402
import session_driver  # noqa: E402
import spec_common  # noqa: E402

PLUGIN_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
CLAIM_ROLES = ("reviewer", "ci")
DEFAULT_SKILLS = ("review-finding", "question", "status")
FAILURE_REASONS = ("turn-failed", "watch-failed", "claim-failed")
FIX_REQUIRED_MARKER = "<!-- shipd-verdict: fix-required -->"
SHIP_IT_MARKER = "<!-- shipd-verdict: ship-it -->"
IDLE_WATCH_LINE = "watch: no actionable task"
SLICE_INTERVALS = 4


def _model_base(root):
    """The configured model base for ``root``; a bad config is a
    ``RoomError``."""
    try:
        return spec_common.resolve_model_base(
            spec_common.resolve_config(root)[0])
    except spec_common.ConfigError as exc:
        raise room.RoomError(str(exc))


def _default_runner(opts, root, model_base):
    """The turn runner wrapping ``session_driver.run_turn``; no ``env`` is
    passed, so the process environment reaches the spawned session."""

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


def _head(gh, number, repo, warned):
    """The pull request's head sha, or ``""`` when it cannot be read. A failed
    read warns once (tracked in ``warned``) and never fails the run."""
    rc, out, _err = gh(["pr", "view", str(number), "--json", "headRefOid",
                        "--repo", repo])
    if rc != 0:
        if "head" not in warned:
            warned.add("head")
            sys.stderr.write("warning: could not read the head of %s#%d\n"
                             % (repo, number))
        return ""
    try:
        data = json.loads(out or "null")
    except ValueError:
        return ""
    head = data.get("headRefOid") if isinstance(data, dict) else None
    return head if isinstance(head, str) else ""


def _fix_required(body):
    """Whether ``body``'s verdict is fix-required, read as the CI gate reads
    it: the last line that, stripped, equals a verdict marker. A marker
    quoted anywhere else is prose, not a verdict."""
    for line in reversed(body.splitlines()):
        line = line.strip()
        if line in (FIX_REQUIRED_MARKER, SHIP_IT_MARKER):
            return line == FIX_REQUIRED_MARKER
    return False


def _ci_reviews(gh, repo, number, login, head, warned):
    """The reviews by ``login`` (case-insensitive) of ``head`` whose
    verdict line is the fix-required marker, oldest first. A failed or unparseable
    read warns once (tracked in ``warned``) and returns ``[]``."""
    rc, out, _err = gh(["api", "--paginate",
                        "repos/%s/pulls/%d/reviews" % (repo, number)])
    reviews = None
    if rc == 0:
        # ``--paginate`` without ``--slurp`` prints one JSON array per page.
        reviews, decoder, pos, text = [], json.JSONDecoder(), 0, out or ""
        try:
            while True:
                while pos < len(text) and text[pos].isspace():
                    pos += 1
                if pos >= len(text):
                    break
                page, pos = decoder.raw_decode(text, pos)
                if not isinstance(page, list):
                    raise ValueError("not a review list")
                reviews.extend(page)
        except ValueError:
            reviews = None
    if reviews is None:
        if "ci-reviews" not in warned:
            warned.add("ci-reviews")
            sys.stderr.write("warning: could not read the reviews of %s#%d\n"
                             % (repo, number))
        return []
    wanted = login.lower()
    found = []
    for review in reviews:
        if not isinstance(review, dict):
            continue
        user = review.get("user")
        who = user.get("login") if isinstance(user, dict) else None
        body = review.get("body")
        if isinstance(who, str) and who.lower() == wanted and \
                review.get("commit_id") == head and \
                isinstance(body, str) and _fix_required(body):
            found.append(review)
    return found


def _ci_prompt(url, review, login, head):
    return ("The CI reviewer @%s asked for fixes on %s at head %s: %s. Read "
            "that review and its inline comments with gh. For each finding, "
            "fix it, commit, and push to the pull request branch, or reply "
            "on the pull request with the concrete reason it is wrong. Do "
            "not approve or merge."
            % (login, url, head[:7], review.get("html_url")))


def _first_to(task):
    """The addressee of ``task``'s first message, or ``None``."""
    return task.messages[0].to if task.messages else None


def _has_request(tasks, agent, target, head=None):
    """True when ``agent`` already opened a task addressed to ``target`` --
    at ``head`` too, when one is given."""
    for task in tasks:
        if task.opener != agent or _first_to(task) != target:
            continue
        if head is None or task.messages[0].metadata.get("head") == head:
            return True
    return False


def _open_request(gh, repo, number, context, agent, target, head, text,
                  memo):
    """Open a review-finding task addressed to ``target`` as an author."""
    metadata = {"state": "input-required", "round": 1, "to": target,
                "skill": "review-finding"}
    if head:
        metadata["head"] = head
    room._post_message(
        gh, repo, number, room._message(context, agent, text, None, metadata),
        room._login(gh, memo), "author")


def _re_review(gh, repo, number, context, agent, opts, head, memo):
    """After the head moved, open one re-review task per target
    lacking one at ``head``: the ``--request-review`` agents plus every
    reviewer-role agent who opened a task addressed to this agent."""
    cards, tasks, _raw, _comments = room._read_room(gh, repo, number)
    targets = set(opts.request_review)
    for task in tasks:
        if _first_to(task) == agent and \
                room._card_role(cards, task.opener) == "reviewer":
            targets.add(task.opener)
    targets.discard(agent)
    for target in sorted(targets):
        if _has_request(tasks, agent, target, head):
            continue
        _open_request(gh, repo, number, context, agent, target, head,
                      _re_review_text(agent, head), memo)
        sys.stderr.write("room run: re-review requested from %s at %s\n"
                         % (target, head[:7]))


def _sync_head(gh, repo, number, context, agent, opts, known, memo, warned):
    """Re-read the head after a slice or a turn; when it differs from the
    last ``known`` head, whoever pushed it, open the re-reviews at the new
    head. Returns the new last known head. A failed read keeps ``known`` and
    opens nothing, and an empty ``known`` only learns the head."""
    head = _head(gh, number, repo, warned)
    if not head:
        return known
    if known and head != known:
        try:
            _re_review(gh, repo, number, context, agent, opts, head, memo)
        except room.RoomError as exc:
            sys.stderr.write("warning: re-review request failed: %s\n" % exc)
    return head


def _kick_off_text(agent, head):
    return ("Please review this pull request%s. Post each finding as a task "
            "to %s; approve when nothing blocking is left."
            % (" at head %s" % head[:7] if head else "", agent))


def _re_review_text(agent, head):
    return ("Re-review please: the head moved to %s. Approve it if nothing "
            "blocking remains, or post each finding as a task to %s."
            % (head[:7], agent))


def _summary(turns, session_id, reason, context, cursor, closed=None,
             failure=None):
    out = {"turns": turns, "session_id": session_id, "reason": reason,
           "context": context, "cursor": room._cursor_text(cursor)}
    if reason == "closed":
        out["closed"] = closed
    if reason in FAILURE_REASONS:
        out["failure"] = failure
    return out


def cmd_run(opts, parser, gh, runner, sleep, clock, preflight=None):
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
    if opts.pr is None:
        import room_run_repo
        return room_run_repo.cmd_run_repo(opts, parser, gh, runner, sleep,
                                          clock, preflight)
    if opts.state is not None:
        parser.error("--state needs repo mode (omit the pull request)")
    opts.since = opts.since or (0, 0)
    opts.budget = 14400.0 if opts.budget is None else opts.budget
    if opts.request_review and opts.role != "author":
        parser.error("--request-review needs --role author")
    root = room._root(opts)
    agent = room._agent_name(opts, parser, root)
    if agent in opts.request_review:
        parser.error("--request-review cannot name this run's own agent")
    repo, number, context = room._resolve_room(gh, opts.pr, opts.repo)
    login = _check_identity(gh, number, repo, opts.role)
    sys.stderr.write("room run: acting as @%s (%s)\n" % (
        login, room._credential_source(
            os.environ, room._room_host(opts.pr, os.environ))))
    model_base = None
    if runner is None or preflight is None:
        model_base = _model_base(root)
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
    import room_run_repo
    locks = room_run_repo.lock_pr_run(repo, agent, number)
    try:
        if opts.role in CLAIM_ROLES:
            room_claim.require_push(gh, repo, login)
        return _run_pr(opts, parser, gh, runner, sleep, clock, root, agent,
                       repo, number, context, model_base)
    finally:
        for lock in locks:
            lock.close()


def _run_pr(opts, parser, gh, runner, sleep, clock, root, agent, repo,
            number, context, model_base):
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

    memo = {}
    warned = set()
    author = opts.role == "author"
    known = ""
    if opts.request_review:
        _cards, tasks, _raw, _comments = room._read_room(gh, repo, number)
        head = known = _head(gh, number, repo, warned)
        for name in dict.fromkeys(opts.request_review):
            if _has_request(tasks, agent, name):
                continue
            _open_request(gh, repo, number, context, agent, name, head,
                          _kick_off_text(agent, head), memo)
            sys.stderr.write("room run: review requested from %s\n" % name)
    elif author:
        known = _head(gh, number, repo, warned)

    if runner is None:
        runner = _default_runner(opts, root, model_base)
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
    ci = author and bool(opts.ci_reviewer)
    claimed = opts.role in CLAIM_ROLES
    handled = set()
    check_ci = ci
    while reason is None:
        remaining = opts.budget - (clock() - start)
        review = None
        if check_ci:
            check_ci = False
            review = _next_ci_review(gh, repo, number, opts.ci_reviewer,
                                     handled, warned)
        if review is None and remaining <= 0:
            reason = "budget"
            break
        tasks = []
        if review is not None:
            turns += 1
            sys.stderr.write("room run: turn %d on CI review %s by %s\n" % (
                turns, review.get("id"), opts.ci_reviewer))
            turn_prompt = _ci_prompt(url, review, opts.ci_reviewer,
                                     review.get("commit_id") or "")
        else:
            slice_timeout = min(remaining, opts.interval * SLICE_INTERVALS) \
                if author else remaining
            watch_ns = argparse.Namespace(
                pr=opts.pr, agent=agent, root=opts.root, repo=opts.repo,
                max_rounds=opts.max_rounds, since=cursor,
                interval=opts.interval, timeout=slice_timeout, once=False)
            captured = io.StringIO()
            quiet = io.StringIO()
            try:
                with contextlib.redirect_stdout(captured):
                    if author:
                        with contextlib.redirect_stderr(quiet):
                            room.cmd_watch(watch_ns, gh, sleep, clock, parser)
                    else:
                        room.cmd_watch(watch_ns, gh, sleep, clock, parser)
            except room.RoomError as exc:
                reason, failure = "watch-failed", str(exc)
                break
            finally:
                for text in quiet.getvalue().splitlines():
                    if not text.startswith(IDLE_WATCH_LINE):
                        sys.stderr.write(text + "\n")
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
                if author:
                    known = _sync_head(gh, repo, number, context, agent,
                                       opts, known, memo, warned)
                    check_ci = ci
                    continue
                reason = "budget"
                break
            turn_prompt = prompt
        if claimed and any(t.get("opener") != agent for t in tasks):
            def run_turn():
                nonlocal turns
                turns += 1
                sys.stderr.write("room run: turn %d on task(s) %s\n" % (
                    turns, ", ".join("#%s" % t.get("task") for t in tasks)))
                return runner(turn_prompt, root, session_id, turns - 1)

            try:
                outcome, result = room_claim.claimed_turn(
                    gh, repo, number, agent,
                    _head(gh, number, repo, warned), run_turn)
            except room.RoomError as exc:
                reason, failure = "claim-failed", str(exc)
                break
            if outcome == "held":
                sleep(opts.interval)
                continue
            if outcome == "done":
                cursor = _line_cursor(tasks[-1], cursor)
                continue
            ok, why, new_id = result
        else:
            if tasks:
                turns += 1
                sys.stderr.write("room run: turn %d on task(s) %s\n" % (
                    turns, ", ".join("#%s" % t.get("task") for t in tasks)))
            ok, why, new_id = runner(turn_prompt, root, session_id,
                                     turns - 1)
        if new_id:
            session_id = new_id
        if tasks:
            cursor = _line_cursor(tasks[-1], cursor)
        if ok and author:
            known = _sync_head(gh, repo, number, context, agent, opts,
                               known, memo, warned)
        if not ok:
            reason, failure = "turn-failed", why
        elif turns >= opts.max_turns:
            reason = "turn-cap"

    if reason == "closed" and claimed:
        try:
            room_claim.delete_pr_claims(gh, repo, number)
        except room.RoomError as exc:
            sys.stderr.write("warning: could not delete the claims of #%d: "
                             "%s\n" % (number, exc))
    sys.stdout.write(json.dumps(_summary(
        turns, session_id, reason, context, cursor, closed, failure)) + "\n")
    sys.stdout.flush()
    if reason in FAILURE_REASONS:
        cli_common.err("%s: %s" % (reason, failure))
        return 1
    return 0


def _next_ci_review(gh, repo, number, login, handled, warned):
    """The newest unhandled fix-required review of the current head by
    ``login``, with every matching review marked handled; ``None`` when
    there is none."""
    head = _head(gh, number, repo, warned)
    if not head:
        return None
    fresh = [r for r in _ci_reviews(gh, repo, number, login, head, warned)
             if r.get("id") not in handled]
    if not fresh:
        return None
    handled.update(r.get("id") for r in fresh)
    return fresh[-1]


def _line_cursor(line, default):
    try:
        return room._cursor(line["cursor"])
    except (KeyError, TypeError, argparse.ArgumentTypeError):
        return default
