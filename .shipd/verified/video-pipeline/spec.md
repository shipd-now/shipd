# video-pipeline

### Requirement: Dependency preflight
id: video-doctor-preflight

`video_ingest.py` SHALL provide a `doctor [--fix]` verb reporting each
prerequisite against a tier — `ffmpeg` and `uv` required, the ASR model caches
recommended — printing a per-tool state and a concrete install hint, and exiting
non-zero when a required tool is missing. No reported prerequisite SHALL be a
diarization model or require a credentialed or gated model. If `--fix` is given,
then the verb SHALL install the required tools via Homebrew and pre-warm the ASR
model caches; network access SHALL occur only under `--fix`. If a required tool
is missing, then `ingest` SHALL refuse before extracting any audio.

#### Scenario: Missing required tool fails the check
- **WHEN** `doctor` runs with `ffmpeg` absent
- **THEN** it prints `ffmpeg` as missing with an install hint and exits non-zero

#### Scenario: Cold model cache is reported, not fatal
- **WHEN** `doctor` runs with every required tool present but no ASR model
  cached
- **THEN** it reports the cache as recommended-and-absent, names the download
  size, and exits zero

#### Scenario: Ingest refuses a missing prerequisite
- **WHEN** `ingest` runs while a required tool is missing
- **THEN** it reports the missing tool and exits non-zero without writing a
  bundle directory

#### Scenario: No prerequisite is a diarization or credentialed model
- **WHEN** `doctor` runs with every cache cold and no `HF_TOKEN` set
- **THEN** no reported entry names a diarization model, a token, or gated
  access, and the verb exits zero

### Requirement: Bundle contract
id: video-bundle-contract

`video_ingest.py` SHALL write each ingest to `<video-root>/<slug>/` holding
`manifest.json`, `audio.wav`, `transcript.json`, `frames.json`, and a `frames/`
directory holding the extracted keyframes, where `<video-root>` resolves from
the layered configuration's `build.video_dir` key, home-expanded, defaulting to
`~/.shipd/video` — a location outside any repository. A `path <slug>` verb SHALL
print that absolute directory. `manifest.json` SHALL record the source path,
duration, size, the selected ASR backend, and its reported model, and SHALL NOT
record any diarization backend, diarization model, or speaker count. If the
bundle directory already exists, then `ingest` SHALL refuse unless `--force` is
given.

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

#### Scenario: The manifest records no diarization
- **WHEN** `ingest` completes
- **THEN** `manifest.json` names the ASR backend and its model and carries no
  diarizer, diarization, or speaker-count field

### Requirement: Audio extraction and slug derivation
id: video-audio-extraction

`video_ingest.py` SHALL extract the recording's audio to 16 kHz mono PCM WAV via
`ffmpeg`, passing every path as a subprocess argument-list element and never
interpolating one into a shell string. The bundle slug SHALL default to the
source filename with Unicode whitespace and every non-alphanumeric run folded to
a single `-`, lowercased and stripped of leading and trailing separators, and
SHALL be overridable with `--slug`. If the recording carries no audio stream,
then `ingest` SHALL report that and exit non-zero.

#### Scenario: macOS recording filename yields a clean slug
- **WHEN** `ingest` runs on a file named with a U+202F narrow no-break space
  before `am`, as macOS writes timestamped recordings
- **THEN** the derived slug contains only lowercase alphanumerics and single
  `-` separators, and the ffmpeg invocation receives the original path intact

#### Scenario: Audio is normalized for the backends
- **WHEN** audio extraction runs
- **THEN** `audio.wav` is 16 kHz mono PCM regardless of the source's rate or
  channel count

#### Scenario: Silent video is rejected
- **WHEN** `ingest` runs on a file with no audio stream
- **THEN** it reports the missing audio stream and exits non-zero

### Requirement: Pluggable transcription backends
id: video-backend-adapters

