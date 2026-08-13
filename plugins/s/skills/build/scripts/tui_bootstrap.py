#!/usr/bin/env python3
"""tui_bootstrap.py — self-provisions the delivery board's ``textual`` dep.

Stdlib only, so it is importable (and its missing-``textual`` path
unit-testable) without ``textual`` installed and without creating a real
virtualenv or touching the network — every effectful step is reached through
an injectable seam (``has_textual``/``venv_has_textual``/``run``/``execv``/
``out``/``environ``; see ``ensure_textual``).

``dashboard.py``'s script entry calls :func:`ensure_textual` before its own
module-scope ``textual`` import: when ``textual`` is already importable it is
a no-op; otherwise it creates (or reuses) a dedicated virtualenv under
``${XDG_CACHE_HOME:-~/.cache}/shipd/tui-venv``, installs the pinned
dependency from the repo-root ``requirements.txt``, and ``os.execv``s the same
command with that venv's interpreter. Any failure along the way falls back to
a clear ``pip install`` hint and ``SystemExit(1)`` rather than a traceback.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys

_SETUP_MESSAGE = "Setting up the delivery board..."
_HINT = ("Could not set up the delivery board automatically. "
        "Install its dependency yourself: pip install -r requirements.txt")


def venv_dir(environ):
    """The cache dir the bootstrap's venv lives in, honoring ``XDG_CACHE_HOME``."""
    xdg = environ.get("XDG_CACHE_HOME")
    base = xdg if xdg else os.path.join(environ.get("HOME", os.path.expanduser("~")),
                                        ".cache")
    return os.path.join(base, "shipd", "tui-venv")


def venv_python(vdir):
    """The venv's interpreter path (POSIX layout: ``<vdir>/bin/python``)."""
    return os.path.join(vdir, "bin", "python")


def find_requirements(start_dir):
    """Walk up from ``start_dir`` (the scripts dir) to the repo-root
    ``requirements.txt``; ``None`` if none is found."""
    d = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(d, "requirements.txt")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _default_has_textual():
    try:
        importlib.import_module("textual")
        return True
    except ImportError:
        return False


def _default_venv_has_textual(vpy):
    if not os.path.exists(vpy):
        return False
    try:
        result = subprocess.run([vpy, "-c", "import textual"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except OSError:
        return False


def _default_out(msg):
    print(msg, file=sys.stderr)


def ensure_textual(argv, script, *, has_textual=None, venv_has_textual=None,
                    run=None, execv=None, out=None, environ=None):
    """No-op if ``textual`` is importable; otherwise provision the cached venv
    and re-exec into it, or fall back to a hint + ``SystemExit(1)``.

    ``argv`` is the running process's ``sys.argv`` (its ``[1:]`` — the CLI args
    after the script name — is preserved across the re-exec); ``script`` is
    the entry script's path (``__file__``), used both to locate the
    repo-root ``requirements.txt`` and, on re-exec, as the script argument the
    venv's python is invoked with (a plain interpreter path can't run a script
    on its own). Every effectful seam defaults to the real thing
    (``importlib``/``subprocess.run``/``os.execv``/stderr/``os.environ``) so
    production callers pass nothing.
    """
    has_textual = has_textual if has_textual is not None else _default_has_textual
    venv_has_textual = (venv_has_textual if venv_has_textual is not None
                        else _default_venv_has_textual)
    run = run if run is not None else subprocess.run
    execv = execv if execv is not None else os.execv
    out = out if out is not None else _default_out
    environ = environ if environ is not None else os.environ

    if has_textual():
        return

    vdir = venv_dir(environ)
    vpy = venv_python(vdir)

    if not venv_has_textual(vpy):
        req = find_requirements(os.path.dirname(os.path.abspath(script)))
        if req is None:
            out(_HINT)
            raise SystemExit(1)

        out(_SETUP_MESSAGE)

        result = run([sys.executable, "-m", "venv", vdir])
        if getattr(result, "returncode", 1) != 0:
            out(_HINT)
            raise SystemExit(1)

        result = run([vpy, "-m", "pip", "install", "-r", req])
        if getattr(result, "returncode", 1) != 0:
            out(_HINT)
            raise SystemExit(1)

    execv(vpy, [vpy, script] + list(argv[1:]))
