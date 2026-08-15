#!/usr/bin/env python3
"""spec_merge.py — deterministic, LLM-free merge of a change's delta specs into
the master spec library (stdlib only, no network, no third-party imports).

The engine matches each delta requirement to a master requirement by exact
``id`` slug equality only — no similarity, fuzzy matching, or language model
(spec: "Deterministic keyed merge"). It applies the four operations under
take-newer semantics — a surprising situation never fails the merge, it is
applied and a loud, machine-readable warning is emitted instead (design D2).

Operations (all keyed on ``id``):
  ADDED     insert; overwrite + warn on id collision
  MODIFIED  replace; insert + warn if the target id is missing
  REMOVED   delete; no-op + warn if the target id is missing
  RENAMED   re-key from old id to new id; best-effort + warn on conflict

On MODIFIED/REMOVED the engine also compares the entry's ``base:`` hash to the
master requirement's current content hash and warns on a mismatch (stale base),
still applying the change (see :func:`_check_base`).

CLI:  spec_merge.py <change> [--root DIR] [--json] [--no-archive]
"""

import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


class MergeWarning:
    """A single merge warning. ``kind`` is a stable machine-readable tag;
    ``detail`` carries extra fields (e.g. expected/actual hashes)."""

    def __init__(self, id, kind, capability=None, **detail):
        self.id = id
        self.kind = kind
        self.capability = capability
        self.detail = detail

    def to_dict(self):
        d = {"id": self.id, "kind": self.kind}
        if self.capability is not None:
            d["capability"] = self.capability
        d.update(self.detail)
        return d

    def human(self):
        cap = ("[%s] " % self.capability) if self.capability else ""
        msg = _WARNING_MESSAGES.get(self.kind, self.kind)
        extra = ""
        if self.kind == "stale-base":
            extra = " (expected base %s, actual %s)" % (
                self.detail.get("expected"), self.detail.get("actual"))
        return "WARNING: %s%s: %s%s" % (cap, self.id, msg, extra)


_WARNING_MESSAGES = {
    "added-collision":
        "ADDED id already exists in master; overwriting (take-newer)",
    "modified-missing":
        "MODIFIED target id not found in master; inserting (take-newer)",
    "removed-missing":
        "REMOVED target id not found in master; nothing to delete",
    "rename-source-missing":
        "RENAMED source id not found in master; skipping rename",
    "rename-target-exists":
        "RENAMED target id already exists in master; overwriting (take-newer)",
    "stale-base":
        "base hash does not match current master; applying anyway (take-newer)",
}


# ---------------------------------------------------------------------------
# Requirement helpers
# ---------------------------------------------------------------------------


def _clean(entry):
    """Return a master-clean copy of a delta requirement: same title, id, and
    content, but without the delta-only ``base``/``Reason``/``Migration``
    metadata that never belongs in the master library."""
    return sc.Requirement(
        title=entry.title, id=entry.id, body=entry.body,
        scenarios=list(entry.scenarios), content=entry.content)


def _find(reqs, req_id):
    """Return the index of the requirement with ``req_id`` in ``reqs``, or
    None. Exact id equality only."""
    for i, r in enumerate(reqs):
        if r.id == req_id:
            return i
    return None


def _check_base(entry, master, warnings, capability):
    """Base-hash concurrency check (design D2). Compare the delta entry's
    ``base:`` to the master requirement's current content hash; on a mismatch,
    record a ``stale-base`` warning. The caller applies the change regardless
    (take-newer)."""
    actual = sc.content_hash(master)
    if entry.base is not None and entry.base != actual:
        warnings.append(MergeWarning(
            entry.id, "stale-base", capability=capability,
            expected=entry.base, actual=actual))


# ---------------------------------------------------------------------------
# Core merge (pure, in-memory)
# ---------------------------------------------------------------------------


def apply_delta_to_spec(spec, delta, warnings, capability=None):
    """Apply a parsed delta to a parsed master SpecFile, returning a new
    SpecFile. Ordering follows design D5: existing master order is preserved,
    and newly ADDED requirements are appended in delta order. ``warnings`` is a
    list that receives :class:`MergeWarning` entries."""
    reqs = list(spec.requirements)

    # MODIFIED: replace in place, or insert (take-newer) if the id is absent.
    for entry in delta.modified:
        idx = _find(reqs, entry.id)
        if idx is not None:
            _check_base(entry, reqs[idx], warnings, capability)
            reqs[idx] = _clean(entry)
        else:
            warnings.append(MergeWarning(
                entry.id, "modified-missing", capability=capability))
            reqs.append(_clean(entry))

    # REMOVED: delete, or no-op + warn if absent.
    for entry in delta.removed:
        idx = _find(reqs, entry.id)
        if idx is not None:
            _check_base(entry, reqs[idx], warnings, capability)
            del reqs[idx]
        else:
            warnings.append(MergeWarning(
                entry.id, "removed-missing", capability=capability))

    # RENAMED: re-key from old id to new id, best-effort under take-newer.
    for ren in delta.renamed:
        src = _find(reqs, ren.from_id)
        if src is None:
            warnings.append(MergeWarning(
                ren.from_id, "rename-source-missing", capability=capability,
                to=ren.to_id))
            continue
        dst = _find(reqs, ren.to_id)
        if dst is not None and dst != src:
            # Target id already taken: take-newer — the renamed requirement
            # wins, the existing target is dropped.
            warnings.append(MergeWarning(
                ren.to_id, "rename-target-exists", capability=capability,
                **{"from": ren.from_id}))
            del reqs[dst]
            if dst < src:
                src -= 1
        reqs[src].id = ren.to_id

    # ADDED: append new ids in delta order; overwrite + warn on collision.
    for entry in delta.added:
        idx = _find(reqs, entry.id)
        if idx is not None:
            warnings.append(MergeWarning(
                entry.id, "added-collision", capability=capability))
            reqs[idx] = _clean(entry)
        else:
            reqs.append(_clean(entry))

    return sc.SpecFile(preamble=spec.preamble, requirements=reqs)


