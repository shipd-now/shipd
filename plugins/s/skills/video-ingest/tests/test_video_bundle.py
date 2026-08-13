#!/usr/bin/env python3
"""Unit tests for video_ingest.py's bundle root resolution and ``path <slug>``
verb (video-bundle-contract, video-pipeline-testability).

The bundle root resolves from the layered configuration's ``build.video_dir``
key, home-expanded, defaulting to ``~/.shipd/video`` — a location outside any
repository, mirroring ``design.py``'s ``build.design_dir`` resolution. ``path
<slug>`` prints the absolute bundle directory for a slug without creating it
(unlike ``design.py path``, which does create its scratch dir) — creation is
``ingest``'s job, gated by the existing-bundle refusal rule.

The script is driven as a black box via subprocess against isolated ``$HOME``
and project-dir temp directories — the real home is never read or written."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "video_ingest.py")
SLUG = "demo-recording"

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import video_ingest as vi  # noqa: E402


class VideoIngestTestBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="video-ingest-home-")
        self.proj = tempfile.mkdtemp(prefix="video-ingest-proj-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.proj, ignore_errors=True)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--project-dir", self.proj, *args],
            capture_output=True, text=True, env=env)

    def default_root(self):
        return os.path.join(self.home, ".shipd", "video")

    def write_project_config(self, data):
        with open(os.path.join(self.proj, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(data, fh)


class PathVerbTest(VideoIngestTestBase):
    def test_prints_default_root(self):
        r = self.cli("path", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(self.default_root(), SLUG)
        self.assertEqual(r.stdout.strip(), expected)

    def test_does_not_create_the_directory(self):
        r = self.cli("path", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(self.default_root(), SLUG)
        self.assertFalse(os.path.exists(expected))

    def test_video_dir_config_overrides_root(self):
        override = os.path.join(self.home, "elsewhere", "video")
        self.write_project_config({"build": {"video_dir": override}})
        r = self.cli("path", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(override, SLUG)
        self.assertEqual(r.stdout.strip(), expected)

    def test_video_dir_config_is_home_expanded(self):
        self.write_project_config({"build": {"video_dir": "~/custom-video"}})
        r = self.cli("path", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(self.home, "custom-video", SLUG)
        self.assertEqual(r.stdout.strip(), expected)

    def test_missing_config_falls_back_to_default(self):
        # No .shipd-config.json written at all — resolution must still succeed.
        r = self.cli("path", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(self.default_root(), SLUG)
        self.assertEqual(r.stdout.strip(), expected)


class VideoVocabularyConfigTest(unittest.TestCase):
    """`video_config` resolves `build.video_vocabulary` from the layered
    config (video-vocabulary-biasing)."""

    def setUp(self):
        self.proj = tempfile.mkdtemp(prefix="video-vocab-proj-")

    def tearDown(self):
        shutil.rmtree(self.proj, ignore_errors=True)

    def write_config(self, data):
        with open(os.path.join(self.proj, ".shipd-config.json"), "w",
                 encoding="utf-8") as fh:
            json.dump(data, fh)

    def test_configured_terms_resolve(self):
        self.write_config({"build": {"video_vocabulary": ["shipd", "am"]}})
        config = vi.video_config(self.proj)
        self.assertEqual(config["vocabulary"], ["shipd", "am"])

    def test_absent_key_yields_no_vocabulary(self):
        config = vi.video_config(self.proj)
        self.assertEqual(config["vocabulary"], [])

    def test_empty_list_yields_no_vocabulary(self):
        self.write_config({"build": {"video_vocabulary": []}})
        config = vi.video_config(self.proj)
        self.assertEqual(config["vocabulary"], [])


SAMPLE_MANIFEST = {
    "source": "/tmp/source recording.mov",
    "duration": 48.2,
    "size": 12345,
    "asr_backend": "parakeet",
    "asr_model": "mlx-community/parakeet-tdt-0.6b-v2",
}


class BundleLayoutTest(unittest.TestCase):
    """Direct (in-process) tests of the bundle-creation helpers — white-box,
    mirroring test_spec_common.py's convention of importing the script's
    functions rather than only driving the CLI, since the full `ingest`
    pipeline is not wired end-to-end until later tasks."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="video-ingest-bundle-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def bundle_path(self):
        return os.path.join(self.tmp, SLUG)

    def test_creates_frames_dir_and_manifest(self):
        path = vi.ensure_bundle_dir(self.bundle_path(), force=False)
        vi.write_manifest(path, SAMPLE_MANIFEST)
        # audio.wav and transcript.json are written by later stages
        # (audio extraction, transcript assembly); simulate their presence
        # here to assert the full layout contract.
        open(os.path.join(path, "audio.wav"), "w", encoding="utf-8").close()
        open(os.path.join(path, "transcript.json"), "w",
             encoding="utf-8").close()
        self.assertTrue(os.path.isdir(os.path.join(path, "frames")))
        self.assertTrue(os.path.isfile(os.path.join(path, "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(path, "audio.wav")))
        self.assertTrue(os.path.isfile(os.path.join(path, "transcript.json")))

    def test_manifest_fields(self):
        path = vi.ensure_bundle_dir(self.bundle_path(), force=False)
        vi.write_manifest(path, SAMPLE_MANIFEST)
        with open(os.path.join(path, "manifest.json"), encoding="utf-8") as fh:
            written = json.load(fh)
        for key, value in SAMPLE_MANIFEST.items():
            self.assertEqual(written[key], value)

    def test_manifest_carries_no_diarization_fields(self):
        path = vi.ensure_bundle_dir(self.bundle_path(), force=False)
        vi.write_manifest(path, SAMPLE_MANIFEST)
        with open(os.path.join(path, "manifest.json"), encoding="utf-8") as fh:
            written = json.load(fh)
        for key in ("diarizer_backend", "diarizer_model", "diarization",
                   "speakers_count"):
            self.assertNotIn(key, written)

    def test_refuses_existing_bundle_without_force(self):
        path = vi.ensure_bundle_dir(self.bundle_path(), force=False)
        marker = os.path.join(path, "marker")
        open(marker, "w", encoding="utf-8").close()
        with self.assertRaises(vi.VideoIngestError):
            vi.ensure_bundle_dir(self.bundle_path(), force=False)
        # Refusal must leave the existing bundle untouched.
        self.assertTrue(os.path.exists(marker))

    def test_force_overwrites_existing_bundle(self):
        path = vi.ensure_bundle_dir(self.bundle_path(), force=False)
        marker = os.path.join(path, "marker")
        open(marker, "w", encoding="utf-8").close()
        path2 = vi.ensure_bundle_dir(self.bundle_path(), force=True)
        self.assertEqual(path, path2)
        self.assertFalse(os.path.exists(marker))
        self.assertTrue(os.path.isdir(os.path.join(path2, "frames")))


class TranscriptSchemaTest(unittest.TestCase):
    """`build_transcript`/`write_transcript` — the on-disk `transcript.json`
    schema: a `version` plus a `words` array of `start`/`end`/`text` entries,
    ordered by `start`, with no `segments` key and no speaker field
    (video-transcript-schema)."""

    def test_words_are_ordered_and_speaker_free(self):
        words = [
            {"start": 0.5, "end": 1.0, "text": "there"},
            {"start": 0.0, "end": 0.5, "text": "hello"},
        ]
        doc = vi.build_transcript(words)
        starts = [w["start"] for w in doc["words"]]
        self.assertEqual(starts, sorted(starts))
        for w in doc["words"]:
            self.assertEqual(set(w), {"start", "end", "text"})

    def test_no_segments_key(self):
        words = [{"start": 0.0, "end": 0.5, "text": "hello"}]
        doc = vi.build_transcript(words)
        self.assertIn("version", doc)
        self.assertIn("words", doc)
        self.assertNotIn("segments", doc)

    def test_write_transcript_carries_version_and_words(self):
        tmp = tempfile.mkdtemp(prefix="video-transcript-")
        try:
            words = [
                {"start": 0.0, "end": 0.5, "text": "hello"},
                {"start": 0.5, "end": 1.0, "text": "hi"},
            ]
            vi.write_transcript(tmp, words)
            with open(os.path.join(tmp, "transcript.json"),
                     encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertIn("version", data)
            self.assertIsInstance(data["version"], int)
            self.assertNotIn("segments", data)
            starts = [w["start"] for w in data["words"]]
            self.assertEqual(starts, sorted(starts))
            self.assertEqual(len(data["words"]), 2)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
