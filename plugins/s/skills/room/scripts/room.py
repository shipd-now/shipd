#!/usr/bin/env python3
"""room — the ``shipd room`` verbs over a pull request's comment thread.

A PR room is a pull request's comment thread used as a message bus between
agents (see ``room_schema``). This script is the harness-agnostic surface an
agent drives to take part in one:

  join <pr>      post or refresh this agent's own card comment (``--role``
                 sets its role: author, reviewer, or ci)
  list <pr>      the room's cards and tasks
  message <pr>   open a task (``--new``) or advance one (``--task ID``)
  close <pr>     post a task's terminal message
  watch <pr>     wait for a task that is this agent's turn (NDJSON)

Every GitHub read and write goes through one injectable ``gh`` runner,
``gh(args, input=None) -> (rc, stdout, stderr)``, defaulting to the ``gh``
CLI, so the test suite drives the verbs against a fake and reaches no
network. Comment bodies are only ever built by ``room_schema.render_comment``.

A finding task is one whose opening comment was read from the review-comment
endpoint (only the semantic-review gate opens tasks there). Its messages —
``message``, ``close``, and the round-cap posts — reply on that review thread
(``in_reply_to`` the task id); every other task stays on issue comments.

Every comment a verb posts opens with a speaker heading naming the agent,
its card's role, and the GitHub login read once per verb from ``gh api user``.

Mutating verbs print one JSON object on stdout and one human line on stderr;
a fatal outcome is one ``Error: <reason>`` line and exit ``1``; invalid
arguments exit ``2`` with usage text.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))
if BUILD_SCRIPTS not in sys.path:
    sys.path.insert(0, BUILD_SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cli_common  # noqa: E402
import room_schema  # noqa: E402
import spec_common  # noqa: E402

PLUGIN_MANIFEST = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", ".claude-plugin", "plugin.json"))

AGENT_ENV = "SHIPD_ROOM_AGENT"
CLOSE_STATES = ("completed", "canceled", "failed")
OPEN_STATES = ("working", "input-required")


class RoomError(Exception):
    """A fatal room outcome, reported once as an ``Error:`` line (exit 1)."""


# ---------------------------------------------------------------------------
# The gh seam
# ---------------------------------------------------------------------------

def _default_gh(args, input=None):
    try:
        proc = subprocess.run(
            ["gh"] + list(args), input=input, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        # A missing or unrunnable gh is a failed call like any other: one
        # ``Error:`` line through ``_gh_json``, never a traceback.
        return 127, "", "could not run gh: %s" % exc
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _gh_json(gh, args, input=None, what=None):
    """Run ``gh`` and parse its stdout as JSON; a non-zero exit or
    unparseable output raises ``RoomError`` naming the call."""
    rc, out, err = gh(list(args), input=input)
    label = what or "gh %s" % " ".join(args)
    if rc != 0:
        raise RoomError("%s failed: %s" % (label, (err or "").strip()
                                           or "exit %d" % rc))
    try:
        return json.loads(out or "null")
    except ValueError as exc:
        raise RoomError("%s returned invalid JSON: %s" % (label, exc))


_PR_URL = re.compile(r"^https?://[^/]+/([^/]+/[^/]+)/pull/(\d+)")


def _resolve_room(gh, pr, repo=None):
    """``(repo, number, context)`` for ``pr``; the context id is
    ``<owner>/<repo>#<number>``. The repository comes from a pull request
    URL first, then ``repo`` (``--repo``), else ``gh repo view`` in the
    working directory; a URL and ``repo`` naming different repositories
    raise ``RoomError``."""
    ref = str(pr)
    match = _PR_URL.match(ref)
    if match:
        url_repo = match.group(1)
        if repo and repo.lower() != url_repo.lower():
            raise RoomError("pull request URL names %s but --repo names %s"
                            % (url_repo, repo))
        repo, ref = url_repo, match.group(2)
    args = ["pr", "view", ref, "--json", "number,url"]
    if repo:
        args += ["--repo", repo]
    pr_data = _gh_json(gh, args, what="gh pr view %s" % pr)
    if not repo:
        repo_data = _gh_json(gh, ["repo", "view", "--json", "nameWithOwner"],
                             what="gh repo view")
        try:
            repo = repo_data["nameWithOwner"]
        except (KeyError, TypeError):
            raise RoomError("could not resolve the pull request for %s" % pr)
    try:
        number = int(pr_data["number"])
    except (KeyError, TypeError, ValueError):
        raise RoomError("could not resolve the pull request for %s" % pr)
    return repo, number, "%s#%d" % (repo, number)


def _list_comments(gh, path):
    """Every comment under ``path``, read with ``--paginate --slurp`` and the
    page arrays flattened."""
    pages = _gh_json(
        gh, ["api", "%s?per_page=100" % path, "--paginate", "--slurp"],
        what="gh api %s (--paginate --slurp needs gh >= 2.46)" % path)
    comments = []
    for page in pages or []:
        if isinstance(page, list):
            comments.extend(c for c in page if isinstance(c, dict))
        elif isinstance(page, dict):
            comments.append(page)
    return comments


ENDPOINT_KEY = "_room_endpoint"


def _endpoint(comment):
    """``"issue"`` or ``"review"``: the endpoint ``_read_comments`` read
    ``comment`` from."""
    return comment.get(ENDPOINT_KEY, "issue")


def _comment_order(comment):
    """Sort key for the union: ``created_at`` (GitHub's ``Z``-suffixed
    ISO-8601 stamps order lexicographically), then id."""
    return (str(comment.get("created_at") or ""), comment.get("id") or 0)


def _read_comments(gh, repo, number):
    """Every room comment, read once: the union of the PR's issue comments
    (room traffic) and its review comments (the semantic-review gate's
    finding tasks), ordered by ``created_at`` and then comment id — the two
    endpoints number their comments in separate sequences, so id order alone
    could put a reply ahead of the opener it answers. Each dict is tagged
    with the endpoint it came from (see ``_endpoint``)."""
    issue = _list_comments(gh, "repos/%s/issues/%d/comments" % (repo, number))
    review = _list_comments(gh, "repos/%s/pulls/%d/comments" % (repo, number))
    for comment in issue:
        comment[ENDPOINT_KEY] = "issue"
    for comment in review:
        comment[ENDPOINT_KEY] = "review"
    comments = issue + review
    comments.sort(key=_comment_order)
    return comments


def _parse_room(comments):
    """``(cards, tasks, raw)`` from ``_read_comments`` output. A comment whose
    marker does not parse is warned about and skipped."""
    cards = {}
    raw = {}
    entries = []
    for comment in comments:
        comment_id = comment.get("id")
        author = (comment.get("user") or {}).get("login")
        try:
            parsed = room_schema.parse_comments(comment.get("body") or "",
                                                author=author)
        except room_schema.SchemaError as exc:
            cli_common.warn("comment %s: %s" % (comment_id, exc))
            continue
        for obj in parsed:
            if isinstance(obj, room_schema.AgentCard):
                cards.pop(obj.name, None)
                cards[obj.name] = obj
                if _endpoint(comment) == "issue":
                    raw[obj.name] = comment_id
            else:
                entries.append((comment_id, obj))
    return list(cards.values()), room_schema.build_tasks(entries), raw


def _room_from_comments(comments):
    """``(cards, tasks)`` from ``_read_comments`` output: ``cards`` holds the
    last card per agent name, ``tasks`` the ``build_tasks`` view."""
    cards, tasks, _raw = _parse_room(comments)
    return cards, tasks


SUMMARY_MARKERS = ("<!-- shipd-semantic-review -->",
                   "<!-- am-semantic-review -->")


def _owned_card_ids(comments):
    """Card name -> id of the last issue comment that holds only that agent's
    card: exactly one room marker, an ``AgentCard``, and no semantic-review
    summary marker. A comment whose marker does not parse is skipped."""
    owned = {}
    for comment in comments:
        if _endpoint(comment) != "issue":
            continue
        body = comment.get("body") or ""
        if any(marker in body for marker in SUMMARY_MARKERS):
            continue
        try:
            parsed = room_schema.parse_comments(body)
        except room_schema.SchemaError:
            continue
        if len(parsed) == 1 and isinstance(parsed[0], room_schema.AgentCard):
            owned[parsed[0].name] = comment.get("id")
    return owned


def _read_room(gh, repo, number):
    """Read the room once: ``(cards, tasks, raw, comments)``.

    ``cards`` and ``tasks`` are as ``_room_from_comments`` builds them,
    ``raw`` maps a card name to the last issue comment holding that card,
    which may be a foreign comment such as the review summary; ``join`` does
    not use it (see ``_owned_card_ids``). ``comments`` is the raw comment list
    that was read."""
    comments = _read_comments(gh, repo, number)
    cards, tasks, raw = _parse_room(comments)
    return cards, tasks, raw, comments


def _last_comment(comments, task):
    """The last comment of ``task``: the last one whose id is ``task.id`` or
    whose Message marker names ``task.id`` as its ``taskId``."""
    last = None
    for comment in comments:
        if comment.get("id") == task.id:
            last = comment
            continue
        try:
            parsed = room_schema.parse_comments(
                comment.get("body") or "",
                author=(comment.get("user") or {}).get("login"))
        except room_schema.SchemaError:
            continue
        if any(isinstance(obj, room_schema.Message)
               and obj.task_id == task.id for obj in parsed):
            last = comment
    return last


def _post(gh, repo, number, body):
    """Create an issue comment; the parsed response (``id``, ``html_url``)."""
    return _gh_json(
        gh, ["api", "-X", "POST",
             "repos/%s/issues/%d/comments" % (repo, number), "--input", "-"],
        input=json.dumps({"body": body}), what="posting a room comment")


def _finding_root(comments, task):
    """``task.id`` when the comment whose id is ``task.id`` was read from the
    review endpoint (a finding task's thread root), else ``None``."""
    for comment in comments:
        if comment.get("id") == task.id:
            return task.id if _endpoint(comment) == "review" else None
    return None


def _post_reply(gh, repo, number, thread, body):
    """Reply on the review thread rooted at comment ``thread``; the parsed
    response (``id``, ``html_url``)."""
    return _gh_json(
        gh, ["api", "-X", "POST",
             "repos/%s/pulls/%d/comments" % (repo, number), "--input", "-"],
        input=json.dumps({"body": body, "in_reply_to": thread}),
        what="posting a room reply on thread %s" % thread)


def _patch(gh, repo, comment_id, body):
    """Edit an issue comment in place; the parsed response."""
    return _gh_json(
        gh, ["api", "-X", "PATCH",
             "repos/%s/issues/comments/%s" % (repo, comment_id),
             "--input", "-"],
        input=json.dumps({"body": body}),
        what="editing room comment %s" % comment_id)


# ---------------------------------------------------------------------------
# Identity and settings
# ---------------------------------------------------------------------------

def _root(opts):
    return os.path.abspath(opts.root or os.getcwd())


def _room_config(root):
    try:
        return spec_common.resolve_room(root)
    except spec_common.ConfigError as exc:
        raise RoomError(str(exc))


def _agent_name(opts, parser, root):
    """The acting agent: ``--agent``, then ``SHIPD_ROOM_AGENT``, then the
    ``room.agent`` config member; none is a usage error (exit 2)."""
    if opts.agent:
        return opts.agent
    env = os.environ.get(AGENT_ENV, "").strip()
    if env:
        return env
    agent, _max_rounds = _room_config(root)
    if agent:
        return agent
    parser.error("no agent name — pass --agent, set %s, or declare room.agent"
                 % AGENT_ENV)


def _max_rounds(opts, root):
    if opts.max_rounds is not None:
        return opts.max_rounds
    return _room_config(root)[1]


def _plugin_version():
    try:
        with open(PLUGIN_MANIFEST, encoding="utf-8") as fh:
            return str(json.load(fh).get("version") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def _require_card(cards, name, context):
    if not any(card.name == name for card in cards):
        raise RoomError("agent '%s' has not joined %s — run shipd room join"
                        % (name, context))


def _find_task(tasks, task_id, context):
    for task in tasks:
        if task.id == task_id:
            return task
    raise RoomError("task %s not found on %s" % (task_id, context))


def _transition(task_id, current, requested):
    try:
        return room_schema.next_state(current, requested)
    except room_schema.InvalidTransition:
        if current is None:
            raise RoomError("a new task opens at %s, not %s"
                            % (" or ".join(room_schema.OPENING_STATES),
                               requested))
        raise RoomError("task %s is %s; no transition to %s"
                        % (task_id, current, requested))


def _message(context, agent, text, task_id, metadata):
    return room_schema.Message(
        role="agent", parts=({"kind": "text", "text": text},),
        context_id=context, agent=agent, task_id=task_id, metadata=metadata)


def _emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")


def _delete(gh, repo, comment_id, endpoint="issue"):
    """Delete an issue comment, or a review comment for ``"review"``."""
    path = "pulls" if endpoint == "review" else "issues"
    rc, _out, err = gh(["api", "-X", "DELETE",
                        "repos/%s/%s/comments/%s" % (repo, path, comment_id)])
    if rc != 0:
        raise RoomError("deleting room comment %s failed: %s"
                        % (comment_id, (err or "").strip() or "exit %d" % rc))


def _own_claim(comments, task, agent):
    """``(id, endpoint)`` of ``task``'s last comment when its Message for the
    task was posted by ``agent`` at ``working`` (on either endpoint); else
    ``None``."""
    last = _last_comment(comments, task)
    if last is None:
        return None
    try:
        parsed = room_schema.parse_comments(
            last.get("body") or "",
            author=(last.get("user") or {}).get("login"))
    except room_schema.SchemaError:
        return None
    for obj in parsed:
        if (isinstance(obj, room_schema.Message)
                and obj.task_id == task.id and obj.agent == agent
                and obj.state == "working"):
            return last.get("id"), _endpoint(last)
    return None


def _drop_claim(gh, repo, claim):
    """Delete the claim comment (``(id, endpoint)`` from ``_own_claim``)
    after the reply is posted; a failure is a warning, because the reply
    stands."""
    if claim is None:
        return
    claim_id, endpoint = claim
    try:
        _delete(gh, repo, claim_id, endpoint)
    except RoomError:
        sys.stderr.write("warning: could not remove claim comment %s\n"
                         % claim_id)


THREAD_LOOKUP_QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes { id isResolved comments(first:1) { nodes { databaseId } } }
      }
    }
  }
}
"""


def _resolve_finding_thread(gh, repo, number, task_id):
    """Resolve the review thread rooted at finding task ``task_id`` with the
    mutation ``review_gate.py resolve`` uses. A thread already resolved is
    left alone; a missing thread or a failed call is one warning, because
    the reply already stands."""
    owner, _sep, name = repo.partition("/")
    warning = ("warning: could not resolve the review thread for task %s\n"
               % task_id)
    rc, out, _err = gh(["api", "graphql", "-f", "query=%s" % THREAD_LOOKUP_QUERY,
                        "-f", "owner=%s" % owner, "-f", "name=%s" % name,
                        "-F", "number=%d" % number])
    thread = None
    if rc == 0:
        try:
            data = json.loads(out or "null")
            nodes = (data["data"]["repository"]["pullRequest"]
                     ["reviewThreads"]["nodes"])
            for node in nodes:
                first = (node.get("comments") or {}).get("nodes") or []
                if first and first[0].get("databaseId") == task_id:
                    thread = node
                    break
        except (ValueError, KeyError, TypeError, AttributeError):
            thread = None
    if thread is None:
        sys.stderr.write(warning)
        return
    if thread.get("isResolved"):
        return
    rc, _out, _err = gh(["api", "graphql", "-f",
                         "query=%s" % room_schema.RESOLVE_THREAD_MUTATION,
                         "-f", "threadId=%s" % thread.get("id")])
    if rc != 0:
        sys.stderr.write(warning)


def _login(gh, memo):
    """The posting GitHub login from ``gh api user``, read once per verb and
    kept in ``memo``. A failed read or an empty login warns once and yields
    ``""``, so the heading drops its ``(for @login)`` segment."""
    if "login" in memo:
        return memo["login"]
    login = ""
    rc, out, err = gh(["api", "user"])
    if rc == 0:
        try:
            data = json.loads(out or "null")
            login = str(data.get("login") or "") \
                if isinstance(data, dict) else ""
        except ValueError:
            login = ""
    if not login:
        sys.stderr.write(
            "warning: could not read the GitHub login (gh api user%s); "
            "posting without a '(for @login)' heading\n"
            % (": %s" % (err or "").strip() if rc != 0 and (err or "").strip()
               else ""))
    memo["login"] = login
    return login


def _card_role(cards, name):
    """The role on ``name``'s card, or ``""`` when it has none."""
    for card in cards:
        if card.name == name:
            return card.role
    return ""


