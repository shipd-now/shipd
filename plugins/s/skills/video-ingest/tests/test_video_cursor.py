#!/usr/bin/env python3
"""Unit tests for video_ingest.py's pointer-localization stage
(video-cursor-localization, video-cursor-carry-forward, video-cursor-crops).

The pointer is located by short-baseline frame differencing at a fixed
working scale, behind four gates (span, persistent-churn mask, uniqueness,
dominance), all thresholds relative to the strongest change in the same
difference — never an absolute constant, mirroring video-scene-peaks. This
module builds every input as a synthetic grayscale buffer constructed in the
test itself; no `ffmpeg` and no real recording is involved.

A "frame" here is a flat `bytes` buffer of `width * height` single-channel
pixel values, row-major, matching what `read_gray_frames` will split a
`-pix_fmt gray -f rawvideo` `ffmpeg` output into."""

import contextlib
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import video_ingest as vi  # noqa: E402
from _stubs import stub_bindir  # noqa: E402


@contextlib.contextmanager
def home_set_to(path):
    """Override ``$HOME`` for the duration of the block (video-pipeline-
    testability) — mirrors test_video_backends.py's helper of the same
    name."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = path
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


@contextlib.contextmanager
def path_set_to(path_dir):
    """Override ``$PATH`` for the duration of the block, so
    `required_tools_missing()`'s `shutil.which` lookups see only the stub
    bindir under test."""
    old = os.environ.get("PATH")
    os.environ["PATH"] = path_dir
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = old


# --- synthetic buffer helpers ------------------------------------------------

# Mirrors the module's own CURSOR_TILE (16px) and CURSOR_PIXEL_DELTA (24) —
# spelled out as literals here (rather than imported) so this test still
# constructs valid fixtures before those constants exist (task 1.2 adds
# them), per the task's "observe it fail" step.
_TILE = 16
_DELTA = 150  # comfortably above CURSOR_PIXEL_DELTA (24)


def _frame(width, height, fill=100):
    """A flat grayscale buffer of `width * height` pixels, every pixel
    `fill`."""
    return bytes([fill]) * (width * height)


def _paint(frame, width, x0, y0, w, h, value):
    """Return a new buffer with the pixel block `[x0, x0+w) x [y0, y0+h)` of
    `frame` (row-major, stride `width`) set to `value`."""
    out = bytearray(frame)
    for y in range(y0, y0 + h):
        row = y * width
        for x in range(x0, x0 + w):
            out[row + x] = value
    return bytes(out)


class LocatePointerTest(unittest.TestCase):
    """`locate_pointer(frames, width, height, source_size)` applies the four
    gates to `CURSOR_DIFF_FRAMES` (4) grayscale buffers spaced
    `CURSOR_DIFF_STEP_SECONDS` apart and ending at the target time, returning
    a position mapped to source pixel coordinates or `None`
    (video-cursor-localization)."""

    def test_lone_small_block_is_located(self):
        # Nothing changes across the first two differences; the last
        # difference carries a single 8x8 change fully inside tile (1, 1) —
        # the pointer moving shortly before the target frame.
        width = height = 64
        base = _frame(width, height)
        f0 = f1 = f2 = base
        f3 = _paint(base, width, 20, 20, 8, 8, 100 + _DELTA)
        position = vi.locate_pointer([f0, f1, f2, f3], width, height,
                                     source_size=(128, 128))
        self.assertIsNotNone(position)
        # Tile (1, 1) spans working-scale pixels [16, 32); a source twice
        # the working width/height doubles every coordinate.
        self.assertEqual(position["x"], 32)
        self.assertEqual(position["y"], 32)
        self.assertEqual(position["w"], 32)
        self.assertEqual(position["h"], 32)

    def test_large_redraw_is_not_a_pointer(self):
        # The whole 64x64 frame (a 4x4 tile grid) changes at once, as a
        # modal opening does — every dimension exceeds CURSOR_MAX_SPAN_TILES
        # (3), so no position is reported at all.
        width = height = 64
        base = _frame(width, height)
        f0 = f1 = f2 = base
        f3 = _paint(base, width, 0, 0, width, height, 100 + _DELTA)
        position = vi.locate_pointer([f0, f1, f2, f3], width, height,
                                     source_size=(width, height))
        self.assertIsNone(position)

    def test_persistent_churn_is_masked_out(self):
        # A ticking counter occupies tile (0, 0) and toggles on every
        # difference of the window (D1, D2, and D3); the pointer occupies
        # tile (2, 2) and changes only on the last difference (D3). The
        # churn tile is excluded, leaving the pointer as the sole survivor.
        width = height = 64
        base = _frame(width, height)
        f0 = _paint(base, width, 0, 0, _TILE, _TILE, 100)
        f1 = _paint(base, width, 0, 0, _TILE, _TILE, 100 + _DELTA)
        f2 = _paint(base, width, 0, 0, _TILE, _TILE, 100)
        f3 = _paint(f2, width, 0, 0, _TILE, _TILE, 100 + _DELTA)
        f3 = _paint(f3, width, 2 * _TILE, 2 * _TILE, _TILE, _TILE,
                   100 + _DELTA)
        position = vi.locate_pointer([f0, f1, f2, f3], width, height,
                                     source_size=(width, height))
        self.assertIsNotNone(position)
        self.assertEqual(position["x"], 2 * _TILE)
        self.assertEqual(position["y"], 2 * _TILE)

    def test_competing_candidates_yield_no_position(self):
        # Two cursor-sized regions survive to the last difference — tile
        # (0, 0) and tile (3, 3) — neither present in the preceding
        # difference (D2, which shows no change at all), so uniqueness
        # cannot pick one and no position is reported.
        width = height = 64
        base = _frame(width, height)
        f0 = f1 = f2 = base
        f3 = _paint(base, width, 0, 0, _TILE, _TILE, 100 + _DELTA)
        f3 = _paint(f3, width, 3 * _TILE, 3 * _TILE, _TILE, _TILE,
                   100 + _DELTA)
        position = vi.locate_pointer([f0, f1, f2, f3], width, height,
                                     source_size=(width, height))
        self.assertIsNone(position)

    def test_wholly_static_window_yields_no_position(self):
        # No pixel changes across all four frames.
        width = height = 64
        base = _frame(width, height)
        position = vi.locate_pointer([base, base, base, base], width, height,
                                     source_size=(width, height))
        self.assertIsNone(position)

    def test_same_motion_located_at_two_working_scales(self):
        # The same lone-block motion, built independently at two different
        # working-scale dimensions (the block scaled proportionally with
        # the frame) — every threshold is relative to the strongest change
        # in its own difference, so both are located despite the absolute
        # pixel energies differing between the two scales.
        for width, x0, w in ((64, 20, 8), (128, 40, 16)):
            height = width
            base = _frame(width, height)
            f0 = f1 = f2 = base
            f3 = _paint(base, width, x0, x0, w, w, 100 + _DELTA)
            position = vi.locate_pointer(
                [f0, f1, f2, f3], width, height,
                source_size=(width, height))
            self.assertIsNotNone(
                position, "not located at working width %d" % width)


# --- carry-forward -----------------------------------------------------------


class CarryPointerTest(unittest.TestCase):
    """`carry_pointer(previous, frame_a, frame_b, width, height,
    source_size, from_time)` carries a `locate_pointer`-shaped position
    forward to an inconclusive frame only when the two working-scale
    buffers are byte-for-byte identical over the position's region
    (video-cursor-carry-forward). `frame_a` is the working-scale buffer from
    the frame `previous` was located on; `frame_b` is the new, inconclusive
    frame's buffer; `from_time` is `frame_a`'s own source timestamp."""

    WIDTH = HEIGHT = 64
    PREVIOUS = {"x": 16, "y": 16, "w": 16, "h": 16}

    def test_unchanged_region_is_carried_forward(self):
        base = _frame(self.WIDTH, self.HEIGHT)
        frame_a = _paint(base, self.WIDTH, 16, 16, 16, 16, 100 + _DELTA)
        # frame_b differs elsewhere on screen but is identical to frame_a
        # over the carried region itself.
        frame_b = _paint(frame_a, self.WIDTH, 0, 0, 8, 8, 200)
        carried = vi.carry_pointer(
            self.PREVIOUS, frame_a, frame_b, self.WIDTH, self.HEIGHT,
            source_size=(self.WIDTH, self.HEIGHT), from_time=10.0)
        self.assertIsNotNone(carried)
        self.assertEqual(carried["x"], 16)
        self.assertEqual(carried["y"], 16)
        self.assertEqual(carried["w"], 16)
        self.assertEqual(carried["h"], 16)
        self.assertEqual(carried["origin"], "carried")
        self.assertEqual(carried["from"], 10.0)

    def test_changed_region_blocks_the_carry(self):
        base = _frame(self.WIDTH, self.HEIGHT)
        frame_a = _paint(base, self.WIDTH, 16, 16, 16, 16, 100 + _DELTA)
        frame_b = _paint(frame_a, self.WIDTH, 16, 16, 16, 16, 50)
        carried = vi.carry_pointer(
            self.PREVIOUS, frame_a, frame_b, self.WIDTH, self.HEIGHT,
            source_size=(self.WIDTH, self.HEIGHT), from_time=10.0)
        self.assertIsNone(carried)

    def test_nothing_carried_before_first_localization(self):
        base = _frame(self.WIDTH, self.HEIGHT)
        carried = vi.carry_pointer(
            None, base, base, self.WIDTH, self.HEIGHT,
            source_size=(self.WIDTH, self.HEIGHT), from_time=10.0)
        self.assertIsNone(carried)


# --- crop geometry and index entries -----------------------------------------


class CursorCropBoxTest(unittest.TestCase):
    """`cursor_crop_box(position, source_width, source_height)` is a pure
    window computation: `CURSOR_CROP_WIDTH_FRACTION` (1/3) of the source
    width at a 4:3 aspect, centred on the pointer and clamped to the
    frame's bounds (video-cursor-crops)."""

    SOURCE_WIDTH, SOURCE_HEIGHT = 1462, 1350  # the reference recording

    def test_crop_is_a_third_of_source_width_at_4_3(self):
        position = {"x": 700, "y": 650, "w": 4, "h": 10}
        box = vi.cursor_crop_box(position, self.SOURCE_WIDTH,
                                 self.SOURCE_HEIGHT)
        self.assertEqual(box["w"], round(self.SOURCE_WIDTH / 3))
        self.assertAlmostEqual(box["w"] / box["h"], 4 / 3, places=2)

    def test_crop_is_centred_on_the_pointer(self):
        position = {"x": 700, "y": 650, "w": 4, "h": 10}
        box = vi.cursor_crop_box(position, self.SOURCE_WIDTH,
                                 self.SOURCE_HEIGHT)
        center_x = position["x"] + position["w"] / 2
        center_y = position["y"] + position["h"] / 2
        self.assertLessEqual(box["x"], center_x)
        self.assertGreaterEqual(box["x"] + box["w"], center_x)
        self.assertLessEqual(box["y"], center_y)
        self.assertGreaterEqual(box["y"] + box["h"], center_y)

    def test_pointer_near_an_edge_clamps_into_bounds(self):
        position = {"x": 0, "y": 0, "w": 4, "h": 10}
        box = vi.cursor_crop_box(position, self.SOURCE_WIDTH,
                                 self.SOURCE_HEIGHT)
        self.assertGreaterEqual(box["x"], 0)
        self.assertGreaterEqual(box["y"], 0)
        self.assertLessEqual(box["x"] + box["w"], self.SOURCE_WIDTH)
        self.assertLessEqual(box["y"] + box["h"], self.SOURCE_HEIGHT)

    def test_pointer_near_the_far_edge_clamps_into_bounds(self):
        position = {"x": self.SOURCE_WIDTH - 4, "y": self.SOURCE_HEIGHT - 10,
                   "w": 4, "h": 10}
        box = vi.cursor_crop_box(position, self.SOURCE_WIDTH,
                                 self.SOURCE_HEIGHT)
        self.assertGreaterEqual(box["x"], 0)
        self.assertGreaterEqual(box["y"], 0)
        self.assertLessEqual(box["x"] + box["w"], self.SOURCE_WIDTH)
        self.assertLessEqual(box["y"] + box["h"], self.SOURCE_HEIGHT)

    def test_window_taller_than_an_ultrawide_source_is_shrunk_to_fit(self):
        # A multi-monitor span is wider than 4:1, so the nominal 4:3 window
        # (source_width / 4 tall) is taller than the frame. The size — not
        # just the position — is clamped, because `ffmpeg` rejects a crop
        # larger than its input and that would fail the whole ingest.
        source_width, source_height = 5120, 1080
        position = {"x": 2560, "y": 540, "w": 20, "h": 20}
        box = vi.cursor_crop_box(position, source_width, source_height)
        self.assertLessEqual(box["w"], source_width)
        self.assertLessEqual(box["h"], source_height)
        self.assertLessEqual(box["x"] + box["w"], source_width)
        self.assertLessEqual(box["y"] + box["h"], source_height)
        # The 4:3 aspect survives the clamp — width shrinks to match.
        self.assertAlmostEqual(box["w"] / box["h"], 4 / 3, places=2)


