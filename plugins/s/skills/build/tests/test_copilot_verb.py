#!/usr/bin/env python3
"""Tests for the Copilot code-review integration (copilot-review-skill, and
``shipd copilot`` under shipd-cli).

Two layers, both black-box:

* **The templates** shipped at ``plugins/s/integrations/copilot/`` are read off
  disk and asserted on their content — the marker lines carrying the literal
  ``{version}`` placeholder, the instructions the reviewing agent follows, the
  setup workflow's single job and tooling steps, and the gate workflow's
  triggers, guards, concurrency, and verdict mapping. The gate's own script is
  also *executed*: its step body is extracted, its ``${{ … }}`` expressions
  substituted, and the script run under bash against a stubbed ``gh`` serving
  scripted API responses, so both the poll for Copilot's review and the
  classification of it are proved on real bodies and real call sequences
  rather than asserted on the shape of a conditional.
* **The verb** is driven through ``plugins/s/bin/shipd`` by path (so its
  shebang and exec bit are exercised too) against throwaway temp roots, in the
  subprocess-against-temp-roots style of ``test_shipd_cli.py``. ``HOME`` is
  isolated so nothing reaches the real user's files, and no test ever writes
  into this checkout.

The workflow templates are parsed with a small indentation-aware reader rather
than a YAML library, and the gate's shell conditional with a line-based branch
splitter: the engine's suite is stdlib-only, per the constitution.
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
BIN = os.path.join(PLUGIN_ROOT, "bin", "shipd")
INTEGRATIONS = os.path.join(PLUGIN_ROOT, "integrations", "copilot")
SKILL_TEMPLATE = os.path.join(INTEGRATIONS, "SKILL.md")
WORKFLOW_TEMPLATE = os.path.join(INTEGRATIONS, "copilot-code-review.yml")
GATE_TEMPLATE = os.path.join(INTEGRATIONS, "copilot-review-gate.yml")
PLUGIN_SEMDIFF = os.path.join(PLUGIN_ROOT, "skills", "review", "scripts",
                              "semdiff.py")

MANIFEST = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")

# The ownership markers, with the literal placeholder the verb substitutes.
SKILL_MARKER = "<!-- shipd-copilot v{version} -->"
WORKFLOW_MARKER = "# shipd-copilot v{version}"

# The machine-readable verdict markers the gate parses out of a review body.
FIX_MARKER = "<!-- shipd-verdict: fix-required -->"
SHIP_MARKER = "<!-- shipd-verdict: ship-it -->"

# The commit-status context the gate posts — the same one review_gate.py uses,
# so either poster satisfies a required check of that name.
STATUS_CONTEXT = "semantic-review"

# The machine-readable findings the reviewer writes beside its report body, and
# which the posting step reads to anchor inline comments. One literal, asserted
# on both sides of that handoff: the skill template names where it is written,
# the gate template names where it is read.
FINDINGS_FILE = "shipd-copilot-review-findings.json"

# The report shape the skill mandates: the verdict header first, then the
# severity summary table, then the per-finding detail.
VERDICT_HEADERS = ("## Findings: ✅ Ship it",
                   "## Findings: ❌ Fix required")
SEVERITY_TABLE = "| # | rating | details |"

# Where the reviewing agent's instructions live in a repository that installed
# the integration, forward-slashed the way the Linux runner sees them (whatever
# this suite runs on). The gate materializes its own copy from the *base* ref
# of this path rather than following the one on the ref under review.
GATE_SKILL_PATH = ".github/skills/code-review/SKILL.md"

# Where the posting step invokes `gh` from. It is a hardcoded literal in the
# template rather than an environment override, because a variable an earlier
# step could write to $GITHUB_ENV would redirect the credentialed binary just
# as a $GITHUB_PATH shim would — so the runnable tests rewrite this path in the
# extracted script, the way they rewrite the runner's own expressions.
GH_PATH = "/usr/bin/gh"

# Where the posting step's payload builder runs from. Absolute for the same
# reason `gh` is: an earlier step can prepend a directory to $GITHUB_PATH, so a
# PATH-resolved interpreter in the credentialed step would run the reviewer's
# own program. The runnable tests rewrite this literal too.
PY_PATH = "/usr/bin/python3"

# The pinned global install of the reviewer CLI. The version is deliberate — a
# floating tag would let the CLI vendor change gate behaviour on their own
# schedule — so what is asserted is the pin's shape, not one release.
CLI_PIN = re.compile(r"npm install -g @github/copilot@(\d+\.\d+\.\d+)\b")
CLI_UNPINNED = re.compile(r"npm install -g @github/copilot(?!@)")

# The four files the verb manages, relative to the target root.
SKILL_PATH = os.path.join(".github", "skills", "code-review", "SKILL.md")
SEMDIFF_PATH = os.path.join(".github", "skills", "code-review", "scripts",
                            "semdiff.py")
WORKFLOW_PATH = os.path.join(".github", "workflows", "copilot-code-review.yml")
GATE_PATH = os.path.join(".github", "workflows", "copilot-review-gate.yml")
MANAGED = (SKILL_PATH, SEMDIFF_PATH, WORKFLOW_PATH, GATE_PATH)

# The managed files carrying a substituted ownership marker of their own.
MARKED = (SKILL_PATH, WORKFLOW_PATH, GATE_PATH)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def frontmatter(text):
    """The ``key: value`` pairs of a leading ``---`` YAML frontmatter block,
    values of continuation lines folded onto their key. Only top-level keys are
    collected, which is all the two required fields need."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line[:1] not in (" ", "\t") and ":" in line:
            key, _sep, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip()
        elif key is not None:
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def markdown_section(text, heading):
    """The body of the markdown section ``heading`` (given with its ``#``
    prefix) introduces, up to the next heading at the same or a shallower
    level — so an assertion lands on the section that must carry it rather
    than anywhere in the file."""
    level = len(heading) - len(heading.lstrip("#"))
    out = []
    inside = False
    for line in text.splitlines():
        if line.strip() == heading:
            inside = True
            continue
        if not inside:
            continue
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= level:
            break
        out.append(line)
    return "\n".join(out)


def yaml_block(text, key):
    """The lines of the top-level block ``key:`` introduces, with their
    original indentation — a deliberately small stdlib reader, enough for the
    shape assertions below."""
    lines = text.splitlines()
    out = []
    inside = False
    for line in lines:
        if not inside:
            if line.strip() == "%s:" % key and not line.startswith(" "):
                inside = True
            continue
        if line.strip() and not line.startswith(" "):
            break
        out.append(line)
    return out


def block_keys(block):
    """The keys one nesting level into ``block`` — the job names under
    ``jobs:``, given a conventional two-space-per-level file."""
    indents = [len(line) - len(line.lstrip())
               for line in block if line.strip() and line.rstrip().endswith(":")]
    if not indents:
        return []
    level = min(indents)
    return [line.strip()[:-1] for line in block
            if line.strip().endswith(":")
            and len(line) - len(line.lstrip()) == level]


def job_blocks(text):
    """``{job name: the job's body as text}`` for the top-level ``jobs:``
    mapping — enough to assert on one job's guard and steps without pulling in
    a YAML library."""
    block = yaml_block(text, "jobs")
    names = block_keys(block)
    if not names:
        return {}
    level = min(len(line) - len(line.lstrip()) for line in block
                if line.strip() and line.rstrip().endswith(":"))
    jobs = {}
    current = None
    for line in block:
        if (line.strip().endswith(":")
                and len(line) - len(line.lstrip()) == level
                and line.strip()[:-1] in names):
            current = line.strip()[:-1]
            jobs[current] = []
            continue
        if current is not None:
            jobs[current].append(line)
    return {name: "\n".join(lines) for name, lines in jobs.items()}


def verdict_branches(text):
    """``{branch key: the branch's body}`` for the gate's shell conditional,
    keyed by the verdict each arm tests — ``"fix-required"``, ``"ship-it"``, or
    ``"none"`` for the marker-less fallback. A conditional arm testing anything
    else contributes nothing."""
    branches = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        head = stripped.split()[0] if stripped else ""
        if head in ("if", "elif", "else"):
            if FIX_MARKER in stripped:
                current = "fix-required"
            elif SHIP_MARKER in stripped:
                current = "ship-it"
            elif head == "else":
                current = "none"
            else:
                current = None
            if current is not None:
                branches.setdefault(current, [])
            continue
        if head == "fi":
            current = None
            continue
        if current is not None:
            branches[current].append(stripped)
    return {key: "\n".join(lines) for key, lines in branches.items()}


def gate_job(text):
    """The body of the gate workflow's single job. Both triggers are served by
    one job — which event a run is handling is a branch inside its script, not
    a job of its own — so there is exactly one to return."""
    jobs = job_blocks(text)
    if len(jobs) != 1:
        raise AssertionError("expected exactly one job, found %d: %s"
                             % (len(jobs), ", ".join(sorted(jobs))))
    return next(iter(jobs.values()))


def job_steps(job_body):
    """The job's steps, each as its own chunk of text in declaration order —
    everything from one ``- name:`` at the steps' indent up to the next."""
    lines = job_body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "steps:":
            start = i + 1
            break
    if start is None:
        return []
    body = lines[start:]
    indents = [len(line) - len(line.lstrip()) for line in body
               if line.strip().startswith("- ")]
    if not indents:
        return []
    level = min(indents)
    steps = []
    current = None
    for line in body:
        if (line.strip().startswith("- ")
                and len(line) - len(line.lstrip()) == level):
            current = [line]
            steps.append(current)
        elif current is not None:
            current.append(line)
    return ["\n".join(chunk) for chunk in steps]


def step_body(step):
    """A step's own text. A chunk from :func:`job_steps` runs to the next
    ``- name:``, so it also carries the *following* step's comment preamble;
    those comments sit at the ``- `` indent, while every comment a step
    carries of its own is nested deeper inside ``env:`` or ``run:``. Trimming
    them is what lets an assertion say "this step mentions no credential"
    without the next step's commentary answering for it."""
    lines = step.splitlines()
    if not lines:
        return step
    level = len(lines[0]) - len(lines[0].lstrip())
    while lines:
        last = lines[-1]
        if not last.strip():
            lines.pop()
            continue
        indent = len(last) - len(last.lstrip())
        if last.lstrip().startswith("#") and indent <= level:
            lines.pop()
            continue
        break
    return "\n".join(lines)


def run_block(job_body):
    """The dedented body of the first ``run: |`` block in ``job_body``."""
    lines = job_body.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("run:") and stripped.endswith("|")):
            continue
        head = len(line) - len(line.lstrip())
        body = []
        indent = None
        for follow in lines[i + 1:]:
            if not follow.strip():
                body.append("")
                continue
            pad = len(follow) - len(follow.lstrip())
            if pad <= head:
                break
            if indent is None:
                indent = pad
            body.append(follow[indent:])
        while body and not body[-1].strip():
            body.pop()
        return "\n".join(body) + "\n" if body else ""
    return ""


# A GitHub Actions template expression, which the runner substitutes before
# the shell ever sees it — bash would choke on the braces.
ACTIONS_EXPRESSION = re.compile(r"\$\{\{[^}]*\}\}")


HEREDOC = re.compile(r"<<'([A-Za-z_][A-Za-z0-9_]*)'")


def shell_lines(script):
    """The lines of ``script`` the shell runs as commands — every line outside
    a quoted heredoc body. A heredoc's contents are data handed to a program,
    so a shell-level rule (no pipes, no text tools) has nothing to say about
    them."""
    lines, terminator = [], None
    for line in script.splitlines():
        if terminator is not None:
            if line.strip() == terminator:
                terminator = None
            continue
        lines.append(line)
        opened = HEREDOC.search(line)
        if opened:
            terminator = opened.group(1)
    return lines


def gate_script(text, substitute="stub"):
    """The gate's decision logic, runnable under bash: the ``run`` bodies of the
    steps that touch the ``semantic-review`` status, concatenated in the order
    the job runs them, with the Actions expressions the runner would interpolate
    replaced by ``substitute``.

    That selection is what the gate *decides*; the steps it leaves out are pure
    provisioning — an ``actions/checkout``, and an apt/curl install of the
    engine's optional tooling — with no branch in them, and what they provide is
    stubbed on ``PATH`` for a test run instead. Everything the logic needs of
    the event reaches it through the steps' ``env:``, so a run is driven
    entirely by the environment the test sets."""
    bodies = [run_block(step) for step in job_steps(gate_job(text))]
    return ACTIONS_EXPRESSION.sub(
        substitute, "".join(body for body in bodies if STATUS_CONTEXT in body))


