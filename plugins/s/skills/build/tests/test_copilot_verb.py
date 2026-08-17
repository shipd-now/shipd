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


def gate_script(text, substitute="stub"):
    """The gate job's step body, runnable under bash: the Actions expressions
    the runner would interpolate are replaced by ``substitute``. Everything the
    script needs of the event reaches it through the step's ``env:``, so a run
    is driven entirely by the environment the test sets."""
    return ACTIONS_EXPRESSION.sub(substitute, run_block(gate_job(text)))


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


class WorkflowTemplateTest(unittest.TestCase):
    """``integrations/copilot/copilot-code-review.yml``
    (copilot-review-skill setup-workflow-template)."""

    def setUp(self):
        self.assertTrue(os.path.isfile(WORKFLOW_TEMPLATE),
                        "missing template %s" % WORKFLOW_TEMPLATE)
        self.text = read(WORKFLOW_TEMPLATE)

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

    def test_permissions_grant_statuses_write_and_pull_requests_read(self):
        block = [line.strip() for line in yaml_block(self.text, "permissions")]
        self.assertIn("statuses: write", block)
        # The poll reads the pull request's reviews and its current head.
        self.assertIn("pull-requests: read", block)

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
        self.assertIn("${", self.script,
                      "the gate step does no parameter expansion at all")
        for line in self.script.splitlines():
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

    def test_only_the_workflows_own_token_authenticates(self):
        self.assertIn("GH_TOKEN: ${{ github.token }}", self.text)
        self.assertNotIn("secrets.", self.text)
        self.assertNotIn("${{ secrets", self.text)

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
url=
method=
for arg in "$@"; do
  case "$arg" in
    POST) method=POST ;;
    repos/*) url="$arg" ;;
  esac
done
if [ "$method" = POST ]; then
  for arg in "$@"; do printf '%s\n' "$arg"; done >> "$GH_ARGS"
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
  */reviews/*)
    id="${url##*/}"
    if [ -f "$STUB_DIR/body.$id" ]; then cat "$STUB_DIR/body.$id"
    else cat "$STUB_DIR/body"; fi ;;
  */reviews) serve ids reviews-calls ;;
  */pulls/*) serve head head-calls ;;
esac
exit 0
'''


class GateScriptCase(unittest.TestCase):
    """Base for the tests that *run* the gate job's script (copilot-review-skill
    gate-workflow-template): the step body is extracted from the template and
    run under bash against :data:`GH_STUB`, so what is asserted is the sequence
    of statuses a real event and a real review body produce."""

    HEAD = "0" * 39 + "1"
    MOVED = "0" * 39 + "2"

    # Scripted files the stub serves from, cleared before each run.
    SCRIPTED = ("ids", "head", "body", "reviews-calls", "head-calls")

    def setUp(self):
        self.assertTrue(os.path.isfile(GATE_TEMPLATE),
                        "missing template %s" % GATE_TEMPLATE)
        self.script = gate_script(read(GATE_TEMPLATE))
        self.assertIn("gh api", self.script,
                      "no runnable gate step found in the template")
        self.tmp = tempfile.mkdtemp(prefix="shipd-copilot-gate-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.record = os.path.join(self.tmp, "gh-args")
        self.stub_bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.stub_bin)
        stub = os.path.join(self.stub_bin, "gh")
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write(GH_STUB)
        os.chmod(stub, 0o755)

    def plant(self, name, text):
        with open(os.path.join(self.tmp, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    def calls(self, counter):
        """How many reads the stub served for ``counter`` in the last run."""
        path = os.path.join(self.tmp, counter)
        return int(read(path)) if os.path.exists(path) else 0

    def gate(self, event="pull_request", body="", ids="", cycles=(), heads=(),
             bodies=None, interval="0", timeout="0", run_timeout=30):
        """Run the gate script for ``event`` and return the statuses it posted,
        in order — one dict of ``-f key=value`` fields per post, with the URL
        it posted to under ``"url"``.

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
        script = os.path.join(self.tmp, "gate.sh")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(self.script)
        if os.path.exists(self.record):
            os.remove(self.record)
        env = dict(os.environ)
        env.update({
            "PATH": self.stub_bin + os.pathsep + env.get("PATH", ""),
            "GH_ARGS": self.record,
            "GH_TOKEN": "stub-token",
            "STUB_DIR": self.tmp,
            "RUNNER_TEMP": self.tmp,
            "EVENT_NAME": event,
            "REPO": "acme/widget",
            "PR_NUMBER": "7",
            "HEAD_SHA": self.HEAD,
            # What the runner interpolates on a review event, and the empty
            # string it interpolates on a pull-request one.
            "REVIEW_BODY": body if event == "pull_request_review" else "",
            "SHIPD_GATE_POLL_INTERVAL": interval,
            "SHIPD_GATE_POLL_TIMEOUT": timeout,
        })
        try:
            result = subprocess.run(["bash", script], cwd=self.tmp, env=env,
                                    capture_output=True, text=True,
                                    timeout=run_timeout)
        except subprocess.TimeoutExpired:
            self.fail("the gate step did not finish within %ss on a "
                      "%d-character body — the poll or the verdict parse no "
                      "longer terminates" % (run_timeout, len(body)))
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.posted()

    def posted(self):
        """The recorded status posts, in order."""
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
        return posts

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

    def test_a_timed_out_poll_leaves_pending(self):
        # No review of this head ever arrives: the pending status stands and
        # no verdict is invented. The session flow is the manual out.
        posts = self.gate(ids="", timeout="0")
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
