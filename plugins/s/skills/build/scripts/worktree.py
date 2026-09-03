#!/usr/bin/env python3
"""worktree.py — the engine's worktree front door (stdlib only, no network).

The workflow is: one change = one worktree = one branch = one PR. This script
is the *engine* side of that: it owns the create path — the git mechanics plus
the repo's configured ``post-worktree-scripts`` — and passes the guarded
teardown verbs straight through to ``worktree.sh``, which keeps owning them.

Dispatch mirrors ``worktree.sh``'s, so the two are invoked identically:

  * ``remove`` and ``prune-branches`` re-execute ``worktree.sh`` with the
    arguments passed through verbatim, preserving its output and exit code —
    no behavior of the battle-tested guarded teardown is reimplemented here.
  * ``hooks`` selects the hook-management verb family, which edits the
    ``post-worktree-scripts`` declaration so no flow ever hand-edits
    ``.shipd-config.json``.
  * any other first argument is a change name for the create path.

The create path resolves and validates ``post-worktree-scripts`` *before* any
git mutation, so a malformed declaration never leaves a half-set-up worktree.
It then runs ``worktree.sh``'s create path from the repo root with output
inherited and, when that succeeds and ``.worktrees/<name>`` did not exist
beforehand, runs the configured scripts in order against the new worktree. A
*reused* worktree was already set up when it was created, so its scripts are
skipped; ``hooks run`` covers a manual re-run.

Exit codes: ``0`` success, ``1`` usage/error, ``2`` a guard refusal passed
through from ``worktree.sh``, ``3`` a post-worktree script failed.

Usage (run from the repository root):
  worktree.py <change-name> [--fresh] [--root DIR]
  worktree.py remove <change> [--force]
  worktree.py prune-branches
  worktree.py hooks list [--json] [--root DIR]
  worktree.py hooks add <item> [--root DIR]
  worktree.py hooks remove <item-or-index> [--root DIR]
  worktree.py hooks run [--root DIR]
"""

import json
import os
import subprocess
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402

# The bash helper that owns the git mechanics and the guarded teardown.
WORKTREE_SH = os.path.join(SCRIPTS_DIR, "worktree.sh")

# The config key holding the ordered list of shell command lines the create
# path runs after a worktree is created (shipd-config
# post-worktree-scripts-key).
HOOKS_KEY = "post-worktree-scripts"

# The verbs that are not change names.
PASSTHROUGH_VERBS = ("remove", "prune-branches")

# The exit code a failing post-worktree script produces — deliberately distinct
# from worktree.sh's `1` (usage/error) and `2` (guard refusal), so a caller can
# tell "the worktree exists but its setup failed" from "no worktree".
HOOK_FAILURE_EXIT = 3

USAGE = """usage: worktree.py <change-name> [--fresh] [--root DIR]
       worktree.py remove <change> [--force]
       worktree.py prune-branches
       worktree.py hooks list [--json] [--root DIR]
       worktree.py hooks add <item> [--root DIR]
       worktree.py hooks remove <item-or-index> [--root DIR]
       worktree.py hooks run [--root DIR]
  <change-name> must be kebab-case (lowercase letters, digits, hyphens)
  --fresh: never adopt an existing worktree or unmerged branch
  --root:  repository root the verb operates on (default: cwd)"""


def usage(stream=None):
    (stream if stream is not None else sys.stderr).write(USAGE + "\n")


# ---------------------------------------------------------------------------
# Config: the post-worktree-scripts key
# ---------------------------------------------------------------------------

def resolve_hooks(root):
    """Resolve ``(items, source)`` for ``root``'s ``post-worktree-scripts``
    (shipd-config post-worktree-scripts-key).

    ``items`` is the effective list — empty when no layer declares the key —
    and ``source`` the path of the config file that declared it, or ``None``
    for an undeclared key. The key merges nearest-wins-wholesale like every
    other top-level key, so a workspace root's declaration governs every member
    repo beneath it. A *declared* value that is not a list of non-empty strings
    raises :class:`spec_common.ConfigError` naming the key, the offending
    value, and the file that supplied it."""
    config, prov = sc.resolve_config(root)
    if HOOKS_KEY not in config:
        return [], None
    raw = config[HOOKS_KEY]
    source = prov.get(HOOKS_KEY, "default")
    if not isinstance(raw, list):
        raise sc.ConfigError(
            "`%s` must be a JSON list of shell command lines (from %s), "
            "got %r" % (HOOKS_KEY, source, raw))
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise sc.ConfigError(
                "`%s` items must be non-empty strings (from %s), got %r"
                % (HOOKS_KEY, source, item))
    return list(raw), source


# ---------------------------------------------------------------------------
# Hook execution (worktree-hooks post-worktree-execution)
# ---------------------------------------------------------------------------

def hook_env(worktree, root, change):
    """The environment a post-worktree script runs under: the parent
    environment extended with the three ``SHIPD_*`` variables that tell the
    script where and what it is setting up."""
    env = dict(os.environ)
    env["SHIPD_WORKTREE"] = os.path.abspath(worktree)
    env["SHIPD_ROOT"] = os.path.abspath(root)
    env["SHIPD_CHANGE"] = change
    return env


