#!/usr/bin/env python3
"""postprocess.py — the stdlib-only Python 3 engine behind `drive.py`'s
`post` verb (drive-postprocess): turns a raw recording and its semantic
timeline (`record_worker.py`'s `spans`/`holds`/`leadingCut`, drive-recording)
into a branded, fast-forwarded demo video.

Every decision — which stretches of the recording are eligible for
fast-forward, where the leading boot is cut, how the spinner backstop
detects dead air `ffmpeg`/pixel-freeze detection cannot see, and how the
branded title card and speed badge are composited — lives here, matching
`drive.py`'s CLI split: nothing in this module imports Playwright, and the
pure span algebra below never shells out to `ffmpeg` at all, so this file's
test suite runs with no video toolchain installed (drive-postprocess's own
tests exercise the algebra directly; every function that shells out —
`spinner_backstop_spans`, `probe_duration`, `detect_content_start`, and
`assemble` at the bottom of this file — does so through the same injectable
`run` seam `drive.py`'s `doctor --fix` uses, so a caller can substitute a
fake without touching a real video toolchain).

Span algebra (this module's core, task 6.2):
  1. ``union_spans`` — merge any number of `{"start", "end"}` span lists into
     their sorted, non-overlapping union.
  2. ``merge_short_blips`` — merge two dead-air blocks separated by a gap no
     longer than `BLIP_MERGE_GAP_SECONDS` (a fleeting DOM mutation or a
     blip of activity too short to be real interaction), so the whole
     stretch is treated as continuous dead air.
  3. The five-second floor (`FLOOR_SECONDS`), applied once here to drop a
     merged block that is too short to bother with before subtraction ever
     runs.
  4. ``subtract_spans`` — remove every `holds` window from the eligible set,
     so a protected reveal (an annotation, or the recorder's own protected
     tail beat) always plays at normal speed regardless of how static it
     looks. Subtracting a hold from the *middle* of a floored block can
     leave fragments shorter than the floor (a 20s block with a 16s hold in
     its middle leaves two ~2s remainders) — those are not "a dead-air
     block of at least five seconds" either, so a sub-floor fragment would
     be a visible glitch if left eligible.
  5. The five-second floor, applied **again** to the fragments subtraction
     produced, so the floor is a property of what actually ends up
     fast-forwarded, not just of the intermediate pre-subtraction blocks
     ("A short pause stays at normal speed").
  6. ``build_segments`` — turn the final eligible-span set into the ordered,
     gap-free segment list covering the whole body, holding the final beat
     at normal speed as a backstop even if an eligible span would otherwise
     reach the very end.

``compute_ff_spans`` composes steps 1-5; ``build_segments`` is step 6,
kept separate because it is the one step that needs the recording's total
duration.
"""

import os
import re
import shutil
import tempfile

NORMAL_SPEED = 1.0
FF_SPEED = 10.0

# A merged dead-air block shorter than this is a "short pause" and stays at
# normal speed (drive-postprocess: "A short pause stays at normal speed").
FLOOR_SECONDS = 5.0

# Two dead-air blocks separated by an activity gap this short (or shorter)
# are treated as one continuous stretch — the gap is noise (e.g. a fleeting
# DOM mutation), not real interaction the viewer needs to see at normal
# speed.
BLIP_MERGE_GAP_SECONDS = 1.0

# Defensive minimum trailing stretch held at normal speed even when an
# eligible span would otherwise reach the recording's very end
# (drive-postprocess: "the final result SHALL be held at normal speed").
# `record_worker.py`'s own protected tail beat (drive-recording) should
# already produce a `holds` window covering this; this is a backstop, not
# the primary mechanism.
TAIL_HOLD_SECONDS = 1.0

# The fixed fallback leading-cut point used when neither the timeline's
# `leadingCut` nor a detected content start is available.
FALLBACK_LEADING_CUT_SECONDS = 2.0


def _as_span(span):
    return {"start": float(span["start"]), "end": float(span["end"])}


