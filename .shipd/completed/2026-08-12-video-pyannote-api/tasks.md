## 1. Pyannote backend API contract

- [x] 1.1 [req: video-pyannote-api-contract] In
      `plugins/s/skills/video-ingest/tests/test_video_diarize_pyannote.py`,
      redeclare the stub pipeline's `from_pretrained` classmethod (currently
      `from_pretrained(cls, model_id, use_auth_token=None)`, around line 67) as
      `from_pretrained(cls, checkpoint, *, token=None)`, recording
      `(checkpoint, token)`, and update every existing assertion that reads the
      recorded tuple. Run the file and observe the failures — the backend still
      passes `use_auth_token=`.
- [x] 1.2 [req: video-pyannote-api-contract] In the same file, add a test
      asserting the backend passes the environment's token to
      `Pipeline.from_pretrained` as the `token` keyword, and a test asserting
      that invoking the double with `use_auth_token=` raises `TypeError`. Run
      and observe them fail.
- [x] 1.3 [req: video-pyannote-api-contract] In
      `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`
      line 69, change `Pipeline.from_pretrained(args.model, use_auth_token=token)`
      to pass `token=token`. Confirm the tests from 1.1 and 1.2 now pass.
- [x] 1.4 [req: video-pyannote-api-contract] In the same file's inline script
      metadata header (the `# dependencies = [` block, lines 4-7), change the
      `pyannote.audio` entry to `pyannote.audio>=4,<5`.
- [x] 1.5 [req: video-pyannote-api-contract] In
      `plugins/s/skills/video-ingest/tests/test_video_diarize_pyannote.py`, add
      a test that reads `diarize_pyannote.py`'s inline dependency metadata as
      text and asserts its `pyannote.audio` entry carries a version constraint.
      Confirm it passes.

## 2. Doctor preflight for the pyannote model

- [x] 2.1 [req: video-doctor-preflight] In
      `plugins/s/skills/video-ingest/tests/test_video_doctor.py`, add a test
      that `doctor` with the pyannote model uncached prints an entry naming both
      the model's terms acceptance and `HF_TOKEN`, and exits zero. Run and
      observe it fail.
- [x] 2.2 [req: video-doctor-preflight] In
      `plugins/s/skills/video-ingest/scripts/video_ingest.py`, beside the
      `SHERPA_CACHE_*` block (around lines 1114-1129), add a `PYANNOTE_CACHE_*`
      block: label, the Hugging Face repo id already defined as `MODEL_ID` in
      `plugins/s/skills/video-ingest/scripts/backends/diarize_pyannote.py`, a download
      size hint, the `diarize_pyannote.py` script path, and a hint string naming
      the terms acceptance and the `HF_TOKEN` export.
- [x] 2.3 [req: video-doctor-preflight] In the same file, add two optional
      parameters to `_report_cache` (line 1187): `hint=None`, appended to the
      not-cached line when given, and `warmable=True`, which when false skips
      the `if not cached and fix` warm branch entirely so the not-cached line is
      printed instead. Leave the cached branch and both existing call sites
      unchanged.
- [x] 2.4 [req: video-doctor-preflight] In `cmd_doctor` (line 1158), report the
      pyannote model through `_report_cache` using
      `hf_model_cached(PYANNOTE_CACHE_REPO)` and the new hint, after the
      existing sherpa report. Confirm the test from 2.1 passes.
- [x] 2.5 [req: video-doctor-preflight] In
      `plugins/s/skills/video-ingest/tests/test_video_doctor.py`, add a test
      that `doctor --fix` with the pyannote model uncached and no `HF_TOKEN` in
      the environment makes no warm invocation for the pyannote backend and
      exits zero. Run and observe it fail.
- [x] 2.6 [req: video-doctor-preflight] In `cmd_doctor`, pass
      `warmable=bool(os.environ.get("HF_TOKEN"))` on the pyannote
      `_report_cache` call, so `--fix` skips the warm branch and reports the
      gated-access hint when no token is set. Confirm the test from 2.5 passes.

## 3. Verification and release

- [x] 3.1 [req: *] Run the full video-ingest suite
      (`python3 -m unittest discover -s plugins/s/skills/video-ingest/tests`)
      and confirm every test passes.
- [x] 3.2 [req: *] Run `python3 plugins/s/skills/video-ingest/scripts/video_ingest.py doctor`
      and confirm it exits zero and lists the pyannote model entry with its
      gated-access hint.
- [x] 3.3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` to
      the next patch version, as required for any change touching
      `plugins/s/`.
