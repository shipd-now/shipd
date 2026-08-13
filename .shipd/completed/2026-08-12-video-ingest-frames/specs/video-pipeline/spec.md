## MODIFIED Requirements

### Requirement: Bundle contract
id: video-bundle-contract
base: a270e96c500e

`video_ingest.py` SHALL write each ingest to `<video-root>/<slug>/` holding
`manifest.json`, `audio.wav`, `transcript.json`, `frames.json`, and a `frames/`
directory holding the extracted keyframes, where `<video-root>` resolves from
the layered configuration's `build.video_dir` key, home-expanded, defaulting to
`~/.shipd/video` — a location outside any repository. A `path <slug>` verb SHALL
print that absolute directory. `manifest.json` SHALL record the source path,
duration, size, the selected ASR and diarization backends, and their reported
models. If the bundle directory already exists, then `ingest` SHALL refuse
unless `--force` is given.

#### Scenario: Bundle lands outside the repository
- **WHEN** `ingest` completes on a recording
- **THEN** `<video-root>/<slug>/` holds `manifest.json`, `audio.wav`,
  `transcript.json`, `frames.json`, and `frames/`, and no file is written inside
  the repository

#### Scenario: Configured root overrides the default
- **WHEN** the resolved configuration sets `build.video_dir`
- **THEN** `path <slug>` resolves under that root rather than `~/.shipd/video`

#### Scenario: Existing bundle is refused
- **GIVEN** `<video-root>/<slug>/` already exists
- **WHEN** `ingest` runs without `--force`
- **THEN** it exits non-zero and the existing bundle is untouched

## ADDED Requirements

### Requirement: Deixis-anchored frame candidates
id: video-deixis-anchors

`video_ingest.py` SHALL derive frame candidates from the attributed transcript
by matching each word, normalized to lowercase with non-alphanumeric characters
stripped, against a module-level set of spatial demonstratives comprising
`this`, `that`, `these`, `those`, `here` and `there`. The anaphoric pronoun
`it` SHALL NOT be an anchor. Each matched word at time `t` SHALL contribute
candidates at `t-0.5`, `t` and `t+1.5` seconds, each clamped to the recording's
bounds. Candidate derivation SHALL be a pure function over the transcript words.

#### Scenario: Demonstrative yields a three-frame window
- **WHEN** a word `here` starts at 10.0 seconds in a recording longer than 12
  seconds
- **THEN** candidates at 9.5, 10.0 and 11.5 seconds are produced, each marked
  with the anchor word and its start time

#### Scenario: Anaphoric pronoun is not an anchor
- **WHEN** the transcript contains the word `it`
- **THEN** no candidate is produced for it

#### Scenario: Window is clamped to the recording
- **WHEN** a demonstrative starts 0.2 seconds into the recording
- **THEN** the earlier candidate is clamped to 0.0 rather than becoming negative

### Requirement: Scene peaks ranked within the recording
id: video-scene-peaks

`video_ingest.py` SHALL derive additional frame candidates from `ffmpeg` scene
scores computed over the whole recording, selecting **local maxima** — a frame
scoring above both its neighbours — with a non-zero score, enforcing a minimum
separation of `SCENE_PEAK_MIN_GAP_SECONDS` and keeping at most
`ceil(duration / SCENE_PEAK_SECONDS_PER_FRAME)` of them ranked by descending
score. Selection SHALL NOT compare scores against any absolute threshold,
because screen recordings score far below cut-detection thresholds. Parsing
scores from the `ffmpeg` output SHALL be a pure function over that text.

#### Scenario: Peaks are chosen relatively, not by a constant
- **WHEN** every scene score in a recording falls below conventional
  cut-detection thresholds but a few frames score far above their neighbours
- **THEN** those frames are still selected as peaks

#### Scenario: Peak count scales with duration
- **WHEN** a recording's duration allows N peaks by the per-frame-seconds rate
  and more local maxima exist than N
- **THEN** only the N highest-scoring are kept

#### Scenario: Close peaks collapse
- **WHEN** two local maxima fall within the minimum separation
- **THEN** only the higher-scoring one is kept

#### Scenario: A flat recording yields no peaks
- **WHEN** every frame scores zero
- **THEN** no scene candidates are produced and the ingest still succeeds

### Requirement: Candidate merge, dedup and capping
id: video-frame-budget

`video_ingest.py` SHALL merge deixis and scene candidates, dropping a candidate
within `FRAME_DEDUP_MIN_GAP_SECONDS` of an already-kept one and keeping the
earlier, then apply a cap resolved from the configuration's
`build.video_max_frames` key (default 24) by keeping deixis candidates first in
time order and filling any remaining slots with scene candidates by descending
score. Every candidate dropped by the cap SHALL be reported on stderr with its
timestamp and its selection reason.

#### Scenario: Near-duplicate candidates collapse
- **WHEN** a deixis candidate and a scene candidate fall within the dedup gap
- **THEN** only the earlier is kept

#### Scenario: Cap prefers deixis candidates
- **WHEN** the merged candidates exceed the configured cap
- **THEN** deixis candidates are kept in time order before any scene candidate

#### Scenario: Dropped candidates are always reported
- **WHEN** the cap drops one or more candidates
- **THEN** each dropped candidate's timestamp and reason are written to stderr,
  so a capped set is never silently presented as complete

### Requirement: Frame extraction and index
id: video-frame-extraction

`video_ingest.py` SHALL extract each selected candidate as a PNG into the
bundle's `frames/` directory through the injectable runner, scaling so the long
edge is at most 1568 pixels with aspect preserved and no upscaling, and SHALL
write `frames.json` carrying a schema `version` and a `frames` array whose
entries hold the frame's `file`, its `time`, and its selection `reason` —
`deixis` carrying the anchor word and that word's start time, or `scene`
carrying the score. Where no candidate survives selection, `frames/` SHALL
remain empty, `frames.json` SHALL record an empty array, and the ingest SHALL
still succeed.

#### Scenario: Selected frames are written as scaled PNGs
- **WHEN** frame extraction runs for a selected candidate
- **THEN** a PNG is written into the bundle's `frames/` directory and the
  ffmpeg invocation caps the long edge at 1568 pixels without upscaling

#### Scenario: Index records why each frame was chosen
- **WHEN** `frames.json` is written after a mixed selection
- **THEN** each entry names its file and time, a deixis entry carries its anchor
  word and that word's start time, and a scene entry carries its score

#### Scenario: A recording with no candidates still succeeds
- **WHEN** neither a demonstrative nor a scene peak is found
- **THEN** `frames/` is empty, `frames.json` holds an empty array, and the
  ingest exits zero