def run_hooks(items, worktree, root, change):
    """Run ``items`` in order as shell command lines with ``worktree`` as the
    working directory, announcing each before it runs.

    Returns ``0`` when every item succeeded, or :data:`HOOK_FAILURE_EXIT` on
    the first non-zero exit — the chain stops there and the failing item and
    its exit code are reported. The created worktree is never torn down: a
    partial setup is resumable with ``hooks run``."""
    env = hook_env(worktree, root, change)
    for item in items:
        sys.stdout.write("post-worktree: running %s\n" % item)
        sys.stdout.flush()
        code = subprocess.run(item, shell=True, cwd=worktree, env=env).returncode
        if code != 0:
            cc.err("post-worktree script failed (exit %d): %s" % (code, item))
            return HOOK_FAILURE_EXIT
    return 0


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------

def _take_root(args):
    """Pull an optional ``--root DIR`` / ``--root=DIR`` out of ``args``,
    returning ``(root, remaining)``. Defaults to the current directory."""
    root = os.getcwd()
    rest = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--root":
            if i + 1 >= len(args):
                raise ValueError("--root needs a directory")
            root = args[i + 1]
            i += 2
            continue
        if arg.startswith("--root="):
            root = arg[len("--root="):]
            if not root:
                raise ValueError("--root needs a directory")
            i += 1
            continue
        rest.append(arg)
        i += 1
    return os.path.abspath(root), rest


def cmd_passthrough(argv):
    """Re-execute ``worktree.sh`` with ``argv`` verbatim, inheriting its
    stdout/stderr so its output is this script's own, and returning its exit
    code unchanged (worktree-hooks engine-worktree-create)."""
    return subprocess.run(["bash", WORKTREE_SH, *argv]).returncode


def cmd_create(argv):
    """The create path: validate the config, run ``worktree.sh``'s git
    mechanics, then run the configured scripts for a newly created or attached
    worktree (worktree-hooks engine-worktree-create)."""
    try:
        root, rest = _take_root(argv)
    except ValueError as exc:
        cc.err(str(exc))
        usage()
        return 1

    name = rest[0] if rest else ""
    flags = rest[1:]
    for flag in flags:
        if flag != "--fresh":
            cc.err("unknown argument '%s'" % flag)
            usage()
            return 1
    if not name:
        usage()
        return 1

    # Validate before any git mutation, so an invalid declaration never leaves
    # a worktree behind (worktree-hooks post-worktree-execution).
    items, _source = resolve_hooks(root)

    worktree = os.path.join(root, ".worktrees", name)
    pre_existed = os.path.exists(worktree)

    code = subprocess.run(
        ["bash", WORKTREE_SH, name, *flags], cwd=root).returncode
    if code != 0:
        return code
    # A reused worktree was set up when it was created; only a fresh create or
    # a branch attach is a new checkout needing setup.
    if pre_existed or not items:
        return 0
    return run_hooks(items, worktree, root, name)


# ---------------------------------------------------------------------------
# The `hooks` verb family (worktree-hooks worktree-hooks-verbs)
# ---------------------------------------------------------------------------

def _config_path(root):
    return os.path.join(root, sc.CONFIG_FILENAME)


def _read_root_config(root):
    """Load ``<root>/.shipd-config.json``, or ``{}`` when the file is absent.
    A malformed file raises :class:`spec_common.ConfigError` naming it, the
    same contract the layered loader honors."""
    path = _config_path(root)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise sc.ConfigError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict):
        raise sc.ConfigError("%s must contain a JSON object" % path)
    return data


def _write_root_config(root, data):
    """Write ``data`` back to ``<root>/.shipd-config.json`` in the existing
    file style: 2-space-indented JSON with a trailing newline."""
    path = _config_path(root)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    return path


def _root_declared_list(root, data):
    """The root file's own ``post-worktree-scripts`` list, validated the same
    way the resolver validates a declared value, or ``None`` when the root file
    does not declare the key."""
    if HOOKS_KEY not in data:
        return None
    raw = data[HOOKS_KEY]
    path = _config_path(root)
    if not isinstance(raw, list):
        raise sc.ConfigError(
            "`%s` must be a JSON list of shell command lines (from %s), "
            "got %r" % (HOOKS_KEY, path, raw))
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise sc.ConfigError(
                "`%s` items must be non-empty strings (from %s), got %r"
                % (HOOKS_KEY, path, item))
    return list(raw)


def hooks_list(root, as_json):
    """Print the effective list with each item's index and the config file that
    declared it, or the same payload as JSON under ``--json``."""
    items, source = resolve_hooks(root)
    if as_json:
        sys.stdout.write(json.dumps({
            "root": root,
            "source": source,
            "items": [{"index": i, "item": item, "source": source}
                      for i, item in enumerate(items)],
        }, indent=2) + "\n")
        return 0
    if not items:
        sys.stdout.write("no %s configured for %s\n" % (HOOKS_KEY, root))
        return 0
    for i, item in enumerate(items):
        sys.stdout.write("%d  %s  (from %s)\n" % (i, item, source))
    return 0


