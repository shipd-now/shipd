#!/usr/bin/env python3
"""Tests for the command-body render engine — ``harness_bodies.py``.

These are the *mechanics* tests: gate keeping and dropping, ``else``
branches, include resolution, marker stripping, ``{refs}`` substitution, and
the two refusals. They run against fixture templates written into a
throwaway directory rather than the shipped ``plugins/s/harness/`` tree, so
they pin the renderer's behaviour and never move when a real body's wording
is edited. That is what the module's optional ``base_dir`` argument exists
for; the shipped templates get their own integration tests alongside.

Gate names in the fixtures are real ``harness_registry.FEATURES`` members —
the renderer validates against that vocabulary, so a fixture cannot invent
one except in the template that deliberately does, to be refused.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import harness_bodies as hb  # noqa: E402
import harness_registry as hr  # noqa: E402

PREAMBLE = """Purpose: run the command.

S="$HOME/.claude/plugins/cache/shipd/s/latest/skills/build/scripts"
"""

ALPHA = """<!-- description: Alpha does the alpha thing. -->
<!-- include:preamble -->
1. Always do this.
<!-- if:subagents -->
2. Delegate the work to a worker.
<!-- else -->
2. Do the work yourself, in order.
<!-- end -->
<!-- if:file-references -->
3. Read {refs}/alpha.md for the long form.
<!-- else -->
3. No long form is available here; continue inline.
<!-- end -->
"""

BETA = """<!-- description: Beta does the beta thing. -->
1. Beta step.
"""

BAD_GATE = """<!-- description: Bad carries a gate nobody declared. -->
<!-- if:telepathy -->
1. Read the user's mind.
<!-- end -->
"""

ALPHA_REFERENCE = """# alpha, the long form