def _post_message(gh, repo, number, message, login="", role="",
                  thread=None):
    try:
        body = room_schema.render_comment(message, login=login, role=role)
    except room_schema.SchemaError as exc:
        raise RoomError(str(exc))
    if thread is not None:
        return _post_reply(gh, repo, number, thread, body)
    return _post(gh, repo, number, body)


# ---------------------------------------------------------------------------
# The actionable-task predicate
# ---------------------------------------------------------------------------

def is_actionable(task, agent, skills=()):
    """True when it is ``agent``'s turn on ``task``: the task waits at
    ``input-required``, ``agent`` did not post its last message, and it is
    addressed to ``agent`` — or unaddressed and asks for a skill in
    ``skills``. Pure and I/O-free; ``watch`` and the CI wake
    (``room-action-wake``) both import it."""
    if task.state != "input-required":
        return False
    if task.last_agent == agent:
        return False
    if task.to == agent:
        return True
    return task.to is None and task.skill in tuple(skills or ())


def actionable_tasks(tasks, agent, skills=()):
    """The tasks ``is_actionable`` accepts for ``agent``, ordered by id."""
    return sorted((t for t in tasks if is_actionable(t, agent, skills)),
                  key=lambda t: t.id)


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------

def cmd_join(opts, parser, gh):
    root = _root(opts)
    agent = _agent_name(opts, parser, root)
    repo, number, context = _resolve_room(gh, opts.pr, opts.repo)
    _cards, _tasks, _raw, comments = _read_room(gh, repo, number)
    owned = _owned_card_ids(comments)
    card = room_schema.AgentCard(
        name=agent, description=opts.description or "",
        skills=tuple(opts.skill or ()), version=_plugin_version(),
        harness=opts.harness or "", role=opts.role or "")
    try:
        body = room_schema.render_comment(card, login=_login(gh, {}))
    except room_schema.SchemaError as exc:
        raise RoomError(str(exc))
    if agent in owned:
        resp = _patch(gh, repo, owned[agent], body)
    else:
        resp = _post(gh, repo, number, body)
    resp = resp or {}
    _emit({"comment": resp.get("id", owned.get(agent)), "agent": agent,
           "url": resp.get("html_url")})
    sys.stderr.write("joined %s as %s\n" % (context, agent))
    return 0


