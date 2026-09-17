#!/usr/bin/env python3
"""version_guard.py — stdlib-only guard for the plugin version bump
convention (shipd `plugin-version-advance`).

The plugin's cache snapshot is keyed by the version in
``plugins/s/.claude-plugin/plugin.json``. A pull request that edits
``plugins/s/`` without advancing that version leaves ``claude plugin update``
a no-op and every session running the superseded snapshot. This module's
comparison, :func:`find_finding`, is a pure function — no git, no network —
taking a base version, a head version, and the paths a change touched, and
returning a finding string when the change touches ``plugins/s/`` (other than
the manifest itself) without the version increasing, or ``None`` otherwise.
The CLI below is the only part that shells out to git.

Version comparison (:func:`compare_versions`) splits each value on ``.`` and
compares components pairwise as integers where both parse as integers, and as
strings otherwise — never ``float()``, which would collapse ``0.6.9`` and
``0.6.90``.
"""

import argparse
import itertools
import json
import subprocess
import sys

MANIFEST_PATH = "plugins/s/.claude-plugin/plugin.json"
PLUGIN_PREFIX = "plugins/s/"


def compare_versions(base_version, head_version):
    """Compare two dotted version strings component-wise.

    Returns a negative number when ``base_version`` ranks below
    ``head_version``, zero when they rank equal, and a positive number when
    ``base_version`` ranks above it. Each component is compared as an
    integer when both sides parse as one, and as a string otherwise; missing
    trailing components are treated as ``"0"``.
    """
    base_parts = base_version.split(".")
    head_parts = head_version.split(".")
    for base_part, head_part in itertools.zip_longest(
        base_parts, head_parts, fillvalue="0"
    ):
        try:
            base_val = int(base_part)
            head_val = int(head_part)
        except ValueError:
            base_val, head_val = base_part, head_part
        if base_val != head_val:
            return -1 if base_val < head_val else 1
    return 0


def find_finding(base_version, head_version, changed_paths):
    """Return a finding string, or ``None``, for one base/head/paths triple.

    A finding is reported when both hold: at least one changed path lies
    under ``plugins/s/`` other than the manifest itself, and the head version
    does not exceed the base version.
    """
    touches_plugin = any(
        path.startswith(PLUGIN_PREFIX) and path != MANIFEST_PATH
        for path in changed_paths
    )
    if not touches_plugin:
        return None
    if compare_versions(base_version, head_version) < 0:
        return None
    return (
        "plugins/s/ changed without a version bump: "
        f"base version {base_version!r}, head version {head_version!r} "
        "does not exceed it"
    )


def _read_version(ref, cwd=None):
    """Resolve the plugin manifest's ``version`` field at ``ref``.

    Exits 2, naming ``ref``, when the manifest cannot be read at that ref or
    does not parse as JSON with a ``version`` field.
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{MANIFEST_PATH}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError:
        print(
            f"error: could not read {MANIFEST_PATH} at ref {ref!r}",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        manifest = json.loads(result.stdout)
        version = manifest["version"]
    except (json.JSONDecodeError, KeyError, TypeError):
        print(
            f"error: could not parse {MANIFEST_PATH} at ref {ref!r}",
            file=sys.stderr,
        )
        sys.exit(2)
    if not isinstance(version, str):
        print(
            f"error: could not parse {MANIFEST_PATH} at ref {ref!r}",
            file=sys.stderr,
        )
        sys.exit(2)
    return version


def _changed_paths(base, head, cwd=None):
    """List the paths that differ between ``base`` and ``head``."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError:
        print(
            f"error: could not diff {base!r}...{head!r}",
            file=sys.stderr,
        )
        sys.exit(2)
    return [line for line in result.stdout.splitlines() if line]


def main(argv=None, cwd=None):
    parser = argparse.ArgumentParser(
        description=(
            "Fail a pull request that touches plugins/s/ without advancing "
            "the plugin manifest's version."
        )
    )
    parser.add_argument("--base", required=True, help="base ref to compare")
    parser.add_argument("--head", required=True, help="head ref to compare")
    args = parser.parse_args(argv)

    base_version = _read_version(args.base, cwd=cwd)
    head_version = _read_version(args.head, cwd=cwd)
    changed_paths = _changed_paths(args.base, args.head, cwd=cwd)

    finding = find_finding(base_version, head_version, changed_paths)
    if finding is not None:
        print(finding)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