def union_spans(*span_lists):
    """Merge any number of `{"start", "end"}` span lists into their sorted,
    non-overlapping (and non-touching-with-a-gap) union. Pure — no I/O."""
    all_spans = []
    for spans in span_lists:
        all_spans.extend(_as_span(s) for s in spans)
    if not all_spans:
        return []
    ordered = sorted(all_spans, key=lambda s: (s["start"], s["end"]))
    merged = [dict(ordered[0])]
    for span in ordered[1:]:
        last = merged[-1]
        if span["start"] <= last["end"]:
            last["end"] = max(last["end"], span["end"])
        else:
            merged.append(dict(span))
    return merged


def merge_short_blips(spans, max_gap=BLIP_MERGE_GAP_SECONDS):
    """Merge consecutive spans separated by a gap of at most `max_gap`
    seconds into one. `spans` need not be pre-sorted or pre-merged; this
    also collapses any residual overlap. Pure — no I/O."""
    if not spans:
        return []
    ordered = sorted((_as_span(s) for s in spans), key=lambda s: s["start"])
    merged = [ordered[0]]
    for span in ordered[1:]:
        last = merged[-1]
        gap = span["start"] - last["end"]
        if gap <= max_gap:
            last["end"] = max(last["end"], span["end"])
        else:
            merged.append(span)
    return merged


def subtract_spans(spans, cuts):
    """Remove every window in `cuts` from `spans`, splitting a span in two
    when a cut falls in its middle and trimming or dropping it when a cut
    overlaps an edge or covers it entirely. Pure — no I/O."""
    cuts = [_as_span(c) for c in cuts]
    result = []
    for span in spans:
        pieces = [dict(span)]
        for cut in cuts:
            next_pieces = []
            for piece in pieces:
                next_pieces.extend(_subtract_one(piece, cut))
            pieces = next_pieces
        result.extend(p for p in pieces if p["end"] > p["start"])
    return result


def _subtract_one(span, cut):
    if cut["end"] <= span["start"] or cut["start"] >= span["end"]:
        return [span]
    pieces = []
    if cut["start"] > span["start"]:
        pieces.append({"start": span["start"],
                       "end": min(cut["start"], span["end"])})
    if cut["end"] < span["end"]:
        pieces.append({"start": max(cut["end"], span["start"]),
                       "end": span["end"]})
    return pieces


def compute_ff_spans(timeline_spans, holds=None, backstop_spans=None):
    """The fast-forward-eligible span set: the timeline's recorded waits
    unioned with the spinner backstop's detected dead air, blip-merged,
    floored at `FLOOR_SECONDS`, subtracted by every `holds` window, and
    floored again — subtracting a hold from a block's middle can leave
    fragments shorter than the floor, and those are not "a dead-air block
    of at least five seconds" either, so the floor is re-applied to what
    subtraction actually produced rather than only to the pre-subtraction
    blocks. Pure — no I/O; the actual backstop sampling lives in a later
    task."""
    holds = list(holds or [])
    backstop_spans = list(backstop_spans or [])
    raw = union_spans(timeline_spans, backstop_spans)
    merged = merge_short_blips(raw)
    floored = [s for s in merged if (s["end"] - s["start"]) >= FLOOR_SECONDS]
    remaining = subtract_spans(floored, holds)
    return [s for s in remaining if (s["end"] - s["start"]) >= FLOOR_SECONDS]


