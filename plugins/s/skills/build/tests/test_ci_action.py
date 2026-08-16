#!/usr/bin/env python3
"""Tests for the repo-root ``action.yml`` — the composite GitHub Action that
runs shipd's structural spec lint in a consumer repository's CI.

The manifest is read as text and parsed by a tiny indentation-based reader
(:func:`parse_action`): the engine is stdlib-only, so no YAML parser is
available and none is introduced. The reader is deliberately narrow — it
understands exactly the shape this repository's ``action.yml`` is authored in.

Two kinds of assertion:

* *structural* — the manifest declares the composite contract (``using:
  composite``, the ``path`` input and its ``.`` default, ``spec_lint.py``
  reached through the action-path variable, no third-party ``uses:`` step and
  no cache step);
* *executable* — each step's ``run:`` body is executed verbatim under
  GitHub's composite shell (``bash -e -o pipefail``) with ``GITHUB_ACTION_PATH``
  pointing at this checkout and the step's ``env:`` values substituted, against
  fabricated fixture repositories. That proves the command line the manifest
  encodes actually lints, rather than merely that it mentions the right script.

Follows ``test_install.py``'s pattern of testing a repo file (outside
``plugins/s/``) from the plugin's own test suite.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# tests -> build -> skills -> s -> plugins -> repository root
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
ACTION_YML = os.path.join(REPO_ROOT, "action.yml")

# The expression a step's `env:` may bind to the consumer directory input.
INPUTS_PATH_EXPR = "${{ inputs.path }}"

# The composite shell GitHub runs a `shell: bash` step under.
COMPOSITE_BASH = ["bash", "-e", "-o", "pipefail"]


def read_action():
    with open(ACTION_YML, encoding="utf-8") as fh:
        return fh.read()


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def parse_action(text):
    """Parse ``action.yml`` into ``(top_level, steps)``.

    ``top_level`` maps the scalar keys seen at column 0 and inside ``runs:``
    (as ``runs.using``) plus the ``path`` input's keys (as
    ``inputs.path.<key>``). ``steps`` is a list of dicts with the scalar step
    keys, an ``env`` dict, and the ``run`` block's dedented body.
    """
    lines = text.splitlines()
    top = {}
    steps = []
    scalar = re.compile(r"^(\s*)([A-Za-z_][\w.-]*):\s*(.*)$")

    # Scalars at column 0, `runs.using`, and the `path` input's keys.
    section = None
    for i, line in enumerate(lines):
        m = scalar.match(line)
        if not m:
            continue
        pad, key, value = _indent(line), m.group(2), m.group(3).strip()
        if value in (">", ">-", "|", "|-"):
            value = _block_value(lines, i + 1, pad)
        if pad == 0:
            section = key
            if value:
                top[key] = value
            continue
        if section == "runs" and pad == 2 and value:
            top["runs.%s" % key] = value
        elif section == "inputs" and pad == 2 and key == "path":
            top["inputs.path"] = value
        elif section == "inputs" and pad == 4 and "inputs.path" in top:
            top["inputs.path.%s" % key] = value

    # The steps list under `runs:`.
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "steps:" and _indent(line) == 2:
            start = i + 1
            break
    if start is None:
        return top, steps

    item = re.compile(r"^(\s*)-\s+([A-Za-z_][\w-]*):\s*(.*)$")
    current = None
    mode = None  # None | "env" | "run"
    run_lines = []
    run_indent = None

    def flush():
        if current is not None:
            current["run"] = _dedent(run_lines, run_indent)
            steps.append(current)

    for line in lines[start:]:
        if line.strip() and _indent(line) == 0:
            break  # a new top-level key ends the steps list
        m = item.match(line)
        if m and _indent(line) == 4:
            flush()
            current = {"env": {}, "run": ""}
            run_lines, run_indent, mode = [], None, None
            current[m.group(2)] = m.group(3).strip()
            continue
        if current is None:
            continue
        if mode == "run":
            if not line.strip() or _indent(line) >= run_indent:
                run_lines.append(line)
                continue
            mode = None
        m = scalar.match(line)
        if m and _indent(line) == 6:
            key, value = m.group(2), m.group(3).strip()
            if key == "env" and not value:
                mode = "env"
            elif key == "run" and value in ("|", "|-"):
                mode, run_indent = "run", 8
            else:
                mode = None
                current[key] = value
            continue
        if mode == "env" and m and _indent(line) == 8:
            current["env"][m.group(2)] = m.group(3).strip()
    flush()
    return top, steps


def _block_value(lines, start, pad):
    """Join the indented continuation lines of a block scalar opened at
    ``pad`` — enough to read a folded ``description:``."""
    body = []
    for line in lines[start:]:
        if not line.strip():
            body.append("")
            continue
        if _indent(line) <= pad:
            break
        body.append(line.strip())
    return " ".join(part for part in body if part)


def _dedent(run_lines, run_indent):
    if not run_lines:
        return ""
    body = [ln[run_indent:] if len(ln) >= run_indent else ln.lstrip(" ")
            for ln in run_lines]
    while body and not body[-1].strip():
        body.pop()
    return "\n".join(body) + "\n" if body else ""


# ---------------------------------------------------------------------------
# Fixture repositories
# ---------------------------------------------------------------------------

MASTER_SPEC = """# billing

### Requirement: Charge on invoice close
id: charge-on-close

The system SHALL charge the customer's payment method when an invoice closes.

#### Scenario: Invoice closes
- **WHEN** an invoice transitions to closed
- **THEN** the payment method on file is charged
"""

PLAN = """# widget-refund
Status: ready

## Idea

Refund a charge when a closed invoice is voided.

### Motivation

Customers charged for a voided invoice must be made whole automatically.