`video_ingest.py` SHALL invoke transcription as a separate `uv run` script
carrying PEP 723 inline dependency metadata, receiving `--audio <wav>` and
printing one JSON object to stdout — a `words` array of `{start, end, text}`
plus its `model`. Where a vocabulary is configured, the orchestrator SHALL
additionally pass `--vocab <terms>` to the ASR backend, and every ASR backend
SHALL accept that option — a backend with no biasing mechanism ignoring it
rather than failing. The ASR backend SHALL be selectable as `parakeet` (default)
or `whisper`, via `--asr` or the configuration's `build.video_asr` key, resolved
through a backend table so a further backend can be added as a table entry. If
the backend exits non-zero or prints unparseable stdout, then `ingest` SHALL
fail with the backend's stderr attached and SHALL NOT leave a partial bundle.

#### Scenario: The default backend is selected without flags
- **WHEN** `ingest` runs with no backend flag and no configuration override
- **THEN** the parakeet ASR backend is invoked and `manifest.json` records it

#### Scenario: Flag overrides the configured backend
- **WHEN** `ingest --asr whisper` runs while the configuration selects
  `parakeet`
- **THEN** the whisper backend is invoked

#### Scenario: A diarizer option is rejected
- **WHEN** `ingest --diarizer sherpa` or `ingest --speakers 2` runs
- **THEN** the invocation is rejected as an unrecognized argument and no bundle
  directory is written

#### Scenario: Backend failure leaves no partial bundle
- **WHEN** the backend exits non-zero
- **THEN** the ingest fails reporting the backend's stderr, and the bundle
  directory does not exist afterward

#### Scenario: Every ASR backend accepts the vocabulary option
- **WHEN** an ASR backend is invoked with `--vocab` while having no biasing
  mechanism
- **THEN** it ignores the option and transcribes normally rather than exiting
  non-zero

### Requirement: Transcript schema
id: video-transcript-schema

`transcript.json` SHALL carry a schema `version` and a `words` array whose
entries hold `start`, `end`, and `text`, ordered by `start`. It SHALL NOT carry
a `segments` array, nor any speaker field on the transcript or on a word.

#### Scenario: Words are ordered and speaker-free
- **WHEN** a transcript is written
- **THEN** its `words` entries carry only `start`, `end`, and `text`, ordered by
  start time

#### Scenario: No segments array is written
- **WHEN** a transcript is written
- **THEN** the document holds `version` and `words` and no `segments` key

### Requirement: Dependency-free test surface
id: video-pipeline-testability

Every subprocess the pipeline runs SHALL go through an injectable runner with
signature `run(args, input=None) -> (rc, stdout, stderr)`, so the test suite
exercises the orchestrator with no `ffmpeg`, `uv`, or `mlx` installed. The suite
SHALL live at `plugins/s/skills/video-ingest/tests/` and SHALL be discovered by
its own `ci` step.

#### Scenario: Suite passes on a machine without the toolchain
- **WHEN** the video-ingest suite runs with no `ffmpeg`, `uv`, or `mlx` present
- **THEN** every test passes, driving fake runners rather than real tools

#### Scenario: CI discovers the suite
- **WHEN** the `ci` workflow runs
- **THEN** it discovers and runs `plugins/s/skills/video-ingest/tests/`

### Requirement: Configured vocabulary biases transcription
id: video-vocabulary-biasing

Where the resolved configuration's `build.video_vocabulary` key holds a
non-empty list of terms, `video_ingest.py` SHALL pass them to the ASR backend as
a single comma-separated `--vocab` value, and the whisper backend SHALL apply
them as Whisper's `initial_prompt` so the decoder is biased toward them. If the
key is absent or empty, then no `--vocab` argument SHALL be passed and
transcription behaviour SHALL be unchanged. The parakeet backend SHALL document
that it accepts and ignores `--vocab`, because `parakeet_mlx` exposes no
biasing parameter.

#### Scenario: Configured terms reach the whisper backend
- **WHEN** `build.video_vocabulary` lists domain terms and `ingest --asr
  whisper` runs
