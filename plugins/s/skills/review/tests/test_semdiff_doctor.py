#!/usr/bin/env python3
"""Unit tests for `semdiff doctor` — dependency reporting exit codes and the
installer's pure helpers. No `--fix` is ever passed, so no test touches the
network."""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "semdiff.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import semdiff  # noqa: E402


def _bindir(base, name, tools):
    d = os.path.join(base, name)
    os.makedirs(d, exist_ok=True)
    for tool in tools:
        src = shutil.which(tool)
        if src:
            link = os.path.join(d, tool)
            if not os.path.exists(link):
                os.symlink(src, link)
    return d


def run_doctor(path_dir, home):
    env = {"PATH": path_dir, "HOME": home}
    return subprocess.run([sys.executable, SCRIPT, "doctor"],
                          capture_output=True, text=True, env=env)


class DoctorExitCodeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-doctor-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_git_present_difft_missing_exits_nonzero(self):
        # git available, difft absent (only git symlinked into the bindir):
        # difft is a required tool, so its absence fails the preflight.
        bindir = _bindir(self.tmp, "gitonly", ["git"])
        r = run_doctor(bindir, self.tmp)
        self.assertNotEqual(r.returncode, 0)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("difft", out)
        self.assertIn("required", out)

    def test_git_missing_exits_nonzero(self):
        # empty bindir: git cannot be found → required tool missing.
        bindir = _bindir(self.tmp, "empty", [])
        r = run_doctor(bindir, self.tmp)
        self.assertNotEqual(r.returncode, 0)


class DifftTargetTest(unittest.TestCase):
    def _target(self, system, machine):
        with mock.patch.object(semdiff.platform, "system",
                               return_value=system), \
             mock.patch.object(semdiff.platform, "machine",
                               return_value=machine):
            return semdiff._difft_target()

    def test_darwin_arm64(self):
        self.assertEqual(self._target("Darwin", "arm64"), "aarch64-apple-darwin")

    def test_darwin_x86_64(self):
        self.assertEqual(self._target("Darwin", "x86_64"), "x86_64-apple-darwin")

    def test_linux_aarch64(self):
        self.assertEqual(self._target("Linux", "aarch64"),
                         "aarch64-unknown-linux-gnu")

    def test_linux_x86_64(self):
        self.assertEqual(self._target("Linux", "x86_64"),
                         "x86_64-unknown-linux-gnu")

    def test_unsupported_os_is_none(self):
        self.assertIsNone(self._target("Windows", "x86_64"))

    def test_unsupported_arch_is_none(self):
        self.assertIsNone(self._target("Linux", "sparc64"))


class InstallDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-installdir-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_prefers_plugin_root_bin(self):
        root = os.path.join(self.tmp, "plugin")
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": root}):
            self.assertEqual(semdiff._install_dir(),
                             os.path.join(root, "bin"))

    def test_falls_back_to_local_bin(self):
        env = dict(os.environ)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["HOME"] = self.tmp
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                semdiff._install_dir(),
                os.path.join(self.tmp, ".local", "bin"))


class ReleaseUrlTest(unittest.TestCase):
    """The release-binary installer's download URL names a pinned version,
    never the unversioned ``releases/latest/download/`` asset name difftastic
    stopped publishing after 0.65.0."""

    def test_url_names_a_pinned_version_not_latest(self):
        captured = {}

        def fake_urlretrieve(url, filename):
            captured["url"] = url
            raise OSError("network access is not permitted in this test")

        with mock.patch.object(semdiff, "have", return_value=False), \
             mock.patch.object(semdiff, "_difft_target",
                               return_value="x86_64-unknown-linux-gnu"), \
             mock.patch.object(semdiff.urllib.request, "urlretrieve",
                               side_effect=fake_urlretrieve), \
             contextlib.redirect_stderr(io.StringIO()):
            try:
                semdiff.install_difft()
            except OSError:
                pass

        self.assertIn("url", captured, "install_difft never attempted a download")
        self.assertNotIn("releases/latest/download/", captured["url"],
                          "the download URL still names the unversioned asset")
        self.assertIn(semdiff.DIFFT_VERSION, captured["url"],
                      "the download URL does not name the pinned version")


