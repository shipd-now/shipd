"""Tests for tools/port.py, the automikk -> shipd port tool."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PORT_PY = Path(__file__).resolve().parent.parent / "port.py"


def _run_git(repo_path, *args):
    subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def run_port(*args):
    """Invoke tools/port.py as a subprocess and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(PORT_PY), *args],
        capture_output=True,
        text=True,
    )


class PortToolTestCase(unittest.TestCase):
    """Base test case providing a synthetic source-repo builder."""

    def make_source_repo(self, files):
        """Build a synthetic source git repo under a TemporaryDirectory.

        ``files`` maps a relative path (str) to its content (str or bytes).
        The repo is initialized, the files are written, and everything is
        added and committed. Returns the repo's path as a string. The
        TemporaryDirectory is cleaned up automatically via addCleanup.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo_path = Path(tmp.name)

        _run_git(repo_path, "init", "-q")
        _run_git(repo_path, "config", "user.email", "port-tool-tests@example.com")
        _run_git(repo_path, "config", "user.name", "Port Tool Tests")

        for rel_path, content in files.items():
            full_path = repo_path / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                full_path.write_bytes(content)
            else:
                full_path.write_text(content)

        _run_git(repo_path, "add", "-A")
        _run_git(repo_path, "commit", "-q", "-m", "initial")

        return str(repo_path)

    def make_dest_dir(self):
        """Return the path of a fresh, empty destination TemporaryDirectory."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name


class PlanAndErrorsTests(PortToolTestCase):
    def test_plan_writes_nothing_to_destination(self):
        source = self.make_source_repo({"README.md": "hello\n"})
        dest = self.make_dest_dir()

        result = run_port("plan", "--source", source, "--ref", "HEAD", "--dest", dest)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(Path(dest).iterdir()), [])

    def test_non_git_source_exits_one_with_error(self):
        not_a_repo = tempfile.TemporaryDirectory()
        self.addCleanup(not_a_repo.cleanup)
        dest = self.make_dest_dir()

        result = run_port(
            "plan",
            "--source", not_a_repo.name,
            "--ref", "HEAD",
            "--dest", dest,
        )

        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.startswith("Error: "), result.stderr)

    def test_source_that_is_a_subdirectory_of_a_repo_exits_one(self):
        # `rev-parse --is-inside-work-tree` succeeds for any directory inside
        # a work tree, so a `--source` off by one segment must be rejected
        # explicitly rather than silently porting an empty tree.
        source = self.make_source_repo({"pkg/notes.txt": "hello\n"})
        dest = self.make_dest_dir()

        result = run_port(
            "plan",
            "--source", str(Path(source) / "pkg"),
            "--ref", "HEAD",
            "--dest", dest,
        )

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertTrue(result.stderr.startswith("Error: "), result.stderr)

    def test_verify_on_missing_destination_exits_one(self):
        # A mistyped `--dest` must be an error, never a silent clean scan.
        dest = self.make_dest_dir()

        result = run_port("verify", "--dest", str(Path(dest) / "nope"))

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertTrue(result.stderr.startswith("Error: "), result.stderr)


