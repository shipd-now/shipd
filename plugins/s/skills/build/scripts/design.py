#!/usr/bin/env python3
"""design.py — the global design scratch area for the design-fidelity
handoff (stdlib only, no network).

A design lives outside the consuming repository so it never enters that
repo's PR: ``path <change>`` resolves and creates
``<designs-root>/<change>``, and ``clean <change>`` removes it. The designs
root defaults to ``~/.shipd/designs`` and is overridable via the resolved
layered configuration's ``build.design_dir`` key, home-expanded — the same
resolution shape as ``build_report.py::build_log_dir`` (design-handoff
design-scratch-area).

``clean`` is fail-soft: a missing directory or a removal failure warns on
stderr and still exits 0, mirroring heartbeat.py's write-tolerance rule, so
cleanup never blocks a build (design-handoff design-scratch-cleanup).
"""

import argparse
import os
import shutil
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import spec_common as sc  # noqa: E402

DEFAULT_DESIGNS_DIR = "~/.shipd/designs"


def design_config(project_dir="."):
    """Return the effective design settings: the resolved layered
    configuration's ``build.design_dir`` key, defaulting to
    ``~/.shipd/designs`` (design-handoff design-scratch-area).

    Read-only — a missing config, a missing ``build`` key, or an unreadable
    config yields the default, so callers always proceed."""
    settings = {"design_dir": DEFAULT_DESIGNS_DIR}
    try:
        config, _prov = sc.resolve_config(os.path.abspath(project_dir))
    except sc.ConfigError:
        return settings
    build = config.get("build")
    if isinstance(build, dict) and build.get("design_dir"):
        settings["design_dir"] = build["design_dir"]
    return settings


def designs_root(config):
    """Return the resolved designs root (default ``~/.shipd/designs``),
    home-expanded, mirroring ``build_report.py::build_log_dir``."""
    return os.path.expanduser(config.get("design_dir") or DEFAULT_DESIGNS_DIR)


def change_design_dir(change, config):
    """Return the absolute per-change design scratch directory."""
    return os.path.join(designs_root(config), change)


def cmd_path(change, project_dir):
    """Resolve and create the change's design scratch directory, printing its
    absolute path."""
    config = design_config(project_dir)
    path = change_design_dir(change, config)
    os.makedirs(path, exist_ok=True)
    print(path)
    return 0


def cmd_clean(change, project_dir):
    """Remove the change's design scratch directory, fail-soft: a missing
    directory or a removal failure warns on stderr and still exits 0."""
    config = design_config(project_dir)
    path = change_design_dir(change, config)
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        print("Warning: design scratch dir not found: %s" % path,
              file=sys.stderr)
    except OSError as exc:
        print("Warning: could not remove design scratch dir %s (%s); "
              "continuing." % (path, exc), file=sys.stderr)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Global design scratch area for the design-fidelity "
                    "handoff (stdlib only).")
    parser.add_argument("--project-dir", default=".",
                        help="project root used to resolve config "
                             "(default: cwd)")
    sub = parser.add_subparsers(dest="verb", required=True)

    p_path = sub.add_parser(
        "path", help="resolve and create the change's design scratch dir")
    p_path.add_argument("change")

    p_clean = sub.add_parser(
        "clean",
        help="remove the change's design scratch dir (fail-soft)")
    p_clean.add_argument("change")

    args = parser.parse_args(argv)
    if args.verb == "path":
        return cmd_path(args.change, args.project_dir)
    if args.verb == "clean":
        return cmd_clean(args.change, args.project_dir)
    return 2


if __name__ == "__main__":
    sys.exit(main())
