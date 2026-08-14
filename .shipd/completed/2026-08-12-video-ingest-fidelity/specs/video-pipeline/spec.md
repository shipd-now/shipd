## ADDED Requirements

### Requirement: Pyannote diarization backend
id: video-diarizer-pyannote

`video_ingest.py` SHALL ship a second diarization backend,
`backends/diarize_pyannote.py`, invoked through the same `uv run` PEP 723 seam
as every other backend and printing the same `{"turns": [{"start", "end",
"speaker"}], "model"}` object the sherpa backend prints. It SHALL declare
`pyannote.audio` and `torch` as PEP 723 inline dependencies only, so neither
enters the repository's own dependency set. Where `--speakers <n>` is supplied,
the backend SHALL pass it to the pipeline as its exact speaker count. The model
id SHALL default to `pyannote/speaker-diarization-3.1` and SHALL be overridable
via `--model <id>`. If the Hugging Face credentials are absent or the gated
model licence has not been accepted, then the backend SHALL exit non-zero with
remediation guidance on stderr rather than hanging or reporting a generic
failure. `--warm-cache` SHALL resolve the model without requiring `--audio`.

#### Scenario: Turns match the backend contract
- **WHEN** the pyannote backend diarizes a recording
- **THEN** it prints one JSON object carrying a `turns` array of `{start, end,
  speaker}` entries plus its `model`, exactly as the sherpa backend does

#### Scenario: A speaker count constrains the pipeline
- **WHEN** the backend is invoked with `--speakers 2`
- **THEN** the pipeline is called with an exact speaker count of 2

#### Scenario: No speaker count leaves the pipeline unconstrained
- **WHEN** the backend is invoked without `--speakers`
- **THEN** the pipeline is called with no speaker-count constraint

#### Scenario: Missing gated-model access fails with guidance
- **WHEN** the backend runs without accepted model terms or a usable token
- **THEN** it exits non-zero and its stderr names the remediation, rather than
  failing with an unexplained error

#### Scenario: The model id is overridable
- **WHEN** the backend is invoked with `--model <other-id>`
- **THEN** that id is loaded instead of the default

#### Scenario: Warming the cache transcribes nothing
- **WHEN** the backend is invoked with `--warm-cache`
- **THEN** it resolves the model and exits zero without diarizing, and without
  requiring `--audio`

### Requirement: Diarization outcome is reported
id: video-diarization-report

`video_ingest.py` SHALL expose the diarization outcome as pure functions over
the speaker-attributed words, and SHALL record that outcome in `manifest.json`
under a `diarization` key carrying the distinct speaker-label count, the turn
count, and the attributed speech seconds per label. Where a speaker count was
requested and the produced label count differs from it, `ingest` SHALL write a
warning to stderr naming both counts. Where no speaker count was requested and
two or more labels each hold less than `DIARIZATION_MINOR_LABEL_SHARE` (0.05) of
all attributed speech, `ingest` SHALL write a warning to stderr naming the
produced label count. Every such warning SHALL name the available remedies —
supplying `--speakers <n>` and selecting a different `--diarizer`. A warning
SHALL NOT fail the ingest, change the bundle's contents, or cause a backend to
be re-run.

#### Scenario: The manifest records the diarization outcome
- **WHEN** an ingest completes
- **THEN** `manifest.json` carries a `diarization` entry with the label count,
  the turn count, and the attributed seconds per label

#### Scenario: A requested count the backend did not produce warns
- **WHEN** `ingest --speakers 2` runs and the backend returns three labels
- **THEN** a warning naming the requested and produced counts is written to
  stderr and the ingest still succeeds

#### Scenario: Over-clustering warns without a requested count
- **WHEN** no speaker count is requested and two or more labels each hold under
  5% of all attributed speech
- **THEN** a warning naming the produced label count is written to stderr

#### Scenario: A plausible diarization warns about nothing
- **WHEN** two labels split the speech evenly and no count was requested
- **THEN** no diarization warning is written

#### Scenario: A warning names the remedies
- **WHEN** any diarization warning is written
- **THEN** its text names both supplying a speaker count and selecting a
  different diarization backend

#### Scenario: Warnings never alter the bundle
- **WHEN** a diarization warning is written
- **THEN** the ingest exits zero and the bundle's transcript and frames are
  identical to a run that emitted no warning

## MODIFIED Requirements

