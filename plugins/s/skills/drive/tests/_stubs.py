#!/usr/bin/env python3
"""Shared PATH-stubbing helper for the drive test suite (drive-doctor):
tool presence must be synthesized, never borrowed from the host running the
tests, so the suite is deterministic on a machine with none of
`uv`/`ffmpeg`/`ffprobe` installed (as CI is) — and passes with no Playwright
installed at all, since these scripts only check for the `uv` and
`ffmpeg`/`ffprobe` executables on PATH, never import `playwright`.

Copied verbatim in shape from
`plugins/s/skills/video-ingest/tests/_stubs.py`: it writes a tiny
`#!/bin/sh` stub that exits 0 rather than symlinking to a real tool, so a
tool's presence in a built bindir is never contingent on what the host
actually has installed. Nothing under test here executes these stubs (only
`have()`'s `shutil.which` presence check matters), so the stub body's only
job is to exist and be executable."""

import os
import stat

_STUB_BODY = "#!/bin/sh\nexit 0\n"


def stub_bindir(base, name, tools):
    """Build `base/name` containing one executable stub per tool in
    `tools` and return its path. A tool NOT listed is simply absent from
    the directory, which is how the "missing tool" tests simulate that
    tool being unavailable."""
    d = os.path.join(base, name)
    os.makedirs(d, exist_ok=True)
    for tool in tools:
        path = os.path.join(d, tool)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(_STUB_BODY)
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC
                     | stat.S_IXGRP | stat.S_IXOTH)
    return d
