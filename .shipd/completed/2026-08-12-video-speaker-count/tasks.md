## 1. Fallback window

- [x] 1.1 [req: video-speaker-attribution] In
      `plugins/s/skills/video-ingest/tests/test_video_attribution.py`, add a
      test asserting a word overlapping no turn but sitting 0.3 seconds from the
      nearest one takes that turn's speaker, and update any existing test that
      asserts the old 0.25 s boundary so it exercises the new one. Run and
      observe the 0.3 s case fail.
- [x] 1.2 [req: video-speaker-attribution] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, change
      `ATTRIBUTION_FALLBACK_WINDOW` from `0.25` to `0.35` and update its
      comment to cite observed diarization boundary error rather than a bare
      number. Confirm 1.1 passes and the rest of the suite is unaffected.

## 2. Count resolution

- [x] 2.1 [req: video-speaker-count] In
      `plugins/s/skills/video-ingest/tests/test_video_bundle.py`, add tests for
      resolving `build.video_speakers_count`: a configured integer resolves; an
      absent key yields no count; the `--speakers` flag takes precedence over
      the configured value. Run and observe failure.
- [x] 2.2 [req: video-speaker-count] In `video_ingest.py`, resolve
      `build.video_speakers_count` in `video_config` alongside the existing
      `build.video_*` keys, and add the `--speakers` argument to the `ingest`
      subparser. Confirm 2.1 passes.
- [x] 2.3 [req: video-speaker-count] In
      `plugins/s/skills/video-ingest/tests/test_video_backends.py`, add tests
      asserting `ingest --speakers 0` exits non-zero without invoking any
      backend, and that a negative value is refused the same way. Run and
      observe failure.
- [x] 2.4 [req: video-speaker-count] In `video_ingest.py`, validate the
      resolved count is at least 1 before any backend runs, exiting non-zero
      with a message naming the invalid value. Confirm 2.3 passes.

## 3. Passing it to the backend

- [x] 3.1 [req: video-speaker-count, video-backend-adapters] In
      `test_video_backends.py`, add tests asserting the diarization backend's
      argv carries `--speakers <n>` when a count is resolved and carries no
      `--speakers` element when none is, and that `manifest.json` records the
      requested count only when one was supplied. Run and observe failure.
- [x] 3.2 [req: video-speaker-count, video-backend-adapters] In
      `video_ingest.py`, extend `backend_argv` to append `--speakers <n>` when a
      count is given — mirroring how it appends `--vocab` — thread the count
      through the diarization call only, and record it in the manifest. Confirm
      3.1 passes.
- [x] 3.3 [req: video-backend-adapters] In
      `plugins/s/skills/video-ingest/scripts/backends/asr_parakeet.py` and
      `asr_whisper.py`, add a `--speakers` argument that is accepted and
      ignored, so the backend contract holds for every backend.
- [x] 3.4 [req: video-speaker-count] In
      `plugins/s/skills/video-ingest/scripts/backends/diarize_sherpa.py`, add a
      `--speakers` argument and pass it as `num_clusters` to
      `FastClusteringConfig`, keeping `num_clusters=-1` when the option is
      absent. Do not change `CLUSTER_THRESHOLD`, which governs automatic mode.

## 4. Ship

- [x] 4.1 [req: *] Run the video-ingest suite under a stripped PATH excluding
      ffmpeg and uv — `D=$(mktemp -d); ln -s "$(command -v python3)" $D/python3;
      PATH="$D:/usr/bin:/bin" python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` — and confirm it passes.
- [x] 4.2 [req: *] Run both suites normally —
      `plugins/s/skills/video-ingest/tests` and
      `plugins/s/skills/build/tests` — and confirm they pass.
- [x] 4.3 [req: *] Manual verification on real hardware, the decisive check for
      this change. Ingest the recording in the main checkout — match it with the
      glob `/Users/mikkelbergmann/projects/shipd/docs/research/Screen*.mov`,
      whose filename holds a U+202F space, so never retype it — into a NEW slug
      (do not overwrite `video-ingest-frames-verify`), once with `--speakers 1`
      and once with no flag. Record in the PR description, for each run: the
      number of distinct speaker labels in `transcript.json`, the number of
      segments, and how many turns `filter_spurious_turns` removed. The
      unconstrained run previously produced three labels for one speaker; state
      plainly whether `--speakers 1` produced exactly one.
- [x] 4.4 [req: *] Delete the scratch bundles created by 4.3 and confirm
      `git status --short` in both the worktree and the main checkout shows no
      artifact from this verification.
- [x] 4.5 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.81` to `0.6.82`.