class FramesIndexCursorTest(unittest.TestCase):
    """`build_frames_index` emits the optional `cursor` object on a
    candidate carrying a pointer and nothing on one that does not — a
    consumer can never mistake absence for a position (video-cursor-crops)."""

    def test_entry_with_pointer_carries_cursor_fields(self):
        candidates = [{
            "time": 10.0, "reason": "deixis", "anchor": "here",
            "word_start": 10.0, "file": "000-10.00s.png",
            "cursor": {"x": 100, "y": 200, "w": 480, "h": 360,
                      "file": "000-10.00s-cursor.png", "origin": "located"},
        }]
        index = vi.build_frames_index(candidates)
        [entry] = index["frames"]
        self.assertIn("cursor", entry)
        self.assertEqual(entry["cursor"]["x"], 100)
        self.assertEqual(entry["cursor"]["y"], 200)
        self.assertEqual(entry["cursor"]["w"], 480)
        self.assertEqual(entry["cursor"]["h"], 360)
        self.assertEqual(entry["cursor"]["file"], "000-10.00s-cursor.png")
        self.assertEqual(entry["cursor"]["origin"], "located")

    def test_entry_without_pointer_carries_no_cursor_key(self):
        candidates = [{"time": 20.0, "reason": "scene", "score": 0.05,
                       "file": "000-20.00s.png"}]
        index = vi.build_frames_index(candidates)
        [entry] = index["frames"]
        self.assertNotIn("cursor", entry)