class SkillTemplateTest(unittest.TestCase):
    """``integrations/copilot/SKILL.md`` (copilot-review-skill
    skill-template)."""

    def setUp(self):
        self.assertTrue(os.path.isfile(SKILL_TEMPLATE),
                        "missing template %s" % SKILL_TEMPLATE)
        self.text = read(SKILL_TEMPLATE)

    def test_frontmatter_carries_name_and_description(self):
        fields = frontmatter(self.text)
        self.assertIn("name", fields)
        self.assertIn("description", fields)
        self.assertTrue(fields["name"].strip())
        self.assertTrue(fields["description"].strip())

    def test_ownership_marker_line_is_present_with_the_placeholder(self):
        # The literal placeholder, not a substituted version: the shipped
        # template is what ``copilot add`` renders from.
        self.assertIn(SKILL_MARKER,
                      [line.strip() for line in self.text.splitlines()])

    def test_directs_the_agent_to_the_bundled_engine(self):
        self.assertIn(".github/skills/code-review/scripts/semdiff.py",
                      self.text)
        for subcommand in ("files", "diff", "context"):
            self.assertIn(subcommand, self.text,
                          "template omits semdiff subcommand %r" % subcommand)

    def test_prefers_structural_json_over_raw_file_dumps(self):
        lowered = self.text.lower()
        self.assertIn("json", lowered)
        self.assertIn("raw file", lowered)

    def test_severity_rubric_and_blocking_rule(self):
        for level in ("high", "medium", "low"):
            self.assertIn(level, self.text,
                          "template omits severity %r" % level)
        lowered = self.text.lower()
        self.assertIn("ship it", lowered)
        self.assertIn("fix required", lowered)
        self.assertIn("block", lowered)

    def test_read_only_and_text_engine_degradation_are_stated(self):
        lowered = self.text.lower()
        self.assertIn("read-only", lowered)
        self.assertIn("difft", lowered)
        self.assertIn("text engine", lowered)

    def test_documents_the_absent_model_pin_and_advisory_posture(self):
        lowered = self.text.lower()
        self.assertIn("model", lowered)
        self.assertIn("advisory", lowered)

    def test_report_instructions_mandate_the_verdict_marker(self):
        report = markdown_section(self.text, "### 5. Report")
        self.assertTrue(report.strip(), "no report section in the template")
        self.assertIn(SHIP_MARKER, report)
        self.assertIn(FIX_MARKER, report)
        lowered = report.lower()
        self.assertIn("verdict line", lowered)
        self.assertIn("own line", lowered)

    def test_the_marker_instruction_states_last_line_equality(self):
        # The gate reads the marker off the body's last non-empty line and
        # compares it for equality. An instruction promising an "exact
        # substring match" describes a matcher that does not exist and that
        # the gate deliberately does not use — a marker quoted mid-text is
        # prose, and matching it anywhere would fail a passing pull request.
        report = markdown_section(self.text, "### 5. Report")
        self.assertTrue(report.strip(), "no report section in the template")
        lowered = report.lower()
        self.assertIn("last non-empty line", lowered)
        self.assertIn("exact equality", lowered)
        self.assertIn("never by a substring match", lowered,
                      "the instruction does not rule the substring match out")
        self.assertNotIn("exact substring match", self.text.lower(),
                         "the template still promises a substring match")

    def test_the_report_opens_with_a_verdict_header_and_severity_table(self):
        # A reader who stops after the first screen must already have the
        # verdict and every finding's rating — the shape `/s:review` renders
        # and the gate has never matched.
        report = markdown_section(self.text, "### 5. Report")
        self.assertTrue(report.strip(), "no report section in the template")
        for header in VERDICT_HEADERS:
            self.assertIn(header, report,
                          "the report shape omits the verdict header %r"
                          % header)
        self.assertIn(SEVERITY_TABLE, report,
                      "the report shape omits the severity summary table")
        for dot in ("🔴", "🟠", "🟡"):
            self.assertIn(dot, report, "the table omits the %s rating" % dot)
        # Ordering, not just presence: header, then table, then the detail.
        self.assertLess(report.index(VERDICT_HEADERS[0]),
                        report.index(SEVERITY_TABLE),
                        "the severity table precedes the verdict header")
        self.assertLess(report.index(SEVERITY_TABLE),
                        report.index("**The per-finding detail**"),
                        "per-finding detail precedes the severity table")
        self.assertIn("brief", report.lower(),
                      "the template does not ask for brief findings")

    def test_the_findings_file_is_specified_with_its_replacement_rule(self):
        report = markdown_section(self.text, "### 5. Report")
        self.assertTrue(report.strip(), "no report section in the template")
        self.assertIn(FINDINGS_FILE, report,
                      "the template names no machine-readable findings file")
        for key in ("severity", "path", "start_line", "end_line", "detail",
                    "replacement"):
            self.assertIn('"%s"' % key, report,
                          "the findings entry omits %r" % key)
        lowered = report.lower()
        # `replacement` is the confidence declaration, and it is whole lines or
        # nothing: a one-click apply commits the reviewer's text unread.
        self.assertIn("optional", lowered)
        self.assertIn("confident", lowered)
        self.assertIn("contiguous whole lines", lowered)

    def test_the_skill_is_the_contract_for_both_reviewer_surfaces(self):
        # One rubric, two consumers: GitHub's own code-review runs, and the
        # gate workflow's headless Copilot CLI reviewer, whose prompt defers to
        # this file rather than restating it.
        scope = markdown_section(self.text, "## Scope of this review")
        self.assertTrue(scope.strip(), "no scope section in the template")
        lowered = scope.lower()
        self.assertIn("contract", lowered)
        self.assertIn("both", lowered)
        self.assertIn("code review", lowered)
        self.assertIn("copilot cli", lowered)
        self.assertIn("headless", lowered)

    def test_scope_describes_the_gate_workflows_fail_open_bridging(self):
        scope = markdown_section(self.text, "## Scope of this review")
        self.assertTrue(scope.strip(), "no scope section in the template")
        self.assertIn("copilot-review-gate.yml", scope)
        self.assertIn(STATUS_CONTEXT, scope)
        lowered = scope.lower()
        self.assertIn("fail-open", lowered)
        # Advisory is what remains where no gate workflow is installed.
        self.assertIn("advisory", lowered)
        self.assertIn("no gate workflow", lowered)

    def test_the_gate_bullet_names_the_strictness_knob(self):
        # The consequence of omitting the marker is not one thing: in a
        # repository that set the knob, a marker-less review leaves the
        # required check `pending` rather than greening it. A reviewer told
        # only the fail-open half is told the wrong stakes.
        scope = markdown_section(self.text, "## Scope of this review")
        bullets = [bullet for bullet in scope.split("\n- ")
                   if "copilot-review-gate.yml" in bullet]
        self.assertEqual(len(bullets), 1,
                         "expected exactly one merge-gate bullet, found %d"
                         % len(bullets))
        lowered = bullets[0].lower()
        self.assertIn("shipd_gate_fail_open", lowered,
                      "the merge-gate bullet does not name the strictness "
                      "knob")
        self.assertIn("fail-open", lowered,
                      "the knob is named without its default")
        self.assertIn("`false`", lowered,
                      "the knob is named without the value that turns it on")
        self.assertIn("pending", lowered,
                      "the knob is named without what `false` does to the "
                      "status")


class WorkflowTemplateTest(unittest.TestCase):
    """``integrations/copilot/copilot-code-review.yml``
    (copilot-review-skill setup-workflow-template)."""

    def setUp(self):
        self.assertTrue(os.path.isfile(WORKFLOW_TEMPLATE),
                        "missing template %s" % WORKFLOW_TEMPLATE)
        self.text = read(WORKFLOW_TEMPLATE)
        jobs = job_blocks(self.text)
        self.assertEqual(sorted(jobs), ["copilot-setup-steps"])
        self.steps = job_steps(jobs["copilot-setup-steps"])

    def step(self, needle):
        """The one step whose text carries ``needle``."""
        found = [step for step in self.steps if needle in step]
        self.assertEqual(len(found), 1,
                         "expected exactly one step carrying %r, found %d"
                         % (needle, len(found)))
        return found[0]

    def test_ownership_marker_line_is_present_with_the_placeholder(self):
        self.assertIn(WORKFLOW_MARKER,
                      [line.strip() for line in self.text.splitlines()])

    def test_defines_exactly_one_job_named_copilot_setup_steps(self):
        jobs = block_keys(yaml_block(self.text, "jobs"))
        self.assertEqual(jobs, ["copilot-setup-steps"])

    def test_the_job_runs_on_ubuntu_latest(self):
        self.assertIn("runs-on: ubuntu-latest",
                      [line.strip() for line in self.text.splitlines()])

    def test_a_step_installs_the_difft_release_binary_onto_path(self):
        self.assertIn(
            "https://github.com/Wilfred/difftastic/releases/latest/download/"
            "difft-x86_64-unknown-linux-gnu.tar.gz", self.text)
        self.assertIn("$GITHUB_PATH", self.text)

    def test_a_step_installs_ripgrep(self):
        self.assertIn("ripgrep", self.text)
        self.assertIn("apt-get install", self.text)

    def test_no_secrets_are_referenced(self):
        self.assertNotIn("secrets.", self.text)
        self.assertNotIn("${{ secrets", self.text)

    def test_the_checkout_is_fail_soft_and_identified(self):
        # GitHub's Copilot review runner cannot check out a private
        # repository, and a setup job that fails there earns every reviewed
        # pull request a visible `ccr-setup-step-failure` notice. The
        # checkout keeps its place — the public-repo case needs it for skill
        # loading — but a failure of it no longer fails the job, and the step
        # carries an `id` so the installs can read its outcome.
        checkout = self.step("uses: actions/checkout")
        self.assertIn("continue-on-error: true", checkout)
        ids = [line.strip() for line in checkout.splitlines()
               if line.strip().startswith("id:")]
        self.assertEqual(len(ids), 1,
                         "the checkout step carries no id for the installs to "
                         "condition on")
        self.checkout_id = ids[0].split(":", 1)[1].strip()

    def test_the_installs_run_only_on_a_successful_checkout(self):
        self.test_the_checkout_is_fail_soft_and_identified()
        guard = "steps.%s.outcome == 'success'" % self.checkout_id
        for needle in ("difft-x86_64-unknown-linux-gnu.tar.gz",
                       "apt-get install"):
            step = self.step(needle)
            self.assertIn("if:", step,
                          "the %r step is not conditioned on the checkout"
                          % needle)
            self.assertIn(guard, step,
                          "the %r step does not require the checkout to have "
                          "succeeded" % needle)

    def test_a_binary_less_archive_fails_the_difftastic_step_loudly(self):
        # `find` printing nothing would otherwise reach `install` as an empty
        # source path — an obscure failure at best, and a silently skipped
        # install at worst.
        run = run_block(self.step("difft-x86_64-unknown-linux-gnu.tar.gz"))
        self.assertIn('-z "$binary"', run,
                      "the located binary path is never tested for emptiness")
        self.assertLess(run.index('-z "$binary"'), run.index("install -m"),
                        "the emptiness guard runs after the install it is "
                        "supposed to protect")
        guard = run[run.index('-z "$binary"'):run.index("install -m")]
        self.assertIn("difft", guard,
                      "the failure message does not name the missing binary")
        self.assertIn("exit 1", guard,
                      "a binary-less archive does not fail the step")


