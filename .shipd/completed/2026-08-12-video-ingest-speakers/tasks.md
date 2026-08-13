## 1. Per-speaker samples

- [x] 1.1 [req: video-speaker-samples] In
      `plugins/s/skills/video-ingest/tests/test_video_speakers.py` (new), add
      tests for the pure window-selection function: it picks a window inside the
      label's longest turn; a label whose longest turn is shorter than
      `SAMPLE_SECONDS` yields a window of that turn's duration; a label with
      several equal-length turns resolves deterministically to the earliest. Run
      them and observe they fail.
- [x] 1.2 [req: video-speaker-samples] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, add
      `SAMPLE_SECONDS = 5.0` and a pure `sample_window(turns, label)` returning
      the `(start, duration)` to cut, centred on that label's longest turn and
      clamped to it. No I/O. Confirm 1.1 passes.
- [x] 1.3 [req: video-speaker-samples, video-bundle-contract] In
      `test_video_speakers.py`, add tests for the `samples <slug>` verb: it
      writes one clip per distinct label into the bundle's `samples/`, and the
      ffmpeg argv seeks to the computed start with the computed duration against
      `audio.wav`. Run and observe failure.
- [x] 1.4 [req: video-speaker-samples, video-bundle-contract] In
      `video_ingest.py`, add the `samples` subparser and its implementation,
      cutting each clip through the injectable runner and creating `samples/` if
      absent. Confirm 1.3 passes.

## 2. Label merging

- [x] 2.1 [req: video-speaker-merge] In `test_video_speakers.py`, add tests for
      applying a label→name mapping: two labels sharing a name produce a
      transcript with that single name and no two adjacent segments sharing a
      speaker; a mapping with distinct names per label leaves the speaker count
      unchanged; word-level `speaker` values are rewritten too. Run and observe
      failure.
- [x] 2.2 [req: video-speaker-merge] In `video_ingest.py`, add a pure
      `apply_speaker_names(words, mapping)` relabelling words, and reuse the
      existing `assemble_segments` to rebuild segments. No I/O. Confirm 2.1
      passes.
- [x] 2.3 [req: video-speaker-merge] In `test_video_speakers.py`, add tests for
      the `merge-speakers <slug>` verb: it rewrites the bundle's
      `transcript.json`, and `manifest.json` gains a `speaker_merges` entry
      naming which labels were folded into which name. Run and observe failure.
- [x] 2.4 [req: video-speaker-merge] In `video_ingest.py`, add the
      `merge-speakers` subparser (taking the mapping as repeated
      `--name <label>=<name>` arguments), writing the transcript back and
      recording the mapping in the manifest. Confirm 2.3 passes.

## 3. Roster persistence

- [x] 3.1 [req: video-speaker-roster] In `test_video_speakers.py`, add tests for
      `roster --add`: a name is appended to `build.video_speakers` while every
      other key in the config file is preserved byte-for-byte in value; adding a
      known name is a no-op exiting zero; the file is created when absent; the
      written structure carries names only. Run and observe failure.
- [x] 3.2 [req: video-speaker-roster] In `video_ingest.py`, add the `roster`
      subparser writing the project `.shipd-config.json`, reading the existing file
      first and merging rather than overwriting. Confirm 3.1 passes.

## 4. The naming round in the skill

- [x] 4.1 [req: video-skill-arbitration] In
      `plugins/s/skills/video-ingest/SKILL.md`, replace the "never
      interactively" rule in the speakers section with the gated naming round:
      run it only when two or more labels remain unnamed after mining; cut clips
      with `samples`, play each with `afplay`, state each label's total speech
      duration before asking, offer `build.video_speakers` names as candidates,
      and ask for one name per label in a single round.
- [x] 4.2 [req: video-skill-arbitration] In that same section, specify applying
      the answers with `merge-speakers` and persisting new names with
      `roster --add`, and state that the roster is offered as candidates only
      and never auto-applied to a label.
- [x] 4.3 [req: video-skill-arbitration] In that same section, specify the
      playback fallback: where `afplay` is missing or a clip fails to play,
      continue the round using a transcript excerpt from that label's longest
      turn rather than blocking the brief.
- [x] 4.4 [req: video-skill-arbitration] Re-read the edited section and confirm
      it no longer claims naming is a sibling skill's job, and that the
      single-unnamed-label case still documents the label-as-name fallback.

## 5. Ship

- [x] 5.1 [req: *] Run the video-ingest suite under a stripped PATH excluding
      ffmpeg and uv — `D=$(mktemp -d); ln -s "$(command -v python3)" $D/python3;
      PATH="$D:/usr/bin:/bin" python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` — and confirm it passes. This
      reproduces CI, where neither tool exists.
- [x] 5.2 [req: *] Run both suites normally —
      `plugins/s/skills/video-ingest/tests` and
      `plugins/s/skills/build/tests` — and confirm they pass.
- [x] 5.3 [req: *] Manual verification against the existing bundle at
      `~/.shipd/video/video-ingest-frames-verify` (do not re-ingest). Run `samples`
      and confirm two clips appear; check with `ffprobe` that the `speaker_00`
      clip is about 1.8s (its only turn is shorter than `SAMPLE_SECONDS`) and
      that the `speaker_03` clip is 5.0s. Play one with `afplay` and confirm it
      is audible speech. Record both durations in the PR description.
- [x] 5.4 [req: *] Continuing on a COPY of that bundle (copy it to a scratch
      slug first so the original stays intact), run `merge-speakers` mapping
      both labels to one name, then confirm the rewritten transcript carries one
      speaker, no two adjacent segments share a speaker, and `manifest.json`
      records the merge. Record the before/after speaker counts in the PR
      description.
- [x] 5.5 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.80` to `0.6.81`.
