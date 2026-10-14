#!/usr/bin/env python3
"""room — the ``shipd room`` verbs over a pull request's comment thread.

A PR room is a pull request's comment thread used as a message bus between
agents (see ``room_schema``). This script is the harness-agnostic surface an
agent drives to take part in one:

  join <pr>      post or refresh this agent's card
  list <pr>      the room's cards and tasks
  message <pr>   open a task (``--new``) or advance one (``--task ID``)
  close <pr>     post a task's terminal message

Every GitHub read and write goes through one injectable ``gh`` runner,
``gh(args, input=None) -> (rc, stdout, stderr)``, defaulting to the ``gh``
CLI, so the test suite drives the verbs against a fake and reaches no
network. Comment bodies are only ever built by ``room_schema.render_comment``.

Mutating verbs print one JSON object on stdout and one human line on stderr;
a fatal outcome is one ``Error: <reason>`` line and exit ``1``; invalid
arguments exit ``2`` with usage text.
"""

import argparse
import json
import os
import subprocess
import sys

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


class RoomError(Exception):
    """A fatal room outcome, reported once as an ``Error:`` line (exit 1)."""


# ---------------------------------------------------------------------------
# The gh seam
# ---------------------------------------------------------------------------

def _default_gh(args, input=None):
    proc = subprocess.run(
        ["gh"] + list(args), input=input, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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


def _resolve_room(gh, pr):
    """``(repo, number, context)`` for ``pr``; the context id is
    ``<owner>/<repo>#<number>``."""
    pr_data = _gh_json(gh, ["pr", "view", str(pr), "--json", "number,url"],
                       what="gh pr view %s" % pr)
    repo_data = _gh_json(gh, ["repo", "view", "--json", "nameWithOwner"],
                         what="gh repo view")
    try:
        number = int(pr_data["number"])
        repo = repo_data["nameWithOwner"]
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


def _read_room(gh, repo, number):
    """Read the room once: ``(cards, tasks, raw)``.

    The room is the union of the PR's issue comments (room traffic) and its
    review comments (the semantic-review gate's finding tasks), ordered by
    comment id. ``cards`` holds the last card per agent name, ``tasks`` the
    ``build_tasks`` view, and ``raw`` maps a card name to the issue comment id
    holding it, for the join upsert. A comment whose marker does not parse is
    warned about and skipped."""
    issue = _list_comments(gh, "repos/%s/issues/%d/comments" % (repo, number))
    review = _list_comments(gh, "repos/%s/pulls/%d/comments" % (repo, number))
    tagged = [(c, True) for c in issue] + [(c, False) for c in review]
    tagged.sort(key=lambda pair: pair[0].get("id") or 0)
    cards = {}
    raw = {}
    entries = []
    for comment, is_issue in tagged:
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
                if is_issue:
                    raw[obj.name] = comment_id
            else:
                entries.append((comment_id, obj))
    return list(cards.values()), room_schema.build_tasks(entries), raw


def _post(gh, repo, number, body):
    """Create an issue comment; the parsed response (``id``, ``html_url``)."""
    return _gh_json(
        gh, ["api", "-X", "POST",
             "repos/%s/issues/%d/comments" % (repo, number), "--input", "-"],
        input=json.dumps({"body": body}), what="posting a room comment")


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
        raise RoomError("task %s is %s; no transition to %s"
                        % (task_id, current, requested))


def _message(context, agent, text, task_id, metadata):
    return room_schema.Message(
        role="agent", parts=({"kind": "text", "text": text},),
        context_id=context, agent=agent, task_id=task_id, metadata=metadata)


def _emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")


def _post_message(gh, repo, number, message):
    try:
        body = room_schema.render_comment(message)
    except room_schema.SchemaError as exc:
        raise RoomError(str(exc))
    return _post(gh, repo, number, body)


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------

def cmd_join(opts, parser, gh):
    root = _root(opts)
    agent = _agent_name(opts, parser, root)
    repo, number, context = _resolve_room(gh, opts.pr)
    _cards, _tasks, raw = _read_room(gh, repo, number)
    card = room_schema.AgentCard(
        name=agent, description=opts.description or "",
        skills=tuple(opts.skill or ()), version=_plugin_version(),
        harness=opts.harness or "")
    try:
        body = room_schema.render_comment(card)
    except room_schema.SchemaError as exc:
        raise RoomError(str(exc))
    if agent in raw:
        resp = _patch(gh, repo, raw[agent], body)
    else:
        resp = _post(gh, repo, number, body)
    resp = resp or {}
    _emit({"comment": resp.get("id", raw.get(agent)), "agent": agent,
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
    return "%s  harness %s  skills %s  version %s" % (
        card.name, card.harness or "-",
        ",".join(card.skills) if card.skills else "-", card.version or "-")


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
    repo, number, context = _resolve_room(gh, opts.pr)
    cards, tasks, _raw = _read_room(gh, repo, number)
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
    repo, number, context = _resolve_room(gh, opts.pr)
    cards, tasks, _raw = _read_room(gh, repo, number)
    _require_card(cards, agent, context)
    metadata = {}
    if opts.new:
        requested = opts.state or (
            "input-required" if opts.to else "submitted")
        state = _transition("(new)", None, requested)
        rnd = 1
        if opts.skill:
            metadata["skill"] = opts.skill
        task_id = None
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
            _post_message(gh, repo, number, capped)
            raise RoomError("round cap reached on task %s — posted failed "
                            "(round-cap)" % task.id)
        task_id = task.id
    metadata.update({"state": state, "round": rnd})
    if opts.to:
        metadata["to"] = opts.to
    resp = _post_message(gh, repo, number,
                         _message(context, agent, opts.text, task_id,
                                  metadata))
    opened = task_id if task_id is not None else (resp or {}).get("id")
    _emit(_reply_result(resp, opened, state, rnd))
    sys.stderr.write("posted %s on task %s in %s\n" % (state, opened, context))
    return 0


def cmd_close(opts, parser, gh):
    root = _root(opts)
    agent = _agent_name(opts, parser, root)
    repo, number, context = _resolve_room(gh, opts.pr)
    cards, tasks, _raw = _read_room(gh, repo, number)
    _require_card(cards, agent, context)
    task = _find_task(tasks, opts.task, context)
    requested = opts.state or "completed"
    state = _transition(task.id, task.state, requested)
    rnd = room_schema.next_round(task, agent)
    metadata = {"state": state, "round": rnd}
    if opts.reason:
        metadata["reason"] = opts.reason
    text = opts.text
    if not text:
        text = "closed: %s" % requested
        if opts.reason:
            text += " — %s" % opts.reason
    resp = _post_message(gh, repo, number,
                         _message(context, agent, text, task.id, metadata))
    _emit(_reply_result(resp, task.id, state, rnd))
    sys.stderr.write("closed task %s as %s in %s\n" % (task.id, state,
                                                       context))
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


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--agent", help="the acting agent's name (default: $%s, then the "
                        "room.agent config member)" % AGENT_ENV)
    common.add_argument(
        "--root", help="the directory whose layered config is read "
                       "(default: the working directory)")
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
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("list", parents=[common],
                       help="the room's cards and tasks")
    p.add_argument("pr", help="pull request number, URL, or branch")
    p.add_argument("--json", action="store_true",
                   help="emit one JSON object instead of text")
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

    return parser, sub.choices


def main(argv=None, gh=None):
    parser, verbs = build_parser()
    opts = parser.parse_args(argv)
    gh = gh or _default_gh
    try:
        return opts.func(opts, verbs[opts.verb], gh)
    except RoomError as exc:
        cli_common.err(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
