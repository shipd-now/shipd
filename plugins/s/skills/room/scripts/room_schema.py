#!/usr/bin/env python3
"""room_schema — the A2A-shaped data model of the PR room.

A PR room is a pull request's comment thread used as a message bus between
agents. Every room comment carries a hidden HTML-comment marker on its first
line — ``<!-- shipd-room <json> -->`` for a Message, ``<!-- shipd-room-card
<json> -->`` for an Agent Card — followed by a blank line and the human prose.

This module is pure standard library with no I/O: it never spawns a process,
touches the filesystem, or opens a network connection. It parses and renders
comment bodies, folds a comment chain into Task views, and owns the task state
machine and the round cap. Callers (the ``shipd room`` verbs, ``watch``, the
gate) do the fetching and posting.

An agent Message's prose opens with a speaker heading, ``### ☕ <agent>[ ·
<role>][ (for @<login>)]``, and ends with the ``FOOTER`` paragraph; the role
and login are render arguments, so a Message marker never stores them. An
Agent Card's prose is one ``<sub>`` line with no heading, role, or login; the
card marker carries its own optional ``role``.
"""

import json
import re
from dataclasses import dataclass, field

MESSAGE_MARKER = "shipd-room"
CARD_MARKER = "shipd-room-card"

# The GraphQL mutation that resolves a review thread; owned here so the room
# verbs and ``review_gate.py resolve`` send the same text.
RESOLVE_THREAD_MUTATION = """
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) { thread { isResolved } }
}
"""

STATES = (
    "submitted",
    "working",
    "input-required",
    "completed",
    "failed",
    "canceled",
)
TERMINAL_STATES = ("completed", "failed", "canceled")
ROLES = ("user", "agent")

# The states a task may open in: a plain opener is `submitted`; an opener
# addressed to another agent with `--to` opens straight at `input-required`.
OPENING_STATES = ("submitted", "input-required")

# The first room marker anywhere in a body. The rendered JSON never holds a
# `>` (``_dump`` escapes it), so the first ` -->` on the line closes it.
_MARKER_RE = re.compile(
    r"<!-- (%s|%s) ([^\n]*?) -->" % (re.escape(CARD_MARKER),
                                     re.escape(MESSAGE_MARKER)))


class SchemaError(ValueError):
    """A room marker that does not parse, or an object that fails validation."""


class InvalidTransition(SchemaError):
    """A task state change the transition table does not allow."""


# ---------------------------------------------------------------------------
# Marker wire format
# ---------------------------------------------------------------------------

def _dump(obj):
    """Compact, key-sorted JSON with every ``>`` escaped as ``\\u003e``, so no
    text inside it can close the surrounding HTML comment."""
    text = json.dumps(obj, separators=(",", ":"), sort_keys=True)
    return text.replace(">", "\\u003e")


def render_marker(kind, obj):
    """The one-line hidden marker ``<!-- <kind> <json> -->``."""
    if kind not in (MESSAGE_MARKER, CARD_MARKER):
        raise SchemaError("unknown room marker kind: %r" % (kind,))
    return "<!-- %s %s -->" % (kind, _dump(obj))


def _decode(match):
    kind, raw = match.group(1), match.group(2)
    try:
        obj = json.loads(raw)
    except ValueError as exc:
        raise SchemaError("malformed %s marker JSON: %s" % (kind, exc))
    if not isinstance(obj, dict):
        raise SchemaError("%s marker JSON is not an object" % kind)
    return kind, obj


def find_marker(body):
    """``(kind, dict)`` for the first room marker anywhere in ``body``, or
    ``None`` when it carries none. Raises ``SchemaError`` on bad JSON."""
    match = _MARKER_RE.search(body or "")
    if match is None:
        return None
    return _decode(match)


def _find_markers(body):
    return [_decode(match) for match in _MARKER_RE.finditer(body or "")]


# ---------------------------------------------------------------------------
# Agent Card
# ---------------------------------------------------------------------------

@dataclass
class AgentCard:
    name: str
    description: str = ""
    skills: tuple = ()
    version: str = ""
    harness: str = ""
    role: str = ""
    extra: dict = field(default_factory=dict)


_CARD_KEYS = ("name", "description", "skills", "version", "harness", "role")

# The roles `room join --role` accepts; the schema itself takes any string.
ROLE_VALUES = ("author", "reviewer", "ci")

# The closing paragraph of every agent Message comment.
FOOTER = "<sub>\u2615 Posted by Shipd</sub>"


def speaker_heading(agent, role="", login="", brand=False):
    """The speaker heading text (no markdown prefix): ``☕ agent``, then
    `` · role`` and `` (for @login)`` when those are set. ``brand=True``
    keeps the brand word: ``☕ shipd · agent``."""
    heading = "\u2615 shipd \u00b7 %s" % agent if brand \
        else "\u2615 %s" % agent
    if role:
        heading += " \u00b7 %s" % role
    if login:
        heading += " (for @%s)" % login
    return heading


def _str_field(d, key, what):
    value = d.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SchemaError("%s %s must be a string" % (what, key))
    return value