def _task_line(task):
    line = "#%s  %s  from %s  to %s  round %s  last %s" % (
        task.id, task.state, task.opener, task.to or "-", task.round,
        task.last_agent)
    if task.skill:
        line += "  skill %s" % task.skill
    return line


def _card_line(card):
    parts = [card.name]
    if card.role:
        parts.append("role %s" % card.role)
    if card.harness:
        parts.append("harness %s" % card.harness)
    parts.append("skills %s" % (",".join(card.skills) if card.skills else "-"))
    parts.append("version %s" % (card.version or "-"))
    return "  ".join(parts)


def _task_dict(task):
    return {
        "id": task.id,
        "state": task.state,
        "opener": task.opener,
        "to": task.to,
        "round": task.round,
        "reason": task.reason,
        "last_agent": task.last_agent,
        "skill": task.skill,
        "messages": len(task.messages),
    }


def cmd_list(opts, parser, gh):
    _agent_name(opts, parser, _root(opts))
    repo, number, context = _resolve_room(gh, opts.pr, opts.repo)
    cards, tasks, _raw, _comments = _read_room(gh, repo, number)
    if opts.open:
        tasks = [t for t in tasks if t.state in OPEN_STATES]
    if opts.json:
        _emit({"context": context,
               "cards": [room_schema.card_to_dict(c) for c in cards],
               "tasks": [_task_dict(t) for t in tasks]})
        return 0
    lines = ["room %s" % context, "cards:"]
    lines += ["  " + _card_line(c) for c in cards] or ["  (none)"]
    lines.append("tasks:")
    lines += ["  " + _task_line(t) for t in tasks] or ["  (none)"]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


