#!/usr/bin/env python3
"""pr_title — render a pull request title from the layered ``pr`` config
(shipd-pr pr-title-render).

  pr_title.py [--root R] title --summary S [--ticket T] [--branch B]

The template comes from ``spec_common.resolve_pr``. The ticket is ``--ticket``,
else the first ``ticket_pattern`` match in the branch name. With no ticket,
``{ticket}`` and the whitespace after it drop out. ``{change}`` is the slug of
a ``change/<slug>`` branch, else empty. Repeated whitespace collapses. The
title prints on stdout; an empty title or a config error is one
``Error: <reason>`` line and exit ``1``. Stdlib only.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))
if BUILD_SCRIPTS not in sys.path:
    sys.path.insert(0, BUILD_SCRIPTS)

import cli_common  # noqa: E402
import spec_common  # noqa: E402

CHANGE_PREFIX = "change/"


def find_ticket(pattern, branch):
    """The first match of ``pattern`` in ``branch``, or ``None``."""
    if not pattern or not branch:
        return None
    match = re.search(pattern, branch)
    return match.group(0) if match else None


def change_slug(branch):
    """The slug of a ``change/<slug>`` branch, else the empty string."""
    if branch and branch.startswith(CHANGE_PREFIX):
        return branch[len(CHANGE_PREFIX):]
    return ""


def render_title(template, summary, ticket, change):
    """Render ``template``. A missing ticket drops ``{ticket}`` and the
    whitespace after it; the result has single spaces and no edge space."""
    if ticket:
        title = template.replace("{ticket}", ticket)
    else:
        title = re.sub(r"\{ticket\}\s*", "", template)
    title = title.replace("{change}", change or "")
    title = title.replace("{summary}", summary or "")
    return re.sub(r"\s+", " ", title).strip()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pr_title.py", description="Render a pull request title.")
    parser.add_argument(
        "--root", default=os.getcwd(),
        help="the directory whose layered config is read (default: cwd)")
    sub = parser.add_subparsers(dest="verb", required=True)
    title = sub.add_parser("title", help="print the rendered title")
    title.add_argument("--summary", required=True,
                       help="the one-sentence summary")
    title.add_argument("--ticket", help="the ticket id; beats the branch")
    title.add_argument("--branch", help="the branch name")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        template, pattern = spec_common.resolve_pr(args.root)
    except spec_common.ConfigError as exc:
        cli_common.err(str(exc))
        return 1
    ticket = args.ticket or find_ticket(pattern, args.branch)
    title = render_title(template, args.summary, ticket,
                         change_slug(args.branch))
    if not title:
        cli_common.err("the rendered title is empty")
        return 1
    print(title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