def build_segments(duration, ff_spans):
    """The ordered, gap-free segment list covering `[0, duration]`: every
    `ff_spans` window tagged `FF_SPEED`, everything else `NORMAL_SPEED`.
    Never cuts interior content — every second of `duration` is covered by
    exactly one segment. Holds the final beat at normal speed even if an
    eligible span would otherwise reach `duration` (see
    `TAIL_HOLD_SECONDS`). Pure — no I/O."""
    ff_spans = sorted((_as_span(s) for s in ff_spans),
                      key=lambda s: s["start"])

    if ff_spans and ff_spans[-1]["end"] >= duration:
        last = ff_spans[-1]
        trimmed_end = max(last["start"], duration - TAIL_HOLD_SECONDS)
        if trimmed_end <= last["start"]:
            ff_spans = ff_spans[:-1]
        else:
            last["end"] = trimmed_end

    segments = []
    cursor = 0.0
    for span in ff_spans:
        start = max(span["start"], 0.0)
        end = min(span["end"], duration)
        if end <= start:
            continue
        if start > cursor:
            segments.append(
                {"start": cursor, "end": start, "speed": NORMAL_SPEED})
        segments.append({"start": start, "end": end, "speed": FF_SPEED})
        cursor = max(cursor, end)
    if cursor < duration:
        segments.append(
            {"start": cursor, "end": duration, "speed": NORMAL_SPEED})
    return segments


def resolve_leading_cut(leading_cut=None, detected_content_start=None):
    """Where to cut the leading application boot: the timeline's own
    `leadingCut` when present, the detected content start otherwise, and
    `FALLBACK_LEADING_CUT_SECONDS` when neither is available
    (drive-postprocess). Pure — no I/O."""
    if leading_cut is not None:
        return leading_cut
    if detected_content_start is not None:
        return detected_content_start
    return FALLBACK_LEADING_CUT_SECONDS


# --- the spinner backstop (task 6.3) --------------------------------------
#
# The timeline `record_worker.py` writes only knows about the waits an
# action module explicitly recorded. An animated spinner confined to a
# small region of the frame is dead air the viewer is still just waiting
# through, but nothing marks it — and naive pixel-freeze detection cannot
# see it either, since the frame keeps changing every sample. The backstop
# below classifies a sample as "waiting" two ways: the frame itself is
# near-blank (a blank loading screen), or the *union* of changed cells
# across a short time window stays small (an animation confined to one
# corner still leaves most of the grid untouched, sample after sample). Its
# spans are unioned into `compute_ff_spans`'s `backstop_spans` exactly like
# a timeline span.
#
# Everything below `spinner_backstop_spans` (`read_gray_frames`,
# `_frame_std`, `_changed_cells`, `classify_samples`,
# `group_waiting_samples`) is pure — it operates on raw grayscale sample
# bytes already in memory, so it is directly unit-testable with no `ffmpeg`
# involved. `spinner_backstop_spans` itself is the one function in this
# module that shells out, through the same injectable `run` seam as
# `drive.py`'s `doctor --fix` (`default_run`'s `(rc, stdout, stderr)`
# signature) so a caller can substitute a fake without touching a real
# video toolchain.

# The grid every sample is downscaled to before classification — small
# enough that a spinner's few animated cells are still a small fraction of
# the whole grid, large enough that real content changes clearly dominate.
SPINNER_GRID_WIDTH = 32
SPINNER_GRID_HEIGHT = 18

# Samples per second `ffmpeg` extracts. 2/s (one every 0.5s) is fine-grained
# enough to catch a fast spinner's animation frames without an excessive
# sample count over a multi-minute recording.
SPINNER_SAMPLE_FPS = 2.0

# A per-pixel grayscale delta at or below this is noise, not a real change,
# when comparing two consecutive samples.
SPINNER_PIXEL_DELTA = 10

# A sample's own pixel-value standard deviation at or below this counts the
# frame as near-blank on its own (e.g. a plain loading screen), independent
# of the windowed change-union check.
SPINNER_BLANK_STD_THRESHOLD = 6.0

# The window (in samples) whose changed-cell union is checked around each
# sample — 6 samples at SPINNER_SAMPLE_FPS is a 3-second window, long enough
# to see a spinner's animation cycle without smearing across real scene
# changes on either side of it.
SPINNER_WINDOW_SAMPLES = 6

# A window whose changed-cell union covers at most this fraction of the
# grid is classified as dead air — an animated spinner confined to a small
# region never pushes the union past a small fraction of the grid, however
# long the window runs.
SPINNER_CHANGE_FRACTION = 0.12