def card_from_dict(d):
    """Validate a card marker's dict into an ``AgentCard``."""
    if not isinstance(d, dict):
        raise SchemaError("agent card is not an object")
    name = d.get("name")
    if not isinstance(name, str) or not name.strip():
        raise SchemaError("agent card needs a non-empty name")
    skills = d.get("skills", ())
    if skills is None:
        skills = ()
    if isinstance(skills, str) or not isinstance(skills, (list, tuple)) or \
            not all(isinstance(s, str) for s in skills):
        raise SchemaError("agent card skills must be a list of skill ids")
    return AgentCard(
        name=name,
        description=_str_field(d, "description", "agent card"),
        skills=tuple(skills),
        version=_str_field(d, "version", "agent card"),
        harness=_str_field(d, "harness", "agent card"),
        role=_str_field(d, "role", "agent card"),
        extra={k: v for k, v in d.items() if k not in _CARD_KEYS},
    )


def card_to_dict(card):
    """The card's marker dict: the known keys plus every ``extra`` key."""
    d = dict(card.extra)
    d.update({
        "name": card.name,
        "description": card.description,
        "skills": list(card.skills),
        "version": card.version,
        "harness": card.harness,
    })
    if card.role:
        d["role"] = card.role
    return d


def _card_prose(card):
    line = "\u2615 **%s** joined the room" % card.name
    if card.harness:
        line += " from %s" % card.harness
    if card.skills:
        line += " · skills: %s" % ", ".join(card.skills)
    line = "<sub>%s</sub>" % line
    if card.description:
        return "%s\n\n%s" % (line, card.description)
    return line


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

@dataclass
class Message:
    role: str
    parts: tuple
    context_id: object
    agent: object
    task_id: object = None
    metadata: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    @property
    def state(self):
        return self.metadata.get("state")

    @property
    def to(self):
        return self.metadata.get("to")

    @property
    def round(self):
        return self.metadata.get("round")

    @property
    def reason(self):
        return self.metadata.get("reason")

    @property
    def skill(self):
        return self.metadata.get("skill")

    @property
    def text(self):
        """The text parts joined with blank lines — the rendered prose."""
        return "\n\n".join(
            part.get("text", "") for part in self.parts
            if isinstance(part, dict) and part.get("kind") == "text")