# --- the window's own span -----------------------------------------------


class LocateCursorsWindowSpanTest(unittest.TestCase):
    """`locate_cursors` declines a frame earlier than
    `CURSOR_WINDOW_SPAN_SECONDS`: `cursor_window_argv` clamps its `-ss` to 0
    but keeps its duration, so such a frame's window would end *after* the
    frame's own timestamp and ground it on pixels it does not show
    (video-cursor-localization)."""

    SOURCE = (192, 108)

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="video-cursor-span-")
        self.frames_dir = os.path.join(self.tmp, "frames")
        os.makedirs(self.frames_dir)
        self.window_path = os.path.join(self.tmp, "window.raw")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_run(self):
        """A runner whose window pass always writes a locatable window — so a
        declined frame can only come from the span guard, never from a
        failed or inconclusive localization."""
        width, height = vi.cursor_work_dimensions(*self.SOURCE)
        calls = []

        def run(args, input=None):
            calls.append(list(args))
            if "rawvideo" in args:
                base = _frame(width, height)
                last = _paint(base, width, 48, 48, 8, 8, 100 + _DELTA)
                with open(args[-1], "wb") as fh:
                    fh.write(base + base + base + last)
            return 0, "", ""

        return run, calls

    def locate(self, times):
        run, calls = self.make_run()
        candidates = [{"time": t, "reason": "deixis", "file": "f.png"}
                     for t in times]
        result = vi.locate_cursors(
            candidates, "/fake/source.mov", self.frames_dir,
            self.window_path, self.SOURCE, run)
        windows = [c for c in calls if "rawvideo" in c]
        return result, windows

    def test_frame_earlier_than_the_span_is_declined(self):
        # 0.0s and 0.4s both sit inside the 0.6s span: no window pass is
        # even attempted and neither frame carries a position.
        result, windows = self.locate([0.0, 0.4])
        self.assertEqual(windows, [])
        for entry in result:
            self.assertNotIn("cursor", entry)

    def test_frame_at_the_span_boundary_is_localized(self):
        # 0.6s is the first timestamp with a full window behind it.
        result, windows = self.locate([vi.CURSOR_WINDOW_SPAN_SECONDS])
        self.assertEqual(len(windows), 1)
        self.assertIn("cursor", result[0])
        self.assertEqual(result[0]["cursor"]["origin"], "located")

    def test_a_declined_early_frame_does_not_block_a_later_one(self):
        result, windows = self.locate([0.0, 5.0])
        self.assertEqual(len(windows), 1)
        self.assertNotIn("cursor", result[0])
        self.assertIn("cursor", result[1])


