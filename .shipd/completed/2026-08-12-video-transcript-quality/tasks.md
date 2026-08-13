## 1. Spurious-turn filter

- [x] 1.1 [req: video-spurious-turn-filter] Create
      `plugins/s/skills/video-ingest/tests/test_video_turn_filter.py` covering:
      a 1.2s turn between two same-speaker turns is dropped and its span
      absorbed by that speaker; a short turn between two *different* speakers is
      kept; a short turn first in the list is kept; a short turn last in the
      list is kept; a turn at the threshold is kept. Run them and observe they
      fail — the function does not exist yet.
- [x] 1.2 [req: video-spurious-turn-filter] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, add a module
      constant `SPURIOUS_TURN_MAX_SECONDS = 2.0` and a pure
      `filter_spurious_turns(turns)` implementing the sandwich rule, absorbing a
      dropped turn's span into the surrounding speaker's adjacent turn. No I/O.
      Confirm 1.1 passes.
- [x] 1.3 [req: video-spurious-turn-filter] In
      `plugins/s/skills/video-ingest/tests/test_video_turn_filter.py`, add a
      test asserting `filter_spurious_turns` does not mutate its input list or
      the turn dicts it was given. Run and observe failure, then make it pass in
      `video_ingest.py` if it does not already hold.
- [x] 1.4 [req: video-spurious-turn-filter] In `video_ingest.py`'s ingest flow,
      call `filter_spurious_turns` on the diarization turns before `join`, and
      confirm the existing `join` tests in
      `plugins/s/skills/video-ingest/tests/test_video_attribution.py` still
      pass unchanged.

## 2. Vocabulary configuration

- [x] 2.1 [req: video-vocabulary-biasing] In
      `plugins/s/skills/video-ingest/tests/test_video_bundle.py`, add tests for
      resolving `build.video_vocabulary` from the layered config: a list of
      terms resolves, an absent key yields no vocabulary, and an empty list
      yields no vocabulary. Run and observe failure.
- [x] 2.2 [req: video-vocabulary-biasing] In `video_ingest.py`'s
      `video_config`, resolve `build.video_vocabulary` alongside the existing
      `video_dir` / `video_asr` / `video_diarizer` keys. Confirm 2.1 passes.
- [x] 2.3 [req: video-vocabulary-biasing, video-backend-adapters] In
      `plugins/s/skills/video-ingest/tests/test_video_backends.py`, add tests
      asserting the ASR backend argv carries `--vocab` with the configured terms
      comma-joined when a vocabulary is configured, and carries no `--vocab`
      element when the key is absent or empty. Run and observe failure.
- [x] 2.4 [req: video-vocabulary-biasing, video-backend-adapters] In
      `video_ingest.py`, extend the ASR backend argv builder to append
      `--vocab <comma-joined terms>` only when the resolved vocabulary is
      non-empty. Confirm 2.3 passes.

## 3. Backend support for the option

- [x] 3.1 [req: video-vocabulary-biasing] In
      `plugins/s/skills/video-ingest/scripts/backends/asr_whisper.py`, add a
      `--vocab` argument, render its comma-separated terms into a single
      `initial_prompt` sentence, and pass that to `mlx_whisper.transcribe`
      (which accepts `initial_prompt`). Omit the argument entirely when no
      `--vocab` is given so behaviour is unchanged.
- [x] 3.2 [req: video-backend-adapters] In
      `plugins/s/skills/video-ingest/scripts/backends/asr_parakeet.py`, add a
      `--vocab` argument that is accepted and ignored, and state in the module
      docstring that `parakeet_mlx.transcribe` exposes no biasing parameter
      (`path, dtype, decoding_config, chunk_duration, overlap_duration,
      chunk_callback` only), so the option is accepted for contract
      compatibility.

## 4. Ship

- [x] 4.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` under a stripped PATH that excludes
      ffmpeg and uv — `D=$(mktemp -d); ln -s "$(command -v python3)" $D/python3;
      PATH="$D:/usr/bin:/bin" python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` — and confirm it passes. This
      reproduces CI, where neither tool exists.
- [x] 4.2 [req: *] Run both suites normally — `plugins/s/skills/video-ingest/
      tests` and `plugins/s/skills/build/tests` — and confirm they pass.
- [x] 4.3 [req: *] Manual verification on real hardware. Add
      `build.video_vocabulary` with shipd terms (including `shipd`) to a
      scratch config, then ingest the recording in the main checkout — match it
      with the glob `/Users/mikkelbergmann/projects/shipd/docs/research/
      Screen*.mov`, whose filename holds a U+202F space, so never retype it.
      Run it twice: once `--asr whisper` and once with the default parakeet.
      Record in the PR description, for each run, whether `shipd` was
      transcribed correctly, and whether the word `header.` is still attributed
      to a different speaker than the sentence containing it.
- [x] 4.4 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.77` to `0.6.78`.
