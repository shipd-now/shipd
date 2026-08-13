#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "parakeet-mlx",
# ]
# ///
"""asr_parakeet.py — the default ASR backend for video_ingest.py, invoked as
``uv run asr_parakeet.py --audio <wav>`` (video-backend-adapters).

Transcribes on-device via Apple MLX (senstella/parakeet-mlx), which resolves
`MODEL_ID` from the Hugging Face hub cache — the same cache
`video_ingest.py doctor` inspects and `doctor --fix` pre-warms.

Prints one JSON object to stdout: ``{"words": [{"start", "end", "text"}],
"model": MODEL_ID}``. Any failure (missing audio, model load error,
transcription error) is reported on stderr with a non-zero exit, matching the
backend contract `video_ingest.py` enforces on every backend.

``--warm-cache`` downloads the model without requiring ``--audio`` — the code
path `doctor --fix` invokes to pre-warm the cache ahead of a first `ingest`.

``--chunk-duration``/``--overlap-duration`` bound the encoder's activation
memory: the transcription is windowed rather than run over the whole recording
in one pass, so peak memory is a function of the window, not of the recording's
length. See `DEFAULT_CHUNK_DURATION` for why the API default is unusable here.

``--vocab <comma-joined terms>`` is accepted and ignored (video-backend-
adapters): `parakeet_mlx`'s `model.transcribe` exposes only `path, dtype,
decoding_config, chunk_duration, overlap_duration, chunk_callback` — no
prompt, vocabulary, or context parameter — so this backend has no biasing
mechanism to apply the option to. The option is accepted purely for backend
contract compatibility with `video_ingest.py`, which passes `--vocab` to
every ASR backend when a vocabulary is configured.

Note: `model.transcribe()`'s `AlignedSentence.tokens` are sub-word pieces, not
whole words — confirmed against a real run (video-pipeline-pipeline manual
verification): a new word's token text carries a leading space (e.g.
``' automatic'``), and a continuation piece does not (e.g. ``'ic'``), matching
the SentencePiece convention `AlignedSentence.text` relies on
(`"".join(t.text for t in tokens)`). `words_from_tokens` regroups tokens on
that leading-space boundary so the emitted ``words`` are real words, not
sub-word fragments.
"""

import argparse
import json
import sys

MODEL_ID = "mlx-community/parakeet-tdt-0.6b-v2"

# `BaseParakeet.transcribe` defaults to `chunk_duration=None`, which encodes
# the *entire* recording in a single forward pass — activation memory grows
# with the audio's length, and a 19-minute screen recording drove a real run
# past 25 GB of unified memory before the kernel killed the backend. Chunking
# bounds that cost to a fixed window regardless of duration. These are
# `parakeet-mlx`'s own CLI defaults (120 s windows, 15 s overlap), which the
# library applies for exactly this reason; only the Python API defaults to
# unchunked. `0` disables chunking, matching that CLI's contract.
DEFAULT_CHUNK_DURATION = 120.0
DEFAULT_OVERLAP_DURATION = 15.0


def words_from_tokens(tokens):
    """Regroup parakeet-mlx's sub-word `AlignedToken`s into whole words: a
    new word starts wherever a token's text carries a leading space (or at
    the very first token); continuation pieces (no leading space) extend the
    current word. Pure — operates on plain (start, end, text) tuples so it
    is testable without the `parakeet_mlx` dependency."""
    words = []
    current = None
    for start, end, text in tokens:
        if current is None or text.startswith(" ") or text.startswith("\n"):
            current = {"start": start, "end": end, "text": text.strip()}
            if current["text"]:
                words.append(current)
            else:
                current = None
        else:
            current["end"] = end
            current["text"] += text.strip()
    return words


def main(argv=None):
    parser = argparse.ArgumentParser(prog="asr_parakeet")
    parser.add_argument("--audio", help="path to the 16 kHz mono WAV to transcribe")
    parser.add_argument("--warm-cache", action="store_true",
                        help="download the model and exit, without "
                             "transcribing anything")
    parser.add_argument("--vocab", default=None,
                        help="accepted for backend contract compatibility "
                             "and ignored: parakeet_mlx exposes no biasing "
                             "parameter")
    parser.add_argument("--chunk-duration", type=float,
                        default=DEFAULT_CHUNK_DURATION,
                        help="seconds of audio per encoder pass; 0 disables "
                             "chunking and encodes the whole recording at "
                             "once (default: %(default)s)")
    parser.add_argument("--overlap-duration", type=float,
                        default=DEFAULT_OVERLAP_DURATION,
                        help="seconds of overlap between chunks, so a word "
                             "spanning a boundary is not lost "
                             "(default: %(default)s)")
    args = parser.parse_args(argv)

    if not args.warm_cache and not args.audio:
        parser.error("--audio is required unless --warm-cache is given")

    # An overlap at or past the window leaves `parakeet_mlx`'s chunk loop —
    # `range(0, len(audio), chunk_samples - overlap_samples)` — with a
    # non-positive step. A negative step makes the range *empty*, so nothing is
    # ever encoded and the backend reports an empty transcript with a success
    # exit; a zero step raises deep inside the library. Both are far worse than
    # refusing the pair up front, an empty transcript worst of all: it is
    # silently wrong rather than loudly broken.
    if args.chunk_duration and args.overlap_duration >= args.chunk_duration:
        parser.error(
            "--overlap-duration (%g) must be less than --chunk-duration (%g)"
            % (args.overlap_duration, args.chunk_duration))

    try:
        from parakeet_mlx import from_pretrained
        model = from_pretrained(MODEL_ID)
        if args.warm_cache:
            return 0

        result = model.transcribe(
            args.audio,
            chunk_duration=(args.chunk_duration
                            if args.chunk_duration else None),
            overlap_duration=args.overlap_duration)
        tokens = [
            (token.start, token.end, token.text)
            for sentence in result.sentences for token in sentence.tokens
        ]
        words = words_from_tokens(tokens)
        print(json.dumps({"words": words, "model": MODEL_ID}))
        return 0
    except Exception as exc:  # noqa: BLE001 - report any failure to stderr
        print("asr_parakeet: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