# Wire key -> field name; the wire keys are the A2A Message names.
_MESSAGE_KEYS = {
    "role": "role",
    "parts": "parts",
    "contextId": "context_id",
    "taskId": "task_id",
    "agent": "agent",
    "metadata": "metadata",
}


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def message_from_dict(d):
    """Validate a Message marker's dict into a ``Message``."""
    if not isinstance(d, dict):
        raise SchemaError("message is not an object")
    role = d.get("role")
    if role not in ROLES:
        raise SchemaError("message role must be one of %s, got %r"
                          % (", ".join(ROLES), role))
    parts = d.get("parts", ())
    if parts is None:
        parts = ()
    if not isinstance(parts, (list, tuple)) or not all(
            isinstance(part, dict) for part in parts):
        raise SchemaError("message parts must be a list of objects")
    for part in parts:
        if part.get("kind") == "text" and not isinstance(
                part.get("text", ""), str):
            raise SchemaError("message text part text must be a string")
    metadata = d.get("metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise SchemaError("message metadata must be an object")
    task_id = d.get("taskId")
    if task_id is not None and not _is_int(task_id):
        raise SchemaError("message taskId must be an int or null")
    context_id = d.get("contextId")
    agent = d.get("agent")
    if role == "agent":
        if not isinstance(agent, str) or not agent:
            raise SchemaError("an agent message needs an agent")
        if not isinstance(context_id, str) or not context_id:
            raise SchemaError("an agent message needs a contextId")
        if metadata.get("state") not in STATES:
            raise SchemaError("message metadata.state must be one of %s, "
                              "got %r" % (", ".join(STATES),
                                          metadata.get("state")))
    if "round" in metadata:
        rnd = metadata["round"]
        if not _is_int(rnd) or rnd < 1:
            raise SchemaError("message metadata.round must be an int >= 1, "
                              "got %r" % (rnd,))
    return Message(
        role=role,
        parts=tuple(dict(part) for part in parts),
        context_id=context_id,
        agent=agent,
        task_id=task_id,
        metadata=dict(metadata),
        extra={k: v for k, v in d.items() if k not in _MESSAGE_KEYS},
    )


def message_to_dict(m):
    """The Message's marker dict under the A2A wire keys, plus ``extra``."""
    d = dict(m.extra)
    d.update({
        "role": m.role,
        "parts": [dict(part) for part in m.parts],
        "contextId": m.context_id,
        "taskId": m.task_id,
        "agent": m.agent,
        "metadata": dict(m.metadata),
    })
    return d


def _message_prose(m, login="", role=""):
    if m.role != "agent":
        return m.text
    lines = ["### " + speaker_heading(m.agent, role, login)]
    if m.to and m.state:
        lines.append("\u2192 %s \u00b7 %s" % (m.to, m.state))
    elif m.to:
        lines.append("\u2192 %s" % m.to)
    elif m.state:
        lines.append(m.state)
    return "%s\n\n%s\n\n%s" % ("\n".join(lines), m.text, FOOTER)


# ---------------------------------------------------------------------------
# Parse / render
# ---------------------------------------------------------------------------

def _from_marker(kind, obj):
    if kind == CARD_MARKER:
        return card_from_dict(obj)
    return message_from_dict(obj)


def _human_message(body, author):
    return Message(
        role="user",
        parts=({"kind": "text", "text": (body or "").strip()},),
        context_id=None,
        agent=author,
        task_id=None,
    )


def parse_comments(body, author=None):
    """Every room marker's parsed object in body order. A body with no marker
    is one human message: ``[Message(role="user", ...)]``."""
    found = _find_markers(body)
    if not found:
        return [_human_message(body, author)]
    return [_from_marker(kind, obj) for kind, obj in found]


def parse_comment(body, author=None):
    """The ``AgentCard`` or ``Message`` held by the first room marker in
    ``body``; an unmarked body is a ``user`` Message from ``author``.
    Raises ``SchemaError`` on a malformed or invalid marker."""
    return parse_comments(body, author)[0]


def render_comment(obj, login="", role=""):
    """A room comment body: the marker on line 1, a blank line, the prose.
    ``login`` and ``role`` head a Message's speaker heading and are ignored
    for a card. Neither is written into a Message marker.
    The object is validated first, so an invalid one raises ``SchemaError``."""
    if isinstance(obj, AgentCard):
        d = card_to_dict(obj)
        card_from_dict(d)
        return "%s\n\n%s" % (render_marker(CARD_MARKER, d), _card_prose(obj))
    if isinstance(obj, Message):
        d = message_to_dict(obj)
        message_from_dict(d)
        return "%s\n\n%s" % (render_marker(MESSAGE_MARKER, d),
                             _message_prose(obj, login, role))
    raise SchemaError("cannot render %r as a room comment" % (obj,))


# ---------------------------------------------------------------------------
# Task view
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: int
    context_id: object
    opener: object
    skill: object
    messages: list
    state: object
    to: object
    round: int
    reason: object
    last_agent: object


def build_tasks(entries):
    """Fold ``(comment_id, Message)`` pairs, in comment order, into ``Task``
    views ordered by id. An agent Message with no ``task_id`` opens a task
    whose id is its own comment id; a Message naming an opened task is
    appended to it. ``user`` Messages, and Messages naming a task not seen —
    the caller may have paged only part of the PR — are skipped."""
    chains = {}
    for comment_id, message in entries:
        if not isinstance(message, Message) or message.role != "agent":
            continue
        if message.task_id is None:
            chains.setdefault(comment_id, [message])
        elif message.task_id in chains:
            chains[message.task_id].append(message)
    tasks = []
    for task_id in sorted(chains):
        messages = chains[task_id]
        opener, last = messages[0], messages[-1]
        # The last round any message carried: one post that omits it must
        # not reset the task to round 1 and lapse the round cap.
        rnd = next((m.round for m in reversed(messages)
                    if m.round is not None), None)
        tasks.append(Task(
            id=task_id,
            context_id=opener.context_id,
            opener=opener.agent,
            skill=opener.skill,
            messages=list(messages),
            state=last.state,
            to=last.to,
            round=rnd if rnd is not None else 1,
            reason=last.reason,
            last_agent=last.agent,
        ))
    return tasks


# ---------------------------------------------------------------------------
# State machine and rounds
# ---------------------------------------------------------------------------

def is_terminal(state):
    """True for an absorbing state: ``completed``, ``failed``, ``canceled``."""
    return state in TERMINAL_STATES


def next_state(current, requested):
    """The only transition table. A new task (``current`` ``None``) opens at
    ``submitted`` or ``input-required``; a non-terminal task may move to any
    state except ``submitted``; a terminal task accepts nothing. Returns the
    accepted state or raises ``InvalidTransition``."""
    if requested not in STATES:
        raise InvalidTransition("unknown task state %r" % (requested,))
    if current is None:
        if requested in OPENING_STATES:
            return requested
        raise InvalidTransition(
            "a task opens at %s, not %r" % (" or ".join(OPENING_STATES),
                                             requested))
    if is_terminal(current):
        raise InvalidTransition(
            "task is %s; a terminal state accepts no transition" % current)
    if current not in STATES:
        raise InvalidTransition("unknown current task state %r" % (current,))
    if requested == "submitted":
        raise InvalidTransition(
            "%s -> submitted: only a new task is submitted" % current)
    return requested


def next_round(task, agent):
    """The round ``agent``'s next post carries: a round is a turn, so the same
    agent keeps ``task.round`` and a different agent advances it by one."""
    if agent == task.last_agent:
        return task.round
    return task.round + 1


def at_round_cap(task, agent, max_rounds):
    """True when ``agent``'s next post would exceed ``max_rounds``."""
    return next_round(task, agent) > max_rounds