def spinner_sample_argv(video_path, out_path, width=SPINNER_GRID_WIDTH,
                        height=SPINNER_GRID_HEIGHT, fps=SPINNER_SAMPLE_FPS):
    """Argv for the single `ffmpeg` pass that samples the whole of
    `video_path` down to `width`x`height` grayscale frames at `fps`
    samples/second, written as raw pixel bytes to `out_path`. Pure — no I/O;
    every path is its own argv element, never a shell string (mirrors
    `video_ingest.py`'s `cursor_window_argv`)."""
    return ["ffmpeg", "-y", "-i", video_path, "-vf",
           "fps=%g,scale=%d:%d" % (fps, width, height),
           "-pix_fmt", "gray", "-f", "rawvideo", out_path]


def read_gray_frames(path, width, height):
    """Read the grayscale rawvideo bytes `spinner_sample_argv`'s `ffmpeg`
    pass wrote to `path` and split them into `width * height`-byte frame
    buffers, oldest first. Any trailing partial frame (a short final write)
    is dropped rather than yielding a mismatched buffer."""
    frame_size = width * height
    with open(path, "rb") as fh:
        data = fh.read()
    return [data[offset:offset + frame_size]
           for offset in range(0, len(data) - frame_size + 1, frame_size)]


def _frame_std(frame):
    """Population standard deviation of a grayscale frame's pixel values —
    low for a near-blank frame (a plain loading screen), high for one with
    real visual structure. Pure."""
    n = len(frame)
    if n == 0:
        return 0.0
    mean = sum(frame) / n
    variance = sum((pixel - mean) ** 2 for pixel in frame) / n
    return variance ** 0.5


def _changed_cells(a, b, pixel_delta=SPINNER_PIXEL_DELTA):
    """The set of cell (pixel) indices whose grayscale value differs by more
    than `pixel_delta` between two same-sized consecutive samples `a` and
    `b`. Pure."""
    return {i for i in range(len(a)) if abs(a[i] - b[i]) > pixel_delta}


def classify_samples(frames, width, height,
                     window=SPINNER_WINDOW_SAMPLES,
                     change_fraction=SPINNER_CHANGE_FRACTION,
                     blank_std=SPINNER_BLANK_STD_THRESHOLD,
                     pixel_delta=SPINNER_PIXEL_DELTA):
    """Classify each of `frames` as waiting (`True`) or active (`False`).

    A sample is waiting when either holds:
      - its own frame is near-blank (`_frame_std` at or below `blank_std`);
      - the union of changed cells across the `window`-sample stretch
        centered on it, relative to `width * height`, stays at or below
        `change_fraction` — the defining trait of a small confined
        animation (a spinner): *something* changes every sample, but the
        union of *what* changes never grows large.

    Pure — no I/O; operates purely on the in-memory sample buffers."""
    n = len(frames)
    total_cells = width * height
    threshold = change_fraction * total_cells
    half = window // 2
    waiting = [False] * n
    for i in range(n):
        if _frame_std(frames[i]) <= blank_std:
            waiting[i] = True
            continue
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        union = set()
        for j in range(lo, hi - 1):
            union |= _changed_cells(frames[j], frames[j + 1], pixel_delta)
        waiting[i] = len(union) <= threshold
    return waiting


def group_waiting_samples(waiting, sample_interval):
    """Group a per-sample `waiting` classification (as `classify_samples`
    returns) into `{"start", "end"}` spans covering each consecutive
    waiting run, where sample `i` covers
    `[i * sample_interval, (i + 1) * sample_interval)`. Pure — no I/O."""
    spans = []
    start_i = None
    for i, is_waiting in enumerate(waiting):
        if is_waiting and start_i is None:
            start_i = i
        elif not is_waiting and start_i is not None:
            spans.append({"start": start_i * sample_interval,
                         "end": i * sample_interval})
            start_i = None
    if start_i is not None:
        spans.append({"start": start_i * sample_interval,
                     "end": len(waiting) * sample_interval})
    return spans


