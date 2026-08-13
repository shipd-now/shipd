#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mlx-whisper",
# ]
# ///
"""asr_whisper.py — the `--asr whisper` ASR backend for video_ingest.py,
invoked as ``uv run asr_whisper.py --audio <wav>`` (video-backend-adapters).

Transcribes on-device via Apple MLX (ml-explore/mlx-examples' `mlx_whisper`),
which resolves `MODEL_ID` from the Hugging Face hub cache — the same cache
`video_ingest.py doctor` inspects and `doctor --fix` pre-warms.

Prints one JSON object to stdout: ``{"words": [{"start", "end", "text"}],
"model": MODEL_ID}``. Any failure (missing audio, model load error,
transcription error) is reported on stderr with a non-zero exit, matching the
backend contract `video_ingest.py` enforces on every backend.

``--warm-cache`` downloads the model without requiring ``--audio`` — the code
path `doctor --fix` invokes to pre-warm the cache ahead of a first `ingest`.

``--vocab <comma-joined terms>`` (video-vocabulary-biasing) renders the
configured domain terms into a single sentence and passes it to
`mlx_whisper.transcribe` as `initial_prompt` — a parameter its signature
accepts — biasing the decoder toward them. Omitted entirely when no
``--vocab`` is given, so behaviour is unchanged.
"""

import argparse
import json
import sys

MODEL_ID = "mlx-community/whisper-large-v3-turbo"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="asr_whisper")
    parser.add_argument("--audio", help="path to the 16 kHz mono WAV to transcribe")
    parser.add_argument("--warm-cache", action="store_true",
                        help="download the model and exit, without "
                             "transcribing anything")
    parser.add_argument("--vocab", default=None,
                        help="comma-separated domain terms to bias "
                             "transcription toward, applied as Whisper's "
                             "initial_prompt")
    args = parser.parse_args(argv)

    if not args.warm_cache and not args.audio:
        parser.error("--audio is required unless --warm-cache is given")

    try:
        import mlx_whisper

        if args.warm_cache:
            # Loading the model resolves (and downloads, if absent) the HF
            # hub cache entry doctor inspects — no audio is required.
            from mlx_whisper.load_models import load_model
            load_model(MODEL_ID)
            return 0

        kwargs = {}
        if args.vocab:
            terms = [t.strip() for t in args.vocab.split(",") if t.strip()]
            if terms:
                kwargs["initial_prompt"] = (
                    "Domain terms: %s." % ", ".join(terms))
        output = mlx_whisper.transcribe(
            args.audio, path_or_hf_repo=MODEL_ID, word_timestamps=True,
            **kwargs)
        words = []
        for segment in output.get("segments", []):
            for w in segment.get("words", []):
                words.append({
                    "start": w["start"],
                    "end": w["end"],
                    "text": w["word"].strip(),
                })
        print(json.dumps({"words": words, "model": MODEL_ID}))
        return 0
    except Exception as exc:  # noqa: BLE001 - report any failure to stderr
        print("asr_whisper: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
