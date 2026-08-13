# video-ingest-frames
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Fill the bundle's empty `frames/` slot with the handful of video frames that
matter — the moments a speaker points at something, plus the recording's own UI
transitions — each indexed with the reason it was chosen.

### Motivation

Every intent in a video brief has to cite the frame that was on screen when it
was spoken, and the pipeline currently produces no frames at all — `frames/` is
created empty and nothing writes into it.

### Details

- Select candidate timestamps from two sources: deixis anchors in
  `transcript.json` and scene-score peaks ranked within the recording.
- Merge, deduplicate, and cap the candidates, logging every dropped frame.
- Extract each selected frame with `ffmpeg`, capped at a 1568 px long edge.
- Write `frames.json` recording each frame's timestamp and selection reason.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`, the suite under
`plugins/s/skills/video-ingest/tests/`, and the plugin version in
`plugins/s/.claude-plugin/plugin.json`. No new dependencies — `ffmpeg` is
already a required tool.

### Non-goals

- No cursor detection or zoom crops — `video-cursor-grounding` owns that.
- No vision-model analysis of the frames; this member only selects and extracts.
- No brief authoring or frame-to-intent citation — `video-ingest-skill`.
- No change to audio extraction, transcription, diarization, or attribution.
- No re-extraction of frames for an existing bundle without `--force`; frame
  selection rides the normal ingest.

## Implementation

**Absolute scene thresholds do not work on screen recordings, and this is
measured, not assumed.** Running `ffmpeg`'s scene filter over the reference
recording scored 1923 frames with a **maximum score of 0.0535**; the
conventional `gt(scene,0.3)` used for cut detection selects **zero** frames, and
so does `0.1`. Screen recordings scroll and open menus rather than cutting, so
inter-frame deltas stay tiny. This contradicts the epic's D7, which assumed an
absolute `gt(scene,N)` threshold would catch UI transitions; D7's *intent*
(scene changes are a useful signal) holds, its *mechanism* does not.

**So peaks are ranked within the recording, never compared to a constant.** In
the reference recording the five real transitions score 0.046–0.054 against a
next-highest of 0.0017 — a 27× gap — and land at 12.94 s, 19.75 s, 24.59 s,
39.57 s and 40.69 s, matching the moments the speaker discusses opening a spec,
clicking filters, and switching windows. The rule is therefore: keep local
maxima (a frame scoring above both neighbours), require a non-zero score,
enforce a minimum separation of `SCENE_PEAK_MIN_GAP_SECONDS` (1.0), and take the
top `ceil(duration / SCENE_PEAK_SECONDS_PER_FRAME)` by score — one peak per 10
seconds, which yields exactly 5 on the 48-second reference. Rejected: lowering
the constant to ~0.04, which overfits to this one file and would silently select
nothing on a different encoder or resolution.

**Deixis is the primary signal; scene peaks supplement it.** The anchor set is
the spatial demonstratives — `this`, `that`, `these`, `those`, `here`,
`there` — deliberately **excluding `it`**, which is anaphoric (it refers back to
something already named) rather than pointing at the screen; on the reference
transcript `it` contributes 3 of 11 hits and none of them mark a gesture. Each
anchor at time `t` contributes candidates at `t-0.5`, `t` and `t+1.5`, clamped
to the recording, because a speaker points slightly before and after speaking.

**Candidate resolution is deterministic and never silently truncating.**
Candidates are deduplicated when within `FRAME_DEDUP_MIN_GAP_SECONDS` (0.5) of
each other, keeping the earlier. The cap is `build.video_max_frames`
(default 24). When candidates exceed it, deixis candidates are kept first in
time order, then scene peaks by descending score. **Every dropped candidate is
logged to stderr with its timestamp and reason** — a capped frame set that reads
as complete coverage is a correctness bug, not a performance trade.

**Extraction preserves UI legibility.** Frames are written as PNG (lossless —
JPEG artefacts on small UI text are exactly what a downstream reader must not
be given), scaled with
`scale='min(1568,iw)':'min(1568,ih)':force_original_aspect_ratio=decrease`,
which caps the long edge at 1568 px, preserves aspect, and never upscales. On
the 1462×1350 reference source this is a no-op, so the scaling path is exercised
by unit tests over the argv rather than by the reference recording.

**`frames.json` carries provenance, not just filenames.** Each entry records the
file, its timestamp, and why it was chosen — `deixis` with the anchor word and
that word's start time, or `scene` with its score. The skill member has to cite
a frame against an intent, and a bare directory of PNGs cannot support that.

**Frame extraction runs through the injectable runner** like every other
subprocess in this script, so the suite continues to pass with no `ffmpeg`
installed, and the scene-score parse is a pure function over captured stdout.

Risk: a recording with no speech and no UI transitions yields no frames. That is
correct behaviour rather than an error — `frames/` stays empty, `frames.json`
records an empty list, and the ingest still succeeds, because the transcript
remains useful on its own.
