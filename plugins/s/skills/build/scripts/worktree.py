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
    ``.shipd-config.json``, and records this machine's trust in it.
  * any other first argument is a change name for the create path.

The create path resolves and validates ``post-worktree-scripts`` *before* any
git mutation, so a malformed declaration never leaves a half-set-up worktree.
It then runs ``worktree.sh``'s create path from the repo root with output
inherited and, when that succeeds and ``.worktrees/<name>`` did not exist
beforehand, runs the configured scripts in order against the new worktree. A
*reused* worktree was already set up when it was created, so its scripts are
skipped; ``hooks run`` covers a manual re-run.

Every execution passes through the consent gate first: a resolved list runs
only while a machine-local ledger records this machine's user as trusting
exactly that list of commands, wherever it was declared. An untrusted list
prompts on a terminal and refuses without one, so a cloned repo's — or an
enclosing workspace's — tracked shell commands never execute unannounced.

Exit codes: ``0`` success, ``1`` usage/error, ``2`` a guard refusal passed
through from ``worktree.sh``, ``3`` a post-worktree script failed or its
consent gate refused.

Usage (run from the repository root):
  worktree.py <change-name> [--fresh] [--root DIR]
  worktree.py remove <change> [--force]
  worktree.py prune-branches
  worktree.py hooks list [--json] [--root DIR]
  worktree.py hooks add <item> [--root DIR]
  worktree.py hooks remove <item-or-index> [--root DIR]
  worktree.py hooks run [--root DIR]
  worktree.py hooks trust [--root DIR]