class GateWorkflowTemplateTest(unittest.TestCase):
    """``integrations/copilot/copilot-review-gate.yml`` (copilot-review-skill
    gate-workflow-template) — the workflow that bridges Copilot's review into
    the required ``semantic-review`` commit status."""

    def setUp(self):
        self.assertTrue(os.path.isfile(GATE_TEMPLATE),
                        "missing template %s" % GATE_TEMPLATE)
        self.text = read(GATE_TEMPLATE)
        self.job = gate_job(self.text)
        self.assertIn("steps:", self.job)
        # Everything the job declares before its steps — its trigger guard.
        self.guard = self.job[:self.job.index("steps:")]
        self.script = gate_script(self.text)
        self.steps = job_steps(self.job)

    def test_ownership_marker_line_is_present_with_the_placeholder(self):
        self.assertIn(WORKFLOW_MARKER,
                      [line.strip() for line in self.text.splitlines()])

    def test_triggers_on_pull_request_and_review_submission(self):
        block = yaml_block(self.text, "on")
        self.assertEqual(block_keys(block),
                         ["pull_request", "pull_request_review"])
        joined = "\n".join(block)
        opened = joined.index("pull_request:")
        submitted = joined.index("pull_request_review:")
        on_pull_request = joined[opened:submitted]
        on_review = joined[submitted:]
        for event_type in ("opened", "synchronize", "reopened"):
            self.assertIn(event_type, on_pull_request,
                          "pull_request omits type %r" % event_type)
        self.assertIn("submitted", on_review)
        self.assertNotIn("submitted", on_pull_request)

    def test_permissions_grant_statuses_and_pull_requests_write(self):
        block = [line.strip() for line in yaml_block(self.text, "permissions")]
        self.assertIn("statuses: write", block)
        self.assertIn("contents: read", block)
        # `write`, not the `read` the poll alone needed: the CLI reviewer posts
        # the review text it judged as a pull-request comment.
        self.assertIn("pull-requests: write", block)
        self.assertNotIn("pull-requests: read", block)

    def test_one_concurrency_group_per_pull_request_cancels_superseded_runs(
            self):
        # A push while a poll is running supersedes it: the new head's own run
        # owns the gate, and cancelling the old one is what stops two polls
        # racing to post on the same pull request.
        block = [line.strip() for line in yaml_block(self.text, "concurrency")]
        group = [line for line in block if line.startswith("group:")]
        self.assertEqual(len(group), 1,
                         "expected exactly one concurrency group, found %d"
                         % len(group))
        self.assertIn("github.event.pull_request.number", group[0],
                      "the concurrency group is not keyed on the pull request")
        self.assertIn("cancel-in-progress: true", block)

    def test_one_job_serves_both_triggers(self):
        # Both events land in the same job, so the poll and the review-event
        # classification share one script — and one classification block.
        jobs = job_blocks(self.text)
        self.assertEqual(len(jobs), 1,
                         "expected one job, found: %s" % ", ".join(sorted(jobs)))
        self.assertIn("github.event_name == 'pull_request'", self.guard)

    def test_the_review_event_path_guards_reviewer_and_head_commit(self):
        # A review event is worth a run only for Copilot's own review of the
        # commit that is currently the head: a stale review is ignored.
        self.assertIn("github.event.review.user.login == "
                      "'copilot-pull-request-reviewer[bot]'", self.guard)
        self.assertIn("github.event.review.commit_id == "
                      "github.event.pull_request.head.sha", self.guard)

    def test_every_status_is_posted_on_the_triggering_head_sha(self):
        self.assertIn("HEAD_SHA: ${{ github.event.pull_request.head.sha }}",
                      self.job)
        self.assertIn("REPO: ${{ github.repository }}", self.job)
        self.assertIn('repos/$REPO/statuses/$HEAD_SHA', self.script)
        self.assertIn("context=%s" % STATUS_CONTEXT, self.script)

    def test_the_poll_looks_for_copilots_review_of_the_triggering_head(self):
        self.assertIn("PR_NUMBER: ${{ github.event.pull_request.number }}",
                      self.job)
        self.assertIn("pulls/$PR_NUMBER/reviews", self.script)
        self.assertIn("--paginate", self.script,
                      "the reviews listing is not paginated")
        self.assertIn("copilot-pull-request-reviewer[bot]", self.script)
        self.assertIn("env.HEAD_SHA", self.script,
                      "the poll does not match the review's commit_id against "
                      "the triggering head")
        # Each cycle also re-reads the pull request's own head, so a poll for
        # a superseded commit can stop itself.
        self.assertIn('"repos/$REPO/pulls/$PR_NUMBER"', self.script)

    def test_the_production_poll_cadence_is_20_seconds_over_15_minutes(self):
        # The overrides exist only so the suite can drive the loop without
        # waiting on it; nothing in the runner sets them, so these defaults
        # are what every real run polls at.
        self.assertIn('poll_interval="${SHIPD_GATE_POLL_INTERVAL:-20}"',
                      self.script)
        self.assertIn('poll_timeout="${SHIPD_GATE_POLL_TIMEOUT:-900}"',
                      self.script)

    # -- the CLI reviewer path ---------------------------------------------

    def cli_step(self):
        """The step that runs the Copilot CLI — the one place the secret is
        allowed to reach."""
        found = [step for step in self.steps if "copilot -p" in step]
        self.assertEqual(len(found), 1,
                         "expected exactly one step invoking the Copilot CLI, "
                         "found %d" % len(found))
        return step_body(found[0])

    def posting_step(self):
        """The step that classifies the reviewed text and publishes it — the
        one place the workflow's own token is allowed to reach. Selected by
        the status post it makes, which is the thing that defines it; how it
        publishes the reviewed text is what this change moves."""
        found = [step for step in self.steps if "post_status()" in step]
        self.assertEqual(len(found), 1,
                         "expected exactly one step posting the verdict, found "
                         "%d" % len(found))
        return step_body(found[0])

    def test_the_pull_request_path_branches_on_the_secret(self):
        # A non-empty secret selects the CLI reviewer; an empty one falls back
        # to the poll, which is what every repository without the secret keeps
        # getting.
        self.assertIn('-n "${COPILOT_GITHUB_TOKEN:-}"', self.script)
        cli = self.script.index('-n "${COPILOT_GITHUB_TOKEN:-}"')
        poll = self.script.index("pulls/$PR_NUMBER/reviews")
        self.assertLess(cli, poll,
                        "the secret is tested after the poll rather than "
                        "selecting between the two paths")

    def test_the_pending_status_is_posted_before_any_provisioning(self):
        # Whatever fails afterwards — a checkout, an install, the CLI — the
        # required check reads `pending` rather than going unreported.
        first = run_block(self.steps[0])
        self.assertIn("state=pending", first)
        self.assertIn("context=%s" % STATUS_CONTEXT, first)
        for step in self.steps[1:]:
            self.assertNotIn("state=pending", run_block(step),
                             "pending is posted after the first step")

    def test_the_cli_path_checks_out_the_reviewed_commit_with_full_history(
            self):
        checkout = [step for step in self.steps
                    if "uses: actions/checkout" in step]
        self.assertEqual(len(checkout), 1,
                         "expected exactly one checkout step, found %d"
                         % len(checkout))
        self.assertIn("ref: ${{ github.event.pull_request.head.sha }}",
                      checkout[0])
        # The engine's merge-base diff needs the history behind both commits.
        self.assertIn("fetch-depth: 0", checkout[0])
        # Provisioning only happens where the CLI reviewer is configured.
        self.assertIn("env.COPILOT_CLI_REVIEWER == 'true'", checkout[0])

    def test_the_cli_path_provisions_difftastic_and_ripgrep(self):
        tooling = [step for step in self.steps
                   if "difft-x86_64-unknown-linux-gnu.tar.gz" in step]
        self.assertEqual(len(tooling), 1,
                         "expected exactly one difftastic install step, found "
                         "%d" % len(tooling))
        self.assertIn(
            "https://github.com/Wilfred/difftastic/releases/latest/download/"
            "difft-x86_64-unknown-linux-gnu.tar.gz", tooling[0])
        self.assertIn("$GITHUB_PATH", tooling[0])
        self.assertIn("ripgrep", tooling[0])
        self.assertIn("apt-get install", tooling[0])
        self.assertIn("env.COPILOT_CLI_REVIEWER == 'true'", tooling[0])

    def test_a_binary_less_archive_fails_the_difftastic_install_loudly(self):
        # The same guard the setup workflow carries: `find` printing nothing
        # would otherwise reach `install` as an empty source path. Failing
        # this step fails the CLI review, which leaves the `pending` posted
        # by the first step standing — the right outcome for a review that
        # never ran.
        tooling = [step for step in self.steps
                   if "difft-x86_64-unknown-linux-gnu.tar.gz" in step]
        run = run_block(tooling[0])
        self.assertIn('-z "$binary"', run,
                      "the located binary path is never tested for emptiness")
        self.assertLess(run.index('-z "$binary"'), run.index("install -m"),
                        "the emptiness guard runs after the install it is "
                        "supposed to protect")
        guard = run[run.index('-z "$binary"'):run.index("install -m")]
        self.assertIn("difft", guard,
                      "the failure message does not name the missing binary")
        self.assertIn("exit 1", guard,
                      "a binary-less archive does not fail the step")

    def test_the_cli_path_installs_the_copilot_cli(self):
        self.assertIn("npm install -g @github/copilot", self.script)

    def test_the_cli_install_is_pinned_to_an_exact_version(self):
        # An unpinned install changes what the gate runs on the CLI vendor's
        # schedule rather than this template's. The upgrade is a deliberate
        # bump in a template change, so the shipped install names a version.
        self.assertRegex(self.script, CLI_PIN,
                         "the Copilot CLI is not installed at an exact "
                         "pinned version")
        self.assertNotRegex(self.script, CLI_UNPINNED,
                            "a floating install of the Copilot CLI remains")

    def test_the_cli_step_carries_the_secret_and_no_other_credential(self):
        # The security boundary. The CLI runs `--allow-all-tools` on
        # instructions an adversarial change could try to steer, so the worst
        # a steered agent can reach is bounded by what is in its environment:
        # the minimal reviewer PAT (no repository access, Copilot Requests
        # only) and nothing else. With `github.token` absent it cannot forge
        # the required status or post as the workflow.
        cli = self.cli_step()
        self.assertIn("COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}",
                      cli)
        self.assertNotIn("GH_TOKEN", cli,
                         "the Copilot CLI step's environment carries a gh "
                         "credential")
        self.assertNotIn("github.token", cli,
                         "the Copilot CLI step's environment carries the "
                         "workflow token")

    def test_the_posting_step_carries_the_workflow_token_and_not_the_secret(
            self):
        posting = self.posting_step()
        self.assertNotEqual(
            posting, self.cli_step(),
            "the CLI run and the status posting are still one step, so the "
            "reviewer's environment holds the posting credential")
        self.assertIn("GH_TOKEN: ${{ github.token }}", posting)
        self.assertNotIn("COPILOT_GITHUB_TOKEN:", posting,
                         "the posting step's environment carries the reviewer "
                         "secret")

    def test_the_captured_output_travels_between_the_steps_as_a_file(self):
        # Splitting the credentials apart costs the shared shell, so the
        # reviewed text crosses the boundary as the workspace file it already
        # was, and the posting step picks its path off the job-level presence
        # boolean rather than the secret it can no longer see.
        expression = 'body_file="${RUNNER_TEMP:-.}/shipd-copilot-review-body.md"'
        self.assertIn(expression, run_block(self.cli_step()))
        posting = run_block(self.posting_step())
        self.assertIn(expression, posting)
        self.assertIn('"${COPILOT_CLI_REVIEWER:-false}" == \'true\'', posting,
                      "the posting step does not select the CLI path off the "
                      "job-level presence boolean")

    def test_the_findings_file_is_the_only_channel_it_added(self):
        # Anchoring gave the reviewer something new to say to the credentialed
        # step, and it says it the way the body already did: one workspace
        # file, written by a step holding only the reviewer PAT and read by a
        # step holding only `github.token`. Nothing new travels through a step
        # output or $GITHUB_ENV, which are channels the credentialed step
        # deliberately does not trust.
        expression = 'findings_file="${RUNNER_TEMP:-.}/%s"' % FINDINGS_FILE
        cli, posting = self.cli_step(), self.posting_step()
        self.assertIn(expression, run_block(cli),
                      "the reviewer step names no findings file")
        self.assertIn(expression, run_block(posting),
                      "the posting step reads the findings from another path")
        for step in (cli, posting):
            run = run_block(step)
            for channel in ("$GITHUB_OUTPUT", "$GITHUB_ENV"):
                self.assertNotIn('>> "%s"' % channel, run,
                                 "a step writes to %s" % channel)
                self.assertNotIn(">> %s" % channel, run,
                                 "a step writes to %s" % channel)
            self.assertNotIn("${{ steps.", step,
                             "a step output carries data between the steps")
        # And the reviewer is told to write it, at that same path: the
        # contract names the file, the prompt names where this run wants it.
        self.assertIn("$findings_file", run_block(cli))

    def test_the_findings_path_matches_the_skill_templates_own(self):
        # The write side is specified in the review contract, the read side
        # here. A path that drifted on either would silently post a review
        # with nothing anchored.
        self.assertIn(FINDINGS_FILE, read(SKILL_TEMPLATE),
                      "the review contract names no findings file")
        self.assertIn(FINDINGS_FILE, self.text)

    def test_the_reviewer_instructions_are_materialized_from_the_base_ref(self):
        # The instructions are the one input the reviewed change must not be
        # able to rewrite: a change that edits SKILL.md would otherwise be
        # reviewed under its own rules.
        cli = self.cli_step()
        self.assertIn("BASE_REF: ${{ github.event.pull_request.base.ref }}",
                      cli)
        run = run_block(cli)
        self.assertIn('skill_path="%s"' % GATE_SKILL_PATH, run)
        self.assertIn(
            'instructions_file="${RUNNER_TEMP:-.}/shipd-copilot-review-skill.md"',
            run)
        self.assertIn('git rev-parse --verify --quiet', run,
                      "the base ref is never resolved")
        self.assertIn('git show "$base_commit:$skill_path"', run,
                      "the reviewer instructions are not read from the base "
                      "ref")
        # The head's copy is the fallback — a pull request that installs the
        # integration has no base copy to read — and the run says so.
        fallback = run[run.index('git cat-file -e "$base_commit:$skill_path"'):]
        fallback = fallback[:fallback.index("prompt=")]
        self.assertIn('cp "$skill_path" "$instructions_file"', fallback,
                      "there is no head-copy fallback for a base ref without "
                      "the skill")
        self.assertIn("echo", fallback,
                      "the fallback to the head's copy is silent")

    def test_only_a_confirmed_absence_falls_back_to_the_head_copy(self):
        # The fallback un-pins the instructions, so it must be reachable from
        # exactly one cause: the base tree not carrying the file. An
        # unresolvable base ref, or a copy that is there and cannot be read,
        # is a failure to pin — and a gate that cannot pin must not review.
        run = run_block(self.cli_step())
        self.assertIn('git cat-file -e "$base_commit:$skill_path"', run,
                      "absence is never confirmed before falling back")
        self.assertLess(run.index('git cat-file -e "$base_commit:$skill_path"'),
                        run.index('cp "$skill_path" "$instructions_file"'),
                        "the head's copy is used before absence is confirmed")
        guard = run[run.index('base_commit="'):
                    run.index('cp "$skill_path" "$instructions_file"')]
        self.assertIn('if [[ -z "$base_commit" ]]; then', guard,
                      "an unresolvable base ref is not detected")
        self.assertEqual(
            guard.count("exit 1"), 2,
            "a base ref that cannot be resolved, and a skill that is present "
            "but cannot be read, do not both fail the reviewer step")

    def test_the_posting_step_is_insulated_from_the_reviewers_step(self):
        # A reviewer step runs before this one and can append to $GITHUB_PATH
        # and $GITHUB_ENV. Neither may reach the posting step: a shimmed `gh`
        # would run with `github.token`, and an injected
        # SHIPD_GATE_FAIL_OPEN=true would green a strict repository's
        # marker-less outcome.
        posting = self.posting_step()
        run = run_block(posting)
        self.assertIn("gh_bin=%s" % GH_PATH, run,
                      "the posting step does not resolve gh to an absolute "
                      "path")
        # And the path carries no environment override. $GITHUB_ENV writes land
        # in a later step's process environment, so a `${SHIPD_GATE_GH_BIN:-…}`
        # here would be a $GITHUB_PATH shim by another name — and a step's
        # `env:` cannot express "unset this" the way it re-binds the knob
        # below. The suite substitutes the literal instead.
        self.assertNotIn("SHIPD_GATE_GH_BIN", self.text,
                         "the credentialed gh path is redirectable through "
                         "the environment")
        self.assertNotRegex(
            run, r"gh_bin=.*\$\{?[A-Za-z_]",
            "the gh path is read from a variable an earlier step could write")
        for line in run.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            self.assertNotRegex(
                stripped, r"(^|[|&;(]\s*)gh\s",
                "the posting step invokes gh through PATH: %s" % stripped)
        self.assertIn("SHIPD_GATE_FAIL_OPEN: ${{ vars.SHIPD_GATE_FAIL_OPEN }}",
                      posting,
                      "the posting step does not re-bind the strictness knob "
                      "from the vars context, so a GITHUB_ENV write wins")

    def test_the_prompt_names_the_materialized_instructions_file(self):
        prompt = self.script[self.script.index("prompt="):
                             self.script.index('timeout "$cli_timeout"')]
        self.assertIn("$instructions_file", prompt,
                      "the prompt does not name the materialized instructions")
        self.assertNotIn(
            GATE_SKILL_PATH, prompt,
            "the prompt sends the reviewer to the live file on the ref under "
            "review")

    def test_the_cli_fail_open_description_names_the_cli_review(self):
        # A status reader can tell which reviewer produced a marker-less
        # outcome: the CLI path words its own, the poll and review-event paths
        # keep the shared default.
        posting = run_block(self.posting_step())
        self.assertIn(
            'description="${no_marker_description:-'
            'Copilot reviewed this commit; no verdict marker was parsed.}"',
            posting,
            "the shared marker-less description is no longer the default")
        overrides = [line.strip() for line in posting.splitlines()
                     if line.strip().startswith("no_marker_description=")]
        self.assertEqual(len(overrides), 1,
                         "expected exactly one marker-less description "
                         "override, found %d" % len(overrides))
        lowered = overrides[0].lower()
        self.assertIn("copilot cli", lowered,
                      "the CLI path's marker-less description does not name "
                      "the CLI review as its source")
        self.assertIn("no verdict marker", lowered)

    def test_the_cli_runs_non_interactively_under_a_bounded_timeout(self):
        # The bound's default is what every runner uses; the override exists so
        # the suite can drive a simulated timeout without waiting ten minutes.
        self.assertIn('cli_timeout="${SHIPD_GATE_CLI_TIMEOUT:-600}"',
                      self.script)
        self.assertIn('timeout "$cli_timeout" copilot -p ', self.script)
        self.assertIn("--allow-all-tools", self.script)

    def test_the_cli_prompt_defers_to_the_installed_skill(self):
        # The rubric lives in SKILL.md, one contract for both reviewer modes,
        # rather than being restated in YAML.
        self.assertIn(".github/skills/code-review/SKILL.md", self.script)
        prompt = self.script[self.script.index("prompt="):
                             self.script.index('timeout "$cli_timeout"')]
        self.assertIn("$BASE_SHA", prompt,
                      "the prompt does not name the base to diff")
        self.assertIn("$HEAD_SHA", prompt,
                      "the prompt does not name the commit under review")
        lowered = prompt.lower()
        self.assertIn("do not post", lowered,
                      "the prompt does not forbid the CLI from posting")
        self.assertIn("last line", lowered,
                      "the prompt does not require the marker as the last line")

    def test_the_cli_output_is_captured_to_the_workspace_file(self):
        # Only stdout: the CLI writes its report there and its run statistics
        # to stderr, which belongs in the job log, not in the classified text.
        run = self.script[self.script.index('timeout "$cli_timeout"'):]
        run = run[:run.index("; then")]
        self.assertIn('> "$body_file"', run)
        self.assertNotIn("2>&1", run,
                         "stderr is folded into the classified text")
        self.assertIn('body="$(<"$body_file")"', self.script)

    def test_the_review_text_is_never_posted_as_an_issue_comment(self):
        # The issue comment the gate used to post carried no anchoring and no
        # thread; the reviews API replaces it outright rather than doubling up.
        self.assertNotIn("pr comment", self.script,
                         "the gate still posts its report as an issue comment")

    def test_the_gates_own_review_is_posted_through_the_reviews_api(self):
        # An issue comment carries no anchoring and no thread to disposition.
        # The gate's own report is a pull-request review, submitted as a
        # `COMMENT`: the required status is the merge blocker, and a
        # `REQUEST_CHANGES` decision would need a human to dismiss it even
        # after the fix landed.
        posting = run_block(self.posting_step())
        self.assertIn('"repos/$REPO/pulls/$PR_NUMBER/reviews"', posting,
                      "the gate's own review is not posted through the "
                      "pull-request reviews API")
        self.assertIn('"event": "COMMENT"', posting,
                      "the review is not submitted as a COMMENT")
        for event in ("REQUEST_CHANGES", "APPROVE"):
            self.assertNotIn('"%s"' % event, posting,
                             "the review submits the event %s" % event)
        # After the verdict, so a failed publication cannot cost the status.
        # (`/reviews` alone would find the poll's own read of the endpoint,
        # which runs long before the verdict is known.)
        self.assertLess(posting.index('post_status "$state"'),
                        posting.index("review_payload="))

    def test_the_posting_step_verifies_findings_against_its_own_diff(self):
        # The findings file crosses the trust boundary from a reviewer that
        # ran `--allow-all-tools` over a steerable diff. Its paths and ranges
        # are claims, checked here against the diff this step read itself
        # before anything is anchored on them.
        posting = run_block(self.posting_step())
        self.assertIn('findings_file="${RUNNER_TEMP:-.}/%s"' % FINDINGS_FILE,
                      posting,
                      "the posting step reads no findings file")
        self.assertIn('"repos/$REPO/pulls/$PR_NUMBER/files', posting,
                      "the posting step never reads the diff it verifies "
                      "findings against")
        self.assertLess(posting.index("/files"),
                        posting.index('--input "$review_payload"'),
                        "the diff is read after the review is posted")

    def test_the_payload_builder_runs_from_an_absolute_interpreter(self):
        # Same hole `gh_bin` closes: an earlier step can prepend a directory
        # to $GITHUB_PATH, so a PATH-resolved interpreter in the credentialed
        # step would be the reviewer's own program.
        posting = run_block(self.posting_step())
        self.assertIn('py_bin=%s' % PY_PATH, posting,
                      "the payload builder's interpreter is not an absolute "
                      "literal")
        self.assertNotIn("$(command -v python3)", posting)
        self.assertNotIn('py_bin="${', posting,
                         "the interpreter path is read from an environment "
                         "variable an earlier step could write")

    def test_the_polled_body_reaches_the_classifier_through_a_file(self):
        # A polled review body is written to a workspace file and read back
        # with bash redirection: never through an environment variable (review
        # bodies reach 65,536 characters, close enough to the 128 KiB per-string
        # limit to matter) and never through a pipe.
        self.assertIn('> "$body_file"', self.script)
        self.assertIn('body="$(<"$body_file")"', self.script)
        self.assertEqual(
            self.script.count("REVIEW_BODY"), 1,
            "the env-passed body belongs to the review-event branch alone")
        poll = self.script[:self.script.index('body="$REVIEW_BODY"')]
        self.assertIn("$body_file", poll)
        self.assertNotIn("REVIEW_BODY", poll,
                         "the polling path carries the body in an environment "
                         "variable")

    def test_fix_required_maps_to_failure(self):
        branch = verdict_branches(self.text)["fix-required"]
        self.assertIn("failure", branch)
        self.assertNotIn("success", branch)

    def test_ship_it_maps_to_success(self):
        branch = verdict_branches(self.text)["ship-it"]
        self.assertIn("success", branch)
        self.assertNotIn("failure", branch)

    def test_a_marker_less_review_passes_fail_open_saying_so(self):
        branch = verdict_branches(self.text)["none"]
        self.assertIn("success", branch)
        self.assertNotIn("failure", branch)
        self.assertIn("no verdict", branch.lower(),
                      "the fail-open description must say no verdict was "
                      "parsed")

    def test_the_gate_job_reads_the_strictness_variable(self):
        # The knob is a repository Actions variable, hoisted into the job's
        # environment: a repository turns strictness on with `gh variable set`
        # rather than by patching the installed workflow, which the next
        # `shipd copilot add` would revert.
        self.assertIn("SHIPD_GATE_FAIL_OPEN: ${{ vars.SHIPD_GATE_FAIL_OPEN }}",
                      self.guard,
                      "the gate job does not read the SHIPD_GATE_FAIL_OPEN "
                      "repository variable into its environment")

    def test_the_no_marker_outcome_branches_on_the_strictness_variable(self):
        # Unset — which the runner interpolates as the empty string — or any
        # value other than `false` keeps the fail-open default, so the test is
        # on the one value that turns it off.
        self.assertIn('"${SHIPD_GATE_FAIL_OPEN:-true}" == "false"', self.script)

    def test_the_verdict_match_is_an_anchored_equality_test(self):
        # Equality against the extracted last line, never containment: a
        # review that quotes a marker while describing the diff must not be
        # classified by the quote.
        for marker in (FIX_MARKER, SHIP_MARKER):
            self.assertRegex(
                self.text,
                r"""\[\[ "\$\{?[A-Za-z_][A-Za-z0-9_]*\}?" == '%s' \]\]"""
                % re.escape(marker),
                "%r is not compared for equality against a single line"
                % marker)
            self.assertNotIn(
                "*'%s'*" % marker, self.text,
                "%r is still matched anywhere in the body" % marker)

    def test_the_last_line_is_extracted_with_parameter_expansion_only(self):
        # The extraction has to be pure bash for the same reason the match
        # is: shelling out reintroduces the pipe the regression below forbids.
        # `gh` and `sleep` are the poll's business; no text tool is anyone's.
        # Heredoc bodies are skipped: those lines are data the shell hands to
        # a program, not commands it runs, and the payload builder they carry
        # runs after the verdict is decided and reads its input from a file
        # rather than through a pipe.
        self.assertIn("${", self.script,
                      "the gate step does no parameter expansion at all")
        for line in shell_lines(self.script):
            if line.lstrip().startswith("#"):
                continue
            words = line.replace("$(", " ").replace("`", " ").split()
            for command in ("tail", "head", "awk", "sed", "grep", "cut", "tr",
                            "python", "python3"):
                self.assertNotIn(
                    command, words,
                    "the gate step shells out to %r: %s"
                    % (command, line.strip()))

    def test_the_review_body_is_never_piped_into_a_matcher(self):
        # `grep -q` exits at its first match, so on a review body larger than
        # the pipe buffer the writer dies of SIGPIPE, `pipefail` makes the
        # matched condition false, and a fix-required verdict falls through to
        # the fail-open branch and posts success. Review bodies reach 65,536
        # characters, well past that buffer — so the body is never piped, on
        # either path: the polled one is redirected into a file and read back,
        # the event-passed one is only ever expanded.
        carriers = ("REVIEW_BODY", "$body", "${body", "$(<")
        for line in self.script.splitlines():
            if line.lstrip().startswith("#"):
                continue
            if not any(carrier in line for carrier in carriers):
                continue
            self.assertNotIn("|", line,
                             "the review body is piped: %s" % line.strip())

    def test_the_blocking_verdict_is_tested_first(self):
        # A body carrying both markers must block, so fix-required is the
        # first arm of the conditional.
        self.assertLess(self.text.index(FIX_MARKER),
                        self.text.index(SHIP_MARKER))

    def test_exactly_one_optional_secret_scoped_to_the_copilot_cli(self):
        # `gh` authenticates with the workflow's own token throughout; the one
        # secret a repository may configure is the Copilot PAT, and it reaches
        # nothing but the CLI's own environment.
        self.assertIn("GH_TOKEN: ${{ github.token }}", self.text)
        self.assertEqual(
            set(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", self.text)),
            {"COPILOT_GITHUB_TOKEN"},
            "the template reads a secret other than the Copilot PAT")
        binding = "COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}"
        self.assertEqual(self.text.count(binding), 1,
                         "the secret's value is bound in more than one place")
        # The only other mention is the presence test hoisted to the job's
        # `env:`, which carries a boolean rather than the secret — a step's
        # `if:` cannot read the `secrets` context at all.
        self.assertIn(
            "COPILOT_CLI_REVIEWER: ${{ secrets.COPILOT_GITHUB_TOKEN != '' }}",
            self.text)
        self.assertEqual(self.text.count("${{ secrets.COPILOT_GITHUB_TOKEN }}"),
                         1)
        self.assertIn(binding, self.cli_step(),
                      "the secret is bound outside the step running the CLI")
        # No `gh` call is handed the secret: it authenticates on GH_TOKEN.
        # Both spellings count — the bare one the pending step uses and the
        # resolved `"$gh_bin"` the posting step is required to use.
        for line in self.script.splitlines():
            if line.lstrip().startswith("#"):
                continue
            if "gh " not in line and "$gh_bin" not in line:
                continue
            self.assertNotIn("COPILOT_GITHUB_TOKEN", line,
                             "a gh call carries the Copilot secret: %s"
                             % line.strip())

    def test_no_step_requests_copilot_as_a_reviewer(self):
        # Triggering the review stays GitHub-side: a per-PR reviewer request
        # or a branch ruleset. Nothing here asks for one.
        self.assertNotIn("requested_reviewers", self.text)
        self.assertNotIn("--add-reviewer", self.text)
        self.assertNotIn("gh pr edit", self.text)


# The review that motivated the anchor. Dogfooding on shipd-now-website#18 —
# the pull request that installs the skill — produced a Copilot review whose
# body quotes both verdict markers while describing the diff and ends with
# neither, which the shipped anywhere-in-body match classified `fix-required`
# on a passing pull request.
QUOTING_BODY = """## Pull Request Overview

This pull request adds the shipd code-review skill. The skill tells the
reviewing agent to end its report with `<!-- shipd-verdict: fix-required -->`
when a high-severity finding blocks the merge, and with
`<!-- shipd-verdict: ship-it -->` otherwise.

No blocking findings were identified.
"""


# A scripted `gh` for the runnable gate tests. Status posts are recorded; the
# reads the poll makes are served from files in ``$STUB_DIR``, and a read's
# answer may be scripted per call — ``ids.1``, ``ids.2``, … for successive
# reviews listings, ``head.1``, ``head.2``, … for successive reads of the pull
# request's own head — falling back to the unnumbered file once the script
# runs out. That is what lets a test drive a poll through several cycles and
# move the head underneath it.
GH_STUB = r'''#!/bin/sh
if [ "$1" = pr ]; then
  for arg in "$@"; do printf '%s\n' "$arg"; done >> "$GH_COMMENTS"
  exit 0
fi
url=
method=
input=
prev=
for arg in "$@"; do
  case "$prev" in
    --input) input="$arg" ;;
  esac
  case "$arg" in
    POST) method=POST ;;
    repos/*) url="$arg" ;;
  esac
  prev="$arg"
done
if [ "$method" = POST ]; then
  for arg in "$@"; do printf '%s\n' "$arg"; done >> "$GH_ARGS"
  # A review POST carries its payload in a file; record what was posted, not
  # just that something was, so the anchoring can be asserted.
  case "$url" in
    */reviews)
      if [ -n "$input" ] && [ -f "$input" ]; then
        cat "$input" >> "$GH_REVIEWS"
        printf '\n<<<REVIEW>>>\n' >> "$GH_REVIEWS"
      fi ;;
  esac
  exit 0
fi
serve() {
  n=1
  if [ -f "$STUB_DIR/$2" ]; then n=$(($(cat "$STUB_DIR/$2") + 1)); fi
  printf '%s' "$n" > "$STUB_DIR/$2"
  if [ -f "$STUB_DIR/$1.$n" ]; then cat "$STUB_DIR/$1.$n"
  elif [ -f "$STUB_DIR/$1" ]; then cat "$STUB_DIR/$1"
  fi
}
case "$url" in
  */files*)
    if [ -f "$STUB_DIR/files" ]; then cat "$STUB_DIR/files"; else printf '[]'; fi ;;
  */reviews/*)
    id="${url##*/}"
    if [ -f "$STUB_DIR/body.$id" ]; then cat "$STUB_DIR/body.$id"
    else cat "$STUB_DIR/body"; fi ;;
  */reviews) serve ids reviews-calls ;;
  */pulls/*) serve head head-calls ;;
esac
exit 0
'''


# The Copilot CLI, stubbed. It records the arguments it was handed, writes the
# scripted review on **stdout**, and writes a run-statistics footer on stderr —
# which is where the real CLI puts it. A gate that captured stderr into the
# classified text would read that footer as the last non-empty line and lose
# every verdict, so the stub emits one on every run.
#
# Its arguments are recorded one per record rather than one per line: the
# prompt is a paragraph, so a line-per-argument log could not be split back up.
COPILOT_STUB = r'''#!/bin/sh
for arg in "$@"; do printf '%s\n<<<ARG>>>\n' "$arg"; done >> "$COPILOT_ARGS"
printf 'Total duration 16s\nAI Credits used 6.64\n' >&2
# The findings file a reviewer following the contract writes beside its
# report — scripted per test, and absent for the reviewer that writes none.
if [ -f "$STUB_DIR/cli-findings" ]; then
  cp "$STUB_DIR/cli-findings" "$STUB_DIR/shipd-copilot-review-findings.json"
fi
if [ -f "$STUB_DIR/cli-out" ]; then cat "$STUB_DIR/cli-out"; fi
if [ -f "$STUB_DIR/cli-code" ]; then exit "$(cat "$STUB_DIR/cli-code")"; fi
exit 0
'''

# `timeout DURATION COMMAND ...`, stubbed: it runs the command, unless the test
# scripted the timeout itself — the real one kills the command and exits 124,
# so the stub exits without running it and writes nothing.
TIMEOUT_STUB = r'''#!/bin/sh
duration="$1"
shift
printf '%s\n' "$duration" >> "$TIMEOUT_ARGS"
if [ -f "$STUB_DIR/cli-timeout" ]; then exit 124; fi
exec "$@"
'''

# A hostile `gh`, standing in for the one a reviewer would leave on PATH by
# appending a directory of its own to $GITHUB_PATH. It records that it was
# reached and answers nothing — so a step that finds it posts no status.
SHIM_STUB = r'''#!/bin/sh
for arg in "$@"; do printf '%s\n' "$arg"; done >> "$SHIM_ARGS"
exit 0
'''

# `npm`, stubbed: the global install of the CLI is recorded, never run.
NPM_STUB = r'''#!/bin/sh
for arg in "$@"; do printf '%s\n' "$arg"; done >> "$NPM_ARGS"
exit 0
'''

# `git`, stubbed. Three calls have answers that matter, because the CLI path
# tells three outcomes apart: `rev-parse` resolving the base ref at all (a
# fetch that failed leaves it unresolvable), `cat-file -e` saying whether the
# base carries the review skill, and `show` reading it. Each is scriptable, so
# a test can drive the fallback and both fail-closed branches.
GIT_STUB = r'''#!/bin/sh
for arg in "$@"; do printf '%s\n' "$arg"; done >> "$GIT_ARGS"
case "$1" in
  rev-parse)
    if [ -f "$STUB_DIR/base-missing" ]; then exit 1; fi
    printf '%s\n' "@BASE_COMMIT@"
    exit 0 ;;
  cat-file)
    if [ -f "$STUB_DIR/base-skill" ]; then exit 0; fi
    echo "fatal: path does not exist in that ref" >&2
    exit 128 ;;
  show)
    if [ -f "$STUB_DIR/base-unreadable" ]; then
      echo "fatal: unable to read object" >&2
      exit 128
    fi
    if [ -f "$STUB_DIR/base-skill" ]; then cat "$STUB_DIR/base-skill"; exit 0; fi
    echo "fatal: path does not exist in that ref" >&2
    exit 128 ;;
esac
exit 0
'''

# What the stubbed `git rev-parse` resolves the base ref to. Every read of the
# instructions must be addressed to *this* commit: an argument naming
# `origin/<ref>` or a bare path would be a read of something the workflow never
# pinned.
BASE_COMMIT = "0" * 36 + "base"
GIT_STUB = GIT_STUB.replace("@BASE_COMMIT@", BASE_COMMIT)

# The review contract, in the two copies the CLI path chooses between: the base
# ref's (what a reviewer must follow) and the reviewed commit's own (the
# fallback, and what an adversarial change would rewrite).
BASE_SKILL = "# Review contract, as the base ref carries it.\n"
HEAD_SKILL = "# Review contract, as the reviewed commit carries it.\n"


class GateScriptCase(unittest.TestCase):
    """Base for the tests that *run* the gate job's script (copilot-review-skill
    gate-workflow-template): the step body is extracted from the template and
    run under bash against :data:`GH_STUB`, so what is asserted is the sequence
    of statuses a real event and a real review body produce."""

    HEAD = "0" * 39 + "1"
    MOVED = "0" * 39 + "2"

    # Scripted files the stubs serve from, cleared before each run.
    SCRIPTED = ("ids", "head", "body", "reviews-calls", "head-calls",
                "cli-out", "cli-code", "cli-timeout", "base-skill",
                "base-missing", "base-unreadable", "files", "cli-findings")

    def setUp(self):
        self.assertTrue(os.path.isfile(GATE_TEMPLATE),
                        "missing template %s" % GATE_TEMPLATE)
        self.tmp = tempfile.mkdtemp(prefix="shipd-copilot-gate-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.record = os.path.join(self.tmp, "gh-args")
        self.stub_bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.stub_bin)
        for name, source in (("gh", GH_STUB), ("copilot", COPILOT_STUB),
                             ("timeout", TIMEOUT_STUB), ("npm", NPM_STUB),
                             ("git", GIT_STUB)):
            stub = os.path.join(self.stub_bin, name)
            with open(stub, "w", encoding="utf-8") as fh:
                fh.write(source)
            os.chmod(stub, 0o755)
        script = gate_script(read(GATE_TEMPLATE))
        self.assertIn("api --method POST", script,
                      "no runnable gate step found in the template")
        # The posting step's `gh` is an absolute path with no environment knob
        # behind it, so pointing it at the stub is a rewrite of the extracted
        # text — one more substitution beside the runner's `${{ … }}`
        # expressions. Asserting the literal first is what stops a template
        # change silently sending these runs at a real `gh`: on the CI runner
        # this suite runs on, /usr/bin/gh exists and is authenticated.
        self.assertIn(GH_PATH, script,
                      "the posting step no longer names %s, so the stub "
                      "substitution below would not bind" % GH_PATH)
        script = script.replace(GH_PATH, os.path.join(self.stub_bin, "gh"))
        # The payload builder's interpreter, named by the same kind of absolute
        # literal and for the same reason — a PATH lookup would let a reviewer's
        # $GITHUB_PATH shim run as the credentialed step. Pointed at whatever
        # interpreter runs this suite, since the runner's own path need not
        # exist here.
        self.assertIn(PY_PATH, script,
                      "the posting step no longer names %s, so the stub "
                      "substitution below would not bind" % PY_PATH)
        self.script = script.replace(PY_PATH, sys.executable)
        # The checkout the CLI path runs in: the reviewed commit's own copy of
        # the review skill, at the path the workflow reads it from. It is the
        # fallback source, never the preferred one.
        head_skill = os.path.join(self.tmp, *GATE_SKILL_PATH.split("/"))
        os.makedirs(os.path.dirname(head_skill))
        with open(head_skill, "w", encoding="utf-8") as fh:
            fh.write(HEAD_SKILL)

    def recorded(self, name):
        """The argument lines a stub recorded in the last run, or ``[]``."""
        path = os.path.join(self.tmp, name + "-args")
        return read(path).splitlines() if os.path.exists(path) else []

    def cli_args(self):
        """The arguments the Copilot CLI was invoked with, or ``[]`` — split on
        the stub's record separator, since the prompt spans lines."""
        path = os.path.join(self.tmp, "copilot-args")
        if not os.path.exists(path):
            return []
        return read(path).split("\n<<<ARG>>>\n")[:-1]

    def plant(self, name, text):
        with open(os.path.join(self.tmp, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    def calls(self, counter):
        """How many reads the stub served for ``counter`` in the last run."""
        path = os.path.join(self.tmp, counter)
        return int(read(path)) if os.path.exists(path) else 0

    def instructions_path(self):
        """Where the CLI path materializes the reviewer's instructions."""
        return os.path.join(self.tmp, "shipd-copilot-review-skill.md")

    def instructions(self):
        """What the last run put in front of the reviewer, or ``None`` where it
        materialized nothing at all."""
        path = self.instructions_path()
        return read(path) if os.path.exists(path) else None

    def prompt(self):
        """The prompt the stubbed CLI was invoked with."""
        args = self.cli_args()
        self.assertIn("-p", args, "the CLI was never invoked with a prompt")
        return args[args.index("-p") + 1]

    def findings_path(self):
        """Where the reviewer leaves its machine-readable findings, and where
        the posting step reads them from."""
        return os.path.join(self.tmp, FINDINGS_FILE)

    def reviews(self):
        """The review payloads the run POSTed through the pull-request reviews
        API, parsed, in order."""
        path = os.path.join(self.tmp, "gh-reviews")
        if not os.path.exists(path):
            return []
        return [json.loads(chunk)
                for chunk in read(path).split("\n<<<REVIEW>>>\n")[:-1]]

    def gate(self, event="pull_request", body="", ids="", cycles=(), heads=(),
             bodies=None, interval="0", timeout="0", run_timeout=30,
             secret="", cli_out=None, cli_code=None, cli_timed_out=False,
             fail_open="", base_skill=BASE_SKILL, base_ref_missing=False,
             base_unreadable=False, expect_failure=False, path_shim=False,
             files=None, findings=None):
        """Run the gate script for ``event`` and return the statuses it posted,
        in order — one dict of ``-f key=value`` fields per post, with the URL
        it posted to under ``"url"``. What the run logged is left on
        ``self.stdout``.

        ``secret`` is the ``COPILOT_GITHUB_TOKEN`` the runner would interpolate:
        empty (the default) leaves every existing case on the poll path, and a
        non-empty one selects the CLI reviewer. ``cli_out`` is what the stubbed
        CLI writes on stdout, ``cli_code`` the status it exits with, and
        ``cli_timed_out`` makes the stubbed ``timeout`` kill it the way the real
        one does.

        ``base_skill`` is the review skill as the *base* ref carries it — the
        instructions the CLI path must review under. ``None`` is the base ref
        that has no copy at all (the pull request that installs the
        integration), which falls back to the reviewed commit's own.
        ``path_shim`` puts a hostile ``gh`` ahead of the stub on ``PATH``, the
        way a reviewer that appended a directory to ``$GITHUB_PATH`` would:
        it records that it was reached and answers nothing.

        ``base_ref_missing`` is the base ref that does not resolve, and
        ``base_unreadable`` the copy that is there but cannot be read: both
        are failures to *pin*, not absences, so both fail the reviewer step —
        which is what ``expect_failure`` allows the run to do.

        ``fail_open`` is the ``SHIPD_GATE_FAIL_OPEN`` repository variable as the
        runner interpolates it: the empty string (the default) is the variable
        being unset, ``None`` drops it from the environment altogether, and
        ``"false"`` is the strict repository.

        ``ids`` is the reviews listing the poll sees every cycle (``cycles``
        overrides it call by call), ``heads`` the pull request's own head call
        by call, and ``bodies`` maps a review id to its body where the default
        ``body`` will not do. The poll's cadence is driven flat out
        (``interval``/``timeout`` of ``0`` means: one cycle, no sleeping), so
        the timeout case costs milliseconds rather than fifteen minutes.

        The run is bounded by ``run_timeout``: reintroducing a trim that is
        quadratic in a trailing whitespace run makes the script crawl rather
        than misbehave (the shipped one classified a 65,000-space body in ~64s
        on the runner's bash, and minutes locally), and a poll that never
        notices a moved head spins forever — an unbounded ``run`` would stall
        the whole suite instead of reporting either."""
        for name in os.listdir(self.tmp):
            if name in self.SCRIPTED or name.split(".")[0] in self.SCRIPTED:
                os.remove(os.path.join(self.tmp, name))
        self.plant("head", self.HEAD)
        self.plant("ids", ids)
        self.plant("body", body)
        for cycle, listing in enumerate(cycles, start=1):
            self.plant("ids.%d" % cycle, listing)
        for cycle, sha in enumerate(heads, start=1):
            self.plant("head.%d" % cycle, sha)
        for review_id, text in (bodies or {}).items():
            self.plant("body.%s" % review_id, text)
        if cli_out is not None:
            self.plant("cli-out", cli_out)
        if cli_code is not None:
            self.plant("cli-code", str(cli_code))
        if cli_timed_out:
            self.plant("cli-timeout", "")
        if base_skill is not None:
            self.plant("base-skill", base_skill)
        if base_ref_missing:
            self.plant("base-missing", "")
        if base_unreadable:
            self.plant("base-unreadable", "")
        # The pull request's files as the API serves them — the diff the
        # posting step verifies findings against — and the findings file the
        # reviewer would have left beside its report.
        if files is not None:
            self.plant("files", json.dumps(files))
        if findings is not None:
            self.plant("cli-findings", findings if isinstance(findings, str)
                       else json.dumps(findings))
        script = os.path.join(self.tmp, "gate.sh")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(self.script)
        for name in ("gh-args", "comments-args", "copilot-args",
                     "timeout-args", "npm-args", "git-args", "shim-args",
                     "gh-reviews",
                     "shipd-copilot-review-skill.md",
                     "shipd-copilot-review-body.md",
                     "shipd-copilot-review-payload.json",
                     "shipd-copilot-review-plain.json",
                     "shipd-copilot-review-files.json",
                     FINDINGS_FILE):
            path = os.path.join(self.tmp, name)
            if os.path.exists(path):
                os.remove(path)
        search_path = self.stub_bin
        if path_shim:
            shim_bin = os.path.join(self.tmp, "shim")
            if not os.path.isdir(shim_bin):
                os.makedirs(shim_bin)
            shim = os.path.join(shim_bin, "gh")
            with open(shim, "w", encoding="utf-8") as fh:
                fh.write(SHIM_STUB)
            os.chmod(shim, 0o755)
            search_path = shim_bin + os.pathsep + search_path
        env = dict(os.environ)
        env.update({
            "PATH": search_path + os.pathsep + env.get("PATH", ""),
            "SHIM_ARGS": os.path.join(self.tmp, "shim-args"),
            "GH_ARGS": self.record,
            "GH_COMMENTS": os.path.join(self.tmp, "comments-args"),
            "GH_REVIEWS": os.path.join(self.tmp, "gh-reviews"),
            "COPILOT_ARGS": os.path.join(self.tmp, "copilot-args"),
            "TIMEOUT_ARGS": os.path.join(self.tmp, "timeout-args"),
            "NPM_ARGS": os.path.join(self.tmp, "npm-args"),
            "GIT_ARGS": os.path.join(self.tmp, "git-args"),
            "GH_TOKEN": "stub-token",
            "STUB_DIR": self.tmp,
            "RUNNER_TEMP": self.tmp,
            "EVENT_NAME": event,
            "REPO": "acme/widget",
            "PR_NUMBER": "7",
            "HEAD_SHA": self.HEAD,
            "BASE_SHA": "0" * 39 + "b",
            "BASE_REF": "main",
            # The repository secret, interpolated by the runner: empty unless a
            # test configures the CLI reviewer. It reaches only the step that
            # runs the CLI; the classifying step selects its path off the
            # job-level presence boolean below, which is all the runner gives
            # it.
            "COPILOT_GITHUB_TOKEN": secret,
            "COPILOT_CLI_REVIEWER": "true" if secret else "false",
            # What the runner interpolates on a review event, and the empty
            # string it interpolates on a pull-request one.
            "REVIEW_BODY": body if event == "pull_request_review" else "",
            "SHIPD_GATE_POLL_INTERVAL": interval,
            "SHIPD_GATE_POLL_TIMEOUT": timeout,
            "SHIPD_GATE_CLI_TIMEOUT": "5",
        })
        # The strictness variable, hoisted into the job's environment by the
        # runner. `None` is the environment the variable never reaches at all;
        # the empty string is what an unset repository variable interpolates to.
        if fail_open is None:
            env.pop("SHIPD_GATE_FAIL_OPEN", None)
        else:
            env["SHIPD_GATE_FAIL_OPEN"] = fail_open
        try:
            result = subprocess.run(["bash", script], cwd=self.tmp, env=env,
                                    capture_output=True, text=True,
                                    timeout=run_timeout)
        except subprocess.TimeoutExpired:
            self.fail("the gate step did not finish within %ss on a "
                      "%d-character body — the poll or the verdict parse no "
                      "longer terminates" % (run_timeout, len(body)))
        if expect_failure:
            self.assertNotEqual(result.returncode, 0,
                                "the run was expected to fail the reviewer "
                                "step and exited zero instead")
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
        self.stdout = result.stdout
        self.stderr = result.stderr
        return self.posted()

    def posted(self):
        """The recorded **status** posts, in order. The CLI path's review POST
        goes through the same `gh api --method POST`, so it is filtered out
        here by endpoint and read back through :meth:`reviews` instead."""
        if not os.path.exists(self.record):
            return []
        posts = []
        for arg in read(self.record).splitlines():
            if arg == "api":
                posts.append({})
            elif not posts:
                continue
            elif arg.startswith("repos/"):
                posts[-1]["url"] = arg
            elif "=" in arg and not arg.startswith("-"):
                key, _sep, value = arg.partition("=")
                posts[-1][key] = value
        return [post for post in posts if "/statuses/" in post.get("url", "")]

    def assertStates(self, posts, expected):
        self.assertEqual([post.get("state") for post in posts], expected)
        for post in posts:
            self.assertEqual(post.get("context"), STATUS_CONTEXT)
            self.assertEqual(post.get("url"),
                             "repos/acme/widget/statuses/" + self.HEAD,
                             "a status was posted off the triggering head")


class GatePollTest(GateScriptCase):
    """The `pull_request` path: pending, then the poll for Copilot's review of
    the triggering head (copilot-review-skill gate-workflow-template)."""

    def test_a_found_review_turns_pending_into_a_terminal_status(self):
        posts = self.gate(ids="42", body=SHIP_MARKER + "\n")
        self.assertStates(posts, ["pending", "success"])

    def test_the_newest_matching_review_is_the_one_classified(self):
        # The listing arrives in submission order, so the last id is Copilot's
        # latest word on this commit.
        posts = self.gate(ids="31\n42",
                          bodies={"31": FIX_MARKER + "\n",
                                  "42": SHIP_MARKER + "\n"})
        self.assertStates(posts, ["pending", "success"])

    def test_the_poll_keeps_cycling_until_the_review_lands(self):
        posts = self.gate(cycles=("", "", "42"), body=FIX_MARKER + "\n",
                          timeout="30", interval="0", run_timeout=10)
        self.assertStates(posts, ["pending", "failure"])
        self.assertEqual(self.calls("reviews-calls"), 3,
                         "the poll did not run one reviews read per cycle")

    def test_a_timed_out_poll_fails_loudly(self):
        # No review of this head ever arrives: the pending status stands and
        # no verdict is invented. The session flow is the manual out.
        posts = self.gate(ids="", timeout="0", expect_failure=True)
        self.assertStates(posts, ["pending"])
        self.assertGreaterEqual(self.calls("reviews-calls"), 1,
                                "the poll never looked for a review at all")

    def test_a_moved_head_stops_the_poll_quietly(self):
        # The second cycle sees a newer head: that push's own run owns the
        # gate, so this one exits without posting anything further.
        posts = self.gate(ids="", heads=(self.HEAD, self.MOVED),
                          timeout="30", interval="0", run_timeout=10)
        self.assertStates(posts, ["pending"])
        self.assertEqual(self.calls("head-calls"), 2,
                         "the poll does not re-read the head every cycle")


class GateCliReviewerTest(GateScriptCase):
    """The CLI reviewer path: with a ``COPILOT_GITHUB_TOKEN`` configured the
    gate runs the review itself through headless Copilot CLI instead of waiting
    on GitHub's review surface (copilot-review-skill gate-workflow-template)."""

    SECRET = "ghp-stub-copilot-pat"

    REVIEW = ("## Findings\n\nNothing blocking.\n\n**Verdict: Ship it**\n\n"
              + SHIP_MARKER + "\n")

    def cli_gate(self, **kwargs):
        kwargs.setdefault("secret", self.SECRET)
        return self.gate(**kwargs)

    def test_a_marker_ending_review_posts_pending_then_the_verdict(self):
        posts = self.cli_gate(cli_out=self.REVIEW)
        self.assertStates(posts, ["pending", "success"])
        self.assertIn("ship it", posts[-1].get("description", "").lower())

    def test_the_cli_is_installed_and_run_non_interactively(self):
        self.cli_gate(cli_out=self.REVIEW)
        npm = self.recorded("npm")
        self.assertEqual(npm[:2], ["install", "-g"])
        self.assertRegex(npm[2], r"^@github/copilot@\d+\.\d+\.\d+$",
                         "the CLI is not installed at an exact pinned version")
        args = self.cli_args()
        self.assertIn("-p", args)
        self.assertIn("--allow-all-tools", args)
        prompt = self.prompt()
        self.assertIn(self.instructions_path(), prompt)
        self.assertIn(self.HEAD, prompt,
                      "the prompt does not name the commit under review")
        # The run is bounded, and the bound is the one the step computed.
        self.assertEqual(self.recorded("timeout"), ["5"])

    def test_the_reviewer_reads_the_base_refs_instructions(self):
        # The instructions the reviewer follows come off the base ref, so a
        # change that edits SKILL.md is still reviewed under the rules it is
        # asking to change.
        self.cli_gate(cli_out=self.REVIEW)
        self.assertEqual(self.instructions(), BASE_SKILL,
                         "the reviewer was given instructions that did not "
                         "come from the base ref")
        git = self.recorded("git")
        self.assertIn("origin/main^{commit}", git,
                      "the base ref was never resolved")
        reads = [arg for arg in git if arg.endswith(":" + GATE_SKILL_PATH)]
        self.assertTrue(reads,
                        "the base ref's copy of the skill was never read")
        for arg in reads:
            self.assertTrue(
                arg.startswith(BASE_COMMIT + ":"),
                "the skill was read from %r rather than the resolved base "
                "commit" % arg)
        prompt = self.prompt()
        self.assertIn(self.instructions_path(), prompt)
        self.assertNotIn(GATE_SKILL_PATH, prompt,
                         "the prompt still sends the reviewer to the file on "
                         "the ref under review")

    def test_a_base_ref_without_the_skill_falls_back_to_the_head_copy(self):
        # The pull request that installs the integration: there is no base
        # copy to pin to, so the reviewed commit's own is used and the run
        # says so rather than reviewing against nothing.
        posts = self.cli_gate(cli_out=self.REVIEW, base_skill=None)
        self.assertStates(posts, ["pending", "success"])
        self.assertEqual(self.instructions(), HEAD_SKILL,
                         "the run did not fall back to the reviewed commit's "
                         "own copy of the skill")
        self.assertIn(GATE_SKILL_PATH, self.stdout,
                      "the fallback to the head's copy went unlogged")
        self.assertIn("main", self.stdout,
                      "the fallback log does not name the base ref that "
                      "lacked the skill")

    def test_a_path_shim_cannot_intercept_the_posting_steps_gh(self):
        # The $GITHUB_PATH vector, exercised rather than asserted: a hostile
        # `gh` sits ahead of the stub on PATH for the whole run. The posting
        # step resolves its binary absolutely, so its calls go straight past
        # the shim — while the *pending* step, which looks `gh` up on PATH
        # because it runs before the reviewer exists, is caught by it. That
        # split is the proof: the shim is live (it recorded the pending call)
        # and the credentialed calls still reached the real binary.
        posts = self.cli_gate(cli_out=self.REVIEW, path_shim=True)
        self.assertTrue(self.recorded("shim"),
                        "the shim was never on PATH, so this proves nothing")
        self.assertStates(posts, ["success"])
        self.assertNotEqual(self.reviews(), [],
                            "the shim swallowed the review POST too")

    def test_an_unresolvable_base_ref_fails_rather_than_un_pinning(self):
        # The fetch failed, or the branch is gone. Falling back here would
        # quietly review the change under its own instructions, which is the
        # thing the pinning exists to prevent — so the reviewer never runs.
        posts = self.cli_gate(cli_out=self.REVIEW, base_ref_missing=True,
                              expect_failure=True)
        self.assertStates(posts, ["pending"])
        self.assertEqual(self.cli_args(), [],
                         "the reviewer ran without pinned instructions")
        self.assertIn("main", self.stderr,
                      "the failure does not name the base ref it could not "
                      "resolve")
        self.assertEqual(self.reviews(), [])

    def test_an_unreadable_base_skill_fails_rather_than_un_pinning(self):
        # The base carries the file and it could not be read: an error, not
        # an absence, so the head's copy is not substituted for it.
        posts = self.cli_gate(cli_out=self.REVIEW, base_unreadable=True,
                              expect_failure=True)
        self.assertStates(posts, ["pending"])
        self.assertEqual(self.cli_args(), [],
                         "the reviewer ran without pinned instructions")
        self.assertNotEqual(self.instructions(), HEAD_SKILL,
                            "an unreadable base copy fell back to the ref "
                            "under review")
        self.assertIn(GATE_SKILL_PATH, self.stderr)

    def test_the_reviewed_text_is_posted_as_a_pull_request_review(self):
        self.cli_gate(cli_out=self.REVIEW)
        posted = self.reviews()
        self.assertEqual(len(posted), 1,
                         "the reviewed text was not posted as a review")
        self.assertEqual(posted[0]["body"], self.REVIEW,
                         "the review does not carry what the gate judged")
        self.assertEqual(posted[0]["event"], "COMMENT")
        self.assertEqual(posted[0]["commit_id"], self.HEAD)
        self.assertEqual(self.recorded("comments"), [],
                         "the report was also posted as an issue comment")

    def test_the_cli_path_never_polls_the_reviews_api(self):
        self.cli_gate(cli_out=self.REVIEW)
        self.assertEqual(self.calls("reviews-calls"), 0,
                         "the CLI path fell through into the poll")

    def test_a_fix_required_last_line_fails_the_check(self):
        posts = self.cli_gate(
            cli_out="One high-severity finding blocks.\n\n" + FIX_MARKER + "\n")
        self.assertStates(posts, ["pending", "failure"])

    def test_a_review_without_a_marker_fails_open(self):
        posts = self.cli_gate(cli_out=QUOTING_BODY)
        self.assertStates(posts, ["pending", "success"])
        description = posts[-1].get("description", "").lower()
        self.assertIn("no verdict", description)
        # Whose review produced no marker is exactly what a status reader
        # needs, and the two reviewers are not interchangeable.
        self.assertIn("copilot cli", description,
                      "the CLI path's fail-open description does not name the "
                      "CLI review as its source")

    def test_the_run_statistics_footer_never_reaches_the_classifier(self):
        # The real CLI writes its report on stdout and its statistics footer on
        # stderr. Capturing both would make the footer the last non-empty line
        # and throw every verdict away — the stub writes one on every run, so
        # only a stdout-only capture classifies this as `failure`.
        posts = self.cli_gate(cli_out="Blocking.\n\n" + FIX_MARKER + "\n")
        self.assertStates(posts, ["pending", "failure"])

    def test_a_nonzero_cli_run_fails_loudly(self):
        posts = self.cli_gate(cli_out="partial output\n", cli_code=1,
                              expect_failure=True)
        self.assertNotEqual(self.cli_args(), [],
                            "the CLI was never invoked at all")
        self.assertStates(posts, ["pending"])
        self.assertEqual(self.reviews(), [],
                         "a failed review was published anyway")

    def test_a_timed_out_cli_run_fails_loudly(self):
        posts = self.cli_gate(cli_timed_out=True, expect_failure=True)
        self.assertEqual(self.recorded("timeout"), ["5"],
                         "the CLI was not run under the bound at all")
        self.assertStates(posts, ["pending"])
        self.assertEqual(self.cli_args(), [],
                         "the timeout did not stop the CLI")
        self.assertEqual(self.reviews(), [])

    def test_an_empty_secret_keeps_the_poll_path(self):
        # Every repository without the secret keeps today's behaviour: the poll
        # runs, and the CLI is never installed or invoked.
        posts = self.gate(ids="42", body=SHIP_MARKER + "\n")
        self.assertStates(posts, ["pending", "success"])
        self.assertEqual(self.cli_args(), [])
        self.assertEqual(self.recorded("npm"), [])
        self.assertEqual(self.reviews(), [])
        self.assertGreaterEqual(self.calls("reviews-calls"), 1)


class GateReviewPostTest(GateScriptCase):
    """The CLI path publishes what it judged as a pull-request review, anchoring
    the reviewer's findings only where this step could verify them against the
    diff it read itself (copilot-review-skill gate-workflow-template)."""

    SECRET = "ghp-stub-copilot-pat"

    REVIEW = ("## Findings: ❌ Fix required\n\n"
              "| # | rating | details |\n| --- | --- | --- |\n"
              "| 1 | 🔴 high | `src/api/handler.py:11` — the backoff never "
              "resets |\n\n**Verdict: Fix required**\n\n" + FIX_MARKER + "\n")

    # 10 (context), 11–12 (added) and 13 (context) are the RIGHT-side lines
    # this diff makes commentable; 14 and beyond are not in it at all.
    FILES = [{"filename": "src/api/handler.py",
              "patch": ("@@ -10,2 +10,4 @@\n"
                        " ctx\n"
                        "+added one\n"
                        "+added two\n"
                        " ctx2\n")}]

    ANCHORED = {"severity": "high", "path": "src/api/handler.py",
                "start_line": 11, "end_line": 12,
                "detail": "The backoff never resets.",
                "replacement": ["    backoff = INITIAL", "    attempts = 0"]}

    def cli_gate(self, **kwargs):
        kwargs.setdefault("secret", self.SECRET)
        kwargs.setdefault("cli_out", self.REVIEW)
        kwargs.setdefault("files", self.FILES)
        return self.gate(**kwargs)

    def review(self):
        """The single review payload the run posted."""
        posted = self.reviews()
        self.assertEqual(len(posted), 1,
                         "expected exactly one review POST, got %d"
                         % len(posted))
        return posted[0]

    def test_the_review_carries_the_judged_body_as_a_comment_event(self):
        self.cli_gate(findings=[])
        review = self.review()
        self.assertEqual(review["event"], "COMMENT")
        self.assertEqual(review["commit_id"], self.HEAD)
        self.assertIn("**Verdict: Fix required**", review["body"])
        self.assertEqual(review["body"].strip().splitlines()[-1], FIX_MARKER,
                         "the verdict marker is no longer the body's last line")

    def test_a_verified_finding_is_anchored_on_its_range(self):
        self.cli_gate(findings=[self.ANCHORED])
        comments = self.review()["comments"]
        self.assertEqual(len(comments), 1)
        comment = comments[0]
        self.assertEqual(comment["path"], "src/api/handler.py")
        self.assertEqual((comment["start_line"], comment["line"]), (11, 12))
        self.assertEqual((comment["start_side"], comment["side"]),
                         ("RIGHT", "RIGHT"))
        self.assertIn("The backoff never resets.", comment["body"])

    def test_a_high_finding_is_anchored(self):
        finding = dict(self.ANCHORED, severity="high",
                       detail="High severity finding.")
        self.cli_gate(findings=[finding])
        comments = self.review()["comments"]
        self.assertEqual(len(comments), 1)
        self.assertIn("High severity finding.", comments[0]["body"])

    def test_a_medium_finding_is_anchored(self):
        finding = dict(self.ANCHORED, severity="medium",
                       detail="Medium severity finding.")
        self.cli_gate(findings=[finding])
        comments = self.review()["comments"]
        self.assertEqual(len(comments), 1)
        self.assertIn("Medium severity finding.", comments[0]["body"])

    def test_a_low_finding_is_never_anchored(self):
        # Same path and range as the high/medium cases above — only the
        # severity differs — so this is the anchor loop's own severity gate
        # under test, not `placed()`'s verification against the diff.
        finding = dict(self.ANCHORED, severity="low",
                       detail="Low severity finding.")
        self.cli_gate(findings=[finding])
        review = self.review()
        self.assertEqual(review.get("comments", []), [],
                         "a low-severity finding was anchored despite the "
                         "rubric never blocking on it")
        self.assertIn("### Findings not anchored to the diff", review["body"])
        self.assertIn("Low severity finding.", review["body"])

    def test_a_single_line_finding_keeps_the_single_line_anchor(self):
        finding = dict(self.ANCHORED, start_line=11, end_line=11)
        self.cli_gate(findings=[finding])
        comment = self.review()["comments"][0]
        self.assertEqual(comment["line"], 11)
        self.assertNotIn("start_line", comment)

    def test_a_replacement_becomes_a_committable_suggestion(self):
        self.cli_gate(findings=[self.ANCHORED])
        body = self.review()["comments"][0]["body"]
        self.assertIn("```suggestion\n    backoff = INITIAL\n    attempts = 0\n```",
                      body)

    def test_a_finding_without_a_replacement_carries_no_suggestion(self):
        finding = {k: v for k, v in self.ANCHORED.items()
                   if k != "replacement"}
        self.cli_gate(findings=[finding])
        comment = self.review()["comments"][0]
        self.assertNotIn("```suggestion", comment["body"])
        self.assertIn("The backoff never resets.", comment["body"])

    def test_a_finding_on_an_untouched_file_is_folded_into_the_body(self):
        # The reviewer names a file this pull request never touched. Anchoring
        # it would be posting a comment onto the reviewer's own claim.
        finding = dict(self.ANCHORED, path="other/module.py",
                       detail="Claimed defect in an untouched file.")
        self.cli_gate(findings=[finding])
        review = self.review()
        self.assertEqual(review.get("comments", []), [])
        self.assertIn("Claimed defect in an untouched file.", review["body"])
        self.assertIn("other/module.py", review["body"])
        self.assertEqual(review["body"].strip().splitlines()[-1], FIX_MARKER,
                         "the folded prose displaced the verdict marker")

    def test_a_range_leaving_the_diff_is_folded_into_the_body(self):
        # 13 is in the diff, 14 is not: a comment spanning both would be
        # rejected outright and cost every other finding with it.
        finding = dict(self.ANCHORED, start_line=13, end_line=14,
                       detail="Range half outside the diff.")
        self.cli_gate(findings=[finding])
        review = self.review()
        self.assertEqual(review.get("comments", []), [])
        self.assertIn("Range half outside the diff.", review["body"])

    def test_a_malformed_finding_is_folded_rather_than_dropped(self):
        finding = {"severity": "medium", "path": "src/api/handler.py",
                   "detail": "No range at all."}
        self.cli_gate(findings=[finding])
        review = self.review()
        self.assertEqual(review.get("comments", []), [])
        self.assertIn("No range at all.", review["body"])

    def test_a_missing_findings_file_still_posts_the_body(self):
        # Every reviewer that writes only a report — GitHub's surface, or a CLI
        # run that could not write the file — keeps working: the body is the
        # review, the findings file only anchors it.
        self.cli_gate()
        review = self.review()
        self.assertEqual(review.get("comments", []), [])
        self.assertIn("**Verdict: Fix required**", review["body"])

    def test_an_unparseable_findings_file_still_posts_the_body(self):
        self.cli_gate(findings="not json at all {")
        review = self.review()
        self.assertEqual(review.get("comments", []), [])
        self.assertIn("**Verdict: Fix required**", review["body"])

    def test_the_status_is_posted_whatever_the_findings_file_says(self):
        posts = self.cli_gate(findings="not json at all {")
        self.assertStates(posts, ["pending", "failure"])

    def test_the_poll_path_posts_no_review_of_its_own(self):
        # GitHub's own reviewer already posted its review; re-posting it would
        # duplicate it under the workflow's account.
        self.gate(ids="42", body=self.REVIEW, files=self.FILES,
                  findings=[self.ANCHORED])
        self.assertEqual(self.reviews(), [])


class GateVerdictParseTest(GateScriptCase):
    """The gate's verdict parse, executed on both paths: the classification is
    one shared block, so every body is put through the polled route and the
    review-event route and must come out the same."""

    def classify(self, body, run_timeout=30):
        """The terminal status ``body`` posts, proved identical on both
        paths."""
        terminal = {}
        for event in ("pull_request", "pull_request_review"):
            posts = self.gate(event=event, body=body, ids="42",
                              run_timeout=run_timeout)
            self.assertTrue(posts, "the gate posted no status at all")
            if event == "pull_request":
                self.assertEqual(posts[0].get("state"), "pending")
                self.assertEqual(len(posts), 2,
                                 "the polled review was not classified")
            terminal[event] = posts[-1]
        self.assertEqual(terminal["pull_request"],
                         terminal["pull_request_review"],
                         "the two paths classified the same body differently")
        return terminal["pull_request_review"]

    def test_a_quoted_marker_never_beats_the_ship_it_last_line(self):
        fields = self.classify(QUOTING_BODY + "\n" + SHIP_MARKER + "\n")
        self.assertEqual(fields.get("context"), STATUS_CONTEXT)
        self.assertEqual(fields.get("state"), "success",
                         "the quoted fix-required text won over the last line")

    def test_a_fix_required_last_line_fails_the_check(self):
        fields = self.classify("One high-severity finding blocks.\n\n"
                               + FIX_MARKER + "\n")
        self.assertEqual(fields.get("context"), STATUS_CONTEXT)
        self.assertEqual(fields.get("state"), "failure")

    def test_a_fix_required_last_line_survives_crlf_and_whitespace(self):
        fields = self.classify("One high-severity finding blocks.\r\n\r\n  "
                               + FIX_MARKER + "  \r\n\r\n")
        self.assertEqual(fields.get("state"), "failure")

    def test_a_long_trailing_whitespace_run_is_trimmed_promptly(self):
        # The liveness guard. Every way of asking bash for the trailing
        # whitespace in one shot is quadratic in the run — measured at 64s on
        # bash 5.2 and minutes on bash 3.2 for a body-sized 65,000 spaces —
        # and a gate job that crawls strands the required check in progress
        # until the job times out. Both placements of the run are covered: on
        # its own line after the verdict, and on the verdict's own line.
        fields = self.classify("One high-severity finding blocks.\n\n"
                               + FIX_MARKER + "\n" + " " * 65000 + "\n\n")
        self.assertEqual(fields.get("state"), "failure")
        fields = self.classify("One high-severity finding blocks.\n\n"
                               + FIX_MARKER + " " * 65000)
        self.assertEqual(fields.get("state"), "failure")

    def test_an_all_whitespace_body_fails_open(self):
        # The trim pattern needs a non-space character to anchor on; with
        # none, the whole string is the whitespace run and the line must come
        # out empty rather than erroring under `set -euo pipefail`.
        fields = self.classify("   \n\n \t \n")
        self.assertEqual(fields.get("state"), "success")
        self.assertIn("no verdict", fields.get("description", "").lower())

    def test_markers_quoted_only_mid_text_fail_open(self):
        fields = self.classify(QUOTING_BODY)
        self.assertEqual(fields.get("state"), "success")
        self.assertIn("no verdict",
                      fields.get("description", "").lower(),
                      "the fail-open description must say no verdict was "
                      "parsed")

    def test_an_empty_body_fails_open(self):
        fields = self.classify("")
        self.assertEqual(fields.get("state"), "success")
        self.assertIn("no verdict", fields.get("description", "").lower())


class GateStrictModeTest(GateScriptCase):
    """The `SHIPD_GATE_FAIL_OPEN` repository variable (copilot-review-skill
    gate-workflow-template). A repository that has ruled a marker-less review
    must never green the required check sets it to `false`; everything else —
    unset, or any other value — keeps the fail-open default. The knob is a
    variable rather than a local edit to the installed workflow because the
    next `shipd copilot add` reverts such an edit.

    Every classify path is covered, because they share one classification
    block: the polled review, the review event, and the CLI reviewer's own
    output."""

    SECRET = "ghp-stub-copilot-pat"

    # -- strict: `false` --------------------------------------------------

    def test_the_polled_path_leaves_pending_on_a_marker_less_review(self):
        posts = self.gate(ids="42", body=QUOTING_BODY, fail_open="false")
        self.assertStates(posts, ["pending"])

    def test_the_review_event_path_posts_nothing_on_a_marker_less_review(self):
        # A review event posts no pending of its own, so a strict marker-less
        # classification posts nothing at all and the pull-request run's
        # `pending` stands.
        posts = self.gate(event="pull_request_review", body=QUOTING_BODY,
                          fail_open="false")
        self.assertEqual(posts, [],
                         "a marker-less review event posted a status under "
                         "strict mode")

    def test_the_cli_path_leaves_pending_on_a_marker_less_review(self):
        posts = self.gate(secret=self.SECRET, cli_out=QUOTING_BODY,
                          fail_open="false")
        self.assertStates(posts, ["pending"])

    def test_the_cli_path_still_publishes_what_it_could_not_classify(self):
        # No status was derived from this text, which makes it exactly the
        # text an operator has to read to decide what to do about the pending
        # check. Posting it is what stops strict mode swallowing the review.
        self.gate(secret=self.SECRET, cli_out=QUOTING_BODY, fail_open="false")
        posted = self.reviews()
        self.assertEqual(len(posted), 1,
                         "strict mode swallowed the reviewer's own text")
        self.assertEqual(posted[0]["body"], QUOTING_BODY,
                         "the review does not carry what the reviewer wrote")

    def test_the_other_paths_still_publish_nothing(self):
        # A Copilot-authored review is already on the pull request; only the
        # CLI reviewer's own text is ever posted.
        self.gate(ids="42", body=QUOTING_BODY, fail_open="false")
        self.assertEqual(self.reviews(), [])
        self.gate(event="pull_request_review", body=QUOTING_BODY,
                  fail_open="false")
        self.assertEqual(self.reviews(), [])

    def test_the_strict_run_logs_the_no_verdict_condition_and_exits_zero(self):
        # `exit 0`: the run judged nothing, which is not a failure of the run.
        # The job's log is where an operator reads why the check stayed
        # pending, so the condition is stated there.
        self.gate(ids="42", body=QUOTING_BODY, fail_open="false")
        self.assertIn("no verdict", self.stdout.lower(),
                      "the strict run did not log that no verdict was parsed")

    def test_a_fix_required_verdict_still_fails_the_check(self):
        posts = self.gate(ids="42", body=FIX_MARKER + "\n", fail_open="false")
        self.assertStates(posts, ["pending", "failure"])

    def test_a_ship_it_verdict_still_passes_the_check(self):
        posts = self.gate(ids="42", body=SHIP_MARKER + "\n", fail_open="false")
        self.assertStates(posts, ["pending", "success"])

    def test_the_cli_reviewers_own_verdicts_still_classify(self):
        posts = self.gate(secret=self.SECRET, fail_open="false",
                          cli_out="Blocking.\n\n" + FIX_MARKER + "\n")
        self.assertStates(posts, ["pending", "failure"])

    # -- the fail-open default --------------------------------------------

    def test_an_unset_variable_keeps_the_fail_open_default(self):
        # What the runner interpolates for a variable the repository never set.
        posts = self.gate(ids="42", body=QUOTING_BODY, fail_open="")
        self.assertStates(posts, ["pending", "success"])
        description = posts[-1].get("description", "").lower()
        self.assertIn("no verdict", description)
        # The poll classified a review GitHub's own reviewer wrote, so the
        # description keeps the shared wording rather than the CLI path's.
        self.assertNotIn("copilot cli", description,
                         "the polled path claims the CLI reviewer's wording")

    def test_an_absent_variable_keeps_the_fail_open_default(self):
        posts = self.gate(ids="42", body=QUOTING_BODY, fail_open=None)
        self.assertStates(posts, ["pending", "success"])
        self.assertIn("no verdict", posts[-1].get("description", "").lower())

    def test_the_variable_set_true_keeps_the_fail_open_default(self):
        posts = self.gate(ids="42", body=QUOTING_BODY, fail_open="true")
        self.assertStates(posts, ["pending", "success"])

    def test_the_default_fails_open_on_the_review_event_path(self):
        posts = self.gate(event="pull_request_review", body=QUOTING_BODY)
        self.assertStates(posts, ["success"])
        self.assertIn("no verdict", posts[-1].get("description", "").lower())

    def test_the_default_fails_open_on_the_cli_path(self):
        posts = self.gate(secret=self.SECRET, cli_out=QUOTING_BODY)
        self.assertStates(posts, ["pending", "success"])
        self.assertIn("no verdict", posts[-1].get("description", "").lower())


class CopilotVerbTest(unittest.TestCase):
    """``shipd copilot`` (shipd-cli copilot-verb), driven as a black box
    against a throwaway target root — this checkout is never a target."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="shipd-copilot-test-")
        self.home = tempfile.mkdtemp(prefix="shipd-copilot-home-")
        self.version = json.loads(read(MANIFEST))["version"]

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    # -- runners -----------------------------------------------------------

    def env(self):
        env = dict(os.environ)
        env["HOME"] = self.home
        return env

    def cli(self, *args):
        """Run the binary itself (shebang + exec bit) against the temp root."""
        return subprocess.run(
            [BIN, "copilot", *args, "--root", self.root],
            capture_output=True, text=True, cwd=self.root, env=self.env())

    # -- target-tree helpers -----------------------------------------------

    def path(self, relative):
        return os.path.join(self.root, relative)

    def exists(self, relative):
        return os.path.exists(self.path(relative))

    def contents(self, relative):
        return read(self.path(relative))

    def plant(self, relative, text):
        """Write ``text`` at a managed path, creating its parents."""
        target = self.path(relative)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)

    def tree(self):
        """Every file under the target root, as root-relative paths."""
        found = set()
        for base, _dirs, names in os.walk(self.root):
            for name in names:
                found.add(os.path.relpath(os.path.join(base, name), self.root))
        return found

    def states(self, *args):
        """``{managed path: state word}`` parsed from a bare report."""
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        found = {}
        for line in result.stdout.splitlines():
            for relative in MANAGED:
                if relative in line:
                    found[relative] = line.split()[0]
        return found

    def install(self):
        """A clean, current install — the fixture most cases start from."""
        result = self.cli("add")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    # -- the bare report ---------------------------------------------------

    def test_bare_report_on_an_empty_root_is_all_absent(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        for relative in MANAGED:
            self.assertIn(relative, result.stdout)
        self.assertEqual(self.states(),
                         {relative: "absent" for relative in MANAGED})

    def test_bare_report_creates_nothing(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), set())

    def test_bare_report_notes_the_ruleset_and_the_absent_model_pin(self):
        result = self.cli()
        lowered = result.stdout.lower()
        self.assertIn("ruleset", lowered)
        self.assertIn("model", lowered)

    def test_bare_report_after_add_is_all_installed(self):
        self.install()
        self.assertEqual(self.states(),
                         {relative: "installed" for relative in MANAGED})

    def test_report_marks_a_differing_semdiff_stale(self):
        self.install()
        self.plant(SEMDIFF_PATH,
                   self.contents(SEMDIFF_PATH) + "\n# local edit\n")
        states = self.states()
        self.assertEqual(states[SEMDIFF_PATH], "stale")
        # The skill is only installed when its bundled engine matches.
        self.assertEqual(states[SKILL_PATH], "stale")
        self.assertEqual(states[WORKFLOW_PATH], "installed")
        self.assertEqual(states[GATE_PATH], "installed")

    def test_report_marks_an_older_marker_stale_naming_the_version(self):
        self.install()
        self.plant(WORKFLOW_PATH,
                   self.contents(WORKFLOW_PATH).replace(
                       "# shipd-copilot v%s" % self.version,
                       "# shipd-copilot v0.0.1"))
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.states()[WORKFLOW_PATH], "stale")
        self.assertIn("0.0.1", result.stdout)

    def test_report_marks_a_marker_less_file_foreign(self):
        self.plant(WORKFLOW_PATH, "name: someone else's workflow\n")
        self.assertEqual(self.states()[WORKFLOW_PATH], "foreign")

    def test_report_marks_a_marker_less_gate_workflow_foreign(self):
        self.plant(GATE_PATH, "name: someone else's gate\n")
        self.assertEqual(self.states()[GATE_PATH], "foreign")

    def test_report_marks_semdiff_foreign_when_its_skill_is_not_owned(self):
        self.plant(SKILL_PATH, "# someone else's skill\n")
        self.plant(SEMDIFF_PATH, read(PLUGIN_SEMDIFF))
        states = self.states()
        self.assertEqual(states[SKILL_PATH], "foreign")
        self.assertEqual(states[SEMDIFF_PATH], "foreign")

    # -- add ---------------------------------------------------------------

    def test_add_installs_exactly_the_four_managed_files(self):
        self.install()
        self.assertEqual(self.tree(), set(MANAGED))

    def test_add_substitutes_the_manifest_version_into_every_marker(self):
        self.install()
        skill = self.contents(SKILL_PATH)
        self.assertIn("<!-- shipd-copilot v%s -->" % self.version, skill)
        for relative in (WORKFLOW_PATH, GATE_PATH):
            self.assertIn("# shipd-copilot v%s" % self.version,
                          self.contents(relative), relative)
        for relative in MARKED:
            self.assertNotIn("{version}", self.contents(relative), relative)

    def test_add_installs_the_plugins_semdiff_byte_for_byte(self):
        self.install()
        with open(PLUGIN_SEMDIFF, "rb") as fh:
            expected = fh.read()
        with open(self.path(SEMDIFF_PATH), "rb") as fh:
            self.assertEqual(fh.read(), expected)

    def test_add_carries_no_marker_into_semdiff(self):
        self.install()
        self.assertNotIn("shipd-copilot v", self.contents(SEMDIFF_PATH))

    def test_repeated_add_is_idempotent(self):
        self.install()
        before = {relative: self.contents(relative) for relative in MANAGED}
        self.install()
        self.assertEqual(
            {relative: self.contents(relative) for relative in MANAGED},
            before)

    def test_add_upgrades_a_stale_install_to_the_current_version(self):
        self.install()
        self.plant(SKILL_PATH,
                   self.contents(SKILL_PATH).replace(
                       "<!-- shipd-copilot v%s -->" % self.version,
                       "<!-- shipd-copilot v0.0.1 -->"))
        self.install()
        self.assertIn("<!-- shipd-copilot v%s -->" % self.version,
                      self.contents(SKILL_PATH))
        self.assertNotIn("v0.0.1", self.contents(SKILL_PATH))
        self.assertEqual(self.states(),
                         {relative: "installed" for relative in MANAGED})

    def test_add_refuses_a_foreign_workflow_and_writes_nothing(self):
        self.plant(WORKFLOW_PATH, "name: someone else's workflow\n")
        result = self.cli("add")
        self.assertEqual(result.returncode, 1)
        self.assertIn(WORKFLOW_PATH, result.stderr)
        self.assertEqual(self.contents(WORKFLOW_PATH),
                         "name: someone else's workflow\n")
        # Nothing partially installed: the refusal is all-or-nothing.
        self.assertEqual(self.tree(), {WORKFLOW_PATH})

    def test_force_replaces_a_foreign_workflow(self):
        self.plant(WORKFLOW_PATH, "name: someone else's workflow\n")
        result = self.cli("add", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# shipd-copilot v%s" % self.version,
                      self.contents(WORKFLOW_PATH))
        self.assertEqual(self.tree(), set(MANAGED))

    def test_add_refuses_a_foreign_gate_workflow_and_writes_nothing(self):
        self.plant(GATE_PATH, "name: someone else's gate\n")
        result = self.cli("add")
        self.assertEqual(result.returncode, 1)
        self.assertIn(GATE_PATH, result.stderr)
        self.assertEqual(self.contents(GATE_PATH),
                         "name: someone else's gate\n")
        self.assertEqual(self.tree(), {GATE_PATH})

    def test_force_replaces_a_foreign_gate_workflow(self):
        self.plant(GATE_PATH, "name: someone else's gate\n")
        result = self.cli("add", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# shipd-copilot v%s" % self.version,
                      self.contents(GATE_PATH))
        self.assertEqual(self.tree(), set(MANAGED))

    def test_add_creates_the_parent_directories(self):
        self.assertFalse(os.path.isdir(os.path.join(self.root, ".github")))
        self.install()
        for relative in MANAGED:
            self.assertTrue(self.exists(relative), relative)

    def test_add_leaves_no_temporary_files_behind(self):
        self.install()
        self.assertEqual(
            [name for name in self.tree()
             if os.path.basename(name).startswith(".")], [])

    # -- remove ------------------------------------------------------------

    def test_remove_deletes_the_owned_files_and_prunes_the_skill_tree(self):
        self.install()
        result = self.cli("remove")
        self.assertEqual(result.returncode, 0, result.stderr)
        for relative in MANAGED:
            self.assertFalse(self.exists(relative), relative)
        self.assertFalse(os.path.isdir(
            os.path.join(self.root, ".github", "skills", "code-review")))

    def test_remove_on_an_empty_root_succeeds(self):
        result = self.cli("remove")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), set())

    def test_remove_is_idempotent(self):
        self.install()
        self.assertEqual(self.cli("remove").returncode, 0)
        self.assertEqual(self.cli("remove").returncode, 0)
        self.assertEqual(self.tree(), set())

    def test_remove_keeps_unmanaged_neighbours_and_their_directory(self):
        self.install()
        self.plant(os.path.join(".github", "workflows", "ci.yml"),
                   "name: ci\n")
        self.plant(os.path.join(".github", "skills", "code-review", "NOTES.md"),
                   "mine\n")
        self.assertEqual(self.cli("remove").returncode, 0)
        self.assertTrue(self.exists(os.path.join(".github", "workflows",
                                                 "ci.yml")))
        # The skill directory still holds a file, so it is not pruned.
        self.assertTrue(self.exists(
            os.path.join(".github", "skills", "code-review", "NOTES.md")))

    def test_remove_refuses_a_foreign_skill_and_deletes_nothing(self):
        self.install()
        self.plant(SKILL_PATH, "# someone else's skill\n")
        result = self.cli("remove")
        self.assertEqual(result.returncode, 1)
        self.assertIn(SKILL_PATH, result.stderr)
        self.assertEqual(self.tree(), set(MANAGED))

    def test_force_removes_a_foreign_skill(self):
        self.install()
        self.plant(SKILL_PATH, "# someone else's skill\n")
        result = self.cli("remove", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), set())

    def test_remove_refuses_a_foreign_gate_workflow_and_deletes_nothing(self):
        self.install()
        self.plant(GATE_PATH, "name: someone else's gate\n")
        result = self.cli("remove")
        self.assertEqual(result.returncode, 1)
        self.assertIn(GATE_PATH, result.stderr)
        self.assertEqual(self.tree(), set(MANAGED))

    def test_force_removes_a_foreign_gate_workflow(self):
        self.install()
        self.plant(GATE_PATH, "name: someone else's gate\n")
        result = self.cli("remove", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), set())


if __name__ == "__main__":
    unittest.main()