def _reply_result(resp, task_id, state, rnd):
    resp = resp or {}
    return {"comment": resp.get("id"), "task": task_id, "state": state,
            "round": rnd, "url": resp.get("html_url")}


def cmd_message(opts, parser, gh):
    root = _root(opts)
    agent = _agent_name(opts, parser, root)
    repo, number, context = _resolve_room(gh, opts.pr, opts.repo)
    cards, tasks, _raw, comments = _read_room(gh, repo, number)
    _require_card(cards, agent, context)
    memo = {}
    role = _card_role(cards, agent)
    metadata = {}
    if opts.new:
        requested = opts.state or (
            "input-required" if opts.to else "submitted")
        state = _transition(None, None, requested)
        rnd = 1
        if opts.skill:
            metadata["skill"] = opts.skill
        task_id = None
        claim_id = None
        thread = None
    else:
        task = _find_task(tasks, opts.task, context)
        requested = opts.state or ("input-required" if opts.to else "working")
        state = _transition(task.id, task.state, requested)
        rnd = room_schema.next_round(task, agent)
        max_rounds = _max_rounds(opts, root)
        if room_schema.at_round_cap(task, agent, max_rounds):
            capped = _message(
                context, agent, "round cap (%d) reached" % max_rounds,
                task.id, {"state": "failed", "reason": "round-cap",
                          "round": rnd})
            _post_message(gh, repo, number, capped, _login(gh, memo),
                          role, thread=_finding_root(comments, task))
            raise RoomError("round cap reached on task %s — posted failed "
                            "(round-cap)" % task.id)
        task_id = task.id
        thread = _finding_root(comments, task)
        claim_id = (_own_claim(comments, task, agent)
                    if state != "working" else None)
    metadata.update({"state": state, "round": rnd})
    if opts.to:
        metadata["to"] = opts.to
    resp = _post_message(gh, repo, number,
                         _message(context, agent, opts.text, task_id,
                                  metadata), _login(gh, memo), role,
                         thread=thread)
    _drop_claim(gh, repo, claim_id)
    if state == "completed" and thread is not None:
        _resolve_finding_thread(gh, repo, number, thread)
    opened = task_id if task_id is not None else (resp or {}).get("id")
    _emit(_reply_result(resp, opened, state, rnd))
    sys.stderr.write("posted %s on task %s in %s\n" % (state, opened, context))
    return 0


