#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "playwright",
# ]
# ///
"""record_worker.py — the Playwright recording worker for `/s:drive`'s
`record` verb, invoked as ``uv run record_worker.py <action-module> --base-url
<url> --out-dir <dir> [--storage-state <path>] [--out <path>]``.

Launches one browser and one page, loads the target's cached Playwright
storage state so the recording is authenticated, records the session to
video, then imports the requested action module by path and calls its
``run(page, h, base_url)`` — the action-module contract every recording
script implements (see `references/recording.md`). ``h`` is the recording
helper object passed to every action module: an injected cursor, glide-and-
click, glide-and-type, an anchored annotation card, an element highlight, a
protected `hold`, a recorded wait, and a content-ready mark. Each of these
logs its own start/end offset (seconds since the helper was constructed, which
tracks the start of the recording) into a raw event log on the helper; folding
that log into the semantic timeline (`spans`, `holds`, `leadingCut`), writing
it beside the recording, and holding a protected tail beat before closing are
implemented separately.

Prints one JSON object to stdout on success: ``{"video": <path or null>,
"timeline": <path or null>}``. The timeline file (written beside the
recording, `.timeline.json` in place of the video's own extension unless
``--timeline`` names another path) carries `spans` (fast-forward-eligible
wait stretches), `holds` (protected windows — explicit holds plus every
annotation's visible window), and `leadingCut` (the application-boot end
`content_ready()` marked, or `null`). Any failure (missing action module, an
action module with no ``run``, or a Playwright error) is reported on stderr
as a single ``record_worker: <reason>`` line with a non-zero exit, matching
the worker convention `asr_whisper.py` sets for this plugin's other `uv run`
workers.
"""

import argparse
import importlib.util
import json
import os
import shutil
import sys
import time

_CURSOR_ID = "__drive_cursor__"
_HIGHLIGHT_ID = "__drive_highlight__"
_ANNOTATION_ID = "__drive_annotation__"

_CURSOR_INIT_SCRIPT = """
(() => {
  if (document.getElementById('%(cursor)s')) return;
  const c = document.createElement('div');
  c.id = '%(cursor)s';
  c.style.cssText = 'position:fixed;z-index:2147483647;width:18px;' +
    'height:18px;border-radius:50%%;background:rgba(198,255,78,0.9);' +
    'border:2px solid rgba(15,23,42,0.9);pointer-events:none;left:0;top:0;' +
    'transform:translate(-50%%,-50%%);transition:none;display:none;';
  document.documentElement.appendChild(c);
})();
""" % {"cursor": _CURSOR_ID}

_MOVE_CURSOR_SCRIPT = """([x, y]) => {
  const c = document.getElementById('%(cursor)s');
  if (c) {
    c.style.display = 'block';
    c.style.left = x + 'px';
    c.style.top = y + 'px';
  }
}""" % {"cursor": _CURSOR_ID}

_HIGHLIGHT_SCRIPT = """(box) => {
  let el = document.getElementById('%(highlight)s');
  if (!el) {
    el = document.createElement('div');
    el.id = '%(highlight)s';
    el.style.cssText = 'position:fixed;z-index:2147483646;' +
      'pointer-events:none;border:3px solid #c6ff4e;border-radius:6px;' +
      'box-shadow:0 0 0 2px rgba(15,23,42,0.6);transition:none;';
    document.documentElement.appendChild(el);
  }
  el.style.left = box.x + 'px';
  el.style.top = box.y + 'px';
  el.style.width = box.width + 'px';
  el.style.height = box.height + 'px';
  el.style.display = 'block';
}""" % {"highlight": _HIGHLIGHT_ID}

_HIGHLIGHT_HIDE_SCRIPT = """() => {
  const el = document.getElementById('%(highlight)s');
  if (el) el.style.display = 'none';
}""" % {"highlight": _HIGHLIGHT_ID}

_ANNOTATION_SHOW_SCRIPT = """(args) => {
  let el = document.getElementById('%(annotation)s');
  if (!el) {
    el = document.createElement('div');
    el.id = '%(annotation)s';
    el.style.cssText = 'position:fixed;z-index:2147483647;' +
      'pointer-events:none;max-width:320px;padding:10px 14px;' +
      'border-radius:10px;background:#0f172a;color:#f8fafc;' +
      'font:600 14px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",' +
      'sans-serif;box-shadow:0 8px 24px rgba(0,0,0,0.35);';
    document.documentElement.appendChild(el);
  }
  el.textContent = args.text;
  el.style.display = 'block';
  if (args.box) {
    el.style.left = Math.max(8, args.box.x) + 'px';
    el.style.top = Math.max(8, args.box.y - 56) + 'px';
  } else {
    el.style.left = '24px';
    el.style.top = '24px';
  }
}""" % {"annotation": _ANNOTATION_ID}

