#!/usr/bin/env python3
"""spec_emit.py — staged validate-then-install of spec content for the shipd
spec engine (stdlib only, no network, no third-party imports).

The engine is the single interface for every spec write: skills author artifacts
in a staging area and install them through this script, never writing into the
spec tree directly or constructing a storage path. Installation is
validate-then-commit — content is copied to its resolved destination, the
linter's checks run in-process against the real tree, and on any finding
everything installed is removed and the command exits non-zero. An invalid spec
therefore never remains in the tree (spec-io staged-emission).

Modes (all resolve locations through the layered configuration):

  change <name> --from <staging-dir> [--replace]
      Install a staged change artifact set (plan.md, specs/<cap>/spec.md,
      tasks.md) to ``<content-dir>/planned/<name>/`` and run the change checks.

  initiative <slug> --from <file> [--replace]
      Install a brief to the workspace's ``<content-dir>/initiatives/<slug>/
      brief.md`` and run the initiative checks. Requires a discoverable
      workspace.

  epic <slug> --from <file> [--replace]
      Install an epic to ``<content-dir>/epics/<slug>/epic.md`` and run the
      epic checks.

  research <slug> --from <file> [--replace]
      Install a research report to ``<content-dir>/research/<slug>/report.md``
      and run the research report checks.

  video <slug> --from <file> [--replace]
      Install a video intent brief to ``<content-dir>/video/<slug>/brief.md``
      and run the video brief checks.

  wiki --from <staging-dir>
      Install a staged wiki-store subset (``wiki/<slug>.md`` pages, ``index.md``,
      ``log.md``, ``queue.md``, add-only ``sources/<file>``) into the workspace
      wiki and run the whole-store wiki lint. Backs up the affected files and
      restores them byte-for-byte on any finding. Requires a discoverable
      workspace.

An existing destination is refused unless ``--replace`` is given, in which case
the existing content is set aside, replaced, and — should the fresh content fail
validation — restored, so a failed replace never destroys a valid spec.

Exit codes: 0 success, 1 error (missing source, no workspace, refusal, or lint
findings), 2 usage.
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402
import spec_lint as sl  # noqa: E402


class EmitError(Exception):
    """A user-facing error: printed as ``Error: ...`` to stderr, exit 1."""


def _print_findings(errors):
    for err in errors:
        print(str(err), file=sys.stderr)


def _install_dir(install_root, src_is_dir, src, dest_dir, replace,
                 validate, copy):
    """Shared validate-then-commit installer.

    ``dest_dir`` is the directory that *is* the install unit (removed on
    failure, checked for the existing-destination refusal). ``copy`` performs
    the staged copy into place; ``validate`` returns the list of lint findings
    for the just-installed content. On any finding the install unit is removed
    (and a replaced original restored) and the function raises
    :class:`EmitError`."""
    exists = os.path.exists(dest_dir)
    if exists and not replace:
        raise EmitError(
            "destination already exists: %s (pass --replace to overwrite)"
            % dest_dir)

    backup = None
    if exists:
        backup = dest_dir + ".bak-%d" % os.getpid()
        if os.path.exists(backup):
            shutil.rmtree(backup)
        os.rename(dest_dir, backup)

    try:
        copy()
    except OSError as exc:
        # Copy failed outright: restore any backup and surface the error.
        if backup is not None and not os.path.exists(dest_dir):
            os.rename(backup, dest_dir)
        raise EmitError("failed to install into %s: %s" % (dest_dir, exc))

    errors = validate()
    if errors:
        _print_findings(errors)
        shutil.rmtree(dest_dir, ignore_errors=True)
        if backup is not None:
            os.rename(backup, dest_dir)
        raise EmitError(
            "staged content failed validation; nothing was installed")

    if backup is not None:
        shutil.rmtree(backup, ignore_errors=True)


def emit_change(root, name, src, replace):
    if not os.path.isdir(src):
        raise EmitError("staging directory not found: %s" % src)
    dest_dir = os.path.join(sc.specs_dir(root), "planned", name)

    def copy():
        shutil.copytree(src, dest_dir)

    def validate():
        return sl.lint_change(root, name)

    _install_dir(root, True, src, dest_dir, replace, validate, copy)
    # Declare the grammar the installed artifacts are written under
    # (schema-versioning schema-marker-stamping); the marker joins the install's
    # own pathspec below so it travels in that one commit, never a second.
    marker = sc.stamp_schema_marker(root)
    # A successful install into an external store auto-commits locally, scoped
    # to the installed tree (shipd-config store-autocommit); a no-op for an
    # in-repo content directory, and a commit failure never fails the install.
    sc.store_autocommit(root, [dest_dir] + ([marker] if marker else []),
                        "shipd: install change %s" % name)
    print("installed change %s at %s" % (name, dest_dir))
    # Best-effort flow-time-series capture: a change install (unplanned → draft)
    # is one of the three lifecycle mutation chokepoints (delivery-metrics
    # flow-timeseries). A capture failure never fails the install.
    try:
        import metrics
        metrics.record_flow(root)
    except Exception:
        pass
    return 0


def emit_initiative(root, slug, src, replace):
    if not os.path.isfile(src):
        raise EmitError("brief file not found: %s" % src)
    ws_root = sc.find_workspace_root(root)
    if ws_root is None:
        raise EmitError(
            "no workspace found from %s; `initiative` requires a discoverable "
            "workspace root" % os.path.abspath(root))
    brief_path = sc.initiative_brief_path(ws_root, slug)
    dest_dir = os.path.dirname(brief_path)

    def copy():
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copyfile(src, brief_path)

    def validate():
        errors = []
        sl.lint_initiative(ws_root, slug, errors)
        return errors

    _install_dir(root, False, src, dest_dir, replace, validate, copy)
    print("installed initiative %s at %s" % (slug, brief_path))
    return 0


def emit_epic(root, slug, src, replace):
    if not os.path.isfile(src):
        raise EmitError("epic file not found: %s" % src)
    epic_path = os.path.join(sc.specs_dir(root), "epics", slug, "epic.md")
    dest_dir = os.path.dirname(epic_path)

    def copy():
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copyfile(src, epic_path)

    def validate():
        errors = []
        sl.lint_epic(root, slug, errors)
        return errors

    _install_dir(root, False, src, dest_dir, replace, validate, copy)
    # Declare the grammar the installed artifact is written under
    # (schema-versioning schema-marker-stamping).
    sc.stamp_schema_marker(root)
    print("installed epic %s at %s" % (slug, epic_path))
    return 0


def emit_research(root, slug, src, replace):
    if not os.path.isfile(src):
        raise EmitError("report file not found: %s" % src)
    report_path = os.path.join(
        sc.specs_dir(root), "research", slug, "report.md")
    dest_dir = os.path.dirname(report_path)

    def copy():
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copyfile(src, report_path)

    def validate():
        errors = []
        sl.lint_research(root, slug, errors)
        return errors

    _install_dir(root, False, src, dest_dir, replace, validate, copy)
    # Declare the grammar the installed artifact is written under
    # (schema-versioning schema-marker-stamping).
    sc.stamp_schema_marker(root)
    print("installed research %s at %s" % (slug, report_path))
    return 0


def emit_video(root, slug, src, replace):
    if not os.path.isfile(src):
        raise EmitError("brief file not found: %s" % src)
    brief_path = os.path.join(sc.specs_dir(root), "video", slug, "brief.md")
    dest_dir = os.path.dirname(brief_path)

    def copy():
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copyfile(src, brief_path)

    def validate():
        errors = []
        sl.lint_video(root, slug, errors)
        return errors

    _install_dir(root, False, src, dest_dir, replace, validate, copy)
    # Declare the grammar the installed artifact is written under
    # (schema-versioning schema-marker-stamping).
    sc.stamp_schema_marker(root)
    print("installed video %s at %s" % (slug, brief_path))
    return 0


def emit_wiki(root, src, personal=False):
    """Install a staged wiki-store subset into the wiki store (spec-io
    wiki-emission).

    The staging dir mirrors a store subset: ``wiki/<slug>.md`` pages, top-level
    ``index.md``/``log.md``/``queue.md``, and add-only ``sources/<file>``. A
    staged source that already exists in the store is refused before any install
    (sources are immutable). Otherwise the affected store files are backed up,
    the staged set is installed (overwriting existing pages and top-level
    files), and the whole resulting store is validated with the wiki lint; on
    any finding the backup is restored byte-for-byte and the command exits
    non-zero, so an invalid store state never lands.

    By default the destination is the workspace store, resolved through
    workspace discovery. When ``personal`` is set, the destination is the
    personal memory store at ``<memory_dir>/wiki``, resolved by fixed path
    (bypassing workspace discovery), with identical backup, lint, and restore
    semantics."""
    if not os.path.isdir(src):
        raise EmitError("staging directory not found: %s" % src)
    if personal:
        wiki = sc.memory_store_dir(root)
    else:
        ws_root = sc.find_workspace_root(root)
        if ws_root is None:
            raise EmitError(
                "no workspace found from %s; `wiki` requires a discoverable "
                "workspace root" % os.path.abspath(root))
        wiki = sc.wiki_dir(ws_root)

    # Enumerate staged files, validating each against the recognized subset.
    ops = []  # list of (rel, staged_abs, dest_abs, is_source)
    for dirpath, _dirs, names in os.walk(src):
        for name in names:
            staged_abs = os.path.join(dirpath, name)
            rel = os.path.relpath(staged_abs, src)
            parts = rel.split(os.sep)
            if len(parts) == 1 and parts[0] in (
                    "index.md", "log.md", "queue.md"):
                is_source = False
            elif (len(parts) == 2 and parts[0] == "wiki"
                    and parts[1].endswith(".md")):
                is_source = False
            elif len(parts) == 2 and parts[0] == "sources":
                is_source = True
            else:
                raise EmitError(
                    "unrecognized staged path '%s' (allowed: index.md, log.md, "
                    "queue.md, wiki/<slug>.md, sources/<file>)" % rel)
            ops.append((rel, staged_abs, os.path.join(wiki, *parts), is_source))

    if not ops:
        raise EmitError("staging directory has no wiki content: %s" % src)

    # Source immutability: refuse before any install when a staged source
    # already exists in the store.
    for rel, _staged, dest_abs, is_source in ops:
        if is_source and os.path.exists(dest_abs):
            raise EmitError(
                "staged source '%s' already exists in the store; sources are "
                "immutable (add-only)" % rel)

    # Back up affected store files (bytes, or None when the file is new).
    backup = {}
    for _rel, _staged, dest_abs, _is_source in ops:
        if os.path.isfile(dest_abs):
            with open(dest_abs, "rb") as fh:
                backup[dest_abs] = fh.read()
        else:
            backup[dest_abs] = None

    # Install the staged set.
    for _rel, staged_abs, dest_abs, _is_source in ops:
        parent = os.path.dirname(dest_abs)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copyfile(staged_abs, dest_abs)

    # Validate the resulting whole store; restore byte-for-byte on any finding.
    errors = []
    sl.lint_wiki(None, errors, wiki=wiki)
    if errors:
        _print_findings(errors)
        for dest_abs, original in backup.items():
            if original is None:
                if os.path.exists(dest_abs):
                    os.remove(dest_abs)
            else:
                with open(dest_abs, "wb") as fh:
                    fh.write(original)
        raise EmitError(
            "staged content failed validation; nothing was installed")

    # A successful write auto-commits its file set when the store sits inside a
    # git work tree (shipd-wiki wiki-autocommit); a no-op outside git, and a commit
    # failure never fails the write.
    dest_paths = [dest_abs for _rel, _staged, dest_abs, _is_source in ops]
    sc.wiki_autocommit(wiki, dest_paths, "shipd-wiki: emit %d file(s)" % len(ops))

    print("installed wiki content into %s (%d file(s))" % (wiki, len(ops)))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Install spec content only after in-process validation; an "
                    "invalid spec never lands in the tree.")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repo root resolving the content directory "
                             "(default: cwd)")
    sub = parser.add_subparsers(dest="mode")

    p_change = sub.add_parser("change", help="install a staged change")
    p_change.add_argument("name")
    p_change.add_argument("--from", dest="src", required=True)
    p_change.add_argument("--replace", action="store_true")

    p_init = sub.add_parser("initiative", help="install a workspace brief")
    p_init.add_argument("slug")
    p_init.add_argument("--from", dest="src", required=True)
    p_init.add_argument("--replace", action="store_true")

    p_epic = sub.add_parser("epic", help="install an epic")
    p_epic.add_argument("slug")
    p_epic.add_argument("--from", dest="src", required=True)
    p_epic.add_argument("--replace", action="store_true")

    p_research = sub.add_parser("research", help="install a research report")
    p_research.add_argument("slug")
    p_research.add_argument("--from", dest="src", required=True)
    p_research.add_argument("--replace", action="store_true")

    p_video = sub.add_parser("video", help="install a video intent brief")
    p_video.add_argument("slug")
    p_video.add_argument("--from", dest="src", required=True)
    p_video.add_argument("--replace", action="store_true")

    p_wiki = sub.add_parser(
        "wiki", help="install a staged wiki-store subset")
    p_wiki.add_argument("--from", dest="src", required=True)
    p_wiki.add_argument(
        "--personal", action="store_true",
        help="install into the personal memory store (<memory_dir>/wiki) by "
             "fixed path instead of the workspace store")

    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.mode is None:
        parser.print_help(sys.stderr)
        return 2

    try:
        # The schema compatibility gate (schema-versioning schema-compat-gate):
        # refuse a repo whose artifacts declare a different grammar major
        # before anything is installed.
        sc.check_schema_compat(root)
        if args.mode == "change":
            return emit_change(root, args.name, args.src, args.replace)
        if args.mode == "initiative":
            return emit_initiative(root, args.slug, args.src, args.replace)
        if args.mode == "epic":
            return emit_epic(root, args.slug, args.src, args.replace)
        if args.mode == "research":
            return emit_research(root, args.slug, args.src, args.replace)
        if args.mode == "video":
            return emit_video(root, args.slug, args.src, args.replace)
        if args.mode == "wiki":
            return emit_wiki(root, args.src, args.personal)
    except (EmitError, sc.ConfigError) as exc:
        cc.err(str(exc))
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