"""

import hashlib
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

# The machine-local trust ledger, in the user's home directory: a JSON object
# mapping the fingerprint of each `post-worktree-scripts` list this machine's
# user has consented to run to the config file that declared it when consent
# was granted — the path is informational, the fingerprint is the key
# (worktree-hooks hook-trust-ledger).
TRUST_FILENAME = ".shipd-trust.json"

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
       worktree.py hooks trust [--root DIR]
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
# The trust ledger (worktree-hooks hook-trust-ledger)
# ---------------------------------------------------------------------------

def trust_ledger_path():
    """The machine-local ledger file. It lives beside the user's own config in
    ``$HOME`` rather than *inside* it: config is user-authored intent, this is
    engine state, and a tracked or git-dir marker would be attacker-controlled
    or lost per-clone."""
    return os.path.expanduser(os.path.join("~", TRUST_FILENAME))


def hooks_fingerprint(items):
    """The SHA-256 of the list's canonical JSON. Exact-list, so any edit —
    an added item, a reorder, a one-character change — re-prompts."""
    return hashlib.sha256(
        json.dumps(items, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_trust_ledger():
    """The ledger as a ``{fingerprint: declaring config path}`` dict. A
    missing, unreadable, malformed, or non-object file reads as no entries — an
    unreadable ledger must never be a reason to *skip* the gate, and never a
    crash."""
    try:
        with open(trust_ledger_path(), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def hooks_trusted(items):
    """True when the ledger holds ``items``' fingerprint, whatever config file
    declares the list today. Consent is to the exact commands, not to the file
    that carries them, so trust granted at a repo root also covers the
    worktree's own checked-out copy of the same tracked declaration. An empty
    list needs no trust: there is nothing to execute."""
    if not items:
        return True
    return hooks_fingerprint(items) in load_trust_ledger()


def record_trust(items, source):
    """Record trust for exactly ``items``, preserving every other entry, with
    ``source`` stored as the informational record of where the consented list
    was declared. A write failure warns on stderr and returns: the consent was
    already given, so the verb that obtained it must not fail — the only cost
    is another prompt next time."""
    if not items:
        return
    ledger = load_trust_ledger()
    ledger[hooks_fingerprint(items)] = \
        os.path.realpath(source) if source else ""
    path = trust_ledger_path()
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh, indent=2, sort_keys=True)
            fh.write("\n")
    except OSError as exc:
        cc.warn("could not record hook trust in %s: %s" % (path, exc))


# ---------------------------------------------------------------------------
# Hook execution (worktree-hooks post-worktree-execution)
# ---------------------------------------------------------------------------

def describe_hooks(items, source, stream):
    """Write the declaring config file and every item to ``stream`` — what the
    user is being asked to grant, in full, before they answer."""
    stream.write("%s declared in %s:\n" % (HOOKS_KEY, source))
    for item in items:
        stream.write("  %s\n" % item)


def describe_resume(worktree, stream):
    """Write the two-step resume path a refusal leaves behind: consent, then
    run the hooks *from the worktree the create path already made*. Naming the
    worktree matters — ``hooks run`` sets up the directory it is invoked in, so
    re-running it at the parked root would set the root's own checkout up
    instead of the new one (worktree-hooks hook-consent-gate)."""
    stream.write("  to consent:  worktree.py hooks trust\n")
    if worktree:
        stream.write("  then, from %s:  worktree.py hooks run\n" % worktree)
    else:
        stream.write("  then, from the worktree:  worktree.py hooks run\n")


def ensure_hooks_trusted(items, source, worktree=None):
    """The consent gate in front of every hook execution (worktree-hooks
    hook-consent-gate).

    Returns True when ``items`` may run: an empty list or one this machine has
    already trusted returns immediately, so a trusted list behaves exactly as
    it did before the gate existed. Otherwise the list is shown in full and,
    on a TTY, consent is asked for — an affirmative answer records the trust
    entry and returns True. A declined prompt, and any non-interactive
    invocation, returns False after naming the resume path (rooted at
    ``worktree`` when the create path has already made one); the caller turns
    that into :data:`HOOK_FAILURE_EXIT` with the worktree left in place,
    exactly like a failing hook, so an unattended run parks for a human instead
    of silently dropping the gate."""
    if hooks_trusted(items):
        return True
    if not sys.stdin.isatty():
        cc.err("refusing to run untrusted %s without consent" % HOOKS_KEY)
        describe_hooks(items, source, sys.stderr)
        describe_resume(worktree, sys.stderr)
        return False
    describe_hooks(items, source, sys.stdout)
    sys.stdout.write(
        "These shell commands have not been trusted on this machine.\n")
    sys.stdout.flush()
    try:
        answer = input("Run them and remember this list? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() not in ("y", "yes"):
        cc.err("%s not run: consent declined" % HOOKS_KEY)
        describe_resume(worktree, sys.stderr)
        return False
    record_trust(items, source)
    return True


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
    items, source = resolve_hooks(root)

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
    if not ensure_hooks_trusted(items, source, worktree=worktree):
        return HOOK_FAILURE_EXIT
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


def _trust_after_write(root, prior_items):
    """Record trust for whatever ``root`` now resolves to, after a successful
    ``add``/``remove`` write — but only when ``prior_items``, the effective
    list *before* the write, was itself trusted or empty.

    The user just typed the registration, so re-asking for consent to their own
    item at the next create would be theater. But an item that was already
    declared and never consented to must not be blanket-trusted by an unrelated
    registration: a hostile tracked list has to reach the consent gate, where
    the user actually sees it. Re-resolving (rather than trusting the written
    list blind) keeps the recorded entry matching the list that actually wins
    the key (worktree-hooks hook-trust-ledger)."""
    if not hooks_trusted(prior_items):
        return
    items, source = resolve_hooks(root)
    record_trust(items, source)


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
    # The effective list before the write decides whether the result inherits
    # trust (worktree-hooks hook-trust-ledger), so capture it first.
    prior_items, prior_source = resolve_hooks(root)
    if current is None:
        # The key is about to appear at the root. When an outer layer already
        # declares it, the merge is nearest-wins-*wholesale*, so this new list
        # replaces that one rather than extending it — say so out loud.
        if prior_source is not None and prior_source != _config_path(root):
            cc.warn(
                "%s is declared in %s; a list at %s now wins the key "
                "wholesale, shadowing it"
                % (HOOKS_KEY, prior_source, _config_path(root)))
        current = []
    data[HOOKS_KEY] = current + [item]
    path = _write_root_config(root, data)
    _trust_after_write(root, prior_items)
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
    prior_items, _prior_source = resolve_hooks(root)
    data[HOOKS_KEY] = current
    _write_root_config(root, data)
    _trust_after_write(root, prior_items)
    sys.stdout.write("%s: removed %s (%s)\n" % (HOOKS_KEY, removed, path))
    return 0


def hooks_trust(root):
    """Record consent for ``root``'s effective list without running it — the
    resume path a refused create names, and the only way to grant consent in
    a session that has no terminal to prompt on (worktree-hooks
    worktree-hooks-trust-verb). Nothing configured is an error: there is no
    such thing as trusting an absent list, and silently exiting ``0`` would
    read as consent granted."""
    items, source = resolve_hooks(root)
    if not items:
        cc.err("no %s configured for %s" % (HOOKS_KEY, root))
        return 1
    describe_hooks(items, source, sys.stdout)
    record_trust(items, source)
    sys.stdout.write("%s: trusted on this machine (%s)\n"
                     % (HOOKS_KEY, trust_ledger_path()))
    return 0


def hooks_run(root):
    """Execute the effective list against ``root`` itself — the create path's
    execution semantics applied in place, for re-running setup inside a
    worktree that already exists."""
    items, source = resolve_hooks(root)
    if not items:
        return 0
    if not ensure_hooks_trusted(items, source):
        return HOOK_FAILURE_EXIT
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
    """The ``hooks`` verb family: ``list``, ``add``, ``remove``, ``run``,
    ``trust``."""
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

    if verb in ("run", "trust"):
        if args:
            cc.err("unknown argument '%s'" % args[0])
            usage()
            return 1
        return hooks_run(root) if verb == "run" else hooks_trust(root)

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