class SourceReadingTests(PortToolTestCase):
    def test_dirty_working_tree_does_not_affect_port(self):
        source = self.make_source_repo({"notes.txt": "committed\n"})
        # Modify the tracked file without committing.
        (Path(source) / "notes.txt").write_text("modified\n")
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((Path(dest) / "notes.txt").read_text(), "committed\n")

    def test_untracked_source_file_is_not_ported(self):
        source = self.make_source_repo({"notes.txt": "committed\n"})
        # Add a file without `git add`-ing or committing it.
        (Path(source) / "untracked.txt").write_text("untracked\n")
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((Path(dest) / "untracked.txt").exists())

    def test_staged_addition_is_not_ported(self):
        # A `git add`-ed but uncommitted file is in the index and not in
        # HEAD. Enumerating the index would list it and then fail to read it.
        source = self.make_source_repo({"notes.txt": "committed\n"})
        (Path(source) / "staged.txt").write_text("staged\n")
        _run_git(source, "add", "staged.txt")
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((Path(dest) / "staged.txt").exists())
        self.assertEqual((Path(dest) / "notes.txt").read_text(), "committed\n")

    def test_port_at_an_earlier_ref_uses_that_ref_tree(self):
        source = self.make_source_repo({"first.txt": "one\n"})
        first_ref = subprocess.run(
            ["git", "-C", source, "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        (Path(source) / "second.txt").write_text("two\n")
        _run_git(source, "add", "-A")
        _run_git(source, "commit", "-q", "-m", "second")
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", first_ref, "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((Path(dest) / "first.txt").read_text(), "one\n")
        self.assertFalse((Path(dest) / "second.txt").exists())

    def test_failed_run_leaves_destination_untouched(self):
        # Every blob is read before the first write, so an aborted run does
        # not leave a half-ported destination behind. A bad ref is the
        # reachable trigger; the guarantee also covers a read that fails
        # after enumeration succeeded, which is not constructible here.
        source = self.make_source_repo({"notes.txt": "committed\n"})
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "no-such-ref", "--dest", dest,
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(list(Path(dest).iterdir()), [])


class FileModeTests(PortToolTestCase):
    def test_executable_source_file_ports_executable(self):
        source = self.make_source_repo(
            {
                "plugins/am/skills/build/scripts/worktree.sh": "#!/bin/sh\n",
                "plugins/am/skills/build/scripts/spec_lint.py": "print(1)\n",
            }
        )
        _run_git(
            source,
            "update-index", "--chmod=+x",
            "plugins/am/skills/build/scripts/worktree.sh",
        )
        _run_git(source, "commit", "-q", "-m", "make worktree.sh executable")
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        ported = Path(dest) / "plugins/s/skills/build/scripts/worktree.sh"
        self.assertTrue(ported.stat().st_mode & 0o111, "exec bit was dropped")
        plain = Path(dest) / "plugins/s/skills/build/scripts/spec_lint.py"
        self.assertFalse(plain.stat().st_mode & 0o111, "exec bit was invented")


class CapabilityEnumerationTests(PortToolTestCase):
    def test_enumerated_slug_is_renamed_in_content_and_on_disk(self):
        source = self.make_source_repo(
            {
                ".am/verified/am-plan/spec.md": "spec for am-plan\n",
                "notes.md": "See am-plan and am-widget for details.\n",
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        # Once the full path map (rule 12, `.am/` -> `.shipd/`) is in place
        # this also carries the top-level content-directory rename; see the
        # `port-capability-enum` requirement's "Capability directories are
        # renamed on disk" scenario in spec.md.
        spec_path = Path(dest) / ".shipd" / "verified" / "shipd-plan" / "spec.md"
        self.assertTrue(
            spec_path.exists(), "capability directory was not renamed on disk"
        )
        self.assertEqual(spec_path.read_text(), "spec for shipd-plan\n")

        notes_content = (Path(dest) / "notes.md").read_text()
        self.assertIn("shipd-plan", notes_content)
        self.assertIn("am-widget", notes_content)
        self.assertNotIn("am-plan", notes_content)

    def test_non_enumerated_slug_is_left_alone(self):
        source = self.make_source_repo(
            {
                ".am/verified/am-plan/spec.md": "spec for am-plan\n",
                "docs/am-widget/notes.txt": "am-widget notes\n",
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        widget_path = Path(dest) / "docs" / "am-widget" / "notes.txt"
        self.assertTrue(
            widget_path.exists(), "non-enumerated slug path should be untouched"
        )
        self.assertEqual(widget_path.read_text(), "am-widget notes\n")


class TokenMapTests(PortToolTestCase):
    def test_token_map_rewrites_anchored_forms(self):
        source = self.make_source_repo(
            {
                # Enumerates "am-config" as a capability slug, so the
                # ordering between rule 2 (.am-config.json) and rule 10
                # (capability slugs) is exercised for real.
                ".am/verified/am-config/spec.md": "the am-config capability\n",
                "notes.md": (
                    "config file: .am-config.json\n"
                    "ordinary words: ambiguous stream param\n"
                    "skill refs: /am:plan and am:oracle\n"
                    "plugin path: plugins/am/x.py\n"
                    "email token: am@automikk\n"
                    "memory path: ~/.am-memory\n"
                ),
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        content = (Path(dest) / "notes.md").read_text()

        # .am-config.json becomes .shipd-config.json with no doubled or
        # partial rewrite from the capability rule.
        self.assertIn(".shipd-config.json", content)
        self.assertNotIn(".shipd-shipd-config.json", content)
        self.assertNotIn(".am-shipd-config.json", content)
        self.assertNotIn(".am-config.json", content)

        # Ordinary English containing "am" is untouched.
        self.assertIn("ambiguous", content)
        self.assertIn("stream", content)
        self.assertIn("param", content)

        # Anchored forms are rewritten.
        self.assertIn("/s:plan", content)
        self.assertIn("s:oracle", content)
        self.assertIn("plugins/s/x.py", content)
        self.assertIn("s@shipd", content)
        self.assertIn("~/.shipd-memory", content)


class QuotedSegmentTests(PortToolTestCase):
    def test_bare_quoted_content_directory_segment_is_rewritten(self):
        source = self.make_source_repo(
            {
                "engine.py": (
                    'DEFAULT_DIR = ".am"\n'
                    'PATH = os.path.join(root, ".am", "planned", slug)\n'
                ),
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        content = (Path(dest) / "engine.py").read_text()
        self.assertIn('DEFAULT_DIR = ".shipd"', content)
        self.assertIn('os.path.join(root, ".shipd", "planned", slug)', content)

    def test_quoted_segment_rule_does_not_match_longer_strings(self):
        source = self.make_source_repo(
            {
                "engine.py": (
                    'CONFIG = ".am-config.json"\n'
                    'WORD = ".among"\n'
                ),
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        content = (Path(dest) / "engine.py").read_text()
        # The quoted word ".among" is untouched by the quoted-segment rule.
        self.assertIn('".among"', content)
        # Whatever rule 2 does to ".am-config.json" elsewhere, the
        # quoted-segment rule must not have produced a corrupted, doubled
        # rewrite of it.
        self.assertNotIn('.shipd-shipd-config.json', content)
        self.assertNotIn('.am-shipd-config.json', content)


class ApplyScopeTests(PortToolTestCase):
    def test_pre_existing_destination_file_survives(self):
        source = self.make_source_repo({"README.md": "hello\n"})
        dest = self.make_dest_dir()
        license_path = Path(dest) / "LICENSE"
        license_path.write_text("MIT\n")

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(license_path.read_text(), "MIT\n")

    def test_dropped_trees_produce_no_destination_counterpart(self):
        source = self.make_source_repo(
            {
                "openspec/specs/x/spec.md": "an openspec file\n",
                ".automikk/state.json": "{}\n",
                "README.md": "hello\n",
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((Path(dest) / "openspec").exists())
        self.assertFalse((Path(dest) / ".automikk").exists())
        self.assertTrue((Path(dest) / "README.md").exists())


class IncludeFilterTests(PortToolTestCase):
    def _make_layered_source(self):
        return self.make_source_repo(
            {
                "plugins/am/x.py": "hello\n",
                "requirements.txt": "textual\n",
                ".am/verified/am-plan/spec.md": "spec\n",
                "README.md": "readme\n",
            }
        )

    def test_include_restricts_what_is_written(self):
        source = self._make_layered_source()
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
            "--include", "plugins/am/",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(dest) / "plugins" / "s" / "x.py").exists())
        self.assertFalse((Path(dest) / ".shipd" / "verified").exists())

    def test_repeated_include_unions_prefixes(self):
        source = self._make_layered_source()
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
            "--include", "plugins/am/",
            "--include", "requirements.txt",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(dest) / "plugins" / "s" / "x.py").exists())
        self.assertTrue((Path(dest) / "requirements.txt").exists())
        self.assertFalse((Path(dest) / ".shipd").exists())
        self.assertFalse((Path(dest) / "README.md").exists())

    def test_include_matches_whole_path_segments_only(self):
        source = self.make_source_repo(
            {
                "plugins/am/x.py": "hello\n",
                "plugins/amx/y.py": "sibling\n",
            }
        )
        dest = self.make_dest_dir()

        # No trailing slash: must still not pull in the `amx` sibling.
        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
            "--include", "plugins/am",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(dest) / "plugins" / "s" / "x.py").exists())
        self.assertFalse((Path(dest) / "plugins" / "amx").exists())

    def test_no_include_ports_everything_non_excluded(self):
        source = self.make_source_repo(
            {
                "plugins/am/x.py": "hello\n",
                ".am/verified/am-plan/spec.md": "spec\n",
                "openspec/specs/x/spec.md": "an openspec file\n",
                "README.md": "readme\n",
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(dest) / "plugins" / "s" / "x.py").exists())
        self.assertTrue(
            (Path(dest) / ".shipd" / "verified" / "shipd-plan" / "spec.md").exists()
        )
        self.assertTrue((Path(dest) / "README.md").exists())
        self.assertFalse((Path(dest) / "openspec").exists())


class ResidualScanTests(PortToolTestCase):
    def test_unmapped_anchored_form_is_reported_and_exits_two(self):
        source = self.make_source_repo(
            {"notes.md": "design docs live at ~/.am-designs/\n"}
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        report = result.stdout + result.stderr
        self.assertIn("notes.md:1:", report)
        self.assertIn("~/.am-designs/", report)

    def test_fully_mapped_tree_exits_zero(self):
        source = self.make_source_repo(
            {
                ".am/verified/am-plan/spec.md": "spec for am-plan\n",
                "notes.md": (
                    "config file: .am-config.json\n"
                    "ordinary words: ambiguous stream param\n"
                    "skill refs: /am:plan and am:oracle\n"
                    "plugin path: plugins/am/x.py\n"
                    "email token: am@automikk\n"
                    "memory path: ~/.am-memory\n"
                ),
            }
        )
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_non_utf8_file_is_copied_byte_identically_with_no_finding(self):
        binary_content = b"\xff\xfe~/.am-designs/\x00\x01binary-goop"
        source = self.make_source_repo({"binary.dat": binary_content})
        dest = self.make_dest_dir()

        result = run_port(
            "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (Path(dest) / "binary.dat").read_bytes(), binary_content
        )


class EncodingTests(PortToolTestCase):
    def test_non_ascii_content_ports_as_utf8_under_a_c_locale(self):
        # Reads decode UTF-8 explicitly; writes must too, or a non-UTF-8
        # ambient locale corrupts every non-ASCII file the port touches.
        source = self.make_source_repo({"notes.md": "café automikk\n"})
        dest = self.make_dest_dir()

        env = dict(os.environ)
        env.update({"LC_ALL": "C", "LANG": "C"})
        env.pop("PYTHONUTF8", None)
        env.pop("PYTHONIOENCODING", None)
        result = subprocess.run(
            [
                sys.executable, "-X", "utf8=0", str(PORT_PY),
                "apply", "--source", source, "--ref", "HEAD", "--dest", dest,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (Path(dest) / "notes.md").read_bytes(),
            "café shipd\n".encode("utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
