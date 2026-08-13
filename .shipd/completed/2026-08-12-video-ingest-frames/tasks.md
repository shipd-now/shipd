## 1. Deixis anchors

- [x] 1.1 [req: video-deixis-anchors] Create
      `plugins/s/skills/video-ingest/tests/test_video_frames.py` with tests for
      deixis candidate derivation: `here` at 10.0s in a 60s recording yields
      candidates at 9.5/10.0/11.5 each carrying the anchor word and its start
      time; `it` yields nothing; a demonstrative at 0.2s clamps its earlier
      candidate to 0.0; a demonstrative near the end clamps to the duration;
      punctuation and capitalisation are normalized (`This,` matches). Run them
      and observe they fail.
- [x] 1.2 [req: video-deixis-anchors] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, add the module
      constant `DEIXIS_WORDS = {"this", "that", "these", "those", "here",
      "there"}` and a pure `deixis_candidates(words, duration)` returning
      candidate dicts with `time`, `reason="deixis"`, `anchor`, `word_start`.
      No I/O. Confirm 1.1 passes.

## 2. Scene peaks

- [x] 2.1 [req: video-scene-peaks] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add tests for
      parsing `ffmpeg` metadata output into `(time, score)` pairs, using a
      fixture string in the real format (`pts_time:<t>` lines followed by
      `lavfi.scene_score=<s>` lines). Run and observe failure.
- [x] 2.2 [req: video-scene-peaks] In `video_ingest.py`, add a pure
      `parse_scene_scores(text)` returning ordered `(time, score)` pairs.
      Confirm 2.1 passes.
- [x] 2.3 [req: video-scene-peaks] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add tests for
      peak selection: only local maxima (above both neighbours) are eligible;
      zero-scoring frames are never selected; two maxima inside
      `SCENE_PEAK_MIN_GAP_SECONDS` collapse to the higher-scoring one; at most
      `ceil(duration / SCENE_PEAK_SECONDS_PER_FRAME)` are kept, ranked by
      descending score; an all-zero score list yields an empty result. Include a
      case whose scores all sit below 0.06 to assert no absolute threshold is
      applied. Run and observe failure.
- [x] 2.4 [req: video-scene-peaks] In `video_ingest.py`, add module constants
      `SCENE_PEAK_MIN_GAP_SECONDS = 1.0` and `SCENE_PEAK_SECONDS_PER_FRAME =
      10.0`, and a pure `scene_candidates(scores, duration)` returning candidate
      dicts with `time`, `reason="scene"`, `score`. No I/O. Confirm 2.3 passes.
- [x] 2.5 [req: video-scene-peaks] In `video_ingest.py`, add the scene-scoring
      ffmpeg invocation through the injectable runner — one pass over the video
      with `select='gte(scene,0)',metadata=print:file=-` writing to a null
      output — and feed its output through `parse_scene_scores`.

## 3. Merge, dedup and cap

- [x] 3.1 [req: video-frame-budget] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add tests for
      candidate resolution: a deixis and a scene candidate within
      `FRAME_DEDUP_MIN_GAP_SECONDS` collapse to the earlier; with candidates
      over the cap, deixis candidates are kept in time order before any scene
      candidate; scene candidates fill remaining slots by descending score; and
      every dropped candidate is reported on stderr with its timestamp and
      reason. Run and observe failure.
- [x] 3.2 [req: video-frame-budget] In `video_ingest.py`, add
      `FRAME_DEDUP_MIN_GAP_SECONDS = 0.5`, resolve `build.video_max_frames`
      (default 24) in `video_config`, and add `resolve_frame_candidates(deixis,
      scene, max_frames)` performing the merge, dedup and cap, writing one
      stderr line per dropped candidate. Confirm 3.1 passes.

## 4. Extraction and index

- [x] 4.1 [req: video-frame-extraction] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add tests
      asserting the extraction argv for one candidate seeks to its timestamp,
      requests a single frame, writes a `.png` under the bundle's `frames/`,
      and carries the scale filter
      `scale='min(1568,iw)':'min(1568,ih)':force_original_aspect_ratio=decrease`.
      Run and observe failure.
- [x] 4.2 [req: video-frame-extraction] In `video_ingest.py`, add frame
      extraction through the injectable runner, one ffmpeg call per candidate,
      naming files with a zero-padded index and the timestamp so they sort in
      time order. Confirm 4.1 passes.
- [x] 4.3 [req: video-frame-extraction] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add tests for
      `frames.json`: it carries a schema `version` and a `frames` array; a
      deixis entry carries `file`, `time`, `reason`, `anchor` and `word_start`;
      a scene entry carries `file`, `time`, `reason` and `score`; and a run with
      no candidates writes an empty array while the ingest exits zero. Run and
      observe failure.
- [x] 4.4 [req: video-frame-extraction, video-bundle-contract] In
      `video_ingest.py`, write `frames.json` into the bundle and wire the whole
      frame stage into `cmd_ingest` after the transcript is written. Confirm 4.3
      passes.

## 5. Ship

- [x] 5.1 [req: *] Run the video-ingest suite under a stripped PATH that
      excludes ffmpeg and uv — `D=$(mktemp -d); ln -s "$(command -v python3)"
      $D/python3; PATH="$D:/usr/bin:/bin" python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` — and confirm it passes. This
      reproduces CI, where neither tool exists.
- [x] 5.2 [req: *] Run both suites normally —
      `plugins/s/skills/video-ingest/tests` and
      `plugins/s/skills/build/tests` — and confirm they pass.
- [x] 5.3 [req: *] Manual verification on real hardware. Ingest the recording in
      the main checkout — match it with the glob
      `/Users/mikkelbergmann/projects/shipd/docs/research/Screen*.mov`, whose
      filename holds a U+202F space, so never retype it. Record in the PR
      description: how many frames were extracted, how many came from each
      reason, the timestamps of the scene-derived frames, and whether any
      candidate was dropped by the cap. The five scene peaks previously measured
      on this recording fall at 12.94s, 19.75s, 24.59s, 39.57s and 40.69s —
      report whether the implementation reproduces them.
- [x] 5.4 [req: *] Open two extracted frames and confirm by eye that the UI text
      is legible and the image is not upscaled or letterboxed; note the observed
      pixel dimensions in the PR description.
- [x] 5.5 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.78` to `0.6.79`.