class ReleaseArchiveExtractionTest(unittest.TestCase):
    """The release-binary tier of ``install_difft``. The member is selected by
    name, so the archive decides what lands on PATH: only a regular file may
    be extracted, never a symlink or any other member type wearing the name
    ``difft``.

    The tiers above it and the download itself are stubbed, so no network
    access occurs and the archive under test is a local one."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-release-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.dest = os.path.join(self.tmp, "bin")
        os.makedirs(self.dest)

    def _archive(self, symlink):
        """A release tarball whose only ``difft`` member is a symlink or a
        regular file."""
        stage = os.path.join(self.tmp, "stage")
        os.makedirs(stage, exist_ok=True)
        payload = os.path.join(stage, "difft")
        if os.path.lexists(payload):
            os.remove(payload)
        if symlink:
            # A *relative* link: tarfile's own extraction filter rejects a link
            # to an absolute path, so only this form reaches the name-based
            # member selection the guard has to cover.
            os.symlink("payload", payload)
        else:
            with open(payload, "w") as fh:
                fh.write("#!/bin/sh\necho difft\n")
        archive = os.path.join(self.tmp, "difft-release.tar.gz")
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(payload, arcname="difft-x86_64-unknown-linux-gnu/difft")
        return archive

    def _install(self, archive):
        """Run the installer against ``archive``; return (result, stderr)."""
        def fake_urlretrieve(url, filename):
            shutil.copyfile(archive, filename)
            return filename, None

        err = io.StringIO()
        with mock.patch.object(semdiff, "have", return_value=False), \
             mock.patch.object(semdiff, "_difft_target",
                               return_value="x86_64-unknown-linux-gnu"), \
             mock.patch.object(semdiff, "_install_dir",
                               return_value=self.dest), \
             mock.patch.object(semdiff.urllib.request, "urlretrieve",
                               side_effect=fake_urlretrieve), \
             contextlib.redirect_stderr(err):
            result = semdiff.install_difft()
        return result, err.getvalue()

    def test_a_symlink_member_is_refused_and_nothing_is_extracted(self):
        result, err = self._install(self._archive(symlink=True))
        self.assertFalse(result, "a symlink member was accepted as difft")
        self.assertEqual(os.listdir(self.dest), [],
                         "the refused archive still wrote into the install dir")
        self.assertIn("regular file", err,
                      "the failure does not name the non-regular member")
        self.assertIn("difft-x86_64-unknown-linux-gnu/difft", err,
                      "the failure does not name the offending member")

    def test_a_regular_file_member_is_extracted(self):
        result, err = self._install(self._archive(symlink=False))
        self.assertTrue(result, err)
        binp = os.path.join(self.dest, "difft")
        self.assertTrue(os.path.isfile(binp) and not os.path.islink(binp), err)
        with open(binp) as fh:
            self.assertIn("echo difft", fh.read())


class BaseFreshnessProbeTest(unittest.TestCase):
    """`semdiff doctor`'s base-freshness line: report-only, reads only
    already-fetched refs with no network (no `--fix` is ever passed here),
    and never changes doctor's exit code — the exit code stays tied solely
    to required-tool presence."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-doctor-base-")
        self.bindir = _bindir(self.tmp, "bin", ["git"])
        # A stub `difft` so the required-tool check passes without a real
        # difftastic binary — doctor only checks PATH presence, not function.
        stub = os.path.join(self.bindir, "difft")
        with open(stub, "w") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(stub, 0o755)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, repo):
        env = {"PATH": self.bindir, "HOME": self.tmp}
        return subprocess.run([sys.executable, SCRIPT, "doctor"], cwd=repo,
                              capture_output=True, text=True, env=env)

    def _git(self, repo, *args):
        return subprocess.run(["git", "-C", repo, *args],
                              capture_output=True, text=True, check=True)

    def _write(self, repo, rel, text):
        with open(os.path.join(repo, rel), "w") as fh:
            fh.write(text)

    def test_behind_base_reports_count_and_remedy_without_failing(self):
        origin = os.path.join(self.tmp, "origin.git")
        work = os.path.join(self.tmp, "work")
        clone = os.path.join(self.tmp, "clone")
        subprocess.run(["git", "init", "-q", "-b", "main", "--bare", origin],
                       check=True, capture_output=True)
        # Pin origin's HEAD explicitly: only `main` is ever pushed, so a
        # HEAD left to an ambient `init.defaultBranch` (e.g. `master` in
        # CI) would dangle, and the clone under test would then DWIM a
        # brand-new local `main` from an already-advanced `origin/main` —
        # silently erasing the stale-base setup below.
        subprocess.run(["git", "--git-dir", origin, "symbolic-ref", "HEAD",
                        "refs/heads/main"], check=True, capture_output=True)
        subprocess.run(["git", "clone", "-q", origin, work],
                       check=True, capture_output=True)
        self._git(work, "config", "user.email", "t@example.com")
        self._git(work, "config", "user.name", "Test")
        self._git(work, "config", "commit.gpgsign", "false")
        self._write(work, "keep.txt", "hello\n")
        self._git(work, "add", "-A")
        self._git(work, "commit", "-qm", "init")
        self._git(work, "checkout", "-q", "-B", "main")
        self._git(work, "push", "-q", "-u", "origin", "main")
        initial_sha = self._git(work, "rev-parse", "main").stdout.strip()

        # The clone under test: its local `main` is created explicitly at
        # the pre-advance commit rather than left to `git clone`/`checkout`
        # DWIM, which — once origin has moved on — would resolve to the
        # wrong commit.
        subprocess.run(["git", "clone", "-q", origin, clone],
                       check=True, capture_output=True)
        self._git(clone, "checkout", "-q", "-B", "main", initial_sha)
        self._git(clone, "branch", "-q", "--set-upstream-to=origin/main",
                  "main")

        # Advance origin by three commits, never fetched into the clone.
        for n in range(3):
            self._write(work, f"advance{n}.txt", f"advance {n}\n")
            self._git(work, "add", "-A")
            self._git(work, "commit", "-qm", f"advance {n}")
        self._git(work, "push", "-q", "origin", "main")

        self._git(clone, "fetch", "-q", "origin")

        # Precondition: the stale-base setup this fixture exists to build
        # must actually hold, or this test would be testing nothing — as
        # happened in CI before this fixture was pinned.
        clone_main = self._git(clone, "rev-parse", "main").stdout.strip()
        clone_origin_main = self._git(clone, "rev-parse",
                                      "origin/main").stdout.strip()
        self.assertNotEqual(
            clone_main, clone_origin_main,
            "fixture precondition failed: clone's main must be behind "
            "origin/main")
        behind = self._git(clone, "rev-list", "--count",
                           "main..origin/main").stdout.strip()
        self.assertEqual(
            behind, "3",
            "fixture precondition failed: clone's main must be exactly "
            "3 commits behind origin/main")

        r = self._run(clone)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout + r.stderr
        self.assertIn("3", out)
        self.assertIn("behind", out.lower())

    def test_no_counterpart_reports_nothing_to_compare(self):
        repo = os.path.join(self.tmp, "solo")
        os.makedirs(repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        repo], check=True, capture_output=True)
        self._git(repo, "config", "user.email", "t@example.com")
        self._git(repo, "config", "user.name", "Test")
        self._git(repo, "config", "commit.gpgsign", "false")
        self._write(repo, "keep.txt", "hello\n")
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-qm", "init")

        r = self._run(repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("nothing to compare", out)


if __name__ == "__main__":
    unittest.main()
