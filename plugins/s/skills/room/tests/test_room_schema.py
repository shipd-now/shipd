#!/usr/bin/env python3
"""Tests for room_schema.py — the pure-stdlib data model of the PR room.

The module under test performs no I/O, so no test here touches a process,
the filesystem beyond reading the module's own source, or the network.
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import room_schema  # noqa: E402

MODULE_PATH = os.path.join(SCRIPTS, "room_schema.py")


class ModuleContractTests(unittest.TestCase):
    def test_no_process_or_network_imports(self):
        with open(MODULE_PATH) as fh:
            source = fh.read()
        for name in ("subprocess", "urllib", "http", "socket"):
            pattern = r"^\s*(import|from)\s+%s\b" % name
            self.assertIsNone(
                re.search(pattern, source, re.MULTILINE),
                "room_schema.py must not import %s" % name)

    def test_constants_exist(self):
        self.assertEqual(
            set(room_schema.STATES),
            {"submitted", "working", "input-required",
             "completed", "failed", "canceled"})
        self.assertEqual(
            set(room_schema.TERMINAL_STATES),
            {"completed", "failed", "canceled"})
        self.assertEqual(set(room_schema.ROLES), {"user", "agent"})
        self.assertEqual(room_schema.MESSAGE_MARKER, "shipd-room")
        self.assertEqual(room_schema.CARD_MARKER, "shipd-room-card")


CONTEXT = "acme/widgets#7"


def _agent_msg(text="hello", agent="a", task_id=None, **metadata):
    metadata.setdefault("state", "submitted")
    return room_schema.Message(
        role="agent",
        parts=({"kind": "text", "text": text},),
        context_id=CONTEXT,
        agent=agent,
        task_id=task_id,
        metadata=metadata)


class MarkerFormatTests(unittest.TestCase):
    def test_round_trip_escapes_comment_close(self):
        msg = _agent_msg(text="a --> b")
        rendered = room_schema.render_comment(msg)
        first = rendered.split("\n", 1)[0]
        self.assertRegex(first, r"^<!-- shipd-room \{.*\} -->$")
        self.assertEqual(first.count("-->"), 1)
        self.assertTrue(first.endswith(" -->"))
        self.assertEqual(room_schema.parse_comment(rendered), msg)

    def test_rendered_body_is_marker_blank_line_prose(self):
        msg = _agent_msg(text="the prose")
        lines = room_schema.render_comment(msg).split("\n")
        self.assertEqual(lines[1], "")
        self.assertEqual("\n".join(lines[2:]), "the prose")

    def test_marker_below_severity_line_parses(self):
        msg = _agent_msg(text="finding")
        marker = room_schema.render_marker(
            room_schema.MESSAGE_MARKER, room_schema.message_to_dict(msg))
        body = "**● high — x**\n\n" + marker
        self.assertEqual(room_schema.parse_comment(body), msg)

    def test_unmarked_body_is_human_message(self):
        msg = room_schema.parse_comment("looks good", author="octocat")
        self.assertIsInstance(msg, room_schema.Message)
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.agent, "octocat")
        self.assertEqual(msg.text, "looks good")
        self.assertIsNone(msg.task_id)
        self.assertIsNone(msg.context_id)

    def test_malformed_marker_raises(self):
        with self.assertRaises(room_schema.SchemaError):
            room_schema.parse_comment("<!-- shipd-room {not json} -->")

    def test_find_marker_round_trip(self):
        obj = {"name": "x", "note": "a > b"}
        line = room_schema.render_marker(room_schema.CARD_MARKER, obj)
        self.assertNotIn(">", line[:-len(" -->")])
        self.assertEqual(
            room_schema.find_marker("lead\n" + line),
            (room_schema.CARD_MARKER, obj))
        self.assertIsNone(room_schema.find_marker("no marker here"))

    def test_parse_comments_returns_every_marker_in_order(self):
        card = room_schema.AgentCard(name="semantic-review")
        msg = _agent_msg(text="summary", agent="semantic-review")
        body = (room_schema.render_comment(card) + "\n\n"
                + room_schema.render_comment(msg))
        parsed = room_schema.parse_comments(body)
        self.assertEqual(parsed, [card, msg])
        self.assertEqual(room_schema.parse_comment(body), card)

    def test_parse_comments_unmarked_is_one_user_message(self):
        parsed = room_schema.parse_comments("looks good", author="octocat")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(
            parsed[0],
            room_schema.parse_comment("looks good", author="octocat"))
        self.assertEqual(parsed[0].role, "user")


def _marker_json(rendered):
    first = rendered.split("\n", 1)[0]
    match = re.match(r"^<!-- (shipd-room(?:-card)?) (.*) -->$", first)
    return match.group(1), match.group(2)


class AgentCardTests(unittest.TestCase):
    def test_card_renders_marker_and_prose(self):
        card = room_schema.AgentCard(
            name="codex-reviewer", harness="codex",
            skills=("review-finding",))
        rendered = room_schema.render_comment(card)
        kind, _ = _marker_json(rendered)
        self.assertEqual(kind, room_schema.CARD_MARKER)
        self.assertEqual(
            rendered.split("\n", 2)[2],
            "**codex-reviewer** joined the room from codex "
            "— skills: review-finding")
        self.assertEqual(room_schema.parse_comment(rendered), card)

    def test_card_prose_minimal_and_with_description(self):
        self.assertEqual(
            room_schema._card_prose(room_schema.AgentCard(name="x")),
            "**x** joined the room")
        self.assertEqual(
            room_schema._card_prose(room_schema.AgentCard(
                name="x", skills=("a", "b"), description="does things")),
            "**x** joined the room — skills: a, b\n\ndoes things")

    def test_nameless_card_raises(self):
        body = '<!-- shipd-room-card {"harness":"codex"} -->'
        with self.assertRaises(room_schema.SchemaError):
            room_schema.parse_comment(body)
        with self.assertRaises(room_schema.SchemaError):
            room_schema.parse_comment('<!-- shipd-room-card {"name":""} -->')

    def test_non_string_skill_raises(self):
        for skills in ('[{"id":"rev"}]', '[3]'):
            with self.assertRaises(room_schema.SchemaError):
                room_schema.parse_comment(
                    '<!-- shipd-room-card {"name":"x","skills":%s} -->'
                    % skills)

    def test_unknown_card_keys_round_trip(self):
        body = ('<!-- shipd-room-card {"name":"x","securitySchemes":'
                '{"bearer":{"type":"http"}}} -->')
        card = room_schema.parse_comment(body)
        self.assertEqual(
            card.extra, {"securitySchemes": {"bearer": {"type": "http"}}})
        _, raw = _marker_json(room_schema.render_comment(card))
        self.assertIn('"securitySchemes":{"bearer":{"type":"http"}}', raw)
        self.assertEqual(
            room_schema.parse_comment(room_schema.render_comment(card)), card)


class MessageTests(unittest.TestCase):
    def _rendered_dict(self, msg):
        import json
        _, raw = _marker_json(room_schema.render_comment(msg))
        return json.loads(raw)

    def test_state_lives_in_metadata(self):
        msg = _agent_msg(state="input-required", to="codex-reviewer", round=1)
        _, raw = _marker_json(room_schema.render_comment(msg))
        self.assertIn(
            '"metadata":{"round":1,"state":"input-required",'
            '"to":"codex-reviewer"}', raw)
        d = self._rendered_dict(msg)
        self.assertNotIn("state", d)
        self.assertEqual(
            sorted(d),
            ["agent", "contextId", "metadata", "parts", "role", "taskId"])

    def test_properties_read_metadata(self):
        msg = _agent_msg(state="failed", to="b", round=2, reason="why",
                         skill="review-finding")
        self.assertEqual(
            (msg.state, msg.to, msg.round, msg.reason, msg.skill),
            ("failed", "b", 2, "why", "review-finding"))

    def _body(self, d):
        return room_schema.render_marker(room_schema.MESSAGE_MARKER, d)

    def _valid(self, **over):
        d = {"role": "agent", "parts": [{"kind": "text", "text": "x"}],
             "contextId": CONTEXT, "taskId": None, "agent": "a",
             "metadata": {"state": "working"}}
        d.update(over)
        return d

    def test_valid_dict_parses(self):
        msg = room_schema.parse_comment(self._body(self._valid()))
        self.assertEqual(msg.state, "working")

    def test_unknown_state_raises(self):
        with self.assertRaises(room_schema.SchemaError):
            room_schema.parse_comment(
                self._body(self._valid(metadata={"state": "open"})))

    def test_missing_agent_or_context_raises(self):
        for over in ({"agent": None}, {"agent": ""}, {"contextId": None}):
            d = self._valid(**over)
            with self.assertRaises(room_schema.SchemaError):
                room_schema.parse_comment(self._body(d))
        d = self._valid()
        del d["agent"]
        with self.assertRaises(room_schema.SchemaError):
            room_schema.parse_comment(self._body(d))

    def test_round_zero_raises(self):
        for rnd in (0, -1, "2", True):
            with self.assertRaises(room_schema.SchemaError):
                room_schema.parse_comment(self._body(
                    self._valid(metadata={"state": "working",
                                          "round": rnd})))

    def test_non_string_text_part_raises(self):
        for text in (5, None, ["x"]):
            with self.assertRaises(room_schema.SchemaError):
                room_schema.parse_comment(self._body(
                    self._valid(parts=[{"kind": "text", "text": text}])))

    def test_bad_role_raises(self):
        with self.assertRaises(room_schema.SchemaError):
            room_schema.parse_comment(self._body(self._valid(role="bot")))

    def test_non_text_parts_kept_not_rendered(self):
        msg = room_schema.Message(
            role="agent",
            parts=({"kind": "text", "text": "visible"},
                   {"kind": "data", "data": {"k": 1}}),
            context_id=CONTEXT, agent="a",
            metadata={"state": "submitted"})
        rendered = room_schema.render_comment(msg)
        self.assertEqual(rendered.split("\n", 2)[2], "visible")
        parsed = room_schema.parse_comment(rendered)
        self.assertEqual(len(parsed.parts), 2)
        self.assertEqual(parsed, msg)

    def test_text_joins_text_parts_with_blank_line(self):
        msg = room_schema.Message(
            role="agent",
            parts=({"kind": "text", "text": "one"},
                   {"kind": "text", "text": "two"}),
            context_id=CONTEXT, agent="a",
            metadata={"state": "submitted"})
        self.assertEqual(msg.text, "one\n\ntwo")

    def test_unknown_message_keys_preserved(self):
        d = self._valid(kind="message", messageId="m-1")
        msg = room_schema.parse_comment(self._body(d))
        self.assertEqual(msg.extra, {"kind": "message", "messageId": "m-1"})
        self.assertEqual(self._rendered_dict(msg)["messageId"], "m-1")


class TaskViewTests(unittest.TestCase):
    def test_reply_updates_the_task_view(self):
        opener = _agent_msg(agent="a", state="input-required", to="b",
                            round=1)
        human = room_schema.parse_comment("drive-by", author="octocat")
        reply = _agent_msg(agent="b", task_id=10, state="completed",
                           round=2)
        tasks = room_schema.build_tasks(
            [(10, opener), (11, human), (12, reply)])
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.id, 10)
        self.assertEqual(task.context_id, CONTEXT)
        self.assertEqual(task.opener, "a")
        self.assertEqual(task.state, "completed")
        self.assertIsNone(task.to)
        self.assertEqual(task.round, 2)
        self.assertEqual(task.last_agent, "b")
        self.assertEqual(task.messages, [opener, reply])

    def test_round_carried_when_last_message_omits_it(self):
        opener = _agent_msg(agent="a", state="input-required", to="b",
                            round=1)
        reply = _agent_msg(agent="b", task_id=10, state="input-required",
                           to="a", round=4)
        bare = _agent_msg(agent="a", task_id=10, state="working")
        task = room_schema.build_tasks(
            [(10, opener), (12, reply), (14, bare)])[0]
        self.assertEqual(task.round, 4)
        self.assertEqual(task.last_agent, "a")

    def test_orphan_reply_is_skipped(self):
        orphan = _agent_msg(agent="b", task_id=99, state="working")
        self.assertEqual(room_schema.build_tasks([(12, orphan)]), [])

    def test_opener_skill(self):
        opener = _agent_msg(agent="a", skill="review-finding")
        task = room_schema.build_tasks([(5, opener)])[0]
        self.assertEqual(task.skill, "review-finding")
        self.assertEqual(task.round, 1)
        self.assertEqual(task.state, "submitted")

    def test_tasks_ordered_by_id(self):
        tasks = room_schema.build_tasks(
            [(30, _agent_msg(agent="x")), (20, _agent_msg(agent="y"))])
        self.assertEqual([t.id for t in tasks], [20, 30])


def _task(round_, last_agent):
    return room_schema.Task(
        id=1, context_id=CONTEXT, opener="a", skill=None, messages=[],
        state="working", to=None, round=round_, reason=None,
        last_agent=last_agent)


class StateMachineTests(unittest.TestCase):
    NON_TERMINAL = ("submitted", "working", "input-required")

    def test_opener_states(self):
        self.assertEqual(
            room_schema.next_state(None, "input-required"), "input-required")
        self.assertEqual(
            room_schema.next_state(None, "submitted"), "submitted")
        for requested in ("working", "completed", "failed", "canceled"):
            with self.assertRaises(room_schema.InvalidTransition):
                room_schema.next_state(None, requested)

    def test_submitted_cannot_be_requested_again(self):
        for current in self.NON_TERMINAL:
            with self.assertRaises(room_schema.InvalidTransition):
                room_schema.next_state(current, "submitted")

    def test_non_terminal_accepts_every_other_state(self):
        for current in self.NON_TERMINAL:
            for requested in room_schema.STATES:
                if requested == "submitted":
                    continue
                self.assertEqual(
                    room_schema.next_state(current, requested), requested)

    def test_terminal_states_absorb(self):
        for current in room_schema.TERMINAL_STATES:
            self.assertTrue(room_schema.is_terminal(current))
            for requested in room_schema.STATES:
                with self.assertRaises(room_schema.InvalidTransition):
                    room_schema.next_state(current, requested)
        self.assertFalse(room_schema.is_terminal("working"))

    def test_unknown_state_request_raises(self):
        with self.assertRaises(room_schema.InvalidTransition):
            room_schema.next_state("working", "open")

    def test_invalid_transition_is_schema_error(self):
        self.assertTrue(issubclass(
            room_schema.InvalidTransition, room_schema.SchemaError))

    def test_same_agent_keeps_the_round(self):
        task = _task(3, "b")
        self.assertEqual(room_schema.next_round(task, "b"), 3)
        self.assertEqual(room_schema.next_round(task, "a"), 4)

    def test_cap_is_checked_before_posting(self):
        task = _task(6, "b")
        self.assertTrue(room_schema.at_round_cap(task, "a", 6))
        self.assertFalse(room_schema.at_round_cap(task, "b", 6))
