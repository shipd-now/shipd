#!/usr/bin/env python3
"""Tests for the room wake workflow template (pr-room
room-wake-workflow-template, room-wake-tests).

The template is read as text, split into its ``guard``, ``run`` and
``reply`` jobs, and the guard and reply ``run:`` scripts are executed under
``bash`` in a temporary working directory. That directory holds a recording
stub ``room.py`` at the bundled path the workflow runs,
``.github/shipd-room/skills/room/scripts/room.py``, and the workflow's
``/usr/bin/python3`` literal is rewritten to the interpreter running this
suite, the way the gate tests rewrite theirs. No network is reached and no
real ``gh`` or Copilot CLI runs.

Every ``room.py`` call runs under ``/usr/bin/env -i``, so the stub sees only
the environment the workflow hands it explicitly. ``HOME`` is one of those
variables, so the stub locates its argv log and its canned stdout through
``$HOME``, which each run points at its own temporary directory.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
TEMPLATE = os.path.join(PLUGIN_ROOT, "integrations", "copilot",
                        "room-wake.yml")

# The bundled runtime path the workflow runs, relative to its checkout.
ROOM_PY = os.path.join(".github", "shipd-room", "skills", "room", "scripts",
                       "room.py")
# The absolute interpreter the workflow names, rewritten for a test run.
PY_PATH = "/usr/bin/python3"

JOBS = ("guard", "run", "reply")
# The steps whose scripts the suite runs, by name.
GUARD_STEP = "Pick up the addressed task"
RUN_STEP = "Run the Copilot CLI on the task"
REPLY_STEP = "Post the reply to the room"

# The reply marker that hands a task back to its asker.
REPLY_MARKER = "<!-- shipd-room-reply: input-required -->"
# The pinned Copilot CLI, the gate's own pin.
CLI_PIN = "npm install -g @github/copilot@1.0.80"
# The isolated environment every room.py call runs in.
ENV_PREFIX = "/usr/bin/env -i PATH=/usr/bin:/bin"
# The secret, bound as a step environment value.
SECRET_BINDING = re.compile(
    r"^\s*COPILOT_GITHUB_TOKEN:\s*\$\{\{\s*secrets\.COPILOT_GITHUB_TOKEN"
    r"\s*\}\}\s*$", re.M)
WORKFLOW_TOKEN = re.compile(r"\$\{\{\s*github\.token\s*\}\}")


def read_template():
    with open(TEMPLATE, encoding="utf-8") as fh:
        return fh.read()


def split_jobs(text):
    """``{job name: job text}`` for the jobs under ``jobs:``, each job's text
    running from its ``  <name>:`` header to the next job header or the end
    of the file."""
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.rstrip() == "jobs:")
    except StopIteration:
        return {}
    header = re.compile(r"^  ([A-Za-z_][\w-]*):\s*$")
    jobs, name, body = {}, None, []
    for line in lines[start + 1:]:
        found = header.match(line)
        if found:
            if name is not None:
                jobs[name] = "".join(body)
            name, body = found.group(1), [line]
        elif name is not None:
            body.append(line)
    if name is not None:
        jobs[name] = "".join(body)
    return jobs


def step_run(job_text, step_name):
    """The ``run: |`` block of the step named ``step_name`` in
    ``job_text``, dedented, or ``""`` when there is no such step."""
    lines = job_text.splitlines()
    named = re.compile(r"^(\s*)- name:\s*(.+?)\s*$")
    for index, line in enumerate(lines):
        found = named.match(line)
        if not found or found.group(2) != step_name:
            continue
        step_indent = len(found.group(1))
        for follow in range(index + 1, len(lines)):
            current = lines[follow]
            pad = len(current) - len(current.lstrip())
            if current.strip() and pad <= step_indent:
                return ""
            if current.strip() != "run: |":
                continue
            block, indent = [], None
            for body in lines[follow + 1:]:
                if not body.strip():
                    block.append("")
                    continue
                body_pad = len(body) - len(body.lstrip())
                if body_pad <= pad:
                    break
                if indent is None:
                    indent = body_pad
                block.append(body[indent:])
            while block and not block[-1].strip():
                block.pop()
            return "\n".join(block) + "\n" if block else ""
        return ""
    return ""


def parse_outputs(text):
    """``{name: value}`` from a ``$GITHUB_OUTPUT`` file: ``name=value``
    lines and ``name<<DELIM`` … ``DELIM`` multi-line values."""
    outputs = {}
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if "<<" in line and ("=" not in line
                             or line.index("<<") < line.index("=")):
            name, delimiter = line.split("<<", 1)
            value = []
            while index < len(lines) and lines[index] != delimiter:
                value.append(lines[index])
                index += 1
            index += 1
            outputs[name] = "\n".join(value)
        elif "=" in line:
            name, value = line.split("=", 1)
            outputs[name] = value
    return outputs


# The recording stub for the bundled ``room.py``. It appends its argv and the
# environment it was handed as one JSON line to ``$HOME/room-calls.ndjson``,
# prints ``$HOME/room-<verb>.out`` when the test planted one, and exits with
# ``$HOME/room-<verb>.code`` (default 0).
STUB = r'''import json
import os
import sys

home = os.environ.get("HOME", "")
verb = sys.argv[1] if len(sys.argv) > 1 else ""
with open(os.path.join(home, "room-calls.ndjson"), "a",
          encoding="utf-8") as fh:
    fh.write(json.dumps({"argv": sys.argv[1:],
                         "env": dict(os.environ)}) + "\n")
canned = os.path.join(home, "room-%s.out" % verb)
if os.path.exists(canned):
    with open(canned, encoding="utf-8") as fh:
        sys.stdout.write(fh.read())
code = os.path.join(home, "room-%s.code" % verb)
if os.path.exists(code):
    with open(code, encoding="utf-8") as fh:
        sys.exit(int(fh.read().strip() or "0"))
'''


class WakeScriptCase(unittest.TestCase):
    """Base for the tests that *run* a wake job's script: a temporary
    checkout holding the stub ``room.py`` at its bundled path, a temporary
    ``$GITHUB_OUTPUT``, and a ``bash`` runner. Defines no tests of its own."""

    def setUp(self):
        self.assertTrue(os.path.isfile(TEMPLATE),
                        "missing template %s" % TEMPLATE)
        self.tmp = tempfile.mkdtemp(prefix="shipd-room-wake-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = os.path.join(self.tmp, "checkout")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        stub = os.path.join(self.work, ROOM_PY)
        os.makedirs(os.path.dirname(stub))
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write(STUB)
        self.output = os.path.join(self.tmp, "github-output")
        self.jobs = split_jobs(read_template())

    def can(self, verb, stdout, code=None):
        """Plant the stub's canned stdout (and exit code) for ``verb``."""
        with open(os.path.join(self.home, "room-%s.out" % verb), "w",
                  encoding="utf-8") as fh:
            fh.write(stdout)
        if code is not None:
            with open(os.path.join(self.home, "room-%s.code" % verb), "w",
                      encoding="utf-8") as fh:
                fh.write(str(code))

    def calls(self):
        """The stub's recorded calls, in order: ``[{"argv", "env"}]``."""
        log = os.path.join(self.home, "room-calls.ndjson")
        if not os.path.exists(log):
            return []
        with open(log, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def verbs(self):
        return [call["argv"][0] for call in self.calls()]

    def script(self, job, step):
        """The named step's script, its interpreter literal rewritten."""
        body = step_run(self.jobs.get(job, ""), step)
        self.assertTrue(body, "no run block for step %r in job %r"
                        % (step, job))
        self.assertIn(PY_PATH, body,
                      "the %s step no longer names %s, so the interpreter "
                      "rewrite below would not bind" % (job, PY_PATH))
        return body.replace(PY_PATH, sys.executable)

    def run_script(self, job, step, env, expect_failure=False):
        """Run ``step`` of ``job`` under bash with ``env`` on top of a
        minimal environment; ``(result, outputs)``."""
        if os.path.exists(self.output):
            os.remove(self.output)
        open(self.output, "w").close()
        path = os.path.join(self.tmp, "%s.sh" % job)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.script(job, step))
        full = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": self.home,
            "GITHUB_OUTPUT": self.output,
            "RUNNER_TEMP": self.tmp,
        }
        full.update(env)
        result = subprocess.run(["bash", path], cwd=self.work, env=full,
                                capture_output=True, text=True, timeout=60)
        if expect_failure:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
        with open(self.output, encoding="utf-8") as fh:
            outputs = parse_outputs(fh.read())
        return result, outputs


