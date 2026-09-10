#!/usr/bin/env python3
"""Tests for voice_digest.py — the config-gated SessionStart hook that injects
the documentation standard's voice digest into a session.

Every case runs the script as a subprocess inside a synthetic plugin root so
the fixture owns both halves of the resolution: the ``standard.md`` the script
reads relative to its own path, and the ``.shipd-config.json`` layers the
upward search walks. ``HOME`` points at the fixture too, so the developer's own
``~/.shipd-config.json`` can never colour a result.

The hook is fail-soft by contract: every case asserts exit 0, and the only
variable under test is whether anything reaches stdout.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))
sys.path.insert(0, SCRIPTS)

import voice_digest  # noqa: E402


STANDARD = """# shipd documentation standard

## Core rules

Write in the active voice.

## Documentation rules

Open every doc with a doc-type marker.

## Voice digest

- Write in the active voice; name the actor.
- Keep descriptive sentences short.
- Use the shipd glossary terms with one meaning each.
"""

DIGEST_BODY = (
    "- Write in the active voice; name the actor.\n"
    "- Keep descriptive sentences short.\n"
    "- Use the shipd glossary terms with one meaning each."
)


class VoiceDigestTestCase(unittest.TestCase):
    """Base fixture: a throwaway plugin root plus an isolated home."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="voice-digest-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.project = os.path.join(self.tmp, "project")
        os.makedirs(self.project)

    def make_root(self, standard_text=STANDARD, with_spec_common=True):
        """Build a synthetic plugin root and return the script path inside it.

        The real ``voice_digest.py`` is copied verbatim, so the test exercises
        shipped code; ``spec_common.py`` is copied alongside it (it is
        stdlib-only) so the script's layered-config import resolves the same way
        it does in the plugin.
        """
        root = os.path.join(self.tmp, "plugins", "s", "skills")
        doc_scripts = os.path.join(root, "document", "scripts")
        doc_refs = os.path.join(root, "document", "references")
        os.makedirs(doc_scripts)
        os.makedirs(doc_refs)
        shutil.copy(os.path.join(SCRIPTS, "voice_digest.py"), doc_scripts)
        if with_spec_common:
            build_scripts = os.path.join(root, "build", "scripts")
            os.makedirs(build_scripts)
            shutil.copy(
                os.path.join(BUILD_SCRIPTS, "spec_common.py"), build_scripts)
        if standard_text is not None:
            with open(os.path.join(doc_refs, "standard.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(standard_text)
        return os.path.join(doc_scripts, "voice_digest.py")

    def write_config(self, directory, data):
        with open(os.path.join(directory, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data))

    def run_hook(self, script, cwd=None):
        env = dict(os.environ)
        env["HOME"] = self.home
        env.pop("USERPROFILE", None)
        proc = subprocess.run(
            [sys.executable, script],
            cwd=cwd or self.project, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return proc.returncode, proc.stdout, proc.stderr


class TestEnabledByDefault(VoiceDigestTestCase):
    def test_no_voice_key_anywhere_prints_the_digest(self):
        script = self.make_root()
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), DIGEST_BODY)

    def test_digest_excludes_the_heading_and_other_sections(self):
        script = self.make_root()
        _rc, out, _err = self.run_hook(script)
        self.assertNotIn("## Voice digest", out)
        self.assertNotIn("Core rules", out)
        self.assertNotIn("doc-type marker", out)

    def test_voice_true_prints_the_digest(self):
        script = self.make_root()
        self.write_config(self.project, {"voice": True})
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), DIGEST_BODY)

    def test_nearest_layer_wins_over_an_outer_false(self):
        script = self.make_root()
        self.write_config(self.home, {"voice": False})
        inner = os.path.join(self.project, "repo")
        os.makedirs(inner)
        self.write_config(inner, {"voice": True})
        rc, out, _err = self.run_hook(script, cwd=inner)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), DIGEST_BODY)


class TestSilenced(VoiceDigestTestCase):
    def test_voice_false_prints_nothing(self):
        script = self.make_root()
        self.write_config(self.project, {"voice": False})
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_voice_false_in_a_parent_layer_prints_nothing(self):
        script = self.make_root()
        self.write_config(self.project, {"voice": False})
        inner = os.path.join(self.project, "repo", "deep")
        os.makedirs(inner)
        rc, out, _err = self.run_hook(script, cwd=inner)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")


class TestFailSoft(VoiceDigestTestCase):
    def test_missing_standard_prints_nothing_and_exits_zero(self):
        script = self.make_root(standard_text=None)
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_standard_without_the_section_prints_nothing(self):
        script = self.make_root(
            standard_text="# standard\n\n## Core rules\n\nWrite actively.\n")
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_empty_section_body_prints_nothing(self):
        script = self.make_root(
            standard_text="# standard\n\n## Voice digest\n\n## Next\n\nx\n")
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_malformed_config_prints_nothing_and_exits_zero(self):
        script = self.make_root()
        self.write_config(self.project, "{not json")
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_unresolvable_config_import_prints_nothing(self):
        # No spec_common alongside: the guarded import fails, and the hook
        # stays silent rather than breaking session start.
        script = self.make_root(with_spec_common=False)
        rc, out, _err = self.run_hook(script)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")


class TestDigestExtraction(unittest.TestCase):
    """Unit-level coverage of the section reader the hook prints through."""

    def test_reads_the_section_body(self):
        self.assertEqual(voice_digest.extract_digest(STANDARD), DIGEST_BODY)

    def test_stops_at_the_next_level_two_heading(self):
        text = "## Voice digest\n\nline one\n\n## After\n\nline two\n"
        self.assertEqual(voice_digest.extract_digest(text), "line one")

    def test_keeps_deeper_headings_inside_the_section(self):
        text = "## Voice digest\n\n### Detail\n\nline one\n\n## After\n"
        self.assertEqual(
            voice_digest.extract_digest(text), "### Detail\n\nline one")

    def test_absent_section_is_none(self):
        self.assertIsNone(voice_digest.extract_digest("## Core rules\n\nx\n"))

    def test_empty_section_is_none(self):
        self.assertIsNone(
            voice_digest.extract_digest("## Voice digest\n\n\n## After\n"))


class TestHooksRegistration(unittest.TestCase):
    """The plugin's hooks.json registers the hook without losing the others."""

    def setUp(self):
        path = os.path.normpath(
            os.path.join(HERE, "..", "..", "..", "hooks", "hooks.json"))
        with open(path, encoding="utf-8") as fh:
            self.hooks = json.load(fh)["hooks"]

    def test_session_start_runs_the_voice_digest(self):
        commands = [
            hook["command"]
            for entry in self.hooks.get("SessionStart", [])
            for hook in entry.get("hooks", [])
        ]
        self.assertTrue(
            any("skills/document/scripts/voice_digest.py" in cmd
                for cmd in commands),
            "SessionStart does not run voice_digest.py: %r" % (commands,))

    def test_existing_guardrail_hooks_survive(self):
        for event in ("PreToolUse", "PostToolUse"):
            commands = [
                hook["command"]
                for entry in self.hooks.get(event, [])
                for hook in entry.get("hooks", [])
            ]
            self.assertTrue(
                any("guardrails.py" in cmd for cmd in commands),
                "%s lost its guardrails hook" % event)


if __name__ == "__main__":
    unittest.main()
