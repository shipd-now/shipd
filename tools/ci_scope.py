#!/usr/bin/env python3
"""Classify a pull request's changed paths into a CI scope.

Prints ``scope=content`` only when every changed path lies under an
allowlisted planning-content directory, which lets CI skip its test suites;
anything else, and any failure, prints ``scope=full``. The script always
exits 0, so a broken classifier costs time, never test coverage. Stdlib only.
"""

import argparse
import subprocess
import sys

# The one constant to widen if a directory proves safe to skip tests for.
ALLOWED_PREFIXES = (".shipd/epics/", ".shipd/research/", ".shipd/docs/")

# The two CI scopes: planning content only, or everything else.
CONTENT = "content"
FULL = "full"


def classify(paths):
    """Return CONTENT only for a non-empty list of allowlisted, clean paths.

    Every other list returns FULL.
    """
    if not paths:
        return FULL
    for path in paths:
        if "\\" in path or ".." in path.split("/"):
            return FULL
        if not path.startswith(ALLOWED_PREFIXES):
            return FULL
    return CONTENT


def changed_paths(base, head):
    """List paths changed between base and head (three-dot diff).

    Raises subprocess.CalledProcessError or OSError when git fails.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "-z", f"{base}...{head}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [p for p in result.stdout.split("\0") if p]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output")
    args = parser.parse_args(argv)

    scope = FULL
    if args.event != "pull_request":
        reason = f"event {args.event!r} is not pull_request"
    else:
        try:
            paths = changed_paths(args.base, args.head)
        except (subprocess.CalledProcessError, OSError) as exc:
            paths = None
            reason = f"git diff failed: {exc}"
        if paths is not None:
            scope = classify(paths)
            reason = (
                f"all {len(paths)} changed path(s) are allowlisted"
                if scope == CONTENT
                else f"{len(paths)} changed path(s) include non-allowlisted content"
            )
    line = f"scope={scope}"
    print(f"{line} ({reason})")
    if args.github_output:
        try:
            with open(args.github_output, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            print(f"could not write {args.github_output}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
