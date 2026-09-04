#!/usr/bin/env python3
"""Tests for render.py — the shared mermaid-fence substitution and its
non-interactive ``output`` verb.

Stdlib only, and deliberately so: ``render.py``'s module scope may import
nothing beyond the standard library and the vendored ``beautiful_mermaid``, so
this suite passes in an environment with neither ``textual`` nor ``rich``
installed. The importability scenario proves that rather than assuming it — it
runs a subprocess whose meta path finder makes both packages unimportable, so
the verdict is the same on a machine that happens to have them.

The interactive ``screen`` verb is not exercised here; it needs ``textual``, so
its tests live in ``tests_textual/test_render_screen.py``. The ``output``
verb's *styled* path is guarded the same way: without ``rich`` it would send
``render.py``'s script entry through ``tui_bootstrap``, which provisions a venv
over the network, so only the ``--plain`` path — which never imports rich — is
exercised unconditionally.
"""

import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import render  # noqa: E402

RENDER = os.path.join(SCRIPTS, "render.py")

# A flowchart the vendored renderer supports. Spaced arrows are load-bearing:
# ``A-->B`` parses as a single label box, not an edge.
GRAPH = "graph LR\n  A[Plan] --> B[Build]\n"

# A diagram type the renderer rejects (it raises on the header), which is the
# fallback path's fixture.
PIE = 'pie title Pets\n    "Dogs" : 386\n    "Cats" : 85\n'

# The Unicode box-drawing glyphs the default charset draws with.
BOX_DRAWING = "─│┌┐└┘"


def _imports_rich():
    """True when ``rich`` is importable by the interpreter the ``output`` verb
    runs on — the styled path's precondition. Both interpreters are probed for
    the same reason ``test_shipd_cli.py`` probes both: the suite runs on
    ``sys.executable``, the shebang resolves ``python3``."""
    for python in (sys.executable, "python3"):
        try:
            if subprocess.run([python, "-c", "import rich"],
                              capture_output=True).returncode != 0:
                return False
        except OSError:
            return False
    return True


HAS_RICH = _imports_rich()


def fenced(body, info="mermaid"):
    return "```%s\n%s```\n" % (info, body)


def document(body, info="mermaid"):
    """A fence wrapped in prose, so a test can assert the prose survived."""
    return "# Title\n\nBefore.\n\n%s\nAfter.\n" % fenced(body, info)


class SubstituteMermaidFencesTest(unittest.TestCase):
    def test_supported_fence_becomes_a_rendered_diagram(self):
        out = render.substitute_mermaid_fences(document(GRAPH))
        self.assertNotIn("```mermaid", out)
        self.assertIn("```text\n", out)
        self.assertTrue(any(ch in out for ch in BOX_DRAWING), out)
        self.assertIn("Plan", out)
        self.assertIn("Build", out)
        # The prose around the fence is byte-identical.
        self.assertTrue(out.startswith("# Title\n\nBefore.\n\n"), out)
        self.assertTrue(out.endswith("\nAfter.\n"), out)

    def test_unsupported_fence_is_left_untouched(self):
        text = document(PIE)
        self.assertEqual(render.substitute_mermaid_fences(text), text)

    def test_non_mermaid_fence_is_untouched(self):
        text = document("print('hi')\n", info="python")
        self.assertEqual(render.substitute_mermaid_fences(text), text)

    def test_ascii_charset_is_seven_bit(self):
        out = render.substitute_mermaid_fences(document(GRAPH), use_ascii=True)
        self.assertIn("```text\n", out)
        self.assertTrue(all(ord(ch) < 128 for ch in out),
                        sorted({ch for ch in out if ord(ch) > 127}))
        self.assertIn("+", out)
        self.assertIn("|", out)

    def test_indented_fence_is_substituted(self):
        text = "- item:\n\n  ```mermaid\n  %s  ```\n" % GRAPH.replace(
            "\n", "\n  ").rstrip(" ")
        out = render.substitute_mermaid_fences(text)
        self.assertIn("```text", out)
        self.assertNotIn("```mermaid", out)

    def test_text_without_any_fence_is_byte_identical(self):
        text = "# Title\n\nJust prose, no fences at all.\n"
        self.assertEqual(render.substitute_mermaid_fences(text), text)

    def test_importable_without_textual_or_rich(self):
        """render.py must import where neither display package exists."""
        probe = (
            "import sys\n"
            "class Block:\n"
            "    def find_module(self, name, path=None):\n"
            "        return self.find_spec(name, path)\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        root = name.split('.')[0]\n"
            "        if root in ('textual', 'rich'):\n"
            "            raise ImportError('blocked: ' + name)\n"
            "        return None\n"
            "sys.meta_path.insert(0, Block())\n"
            "sys.path.insert(0, %r)\n"
            "import render\n"
            "assert '```text' in render.substitute_mermaid_fences(%r)\n"
            "print('ok')\n" % (SCRIPTS, fenced(GRAPH)))
        proc = subprocess.run([sys.executable, "-c", probe],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "ok")