Everything the body left out.
"""


class BodiesFixtureTest(unittest.TestCase):
    """Base class: a fixture ``base_dir`` holding ``bodies/`` and
    ``references/``."""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="harness-bodies-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        bodies = os.path.join(self.base, "bodies")
        references = os.path.join(self.base, "references")
        os.makedirs(bodies)
        os.makedirs(references)
        for name, text in (("_preamble.md", PREAMBLE),
                           ("alpha.md", ALPHA),
                           ("beta.md", BETA),
                           ("bad-gate.md", BAD_GATE)):
            with open(os.path.join(bodies, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        with open(os.path.join(references, "alpha.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(ALPHA_REFERENCE)

    def render(self, command, features, refs_dir="REFS"):
        return hb.render(command, features, refs_dir=refs_dir,
                         base_dir=self.base)


class GateTest(BodiesFixtureTest):
    def test_declared_feature_keeps_its_segment(self):
        out = self.render("alpha", ("subagents",))
        self.assertIn("Delegate the work to a worker.", out)
        self.assertNotIn("Do the work yourself", out)

    def test_absent_feature_keeps_the_else_segment(self):
        out = self.render("alpha", ())
        self.assertIn("Do the work yourself, in order.", out)
        self.assertNotIn("Delegate the work", out)

    def test_each_gate_is_decided_independently(self):
        out = self.render("alpha", ("file-references",))
        self.assertIn("Do the work yourself, in order.", out)
        self.assertIn("REFS/alpha.md", out)

    def test_ungated_lines_survive_every_feature_set(self):
        for features in ((), ("subagents",), hr.FEATURES):
            self.assertIn("1. Always do this.", self.render("alpha", features))

    def test_unknown_gate_name_is_refused_by_template_and_line(self):
        with self.assertRaises(ValueError) as caught:
            self.render("bad-gate", ())
        message = str(caught.exception)
        self.assertIn("bad-gate", message)
        self.assertIn("telepathy", message)
        self.assertIn("2", message, "the error names the offending line")


class IncludeTest(BodiesFixtureTest):
    def test_preamble_include_is_resolved(self):
        out = self.render("alpha", ())
        self.assertIn('S="$HOME/.claude/plugins/cache/shipd/s/', out)
        self.assertIn("Purpose: run the command.", out)

    def test_no_marker_line_survives_rendering(self):
        for command in ("alpha", "beta"):
            for features in ((), hr.FEATURES):
                self.assertNotIn("<!--", self.render(command, features))


class RefsTest(BodiesFixtureTest):
    def test_placeholder_takes_the_refs_dir(self):
        out = self.render("alpha", ("file-references",), refs_dir="X")
        self.assertIn("3. Read X/alpha.md for the long form.", out)
        self.assertNotIn("{refs}", out)

    def test_kept_placeholder_without_refs_dir_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            hb.render("alpha", ("file-references",), refs_dir=None,
                      base_dir=self.base)
        self.assertIn("alpha", str(caught.exception))

    def test_dropped_placeholder_without_refs_dir_is_fine(self):
        out = hb.render("alpha", (), refs_dir=None, base_dir=self.base)
        self.assertIn("continue inline", out)
        self.assertNotIn("{refs}", out)


class CommandsTest(BodiesFixtureTest):
    def test_commands_are_the_template_ids_without_partials(self):
        self.assertEqual(hb.commands(base_dir=self.base),
                         ("alpha", "bad-gate", "beta"))


class ReferenceTest(BodiesFixtureTest):
    def test_reference_returns_the_fallback_text(self):
        self.assertEqual(hb.reference("alpha", base_dir=self.base),
                         ALPHA_REFERENCE)

    def test_reference_is_none_when_no_fallback_exists(self):
        self.assertIsNone(hb.reference("beta", base_dir=self.base))


class DescriptionTest(BodiesFixtureTest):
    def test_description_is_the_declared_one_liner(self):
        self.assertEqual(hb.description("beta", base_dir=self.base),
                         "Beta does the beta thing.")

    def test_render_strips_the_description_marker(self):
        self.assertEqual(self.render("beta", ()), "1. Beta step.\n")


# ---------------------------------------------------------------------------
# The shipped templates
#
# Everything above pins the *renderer* against fixtures. Everything below
# pins the *templates the plugin actually ships* — properties a body has to
# keep however its wording is edited: one body per command, only declared
# gate names, a fallback file behind every gate, and — the whole point of the
# feature vocabulary — a body that never names a capability the target
# harness does not have.
# ---------------------------------------------------------------------------

# ``plugins/s`` — HERE is ``plugins/s/skills/build/tests``.
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SKILLS_DIR = os.path.join(PLUGIN_ROOT, "skills")
BODIES_DIR = os.path.join(hb.DEFAULT_BASE_DIR, "bodies")

# The tokens a rendered body must never carry when no feature is declared:
# marker syntax, an unsubstituted placeholder, and the names of capabilities
# a bare harness does not have.
FORBIDDEN_UNGATED = ("<!--", "{refs}", "subagent", "sub-agent",
                     "AskUserQuestion")

REFS = "/tmp/harness-refs"

IF_MARKER_RE = re.compile(r"^\s*<!--\s*if:(?P<feature>[a-z0-9-]+)\s*-->\s*$")


def _template_text(command):
    path = os.path.join(BODIES_DIR, "%s.md" % command)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _gate_branches(text, feature):
    """The ``(kept, else)`` content lines of ``text``'s first ``feature``
    gate — the raw template's own wording, so the assertions below never
    hard-code a sentence a body is free to rewrite."""
    kept, otherwise, state = [], [], None
    for line in text.splitlines():
        marker = hb._MARKER_RE.match(line)
        if marker is not None:
            body = marker.group("body")
            if body == "if:%s" % feature and state is None:
                state = "if"
            elif state == "if" and body == "else":
                state = "else"
            elif state in ("if", "else") and body == "end":
                break
            continue
        if state == "if":
            kept.append(line)
        elif state == "else":
            otherwise.append(line)
    return ([ln for ln in kept if ln.strip()],
            [ln for ln in otherwise if ln.strip()])


class ShippedTemplateTest(unittest.TestCase):
    """Structural properties of ``plugins/s/harness/`` itself."""

    def test_every_command_has_exactly_one_body_template(self):
        skills = sorted(name for name in os.listdir(SKILLS_DIR)
                        if os.path.isdir(os.path.join(SKILLS_DIR, name)))
        self.assertEqual(list(hb.commands()), skills)

    def test_every_gate_name_is_in_the_feature_vocabulary(self):
        for command in hb.commands():
            for lineno, line in enumerate(
                    _template_text(command).splitlines(), start=1):
                gate = IF_MARKER_RE.match(line)
                if gate is None:
                    continue
                self.assertIn(gate.group("feature"), hr.FEATURES,
                              "%s.md:%d gates on a feature nobody declares"
                              % (command, lineno))

    def test_every_gated_template_carries_a_fallback_reference(self):
        for command in hb.commands():
            if IF_MARKER_RE.search(_template_text(command)) is None:
                continue
            self.assertIsNotNone(
                hb.reference(command),
                "%s gates content but ships no references/%s.md"
                % (command, command))

    def test_every_template_declares_a_description(self):
        for command in hb.commands():
            for line in _template_text(command).splitlines():
                marker = hb._MARKER_RE.match(line)
                if marker is None:
                    continue
                declared = hb._DESCRIPTION_RE.match(marker.group("body"))
                self.assertIsNotNone(
                    declared,
                    "%s.md's first marker is %r, not a description"
                    % (command, marker.group("body")))
                break
            else:
                self.fail("%s.md carries no marker at all" % command)
            self.assertTrue(hb.description(command),
                            "%s.md declares an empty description" % command)


class ShippedRenderTest(unittest.TestCase):
    """What the shipped templates render to, at both ends of the feature
    vocabulary."""

    def test_a_bare_harness_is_never_told_about_gated_capabilities(self):
        for command in hb.commands():
            out = hb.render(command, (), refs_dir=REFS)
            for token in FORBIDDEN_UNGATED:
                self.assertNotIn(
                    token, out,
                    "%s rendered for a bare harness carries %r"
                    % (command, token))

    def test_every_body_stays_lean_at_the_full_vocabulary(self):
        for command in hb.commands():
            lines = len(hb.render(command, hr.FEATURES,
                                  refs_dir=REFS).splitlines())
            self.assertLess(lines, 120,
                            "%s renders %d lines" % (command, lines))

    def test_a_fallback_pointer_appears_only_when_files_can_be_read(self):
        pointer = "%s/%%s.md" % REFS
        for command in hb.commands():
            if hb.reference(command) is None:
                continue
            with_files = hb.render(command, ("file-references",),
                                   refs_dir=REFS)
            self.assertIn(pointer % command, with_files,
                          "%s never points at its reference file" % command)
            without = hb.render(command, (), refs_dir=REFS)
            self.assertNotIn(REFS, without,
                             "%s points at a file a bare harness cannot read"
                             % command)

    def test_the_build_body_delegates_only_where_workers_exist(self):
        kept, otherwise = _gate_branches(_template_text("build"), "subagents")
        self.assertTrue(kept and otherwise,
                        "build's subagents gate needs both branches")
        delegated = hb.render("build", ("subagents",), refs_dir=REFS)
        alone = hb.render("build", (), refs_dir=REFS)
        for line in kept:
            self.assertIn(line, delegated)
            self.assertNotIn(line, alone)
        for line in otherwise:
            self.assertIn(line, alone)
            self.assertNotIn(line, delegated)

    def test_the_plan_body_drives_the_engine_through_the_scripts_variable(self):
        for features in ((), hr.FEATURES):
            out = hb.render("plan", features, refs_dir=REFS)
            for script in ("spec_emit.py", "spec_gate.py"):
                self.assertIn('"$S/%s"' % script, out,
                              "plan never runs %s via the scripts variable"
                              % script)

    def test_the_plan_body_is_distilled_not_pasted(self):
        with open(os.path.join(SKILLS_DIR, "plan", "SKILL.md"),
                  encoding="utf-8") as handle:
            skill = handle.read().splitlines()
        runs = {tuple(skill[i:i + 10]) for i in range(len(skill) - 9)}
        for features in ((), hr.FEATURES):
            body = hb.render("plan", features, refs_dir=REFS).splitlines()
            shared = [body[i:i + 10] for i in range(len(body) - 9)
                      if tuple(body[i:i + 10]) in runs]
            self.assertEqual(
                [], shared,
                "plan's body repeats 10 consecutive lines of its SKILL.md")


class PreambleSnippetTest(unittest.TestCase):
    """The shared preamble's snapshot resolution, run as a real shell would
    run it."""

    def snippet(self):
        with open(os.path.join(BODIES_DIR, "_preamble.md"),
                  encoding="utf-8") as handle:
            lines = [ln for ln in handle.read().splitlines()
                     if ln.startswith("S=")]
        self.assertEqual(1, len(lines),
                         "the preamble declares exactly one scripts variable")
        return lines[0]

    def test_the_snippet_resolves_the_newest_snapshot(self):
        home = tempfile.mkdtemp(prefix="harness-home-")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        cache = os.path.join(home, ".claude", "plugins", "cache", "shipd", "s")
        for version in ("0.6.9", "0.6.10"):
            os.makedirs(os.path.join(cache, version, "skills", "build",
                                     "scripts"))
        env = dict(os.environ, HOME=home)
        resolved = subprocess.check_output(
            ["sh", "-c", '%s\nprintf %%s "$S"' % self.snippet()],
            env=env).decode("utf-8")
        self.assertEqual(
            os.path.join(cache, "0.6.10", "skills", "build", "scripts"),
            resolved,
            "dotted versions must sort numerically, not lexically")


if __name__ == "__main__":
    unittest.main()