def cmd_close(opts, parser, gh):
    root = _root(opts)
    agent = _agent_name(opts, parser, root)
    repo, number, context = _resolve_room(gh, opts.pr, opts.repo)
    cards, tasks, _raw, comments = _read_room(gh, repo, number)
    _require_card(cards, agent, context)
    task = _find_task(tasks, opts.task, context)
    requested = opts.state or "completed"
    state = _transition(task.id, task.state, requested)
    rnd = room_schema.next_round(task, agent)
    claim_id = _own_claim(comments, task, agent)
    metadata = {"state": state, "round": rnd}
    if opts.reason:
        metadata["reason"] = opts.reason
    text = opts.text
    if not text:
        text = "closed: %s" % requested
        if opts.reason:
            text += " — %s" % opts.reason
    resp = _post_message(gh, repo, number,
                         _message(context, agent, text, task.id, metadata),
                         _login(gh, {}), _card_role(cards, agent),
                         thread=_finding_root(comments, task))
    _drop_claim(gh, repo, claim_id)
    thread = _finding_root(comments, task)
    if state == "completed" and thread is not None:
        _resolve_finding_thread(gh, repo, number, thread)
    _emit(_reply_result(resp, task.id, state, rnd))
    sys.stderr.write("closed task %s as %s in %s\n" % (task.id, state,
                                                       context))
    return 0


