#!/usr/bin/env python3
"""video_ingest.py — turn a screen recording into a transcript bundle,
entirely on the local machine (stdlib only, no direct third-party imports).

Every dependency crosses a process boundary: `ffmpeg`/`ffprobe` as CLIs, and
transcription as a separate `uv run` script carrying PEP 723 inline
dependency metadata (video-backend-adapters). Every subprocess call — `ffmpeg`,
`ffprobe`, `uv`, `brew` — goes through an injectable runner with signature
``run(args, input=None) -> (rc, stdout, stderr)``, so the test suite exercises
the orchestrator with no `ffmpeg`, `uv`, or `mlx` installed
(video-pipeline-testability).

Subcommands:
  doctor [--fix]     report each prerequisite's state, install the required
                     ones and pre-warm backend model caches under --fix
  ingest <video>     extract audio, transcribe, extract frames, and write
                     the bundle
  path <slug>        print the absolute bundle directory for a slug

Bundle contract (video-bundle-contract): each ingest writes
``<video-root>/<slug>/`` holding ``manifest.json``, ``audio.wav``,
``transcript.json``, ``frames.json``, and a ``frames/`` directory holding the
extracted keyframes (empty when no candidate survives selection).
``<video-root>`` resolves from the layered configuration's ``build.video_dir``
key, home-expanded, defaulting to ``~/.shipd/video`` — a location outside any
repository, mirroring ``design.py``'s ``build.design_dir`` resolution. An
existing bundle directory is refused unless ``--force``.
"""

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKENDS_DIR = os.path.join(SCRIPTS_DIR, "backends")


class VideoIngestError(Exception):
    """A user-facing error: printed as ``Error: ...`` to stderr, exit 1."""


def _build_scripts_dir():
    """Absolute path to the build skill's scripts/ (the cross-skill engine
    import point — the established convention, per semdiff.py)."""
    return os.path.normpath(os.path.join(SCRIPTS_DIR, "..", "..", "build", "scripts"))


DEFAULT_VIDEO_DIR = "~/.shipd/video"
DEFAULT_ASR = "parakeet"


def video_config(project_dir="."):
    """Return the effective video-ingest settings: the resolved layered
    configuration's ``build.video_dir`` key (default ``~/.shipd/video``,
    video-bundle-contract), its ``build.video_asr`` key (default
    ``parakeet``, video-backend-adapters), and its ``build.video_vocabulary``
    key (default ``[]``, video-vocabulary-biasing), its
    ``build.video_max_frames`` key (default 24, video-frame-budget), its
    ``build.video_scene_floor`` key (default `SCENE_FLOOR_FRACTION`,
    video-frame-budget), and its ``build.video_cursor`` key (default
    ``True``, video-cursor-crops).

    Read-only — a missing config, a missing ``build`` key, or an unreadable
    config yields the defaults, so callers always proceed."""
    settings = {"video_dir": DEFAULT_VIDEO_DIR, "asr": DEFAULT_ASR,
               "vocabulary": [], "max_frames": DEFAULT_VIDEO_MAX_FRAMES,
               "scene_floor": SCENE_FLOOR_FRACTION, "video_cursor": True}
    try:
        build = _build_scripts_dir()
        if build not in sys.path:
            sys.path.insert(0, build)
        import spec_common as sc  # noqa: WPS433 (local import by design)
        config, _prov = sc.resolve_config(os.path.abspath(project_dir))
    except Exception:  # noqa: BLE001 - config resolution is best-effort
        return settings
    build_cfg = config.get("build")
    if isinstance(build_cfg, dict):
        if build_cfg.get("video_dir"):
            settings["video_dir"] = build_cfg["video_dir"]
        if build_cfg.get("video_asr"):
            settings["asr"] = build_cfg["video_asr"]
        if build_cfg.get("video_vocabulary"):
            settings["vocabulary"] = build_cfg["video_vocabulary"]
        if build_cfg.get("video_max_frames"):
            settings["max_frames"] = build_cfg["video_max_frames"]
        if build_cfg.get("video_scene_floor") is not None:
            settings["scene_floor"] = build_cfg["video_scene_floor"]
        if build_cfg.get("video_cursor") is not None:
            settings["video_cursor"] = bool(build_cfg["video_cursor"])
    return settings


def video_root(config):
    """Return the resolved video bundle root (default ``~/.shipd/video``),
    home-expanded."""
    return os.path.expanduser(config.get("video_dir") or DEFAULT_VIDEO_DIR)


def bundle_dir(slug, config):
    """Return the absolute per-slug bundle directory."""
    return os.path.join(video_root(config), slug)


def ensure_bundle_dir(path, force):
    """Create the bundle directory layout at ``path`` (video-bundle-contract):
    the directory itself plus an empty ``frames/`` subdirectory.

    Refuses when ``path`` already exists unless ``force`` is given, in which
    case the existing directory is removed first — an existing-and-refused
    bundle is left completely untouched. Returns ``path``."""
    if os.path.exists(path):
        if not force:
            raise VideoIngestError(
                "bundle already exists: %s (pass --force to overwrite)"
                % path)
        shutil.rmtree(path)
    os.makedirs(os.path.join(path, "frames"))
    return path


