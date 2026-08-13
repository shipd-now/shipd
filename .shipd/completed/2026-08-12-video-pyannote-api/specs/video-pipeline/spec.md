## ADDED Requirements

### Requirement: Pyannote backend tracks its pinned API
id: video-pyannote-api-contract

`diarize_pyannote.py` SHALL declare a `pyannote.audio` dependency pinned to the
major version whose API it targets, and SHALL pass the Hugging Face token to
`Pipeline.from_pretrained` under the parameter name that version defines
(`token` for 4.x). Where the backend's tests substitute a double for
`Pipeline`, that double SHALL declare the token parameter as keyword-only under
that same name, so a backend passing a superseded parameter name fails the
suite rather than passing against a stale stub.

#### Scenario: The token reaches the pipeline under the pinned parameter name
- **WHEN** the pyannote backend loads its pipeline with a token available in the
  environment
- **THEN** `Pipeline.from_pretrained` receives that token as the `token` keyword
  argument

#### Scenario: A superseded parameter name fails the suite
- **WHEN** the backend invokes the test double with `use_auth_token=` instead of
  the pinned parameter name
- **THEN** the double rejects the call and the test fails

#### Scenario: The dependency is pinned to the targeted major version
- **WHEN** the backend's inline script dependency metadata is read
- **THEN** its `pyannote.audio` entry carries a version constraint bounding it to
  the major version the backend targets

## MODIFIED Requirements

### Requirement: Dependency preflight
id: video-doctor-preflight
base: c5e8fb760a9c

`video_ingest.py` SHALL provide a `doctor [--fix]` verb reporting each
prerequisite against a tier — `ffmpeg` and `uv` required, the backend model
caches recommended — printing a per-tool state and a concrete install hint, and
exiting non-zero when a required tool is missing. The recommended tier SHALL
include the pyannote diarization backend's model, and where that model is not
cached the verb SHALL name its gated-access requirement — accepting the model's
terms and exporting `HF_TOKEN` — in that entry's hint. If `--fix` is given, then
the verb SHALL install the required tools via Homebrew and pre-warm the backend
model caches, except that it SHALL skip warming the pyannote model and report
the gated-access requirement instead when no `HF_TOKEN` is set; network access
SHALL occur only under `--fix`. If a required tool is missing, then `ingest`
SHALL refuse before extracting any audio.

#### Scenario: Missing required tool fails the check
- **WHEN** `doctor` runs with `ffmpeg` absent
- **THEN** it prints `ffmpeg` as missing with an install hint and exits non-zero

#### Scenario: Cold model cache is reported, not fatal
- **WHEN** `doctor` runs with every required tool present but no backend model
  cached
- **THEN** it reports the cache as recommended-and-absent, names the download
  size, and exits zero

#### Scenario: Ingest refuses a missing prerequisite
- **WHEN** `ingest` runs while a required tool is missing
- **THEN** it reports the missing tool and exits non-zero without writing a
  bundle directory

#### Scenario: The uncached pyannote model names its gated-access requirement
- **WHEN** `doctor` runs with the pyannote diarization model absent from the
  cache
- **THEN** it reports that model at the recommended tier with a hint naming both
  the model's terms acceptance and the `HF_TOKEN` export, and exits zero

#### Scenario: Fix skips the pyannote warm when no token is set
- **WHEN** `doctor --fix` runs with the pyannote model uncached and no `HF_TOKEN`
  in the environment
- **THEN** no warm invocation is made for the pyannote backend, the gated-access
  requirement is reported, and the verb exits zero