def spinner_backstop_spans(video_path, run, width=SPINNER_GRID_WIDTH,
                           height=SPINNER_GRID_HEIGHT,
                           fps=SPINNER_SAMPLE_FPS):
    """Sample `video_path` through `run` (the injectable subprocess seam,
    `default_run`'s `(rc, stdout, stderr)` signature — `drive.py`'s `post`
    verb supplies the real one) and return the spinner backstop's detected
    dead-air spans, ready to pass as `compute_ff_spans`'s `backstop_spans`.

    This is the one function in this module that shells out; everything it
    calls above is pure and independently testable. Raises `RuntimeError`
    (never a bare `ffmpeg` exit code) when the sampling pass fails, so a
    caller can report one clear reason."""
    fd, tmp_path = tempfile.mkstemp(suffix=".gray")
    os.close(fd)
    try:
        argv = spinner_sample_argv(video_path, tmp_path, width, height, fps)
        rc, out, err = run(argv)
        if rc != 0:
            raise RuntimeError(
                "ffmpeg failed sampling %s for the spinner backstop: %s"
                % (video_path, (err or out).strip()))
        frames = read_gray_frames(tmp_path, width, height)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if len(frames) < 2:
        return []
    waiting = classify_samples(frames, width, height)
    return group_waiting_samples(waiting, 1.0 / fps)


# --- duration / leading-cut detection (task 6.4) --------------------------


def probe_duration_argv(video_path):
    """Argv for the single `ffprobe` call that reads `video_path`'s total
    duration in seconds as a bare number on stdout. Pure — no I/O."""
    return ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "csv=p=0", video_path]


def probe_duration(video_path, run):
    """`video_path`'s total duration in seconds, via `run` (the injectable
    subprocess seam). Raises `RuntimeError` on a failed or unparseable
    probe."""
    rc, out, err = run(probe_duration_argv(video_path))
    if rc != 0:
        raise RuntimeError("ffprobe failed reading %s: %s"
                           % (video_path, (err or out).strip()))
    try:
        return float(out.strip())
    except ValueError:
        raise RuntimeError(
            "ffprobe returned an unparseable duration for %s: %r"
            % (video_path, out))


# How far into the recording the leading-cut detector looks for the first
# sample carrying real visual structure — the application boot (a blank or
# near-static loading screen) is expected to resolve well within this
# window; a fixed cap keeps this a bounded, cheap probe rather than
# sampling the whole recording just to find its first few seconds.
LEADING_CUT_PROBE_SECONDS = 15.0


def detect_content_start_argv(video_path, out_path,
                              probe_seconds=LEADING_CUT_PROBE_SECONDS,
                              width=SPINNER_GRID_WIDTH,
                              height=SPINNER_GRID_HEIGHT,
                              fps=SPINNER_SAMPLE_FPS):
    """Argv for the `ffmpeg` pass that samples only `video_path`'s first
    `probe_seconds` down to a grayscale grid, for `detect_content_start`.
    Pure — no I/O."""
    return ["ffmpeg", "-y", "-i", video_path, "-t", "%s" % probe_seconds,
           "-vf", "fps=%g,scale=%d:%d" % (fps, width, height),
           "-pix_fmt", "gray", "-f", "rawvideo", out_path]


