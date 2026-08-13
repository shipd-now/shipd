## 1. Retire the diarization test surface

- [x] 1.1 [req: video-speaker-attribution, video-spurious-turn-filter] Delete
      `plugins/s/skills/video-ingest/tests/test_video_attribution.py` and
      `plugins/s/skills/video-ingest/tests/test_video_turn_filter.py`.
- [x] 1.2 [req: video-speaker-samples, video-speaker-merge, video-speaker-roster]
      Delete `plugins/s/skills/video-ingest/tests/test_video_speakers.py`.
- [x] 1.3 [req: video-diarizer-pyannote, video-diarization-report] Delete
      `plugins/s/skills/video-ingest/tests/test_video_diarize_pyannote.py` and
      `plugins/s/skills/video-ingest/tests/test_video_diarization_report.py`,
      which also retires the last coverage of `video-pyannote-api-contract`.
- [x] 1.4 [req: video-backend-adapters] In
      `plugins/s/skills/video-ingest/tests/test_video_backends.py`, delete every
      test that selects, invokes, or asserts a diarization backend, and add a
      test that `ingest --diarizer sherpa` and `ingest --speakers 2` are each
      rejected as unrecognized arguments with no bundle directory written. Run
      the file and observe the new test fail — both options still parse.
- [x] 1.5 [req: video-doctor-preflight] In
      `plugins/s/skills/video-ingest/tests/test_video_doctor.py`, delete the
      sherpa- and pyannote-cache tests and remove both models' cache paths from
      the pre-population loop, then add a test that `doctor` with every cache
      cold and no `HF_TOKEN` names no diarization model, token, or gated access
      and exits zero. Run and observe it fail.
- [x] 1.6 [req: video-transcript-schema, video-bundle-contract] In
      `plugins/s/skills/video-ingest/tests/test_video_bundle.py`, update the
      transcript and manifest fixtures and assertions to the new shape: a
      transcript of `version` plus `words` entries of `start`/`end`/`text` with
      no `segments` key and no speaker field, and a manifest with no diarizer,
      diarization, or speaker-count field. Run and observe the failures.

## 2. Remove the engine's diarization surface

- [x] 2.1 [req: video-diarizer-pyannote] Delete
      `plugins/s/skills/video-ingest/scripts/backends/diarize_sherpa.py` and
      `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`.
- [x] 2.2 [req: video-backend-adapters] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, delete both
      `("diarizer", …)` rows from `BACKEND_SCRIPTS` (line 246) and drop the
      diarizer half of `resolve_backends`, leaving ASR resolution and its table
      lookup intact.
- [x] 2.3 [req: video-speaker-count, video-diarizer-pyannote] In the same file,
      delete the `--diarizer` and `--speakers` arguments from the `ingest`
      parser (around line 1355) and delete `resolve_speaker_count`.
- [x] 2.4 [req: video-speaker-samples, video-speaker-merge, video-speaker-roster]
      In the same file, delete the `samples`, `merge-speakers`, and `roster`
      subparsers (lines 1367-1390) and their command functions, leaving
      `doctor`, `ingest`, and `path`.
- [x] 2.5 [req: video-speaker-attribution, video-spurious-turn-filter] In the
      same file, delete the word-to-turn attribution function `join` (line 390)
      with `ATTRIBUTION_FALLBACK_WINDOW`, and the spurious-turn filter with
      `SPURIOUS_TURN_MAX_SECONDS`.
- [x] 2.6 [req: video-transcript-schema] In the same file, delete
      `assemble_segments` (line 504) and rewrite `build_transcript` (line 528) to
      emit `version` plus a `words` array of `start`/`end`/`text` only, with no
      `segments` key and no speaker field. Confirm the transcript assertions from
      1.6 pass.
- [x] 2.7 [req: video-diarization-report] In the same file, delete the
      diarization report and every call that emits it during `ingest`.
- [x] 2.8 [req: video-bundle-contract] In the same file, remove the diarizer
      backend, diarizer model, diarization, and speaker-count fields from the
      manifest written by `ingest`, and drop the diarization backend invocation
      from the ingest flow. Confirm the manifest assertions from 1.6 pass.
- [x] 2.9 [req: video-doctor-preflight] In the same file, delete the
      `SHERPA_CACHE_*` and `PYANNOTE_CACHE_*` constants blocks and their
      `_report_cache` calls in `cmd_doctor`, and restore `_report_cache` to
      `(label, cached, size, fix, warm)` by dropping the now-unused `hint` and
      `warmable` parameters. Confirm the test from 1.5 passes.
- [x] 2.10 [req: video-backend-adapters] In the same file, remove
      `build.video_diarizer` and `build.video_speakers_count` from the
      configuration resolution (lines 96-111) and from the module docstring's
      description of recognized keys. Confirm the test from 1.4 passes.

## 3. Config, skill text, and release

- [x] 3.1 [req: video-speaker-roster] Confirm no tracked configuration carries a
      diarization key: `git grep -n "video_speakers\|video_speakers_count\|video_diarizer" -- '*.json'`
      from the worktree root must return no match outside `.shipd/completed/`. Do
      not edit `.shipd-config.json` — the committed file holds only `valid_themes`,
      and any `build.video_*` entry in a working copy is an uncommitted local
      artifact outside this change.
- [x] 3.2 [req: video-transcript-schema] In
      `plugins/s/skills/video-ingest/SKILL.md`, correct the transcript-shape
      sentence in step 3 of the staged pipeline (around line 64) to describe a
      `words` array of `{start, end, text}` with no `segments` array and no
      speaker field. Change only that description — the speaker-naming and
      arbitration sections belong to `video-brief-grammar-revision`.
- [x] 3.3 [req: *] Run the full video-ingest suite
      (`python3 -m unittest discover -s plugins/s/skills/video-ingest/tests`)
      and confirm every test passes.
- [x] 3.4 [req: *] Run `python3 plugins/s/skills/video-ingest/scripts/video_ingest.py doctor`
      and confirm it exits zero, lists only `ffmpeg`, `uv`, and the ASR model
      caches, and names no diarization model or `HF_TOKEN`.
- [x] 3.5 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` to
      the next patch version, as required for any change touching
      `plugins/s/`.