- **THEN** the whisper backend is invoked with a `--vocab` argument carrying
  those terms, and applies them as its `initial_prompt`

#### Scenario: Absent vocabulary changes nothing
- **WHEN** no `build.video_vocabulary` key is configured
- **THEN** the ASR backend is invoked with no `--vocab` argument

#### Scenario: Parakeet tolerates a configured vocabulary
- **WHEN** `build.video_vocabulary` is configured and the default parakeet
  backend runs
- **THEN** the ingest succeeds and the transcript is produced, the option having
  been ignored

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
`build.video_max_frames` key (default 24) by **distributing the budget across
the recording**: the recording SHALL be divided into as many equal-width
buckets as the cap allows and at most one candidate SHALL be taken from each
occupied bucket, so the kept frames span the recording rather than clustering
wherever candidates are densest. Within a bucket a deixis candidate SHALL be
preferred over a scene candidate; among candidates of the same reason the
higher-scoring scene peak or the earlier deixis anchor SHALL win. The selection
SHALL then reserve a **scene floor**: where the kept set holds fewer scene
candidates than `int(cap * SCENE_FLOOR_FRACTION)` — a fraction defaulting to
0.25 and overridable via the configuration's `build.video_scene_floor` key —
buckets whose winner is a deixis candidate and which also hold a scene
candidate SHALL be converted to that bucket's highest-scoring scene candidate,
taken highest-scoring first, until the floor is met or no convertible bucket
remains, so a recording dense in deixis anchors cannot drop every scene frame.
The floor SHALL never exceed the number of scene candidates available, and
SHALL never raise the kept count above the cap. Where buckets are empty, the
unused slots SHALL be backfilled from the remaining unselected candidates under
the same preference, so a sparse recording still yields as many frames as the
candidates allow. Where the merged candidates do not exceed the cap, every
candidate SHALL be kept. Every candidate dropped by the cap SHALL be reported on
stderr with its timestamp and its selection reason.

#### Scenario: Near-duplicate candidates collapse
- **WHEN** a deixis candidate and a scene candidate fall within the dedup gap
- **THEN** only the earlier is kept

#### Scenario: Kept frames span the recording
- **WHEN** the merged candidates exceed the cap and cluster heavily in the
  recording's opening minutes
- **THEN** the kept frames are spread across the recording's full duration
  rather than confined to the region where candidates are densest

#### Scenario: A dense early stretch cannot starve later candidates
- **WHEN** enough deixis candidates occur early to fill the cap on their own,
  and scene candidates occur later in the recording
- **THEN** later candidates are still selected, because each bucket contributes
  at most one frame

#### Scenario: Deixis anchors cannot starve every scene frame
- **WHEN** every bucket holds a deixis candidate and scene candidates share
  some of those buckets
- **THEN** at least `int(cap * SCENE_FLOOR_FRACTION)` kept frames are scene
  candidates, rather than the kept set being entirely deixis

#### Scenario: The floor never exceeds the scene candidates available
- **WHEN** fewer scene candidates exist than the floor would reserve
- **THEN** every available scene candidate is kept and no deixis winner is
  displaced beyond that

#### Scenario: The floor does not change the kept count
- **WHEN** the scene floor converts one or more bucket winners
- **THEN** the number of kept frames is unchanged, one per occupied bucket as
  before

#### Scenario: Deixis still wins inside a bucket
- **WHEN** a bucket holds both a deixis candidate and a scene candidate, and the
  scene floor is already satisfied
- **THEN** the deixis candidate is the one kept for that bucket

#### Scenario: Empty buckets backfill rather than waste the budget
- **WHEN** some buckets hold no candidate and unselected candidates remain
- **THEN** the unused slots are filled from those remaining candidates, so the
  kept count is limited by the candidates available, not by bucket occupancy

#### Scenario: An under-cap recording keeps every candidate
- **WHEN** the merged candidates number fewer than the cap
- **THEN** every candidate is kept and none is dropped

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