# --- ingest-level wiring -------------------------------------------------


class CmdIngestCursorStageTest(unittest.TestCase):
    """`cmd_ingest` walks the extracted candidates in time order after
    `extract_frames` and before `write_frames_index`, localizing each and
    requesting a crop for a located frame through the injectable runner —
    skipping the whole walk when the resolved `video_cursor` setting is
    false (video-cursor-crops). The fake runner below writes a real
    synthetic grayscale window file to disk for the cursor-window `ffmpeg`
    call, mirroring production where the pixels are read back from a file
    rather than the runner's (text) stdout."""

    SOURCE_WIDTH, SOURCE_HEIGHT = 192, 108

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="video-cursor-home-")
        self.proj = tempfile.mkdtemp(prefix="video-cursor-proj-")
        self.bindir = stub_bindir(
            tempfile.mkdtemp(prefix="video-cursor-bin-"), "bin",
            ["ffmpeg", "ffprobe", "uv"])

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.proj, ignore_errors=True)

    def write_config(self, video_cursor):
        with open(os.path.join(self.proj, ".shipd-config.json"), "w",
                 encoding="utf-8") as fh:
            json.dump({"build": {"video_max_frames": 1,
                                 "video_cursor": video_cursor}}, fh)

    def make_run(self):
        ffprobe_json = json.dumps({
            "format": {"duration": "20.0"},
            "streams": [
                {"codec_type": "audio"},
                {"codec_type": "video", "width": self.SOURCE_WIDTH,
                 "height": self.SOURCE_HEIGHT},
            ],
        })
        asr_words = json.dumps({
            "words": [{"start": 10.0, "end": 10.2, "text": "here"}],
            "model": "fake-model",
        })

        def window_bytes():
            # Nothing changes between the first three frames; the last
            # carries a single small block change — a located pointer.
            base = _frame(self.SOURCE_WIDTH, self.SOURCE_HEIGHT)
            f3 = _paint(base, self.SOURCE_WIDTH, 50, 50, 8, 8, 100 + _DELTA)
            return base + base + base + f3

        calls = []

        def run(args, input=None):
            calls.append(list(args))
            cmd = args[0]
            if cmd == "ffprobe":
                return 0, ffprobe_json, ""
            if cmd == "uv":
                return 0, asr_words, ""
            if cmd == "ffmpeg":
                if "-vn" in args:
                    return 0, "", ""  # audio extraction
                if "-f" in args and "rawvideo" in args:
                    with open(args[-1], "wb") as fh:
                        fh.write(window_bytes())
                    return 0, "", ""  # cursor window
                if "-filter:v" in args:
                    return 0, "", ""  # scene scoring: no scores at all
                return 0, "", ""  # full-frame extraction or a cursor crop
            return 1, "", "unexpected command: %r" % (args,)

        return run, calls

    def run_ingest(self, slug, video_cursor):
        self.write_config(video_cursor)
        run, calls = self.make_run()
        with home_set_to(self.home), path_set_to(self.bindir):
            rc = vi.main(
                ["--project-dir", self.proj, "ingest", "/fake/source.mov",
                 "--slug", slug, "--force"],
                run=run)
            self.assertEqual(rc, 0)
            config = vi.video_config(self.proj)
            bundle = vi.bundle_dir(slug, config)
            with open(os.path.join(bundle, "frames.json"),
                     encoding="utf-8") as fh:
                index = json.load(fh)
        return calls, index

    def test_crop_is_requested_for_a_located_frame(self):
        calls, index = self.run_ingest("cursor-on", video_cursor=True)
        window_calls = [c for c in calls if "-f" in c and "rawvideo" in c]
        self.assertEqual(len(window_calls), 1)
        crop_calls = [c for c in calls
                     if "-vf" in c and "crop=" in c[c.index("-vf") + 1]]
        self.assertEqual(len(crop_calls), 1)
        [entry] = index["frames"]
        self.assertIn("cursor", entry)
        self.assertEqual(entry["cursor"]["origin"], "located")
        self.assertIn("file", entry["cursor"])

    def test_disabled_config_skips_the_whole_stage(self):
        calls, index = self.run_ingest("cursor-off", video_cursor=False)
        window_calls = [c for c in calls if "-f" in c and "rawvideo" in c]
        self.assertEqual(window_calls, [])
        crop_calls = [c for c in calls
                     if "-vf" in c and "crop=" in c[c.index("-vf") + 1]]
        self.assertEqual(crop_calls, [])
        [entry] = index["frames"]
        self.assertNotIn("cursor", entry)


if __name__ == "__main__":
    unittest.main()
