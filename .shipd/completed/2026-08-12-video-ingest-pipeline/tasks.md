## 1. Skeleton and bundle contract

- [x] 1.1 [req: video-pipeline-testability] Create
      `plugins/s/skills/video-ingest/tests/test_video_bundle.py` with tests for
      bundle root resolution (default `~/.shipd/video`, `build.video_dir` override,
      home expansion) and the `path <slug>` verb. Run them and observe they fail
      — the script does not exist yet.
- [x] 1.2 [req: video-bundle-contract, video-pipeline-testability] Create
      `plugins/s/skills/video-ingest/scripts/video_ingest.py` (stdlib only,
      module docstring naming the verbs) with the argparse skeleton for
      `doctor`, `ingest`, `path`, the injectable
      `run(args, input=None) -> (rc, stdout, stderr)` runner, and bundle root
      resolution mirroring `design.py::design_config`. Confirm 1.1 passes.
- [x] 1.3 [req: video-bundle-contract] In
      `plugins/s/skills/video-ingest/tests/test_video_bundle.py`, add tests for
      the bundle layout (`manifest.json`, `audio.wav`, `transcript.json`,
      `frames/`), the manifest fields, and the refuse-existing-without-`--force`
      rule. Run and observe failure.
- [x] 1.4 [req: video-bundle-contract] In `video_ingest.py`, implement bundle
      creation, the manifest writer, and the `--force` rule. Confirm 1.3 passes.

## 2. Preflight

- [x] 2.1 [req: video-doctor-preflight] Create
      `plugins/s/skills/video-ingest/tests/test_video_doctor.py` covering a
      missing required tool (non-zero exit, hint printed), a cold model cache
      (recommended, exit zero), and `ingest` refusing when a required tool is
      missing. Run and observe failure.
- [x] 2.2 [req: video-doctor-preflight] In `video_ingest.py`, implement `doctor`
      with a tiered `DEPS` table modelled on
      `plugins/s/skills/review/scripts/semdiff.py` (`ffmpeg`, `uv` required;
      model caches recommended), and gate `ingest` on the required tier. Confirm
      2.1 passes.
- [x] 2.3 [req: video-doctor-preflight] In `video_ingest.py`, implement
      `doctor --fix`: Homebrew installs for `ffmpeg` and `uv`, then pre-warm the
      backend model caches. Keep every network call inside this code path.

## 3. Audio extraction

- [x] 3.1 [req: video-audio-extraction] Create
      `plugins/s/skills/video-ingest/tests/test_video_audio.py` covering slug
      derivation from a filename containing a U+202F narrow no-break space,
      16 kHz mono ffmpeg argument construction, paths passed as argv elements
      (never a shell string), and rejection of a video with no audio stream. Run
      and observe failure.
- [x] 3.2 [req: video-audio-extraction] In `video_ingest.py`, implement slug
      derivation (Unicode whitespace and non-alphanumeric runs folded to `-`,
      lowercased, stripped) and `--slug`. Confirm the slug tests pass.
- [x] 3.3 [req: video-audio-extraction] In `video_ingest.py`, implement audio
      extraction through the injectable runner: `ffprobe` for the audio-stream
      check and duration, then `ffmpeg` to 16 kHz mono PCM `audio.wav`. Confirm
      3.1 passes.

## 4. Backends

- [x] 4.1 [req: video-backend-adapters] Create
      `plugins/s/skills/video-ingest/tests/test_video_backends.py` covering
      default selection (parakeet + sherpa), `--asr whisper` overriding a
      configured `parakeet`, `build.video_asr` / `build.video_diarizer`
      resolution, and a non-zero backend exit failing the ingest with stderr
      attached and no bundle left behind. Run and observe failure.
- [x] 4.2 [req: video-backend-adapters] In `video_ingest.py`, implement backend
      selection and invocation: build the `uv run <script> --audio <wav>` argv,
      parse one JSON object from stdout, and fail with the backend's stderr on a
      non-zero exit or unparseable output, removing any partial bundle. Confirm
      4.1 passes.
- [x] 4.3 [req: video-backend-adapters] Create
      `plugins/s/skills/video-ingest/scripts/backends/asr_parakeet.py` — a PEP
      723 script (`# /// script` block declaring `parakeet-mlx`) reading
      `--audio`, transcribing with word-level timestamps, and printing
      `{"words": [{"start","end","text"}], "model": …}` to stdout.
- [x] 4.4 [req: video-backend-adapters] Create
      `plugins/s/skills/video-ingest/scripts/backends/asr_whisper.py` — a PEP
      723 script declaring `mlx-whisper`, transcribing
      `mlx-community/whisper-large-v3-turbo` with `word_timestamps=True`, and
      printing the same `words` shape.
- [x] 4.5 [req: video-backend-adapters] Create
      `plugins/s/skills/video-ingest/scripts/backends/diarize_sherpa.py` — a PEP
      723 script declaring `sherpa-onnx`, running offline speaker diarization
      (pyannote-segmentation-3.0 + a 3D-Speaker embedding model, downloading them
      into the model cache on first use) and printing
      `{"turns": [{"start","end","speaker"}], "model": …}`.

## 5. Attribution and transcript

- [x] 5.1 [req: video-speaker-attribution] Create
      `plugins/s/skills/video-ingest/tests/test_video_attribution.py` covering
      maximum-overlap assignment, the 250 ms nearest-turn fallback, `null` for a
      word far from every turn, and deterministic earlier-turn resolution on an
      exact tie. Run and observe failure.
- [x] 5.2 [req: video-speaker-attribution] In `video_ingest.py`, implement
      `join(words, turns)` as a pure function with no I/O. Confirm 5.1 passes.
- [x] 5.3 [req: video-transcript-schema] In
      `plugins/s/skills/video-ingest/tests/test_video_attribution.py`, add tests
      asserting `transcript.json` carries a schema `version` and `segments`
      ordered by `start`, that a speaker change splits a segment, and that each
      word retains `start`, `end`, `text`, `speaker`. Run and observe failure.
- [x] 5.4 [req: video-transcript-schema] In `video_ingest.py`, implement segment
      assembly (split at speaker changes, ordered by start) and the
      `transcript.json` writer. Confirm 5.3 passes.

## 6. Ship

- [x] 6.1 [req: video-pipeline-testability] In `.github/workflows/ci.yml`, add a
      step running `python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests -v`, placed after the existing review
      test suite step.
- [x] 6.2 [req: video-pipeline-testability] Run `python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm both suites pass.
- [x] 6.3 [req: *] Manual verification on real hardware — a green suite does not
      close this change. Run `python3
      plugins/s/skills/video-ingest/scripts/video_ingest.py doctor`, then
      `ingest` against the 48-second recording in `docs/research/` (match it with
      the glob `docs/research/Screen*.mov`; its filename holds a U+202F space, so
      never retype the name). Confirm a bundle is produced and record in the PR
      description: the derived slug, the wall-clock ingest time, the number of
      speakers diarized, and the first transcribed sentence.
- [x] 6.4 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.76` to `0.6.77`.
