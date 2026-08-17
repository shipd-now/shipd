#!/usr/bin/env python3
"""Tests for the Copilot code-review integration (copilot-review-skill, and
``shipd copilot`` under shipd-cli).

Two layers, both black-box:

* **The templates** shipped at ``plugins/s/integrations/copilot/`` are read off
  disk and asserted on their content — the marker lines carrying the literal
  ``{version}`` placeholder, the instructions the reviewing agent follows, the
  setup workflow's single job and tooling steps, and the gate workflow's
  triggers, guards, and verdict mapping.
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

    def guard(self, event):
        """The ``if`` guard of the single job gated on ``event`` — everything
        the job declares before its ``steps:``."""
        matching = [body for body in job_blocks(self.text).values()
                    if "github.event_name == '%s'" % event in body]
        self.assertEqual(len(matching), 1,
                         "expected exactly one job gated on %r" % event)
        body = matching[0]
        self.assertIn("steps:", body)
        return body[:body.index("steps:")], body

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

    def test_permissions_grant_statuses_write(self):
        block = [line.strip() for line in yaml_block(self.text, "permissions")]
        self.assertIn("statuses: write", block)

    def test_pull_request_events_post_pending_on_the_head_sha(self):
        _guard, body = self.guard("pull_request")
        self.assertIn("state=pending", body)
        self.assertIn("context=%s" % STATUS_CONTEXT, body)
        self.assertIn(
            "repos/${{ github.repository }}/statuses/"
            "${{ github.event.pull_request.head.sha }}", body)

    def test_the_bridge_guards_the_reviewer_login_and_the_head_commit(self):
        guard, _body = self.guard("pull_request_review")
        self.assertIn("github.event.review.user.login == "
                      "'copilot-pull-request-reviewer[bot]'", guard)
        self.assertIn("github.event.review.commit_id == "
                      "github.event.pull_request.head.sha", guard)

    def test_the_bridge_posts_the_same_status_context_on_the_head_sha(self):
        _guard, body = self.guard("pull_request_review")
        self.assertIn("context=%s" % STATUS_CONTEXT, body)
        self.assertIn(
            "repos/${{ github.repository }}/statuses/"
            "${{ github.event.pull_request.head.sha }}", body)

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

    def test_the_verdict_match_is_a_pure_bash_substring_test(self):
        for marker in (FIX_MARKER, SHIP_MARKER):
            self.assertIn("""[[ "$REVIEW_BODY" == *'%s'* ]]""" % marker,
                          self.text,
                          "%r is not matched by a bash substring test" % marker)

    def test_the_review_body_is_never_piped_into_a_matcher(self):
        # `grep -q` exits at its first match, so on a review body larger than
        # the pipe buffer the writer dies of SIGPIPE, `pipefail` makes the
        # matched condition false, and a fix-required verdict falls through to
        # the fail-open branch and posts success. Review bodies reach 65,536
        # characters, well past that buffer — so the body is never piped.
        for line in self.text.splitlines():
            if "$REVIEW_BODY" in line and not line.lstrip().startswith("#"):
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