# ---------------------------------------------------------------------------
# On-disk paths and file orchestration
# ---------------------------------------------------------------------------


def master_path(root, capability):
    return os.path.join(sc.specs_dir(root), "verified", capability, "spec.md")


def change_dir(root, change):
    return os.path.join(sc.specs_dir(root), "planned", change)


def archive_root(root):
    return os.path.join(sc.specs_dir(root), "completed")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def merge_change(root, change, warnings):
    """Apply every capability delta of ``change`` into the master library under
    ``root`` and write the affected master files back. Returns the sorted list
    of affected capability names. Deterministic: capabilities are processed in
    sorted order and each master is rewritten with stable ordering (design
    D5)."""
    deltas_dir = os.path.join(change_dir(root, change), "specs")
    if not os.path.isdir(deltas_dir):
        raise ValueError("no delta specs found for change %r under %s"
                         % (change, deltas_dir))
    affected = []
    for capability in sorted(os.listdir(deltas_dir)):
        delta_path = os.path.join(deltas_dir, capability, "spec.md")
        if not os.path.isfile(delta_path):
            continue
        delta = sc.parse_delta(_read(delta_path))
        mpath = master_path(root, capability)
        if os.path.isfile(mpath):
            master = sc.parse_spec(_read(mpath))
        else:
            # Brand-new capability: seed a master file with a title preamble.
            master = sc.SpecFile(preamble="# %s" % capability)
        merged = apply_delta_to_spec(master, delta, warnings, capability)
        sc.write_spec(mpath, merged)
        affected.append(capability)
    return affected


def archive_change(root, change, date=None):
    """Move the applied change directory to
    ``.shipd/completed/<date>-<change>/`` so it is retained immutably
    and never re-merged. ``date`` defaults to today (YYYY-MM-DD). Returns the
    destination path."""
    if date is None:
        date = datetime.date.today().isoformat()
    src = change_dir(root, change)
    dst = os.path.join(archive_root(root), "%s-%s" % (date, change))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        raise ValueError("archive destination already exists: %s" % dst)
    shutil.move(src, dst)
    # Best-effort flow-time-series capture: archiving a change (→ archived) is
    # one of the three lifecycle mutation chokepoints (delivery-metrics
    # flow-timeseries). A capture failure never fails the archive.
    try:
        import metrics
        metrics.record_flow(root)
    except Exception:
        pass
    return dst


# ---------------------------------------------------------------------------
# Warning reporting
# ---------------------------------------------------------------------------


def report_warnings(warnings, as_json=False, out=None):
    """Emit the merge warnings.

    In ``--json`` mode this writes one JSON object per line (a machine-readable
    summary a caller such as the build report can parse), each object carrying
    at least ``id`` and ``kind`` plus any detail fields. Otherwise it writes
    human-readable ``WARNING:`` lines followed by a count. Returns the number of
    warnings emitted. Warnings never change the exit status (take-newer never
    fails the merge, design D2)."""
    if out is None:
        out = sys.stdout
    if as_json:
        for w in warnings:
            out.write(json.dumps(w.to_dict(), sort_keys=True) + "\n")
    else:
        for w in warnings:
            out.write(w.human() + "\n")
        if warnings:
            out.write("%d merge warning(s).\n" % len(warnings))
        else:
            out.write("Merge clean: no warnings.\n")
    return len(warnings)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge a change's delta specs into the .shipd/verified master "
                    "library (LLM-free, take-newer, never blocking).")
    parser.add_argument("change", help="change name under .shipd/planned/")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repo root containing am/ (default: cwd)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit warnings as machine-readable JSON lines")
    parser.add_argument("--no-archive", action="store_true",
                        help="apply the merge but do not archive the change")
    args = parser.parse_args(argv)

    warnings = []
    # A missing delta set or an occupied archive destination is a user-facing
    # failure, not a bug: report it as the one-line `Error:` the CLI convention
    # requires rather than a traceback.
    try:
        affected = merge_change(args.root, args.change, warnings)
        archived = None
        if not args.no_archive:
            archived = archive_change(args.root, args.change)
    except ValueError as exc:
        cc.err(str(exc))
        return 1

    report_warnings(warnings, as_json=args.as_json)
    if not args.as_json:
        print("Merged change %r into: %s" % (
            args.change, ", ".join(affected) if affected else "(nothing)"))
        if archived is not None:
            print("Archived to: %s" % archived)
    # Take-newer never fails the merge (design D2): always exit 0 on success.
    return 0


if __name__ == "__main__":
    sys.exit(main())