### Requirement: Pluggable transcription and diarization backends
id: video-backend-adapters
base: 840de459dba1

`video_ingest.py` SHALL invoke transcription and diarization as separate
`uv run` scripts carrying PEP 723 inline dependency metadata, each receiving
`--audio <wav>` and printing one JSON object to stdout — an ASR backend a
`words` array of `{start, end, text}` plus its `model`, a diarization backend a
`turns` array of `{start, end, speaker}` plus its `model`. Where a vocabulary is
configured, the orchestrator SHALL additionally pass `--vocab <terms>` to the
ASR backend, and every ASR backend SHALL accept that option — a backend with no
biasing mechanism ignoring it rather than failing. Where a speaker count is
configured, the orchestrator SHALL additionally pass `--speakers <n>` to the
diarization backend, and every backend SHALL accept that option, ignoring it
where it has no use for it. The ASR backend SHALL be selectable as `parakeet`
(default) or `whisper` and the diarization backend as `sherpa` (default) or
`pyannote`, via `--asr` / `--diarizer` or the configuration's `build.video_asr`
/ `build.video_diarizer` keys. If a backend exits non-zero or prints unparseable
stdout, then `ingest` SHALL fail with the backend's stderr attached and SHALL
NOT leave a partial bundle.

#### Scenario: Default backends are selected without flags
- **WHEN** `ingest` runs with no backend flags and no configuration override
- **THEN** the parakeet ASR backend and the sherpa diarization backend are
  invoked, and `manifest.json` records both

#### Scenario: The pyannote diarizer is selectable
- **WHEN** `ingest --diarizer pyannote` runs
- **THEN** the pyannote diarization backend script is invoked and
  `manifest.json` records it as the diarizer

#### Scenario: The configured diarizer is honoured without a flag
- **WHEN** `build.video_diarizer` is `pyannote` and no `--diarizer` flag is given
- **THEN** the pyannote backend is invoked

#### Scenario: Flag overrides the configured backend
- **WHEN** `ingest --asr whisper` runs while the configuration selects
  `parakeet`
- **THEN** the whisper backend is invoked

#### Scenario: Backend failure leaves no partial bundle
- **WHEN** a backend exits non-zero
- **THEN** the ingest fails reporting the backend's stderr, and the bundle
  directory does not exist afterward

#### Scenario: Every ASR backend accepts the vocabulary option
- **WHEN** an ASR backend is invoked with `--vocab` while having no biasing
  mechanism
- **THEN** it ignores the option and transcribes normally rather than exiting
  non-zero

#### Scenario: Every backend accepts the speaker-count option
- **WHEN** a backend is invoked with `--speakers` while having no use for it
- **THEN** it ignores the option and runs normally rather than exiting non-zero

### Requirement: Candidate merge, dedup and capping
id: video-frame-budget
base: dbb43de7f445

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

### Requirement: Speaker roster persistence
id: video-speaker-roster
base: 1b5dc92ea5cf

`video_ingest.py` SHALL provide a `roster --add <name>…` verb appending names to
the resolved project configuration's `build.video_speakers` list, preserving
every other key in that file and creating the file only where absent. Names
already present SHALL NOT be duplicated. Where the verb is invoked with no
`--add` names, it SHALL print the roster's current names to stdout, one per
line, exit zero, and SHALL NOT open the configuration file for writing — a
listing SHALL never modify, reformat, or create the configuration. The roster
SHALL hold names only — no speaker embeddings or other biometric data — and
SHALL NOT be applied automatically to any diarization label.

#### Scenario: A name is added without disturbing other config
- **WHEN** `roster --add Mikk` runs against a config carrying other `build` keys
- **THEN** `build.video_speakers` gains `Mikk` and every other key is unchanged

#### Scenario: Re-adding a known name is a no-op
- **WHEN** a name already in the roster is added again
- **THEN** the list is unchanged and the command still exits zero

#### Scenario: Listing the roster leaves the config untouched
- **WHEN** `roster` runs with no `--add` names against an existing config
- **THEN** the configured names are printed one per line and the config file's
  bytes are unchanged, including its formatting

#### Scenario: Listing never creates a config
- **WHEN** `roster` runs with no `--add` names in a project with no
  configuration file
- **THEN** nothing is printed, the command exits zero, and no configuration file
  is created

#### Scenario: The roster never carries biometric data
- **WHEN** the roster is written
- **THEN** it holds only names, with no embedding or voiceprint field