_ANNOTATION_HIDE_SCRIPT = """() => {
  const el = document.getElementById('%(annotation)s');
  if (el) el.style.display = 'none';
}""" % {"annotation": _ANNOTATION_ID}


class Helper:
    """The recording helper passed to an action module as `h`.

    Every method that takes browser time (gliding, holding, waiting,
    annotating) appends a `{"start", "end", ...}` record — offsets in seconds
    since this helper was constructed, which tracks the start of the
    recording — to one of the raw event logs below (`_waits`, `_holds`,
    `_annotations`, `_content_ready_at`). Compiling those logs into the
    semantic timeline written beside the recording is a separate step.
    """

    def __init__(self, page):
        self.page = page
        self._t0 = time.monotonic()
        self._cursor_pos = None
        self._waits = []
        self._holds = []
        self._annotations = []
        self._content_ready_at = None
        self._inject_cursor()

    def _now(self):
        return time.monotonic() - self._t0

    def _inject_cursor(self):
        # add_init_script re-injects the cursor on every future navigation;
        # evaluate covers the page already loaded at construction time.
        self.page.add_init_script(_CURSOR_INIT_SCRIPT)
        try:
            self.page.evaluate(_CURSOR_INIT_SCRIPT)
        except Exception:
            pass

    def _move_cursor_to(self, x, y):
        self.page.evaluate(_MOVE_CURSOR_SCRIPT, [x, y])
        self._cursor_pos = (x, y)

    def _element_center(self, selector):
        box = self.page.locator(selector).first.bounding_box()
        if box is None:
            raise RuntimeError(
                "element not visible for selector: %s" % selector)
        return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2

    def _glide_to(self, x, y, steps=24):
        start_x, start_y = self._cursor_pos or (x, y)
        for i in range(1, steps + 1):
            fx = start_x + (x - start_x) * i / steps
            fy = start_y + (y - start_y) * i / steps
            self.page.mouse.move(fx, fy)
            self._move_cursor_to(fx, fy)
            self.page.wait_for_timeout(8)
        self._move_cursor_to(x, y)

    def glide_click(self, selector, steps=24):
        """Glide the injected cursor to `selector` and click it."""
        x, y = self._element_center(selector)
        self._glide_to(x, y, steps=steps)
        self.page.mouse.click(x, y)

    def glide_type(self, selector, text, steps=24, delay=40):
        """Glide the injected cursor to `selector`, focus it, and type
        `text`."""
        x, y = self._element_center(selector)
        self._glide_to(x, y, steps=steps)
        self.page.mouse.click(x, y)
        self.page.locator(selector).first.type(text, delay=delay)

    def highlight(self, selector, duration=1.5):
        """Draw a highlight outline around `selector` for `duration`
        seconds."""
        box = self.page.locator(selector).first.bounding_box()
        if box is None:
            raise RuntimeError(
                "element not visible for selector: %s" % selector)
        self.page.evaluate(_HIGHLIGHT_SCRIPT, box)
        self.page.wait_for_timeout(int(duration * 1000))
        self.page.evaluate(_HIGHLIGHT_HIDE_SCRIPT)

    def annotate(self, text, anchor_selector=None, duration=2.5):
        """Show an anchored annotation card carrying `text` for `duration`
        seconds. The card's visible window is logged to `_annotations`, later
        folded into the timeline's `holds` so it is never fast-forwarded."""
        start = self._now()
        box = None
        if anchor_selector is not None:
            box = self.page.locator(anchor_selector).first.bounding_box()
        self.page.evaluate(_ANNOTATION_SHOW_SCRIPT, {"text": text, "box": box})
        self.page.wait_for_timeout(int(duration * 1000))
        self.page.evaluate(_ANNOTATION_HIDE_SCRIPT)
        self._annotations.append({"start": start, "end": self._now(),
                                   "text": text})

    def hold(self, seconds):
        """Pause for `seconds`, protected from fast-forward regardless of how
        static the frame is. Logged to `_holds`."""
        start = self._now()
        self.page.wait_for_timeout(int(seconds * 1000))
        self._holds.append({"start": start, "end": self._now()})

    def wait(self, seconds):
        """Pause for `seconds`, recorded as a stretch eligible for
        fast-forward. Logged to `_waits`."""
        start = self._now()
        self.page.wait_for_timeout(int(seconds * 1000))
        self._waits.append({"start": start, "end": self._now()})

    def content_ready(self):
        """Mark this moment as the end of the application boot — the first
        call's time becomes the timeline's `leadingCut`."""
        if self._content_ready_at is None:
            self._content_ready_at = self._now()

    def compile_timeline(self):
        """Compile the raw event logs into the semantic timeline:

        - `spans` — the fast-forward-eligible wait stretches, one per
          `wait()` call.
        - `holds` — the protected windows that must play at normal speed:
          every explicit `hold()` call plus every annotation's own visible
          window, since a reveal the viewer must read is never sped up.
        - `leadingCut` — the first `content_ready()` call's offset, or
          `None` when the action module never marked one (the `post` verb
          then falls back to a detected content start, then a fixed
          default).
        """
        spans = [{"start": w["start"], "end": w["end"]} for w in self._waits]
        holds = [{"start": rec["start"], "end": rec["end"]}
                 for rec in self._holds]
        holds += [{"start": a["start"], "end": a["end"]}
                  for a in self._annotations]
        return {
            "spans": spans,
            "holds": holds,
            "leadingCut": self._content_ready_at,
        }


