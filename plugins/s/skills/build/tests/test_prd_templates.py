#!/usr/bin/env python3
"""Drift guard for the plugin-shipped PRD templates
(``plugins/s/skills/prd/references/<tier>.md``): each tier's skeleton carries
exactly its tier's required sections from the engine registry, in registry
order, under the header shape the ``/s:prd`` interview fills in — and a PRD
filled from a skeleton lints clean (shipd-prd prd-template-files)."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
TEMPLATES = os.path.normpath(os.path.join(
    HERE, "..", "..", "prd", "references"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_common as sc  # noqa: E402
import spec_lint as sl  # noqa: E402


def template_path(tier):
    """The on-disk path of the skeleton shipped for ``tier``."""
    return os.path.join(TEMPLATES, "%s.md" % tier)


def read_template(tier):
    with open(template_path(tier), encoding="utf-8") as fh:
        return fh.read()


def headings(text):
    """The level-2 headings of ``text``, in document order."""
    return [ln.rstrip() for ln in text.splitlines()
            if ln.rstrip().startswith("## ")]


def header_value(text, key):
    """The value of the ``<key>: <value>`` line among the first five non-blank
    lines, or ``None`` when the header carries no such line."""
    prefix = "%s:" % key
    for line in [ln for ln in text.splitlines() if ln.strip()][:5]:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


class PrdTemplateSkeletonTest(unittest.TestCase):
    """Every tier ships a skeleton whose headings equal its registry tuple."""

    def test_template_exists_per_tier(self):
        for tier in sc.PRD_TEMPLATE_TIERS:
            with self.subTest(tier=tier):
                self.assertTrue(
                    os.path.isfile(template_path(tier)),
                    "tier '%s' has no template at %s"
                    % (tier, template_path(tier)))

    def test_headings_equal_the_registry(self):
        for tier in sc.PRD_TEMPLATE_TIERS:
            with self.subTest(tier=tier):
                self.assertEqual(
                    headings(read_template(tier)),
                    list(sc.PRD_TIER_SECTIONS[tier]),
                    "tier '%s' skeleton drifted from PRD_TIER_SECTIONS" % tier)

    def test_template_line_names_its_own_tier(self):
        for tier in sc.PRD_TEMPLATE_TIERS:
            with self.subTest(tier=tier):
                self.assertEqual(
                    header_value(read_template(tier), "Template"), tier)

    def test_first_line_is_a_title(self):
        for tier in sc.PRD_TEMPLATE_TIERS:
            with self.subTest(tier=tier):
                first = read_template(tier).splitlines()[0].rstrip()
                self.assertTrue(
                    first.startswith("# "),
                    "tier '%s' line 1 is '%s', expected a `# ` title"
                    % (tier, first))

    def test_status_is_draft(self):
        for tier in sc.PRD_TEMPLATE_TIERS:
            with self.subTest(tier=tier):
                self.assertEqual(
                    header_value(read_template(tier), "Status"), "draft")

    def test_no_unexpected_template_files(self):
        found = sorted(name for name in os.listdir(TEMPLATES)
                       if name.endswith(".md"))
        self.assertEqual(
            found, sorted("%s.md" % t for t in sc.PRD_TEMPLATE_TIERS))


class FilledTemplateLintsCleanTest(unittest.TestCase):
    """A PRD produced from the ``basic`` skeleton — title placeholder replaced
    with the directory slug, guidance lines replaced with prose — passes the
    engine's PRD validation.

    The workspace fixture mirrors ``PrdLintTest``: a temp workspace marker so
    ``find_workspace_root`` never escapes into the real filesystem, and an
    overridden ``$HOME`` so the real home config never leaks in."""

    SLUG = "mobile-push"

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        with open(os.path.join(self.ws, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}}, fh)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _fill(self, text):
        """Fill a skeleton the way the interview does: the ``# `` placeholder
        title becomes the PRD's slug, and each italic guidance line becomes
        authored prose."""
        filled = []
        for index, line in enumerate(text.splitlines()):
            if index == 0:
                filled.append("# %s" % self.SLUG)
            elif line.startswith("*") and line.rstrip().endswith("*"):
                filled.append("Authored prose for this section.")
            else:
                filled.append(line)
        return "\n".join(filled) + "\n"

    def test_prd_filled_from_basic_template_lints_clean(self):
        pdir = os.path.join(self.ws, ".shipd", "prds", self.SLUG)
        os.makedirs(pdir, exist_ok=True)
        with open(os.path.join(pdir, "prd.md"), "w", encoding="utf-8") as fh:
            fh.write(self._fill(read_template("basic")))
        errors = []
        sl.lint_prd(self.ws, self.SLUG, errors)
        self.assertEqual([str(e) for e in errors], [])


if __name__ == "__main__":
    unittest.main()