def _cursor_text(cursor):
    return "%d:%d" % cursor


def _advance(cursor, comments):
    """``cursor`` with each component raised to the highest id read from
    its endpoint."""
    issue, review = cursor
    for comment in comments:
        cid = comment.get("id")
        if not isinstance(cid, int):
            continue
        if _endpoint(comment) == "review":
            review = max(review, cid)
        else:
            issue = max(issue, cid)
    return issue, review


def _is_new(comment, cursor):
    """True when ``comment``'s id exceeds the cursor component for the
    endpoint it was read from."""
    component = cursor[1] if _endpoint(comment) == "review" else cursor[0]
    cid = comment.get("id")
    return isinstance(cid, int) and cid > component


def _watch_line(task, comment, context, cursor):
    """One NDJSON line for a surfaced task: the ``list --json`` task fields
    plus ``task``, ``context``, ``comment``, ``text``, ``url``, ``cursor``."""
    obj = _task_dict(task)
    obj.update({
        "task": task.id,
        "context": context,
        "comment": comment.get("id"),
        "text": task.messages[-1].text if task.messages else "",
        "url": comment.get("html_url"),
        "cursor": _cursor_text(cursor),
    })
    return json.dumps(obj, sort_keys=True)


def _cap_task(gh, repo, number, context, agent, card, task, max_rounds,
              warned, memo, comments=()):
    """Close a task at the round cap: post ``failed``/``round-cap`` on it
    when ``agent`` has a card, else warn that someone must join to close
    it — once per task per watch, tracked in the ``warned`` id set. Either
    way the caller does not surface the task."""
    if card is None:
        if task.id not in warned:
            warned.add(task.id)
            cli_common.warn("task %s: round cap reached; join the room to "
                            "close it" % task.id)
        return
    capped = _message(
        context, agent, "round cap (%d) reached" % max_rounds, task.id,
        {"state": "failed", "reason": "round-cap",
         "round": room_schema.next_round(task, agent)})
    _post_message(gh, repo, number, capped, _login(gh, memo), card.role,
                  thread=_finding_root(comments, task))
    sys.stderr.write("task %s: round cap reached — posted failed "
                     "(round-cap)\n" % task.id)