# How long the final frame is held, protected from fast-forward, before the
# recording closes — so the output never cuts off mid-action.
TAIL_BEAT_SECONDS = 1.5


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="record_worker")
    parser.add_argument(
        "action_module",
        help="path to the Python action module exporting "
             "run(page, h, base_url)")
    parser.add_argument(
        "--base-url", required=True,
        help="base URL passed through to the action module")
    parser.add_argument(
        "--out-dir", required=True,
        help="directory Playwright records the raw video into")
    parser.add_argument(
        "--storage-state", default=None,
        help="path to a Playwright storage-state JSON file to load before "
             "recording, so the session is authenticated")
    parser.add_argument(
        "--out", default=None,
        help="final path to move the recorded video to; left at its "
             "Playwright-assigned name under --out-dir when omitted")
    parser.add_argument(
        "--timeline", default=None,
        help="path to write the semantic timeline JSON to; defaults to the "
             "recorded video's path with its extension replaced by "
             "'.timeline.json'")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument(
        "--headed", action="store_true",
        help="run with a visible browser window instead of headless")
    return parser.parse_args(argv)


def load_action_module(path):
    """Import the action module at `path` and return it.

    Raises RuntimeError (never a bare ImportError/AttributeError) when the
    file cannot be loaded or does not export `run`, so callers can report a
    single clear reason.
    """
    if not os.path.isfile(path):
        raise RuntimeError("action module not found: %s" % path)
    spec = importlib.util.spec_from_file_location("drive_action_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load action module: %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run") or not callable(module.run):
        raise RuntimeError(
            "action module %s does not export run(page, h, base_url)"
            % path)
    return module


def run_recording(args):
    from playwright.sync_api import sync_playwright

    action_module = load_action_module(args.action_module)
    os.makedirs(args.out_dir, exist_ok=True)

    recorded_path = None
    timeline = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context_kwargs = {
            "record_video_dir": args.out_dir,
            "record_video_size": {"width": args.width, "height": args.height},
            "viewport": {"width": args.width, "height": args.height},
        }
        if args.storage_state:
            context_kwargs["storage_state"] = args.storage_state
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        h = Helper(page)
        try:
            action_module.run(page, h, args.base_url)
            # Hold the final frame, protected from fast-forward, before the
            # recording closes.
            h.hold(TAIL_BEAT_SECONDS)
        finally:
            timeline = h.compile_timeline()
            video = page.video
            context.close()
            browser.close()
            if video is not None:
                try:
                    recorded_path = str(video.path())
                except Exception:
                    recorded_path = None

    if recorded_path and args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        shutil.move(recorded_path, args.out)
        recorded_path = args.out

    timeline_path = None
    if recorded_path:
        timeline_path = args.timeline or (
            os.path.splitext(recorded_path)[0] + ".timeline.json")
        timeline_dir = os.path.dirname(timeline_path)
        if timeline_dir:
            os.makedirs(timeline_dir, exist_ok=True)
        with open(timeline_path, "w") as fh:
            json.dump(timeline, fh, indent=2)
            fh.write("\n")

    return recorded_path, timeline_path


def main(argv=None):
    args = parse_args(argv)
    try:
        recorded_path, timeline_path = run_recording(args)
    except Exception as exc:  # noqa: BLE001 - report any failure to stderr
        print("record_worker: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps({"video": recorded_path, "timeline": timeline_path}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