def write_manifest(path, manifest):
    """Write ``manifest.json`` into the bundle directory ``path``."""
    with open(os.path.join(path, "manifest.json"), "w",
             encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")


# --- default (production) subprocess seam -----------------------------------


def default_run(args, input=None):
    """Real subprocess runner: ``args`` is a full argv (e.g. ``["ffmpeg",
    ...]``). Returns ``(rc, stdout, stderr)``. Tests substitute a fake with the
    same signature so the orchestrator never needs a real toolchain
    (video-pipeline-testability)."""
    proc = subprocess.run(
        list(args), input=input, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


# --- slug derivation -----------------------------------------------------

_SEPARATOR_RUN = re.compile(r"[^A-Za-z0-9]+")


def derive_slug(filename):
    """Derive a bundle slug from a source filename (video-audio-extraction):
    the basename without its extension, with Unicode whitespace (macOS writes
    a U+202F narrow no-break space before am/pm in a recording's timestamp)
    and every other non-alphanumeric run folded to a single ``-``, lowercased
    and stripped of leading/trailing separators. Pure — no I/O."""
    base = os.path.splitext(os.path.basename(filename))[0]
    return _SEPARATOR_RUN.sub("-", base).strip("-").lower()


# --- audio extraction ----------------------------------------------------


def probe_argv(video_path):
    """Argv for the single `ffprobe` call that reports both duration and
    stream layout as JSON. The path is one argv element — never interpolated
    into a shell string (video-audio-extraction)."""
    return ["ffprobe", "-v", "error", "-print_format", "json",
           "-show_format", "-show_streams", video_path]


def probe_media(video_path, run):
    """Run `ffprobe` on ``video_path`` through the injectable runner.
    Returns ``(has_audio, duration)``. Raises :class:`VideoIngestError` if
    `ffprobe` exits non-zero or prints unparseable output."""
    rc, stdout, stderr = run(probe_argv(video_path))
    if rc != 0:
        raise VideoIngestError(
            "ffprobe failed on %s: %s" % (video_path, stderr.strip()))
    try:
        data = json.loads(stdout)
    except ValueError as exc:
        raise VideoIngestError(
            "ffprobe printed unparseable output for %s: %s"
            % (video_path, exc))
    streams = data.get("streams", [])
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    try:
        duration = float(data.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration = 0.0
    return has_audio, duration


def probe_video_dimensions(video_path, run):
    """Run `ffprobe` on ``video_path`` through the injectable runner and
    return its video stream's ``(width, height)``, or ``None`` if no video
    stream or dimensions can be determined (video-cursor-crops). Mirrors
    `probe_media`'s JSON shape but reports dimensions rather than
    audio/duration — kept as a separate function so `probe_media`'s
    existing ``(has_audio, duration)`` signature, depended on elsewhere,
    never changes. A source whose dimensions cannot be determined simply
    skips the cursor stage rather than failing the ingest."""
    rc, stdout, _stderr = run(probe_argv(video_path))
    if rc != 0:
        return None
    try:
        data = json.loads(stdout)
    except ValueError:
        return None
    for stream in data.get("streams", []):
        if stream.get("codec_type") != "video":
            continue
        width, height = stream.get("width"), stream.get("height")
        if isinstance(width, int) and isinstance(height, int) \
                and width > 0 and height > 0:
            return width, height
    return None


def extract_audio_argv(video_path, wav_path):
    """Argv for the `ffmpeg` call that extracts ``video_path``'s audio to
    16 kHz mono PCM WAV at ``wav_path``. Pure — no I/O. Every path is its own
    argv element, never a shell string (video-audio-extraction)."""
    return ["ffmpeg", "-y", "-i", video_path, "-vn",
           "-ar", "16000", "-ac", "1", wav_path]


def extract_audio(video_path, wav_path, run):
    """Probe ``video_path`` for an audio stream, then extract it to 16 kHz
    mono PCM WAV at ``wav_path`` through the injectable runner. Returns the
    source duration in seconds. Refuses (raises :class:`VideoIngestError`,
    never invoking `ffmpeg`) when the video carries no audio stream."""
    has_audio, duration = probe_media(video_path, run)
    if not has_audio:
        raise VideoIngestError(
            "no audio stream found in %s" % video_path)
    rc, _stdout, stderr = run(extract_audio_argv(video_path, wav_path))
    if rc != 0:
        raise VideoIngestError(
            "ffmpeg failed extracting audio from %s: %s"
            % (video_path, stderr.strip()))
    return duration


# --- backend selection and invocation -------------------------------------

# (kind, name) -> script path. `kind` is "asr".
BACKEND_SCRIPTS = {
    ("asr", "parakeet"): os.path.join(BACKENDS_DIR, "asr_parakeet.py"),
    ("asr", "whisper"): os.path.join(BACKENDS_DIR, "asr_whisper.py"),
}


def resolve_backends(args, config):
    """Resolve the ASR backend name: a CLI flag wins, else the resolved
    configuration's `asr` key (video-backend-adapters)."""
    return args.asr or config.get("asr", DEFAULT_ASR)


def backend_script(kind, name):
    """Resolve ``(kind, name)`` to its backend script path."""
    try:
        return BACKEND_SCRIPTS[(kind, name)]
    except KeyError:
        raise VideoIngestError("unknown %s backend: %s" % (kind, name))


def backend_argv(script, audio_path, vocabulary=None):
    """Argv for invoking a backend script through `uv run`. Where
    ``vocabulary`` is a non-empty list of terms, appends `--vocab
    <comma-joined terms>` (video-vocabulary-biasing) — every ASR backend
    accepts the option per the backend contract (video-backend-adapters), so
    it is safe to pass to any backend. Pure — no I/O. Every path is its own
    argv element, never a shell string."""
    argv = ["uv", "run", script, "--audio", audio_path]
    if vocabulary:
        argv.extend(["--vocab", ",".join(vocabulary)])
    return argv


def backend_failure_detail(rc, stderr):
    """Describe a backend's non-zero exit: its stderr where it wrote any, and
    always the exit status itself.

    A backend killed by a signal — most importantly SIGKILL from the kernel's
    out-of-memory killer — writes no diagnostic at all, so its stderr holds
    only whatever incidental noise its dependencies logged (an HF Hub rate
    limit warning, say). Reporting that noise alone names a warning as the
    cause of the failure and hides the kill. So the status is always carried,
    and a signal is named as such. Pure — no I/O."""
    status = ("killed by signal %d" % -rc) if rc < 0 else ("exit %d" % rc)
    detail = stderr.strip()
    return "%s (%s)" % (detail, status) if detail else status


def run_backend(script, audio_path, run, vocabulary=None):
    """Invoke a backend script through the injectable runner, returning its
    parsed JSON object. Raises :class:`VideoIngestError` carrying the
    backend's stderr and exit status on a non-zero exit, or its unparseable
    stdout (video-backend-adapters)."""
    rc, stdout, stderr = run(backend_argv(script, audio_path, vocabulary))
    if rc != 0:
        raise VideoIngestError(
            "backend %s failed: %s" % (script, backend_failure_detail(rc, stderr)))
    try:
        data = json.loads(stdout)
    except ValueError as exc:
        raise VideoIngestError(
            "backend %s printed unparseable output: %s" % (script, exc))
    if not isinstance(data, dict):
        raise VideoIngestError(
            "backend %s did not print a JSON object" % script)
    return data


# --- transcript assembly ---------------------------------------------------

TRANSCRIPT_SCHEMA_VERSION = 1


def build_transcript(words):
    """Build the `transcript.json` document: a schema `version` plus a
    `words` array of `start`/`end`/`text` entries, ordered by `start`
    (video-transcript-schema). No `segments` key and no speaker field —
    ``words`` is sorted by ``start`` first, so the output is ordered
    regardless of input order."""
    ordered = sorted(words, key=lambda w: w["start"])
    return {
        "version": TRANSCRIPT_SCHEMA_VERSION,
        "words": [{"start": w["start"], "end": w["end"], "text": w["text"]}
                 for w in ordered],
    }


def write_transcript(path, words):
    """Write `transcript.json` into the bundle directory ``path``."""
    with open(os.path.join(path, "transcript.json"), "w",
             encoding="utf-8") as fh:
        json.dump(build_transcript(words), fh, indent=2)
        fh.write("\n")


# --- frame candidates: deixis anchors ---------------------------------------

# Spatial demonstratives: a speaker uses one of these to point at something on
# screen. `it` is deliberately excluded — it is anaphoric (refers back to
# something already named), not a gesture at the screen (video-deixis-anchors).
DEIXIS_WORDS = {"this", "that", "these", "those", "here", "there"}

# A speaker points slightly before and after speaking the anchor word, so each
# anchor contributes a small window of candidates around its start time.
DEIXIS_WINDOW_BEFORE_SECONDS = 0.5
DEIXIS_WINDOW_AFTER_SECONDS = 1.5

_WORD_NORMALIZE = re.compile(r"[^a-z0-9]+")


def _normalize_word(text):
    """Lowercase ``text`` and strip non-alphanumeric characters, so
    punctuation and capitalization never prevent a deixis match."""
    return _WORD_NORMALIZE.sub("", text.lower())


def deixis_candidates(words, duration):
    """Derive frame candidates from the attributed transcript's spatial
    demonstratives (video-deixis-anchors). Each matched word at time `t`
    contributes candidates at `t-0.5`, `t` and `t+1.5` seconds, each clamped
    to `[0, duration]`. Pure — no I/O.

    Returns a list of candidate dicts: `time`, `reason="deixis"`, `anchor`
    (the matched word), `word_start` (the word's own start time)."""
    candidates = []
    for word in words:
        if _normalize_word(word.get("text", "")) not in DEIXIS_WORDS:
            continue
        start = word["start"]
        anchor = _normalize_word(word["text"])
        for offset in (-DEIXIS_WINDOW_BEFORE_SECONDS, 0.0,
                      DEIXIS_WINDOW_AFTER_SECONDS):
            time = min(max(start + offset, 0.0), duration)
            candidates.append({
                "time": time,
                "reason": "deixis",
                "anchor": anchor,
                "word_start": start,
            })
    return candidates


# --- frame candidates: scene peaks ------------------------------------------

_PTS_TIME_RE = re.compile(r"pts_time:(-?[0-9.]+)")
_SCENE_SCORE_RE = re.compile(r"lavfi\.scene_score=(-?[0-9.]+)")


def parse_scene_scores(text):
    """Parse `ffmpeg`'s `metadata=print` output into ordered `(time, score)`
    pairs (video-scene-peaks). Each frame prints a `pts_time:<t>` line
    followed by a `lavfi.scene_score=<s>` line; any other line is ignored.
    Pure — no I/O."""
    pairs = []
    pending_time = None
    for line in text.splitlines():
        time_match = _PTS_TIME_RE.search(line)
        if time_match:
            pending_time = float(time_match.group(1))
            continue
        score_match = _SCENE_SCORE_RE.search(line)
        if score_match and pending_time is not None:
            pairs.append((pending_time, float(score_match.group(1))))
            pending_time = None
    return pairs


# 1.0s: local scene-score maxima closer together than this collapse to the
# higher-scoring one. 10.0s: one scene-derived frame is kept per this many
# seconds of recording (video-scene-peaks). Absolute scene-score thresholds
# (e.g. the conventional `gt(scene,0.3)`) do not work on screen recordings —
# measured on the reference recording, the real transitions score 0.046-0.054
# against a next-highest of 0.0017, a 27x gap, but the *maximum* score in the
# whole recording is only 0.0535. Peaks are therefore ranked within the
# recording, never against a constant.
SCENE_PEAK_MIN_GAP_SECONDS = 1.0
SCENE_PEAK_SECONDS_PER_FRAME = 10.0


def scene_candidates(scores, duration):
    """Derive frame candidates from `(time, score)` pairs (video-scene-peaks):
    keep local maxima (a frame scoring above both neighbours) with a non-zero
    score, collapse maxima closer than `SCENE_PEAK_MIN_GAP_SECONDS` to the
    higher-scoring one, and keep at most
    `ceil(duration / SCENE_PEAK_SECONDS_PER_FRAME)` of them ranked by
    descending score. Never compares scores against an absolute threshold.
    Pure — no I/O.

    Returns a list of candidate dicts: `time`, `reason="scene"`, `score`,
    ordered by ascending time."""
    maxima = []
    for i in range(1, len(scores) - 1):
        time, score = scores[i]
        if score <= 0:
            continue
        if score > scores[i - 1][1] and score > scores[i + 1][1]:
            maxima.append((time, score))

    # Collapse maxima within the minimum separation, keeping the
    # higher-scoring one: scan in time order, and whenever a candidate falls
    # within the gap of the last *kept* one, keep whichever scores higher.
    collapsed = []
    for time, score in maxima:
        if (collapsed and
                time - collapsed[-1][0] < SCENE_PEAK_MIN_GAP_SECONDS):
            if score > collapsed[-1][1]:
                collapsed[-1] = (time, score)
        else:
            collapsed.append((time, score))

    max_peaks = math.ceil(duration / SCENE_PEAK_SECONDS_PER_FRAME) if duration > 0 else 0
    kept = sorted(collapsed, key=lambda ts: -ts[1])[:max_peaks]
    kept.sort(key=lambda ts: ts[0])
    return [{"time": time, "reason": "scene", "score": score}
           for time, score in kept]


def scene_scores_argv(video_path):
    """Argv for the single `ffmpeg` pass that scores every frame's scene
    change against its predecessor and prints the scores to stdout, without
    writing any video output (video-scene-peaks). Pure — no I/O."""
    return ["ffmpeg", "-i", video_path, "-filter:v",
           "select='gte(scene,0)',metadata=print:file=-",
           "-f", "null", "-"]


def compute_scene_scores(video_path, run):
    """Run the scene-scoring `ffmpeg` pass on ``video_path`` through the
    injectable runner and parse its stdout into `(time, score)` pairs via
    :func:`parse_scene_scores` (video-scene-peaks). Raises
    :class:`VideoIngestError` if `ffmpeg` exits non-zero."""
    rc, stdout, stderr = run(scene_scores_argv(video_path))
    if rc != 0:
        raise VideoIngestError(
            "ffmpeg failed computing scene scores for %s: %s"
            % (video_path, stderr.strip()))
    return parse_scene_scores(stdout)


# --- frame candidates: merge, dedup and cap ---------------------------------

# 0.5s: a candidate within this of an already-kept one collapses into it,
# keeping the earlier (video-frame-budget).
FRAME_DEDUP_MIN_GAP_SECONDS = 0.5

DEFAULT_VIDEO_MAX_FRAMES = 24

# 0.25: the fraction of the frame cap reserved for scene candidates, so a
# recording dense in deixis anchors cannot starve every scene-change frame
# (video-frame-budget). Overridable via `build.video_scene_floor`.
SCENE_FLOOR_FRACTION = 0.25


def _frame_candidate_rank(candidate):
    """Sort key ranking a frame candidate for selection preference, both as
    a bucket's single winner and during backfill (video-frame-budget): a
    deixis candidate always outranks a scene candidate; among candidates of
    the same reason, the earlier deixis anchor wins and the higher-scoring
    scene peak wins. Lower sorts first == more preferred. Pure."""
    if candidate["reason"] == "deixis":
        return (0, candidate["time"])
    return (1, -candidate["score"])


def resolve_frame_candidates(deixis, scene, max_frames, duration,
                             scene_floor=SCENE_FLOOR_FRACTION):
    """Merge deixis and scene frame candidates, dedup, and cap by
    distributing the budget across the recording (video-frame-budget).
    Candidates are sorted by time and a candidate within
    `FRAME_DEDUP_MIN_GAP_SECONDS` of an already-kept one is dropped, keeping
    the earlier.

    If the deduped candidates do not exceed `max_frames`, every one is kept.
    Otherwise `duration` is divided into `max_frames` equal-width buckets and
    each occupied bucket contributes at most one candidate — its highest
    -ranked one per `_frame_candidate_rank` — so the kept frames spread
    across the whole recording instead of clustering wherever candidates are
    densest. Buckets left empty (or whose loser candidates are unused) leave
    slots that are backfilled from the remaining candidates, highest-ranked
    first, so a sparse recording still yields as many frames as the
    candidates allow.

    The selection then reserves a scene floor: where the kept set holds
    fewer scene candidates than `int(max_frames * scene_floor)`, buckets
    whose winner is a deixis candidate and which also hold a scene candidate
    are converted to that bucket's highest-scoring scene candidate, taken
    highest-scoring first, until the floor is met or no convertible bucket
    remains — never exceeding the number of scene candidates available and
    never changing the kept count.

    Every candidate dropped by the cap is written to stderr with its
    timestamp and reason.

    Pure aside from the stderr write. Returns `(kept, dropped)`, each a list
    of candidate dicts; `kept` is ordered by time."""
    merged = sorted(deixis + scene, key=lambda c: c["time"])
    deduped = []
    for candidate in merged:
        if (deduped and candidate["time"] - deduped[-1]["time"]
                < FRAME_DEDUP_MIN_GAP_SECONDS):
            continue
        deduped.append(candidate)

    if max_frames <= 0:
        for candidate in deduped:
            print("video_ingest: dropped frame candidate at %.2fs (%s) — "
                  "over the %d-frame cap" % (candidate["time"],
                                             candidate["reason"],
                                             max_frames), file=sys.stderr)
        return [], deduped

    if len(deduped) <= max_frames:
        return sorted(deduped, key=lambda c: c["time"]), []

    bucket_width = duration / max_frames if duration > 0 else 0

    def bucket_index(candidate):
        if bucket_width <= 0:
            return 0
        return min(int(candidate["time"] / bucket_width), max_frames - 1)

    buckets = {}
    for candidate in deduped:
        buckets.setdefault(bucket_index(candidate), []).append(candidate)

    selected = []
    leftover = []
    bucket_winner_pos = {}
    for index, group in buckets.items():
        winner = min(group, key=_frame_candidate_rank)
        bucket_winner_pos[index] = len(selected)
        selected.append(winner)
        leftover.extend(c for c in group if c is not winner)

    remaining_slots = max(max_frames - len(selected), 0)
    leftover_by_rank = sorted(leftover, key=_frame_candidate_rank)
    selected.extend(leftover_by_rank[:remaining_slots])
    dropped = leftover_by_rank[remaining_slots:]

    floor = int(max_frames * scene_floor)
    scene_count = sum(1 for c in selected if c["reason"] == "scene")
    if scene_count < floor:
        selected_ids = {id(c) for c in selected}
        convertible = []
        for index, pos in bucket_winner_pos.items():
            if selected[pos]["reason"] != "deixis":
                continue
            scene_members = [c for c in buckets[index]
                             if c["reason"] == "scene"
                             and id(c) not in selected_ids]
            if not scene_members:
                continue
            best_scene = max(scene_members, key=lambda c: c["score"])
            convertible.append((pos, best_scene))
        convertible.sort(key=lambda item: -item[1]["score"])
        for pos, best_scene in convertible:
            if scene_count >= floor:
                break
            displaced = selected[pos]
            selected[pos] = best_scene
            scene_count += 1
            for i, candidate in enumerate(dropped):
                if candidate is best_scene:
                    del dropped[i]
                    break
            dropped.append(displaced)

    for candidate in dropped:
        print("video_ingest: dropped frame candidate at %.2fs (%s) — over "
             "the %d-frame cap" % (candidate["time"], candidate["reason"],
                                   max_frames), file=sys.stderr)

    kept = sorted(selected, key=lambda c: c["time"])
    return kept, dropped


# --- pointer localization ----------------------------------------------------

# 960px: the working width the differencing pass scales to, making cost
# independent of source resolution — the cursor's tile energy collapses at
# 640px (25) but survives at 960px (272), at ~0.23s/frame (plan.md).
CURSOR_WORK_WIDTH = 960

# 0.2s: the short baseline that isolates the pointer from the app's own
# slower redraws — `diff(t-0.2, t)` peaks on the true cursor (energy 1847 vs
# 64) where `diff(t-1.0, t)` is dominated by a ticking counter (4035 vs the
# cursor's 2728) (plan.md).
CURSOR_DIFF_STEP_SECONDS = 0.2

# 4 grayscale frames spaced CURSOR_DIFF_STEP_SECONDS apart yield 3
# differences: two "earlier" ones (the persistent-churn mask) and the last
# one the pointer is read from (plan.md).
CURSOR_DIFF_FRAMES = 4

# 16px tiles: the differencing grid granularity underlying every gate below.
CURSOR_TILE = 16

# 24: a pixel must move by more than this (0-255 grayscale) to accumulate
# into its tile's energy — filters out compression noise.
CURSOR_PIXEL_DELTA = 24

# 0.15: a tile's energy must exceed this fraction of the difference's
# strongest tile to count as changed at all — relative, never absolute, the
# same lesson video-scene-peaks already encodes (plan.md).
CURSOR_RELATIVE_FLOOR = 0.15

# 3 tiles: the largest span (per dimension) a pointer-sized region may cover
# — a modal redraw at t=30.0 yields 240x48px regions, far larger (plan.md).
CURSOR_MAX_SPAN_TILES = 3

# 2.0x: the winning region's energy must exceed every other changed region's
# by this factor — raw differencing alone is not enough (plan.md).
CURSOR_DOMINANCE = 2.0

# 0.6s: the window's own span — the distance from its first frame to its
# last. A frame earlier than this has no full window ending on it, so
# `locate_cursors` declines rather than differencing a window that ends
# *after* the frame it is grounding.
CURSOR_WINDOW_SPAN_SECONDS = ((CURSOR_DIFF_FRAMES - 1)
                              * CURSOR_DIFF_STEP_SECONDS)


def cursor_window_argv(video_path, time, out_path, width, height):
    """Argv for the single `ffmpeg` pass that writes `CURSOR_DIFF_FRAMES`
    grayscale frames spaced `CURSOR_DIFF_STEP_SECONDS` apart, the last one at
    `time`, scaled to `width`x`height`, as raw pixel bytes to `out_path`
    (video-cursor-localization). Pure — no I/O. Every path is its own argv
    element, never a shell string.

    `time` must be at least `CURSOR_WINDOW_SPAN_SECONDS`, which
    `locate_cursors` enforces: an earlier `time` has no room for the window
    before it, and clamping the start to 0 would silently ground the frame on
    pixels from *after* its own timestamp.

    Raw pixels never cross the text runner: this pass writes them to a file
    (`read_gray_frames` reads them back as bytes) rather than returning them
    through the runner's stdout, which `default_run` decodes as text."""
    span = CURSOR_WINDOW_SPAN_SECONDS
    start = max(0.0, time - span)
    duration = CURSOR_DIFF_FRAMES * CURSOR_DIFF_STEP_SECONDS
    fps = 1.0 / CURSOR_DIFF_STEP_SECONDS
    return ["ffmpeg", "-y", "-ss", "%s" % start, "-i", video_path,
           "-t", "%s" % duration, "-vf",
           "fps=%g,scale=%d:%d" % (fps, width, height),
           "-pix_fmt", "gray", "-f", "rawvideo", out_path]


def read_gray_frames(path, width, height):
    """Read the grayscale rawvideo bytes `cursor_window_argv`'s `ffmpeg` pass
    wrote to `path` and split them into `width * height`-byte frame buffers,
    oldest first (video-cursor-localization). Any trailing partial frame
    (a short final write) is dropped rather than yielding a mismatched
    buffer."""
    frame_size = width * height
    with open(path, "rb") as fh:
        data = fh.read()
    return [data[offset:offset + frame_size]
           for offset in range(0, len(data) - frame_size + 1, frame_size)]


def tile_difference(a, b, width, height):
    """Per-tile accumulated absolute pixel difference between two
    working-scale grayscale buffers `a` and `b` (video-cursor-localization):
    for each pixel whose absolute difference exceeds `CURSOR_PIXEL_DELTA`,
    the full difference accumulates into its `CURSOR_TILE`x`CURSOR_TILE`
    tile — pixels at or below the delta contribute nothing. Returns a flat
    list of tile energies, row-major over the tile grid (`ceil(width /
    CURSOR_TILE)` tiles wide). Pure — no I/O."""
    tile_cols = -(-width // CURSOR_TILE)
    tile_rows = -(-height // CURSOR_TILE)
    energies = [0] * (tile_cols * tile_rows)
    for y in range(height):
        row = y * width
        tile_row_base = (y // CURSOR_TILE) * tile_cols
        for x in range(width):
            diff = a[row + x] - b[row + x]
            if diff < 0:
                diff = -diff
            if diff > CURSOR_PIXEL_DELTA:
                energies[tile_row_base + x // CURSOR_TILE] += diff
    return energies


def changed_regions(tiles, banned, floor, width):
    """Group `tiles` (a flat, row-major list of per-tile energies `width`
    tiles wide, as returned by `tile_difference`) into 8-connected regions,
    excluding any tile index in `banned` and any tile at or below `floor`
    (video-cursor-localization). Each region carries its tile bounding box
    (`min_row`, `max_row`, `min_col`, `max_col`, inclusive), the set of
    member tile indices (`tiles`), and `energy` (the sum of its member
    tiles' energies), ordered by descending energy. Pure — no I/O."""
    active = {index for index, energy in enumerate(tiles)
             if energy > floor and index not in banned}
    visited = set()
    regions = []
    for start in active:
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        members = []
        while stack:
            index = stack.pop()
            members.append(index)
            row, col = divmod(index, width)
            for drow in (-1, 0, 1):
                for dcol in (-1, 0, 1):
                    if drow == 0 and dcol == 0:
                        continue
                    ncol = col + dcol
                    if ncol < 0 or ncol >= width:
                        continue
                    neighbor = (row + drow) * width + ncol
                    if neighbor in active and neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
        rows = [member // width for member in members]
        cols = [member % width for member in members]
        regions.append({
            "tiles": set(members),
            "min_row": min(rows), "max_row": max(rows),
            "min_col": min(cols), "max_col": max(cols),
            "energy": sum(tiles[member] for member in members),
        })
    regions.sort(key=lambda region: -region["energy"])
    return regions


def _region_span(region):
    """A region's tile span in each dimension, inclusive of both edges."""
    return (region["max_row"] - region["min_row"] + 1,
           region["max_col"] - region["min_col"] + 1)


def _tile_bbox_to_pixels(region, width, height):
    """A region's tile bounding box translated to working-scale pixel
    coordinates, clamped to `width`x`height`."""
    x0 = region["min_col"] * CURSOR_TILE
    y0 = region["min_row"] * CURSOR_TILE
    x1 = min((region["max_col"] + 1) * CURSOR_TILE, width)
    y1 = min((region["max_row"] + 1) * CURSOR_TILE, height)
    return x0, y0, x1 - x0, y1 - y0


def locate_pointer(frames, width, height, source_size):
    """Locate the pointer among `CURSOR_DIFF_FRAMES` working-scale grayscale
    buffers `frames`, oldest first, ending at the target time
    (video-cursor-localization). Applies the four gates in order to the last
    of the three successive differences:

    (a) span — a region wider or taller than `CURSOR_MAX_SPAN_TILES` tiles
        is never a pointer, as a modal redraw's region is;
    (b) persistent churn — tiles active (above their own difference's
        relative floor) in *both* earlier differences are excluded before
        grouping, removing a ticking counter that changes on every
        difference;
    (c) uniqueness — the sole surviving region wins outright; where several
        survive, the sole one absent from the preceding difference wins
        (the others being the pointer's own trailing positions), else no
        position is reported;
    (d) dominance — the winner's energy must exceed every other changed
        region's (of the same, last difference) by `CURSOR_DOMINANCE`.

    Returns a dict of `x`, `y`, `w`, `h` mapped to `source_size` pixel
    coordinates, or `None` if no region satisfies all four gates. Pure — no
    I/O."""
    tile_cols = -(-width // CURSOR_TILE)
    diffs = [tile_difference(frames[i], frames[i + 1], width, height)
             for i in range(len(frames) - 1)]
    earlier, last = diffs[:-1], diffs[-1]

    def above_floor(energies):
        peak = max(energies) if energies else 0
        if peak <= 0:
            return set()
        floor = CURSOR_RELATIVE_FLOOR * peak
        return {i for i, e in enumerate(energies) if e > floor}

    earlier_active = [above_floor(d) for d in earlier]
    banned = set.intersection(*earlier_active) if earlier_active else set()

    last_peak = max(last) if last else 0
    if last_peak <= 0:
        return None
    last_floor = CURSOR_RELATIVE_FLOOR * last_peak

    regions = changed_regions(last, banned, last_floor, tile_cols)
    if not regions:
        return None

    sized = [r for r in regions
            if _region_span(r)[0] <= CURSOR_MAX_SPAN_TILES
            and _region_span(r)[1] <= CURSOR_MAX_SPAN_TILES]
    if not sized:
        return None

    if len(sized) == 1:
        winner = sized[0]
    else:
        preceding = earlier[-1] if earlier else []
        preceding_active = above_floor(preceding)
        preceding_tiles = set()
        if preceding_active:
            preceding_floor = CURSOR_RELATIVE_FLOOR * max(preceding)
            for region in changed_regions(preceding, set(), preceding_floor,
                                          tile_cols):
                preceding_tiles |= region["tiles"]
        absent = [r for r in sized if not (r["tiles"] & preceding_tiles)]
        if len(absent) != 1:
            return None
        winner = absent[0]

    others = [r["energy"] for r in regions if r is not winner]
    if others and winner["energy"] < max(others) * CURSOR_DOMINANCE:
        return None

    x, y, w, h = _tile_bbox_to_pixels(winner, width, height)
    source_width, source_height = source_size
    scale_x = source_width / width
    scale_y = source_height / height
    return {
        "x": round(x * scale_x), "y": round(y * scale_y),
        "w": round(w * scale_x), "h": round(h * scale_y),
    }


def region_unchanged(frame_a, frame_b, region, width, height):
    """Whether working-scale grayscale buffers `frame_a` and `frame_b`
    (each `width` x `height`) are byte-for-byte identical over `region`
    (`x`, `y`, `w`, `h`, working-scale pixel coordinates, clamped to the
    buffers' bounds) (video-cursor-carry-forward). Pure — no I/O."""
    x0 = max(0, region["x"])
    y0 = max(0, region["y"])
    x1 = min(width, region["x"] + region["w"])
    y1 = min(height, region["y"] + region["h"])
    for y in range(y0, y1):
        row = y * width
        if frame_a[row + x0:row + x1] != frame_b[row + x0:row + x1]:
            return False
    return True


def carry_pointer(previous, frame_a, frame_b, width, height, source_size,
                  from_time):
    """Carry `previous` — a `locate_pointer`-shaped `x`/`y`/`w`/`h` position
    in source pixel coordinates — forward to a new, inconclusive frame,
    verified rather than assumed (video-cursor-carry-forward): `frame_a` is
    the working-scale buffer of the frame `previous` was located on and
    `frame_b` is the new frame's working-scale buffer, both `width` x
    `height`; `source_size` maps `previous` back to that working scale for
    the byte-for-byte comparison via `region_unchanged`.

    Returns `previous` with `origin` set to `"carried"` and `from` set to
    `from_time` (the frame `previous` was carried from), or `None` when
    `previous` is `None` or the region changed between the two frames. Pure
    — no I/O."""
    if previous is None:
        return None
    source_width, source_height = source_size
    scale_x = width / source_width
    scale_y = height / source_height
    region = {
        "x": round(previous["x"] * scale_x),
        "y": round(previous["y"] * scale_y),
        "w": max(1, round(previous["w"] * scale_x)),
        "h": max(1, round(previous["h"] * scale_y)),
    }
    if not region_unchanged(frame_a, frame_b, region, width, height):
        return None
    carried = dict(previous)
    carried["origin"] = "carried"
    carried["from"] = from_time
    return carried


# 1/3: the crop window's width as a fraction of the source recording's
# width, at a 4:3 aspect — cropping the already downscaled frame PNG would
# discard the only detail that matters, so this crops the source instead
# (plan.md).
CURSOR_CROP_WIDTH_FRACTION = 1.0 / 3.0

# 960px: the crop's long edge after scaling — the tested
# `crop=480:360,scale=960:-2:flags=lanczos` made the I-beam and its target
# row unmistakable where the full frame did not (plan.md).
CURSOR_CROP_LONG_EDGE = 960


def cursor_crop_box(position, source_width, source_height):
    """The zoom-crop window for `position` (an `x`/`y`/`w`/`h` dict in
    source pixel coordinates, as `locate_pointer`/`carry_pointer` return):
    `CURSOR_CROP_WIDTH_FRACTION` of `source_width` at a 4:3 aspect, centred
    on the pointer and clamped into `source_width` x `source_height`
    (video-cursor-crops). Returns `x`, `y`, `w`, `h`. Pure — no I/O.

    The window's *size* is clamped before it is positioned: on a source wider
    than 4:1 — a multi-monitor span, say — the nominal 4:3 window is taller
    than the frame, and a box `ffmpeg` cannot crop would fail the whole
    ingest. The 4:3 aspect is preserved by shrinking width to match, so the
    box always fits inside the frame."""
    width = source_width * CURSOR_CROP_WIDTH_FRACTION
    height = width * 3.0 / 4.0
    if height > source_height:
        height = float(source_height)
        width = min(height * 4.0 / 3.0, float(source_width))
    center_x = position["x"] + position["w"] / 2.0
    center_y = position["y"] + position["h"] / 2.0
    x = center_x - width / 2.0
    y = center_y - height / 2.0
    x = min(max(x, 0.0), max(source_width - width, 0.0))
    y = min(max(y, 0.0), max(source_height - height, 0.0))
    return {
        "x": int(round(x)), "y": int(round(y)),
        "w": int(round(width)), "h": int(round(height)),
    }


def cursor_crop_filename(index, time):
    """Filename for the pointer crop at ordinal `index` (0-based, matching
    its full frame's own ordinal) and `time` seconds (video-cursor-crops).
    Pure — no I/O."""
    return "%03d-%.2fs-cursor.png" % (index, time)


def cursor_crop_argv(video_path, time, box, out_path):
    """Argv for the `ffmpeg` call that crops `box` (`x`, `y`, `w`, `h`,
    source pixel coordinates) out of `video_path` at `time` seconds and
    scales it to a `CURSOR_CROP_LONG_EDGE` long edge with lanczos
    (video-cursor-crops). Pure — no I/O. Every path is its own argv
    element, never a shell string."""
    crop = "crop=%d:%d:%d:%d" % (box["w"], box["h"], box["x"], box["y"])
    scale = "scale=%d:-2:flags=lanczos" % CURSOR_CROP_LONG_EDGE
    return ["ffmpeg", "-y", "-ss", "%s" % time, "-i", video_path,
           "-vframes", "1", "-vf", "%s,%s" % (crop, scale), out_path]


def cursor_work_dimensions(source_width, source_height):
    """The differencing working scale for a source `source_width` x
    `source_height`: capped at `CURSOR_WORK_WIDTH` so a source already
    smaller is never upscaled, with height following the source aspect
    ratio (video-cursor-localization). Pure — no I/O."""
    width = min(CURSOR_WORK_WIDTH, source_width)
    height = max(1, round(width * source_height / source_width))
    return width, height


def locate_cursors(candidates, video_path, frames_dir, window_path,
                   source_size, run):
    """Walk `candidates` (already-extracted frame dicts carrying `file`, in
    time order) localizing the on-screen pointer for each through the
    injectable runner: a single `ffmpeg` pass writes `window_path`'s
    grayscale differencing window (`cursor_window_argv`), read back as
    bytes (`read_gray_frames`) and passed to `locate_pointer`; where a
    frame is inconclusive, `carry_pointer` verifies whether the most
    recently *located* (never carried) position can carry forward
    (video-cursor-localization, video-cursor-carry-forward). Each frame
    with a known position gets a zoom crop extracted into `frames_dir`
    beside its full frame (video-cursor-crops).

    A candidate earlier than `CURSOR_WINDOW_SPAN_SECONDS` is declined
    outright: no window fits before it, so it is indexed with no position
    rather than grounded on one read from after its own timestamp.

    Returns a new list of candidate dicts (input candidates are not
    mutated), each carrying a `cursor` key only where a position is known.
    Raises :class:`VideoIngestError` if a crop `ffmpeg` call exits
    non-zero — a window `ffmpeg` failure or an unreadable window instead
    simply yields no position for that frame, since the fuller frame
    extraction has already succeeded and a cursor position is optional."""
    width, height = cursor_work_dimensions(*source_size)
    last_located = None  # (position, working-scale buffer, its own time)
    result = []
    for index, candidate in enumerate(candidates):
        time = candidate["time"]
        position = None
        origin = None
        # A frame earlier than the window's own span has no full window
        # ending on it; differencing one clamped to 0 would ground it on
        # pixels from after its own timestamp, so decline instead. Candidates
        # arrive in time order, so such a frame precedes any localization and
        # there is nothing to carry forward either.
        if time >= CURSOR_WINDOW_SPAN_SECONDS:
            rc, _stdout, _stderr = run(cursor_window_argv(
                video_path, time, window_path, width, height))
            frames = []
            if rc == 0:
                try:
                    frames = read_gray_frames(window_path, width, height)
                except OSError:
                    frames = []  # an unreadable window is simply no position
            if len(frames) == CURSOR_DIFF_FRAMES:
                position = locate_pointer(frames, width, height, source_size)
                if position is not None:
                    origin = "located"
                    last_located = (position, frames[-1], time)
                elif last_located is not None:
                    prev_position, prev_frame, prev_time = last_located
                    carried = carry_pointer(
                        prev_position, prev_frame, frames[-1], width, height,
                        source_size, prev_time)
                    if carried is not None:
                        position = carried
                        origin = "carried"
        if position is None:
            result.append(dict(candidate))
            continue
        source_width, source_height = source_size
        box = cursor_crop_box(position, source_width, source_height)
        filename = cursor_crop_filename(index, time)
        rc, _stdout, stderr = run(cursor_crop_argv(
            video_path, time, box, os.path.join(frames_dir, filename)))
        if rc != 0:
            raise VideoIngestError(
                "ffmpeg failed extracting a cursor crop at %.2fs from %s: %s"
                % (time, video_path, stderr.strip()))
        cursor_entry = {"x": position["x"], "y": position["y"],
                        "w": position["w"], "h": position["h"],
                        "file": filename, "origin": origin}
        if origin == "carried":
            cursor_entry["from"] = position["from"]
        result.append(dict(candidate, cursor=cursor_entry))
    if os.path.exists(window_path):
        os.remove(window_path)
    return result


# --- frame extraction and index ---------------------------------------------

# 1568px: the long-edge cap applied to every extracted frame, preserving
# aspect ratio and never upscaling — small enough for a vision model's input
# limits, large enough to keep on-screen UI text legible (video-frame-
# extraction).
FRAME_SCALE_FILTER = ("scale='min(1568,iw)':'min(1568,ih)':"
                      "force_original_aspect_ratio=decrease")

# version 2: adds the optional per-frame `cursor` object
# (video-cursor-crops).
FRAMES_SCHEMA_VERSION = 2


def frame_filename(index, time):
    """Filename for the frame at ordinal ``index`` (0-based) and ``time``
    seconds: zero-padded so lexicographic sort matches time order
    (video-frame-extraction). Pure — no I/O."""
    return "%03d-%.2fs.png" % (index, time)


def extract_frame_argv(video_path, time, out_path):
    """Argv for the `ffmpeg` call that extracts a single frame from
    ``video_path`` at ``time`` seconds, scaled per `FRAME_SCALE_FILTER`, to
    ``out_path`` (video-frame-extraction). Pure — no I/O. Every path is its
    own argv element, never a shell string."""
    return ["ffmpeg", "-y", "-ss", "%s" % time, "-i", video_path,
           "-vframes", "1", "-vf", FRAME_SCALE_FILTER, out_path]


def extract_frames(candidates, video_path, frames_dir, run):
    """Extract each selected ``candidates`` entry as a scaled PNG into
    ``frames_dir`` through the injectable runner, one `ffmpeg` call per
    candidate (video-frame-extraction). Files are named with a zero-padded
    index and the timestamp so they sort in time order.

    Returns a new list of candidate dicts (input candidates are not
    mutated), each carrying a `file` key holding the frame's filename.
    Raises :class:`VideoIngestError` if any `ffmpeg` call exits non-zero."""
    result = []
    for index, candidate in enumerate(candidates):
        filename = frame_filename(index, candidate["time"])
        out_path = os.path.join(frames_dir, filename)
        rc, _stdout, stderr = run(
            extract_frame_argv(video_path, candidate["time"], out_path))
        if rc != 0:
            raise VideoIngestError(
                "ffmpeg failed extracting frame at %.2fs from %s: %s"
                % (candidate["time"], video_path, stderr.strip()))
        result.append(dict(candidate, file=filename))
    return result


def build_frames_index(candidates):
    """Build the `frames.json` document: a schema `version` plus a `frames`
    array (video-frame-extraction). Each entry carries the candidate's
    `file`, `time`, `reason`, and its reason-specific provenance fields
    (`anchor`/`word_start` for `deixis`, `score` for `scene`), plus the
    optional `cursor` object on a candidate carrying a known pointer
    position — and nothing at all on one that does not, so a consumer can
    never mistake absence for a position (video-cursor-crops)."""
    frames = []
    for candidate in candidates:
        entry = {
            "file": candidate["file"],
            "time": candidate["time"],
            "reason": candidate["reason"],
        }
        if candidate["reason"] == "deixis":
            entry["anchor"] = candidate["anchor"]
            entry["word_start"] = candidate["word_start"]
        elif candidate["reason"] == "scene":
            entry["score"] = candidate["score"]
        if "cursor" in candidate:
            entry["cursor"] = candidate["cursor"]
        frames.append(entry)
    return {"version": FRAMES_SCHEMA_VERSION, "frames": frames}


def write_frames_index(path, candidates):
    """Write `frames.json` into the bundle directory ``path``."""
    with open(os.path.join(path, "frames.json"), "w",
             encoding="utf-8") as fh:
        json.dump(build_frames_index(candidates), fh, indent=2)
        fh.write("\n")


# --- doctor (dependency preflight) -------------------------------------

# (tool, hint). Both are required: `ingest` refuses to run when either is
# missing (video-doctor-preflight). Modelled on semdiff.py's tiered DEPS
# table, but every tool here is required — there is no optional/degrading
# tier for the orchestrator's own toolchain.
REQUIRED_TOOLS = [
    ("ffmpeg", "install via `doctor --fix`, or: brew install ffmpeg"),
    ("uv", "install via `doctor --fix`, or: brew install uv"),
]

# (label, HF hub repo id, human download-size hint, warming backend script).
# These are the exact model ids the ASR backends (asr_parakeet.py,
# asr_whisper.py) resolve via huggingface_hub, so a warm cache here means the
# first `ingest` will not stall on a download. Each backend script supports a
# `--warm-cache` flag that downloads its model and exits without requiring
# `--audio` (asr_parakeet.py, asr_whisper.py).
HF_MODEL_CACHES = [
    ("parakeet ASR model", "mlx-community/parakeet-tdt-0.6b-v2", "~600 MB",
     os.path.join(BACKENDS_DIR, "asr_parakeet.py")),
    ("whisper ASR model", "mlx-community/whisper-large-v3-turbo", "~1.5 GB",
     os.path.join(BACKENDS_DIR, "asr_whisper.py")),
]

def have(tool):
    return shutil.which(tool) is not None


def hf_cache_dir(repo_id):
    """Home-expanded huggingface_hub cache directory for ``repo_id``."""
    org, _, name = repo_id.partition("/")
    return os.path.expanduser(
        os.path.join("~", ".cache", "huggingface", "hub",
                     "models--%s--%s" % (org, name)))


def hf_model_cached(repo_id):
    return os.path.isdir(hf_cache_dir(repo_id))


def required_tools_missing():
    """Names of every required tool absent from PATH, in table order."""
    return [tool for tool, _hint in REQUIRED_TOOLS if not have(tool)]


def cmd_doctor(args, project_dir, run=default_run):
    """Report each prerequisite's state: `ffmpeg`/`uv` required, the backend
    model caches recommended. Exits non-zero only when a required tool is
    missing — a cold cache is reported but never fails the check
    (video-doctor-preflight)."""
    ok = True
    for tool, hint in REQUIRED_TOOLS:
        if have(tool):
            print("  + %s" % tool)
            continue
        installed = False
        if args.fix:
            installed = install_required_tool(tool, run)
        if installed and have(tool):
            print("  + %s (installed)" % tool)
            continue
        print("  x %s — MISSING (required): %s" % (tool, hint))
        ok = False
    for label, repo_id, size, script in HF_MODEL_CACHES:
        _report_cache(label, hf_model_cached(repo_id), size, args.fix,
                     warm=lambda s=script: warm_backend_cache(s, run))
    if not ok:
        print("video_ingest: required tools missing. Re-run with --fix to "
              "install what can be automated.", file=sys.stderr)
    return 0 if ok else 1


def _report_cache(label, cached, size, fix, warm):
    if not cached and fix:
        warm()
        cached = True
    if cached:
        print("  + %s" % label)
        return
    print("  - %s — recommended, not cached (%s download on first use)"
         % (label, size))


def install_required_tool(tool, run):
    """Install ``tool`` via Homebrew through the injectable runner. Network
    access happens here and only here — reached solely via `doctor --fix`
    (video-doctor-preflight). Returns whether the install command exited
    zero (the caller re-checks PATH before trusting it)."""
    print("video_ingest: installing %s via Homebrew…" % tool, file=sys.stderr)
    rc, _out, err = run(["brew", "install", tool])
    if rc != 0:
        print("video_ingest: brew install %s failed: %s"
              % (tool, err.strip()), file=sys.stderr)
    return rc == 0


def warm_backend_cache(script, run):
    """Pre-warm a backend's model cache by invoking it with `--warm-cache`
    through the injectable runner — the same `uv run` seam `ingest` uses to
    invoke backends. Network access happens here and only here, reached
    solely via `doctor --fix`."""
    print("video_ingest: pre-warming model cache via %s…" % script,
         file=sys.stderr)
    rc, _out, err = run(["uv", "run", script, "--warm-cache"])
    if rc != 0:
        raise VideoIngestError(
            "failed to pre-warm model cache via %s: %s" % (script, err.strip()))


# --- verbs --------------------------------------------------------------


def cmd_path(slug, project_dir):
    """Print the absolute bundle directory for a slug, without creating it —
    creation is ``ingest``'s job, gated by the existing-bundle refusal rule."""
    config = video_config(project_dir)
    print(bundle_dir(slug, config))
    return 0


def cmd_ingest(args, project_dir, run=default_run):
    missing = required_tools_missing()
    if missing:
        raise VideoIngestError(
            "required tool(s) missing: %s — run `doctor` for install hints"
            % ", ".join(missing))
    config = video_config(project_dir)
    slug = args.slug or derive_slug(args.video)
    path = bundle_dir(slug, config)
    ensure_bundle_dir(path, args.force)
    try:
        wav_path = os.path.join(path, "audio.wav")
        duration = extract_audio(args.video, wav_path, run)
        asr_name = resolve_backends(args, config)
        asr_result = run_backend(
            backend_script("asr", asr_name), wav_path, run,
            vocabulary=config.get("vocabulary"))
        words = asr_result.get("words", [])
        write_transcript(path, words)

        deixis = deixis_candidates(words, duration)
        scene_scores = compute_scene_scores(args.video, run)
        scene = scene_candidates(scene_scores, duration)
        max_frames = config.get("max_frames", DEFAULT_VIDEO_MAX_FRAMES)
        scene_floor = config.get("scene_floor", SCENE_FLOOR_FRACTION)
        frame_candidates, _dropped = resolve_frame_candidates(
            deixis, scene, max_frames, duration, scene_floor)
        extracted_frames = extract_frames(
            frame_candidates, args.video, os.path.join(path, "frames"), run)
        if config.get("video_cursor", True):
            source_size = probe_video_dimensions(args.video, run)
            if source_size is not None:
                extracted_frames = locate_cursors(
                    extracted_frames, args.video, os.path.join(path, "frames"),
                    os.path.join(path, ".cursor-window.raw"), source_size, run)
        write_frames_index(path, extracted_frames)

        try:
            size = os.path.getsize(args.video)
        except OSError:
            size = 0
        manifest = {
            "source": os.path.abspath(args.video),
            "duration": duration,
            "size": size,
            "asr_backend": asr_name,
            "asr_model": asr_result.get("model"),
        }
        write_manifest(path, manifest)
    except VideoIngestError:
        shutil.rmtree(path, ignore_errors=True)
        raise
    print(path)
    return 0


def main(argv=None, run=None):
    run = run or default_run
    parser = argparse.ArgumentParser(
        prog="video_ingest",
        description="Turn a screen recording into a transcript bundle "
                    "(stdlib only).")
    parser.add_argument("--project-dir", default=".",
                        help="project root used to resolve config "
                             "(default: cwd)")
    sub = parser.add_subparsers(dest="verb", required=True)

    p_doctor = sub.add_parser(
        "doctor", help="report prerequisite state; --fix installs what it can")
    p_doctor.add_argument("--fix", action="store_true",
                          help="install required tools and pre-warm model "
                               "caches (network access happens only here)")

    p_ingest = sub.add_parser(
        "ingest", help="extract audio, transcribe, extract frames, and write a bundle")
    p_ingest.add_argument("video", help="path to the source recording")
    p_ingest.add_argument("--slug", default=None,
                          help="bundle slug (default: derived from the "
                               "filename)")
    p_ingest.add_argument("--force", action="store_true",
                          help="overwrite an existing bundle for this slug")
    p_ingest.add_argument("--asr", choices=["parakeet", "whisper"],
                          default=None, help="ASR backend (default: "
                          "parakeet, or build.video_asr)")

    p_path = sub.add_parser("path", help="print the absolute bundle directory")
    p_path.add_argument("slug")

    args = parser.parse_args(argv)
    try:
        if args.verb == "path":
            return cmd_path(args.slug, args.project_dir)
        if args.verb == "doctor":
            return cmd_doctor(args, args.project_dir, run=run)
        if args.verb == "ingest":
            return cmd_ingest(args, args.project_dir, run=run)
    except VideoIngestError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
