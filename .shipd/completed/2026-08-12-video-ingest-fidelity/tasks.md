## 1. Scene floor in the frame budget

- [x] 1.1 [req: video-frame-budget] In
      `plugins/s/skills/video-ingest/tests/test_video_frames.py`, add failing
      tests for the scene floor: every bucket holding a deixis candidate with
      scene candidates sharing some buckets yields at least
      `int(cap * SCENE_FLOOR_FRACTION)` scene frames; fewer scene candidates
      than the floor keeps all of them and displaces no further deixis winner;
      the converted selection keeps the same total frame count; and with the
      floor already satisfied a bucket's deixis candidate still wins. Run them
      and observe them fail.
- [x] 1.2 [req: video-frame-budget] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, add
      `SCENE_FLOOR_FRACTION = 0.25` beside `DEFAULT_VIDEO_MAX_FRAMES`, and
      resolve `build.video_scene_floor` into `video_config`'s returned settings
      under a `scene_floor` key, defaulting to that constant.
- [x] 1.3 [req: video-frame-budget] In `video_ingest.py`'s
      `resolve_frame_candidates`, accept a `scene_floor` fraction argument and,
      after bucket winners are chosen, convert deixis-won buckets that also hold
      a scene candidate to that bucket's highest-scoring scene candidate —
      highest-scoring scene first — until the floor
      `int(max_frames * scene_floor)` is met or no convertible bucket remains.
      Never exceed the number of scene candidates available and never change the
      kept count.
- [x] 1.4 [req: video-frame-budget] In `video_ingest.py`, at the
      `resolve_frame_candidates` call inside the ingest command (beside the
      existing `max_frames` lookup), read the resolved `scene_floor` from the
      config the same way and pass it through; confirm the tests from 1.1 now
      pass.

## 2. Read-only roster listing

- [x] 2.1 [req: video-speaker-roster] In
      `plugins/s/skills/video-ingest/tests/test_video_speakers.py`, add failing
      tests that `roster` with no `--add` prints the configured names one per
      line and leaves the config file's bytes byte-for-byte unchanged, and that
      it creates no config file when none exists. Run them and observe them
      fail.
- [x] 2.2 [req: video-speaker-roster] In `video_ingest.py`'s `cmd_roster`,
      return early when `args.add` is empty: read the resolved names, print one
      per line, and exit zero without opening the config for writing. Confirm
      the tests from 2.1 now pass.
- [x] 2.3 [req: video-speaker-roster] In `video_ingest.py`, update the `roster`
      subparser help text at the `roster` parser definition to state that the
      verb lists the roster when no `--add` names are given.

## 3. Pyannote diarization backend

- [x] 3.1 [req: video-diarizer-pyannote] Add
      `plugins/s/skills/video-ingest/tests/test_video_diarize_pyannote.py`
      driving the backend's `main()` against a stubbed `pyannote.audio` module
      injected into `sys.modules`: the emitted JSON carries `turns` and `model`;
      `--speakers 2` reaches the pipeline as an exact speaker count of 2; no
      `--speakers` leaves it unconstrained; `--model <id>` overrides the
      default; `--warm-cache` resolves the model and diarizes nothing. Run them
      and observe them fail.
- [x] 3.2 [req: video-diarizer-pyannote] Add
      `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py` with
      PEP 723 inline dependencies `pyannote.audio` and `torch`, a
      `MODEL_ID = "pyannote/speaker-diarization-3.1"` default, and an
      `argparse` surface of `--audio`, `--speakers`, `--model`, `--warm-cache`
      mirroring
      `plugins/s/skills/video-ingest/scripts/backends/diarize_sherpa.py`. Keep
      the `pyannote.audio` import inside `main()` so the module imports without
      the dependency.
- [x] 3.3 [req: video-diarizer-pyannote] In `diarize_pyannote.py`, load the
      pipeline via `Pipeline.from_pretrained`, run it over `--audio`, map
      `--speakers <n>` to the pipeline's exact speaker count, and print
      `{"turns": [{"start", "end", "speaker"}], "model": MODEL_ID}` to stdout.
- [x] 3.4 [req: video-diarizer-pyannote] In `diarize_pyannote.py`, catch a
      missing-credential or unaccepted-licence failure and exit non-zero with
      stderr naming the remediation (accept the model's terms on Hugging Face,
      export a token); confirm the tests from 3.1 now pass.

## 4. Wire the backend into the orchestrator

- [x] 4.1 [req: video-backend-adapters] In
      `plugins/s/skills/video-ingest/tests/test_video_backends.py`, add failing
      tests that `ingest --diarizer pyannote` invokes
      `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`
      and records `pyannote` as the diarizer in
      `manifest.json`, and that `build.video_diarizer` set to `pyannote` selects
      it with no flag. Run them and observe them fail.
- [x] 4.2 [req: video-backend-adapters] In `video_ingest.py`, add
      `("diarizer", "pyannote")` to the `BACKEND_SCRIPTS` table pointing at
      `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`,
      and add `pyannote` to the `--diarizer`
      argument's `choices`; confirm the tests from 4.1 now pass.

## 5. Diarization outcome reporting

- [x] 5.1 [req: video-diarization-report] Add
      `plugins/s/skills/video-ingest/tests/test_video_diarization_report.py`
      with failing tests for two pure functions: `diarization_report(words)`
      returns the label count, turn count and attributed seconds per label; and
      `diarization_warnings(report, requested)` warns when a requested count
      differs from the produced count, warns when no count was requested and two
      or more labels each hold under 5% of attributed speech, stays silent for an
      even two-label split, and always names both remedies in its text. Run them
      and observe them fail.
- [x] 5.2 [req: video-diarization-report] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, add
      `DIARIZATION_MINOR_LABEL_SHARE = 0.05` and the pure functions
      `diarization_report(words)` and `diarization_warnings(report, requested)`
      beside the existing attribution helpers, performing no I/O; confirm the
      tests from 5.1 now pass.
- [x] 5.3 [req: video-diarization-report] In `video_ingest.py`'s ingest command,
      call `diarization_report` on the attributed words, store the result in the
      manifest under a `diarization` key, and write each line from
      `diarization_warnings` to stderr without changing the exit status.
- [x] 5.4 [req: video-diarization-report] In
      `plugins/s/skills/video-ingest/tests/test_video_bundle.py`, add a test
      that a completed ingest's `manifest.json` carries the `diarization` entry
      and that a warning run still exits zero with an unchanged transcript.

## 6. Verification

- [x] 6.1 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/video-ingest/tests` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests`, and
      confirm both suites pass with neither `torch`, `pyannote.audio`, nor a
      Hugging Face token installed.
- [x] 6.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`, as every change touching
      `plugins/s/` must.