def detect_content_start(video_path, run,
                         probe_seconds=LEADING_CUT_PROBE_SECONDS,
                         width=SPINNER_GRID_WIDTH, height=SPINNER_GRID_HEIGHT,
                         fps=SPINNER_SAMPLE_FPS):
    """Best-effort detection of where the application boot ends: reuses the
    spinner backstop's own classification (`classify_samples`) over the
    first `probe_seconds` of `video_path` and returns the first sample's
    time that is *not* classified waiting — the first moment carrying real
    visual structure, as opposed to the blank/near-static loading screen
    that precedes it.

    Returns `None`, never raises, on any probe failure or inconclusive
    result — this is only ever the middle rung of `resolve_leading_cut`'s
    fallback chain (drive-postprocess: "at the detected content start
    otherwise"), so a failed detection here must never abort the run; it
    just falls through to the fixed default."""
    fd, tmp_path = tempfile.mkstemp(suffix=".gray")
    os.close(fd)
    try:
        argv = detect_content_start_argv(
            video_path, tmp_path, probe_seconds, width, height, fps)
        rc, _out, _err = run(argv)
        if rc != 0:
            return None
        frames = read_gray_frames(tmp_path, width, height)
    except OSError:
        return None
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if len(frames) < 2:
        return None
    waiting = classify_samples(frames, width, height)
    for i, is_waiting in enumerate(waiting):
        if not is_waiting:
            return i / fps
    return None


def _shift_and_clip(spans, offset):
    """Shift every span in `spans` by `-offset` (the leading cut being
    removed from the front of the recording), dropping any span that falls
    entirely before the cut and clipping one that straddles it. Pure —
    no I/O."""
    shifted = []
    for span in spans:
        start = span["start"] - offset
        end = span["end"] - offset
        if end <= 0:
            continue
        shifted.append({"start": max(start, 0.0), "end": end})
    return shifted


# --- title resolution (task 6.8, drive-brand-frames) ----------------------

# The fixed fallback title when the working tree is not on a
# `change/<slug>` branch and no title was explicitly supplied.
DEFAULT_TITLE = "shipd demo"

_CHANGE_BRANCH_RE = re.compile(r"^change/(.+)$")


def resolve_title(branch=None, supplied=None, default=DEFAULT_TITLE):
    """The rendered title card's text (drive-brand-frames): the current
    shipd change name when `branch` is a `change/<slug>` branch, an
    explicitly `supplied` title otherwise, and `default` when neither
    applies. Never derived from an issue-tracker identifier — a branch that
    merely *looks* like one (but does not match `change/<slug>`) falls
    straight through to `supplied`/`default` exactly like any other branch
    name; nothing here ever parses a ticket id out of anything. Pure — no
    I/O: `drive.py` is what asks git for the actual current branch name and
    hands it in as a plain string (or `None` when it cannot tell, e.g. a
    detached HEAD)."""
    if branch:
        match = _CHANGE_BRANCH_RE.match(branch)
        if match:
            return match.group(1)
    if supplied:
        return supplied
    return default


# --- assembly: encode, badge, title card, concatenate (task 6.4) ---------

# How long the title card holds before the recording itself begins.
TITLE_CARD_DURATION_SECONDS = 2.5

# The fast-forward badge's geometry (drive-brand-frames: "at most 44 pixels
# tall and at most 180 pixels wide") and the margin it sits off the frame's
# edge, at the default 1280x720 frame `browser_worker.py cards` renders it
# for.
BADGE_WIDTH = 180
BADGE_HEIGHT = 44
BADGE_MARGIN = 24


def badge_position(corner, frame_width, frame_height,
                   badge_width=BADGE_WIDTH, badge_height=BADGE_HEIGHT,
                   margin=BADGE_MARGIN):
    """The `(x, y)` top-left pixel the badge overlay is composited at for
    `corner` (`"top-left"`, `"top-right"`, `"bottom-left"`, or the default
    `"bottom-right"`), `margin` pixels off both edges. Pure — no I/O."""
    if corner == "top-left":
        return margin, margin
    if corner == "top-right":
        return frame_width - badge_width - margin, margin
    if corner == "bottom-left":
        return margin, frame_height - badge_height - margin
    return (frame_width - badge_width - margin,
           frame_height - badge_height - margin)


def title_card_clip_argv(image_path, duration, out_path,
                         width=1280, height=720, fps=30):
    """Argv for the `ffmpeg` pass that turns a single rendered title-card
    image into a silent `duration`-second video clip, scaled to
    `width`x`height`, ready to prepend via `concat_argv`. Pure — no I/O."""
    return ["ffmpeg", "-y", "-loop", "1", "-i", image_path,
           "-t", "%s" % duration,
           "-vf", "scale=%d:%d,format=yuv420p,fps=%d" % (width, height, fps),
           "-an", out_path]


