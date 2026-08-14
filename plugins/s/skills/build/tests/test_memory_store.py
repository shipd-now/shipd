#!/usr/bin/env python3
"""Unit tests for the personal memory store: the ``memory_dir`` config key and
its ``memory_store_dir`` resolution (shipd-config memory-store-key), the
``--personal`` targeting of the wiki status verbs (spec-status
wiki-status-verbs), and ``spec_emit.py wiki --personal`` (spec-io
wiki-emission)."""

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


@contextlib.contextmanager
def home_set_to(path):
    """Override ``$HOME`` (the ``expanduser`` seam) for the duration of the
    block, so config resolution never reads the real home directory."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = path
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_common as sc  # noqa: E402

STATUS = os.path.join(SCRIPTS, "spec_status.py")
EMIT = os.path.join(SCRIPTS, "spec_emit.py")


def _write_config(root, data):
    """Write ``<root>/.shipd-config.json`` with the given top-level keys."""
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, sc.CONFIG_FILENAME), "w",
              encoding="utf-8") as fh:
        json.dump(data, fh)
    return root


class MemoryStoreDirTest(unittest.TestCase):
    """``memory_store_dir`` resolves the ``memory_dir`` config key
    (shipd-config memory-store-key). ``$HOME`` is overridden so ``~`` expansion is
    deterministic and content-dir resolution never reads the real home
    config."""

    def test_declared_key_resolves_expanded(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            home = os.path.realpath(home)
            _write_config(root, {"memory_dir": "~/personal/shipd-memory"})
            with home_set_to(home):
                self.assertEqual(
                    sc.memory_store_dir(root),
                    os.path.join(home, "personal", "shipd-memory", "wiki"))

    def test_undeclared_key_defaults(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            home = os.path.realpath(home)
            _write_config(root, {})
            with home_set_to(home):
                self.assertEqual(
                    sc.memory_store_dir(root),
                    os.path.join(home, ".shipd-memory", "wiki"))

    def test_relative_value_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_config(root, {"memory_dir": "relative/shipd-memory"})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.memory_store_dir(root)
            self.assertIn("memory_dir", str(cm.exception))

    def test_empty_string_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_config(root, {"memory_dir": ""})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.memory_store_dir(root)
            self.assertIn("memory_dir", str(cm.exception))

    def test_non_string_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_config(root, {"memory_dir": 42})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.memory_store_dir(root)
            self.assertIn("memory_dir", str(cm.exception))


class PersonalTargetingTest(unittest.TestCase):
    """The ``--personal`` flag targets the personal memory store on the wiki
    status verbs (spec-status wiki-status-verbs, shipd-wiki wiki-store-layout).

    ``self.root`` carries a config declaring ``memory_dir`` at an isolated temp
    dir and no ``workspace`` key, so the personal store resolves by fixed path
    without any workspace discovery. ``$HOME`` is isolated per subprocess."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="personal-target-root-")
        self.mem = tempfile.mkdtemp(prefix="personal-target-mem-")
        self.home = tempfile.mkdtemp(prefix="personal-target-home-")
        _write_config(self.root, {"memory_dir": self.mem})

    def tearDown(self):
        for d in (self.root, self.mem, self.home):
            shutil.rmtree(d, ignore_errors=True)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", STATUS, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def store(self):
        return os.path.join(self.mem, "wiki")

    def test_personal_init_show_and_cat(self):
        # wiki-init --personal scaffolds the store at <memory_dir>/wiki without
        # any workspace.
        r = self.cli("wiki-init", "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        store = self.store()
        for name in ("schema.md", "index.md", "log.md", "queue.md"):
            self.assertTrue(os.path.isfile(os.path.join(store, name)), name)
        self.assertTrue(os.path.isdir(os.path.join(store, "wiki")))
        self.assertTrue(os.path.isdir(os.path.join(store, "sources")))
        # No workspace store was created under the root.
        self.assertFalse(os.path.isdir(os.path.join(self.root, ".shipd", "wiki")))

        # wiki-show --personal reports that store's health with base: none.
        r = self.cli("wiki-show", "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(store, r.stdout)
        self.assertIn("base: none", r.stdout)

        # cat wiki <slug> --personal reads a page from the personal store.
        pages = os.path.join(store, "wiki")
        with open(os.path.join(pages, "welcome.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Welcome\n\nHello from the personal store.\n")
        r = self.cli("cat", "wiki", "welcome", "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Hello from the personal store.", r.stdout)
        self.assertIn("welcome.md", r.stdout)


class EmitPersonalTest(unittest.TestCase):
    """``spec_emit.py wiki --from <staging> --personal`` installs into the
    personal memory store by fixed path (spec-io wiki-emission), leaving the
    workspace store untouched."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="emit-personal-root-")
        self.mem = tempfile.mkdtemp(prefix="emit-personal-mem-")
        self.home = tempfile.mkdtemp(prefix="emit-personal-home-")
        self.staging = tempfile.mkdtemp(prefix="emit-personal-stage-")
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}, "memory_dir": self.mem}, fh)

    def tearDown(self):
        for d in (self.root, self.mem, self.home, self.staging):
            shutil.rmtree(d, ignore_errors=True)

    def status(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", STATUS, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def emit(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", EMIT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def snapshot(self, store):
        out = {}
        for dirpath, _dirs, names in os.walk(store):
            for name in names:
                p = os.path.join(dirpath, name)
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, store)] = fh.read()
        return out

    def test_emit_personal_installs_into_memory_store(self):
        # Scaffold both stores; snapshot the workspace store to prove it is
        # untouched by a --personal emit.
        self.assertEqual(self.status("wiki-init").returncode, 0)
        self.assertEqual(self.status("wiki-init", "--personal").returncode, 0)
        ws_store = os.path.join(self.root, ".shipd", "wiki")
        ws_before = self.snapshot(ws_store)

        # Stage a new page and an index cataloging it.
        os.makedirs(os.path.join(self.staging, "wiki"))
        with open(os.path.join(self.staging, "wiki", "note.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Note\n\nA staged note.\n")
        with open(os.path.join(self.staging, "index.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Index\n\n- [[note]] — A staged note.\n")

        r = self.emit("wiki", "--from", self.staging, "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        store = os.path.join(self.mem, "wiki")
        self.assertTrue(
            os.path.isfile(os.path.join(store, "wiki", "note.md")))
        with open(os.path.join(store, "index.md"), encoding="utf-8") as fh:
            self.assertIn("[[note]]", fh.read())
        # The workspace store is byte-for-byte unchanged.
        self.assertEqual(self.snapshot(ws_store), ws_before)


if __name__ == "__main__":
    unittest.main()