class TemplateTextTest(unittest.TestCase):
    """The template's text: marker, triggers, job split, pins."""

    def setUp(self):
        self.assertTrue(os.path.isfile(TEMPLATE),
                        "missing template %s" % TEMPLATE)
        self.text = read_template()
        self.jobs = split_jobs(self.text)

    def test_first_line_is_the_ownership_marker(self):
        self.assertEqual(self.text.splitlines()[0],
                         "# shipd-copilot v{version}")

    def test_both_triggers_fire_on_created_only(self):
        on = self.text.split("\non:\n", 1)[1].split("\n\n", 1)[0]
        for trigger in ("issue_comment", "pull_request_review_comment"):
            found = re.search(r"^  %s:\n    types: \[created\]$" % trigger,
                              on, re.M)
            self.assertIsNotNone(found, trigger)

    def test_composed_of_exactly_three_jobs(self):
        self.assertEqual(tuple(self.jobs), JOBS)

    def test_top_level_permissions_are_read_only(self):
        self.assertRegex(self.text,
                         r"(?m)^permissions:\n  contents: read\n")

    def test_guard_and_reply_may_write_issues_and_pull_requests(self):
        for job in ("guard", "reply"):
            self.assertIn("issues: write", self.jobs[job], job)
            self.assertIn("pull-requests: write", self.jobs[job], job)
        self.assertNotRegex(self.jobs["run"], r"(?m)^\s+[\w-]+: write\s*$")

    def test_concurrency_is_one_group_per_comment_without_cancel(self):
        self.assertIn("group: shipd-room-wake-${{ github.event.comment.id }}",
                      self.text)
        self.assertIn("cancel-in-progress: false", self.text)

    def test_guard_runs_only_for_a_configured_agent_and_a_room_comment(self):
        guard_if = self.jobs["guard"].split("runs-on:", 1)[0]
        self.assertIn("vars.SHIPD_ROOM_AGENT", guard_if)
        self.assertIn("<!-- shipd-room ", guard_if)
        self.assertIn("github.event.issue.pull_request", guard_if)
        self.assertIn("pull_request_review_comment", guard_if)

    def test_guard_runs_only_for_an_owner_member_or_collaborator(self):
        guard_if = self.jobs["guard"].split("runs-on:", 1)[0]
        self.assertIn("github.event.comment.author_association", guard_if)
        for role in ("OWNER", "MEMBER", "COLLABORATOR"):
            self.assertIn('"%s"' % role, guard_if)

    def test_the_pr_number_covers_both_triggers(self):
        self.assertIn("github.event.issue.number || "
                      "github.event.pull_request.number", self.jobs["guard"])

    def test_the_guard_learns_only_whether_the_secret_is_set(self):
        self.assertIn("COPILOT_CONFIGURED: "
                      "${{ secrets.COPILOT_GITHUB_TOKEN != '' }}",
                      self.jobs["guard"])

    # -- Scenario: Credentials never share a job ----------------------------

    def test_the_secret_is_bound_only_in_run(self):
        self.assertRegex(self.jobs["run"], SECRET_BINDING)
        for job in ("guard", "reply"):
            self.assertNotRegex(self.jobs[job], SECRET_BINDING)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", self.jobs["reply"])

    def test_the_workflow_token_is_bound_only_in_guard_and_reply(self):
        for job in ("guard", "reply"):
            self.assertRegex(self.jobs[job], WORKFLOW_TOKEN, job)
        self.assertNotIn("github.token", self.jobs["run"])
        self.assertNotIn("GH_TOKEN", self.jobs["run"])

    def test_run_checks_out_the_pr_head_without_credentials(self):
        run = self.jobs["run"]
        self.assertIn("refs/pull/${{ needs.guard.outputs.pr }}/head", run)
        self.assertIn("persist-credentials: false", run)

    def test_guard_and_reply_check_out_the_default_branch(self):
        for job in ("guard", "reply"):
            self.assertIn("ref: ${{ github.event.repository.default_branch }}",
                          self.jobs[job], job)

    # -- the run job ---------------------------------------------------------

    def test_run_depends_on_an_actionable_guard(self):
        run = self.jobs["run"]
        self.assertIn("needs: guard", run)
        self.assertIn("needs.guard.outputs.actionable == 'true'", run)

    def test_run_installs_the_pinned_cli(self):
        self.assertIn(CLI_PIN, step_run(self.jobs["run"], RUN_STEP))

    def test_run_invokes_the_cli_headless_under_a_timeout(self):
        script = step_run(self.jobs["run"], RUN_STEP)
        self.assertIn('timeout "${SHIPD_ROOM_CLI_TIMEOUT:-600}" copilot -p',
                      script)
        self.assertIn("--allow-all-tools", script)

    def test_run_asks_for_a_silent_markdown_reply(self):
        script = step_run(self.jobs["run"], RUN_STEP)
        self.assertIn('copilot -p "$prompt" -s --allow-all-tools', script)
        self.assertIn("GitHub-flavoured markdown", script)
        self.assertIn("fenced", script)

    def test_run_truncates_the_reply_to_60000_characters(self):
        self.assertIn("60000", step_run(self.jobs["run"], RUN_STEP))

    def test_the_prompt_explains_the_reply_marker(self):
        self.assertIn(REPLY_MARKER, step_run(self.jobs["run"], RUN_STEP))

    # -- the reply job -------------------------------------------------------

    def test_reply_always_runs_after_an_actionable_guard(self):
        reply = self.jobs["reply"]
        self.assertIn("always()", reply)
        self.assertIn("needs.guard.outputs.actionable == 'true'", reply)

    def test_reply_reads_the_reply_only_through_env(self):
        reply = self.jobs["reply"]
        self.assertIn("REPLY: ${{ needs.run.outputs.reply }}", reply)
        self.assertNotIn("${{", step_run(reply, REPLY_STEP))

    def test_scripts_interpolate_no_expressions(self):
        for job, step in (("guard", GUARD_STEP), ("run", RUN_STEP),
                          ("reply", REPLY_STEP)):
            self.assertNotIn("${{", step_run(self.jobs[job], step), job)

    def test_every_room_call_runs_in_an_isolated_environment(self):
        for job, step in (("guard", GUARD_STEP), ("reply", REPLY_STEP)):
            script = step_run(self.jobs[job], step)
            self.assertIn(ROOM_PY.replace(os.sep, "/"), script, job)
            calls = [line for line in script.splitlines()
                     if '"$room_py"' in line]
            self.assertTrue(calls, job)
            for line in calls:
                self.assertIn(ENV_PREFIX, line, job)
                self.assertIn("%s -B" % PY_PATH, line, job)

    def test_multi_line_outputs_use_a_random_delimiter(self):
        for job, step in (("guard", GUARD_STEP), ("run", RUN_STEP)):
            script = step_run(self.jobs[job], step)
            self.assertIn("token_hex", script, job)