class OutputModeTest(unittest.TestCase):
    """The ``output`` verb, driven as a subprocess so its argument parsing,
    stdin handling, and exit codes are exercised exactly as a caller sees
    them."""

    def run_output(self, *args, stdin=None):
        return subprocess.run([sys.executable, RENDER, "output", *args],
                              input=stdin, capture_output=True, text=True)

    def write(self, text):
        fd, path = tempfile.mkstemp(prefix="shipd-render-", suffix=".md")
        self.addCleanup(os.unlink, path)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_plain_stdin_prints_the_substituted_markdown(self):
        text = document(GRAPH)
        proc = self.run_output("--plain", "-", stdin=text)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, render.substitute_mermaid_fences(text))
        self.assertIn("```text", proc.stdout)
        self.assertNotIn("```mermaid", proc.stdout)
        # Nothing but the fence is reformatted: the prose is verbatim.
        self.assertIn("# Title\n\nBefore.\n", proc.stdout)

    def test_styled_stdin_without_rich_degrades_to_plain(self):
        # A stdin document must never reach the provisioning bootstrap: its
        # re-exec would re-read the already-drained pipe and style an empty
        # document. With rich unimportable, the styled path on `-` degrades to
        # the plain rendering — document intact, one warning, exit 0.
        blocker = tempfile.mkdtemp(prefix="shipd-render-blocker-")
        self.addCleanup(lambda: __import__("shutil").rmtree(blocker, True))
        with open(os.path.join(blocker, "sitecustomize.py"), "w",
                  encoding="utf-8") as fh:
            fh.write(
                "import sys\n"
                "class Block:\n"
                "    def find_module(self, name, path=None):\n"
                "        base = name.split('.')[0]\n"
                "        return self if base in ('rich', 'textual') else None\n"
                "    def load_module(self, name):\n"
                "        raise ImportError(name + ' is blocked')\n"
                "sys.meta_path.insert(0, Block())\n")
        env = dict(os.environ, PYTHONPATH=blocker)
        text = document(GRAPH)
        proc = subprocess.run([sys.executable, RENDER, "output", "-"],
                              input=text, capture_output=True, text=True,
                              env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, render.substitute_mermaid_fences(text))
        self.assertIn("styled renderer", proc.stderr)

    def test_plain_reads_a_file_argument(self):
        path = self.write(document(GRAPH))
        proc = self.run_output("--plain", path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("```text", proc.stdout)
        self.assertTrue(any(ch in proc.stdout for ch in BOX_DRAWING))

    def test_plain_ascii_is_seven_bit(self):
        proc = self.run_output("--plain", "--ascii", "-", stdin=fenced(GRAPH))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("```text", proc.stdout)
        self.assertTrue(all(ord(ch) < 128 for ch in proc.stdout),
                        sorted({ch for ch in proc.stdout if ord(ch) > 127}))

    def test_missing_file_is_an_error(self):
        proc = self.run_output("--plain", "/no/such/file.md")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Error:", proc.stderr)
        self.assertIn("/no/such/file.md", proc.stderr)
        self.assertEqual(proc.stdout, "")

    @unittest.skipUnless(HAS_RICH, "the styled path needs rich; without it the "
                                   "script entry provisions a venv")
    def test_missing_file_is_an_error_on_the_styled_path_too(self):
        # The read happens before any provisioning, so the styled default
        # reports the same error rather than setting up a display stack for a
        # document it cannot read.
        proc = self.run_output("/no/such/file.md")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Error:", proc.stderr)
        self.assertEqual(proc.stdout, "")

    @unittest.skipUnless(HAS_RICH, "the styled path needs rich; without it the "
                                   "script entry provisions a venv")
    def test_styled_output_formats_the_prose(self):
        path = self.write(document(GRAPH))
        proc = self.run_output(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # rich renders the heading as styled text, so the raw `#` marker is
        # gone, while the diagram survives inside its code block.
        self.assertNotIn("# Title", proc.stdout)
        self.assertIn("Title", proc.stdout)
        self.assertIn("Before.", proc.stdout)
        self.assertTrue(any(ch in proc.stdout for ch in BOX_DRAWING),
                        proc.stdout)


if __name__ == "__main__":
    unittest.main()
