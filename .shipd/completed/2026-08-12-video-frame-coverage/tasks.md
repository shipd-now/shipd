## 1. Distribution over the timeline

- [x] 1.1 [req: video-frame-budget] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add tests for
      the distributed cap against a synthetic candidate set modelled on the
      measured failure: a 580-second duration, 40 deixis candidates all inside
      the first 50 seconds, and 7 scene candidates spread from 380s to 562s,
      with a cap of 24. Assert the kept set spans beyond 300s, that at least one
      scene candidate survives, and that the kept count is 24. Run them and
      observe they fail — the current rule keeps only the early deixis
      candidates.
- [x] 1.2 [req: video-frame-budget] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, rewrite the cap
      half of `resolve_frame_candidates` to bucket the recording into
      `max_frames` equal-width buckets over its duration and take at most one
      candidate per occupied bucket. Leave the dedup half and the stderr
      drop-reporting untouched. The function stays pure. Confirm 1.1 passes.
- [x] 1.3 [req: video-frame-budget] In `test_video_frames.py`, add tests for the
      within-bucket preference: a bucket holding both a deixis and a scene
      candidate keeps the deixis one; a bucket holding two scene candidates
      keeps the higher-scoring one; a bucket holding two deixis candidates keeps
      the earlier one. Run and observe failure where applicable, then make them
      pass.
- [x] 1.4 [req: video-frame-budget] In `test_video_frames.py`, add tests for
      backfill: with several empty buckets and unselected candidates remaining,
      the kept count still reaches the cap; and with fewer candidates than the
      cap, every candidate is kept and nothing is reported dropped. Run and
      observe failure, then make them pass in `video_ingest.py`.
- [x] 1.5 [req: video-frame-budget] In `test_video_frames.py`, add a test
      asserting every candidate dropped by the distributed cap is still reported
      on stderr with its timestamp and reason, so the drop log that made this
      defect visible keeps working.

## 2. Ship

- [x] 2.1 [req: *] Run the video-ingest suite under a stripped PATH excluding
      ffmpeg and uv — `D=$(mktemp -d); ln -s "$(command -v python3)" $D/python3;
      PATH="$D:/usr/bin:/bin" python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` — and confirm it passes.
- [x] 2.2 [req: *] Run both suites normally —
      `plugins/s/skills/video-ingest/tests` and
      `plugins/s/skills/build/tests` — and confirm they pass.
- [x] 2.3 [req: *] Manual verification against the long recording, the decisive
      check. Re-ingest `~/Downloads/am-video-fixtures/skymiles.mp4` (580.6s) into
      a NEW slug — do not overwrite `~/.shipd/video/skymiles` or
      `~/.shipd/video/skymiles-1spk`, which hold the pre-fix measurements. Record in
      the PR description: the number of frames kept, the split by reason, and
      the first and last frame timestamps. The pre-fix run produced 24 frames,
      all deixis, spanning 2.6s-48.1s of a 580.6s recording; state plainly
      whether the new run spans the recording and whether any scene candidate
      survived.
- [x] 2.4 [req: *] Regression check on the short recording: re-ingest the
      48-second reference at
      `/Users/mikkelbergmann/projects/shipd/docs/research/Screen*.mov`
      (glob-matched; its filename holds a U+202F space, so never retype it) into
      a NEW slug and confirm it still yields 23 frames — 19 deixis and 4 scene —
      because that candidate set never reached the cap and must be unaffected.
      Report the observed counts.
- [x] 2.5 [req: *] Delete every scratch bundle created by 2.3 and 2.4, and
      confirm `git status --short` in both the worktree and the main checkout
      shows no artifact from this verification.
- [x] 2.6 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.83` to `0.6.84`.
