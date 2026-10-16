#!/usr/bin/env python3
"""brand — brand commit subjects with the shipd prefix (shipd-brand).

  brand.py subject <text>
  brand.py commit-msg <file>
  brand.py install-hook [--root DIR]

``subject`` prints ``spec_common.brand_subject(text)``. ``commit-msg`` is the
git hook entry: inside a linked worktree whose parent directory is named
``.worktrees`` it rewrites the first non-comment line of the message file
through ``brand_subject``, and otherwise leaves the file alone; it always
exits 0. ``install-hook`` writes the shipd-managed ``commit-msg`` hook into
``<git-common-dir>/hooks`` and prints one line (``installed:``,
``refreshed:``, or ``note: commit branding skipped — <reason>``); it always
exits 0. The hook never blocks a commit. Stdlib only.
"""

import argparse
import os
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import spec_common  # noqa: E402

MARKER = "# shipd-managed commit-msg hook"
WORKTREES_DIR = ".worktrees"


def _git(cwd, *args):
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def brand_message(text):
    """``text`` with its first non-``#`` line branded; unchanged when every
    line is a comment."""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("#"):
            continue
        lines[index] = spec_common.brand_subject(line)
        break
    return "\n".join(lines)


def cmd_commit_msg(path):
    try:
        top = _git(os.getcwd(), "rev-parse", "--show-toplevel")
        if not top:
            return 0
        if os.path.basename(os.path.dirname(top)) != WORKTREES_DIR:
            return 0
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        branded = brand_message(text)
        if branded != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(branded)
    except (OSError, UnicodeError):
        pass
    return 0


def hook_text():
    me = os.path.join(HERE, "brand.py")
    return (
        "#!/bin/sh\n"
        + MARKER + "\n"
        + 'BRAND="%s"\n' % me
        + '[ -f "$BRAND" ] || exit 0\n'
        + "command -v python3 >/dev/null 2>&1 || exit 0\n"
        + 'python3 "$BRAND" commit-msg "$1"\n'
        + "exit 0\n")


def install_hook(root):
    """Install the hook for the repository at ``root``; returns the one line
    to print."""
    def skipped(reason):
        return "note: commit branding skipped — %s" % reason

    if _git(root, "rev-parse", "--git-dir") is None:
        return skipped("not a git repository")
    if _git(root, "config", "core.hooksPath"):
        return skipped("core.hooksPath is set")
    common = _git(root, "rev-parse", "--git-common-dir")
    if not common:
        return skipped("no git directory")
    common = os.path.join(root, common)
    hooks = os.path.join(common, "hooks")
    target = os.path.join(hooks, "commit-msg")
    existed = os.path.exists(target)
    try:
        if existed:
            with open(target, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
            if MARKER not in lines[:3]:
                return skipped("a commit-msg hook already exists")
        os.makedirs(hooks, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(hook_text())
        os.chmod(target, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP
                 | stat.S_IROTH | stat.S_IXOTH)
    except OSError as exc:
        return skipped(str(exc))
    return "%s %s" % ("refreshed:" if existed else "installed:", target)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="brand.py", description="Brand commit subjects.")
    sub = parser.add_subparsers(dest="verb", required=True)
    s = sub.add_parser("subject", help="print the branded subject")
    s.add_argument("text")
    c = sub.add_parser("commit-msg", help="git commit-msg hook entry")
    c.add_argument("file")
    i = sub.add_parser("install-hook", help="install the commit-msg hook")
    i.add_argument("--root", default=os.getcwd())
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.verb == "subject":
        print(spec_common.brand_subject(args.text))
        return 0
    if args.verb == "commit-msg":
        return cmd_commit_msg(args.file)
    print(install_hook(args.root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
