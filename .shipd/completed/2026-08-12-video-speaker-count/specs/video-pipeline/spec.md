## MODIFIED Requirements

### Requirement: Pluggable transcription and diarization backends
id: video-backend-adapters
base: 415cbf4032c8

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
(default) or `whisper` and the diarization backend as `sherpa` (default), via
`--asr` / `--diarizer` or the configuration's `build.video_asr` /
`build.video_diarizer` keys. If a backend exits non-zero or prints unparseable
stdout, then `ingest` SHALL fail with the backend's stderr attached and SHALL
NOT leave a partial bundle.

#### Scenario: Default backends are selected without flags
- **WHEN** `ingest` runs with no backend flags and no configuration override
- **THEN** the parakeet ASR backend and the sherpa diarization backend are
  invoked, and `manifest.json` records both

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

### Requirement: Word-level speaker attribution
id: video-speaker-attribution
base: f1488979bb3c

`video_ingest.py` SHALL expose speaker attribution as a pure function over the
ASR words and diarization turns, assigning each word the speaker of the turn it
most overlaps in time. Where a word overlaps no turn, it SHALL take the speaker
of the nearest turn within `ATTRIBUTION_FALLBACK_WINDOW`, which SHALL be 0.35
seconds to match observed diarization boundary error, and otherwise `null`.
Where a word overlaps two turns equally, it SHALL take the earlier turn, so the
result is deterministic. The function SHALL perform no I/O.

#### Scenario: Word takes its maximum-overlap speaker
- **WHEN** a word spans two turns and overlaps the second more
- **THEN** it is attributed to the second turn's speaker

#### Scenario: Orphan word falls back then yields null
- **WHEN** a word overlaps no turn but starts within the fallback window of one
- **THEN** it takes that turn's speaker, while a word further from every turn is
  attributed `null`

#### Scenario: A word in a 300 ms boundary gap is attributed
- **WHEN** a word overlaps no turn but sits 0.3 seconds from the nearest one
- **THEN** it takes that turn's speaker rather than `null`

#### Scenario: Equal overlap resolves deterministically
- **WHEN** a word overlaps two turns by an identical duration
- **THEN** it is attributed to the earlier turn on every run

## ADDED Requirements

### Requirement: Configured speaker count constrains clustering
id: video-speaker-count

Where a speaker count is supplied by `ingest --speakers <n>` or the resolved
configuration's `build.video_speakers_count` key, `video_ingest.py` SHALL pass
it to the diarization backend, and the sherpa backend SHALL apply it as its
clustering `num_clusters` so the clusterer produces exactly that many speakers.
The flag SHALL take precedence over the configuration key. If the supplied count
is less than 1, then `ingest` SHALL exit non-zero rather than pass a value the
backend would silently read as automatic. If no count is supplied, then no
`--speakers` argument SHALL be passed and clustering SHALL remain automatic, so
existing behaviour is unchanged. `manifest.json` SHALL record the requested
count where one was supplied.

#### Scenario: A configured count reaches the diarization backend
- **WHEN** `ingest --speakers 2` runs
- **THEN** the diarization backend's argv carries `--speakers 2` and
  `manifest.json` records the requested count

#### Scenario: The flag beats the configuration key
- **WHEN** `ingest --speakers 3` runs while `build.video_speakers_count` is 2
- **THEN** the backend receives `3`

#### Scenario: No count leaves clustering automatic
- **WHEN** neither the flag nor the configuration key supplies a count
- **THEN** the backend argv carries no `--speakers` element and the manifest
  records no requested count

#### Scenario: A count below one is refused
- **WHEN** `ingest --speakers 0` runs
- **THEN** it exits non-zero without invoking a backend