def hooks_add(root, item):
    """Append ``item`` to the root file's list, creating the file or the key as
    needed and preserving every unrelated key. Refuses an exact duplicate, and
    warns when the append newly shadows an outer layer's declared list."""
    if not item.strip():
        cc.err("refusing to register an empty %s item" % HOOKS_KEY)
        return 1
    data = _read_root_config(root)
    current = _root_declared_list(root, data)
    if current is not None and item in current:
        cc.err("%s already registered in %s: %s"
               % (HOOKS_KEY, _config_path(root), item))
        return 1
    if current is None:
        # The key is about to appear at the root. When an outer layer already
        # declares it, the merge is nearest-wins-*wholesale*, so this new list
        # replaces that one rather than extending it — say so out loud.
        _outer, outer_source = resolve_hooks(root)
        if outer_source is not None and outer_source != _config_path(root):
            cc.warn(
                "%s is declared in %s; a list at %s now wins the key "
                "wholesale, shadowing it"
                % (HOOKS_KEY, outer_source, _config_path(root)))
        current = []
    data[HOOKS_KEY] = current + [item]
    path = _write_root_config(root, data)
    sys.stdout.write("%s: added %s (%s)\n" % (HOOKS_KEY, item, path))
    return 0


def hooks_remove(root, target):
    """Delete one entry — matched by index, else by exact item — from the root
    file's list, preserving every unrelated key."""
    path = _config_path(root)
    data = _read_root_config(root)
    current = _root_declared_list(root, data)
    if current is None:
        cc.err("no %s declared in %s" % (HOOKS_KEY, path))
        return 1
    index = None
    if target.isdigit():
        candidate = int(target)
        if candidate >= len(current):
            cc.err("no %s at index %d in %s (%d registered)"
                   % (HOOKS_KEY, candidate, path, len(current)))
            return 1
        index = candidate
    elif target in current:
        index = current.index(target)
    if index is None:
        cc.err("no %s entry matching %r in %s" % (HOOKS_KEY, target, path))
        return 1
    removed = current.pop(index)
    data[HOOKS_KEY] = current
    _write_root_config(root, data)
    sys.stdout.write("%s: removed %s (%s)\n" % (HOOKS_KEY, removed, path))
    return 0


def hooks_run(root):
    """Execute the effective list against ``root`` itself — the create path's
    execution semantics applied in place, for re-running setup inside a
    worktree that already exists."""
    items, _source = resolve_hooks(root)
    if not items:
        return 0
    return run_hooks(items, root, _main_checkout(root),
                     os.path.basename(os.path.abspath(root)))


def _main_checkout(root):
    """The main checkout governing ``root`` — the directory holding the shared
    git dir, so a linked worktree reports the repository root rather than
    itself. Any git failure falls back to ``root`` (the same fail-soft probe
    :func:`spec_common.repo_store_folder` uses). Local git only, never the
    network."""
    try:
        result = subprocess.run(
            ["git", "-C", root, "rev-parse", "--path-format=absolute",
             "--git-common-dir"],
            capture_output=True, text=True)
    except OSError:
        return os.path.abspath(root)
    if result.returncode == 0 and result.stdout.strip():
        return os.path.dirname(os.path.abspath(result.stdout.strip()))
    return os.path.abspath(root)


def cmd_hooks(argv):
    """The ``hooks`` verb family: ``list``, ``add``, ``remove``, ``run``."""
    try:
        root, rest = _take_root(argv)
    except ValueError as exc:
        cc.err(str(exc))
        usage()
        return 1
    if not rest:
        usage()
        return 1
    verb, args = rest[0], rest[1:]

    if verb == "list":
        as_json = False
        for arg in args:
            if arg == "--json":
                as_json = True
            else:
                cc.err("unknown argument '%s'" % arg)
                usage()
                return 1
        return hooks_list(root, as_json)

    if verb == "run":
        if args:
            cc.err("unknown argument '%s'" % args[0])
            usage()
            return 1
        return hooks_run(root)

    if verb in ("add", "remove"):
        if len(args) != 1:
            usage()
            return 1
        if verb == "add":
            return hooks_add(root, args[0])
        return hooks_remove(root, args[0])

    cc.err("unknown hooks verb '%s'" % verb)
    usage()
    return 1


def main(argv=None):
    """Hand-rolled dispatch (mirroring ``worktree.sh``'s), because the first
    argument is either a verb or a change name — a shape argparse subparsers
    cannot express. Returns an exit code; importing the module never runs it."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        usage()
        return 1
    verb = argv[0]
    if verb in ("help", "-h", "--help"):
        usage(sys.stdout)
        return 0
    try:
        if verb in PASSTHROUGH_VERBS:
            return cmd_passthrough(argv)
        if verb == "hooks":
            return cmd_hooks(argv[1:])
        return cmd_create(argv)
    except sc.ConfigError as exc:
        cc.err(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