def segment_clip_argv(video_path, start, end, speed, out_path,
                      badge_path=None, badge_x=0, badge_y=0):
    """Argv for the `ffmpeg` pass that encodes one output segment: the
    `[start, end)` slice of `video_path`, played at `speed` (`NORMAL_SPEED`
    or `FF_SPEED`) via `setpts`, with the fast-forward badge composited on
    top only when `badge_path` is given (drive-brand-frames: "The badge
    SHALL appear only over fast-forwarded stretches"). Pure — no I/O."""
    trim_filter = "trim=start=%s:end=%s,setpts=PTS-STARTPTS" % (start, end)
    if speed != NORMAL_SPEED:
        trim_filter += ",setpts=PTS/%s" % speed
    if badge_path:
        filter_complex = (
            "[0:v]%s[seg];[1:v]format=rgba[badge];"
            "[seg][badge]overlay=%d:%d:shortest=1[out]"
            % (trim_filter, badge_x, badge_y))
        return ["ffmpeg", "-y", "-i", video_path, "-i", badge_path,
               "-filter_complex", filter_complex, "-map", "[out]",
               "-an", out_path]
    return ["ffmpeg", "-y", "-i", video_path, "-vf", trim_filter,
           "-an", out_path]


def write_concat_list(clip_paths, list_path):
    """Write the `ffmpeg` concat-demuxer list file naming `clip_paths` in
    order, and return `list_path`."""
    with open(list_path, "w", encoding="utf-8") as fh:
        for path in clip_paths:
            escaped = os.path.abspath(path).replace("'", "'\\''")
            fh.write("file '%s'\n" % escaped)
    return list_path


def concat_argv(list_path, out_path, width=1280, height=720, fps=30):
    """Argv for the final `ffmpeg` pass that concatenates every clip named
    in the `write_concat_list`-written `list_path` (the title card, then
    every segment, in order) into `out_path`. Re-encodes rather than stream-
    copying, since segments were built at different `setpts` rates. Pure —
    no I/O."""
    return ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
           "-vf", "scale=%d:%d,format=yuv420p,fps=%d" % (width, height, fps),
           "-an", out_path]


# --- inline-embeddable GIF output (task 6.5) -------------------------------

# Frame rate and max width for the animated GIF written beside the finished
# video (drive-postprocess: "Where the verb is asked for an
# inline-embeddable output, it SHALL additionally write an animated GIF") —
# low enough to keep the file small for inline embedding (a PR description,
# a chat message), high enough that fast-forwarded stretches still read.
GIF_FPS = 10
GIF_MAX_WIDTH = 720


def gif_path_for(video_out_path):
    """The GIF path written beside `video_out_path`: the same path with its
    extension replaced by `.gif`. Pure — no I/O."""
    return os.path.splitext(video_out_path)[0] + ".gif"


def gif_argv(video_path, out_path, fps=GIF_FPS, max_width=GIF_MAX_WIDTH):
    """Argv for the single `ffmpeg` pass that turns `video_path` into an
    animated GIF at `out_path`: resampled to `fps`, downscaled to at most
    `max_width` wide (height following proportionally, `-2` keeping it
    even), through a generated-palette filter graph for reasonable size and
    quality in one pass. Pure — no I/O."""
    filter_complex = (
        "fps=%d,scale=%d:-2:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=stats_mode=diff[p];"
        "[s1][p]paletteuse=dither=bayer" % (fps, max_width))
    return ["ffmpeg", "-y", "-i", video_path, "-vf", filter_complex,
           out_path]