### Details

- Capability: `billing`.

### Non-goals

- No partial refunds.

## Implementation

Issue the refund from the invoice-void handler.
"""

TASKS = """## 1. Refunds

- [ ] 1.1 [req: refund-on-void] Refund the charge when an invoice is voided
"""

GOOD_DELTA = """## ADDED Requirements

### Requirement: Refund on void
id: refund-on-void

The system SHALL refund the charge when a closed invoice is voided.

#### Scenario: Voided invoice is refunded
- **WHEN** a closed invoice is voided
- **THEN** the original charge is refunded in full
"""

# The same requirement with its `#### Scenario:` block removed — a structural
# error `spec_lint.py` reports for any delta.
BAD_DELTA = """## ADDED Requirements

### Requirement: Refund on void
id: refund-on-void

The system SHALL refund the charge when a closed invoice is voided.
"""


def write(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def make_fixture_repo(root, content_dir=".shipd", delta=GOOD_DELTA):
    """Fabricate a consumer repository at ``root``: one verified capability
    master plus one planned change whose delta is ``delta``, both under
    ``content_dir``."""
    base = os.path.join(root, content_dir)
    write(os.path.join(base, "verified", "billing", "spec.md"), MASTER_SPEC)
    change = os.path.join(base, "planned", "widget-refund")
    write(os.path.join(change, "plan.md"), PLAN)
    write(os.path.join(change, "tasks.md"), TASKS)
    write(os.path.join(change, "specs", "billing", "spec.md"), delta)
    return root


class ManifestTest(unittest.TestCase):
    """The manifest declares the composite contract (composite-lint-action)."""

    def setUp(self):
        self.assertTrue(
            os.path.isfile(ACTION_YML),
            "no composite action manifest at %s" % ACTION_YML)
        self.text = read_action()
        self.top, self.steps = parse_action(self.text)

    def test_declares_composite_runner(self):
        self.assertEqual(
            self.top.get("runs.using", "").strip('"\''), "composite")

    def test_names_and_describes_the_action(self):
        for key in ("name", "description"):
            self.assertTrue(self.top.get(key),
                            "action.yml has no top-level `%s`" % key)

    def test_path_input_defaults_to_repository_root(self):
        self.assertIn("inputs.path", self.top,
                      "action.yml declares no `path` input")
        self.assertEqual(
            self.top.get("inputs.path.default", "").strip('"\''), ".")

    def test_steps_run_spec_lint_via_the_action_path_variable(self):
        self.assertEqual(len(self.steps), 2,
                         "expected the master-library and per-change steps")
        for step in self.steps:
            self.assertEqual(step.get("shell"), "bash")
            self.assertIn("$GITHUB_ACTION_PATH", step["run"])
            self.assertIn("spec_lint.py", step["run"])

    def test_steps_bind_the_path_input(self):
        for step in self.steps:
            self.assertIn(
                INPUTS_PATH_EXPR, list(step["env"].values()),
                "step %r binds no env value to the `path` input"
                % step.get("name"))

    def test_no_third_party_step_and_no_cache(self):
        for line in self.text.splitlines():
            self.assertNotRegex(line, r"^\s*-?\s*uses:")
        self.assertNotIn("actions/cache", self.text)
        self.assertNotIn("actions/setup-python", self.text)


class EncodedCommandTest(unittest.TestCase):
    """The encoded command lints for real (composite-lint-action): a valid
    consumer repository passes, a structurally broken change fails."""

    def setUp(self):
        self.assertTrue(
            os.path.isfile(ACTION_YML),
            "no composite action manifest at %s" % ACTION_YML)
        _top, self.steps = parse_action(read_action())
        self.tmp = tempfile.mkdtemp(prefix="shipd-ci-action-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # A private HOME so the layered config search can never reach the
        # developer's own ~/.shipd-config.json.
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)

    def run_steps(self, target):
        """Run every step's ``run`` body the way a composite action would,
        stopping at the first failure. Returns ``(returncode, output)``."""
        env = dict(os.environ)
        env.update({
            "HOME": self.home,
            "GITHUB_ACTION_PATH": REPO_ROOT,
        })
        output = []
        for i, step in enumerate(self.steps):
            step_env = dict(env)
            for key, value in step["env"].items():
                step_env[key] = (
                    target if value == INPUTS_PATH_EXPR else value)
            script = write(
                os.path.join(self.tmp, "step-%d.sh" % i), step["run"])
            proc = subprocess.run(
                COMPOSITE_BASH + [script], cwd=self.tmp, env=step_env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output.append(proc.stdout.decode("utf-8", "replace"))
            if proc.returncode != 0:
                return proc.returncode, "".join(output)
        return 0, "".join(output)

    def test_valid_repository_passes(self):
        repo = make_fixture_repo(os.path.join(self.tmp, "clean"))
        code, out = self.run_steps(repo)
        self.assertEqual(code, 0, out)

    def test_invalid_change_fails(self):
        repo = make_fixture_repo(os.path.join(self.tmp, "broken"),
                                 delta=BAD_DELTA)
        code, out = self.run_steps(repo)
        self.assertNotEqual(code, 0, out)
        self.assertIn("Scenario", out)

    def test_custom_content_directory_is_linted(self):
        """The per-change step resolves the content directory from the
        consumer's own `.shipd-config.json`, so a change under a custom
        directory is linted rather than silently skipped."""
        repo = make_fixture_repo(os.path.join(self.tmp, "custom"),
                                 content_dir=".specs", delta=BAD_DELTA)
        write(os.path.join(repo, ".shipd-config.json"), '{"dir": ".specs"}\n')
        code, out = self.run_steps(repo)
        self.assertNotEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