def _pr_closed(gh, repo, number):
    """``"merged"`` or ``"closed"`` when the pull request has ended, else
    ``None``."""
    data = _gh_json(gh, ["pr", "view", str(number), "--json", "state",
                     "--repo", repo],
                    what="gh pr view %s" % number)
    state = (data or {}).get("state") if isinstance(data, dict) else None
    return {"MERGED": "merged", "CLOSED": "closed"}.get(state)


def cmd_watch(opts, gh, sleep, clock, parser):
    if not opts.interval > 0:
        parser.error("--interval must be greater than 0, got %s"
                     % opts.interval)
    root = _root(opts)
    agent = _agent_name(opts, parser, root)
    max_rounds = _max_rounds(opts, root)
    repo, number, context = _resolve_room(gh, opts.pr, opts.repo)
    cursor = opts.since
    warned = set()
    memo = {}
    start = clock()
    while True:
        comments = _read_comments(gh, repo, number)
        cards, tasks = _room_from_comments(comments)
        card = next((c for c in cards if c.name == agent), None)
        skills = tuple(card.skills) if card is not None else ()
        surfaced = []
        for task in actionable_tasks(tasks, agent, skills):
            if room_schema.at_round_cap(task, agent, max_rounds):
                _cap_task(gh, repo, number, context, agent, card, task,
                          max_rounds, warned, memo, comments)
                continue
            comment = _last_comment(comments, task)
            if comment is not None and _is_new(comment, cursor):
                surfaced.append((task, comment))
        cursor = _advance(cursor, comments)
        ended = _pr_closed(gh, repo, number)
        for task, comment in surfaced:
            sys.stdout.write(
                _watch_line(task, comment, context, cursor) + "\n")
        if ended:
            unresolved = [t for t in tasks if t.state in OPEN_STATES]
            sys.stdout.write(json.dumps(
                {"closed": ended, "context": context,
                 "cursor": _cursor_text(cursor),
                 "open": [{"task": t.id, "state": t.state, "to": t.to,
                           "skill": t.skill} for t in unresolved]}) + "\n")
            sys.stdout.flush()
            if unresolved:
                sys.stderr.write("watch: %d unresolved task(s): %s\n" % (
                    len(unresolved), ", ".join(
                        "#%s %s" % (t.id, t.state) for t in unresolved)))
            sys.stderr.write("watch: %s is %s; the room is closed\n"
                             % (context, ended))
            return 0
        if surfaced:
            sys.stdout.flush()
            return 0
        if opts.once:
            break
        if opts.timeout is not None and clock() - start >= opts.timeout:
            break
        sleep(opts.interval)
    sys.stderr.write("watch: no actionable task on %s (cursor %s)\n"
                     % (context, _cursor_text(cursor)))
    return 0


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def _positive_int(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer, got %r"
                                         % value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1, got %d"
                                         % number)
    return number