def write_gif(video_path, out_path, run, fps=GIF_FPS,
             max_width=GIF_MAX_WIDTH):
    """Write an animated GIF of `video_path` to `out_path` through `run`
    (the injectable subprocess seam). Raises `RuntimeError` on failure.
    Returns `out_path`."""
    rc, out, err = run(gif_argv(video_path, out_path, fps, max_width))
    if rc != 0:
        raise RuntimeError(
            "ffmpeg failed writing the animated GIF %s: %s"
            % (out_path, (err or out).strip()))
    return out_path


def assemble(video_path, timeline, out_path, run, workdir=None,
            backstop_spans=None, title_card_path=None, badge_path=None,
            badge_corner="bottom-right", width=1280, height=720, gif=False):
    """Assemble the finished, branded, fast-forwarded video from
    `video_path` and its `timeline` (`record_worker.py`'s `spans`/`holds`/
    `leadingCut`, drive-recording), per drive-postprocess: cut the leading
    boot, encode every `build_segments` segment at normal or `FF_SPEED`,
    composite the fast-forward badge over the fast-forwarded segments only,
    prepend the title card when `title_card_path` is given, concatenate,
    and write `out_path`. Every step shells out through `run` (the
    injectable subprocess seam `default_run`'s signature); nothing above
    this function in the module does. When `gif` is true, additionally
    writes an animated GIF of the finished output beside it (`gif_path`,
    `write_gif`) — drive-postprocess's inline-embeddable output option.
    Returns `out_path` when `gif` is false, otherwise `(out_path,
    gif_path)`.
    """
    own_workdir = workdir is None
    if own_workdir:
        workdir = tempfile.mkdtemp(prefix="drive-post-")
    try:
        duration = probe_duration(video_path, run)
        detected_start = detect_content_start(video_path, run)
        leading_cut = resolve_leading_cut(
            timeline.get("leadingCut"), detected_start)
        leading_cut = max(0.0, min(leading_cut, duration))

        spans = _shift_and_clip(timeline.get("spans") or [], leading_cut)
        holds = _shift_and_clip(timeline.get("holds") or [], leading_cut)
        backstop = _shift_and_clip(backstop_spans or [], leading_cut)

        ff_spans = compute_ff_spans(spans, holds=holds,
                                    backstop_spans=backstop)
        body_duration = max(0.0, duration - leading_cut)
        segments = build_segments(body_duration, ff_spans)

        badge_x, badge_y = badge_position(badge_corner, width, height)

        clip_paths = []
        if title_card_path:
            card_clip = os.path.join(workdir, "title-card.mp4")
            rc, out, err = run(title_card_clip_argv(
                title_card_path, TITLE_CARD_DURATION_SECONDS, card_clip,
                width, height))
            if rc != 0:
                raise RuntimeError(
                    "ffmpeg failed rendering the title card clip: %s"
                    % (err or out).strip())
            clip_paths.append(card_clip)

        for i, seg in enumerate(segments):
            clip_path = os.path.join(workdir, "segment-%03d.mp4" % i)
            seg_badge = badge_path if seg["speed"] == FF_SPEED else None
            argv = segment_clip_argv(
                video_path, leading_cut + seg["start"],
                leading_cut + seg["end"], seg["speed"], clip_path,
                badge_path=seg_badge, badge_x=badge_x, badge_y=badge_y)
            rc, out, err = run(argv)
            if rc != 0:
                raise RuntimeError(
                    "ffmpeg failed encoding segment %d (%.2fs-%.2fs @ "
                    "%sx): %s" % (i, seg["start"], seg["end"], seg["speed"],
                                 (err or out).strip()))
            clip_paths.append(clip_path)

        list_path = os.path.join(workdir, "concat.txt")
        write_concat_list(clip_paths, list_path)
        rc, out, err = run(concat_argv(list_path, out_path, width, height))
        if rc != 0:
            raise RuntimeError(
                "ffmpeg failed concatenating the output: %s"
                % (err or out).strip())

        if gif:
            gif_path = gif_path_for(out_path)
            write_gif(out_path, gif_path, run)
    finally:
        if own_workdir:
            shutil.rmtree(workdir, ignore_errors=True)

    if gif:
        return out_path, gif_path
    return out_path