GUARD_ENV = {
    "GH_TOKEN": "stub-token",
    "GH_REPO": "acme/widget",
    "SHIPD_ROOM_AGENT": "ci-bot",
    "COPILOT_CONFIGURED": "true",
    "EVENT_NAME": "issue_comment",
    "COMMENT_ID": "500",
    "PR_NUMBER": "7",
    "SHIPD_TEST_SENTINEL": "must-not-leak",
}


def watch_line(**fields):
    line = {"comment": 500, "to": "ci-bot", "task": 42, "id": 42,
            "last_agent": "alice", "text": "please look\nat this",
            "state": "input-required"}
    line.update(fields)
    for key in [k for k, v in line.items() if v is None]:
        del line[key]
    return json.dumps(line, sort_keys=True) + "\n"


class GuardScriptTest(WakeScriptCase):
    """The guard step, run against the stub ``room.py``."""

    def guard(self, **env):
        merged = dict(GUARD_ENV)
        merged.update(env)
        return self.run_script("guard", GUARD_STEP, merged)

    # -- Scenario: Addressed task is picked up ------------------------------

    def test_an_addressed_task_is_picked_up(self):
        self.can("watch", watch_line())
        self.can("list", json.dumps({"cards": [], "tasks": []}) + "\n")
        _result, outputs = self.guard()
        self.assertEqual(outputs.get("actionable"), "true")
        self.assertEqual(outputs.get("pr"), "7")
        self.assertEqual(outputs.get("task"), "42")
        self.assertEqual(outputs.get("asker"), "alice")
        self.assertEqual(outputs.get("text"), "please look\nat this")
        message = [c["argv"] for c in self.calls()
                   if c["argv"][0] == "message"]
        self.assertEqual(message, [["message", "7", "--task", "42",
                                    "--state", "working", "--",
                                    "picked up by the CI wake"]])

    def test_watch_runs_once_from_the_issue_cursor(self):
        self.can("watch", watch_line())
        self.guard()
        watch = self.calls()[0]["argv"]
        self.assertEqual(watch, ["watch", "7", "--once", "--since", "499:0"])

    def test_a_review_comment_uses_the_review_cursor(self):
        self.can("watch", watch_line())
        self.guard(EVENT_NAME="pull_request_review_comment")
        self.assertEqual(self.calls()[0]["argv"],
                         ["watch", "7", "--once", "--since", "0:499"])

    def test_join_runs_when_the_agent_has_no_card(self):
        self.can("watch", watch_line())
        self.can("list", json.dumps({"cards": [{"name": "alice"}]}) + "\n")
        self.guard()
        self.assertIn(["join", "7", "--harness", "copilot-cli", "--role", "ci"],
                      [c["argv"] for c in self.calls()])
        self.assertEqual(self.verbs(), ["watch", "list", "join", "message"])

    def test_join_is_skipped_when_the_card_exists(self):
        self.can("watch", watch_line())
        self.can("list", json.dumps({"cards": [{"name": "ci-bot"}]}) + "\n")
        self.guard()
        self.assertEqual(self.verbs(), ["watch", "list", "message"])

    def test_the_task_id_falls_back_to_id(self):
        self.can("watch", watch_line(task=None, id=43))
        _result, outputs = self.guard()
        self.assertEqual(outputs.get("task"), "43")

    def test_the_matching_line_is_chosen_among_several(self):
        self.can("watch", watch_line(comment=400, task=40, id=40)
                 + watch_line())
        _result, outputs = self.guard()
        self.assertEqual(outputs.get("task"), "42")

    def test_room_calls_see_only_the_handed_environment(self):
        self.can("watch", watch_line())
        self.guard()
        for call in self.calls():
            env = call["env"]
            self.assertEqual(env.get("PATH"), "/usr/bin:/bin")
            self.assertEqual(env.get("GH_TOKEN"), "stub-token")
            self.assertEqual(env.get("GH_REPO"), "acme/widget")
            self.assertEqual(env.get("SHIPD_ROOM_AGENT"), "ci-bot")
            self.assertNotIn("SHIPD_TEST_SENTINEL", env)
            self.assertNotIn("GITHUB_OUTPUT", env)

    # -- Scenario: Other or empty lines are ignored -------------------------

    def assertIgnored(self, outputs):
        self.assertEqual(outputs.get("actionable"), "false")
        self.assertNotIn("message", self.verbs())
        self.assertNotIn("join", self.verbs())

    def test_empty_watch_output_is_not_actionable(self):
        _result, outputs = self.guard()
        self.assertIgnored(outputs)

    def test_a_line_for_another_comment_is_ignored(self):
        self.can("watch", watch_line(comment=499))
        _result, outputs = self.guard()
        self.assertIgnored(outputs)

    def test_a_line_addressed_to_another_agent_is_ignored(self):
        self.can("watch", watch_line(to="other-bot"))
        _result, outputs = self.guard()
        self.assertIgnored(outputs)

    def test_an_unaddressed_line_is_ignored(self):
        self.can("watch", watch_line(to=None))
        _result, outputs = self.guard()
        self.assertIgnored(outputs)

    def test_an_unconfigured_secret_is_not_actionable(self):
        result, outputs = self.guard(COPILOT_CONFIGURED="false")
        self.assertEqual(outputs.get("actionable"), "false")
        self.assertEqual(self.calls(), [])
        self.assertIn("COPILOT_GITHUB_TOKEN", result.stdout)


