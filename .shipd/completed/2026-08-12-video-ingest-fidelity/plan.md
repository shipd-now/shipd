# video-ingest-fidelity
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Give the ingest pipeline a second, more accurate diarization backend, stop the
frame budget from starving scene-change frames, and make the roster's listing
form read-only.

### Motivation

A real 19-minute ingest exposed three defects at once: `sherpa` split two
speakers across 15 labels, every scene-change frame was dropped so the brief
lost all UI-transition evidence, and a bare `roster` rewrote the project's
`.shipd-config.json`. The epic's decision D4 already sanctioned `pyannote` as the
opt-in backend for difficult audio, but only `sherpa` was ever built.

### Details

- Add `diarize_pyannote.py`, a second diarization backend selectable as
  `--diarizer pyannote` / `build.video_diarizer`, honouring the same backend
  contract (`--audio`, `--speakers`, `--warm-cache`, JSON `turns` on stdout).
- Record the diarization outcome in `manifest.json` and warn on stderr when it
  looks implausible, so weak diarization is visible on the run that produced it
  rather than discovered from a wrong brief.
- Reserve a floor of the frame budget for scene candidates so a talky recording
  can no longer drop every scene-change frame.
- Make `roster` with no `--add` print the roster and write nothing.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`, new
`plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`, tests
under `plugins/s/skills/video-ingest/tests/`, and the plugin version bump.

### Non-goals

- **No change to `sherpa`'s clustering defaults.** `CLUSTER_THRESHOLD`,
  `min_duration_on` and `min_duration_off` stay as they are; retuning them
  against a single recording would be guesswork, and the accuracy answer here is
  the alternative backend.
- **No automatic backend switching.** A warning names `pyannote` as the remedy;
  `ingest` never re-runs itself on another backend or silently substitutes one.
- **No change to `video-doctor-preflight`.** `pyannote`'s models are gated and
  cannot be pre-warmed like the HF-hub caches `doctor --fix` already warms.
- **No change to word-level attribution.** `join()` and `assemble_segments()`
  are correct as specified; they only span two speakers when the diarization
  turns handed to them already do.
- **No new repository dependency.** `pyannote.audio` and `torch` are reached
  only through `uv run` PEP 723 metadata, never `requirements.txt`.

## Implementation

- **Files.** `video_ingest.py` (`_frame_candidate_rank`/`resolve_frame_candidates`
  around line 602, `cmd_roster` at 905, the `roster` parser at 1193, the
  `--diarizer` choices at 1170, the `BACKEND_SCRIPTS` table at 238); new
  `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`; tests in
  `plugins/s/skills/video-ingest/tests/`.

- **Scene floor, expressed as a swap after bucket selection.** Bucket selection
  is unchanged; afterwards, if the kept set holds fewer scene frames than
  `scene_floor = min(<deduped scene candidates>, int(max_frames *
  SCENE_FLOOR_FRACTION))`, buckets whose winner is deixis *and* which also hold
  a scene candidate are converted to that bucket's best scene candidate, taken
  highest-scoring scene first, until the floor is met or no convertible bucket
  remains. `SCENE_FLOOR_FRACTION` defaults to 0.25 and is overridable via
  `build.video_scene_floor`. Rejected: reworking `_frame_candidate_rank` into a
  single normalized score across both reasons — scene scores are only
  comparable *within* a recording (see `video-scene-peaks`), so there is no
  stable scale to normalize a deixis anchor against. Rejected: raising the cap —
  it delays starvation rather than fixing it, and costs context in every brief.
  The swap keeps one frame per bucket, so the spread `video-frame-budget`
  already guarantees is preserved.

- **`pyannote` backend.** `diarize_pyannote.py` carries PEP 723 dependencies
  `pyannote.audio` and `torch`, loads `Pipeline.from_pretrained` with the model
  id from `--model` (default `pyannote/speaker-diarization-3.1`), maps
  `--speakers <n>` to the pipeline's `num_speakers`, and emits the same
  `{"turns": [...], "model": ...}` object `sherpa` does, so the orchestrator's
  `run_backend` needs no special case. Rejected: replacing `sherpa` as the
  default — `pyannote` needs a Hugging Face token *and* an accepted gated-model
  licence, which is exactly the first-run friction epic decision D4 rejected the
  default on.

- **Diarization reporting is two pure functions plus a manifest field.**
  `diarization_report(words)` returns `{labels, turns, label_seconds}` from the
  already-attributed words, and `diarization_warnings(report, requested)`
  returns the warning lines. Both are pure, so they are tested without any
  backend. The report lands in `manifest.json` under `diarization`; the warnings
  go to stderr, alongside the existing dropped-frame notices. Two triggers, both
  threshold-free where possible: a requested speaker count that the backend did
  not produce, and — when no count was requested — two or more *minor* labels,
  a label holding under `DIARIZATION_MINOR_LABEL_SHARE` (0.05) of all attributed
  speech. The maps-interview run is the calibration case: 15 labels of which
  several held under 6 s of 1146 s. Rejected: warning on a bare label-count
  threshold — a five-person meeting is not a defect, whereas a swarm of
  near-silent labels is the actual over-clustering signature.

- **Gated access fails loudly, in the backend.** Where `HF_TOKEN`/`HF_HOME`
  credentials are missing or the licence has not been accepted,
  `diarize_pyannote.py` exits non-zero with the exact remediation (accept the
  model terms, export a token) on stderr. `run_backend` already surfaces a
  backend's stderr, so no orchestrator change is needed. `doctor` stays out of
  it (see Non-goals).

- **`roster` listing is read-only.** A bare `roster` prints one name per line
  and returns without opening the config for writing; `--add` behaves exactly as
  today. Rejected: making `--add` mandatory (`parser.error` when absent) — it
  turns an accidental no-op into a hard error without giving the listing form
  anyone would expect from the verb.

- **Risk: concurrent edits to `video_ingest.py`.** `change/video-asr-chunking`
  is unmerged and touches `run_backend` in the same file. The regions differ
  (`run_backend` vs. the frame rank, roster and backend tables), so the two
  should merge cleanly; if they conflict, rebase this change onto that branch's
  merged state rather than reverting either.

- **Risk: `pyannote` is untestable in CI.** Every test stubs the subprocess
  boundary per `video-pipeline-testability`, so the suite must pass on Ubuntu
  with neither `torch` nor a Hugging Face token present. The backend's own
  argument mapping is tested by driving `main()` against a stubbed
  `pyannote.audio` module injected into `sys.modules` — the backend's heavy
  import sits inside `main()`, so the module imports without the dependency.