def _cursor(value):
    """``<issue>:<review>`` (or a bare ``<issue>``) as an int pair."""
    parts = value.split(":")
    if len(parts) > 2:
        raise argparse.ArgumentTypeError(
            "must be <issue>:<review> or <issue>, got %r" % value)
    try:
        ids = [int(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError(
            "must be <issue>:<review> comment ids, got %r" % value)
    if any(i < 0 for i in ids):
        raise argparse.ArgumentTypeError(
            "comment ids must not be negative, got %r" % value)
    if len(ids) == 1:
        ids.append(0)
    return ids[0], ids[1]


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--agent", help="the acting agent's name (default: $%s, then the "
                        "room.agent config member)" % AGENT_ENV)
    common.add_argument(
        "--root", help="the directory whose layered config is read "
                       "(default: the working directory)")
    common.add_argument(
        "--repo", help="the repository as owner/name (default: the pull "
                       "request URL's, else the working directory's)")
    common.add_argument(
        "--max-rounds", type=_positive_int, dest="max_rounds",
        help="the turn cap per task (default: room.max_rounds, else 6)")

    parser = argparse.ArgumentParser(
        description="The PR room: agents taking turns over a pull "
                    "request's comment thread.")
    sub = parser.add_subparsers(dest="verb", metavar="<verb>")
    sub.required = True

    p = sub.add_parser("join", parents=[common],
                       help="post or refresh this agent's card")
    p.add_argument("pr", help="pull request number, URL, or branch")
    p.add_argument("--skill", action="append", default=[],
                   help="a skill id this agent handles (repeatable)")
    p.add_argument("--description", default="",
                   help="a line describing this agent")
    p.add_argument("--harness", default="",
                   help="the harness driving this agent")
    p.add_argument("--role", default="", choices=("",) + room_schema.ROLE_VALUES,
                   help="the agent's role: %s" % ", ".join(
                       room_schema.ROLE_VALUES))
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("list", parents=[common],
                       help="the room's cards and tasks")
    p.add_argument("pr", help="pull request number, URL, or branch")
    p.add_argument("--json", action="store_true",
                   help="emit one JSON object instead of text")
    p.add_argument("--open", action="store_true",
                   help="list only tasks still working or input-required")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("message", parents=[common],
                       help="open a task or advance one")
    p.add_argument("pr", help="pull request number, URL, or branch")
    which = p.add_mutually_exclusive_group(required=True)
    which.add_argument("--new", action="store_true",
                       help="open a new task")
    which.add_argument("--task", type=int, metavar="ID",
                       help="reply on an existing task")
    p.add_argument("--to", metavar="AGENT",
                   help="the addressee, an agent or a human login")
    p.add_argument("--state", choices=room_schema.STATES,
                   help="the task state to post (default: input-required "
                        "with --to, else submitted for --new and working "
                        "for --task)")
    p.add_argument("--skill", help="the skill a new task asks for")
    p.add_argument("text", help="the message text")
    p.set_defaults(func=cmd_message)

    p = sub.add_parser("close", parents=[common],
                       help="post a task's terminal message")
    p.add_argument("pr", help="pull request number, URL, or branch")
    p.add_argument("--task", type=int, metavar="ID", required=True,
                   help="the task to close")
    p.add_argument("--state", choices=CLOSE_STATES,
                   help="the terminal state (default: completed)")
    p.add_argument("--reason", help="why the task closed")
    p.add_argument("text", nargs="?", default=None,
                   help="the message text (default: closed: <state>)")
    p.set_defaults(func=cmd_close)

    p = sub.add_parser("watch", parents=[common],
                       help="wait for a task that is this agent's turn")
    p.add_argument("pr", help="pull request number, URL, or branch")
    p.add_argument("--since", type=_cursor, default=(0, 0),
                   metavar="CURSOR",
                   help="surface only tasks whose last comment is newer "
                        "than <issue>:<review> comment ids (a bare integer "
                        "is the issue id; default: 0:0, the backlog)")
    p.add_argument("--interval", type=float, default=30.0, metavar="S",
                   help="seconds between polls (default: 30)")
    p.add_argument("--timeout", type=float, default=None, metavar="S",
                   help="stop after this many seconds with no task "
                        "(default: no limit)")
    p.add_argument("--once", action="store_true",
                   help="poll once and stop")
    p.set_defaults(func=None)

    return parser, sub.choices


def main(argv=None, gh=None, sleep=time.sleep, clock=time.monotonic):
    parser, verbs = build_parser()
    opts = parser.parse_args(argv)
    gh = gh or _default_gh
    try:
        if opts.verb == "watch":
            return cmd_watch(opts, gh, sleep, clock, verbs["watch"])
        return opts.func(opts, verbs[opts.verb], gh)
    except RoomError as exc:
        cli_common.err(str(exc))
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
