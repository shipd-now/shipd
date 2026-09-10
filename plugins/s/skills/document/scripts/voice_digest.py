#!/usr/bin/env python3
"""voice_digest.py — the ``SessionStart`` hook that injects the shipd
documentation standard's voice digest into a session.

The digest is the ``## Voice digest`` section of
``skills/document/references/standard.md``: a short, self-contained
distillation of the standard's core rules, written to steer conversational
output when it arrives with no other context. Printing it on stdout is how a
``SessionStart`` hook adds to the session's context.

The hook is **steering, not enforcement**. No hook can rewrite model output;
mechanical checking exists only for files, through ``docs_lint.py``.

Two contracts govern this script:

* **Config-gated.** The layered configuration's ``voice`` key turns the
  injection off (``"voice": false``); absent, it defaults to on. Resolution
  reuses the engine's own upward search so a workspace, a repository, or a home
  directory can all declare it, nearest layer winning.
* **Fail-soft.** Session start must never break because of this script. Every
  failure path — an unimportable engine, an unparseable config layer, a missing
  or sectionless standard — prints nothing and still exits 0.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STANDARD_PATH = os.path.normpath(
    os.path.join(HERE, "..", "references", "standard.md"))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))

# The layered-configuration key that gates the injection (shipd-config
# voice-key), and its built-in default.
VOICE_KEY = "voice"
DEFAULT_VOICE = True

DIGEST_HEADING = "## Voice digest"


def voice_enabled(start):
    """Return whether the ``voice`` key resolves true for ``start``.

    Resolution goes through the engine's ``spec_common.resolve_config`` — the
    same nearest-wins upward search every other shipd surface uses — imported
    lazily so this module stays importable on its own. The key defaults to
    ``True`` when no layer declares it.

    A guarded failure — the engine is absent, or a layer is malformed — returns
    ``False``. Resolution that cannot answer the question is not the same as
    resolution that answers "on": the hook stays quiet rather than injecting
    from an environment it failed to read.
    """
    if BUILD_SCRIPTS not in sys.path:
        sys.path.insert(0, BUILD_SCRIPTS)
    try:
        import spec_common
        config, _provenance = spec_common.resolve_config(start)
    except Exception:
        return False
    return bool(config.get(VOICE_KEY, DEFAULT_VOICE))


def extract_digest(text):
    """Return the body of ``text``'s ``## Voice digest`` section, or ``None``.

    The body is every line after the heading up to the next level-2 heading —
    deeper headings stay inside — with surrounding blank lines trimmed. A
    missing section and an empty one both return ``None``, so the caller has a
    single "nothing to print" answer.
    """
    body = []
    inside = False
    for line in text.splitlines():
        if line.strip() == DIGEST_HEADING:
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            body.append(line)
    if not inside:
        return None
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if not body:
        return None
    return "\n".join(body)


def read_digest(path=STANDARD_PATH):
    """Return the voice digest recorded in the standard at ``path``, or
    ``None`` when the file is unreadable or carries no digest section."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    return extract_digest(text)


def main(argv=None):
    """Print the voice digest when it is enabled and available; exit 0 always.

    Any exception anywhere below is swallowed deliberately — a hook that raises
    at session start is worse than a hook that says nothing.
    """
    try:
        if not voice_enabled(os.getcwd()):
            return 0
        digest = read_digest()
        if digest:
            sys.stdout.write(digest + "\n")
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