REPLY_ENV = {
    "GH_TOKEN": "stub-token",
    "GH_REPO": "acme/widget",
    "SHIPD_ROOM_AGENT": "ci-bot",
    "PR_NUMBER": "7",
    "TASK_ID": "42",
    "ASKER": "alice",
    "RUN_RESULT": "success",
}


class ReplyScriptTest(WakeScriptCase):
    """The reply step, run against the stub ``room.py``."""

    def reply(self, text, expect_failure=False, **env):
        merged = dict(REPLY_ENV)
        merged["REPLY"] = text
        merged.update(env)
        return self.run_script("reply", REPLY_STEP, merged,
                               expect_failure=expect_failure)

    def message(self):
        calls = [c["argv"] for c in self.calls() if c["argv"][0] == "message"]
        self.assertEqual(len(calls), 1, self.calls())
        return calls[0]

    # -- Scenario: Reply marker selects input-required ----------------------

    def test_a_reply_ending_in_the_marker_asks_back(self):
        self.reply("Which branch should I rebase onto?\n%s\n" % REPLY_MARKER)
        argv = self.message()
        self.assertEqual(argv[:9], ["message", "7", "--task", "42", "--to",
                                    "alice", "--state", "input-required",
                                    "--"])
        self.assertEqual(argv[9], "Which branch should I rebase onto?")
        self.assertNotIn(REPLY_MARKER, argv[9])

    def test_trailing_blank_lines_after_the_marker_still_count(self):
        self.reply("Which one?\n%s\n\n  \n" % REPLY_MARKER)
        argv = self.message()
        self.assertEqual(argv[7], "input-required")
        self.assertNotIn(REPLY_MARKER, argv[9])

    def test_a_marker_before_the_last_line_completes(self):
        text = "Quoting %s\n%s\nDone.\n" % (REPLY_MARKER, REPLY_MARKER)
        self.reply(text)
        argv = self.message()
        self.assertEqual(argv[7], "completed")
        self.assertIn(REPLY_MARKER, argv[9])

    # -- Scenario: Plain reply completes, failed run closes -----------------

    def test_a_plain_reply_completes(self):
        self.reply("Rebased and pushed.\nAll green.\n")
        self.assertEqual(self.message(),
                         ["message", "7", "--task", "42", "--to", "alice",
                          "--state", "completed", "--",
                          "Rebased and pushed.\nAll green."])

    def test_a_failed_run_closes_the_task(self):
        self.reply("", RUN_RESULT="failure")
        self.assertEqual([c["argv"] for c in self.calls()],
                         [["close", "7", "--task", "42", "--state", "failed",
                           "--reason", "wake-runner-failed"]])

    def test_a_cancelled_run_closes_the_task(self):
        self.reply("partial", RUN_RESULT="cancelled")
        self.assertEqual(self.verbs(), ["close"])

    def test_an_empty_reply_closes_the_task(self):
        self.reply("  \n\n")
        self.assertEqual([c["argv"] for c in self.calls()],
                         [["close", "7", "--task", "42", "--state", "failed",
                           "--reason", "wake-runner-failed"]])

    # -- Scenario: Room wake reply drops the CLI transcript -----------------

    BLOCK = ("\u25cf Read src/app.py\n"
             "  \u2502 src/app.py\n"
             "  \u2514 120 lines read\n")

    def test_transcript_blocks_are_stripped_from_the_posted_reply(self):
        self.reply("First paragraph.\n\n%s\nSecond paragraph.\n" % self.BLOCK)
        argv = self.message()
        self.assertEqual(argv[7], "completed")
        self.assertIn("First paragraph.", argv[9])
        self.assertIn("Second paragraph.", argv[9])
        for glyph in ("\u25cf", "\u2502", "\u2514"):
            self.assertNotIn(glyph, argv[9])

    def test_the_marker_still_asks_back_after_cleaning(self):
        self.reply("Which branch?\n%s%s\n" % (self.BLOCK, REPLY_MARKER))
        argv = self.message()
        self.assertEqual(argv[7], "input-required")
        self.assertNotIn(REPLY_MARKER, argv[9])
        self.assertNotIn("\u25cf", argv[9])

    def test_a_transcript_only_reply_fails_the_task(self):
        self.reply(self.BLOCK)
        self.assertEqual([c["argv"] for c in self.calls()],
                         [["close", "7", "--task", "42", "--state", "failed",
                           "--reason", "wake-runner-failed"]])

    def test_a_refused_message_fails_the_job(self):
        self.can("message", "", code=1)
        self.reply("Done.\n", expect_failure=True)

    def test_room_calls_see_only_the_handed_environment(self):
        self.reply("Done.\n", SHIPD_TEST_SENTINEL="must-not-leak")
        env = self.calls()[0]["env"]
        self.assertEqual(env.get("PATH"), "/usr/bin:/bin")
        self.assertNotIn("SHIPD_TEST_SENTINEL", env)
        self.assertNotIn("REPLY", env)


if __name__ == "__main__":
    unittest.main()
