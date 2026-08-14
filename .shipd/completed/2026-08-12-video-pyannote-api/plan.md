# video-pyannote-api
Status: verified

## Idea

Repair the pyannote diarization backend against the pyannote.audio version it
actually resolves, and make `doctor` report the backend's readiness instead of
implying it.

### Motivation

`diarize_pyannote.py:69` passes `use_auth_token=`, which pyannote.audio 4.x
renamed to `token=`, so `--diarizer pyannote` — a backend `video-backend-adapters`
promises is selectable — fails at model load on every invocation. Three
surfaces hid it: the dependency is unpinned so 4.x resolves against 3.x-era
code, the test double declares the superseded parameter name and so passes
against the bug, and `video-doctor-preflight` never checks this backend at all.

### Details

- Pass the token under the parameter name of a pinned `pyannote.audio` major
  version, and pin that dependency in the backend's inline script metadata.
- Make the test double declare the token parameter keyword-only under the real
  name, so a revert to a superseded name fails the suite instead of passing.
- Add the pyannote model to `doctor`'s recommended tier, naming the gated-access
  requirement (accept the model terms, export `HF_TOKEN`) in its hint, and skip
  `--fix` warming when no token is set.

Affected capabilities: `video-pipeline` (modified). Impact:
`plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`,
`plugins/s/skills/video-ingest/scripts/video_ingest.py` (the `doctor` tier
tables and `_report_cache`),
`plugins/s/skills/video-ingest/tests/test_video_diarize_pyannote.py`,
`plugins/s/skills/video-ingest/tests/test_video_doctor.py`, and the plugin
version in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to sherpa's diarization quality, its clustering constants, or which
  diarizer is the default — that is a separate change, deliberately sequenced
  after this one so the pyannote alternative is testable before it is judged.
- No substitution of an ungated model mirror: `pyannote/speaker-diarization-3.1`
  stays the default model id, and its gated access stays a user prerequisite.
- No end-to-end verification against real audio, which requires a Hugging Face
  token this repository cannot supply.
- No fix for `_report_cache`'s existing assumption that a warm attempt
  succeeded; the pyannote path avoids that branch rather than reworking it.

## Implementation

- **Pin to the 4.x API rather than to 3.x.** Constrain `pyannote.audio` to
  `>=4,<5` and call `Pipeline.from_pretrained(..., token=...)`. Rejected:
  pinning `<4` to keep `use_auth_token=` working — it freezes the backend on a
  superseded major purely to avoid a one-word rename, and 4.0.7 is what the
  resolver already produces.
- **The test double is the drift guard.** Declare the double's signature as
  `from_pretrained(cls, checkpoint, *, token=None)` — keyword-only. A backend
  passing `use_auth_token=` then raises `TypeError` inside the suite. Rejected:
  introspecting the real `pyannote.audio` signature in a test, which would
  violate the capability's dependency-free test surface (`video-pipeline`'s
  "Dependency-free test surface" requirement) since CI installs neither
  `pyannote.audio` nor `torch`.
- **Give the pyannote model its own constants block, not an `HF_MODEL_CACHES`
  row.** Its `--fix` behaviour is conditional on `HF_TOKEN`, which the uniform
  table rows cannot express; mirror the existing `SHERPA_CACHE_*` block instead
  and add an optional `hint=None` parameter to `_report_cache` for the gated
  access line. Rejected: widening every `HF_MODEL_CACHES` tuple, which would
  force two unrelated ASR rows to carry fields only pyannote uses.
- **Warming without a token is skipped at the branch, not inside the callable.**
  `_report_cache` sets `cached = True` immediately after calling `warm()`, so a
  warm callable that merely declines to run would still be reported as cached.
  Add a `warmable=True` parameter instead: when it is false the warm branch is
  skipped entirely and the not-cached line — carrying the gated-access hint —
  is printed. `cmd_doctor` passes `warmable` as whether `HF_TOKEN` is set, so
  `--fix` never fails on an optional backend the user has not opted into.
  Rejected: a no-op warm callable, which that optimistic assignment would
  silently convert into a false "cached" report.

Risk: the pin masks a future 5.x rename exactly as the missing pin masked this
one. Guarded by the keyword-only double — a rename that reaches the backend
fails the suite — but the pin's upper bound still needs a human to raise it.
