#!/usr/bin/env python3
"""spec_status.py — spec lifecycle status and current-spec selection for the
shipd spec engine (stdlib only, no network, no third-party imports).

Every change's ``plan.md`` begins with a ``# <change-name>`` title and a
``Status: <status>`` line (one of
draft/ready/active/complete/verified/rejected). This
CLI reads and writes that header, records the currently-selected spec in a
repo-local ``.shipd/state.json`` (git-ignored), and derives the status from
``tasks.md`` checkbox progress.

Verbs (see the spec-status + statusline capabilities for the contract):

  use <change>       record the spec being worked on in .shipd/state.json (the content dir)
  current            print the selected change name (nothing if none)
  show [change]      print "<change>: <status> (<done>/<total> tasks)"; with no
                     change given and none selected, print the workspace board
                     report instead — totals, shipped progress, and the four
                     board lanes over every epic's members plus the standalone
                     changes
  status [change]    print the bare status value ("?" when missing/invalid)
  validate [change]  structurally validate the change; non-zero on errors
  set-status <status> [change] [--force]
                     write a validated status into the plan header,
                     subject to the transition guards (--force bypasses guards
                     but never the status-value check)
  sync [change]      re-derive the status from tasks.md checkbox progress
  locate [change]    find an installed change by probing the invocation root's
                     planned/ then each .worktrees/<name> directory, printing a
                     keyed block (change/root/dir/status) per match
  check-base [change]
                     compare the change's delta specs against the current master
                     library (read-only), printing one finding line per
                     mismatched entry (stale-base/missing-master/id-collision)
                     plus a summary; exit 0 clean, 4 on findings
  epic-show <slug>   print an epic's board-shaped report: status, metadata,
                     shipped progress, and its members grouped into the
                     board's lanes
  epic-sync <slug>   re-derive an epic's status from its members' states
  epic-set-status <status> <slug>
                     write a validated epic status (draft/ready/active/
                     complete); `ready` is refused unless the epic lints clean
  initiative-show <slug>
                     print a brief's status, metadata, and requirement
                     progress (<done>/<total>) plus each requirement line
  initiative-sync <slug>
                     re-derive a brief's status from its requirement
                     checkboxes (achieved when all ticked, else open; a
                     dropped brief is left untouched)
  initiative-set-status <status> <slug>
                     write a validated initiative status (open/achieved/
                     dropped) into the brief header
  workspace-init <path> [--git]
                     initialize a workspace at <path> (declaring `workspace`
                     in <path>/.shipd-config.json), printing the created
                     root; refuses when a workspace is already discoverable
                     from the target or the target directory is missing. With
                     --git, git-init the target when it is not already inside a
                     work tree and seed a marked member-repos .gitignore block.
                     Unlike the other workspace verbs it does not require (or
                     resolve) an existing workspace
  workspace-show     print the workspace root, the declared focus project (when
                     set), each declared project (repos annotated present/absent
                     and [url] when a clone URL is declared, context.md
                     presence), and each initiative with its status and
                     Project: scope
  project-show <slug>
                     print one declared project's repos (annotated the same
                     way), its context.md presence, and the initiatives scoped
                     to it
  workspace-sync [--json] [--write-gitignore]
                     print the per-member materialization plan (one keyed block
                     per member plus a gitignore section, or one JSON object per
                     record with --json), computed from the manifest, the
                     resolved config, and local disk with local git probes only.
                     A computed plan exits zero regardless of drift or
                     unmaterializable members; an invalid registry or a
                     malformed `clone_sources` value exits non-zero. With
                     --write-gitignore, rewrites only the marked member-repos
                     .gitignore block to match the manifest's member paths

The initiative, workspace, and project verbs resolve the workspace from
``--root`` and exit non-zero when no workspace is discoverable.

Where ``[change]`` is omitted it defaults to the currently-selected spec; the
CLI exits non-zero with an error when none is selected — except ``show``, which
reports the workspace board instead. All paths are resolved
under ``--root`` (default: the current working directory), matching spec_lint.

Exit codes: 0 success, 1 error (unknown change/status, missing plan, no
selection), 2 usage, 3 refusal (a guard blocked a ``set-status`` transition),
4 check-base findings (the supersession gate tripped — distinct from a crash).
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_common as sc  # noqa: E402
import spec_merge  # noqa: E402
from spec_lint import lint_change, lint_epic, lint_wiki  # noqa: E402

# The six lifecycle statuses, in pipeline order (design D2). ``rejected`` is the
# context-sufficiency gate's parking state — entered by the gate, exited by a
# human transition back to draft/ready after enrichment.
STATUSES = ("draft", "ready", "active", "complete", "verified", "rejected")

# The selection state lives in a repo-local, git-ignored ``state.json`` inside
# the resolved content directory (default ``.shipd/state.json``).
STATE_FILENAME = "state.json"
CURRENT_KEY = "current_spec"

STATUS_LINE_RE = re.compile(r"^Status:\s*(.*?)\s*$")
TITLE_LINE_RE = re.compile(r"^#\s+(.*?)\s*$")
# Checkbox lines in tasks.md: "- [ ]", "- [x]", "- [~]".
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX~])\]")


class StatusError(Exception):
    """A user-facing error: printed as ``Error: ...`` to stderr, exit 1."""


class RefusalError(Exception):
    """A guarded ``set-status`` transition was refused (design D3). The first
    stderr line is ``Refused: <reason>``; ``details`` are extra lines (the
    individual validation errors when structure was the problem). Exit 3."""

    def __init__(self, reason, details=None):
        super().__init__(reason)
        self.reason = reason
        self.details = list(details) if details else []


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _changes_dir(root):
    return os.path.join(sc.specs_dir(root), "planned")


def _change_dir(root, change):
    return os.path.join(_changes_dir(root), change)


def _readable_change_dir(root, change):
    """Resolve a change directory for *reading* (spec-io mediated-read-verb):
    ``planned/<change>/`` first and, when absent, the archived
    ``completed/*-<change>/`` directory — the lexicographically last (newest
    date prefix) when several match. Returns ``None`` when the change lives in
    neither. Read-only callers use this so a reference survives the
    merge/archive; the lifecycle helpers keep resolving ``planned/`` only,
    since an archived change is not a live one."""
    planned = _change_dir(root, change)
    if os.path.isdir(planned):
        return planned
    archives = sorted(
        path for path in glob.glob(
            os.path.join(sc.specs_dir(root), "completed", "*-" + change))
        if os.path.isdir(path))
    return archives[-1] if archives else None


def _plan_path(root, change):
    return os.path.join(_change_dir(root, change), "plan.md")


def _tasks_path(root, change):
    return os.path.join(_change_dir(root, change), "tasks.md")


def _state_path(root):
    return os.path.join(sc.specs_dir(root), STATE_FILENAME)


def _epic_dir(root, slug):
    return os.path.join(sc.specs_dir(root), "epics", slug)


def _epic_path(root, slug):
    return os.path.join(_epic_dir(root, slug), "epic.md")


def _is_main_checkout(root):
    """True when ``root`` is a git main checkout — its ``.git`` is a directory.
    A linked worktree's ``.git`` is a *file* (a ``gitdir:`` pointer), and a
    root with no ``.git`` at all is not a checkout; both return False. This is
    the same stdlib distinction ``build_report.resolve_project_root`` relies
    on — no git subprocess."""
    return os.path.isdir(os.path.join(root, ".git"))


def _is_change(root, change):
    """True when ``change`` names a real change directory under .shipd/planned/.
    No archive exclusion is needed: applied changes live in the sibling
    .shipd/completed/, so .shipd/planned/ holds only live changes."""
    if not change:
        return False
    return os.path.isdir(_change_dir(root, change))


# ---------------------------------------------------------------------------
# State (current selection)
# ---------------------------------------------------------------------------


def read_current(root):
    """Return the currently-selected change name, or None. Never raises: a
    missing or corrupt state file simply means "nothing selected"."""
    path = _state_path(root)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if isinstance(data, dict):
        val = data.get(CURRENT_KEY)
        if isinstance(val, str) and val:
            return val
    return None


def write_current(root, change):
    """Record ``change`` as the current selection in .shipd/state.json (the content dir)."""
    path = _state_path(root)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({CURRENT_KEY: change}, fh, indent=2)
        fh.write("\n")


def _resolve_change(root, change):
    """Return ``change`` if given, else the current selection; error if none."""
    if change:
        return change
    current = read_current(root)
    if not current:
        raise StatusError(
            "no change given and no spec selected "
            "(run `spec_status.py use <change>`)")
    return current


# ---------------------------------------------------------------------------
# Plan header (status)
# ---------------------------------------------------------------------------


def read_status(root, change):
    """Return the change's status value, or None when the plan is missing
    or carries no valid ``Status:`` line. A value outside the six statuses is
    treated as invalid (None)."""
    path = _plan_path(root, change)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    for line in text.splitlines():
        m = STATUS_LINE_RE.match(line)
        if m:
            val = m.group(1)
            return val if val in STATUSES else None
    return None


def write_status(root, change, status):
    """Write ``status`` into the change's plan header, rewriting an
    existing ``Status:`` line or inserting the ``# <change>`` + ``Status:``
    header when the plan lacks one. The plan must exist."""
    path = _plan_path(root, change)
    if not os.path.isfile(path):
        raise StatusError("plan.md not found for change '%s'" % change)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()

    # Rewrite an existing Status: line in place.
    rewritten = False
    for i, line in enumerate(lines):
        if STATUS_LINE_RE.match(line):
            lines[i] = "Status: %s" % status
            _write_lines(path, lines, text)
            rewritten = True
            break

    if not rewritten:
        # No Status line: insert the header. Reuse a matching title on line 1 if
        # present, otherwise prepend the full "# <change>" + "Status:" header.
        if lines and TITLE_LINE_RE.match(lines[0]) \
                and TITLE_LINE_RE.match(lines[0]).group(1) == change:
            lines.insert(1, "Status: %s" % status)
        else:
            header = ["# %s" % change, "Status: %s" % status, ""]
            lines = header + lines
        _write_lines(path, lines, text)

    # Best-effort flow-time-series capture: a status write is one of the three
    # lifecycle mutation chokepoints (delivery-metrics flow-timeseries).
    _record_flow_snapshot(root)


def _record_flow_snapshot(root):
    """Append a best-effort delivery-metrics flow snapshot for ``root``.

    A capture failure — any exception, including an unwritable log destination —
    is swallowed so a lifecycle mutation is never blocked (heartbeat's
    write-tolerance rule). ``metrics`` is imported lazily inside the guard so the
    status engine never hard-depends on it."""
    try:
        import metrics
        metrics.record_flow(root)
    except Exception:
        pass


def _write_lines(path, lines, original):
    """Write ``lines`` back to ``path``, preserving a trailing newline if the
    original file had one (plans normally do)."""
    out = "\n".join(lines)
    if original.endswith("\n") or not original:
        out += "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)


# ---------------------------------------------------------------------------
# Task progress (tasks.md checkboxes)
# ---------------------------------------------------------------------------


def count_tasks(root, change):
    """Return (done, in_progress, total) checkbox counts, or None when
    tasks.md is absent. done counts ``- [x]``; in-progress counts ``- [~]``;
    total counts every checkbox line."""
    path = _tasks_path(root, change)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    done = in_progress = total = 0
    for line in text.splitlines():
        m = CHECKBOX_RE.match(line)
        if not m:
            continue
        mark = m.group(1)
        total += 1
        if mark in ("x", "X"):
            done += 1
        elif mark == "~":
            in_progress += 1
    return (done, in_progress, total)


def derive_status(counts):
    """Map task counts to a derived pipeline status within {ready, active,
    complete} per design D2. ``counts`` is (done, in_progress, total) or None
    (no tasks.md → treated as none-started)."""
    if counts is None:
        return "ready"
    done, in_progress, total = counts
    if total > 0 and done == total:
        return "complete"
    if done > 0 or in_progress > 0:
        return "active"
    return "ready"


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------


def cmd_use(root, change):
    if not _is_change(root, change):
        raise StatusError("unknown change '%s' (no directory under %s)"
                          % (change, _changes_dir(root)))
    write_current(root, change)
    print(change)
    return 0


def cmd_current(root):
    current = read_current(root)
    if current:
        print(current)
    return 0


def _plan_metadata(root, change):
    """Return the change plan's recognized header metadata as ordered
    ``(key, value)`` pairs (unrecognized keys filtered out), or ``[]`` when the
    plan is missing or carries no metadata block."""
    path = _plan_path(root, change)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    return [(k, v) for k, v in sc.parse_plan_metadata(text)
            if k in sc.METADATA_KEYS]


def _epic_fallback(root, name):
    """True when ``name`` names no change but an epic of that slug exists — the
    ``status``/``show`` epic fallback (spec-status status-cli). Resolution
    lives here at the CLI rather than in a skill so every caller (the ``shipd``
    dispatcher included) gains it."""
    return not _is_change(root, name) and os.path.isfile(_epic_path(root, name))


def cmd_show(root, change):
    # No name and no selection: the board's own no-argument view is the whole
    # workspace, so report it rather than erroring (spec-status
    # workspace-board-report). Checked ahead of `_resolve_change`, which keeps
    # raising for `status`/`validate`/`set-status`/`sync`.
    if not change and read_current(root) is None:
        for line in _workspace_report_lines(root):
            print(line)
        return 0
    change = _resolve_change(root, change)
    if _epic_fallback(root, change):
        for line in _epic_report_lines(root, change):
            print(line)
        return 0
    status = read_status(root, change) or "?"
    counts = count_tasks(root, change)
    if counts is None:
        print("%s: %s" % (change, status))
    else:
        done, _in_progress, total = counts
        print("%s: %s (%d/%d tasks)" % (change, status, done, total))
    for key, value in _plan_metadata(root, change):
        print("%s: %s" % (key, value))
    return 0


def cmd_status(root, change):
    change = _resolve_change(root, change)
    if _epic_fallback(root, change):
        print(read_epic_status(root, change) or "?")
        return 0
    print(read_status(root, change) or "?")
    return 0


def cmd_validate(root, change):
    change = _resolve_change(root, change)
    errors = lint_change(root, change)
    if errors:
        for err in errors:
            print("ERROR: %s" % err, file=sys.stderr)
        print("%d error(s) in change '%s'." % (len(errors), change),
              file=sys.stderr)
        return 1
    print("OK: change '%s' is valid." % change)
    return 0


def _check_guards(root, change, status):
    """Enforce the design D2 transition guards for targeting ``status``, raising
    :class:`RefusalError` when a guard blocks the write. ``draft`` and
    ``rejected`` have no guards (a rejected plan may be structurally broken —
    that is the point); ``ready``/``active`` require the change to validate;
    ``complete``/``verified`` additionally require a finished task checklist."""
    if status in ("draft", "rejected"):
        return
    # ready/active/complete/verified all require structural validation.
    errors = [str(err) for err in lint_change(root, change)]
    if errors:
        raise RefusalError(
            "setting %s requires the change to validate" % status, errors)
    if status not in ("complete", "verified"):
        return
    # complete/verified additionally require a finished checklist.
    counts = count_tasks(root, change)
    if counts is None:
        raise RefusalError(
            "setting %s requires all tasks done (tasks.md not found)" % status)
    done, in_progress, total = counts
    if total == 0:
        raise RefusalError(
            "setting %s requires all tasks done (tasks.md has no checkboxes)"
            % status)
    pending = total - done - in_progress
    if pending > 0 or in_progress > 0:
        raise RefusalError(
            "setting %s requires all tasks done (%d/%d done, %d in progress)"
            % (status, done, total, in_progress))


def cmd_set_status(root, status, change, force):
    if status not in STATUSES:
        raise StatusError("invalid status '%s' (expected one of: %s)"
                          % (status, ", ".join(STATUSES)))
    change = _resolve_change(root, change)
    if not os.path.isfile(_plan_path(root, change)):
        raise StatusError("plan.md not found for change '%s'" % change)
    if not force:
        _check_guards(root, change, status)
    write_status(root, change, status)
    print(status)
    return 0


def cmd_sync(root, change):
    change = _resolve_change(root, change)
    path = _plan_path(root, change)
    if not os.path.isfile(path):
        raise StatusError("plan.md not found for change '%s'" % change)
    current = read_status(root, change)
    # Never touch draft, verified, or rejected — entering/leaving the pipeline
    # (and the gate's parking state) is an explicit act (design D2).
    if current in ("draft", "verified", "rejected"):
        print(current)
        return 0
    derived = derive_status(count_tasks(root, change))
    write_status(root, change, derived)
    print(derived)
    return 0


def cmd_locate(root, change):
    """Probe the invocation root's resolved ``planned/`` first, then each
    ``.worktrees/<name>`` directory under it in sorted name order, for an
    installed ``change`` (spec-status locate-verb). Where ``change`` is
    omitted, falls back to the currently selected spec via
    ``_resolve_change``, raising when none is selected. The content directory
    is resolved independently per candidate root, so a worktree may carry its
    own ``.shipd-config.json``. Print one keyed block per match — ``change:``,
    ``root:`` (absolute), ``dir:`` (relative to that root), ``status:`` (``?``
    when missing or invalid) — separated by a blank line, the invocation root's
    own match first. Exit 0 on at least one match; raise (exit 1) naming the
    probed locations when none. No git, model, or network calls."""
    change = _resolve_change(root, change)
    probed = []
    matches = []

    def _probe(candidate):
        probed.append(candidate)
        try:
            cdir = os.path.join(sc.specs_dir(candidate), "planned", change)
        except sc.ConfigError:
            return
        if os.path.isdir(cdir):
            matches.append(candidate)

    # Invocation root first, then each worktree directory in sorted name order.
    _probe(root)
    worktrees_dir = os.path.join(root, ".worktrees")
    if os.path.isdir(worktrees_dir):
        for name in sorted(os.listdir(worktrees_dir)):
            wt = os.path.join(worktrees_dir, name)
            if os.path.isdir(wt):
                _probe(wt)

    if not matches:
        raise StatusError(
            "change '%s' not found; probed: %s"
            % (change, ", ".join(probed)))

    blocks = []
    for candidate in matches:
        cdir = os.path.join(sc.specs_dir(candidate), "planned", change)
        blocks.append(
            "change: %s\nroot: %s\ndir: %s\nstatus: %s"
            % (change, os.path.abspath(candidate),
               os.path.relpath(cdir, candidate),
               read_status(candidate, change) or "?"))
    print("\n\n".join(blocks))
    return 0


# ---------------------------------------------------------------------------
# Supersession gate (spec-status check-base-verb)
# ---------------------------------------------------------------------------


def cmd_check_base(root, change):
    """Compare a planned change's delta specs against the current master
    library (spec-status check-base-verb), strictly read-only. For each delta
    spec under the change's ``specs/<capability>/`` this reuses the merge
    engine's own primitives — ``spec_merge.master_path`` for master resolution
    and ``sc.content_hash`` for the base comparison, the exact functions
    ``spec_merge._check_base`` uses, so the pre-build gate and the merge-time
    check can never disagree — and reports one finding line per mismatch:

    - ``stale-base`` — a MODIFIED/REMOVED entry whose ``base:`` hash no longer
      matches the master requirement's current content hash (the line reports
      the expected and actual hashes);
    - ``missing-master`` — a MODIFIED/REMOVED entry whose id, or whose whole
      capability master file, is absent;
    - ``id-collision`` — an ADDED entry whose id already exists in the master.

    RENAMED entries are deliberately out of scope — the three kinds above match
    the spec-status contract, and a rename racing another rename still surfaces
    at merge time via ``spec_merge``'s take-newer warnings.

    Prints ``<capability>/<id>: <kind>`` per finding (hash detail on
    ``stale-base``) then a summary line; exits 0 with a clean summary when
    nothing is found and 4 when at least one finding exists — distinct from the
    CLI's general errors (1) and guard refusals (3). No git, model, or network."""
    change = _resolve_change(root, change)
    deltas_dir = os.path.join(_change_dir(root, change), "specs")
    if not os.path.isdir(deltas_dir):
        raise StatusError(
            "change '%s' has no delta specs (%s)" % (change, deltas_dir))

    findings = []  # list of (capability, id, kind, detail-or-None)
    for capability in sorted(os.listdir(deltas_dir)):
        delta_path = os.path.join(deltas_dir, capability, "spec.md")
        if not os.path.isfile(delta_path):
            continue
        with open(delta_path, encoding="utf-8") as fh:
            delta = sc.parse_delta(fh.read())
        mpath = spec_merge.master_path(root, capability)
        master_reqs = {}
        if os.path.isfile(mpath):
            with open(mpath, encoding="utf-8") as fh:
                master = sc.parse_spec(fh.read())
            master_reqs = {r.id: r for r in master.requirements if r.id}

        # MODIFIED/REMOVED: the entry must still name a live master requirement,
        # and its base: must match that requirement's current content hash.
        for entry in list(delta.modified) + list(delta.removed):
            master_req = master_reqs.get(entry.id)
            if master_req is None:
                findings.append((capability, entry.id, "missing-master", None))
                continue
            actual = sc.content_hash(master_req)
            if entry.base is not None and entry.base != actual:
                findings.append((
                    capability, entry.id, "stale-base",
                    "expected %s, actual %s" % (entry.base, actual)))

        # ADDED: the strongest supersession signal — the plan adds an id the
        # master already carries.
        for entry in delta.added:
            if entry.id in master_reqs:
                findings.append((capability, entry.id, "id-collision", None))

    for capability, req_id, kind, detail in findings:
        line = "%s/%s: %s" % (capability, req_id, kind)
        if detail:
            line += " (%s)" % detail
        print(line)
    if findings:
        print("check-base: %d finding(s)." % len(findings))
        return 4
    print("check-base: clean (no findings).")
    return 0


# ---------------------------------------------------------------------------
# Epic status verbs (spec-status epic-status-verbs)
# ---------------------------------------------------------------------------


def read_epic_status(root, slug):
    """Return the epic's status value, or None when the epic is missing or
    carries no valid ``Status:`` line. A value outside the four epic statuses
    is treated as invalid (None)."""
    try:
        with open(_epic_path(root, slug), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    for line in text.splitlines():
        m = STATUS_LINE_RE.match(line)
        if m:
            val = m.group(1)
            return val if val in sc.EPIC_STATUSES else None
    return None


def write_epic_status(root, slug, status):
    """Rewrite the epic's ``Status:`` line in place. The epic must exist and
    already carry a ``Status:`` line (the linter guarantees one)."""
    path = _epic_path(root, slug)
    if not os.path.isfile(path):
        raise StatusError("epic '%s' not found (%s)" % (slug, path))
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if STATUS_LINE_RE.match(line):
            lines[i] = "Status: %s" % status
            _write_lines(path, lines, text)
            _warn_main_checkout_write(root, path)
            return
    raise StatusError("epic '%s' has no `Status:` line to rewrite" % slug)


def _warn_main_checkout_write(root, path):
    """Warn (one line, stderr) when an epic file was just rewritten in a main
    checkout, where a protected-main workflow cannot ship the uncommitted
    change without a worktree PR. Silent in a linked worktree or outside a
    checkout; never changes the exit code (spec-status
    main-checkout-epic-write-warning)."""
    if _is_main_checkout(root):
        rel = os.path.relpath(path, root)
        print("Warning: wrote %s in the main checkout; a protected-main "
              "workflow must ship this via a worktree PR." % rel,
              file=sys.stderr)


def _epic_metadata(text):
    """Return the epic header's recognized metadata as ordered ``(key, value)``
    pairs (unrecognized keys filtered out)."""
    return [(k, v) for k, v in sc.parse_plan_metadata(text)
            if k in sc.EPIC_METADATA_KEYS]


def board_lane(state):
    """Map a lifecycle ``state`` onto its board lane (spec-status
    epic-status-verbs): ``archived``→``shipped``, ``ready``→``ready``,
    ``unplanned``→``unplanned``, every other state (``draft``/``active``/
    ``complete``/``verified``/``rejected``/``?``)→``building``.

    The single shared projection: the epic report groups its members with it
    and ``dashboard.flow_lane`` delegates to it, so the board and the report
    cannot drift. Pure — no I/O."""
    if state == "archived":
        return "shipped"
    if state == "ready":
        return "ready"
    if state == "unplanned":
        return "unplanned"
    return "building"


def _member_state_with_root(root, slug):
    """Derive one stub member's state, and the candidate root that produced it
    (spec-status epic-status-verbs; design: epic status derivation).

    Probes candidate roots in order — ``root`` first, then each
    ``.worktrees/<name>`` directory under it in sorted name order, mirroring
    ``cmd_locate`` at the same file — resolving each candidate's content
    directory independently (``sc.specs_dir(candidate)``) and skipping any
    candidate whose configuration is unreadable (``sc.ConfigError``). Each
    candidate is evaluated whole and in order: ``archived`` when that
    candidate has a matching ``completed/*-<slug>/`` directory; else that
    candidate's plan status when it has ``planned/<slug>/``; else move on to
    the next candidate. The first candidate to yield a state wins, and
    ``hosting_root`` is that candidate. Only when every candidate misses does
    the result stay ``("unplanned", root)`` — ``root`` itself, since nothing
    hosts the member."""
    candidates = [root]
    worktrees_dir = os.path.join(root, ".worktrees")
    if os.path.isdir(worktrees_dir):
        for name in sorted(os.listdir(worktrees_dir)):
            wt = os.path.join(worktrees_dir, name)
            if os.path.isdir(wt):
                candidates.append(wt)

    for candidate in candidates:
        try:
            specs_dir = sc.specs_dir(candidate)
        except sc.ConfigError:
            continue
        for path in glob.glob(os.path.join(specs_dir, "completed", "*-" + slug)):
            if os.path.isdir(path):
                return "archived", candidate
        if os.path.isdir(os.path.join(specs_dir, "planned", slug)):
            return read_status(candidate, slug) or "?", candidate
    return "unplanned", root


def _member_state(root, slug):
    """Return just the state from :func:`_member_state_with_root` — the
    original ``_member_state`` contract, unchanged for every existing caller."""
    state, _hosting_root = _member_state_with_root(root, slug)
    return state


def _standalone_plan_path(content_dir, slug):
    """The plan.md for ``slug`` under ``content_dir`` — the in-flight
    ``planned/<slug>/plan.md``, else the newest ``completed/<date>-<slug>/
    plan.md`` archive, else ``None``. Mirrors ``dashboard.change_artifacts``'
    planned-then-completed resolution."""
    planned = os.path.join(content_dir, "planned", slug, "plan.md")
    if os.path.isfile(planned):
        return planned
    archives = sorted(
        glob.glob(os.path.join(content_dir, "completed", "*-" + slug)))
    if archives:
        candidate = os.path.join(archives[-1], "plan.md")
        if os.path.isfile(candidate):
            return candidate
    return None


def standalone_changes(root, epic_member_slugs):
    """Discover **standalone changes** — those planned outside any epic — for
    the board (delivery-dashboard board-standalone-changes spec) and for the
    status CLI's workspace report (spec-status workspace-board-report).

    Scans every change directory under ``root``'s content ``planned/`` and the
    change named by each ``<root>/.worktrees/<name>/`` dir; a change qualifies
    when its plan carries no ``Epic:`` header line and its slug is in neither
    ``epic_member_slugs`` nor an already-collected entry. Returns member-shaped
    dicts ``{"slug", "description": "", "risk": None, "state", "location"}`` in
    root-then-worktree, slug-sorted order — ``state`` from the hosting root via
    :func:`_member_state` (a completed archive reads ``archived``),
    ``location`` the hosting directory's absolute path. Root entries win a slug
    contested with a worktree, mirroring ``dashboard.member_board_state``'s
    root-first precedence. Unreadable or malformed directories are skipped,
    never raised, so a torn plan mid-worktree-creation cannot fail the board.

    The single implementation both consumers share: ``dashboard`` delegates to
    it (:func:`dashboard.standalone_changes`), so the board's standalone group
    and the workspace report cannot drift."""
    excluded = set(epic_member_slugs or ())
    results = []
    seen = set()

    def _consider(hosting_root, slug):
        if not slug or slug in excluded or slug in seen:
            return
        try:
            content_dir = sc.specs_dir(hosting_root)
            plan_path = _standalone_plan_path(content_dir, slug)
            if plan_path is None:
                return
            with open(plan_path, encoding="utf-8") as fh:
                text = fh.read()
            if any(key == "Epic" for key, _ in sc.parse_plan_metadata(text)):
                return
            state = _member_state(hosting_root, slug)
        except (OSError, ValueError, sc.ConfigError):
            return
        if state == "unplanned":
            return
        seen.add(slug)
        results.append({
            "slug": slug,
            "description": "",
            "risk": None,
            "state": state,
            "location": os.path.abspath(hosting_root),
        })

    # The root's own planned/ changes.
    try:
        planned_dir = os.path.join(sc.specs_dir(root), "planned")
        root_slugs = sorted(os.listdir(planned_dir))
    except (OSError, sc.ConfigError):
        planned_dir, root_slugs = None, []
    for slug in root_slugs:
        if os.path.isdir(os.path.join(planned_dir, slug)):
            _consider(root, slug)

    # Each worktree hosts the change named by its directory.
    worktrees_dir = os.path.join(root, ".worktrees")
    try:
        wt_names = sorted(os.listdir(worktrees_dir))
    except OSError:
        wt_names = []
    for name in wt_names:
        wt = os.path.join(worktrees_dir, name)
        if os.path.isdir(wt):
            _consider(wt, name)

    return results


def _derive_epic_status(states):
    """Derive an epic's status from its members' states: all archived →
    ``complete``; any member archived or with plan status ``active``,
    ``complete``, or ``verified`` → ``active``; otherwise ``ready``."""
    if states and all(s == "archived" for s in states):
        return "complete"
    started = ("archived", "active", "complete", "verified")
    if any(s in started for s in states):
        return "active"
    return "ready"


def _epic_rows(root, slug):
    with open(_epic_path(root, slug), encoding="utf-8") as fh:
        _header, rows = sc.parse_epic_changes(fh.read())
    return rows


# The board lanes in board order — the order the delivery board's columns
# read left to right, and the order the epic report prints them in.
_BOARD_LANES = ("unplanned", "ready", "building", "shipped")


def _epic_report_lines(root, slug):
    """The board-shaped epic report as a list of lines (spec-status
    epic-status-verbs) — the single renderer ``epic-show`` and ``show``'s epic
    fallback both print, so the two outputs are identical by construction.

    In order: the ``<slug>: <status>`` line and the epic's header metadata
    lines (unchanged from before this report existed — the autopilot skill
    reads that status line); a ``shipped <n>/<m>`` line counting the members
    whose derived state is ``archived`` against every stub member; a blank
    line; then the four board lanes in board order, each as a
    ``<LANE> (<count>)`` header even when empty, followed by one indented row
    per member in it. A member's lane comes from :func:`board_lane` — the
    projection the dashboard shares — its risk from the last rating cell of
    its stub-table row (``?`` when the row carries none), and a ``[worktree]``
    marker when its state was derived from a worktree rather than ``root``."""
    path = _epic_path(root, slug)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = ["%s: %s" % (slug, read_epic_status(root, slug) or "?")]
    for key, value in _epic_metadata(text):
        lines.append("%s: %s" % (key, value))

    _header, rows = sc.parse_epic_changes(text)
    members = []
    for mslug, _desc, ratings in rows:
        state, hosting_root = _member_state_with_root(root, mslug)
        risk = ratings[-1].strip() if ratings and ratings[-1].strip() else "?"
        marker = " [worktree]" if hosting_root != root else ""
        members.append((board_lane(state), mslug, state, risk, marker))

    shipped = sum(1 for lane, _s, _st, _r, _m in members if lane == "shipped")
    lines.append("shipped %d/%d" % (shipped, len(members)))
    lines.append("")
    for lane in _BOARD_LANES:
        in_lane = [m for m in members if m[0] == lane]
        lines.append("%s (%d)" % (lane.upper(), len(in_lane)))
        for _lane, mslug, state, risk, marker in in_lane:
            lines.append("  %-22s %-12s risk %s%s"
                         % (mslug, state, risk, marker))
    return lines


def _workspace_epic_slugs(root):
    """Every epic slug under ``root``'s content directory, sorted — the epics
    the workspace report enumerates. An unreadable configuration yields none
    rather than raising."""
    try:
        pattern = os.path.join(sc.specs_dir(root), "epics", "*", "epic.md")
    except sc.ConfigError:
        return []
    return sorted(os.path.basename(os.path.dirname(path))
                  for path in glob.glob(pattern))


def _workspace_report_lines(root):
    """The workspace board report as a list of lines (spec-status
    workspace-board-report) — what ``show`` prints with no name given and no
    spec selected, derived from the spec tree alone (no heartbeat reads).

    In order: a ``N specs · N epics · N initiatives`` totals line mirroring the
    board's filter-strip totals (``dashboard._board_totals_text``) — members
    summed across every epic (standalone changes excluded, as on the board),
    the epic count, and the distinct ``Initiative:`` slugs; a ``shipped <n>/<m>``
    line over every rendered row (epic members plus standalone changes), ``n``
    those whose lane is ``shipped``; a blank line; then the four board lanes in
    board order, each as a ``<LANE> (<count>)`` header even when empty.

    A non-shipped lane prints one indented row per entry carrying its epic's
    slug (``standalone`` for a change planned outside any epic), the member
    slug, its derived state, its risk (the stub-table row's last rating cell,
    ``?`` when absent — always ``?`` for a standalone change, which has no stub
    row), and a ``[worktree]`` marker when the state came from a worktree
    rather than ``root``. ``SHIPPED`` instead prints per-epic rollup rows
    ``<epic-slug> (<n>)`` in epic order, plus ``standalone (<n>)`` last when
    any standalone change is archived — mirroring the board's collapsed
    per-epic shipped groups. Lanes come from :func:`board_lane`, the shared
    projection the epic report and the dashboard use, and standalone changes
    from :func:`standalone_changes`, the discovery the board consumes. An
    unreadable epic file is skipped, never raised."""
    epics = []          # (epic slug, [row, ...]) in epic order
    initiatives = set()
    member_slugs = set()
    for eslug in _workspace_epic_slugs(root):
        try:
            with open(_epic_path(root, eslug), encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        meta = dict(_epic_metadata(text))
        if meta.get("Initiative"):
            initiatives.add(meta["Initiative"])
        _header, stub_rows = sc.parse_epic_changes(text)
        rows = []
        for mslug, _desc, ratings in stub_rows:
            member_slugs.add(mslug)
            state, hosting_root = _member_state_with_root(root, mslug)
            risk = (ratings[-1].strip()
                    if ratings and ratings[-1].strip() else "?")
            marker = " [worktree]" if hosting_root != root else ""
            rows.append((board_lane(state), eslug, mslug, state, risk, marker))
        epics.append((eslug, rows))

    # Changes planned outside any epic fold in under the epic column
    # `standalone`; their hosting location, not a stub table, marks a worktree.
    root_abs = os.path.abspath(root)
    standalone = []
    for entry in standalone_changes(root, member_slugs):
        state = entry["state"]
        marker = " [worktree]" if entry.get("location") != root_abs else ""
        standalone.append((board_lane(state), "standalone", entry["slug"],
                           state, entry.get("risk") or "?", marker))

    all_rows = [row for _eslug, rows in epics for row in rows] + standalone
    specs = sum(len(rows) for _eslug, rows in epics)
    shipped = sum(1 for row in all_rows if row[0] == "shipped")
    lines = ["%d specs · %d epics · %d initiatives"
             % (specs, len(epics), len(initiatives)),
             "shipped %d/%d" % (shipped, len(all_rows)),
             ""]
    for lane in _BOARD_LANES:
        in_lane = [row for row in all_rows if row[0] == lane]
        lines.append("%s (%d)" % (lane.upper(), len(in_lane)))
        if lane == "shipped":
            for eslug, rows in epics:
                count = sum(1 for row in rows if row[0] == "shipped")
                if count:
                    lines.append("  %s (%d)" % (eslug, count))
            count = sum(1 for row in standalone if row[0] == "shipped")
            if count:
                lines.append("  standalone (%d)" % count)
            continue
        for _lane, ecol, mslug, state, risk, marker in in_lane:
            lines.append("  %-20s %-22s %-12s risk %s%s"
                         % (ecol, mslug, state, risk, marker))
    return lines


def cmd_epic_show(root, slug):
    path = _epic_path(root, slug)
    if not os.path.isfile(path):
        raise StatusError("epic '%s' not found (%s)" % (slug, path))
    for line in _epic_report_lines(root, slug):
        print(line)
    return 0


def cmd_epic_sync(root, slug):
    path = _epic_path(root, slug)
    if not os.path.isfile(path):
        raise StatusError("epic '%s' not found (%s)" % (slug, path))
    current = read_epic_status(root, slug)
    # Never touch a draft epic — authoring is still in progress.
    if current == "draft":
        print(current)
        return 0
    states = [_member_state(root, mslug)
              for mslug, _desc, _ratings in _epic_rows(root, slug)]
    derived = _derive_epic_status(states)
    # Write only when the status actually changes: a no-op sync leaves the
    # file untouched (and stays silent about a main-checkout write).
    if derived != current:
        write_epic_status(root, slug, derived)
    print(derived)
    return 0


def cmd_epic_set_status(root, status, slug):
    if status not in sc.EPIC_STATUSES:
        raise StatusError("invalid epic status '%s' (expected one of: %s)"
                          % (status, ", ".join(sc.EPIC_STATUSES)))
    path = _epic_path(root, slug)
    if not os.path.isfile(path):
        raise StatusError("epic '%s' not found (%s)" % (slug, path))
    # Only `ready` is guarded: promoting an epic out of draft requires it to
    # lint clean, mirroring the plan `ready` guard.
    if status == "ready":
        errors = [str(err) for err in _lint_epic_errors(root, slug)]
        if errors:
            raise RefusalError(
                "setting ready requires the epic to validate", errors)
    write_epic_status(root, slug, status)
    print(status)
    return 0


def cmd_epic_set_initiative(root, slug, initiative):
    """Write ``Initiative: <initiative>`` into the epic's header metadata block,
    replacing any existing ``Initiative:`` line and preserving all other header
    and body content (spec-status epic-set-initiative-verb). The value must be a
    kebab-case slug; an unknown epic is an error. Status derivation is
    untouched."""
    if not sc.KEBAB_RE.match(initiative):
        raise StatusError(
            "initiative '%s' is not a kebab-case slug" % initiative)
    path = _epic_path(root, slug)
    if not os.path.isfile(path):
        raise StatusError("epic '%s' not found (%s)" % (slug, path))
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    # Locate the `Status:` line; the metadata block is the contiguous run of
    # `Key: value` lines immediately after it (ended by a blank line or heading).
    status_idx = None
    for i, line in enumerate(lines):
        if STATUS_LINE_RE.match(line):
            status_idx = i
            break
    if status_idx is None:
        raise StatusError("epic '%s' has no `Status:` line" % slug)
    meta_end = status_idx + 1
    init_idx = None
    while meta_end < len(lines):
        ln = lines[meta_end]
        if ln.strip() == "" or ln.lstrip().startswith("#"):
            break
        m = sc.METADATA_LINE_RE.match(ln)
        if not m:
            break
        if m.group(1) == "Initiative":
            init_idx = meta_end
        meta_end += 1
    new_line = "Initiative: %s" % initiative
    if init_idx is not None:
        lines[init_idx] = new_line
    else:
        lines.insert(meta_end, new_line)
    _write_lines(path, lines, text)
    _warn_main_checkout_write(root, path)
    print(initiative)
    return 0


def cmd_config_show(root):
    """Print the resolved layered configuration: each effective top-level key
    with the path of the layer that supplied it (or ``default``), the resolved
    content directory, and the workspace root when discoverable (else a
    none-note). Does not require a workspace; exits zero on a default-only
    resolution (spec-status config-show-verb)."""
    try:
        config, provenance = sc.resolve_config(root)
        content_dir = sc.specs_dirname(config)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    print("config (resolved from %s):" % os.path.abspath(root))
    for key in sorted(config):
        src = provenance.get(key, "default")
        print("  %s = %s  [%s]" % (key, json.dumps(config[key]), src))
    print("content-dir: %s" % content_dir)
    ws_root = sc.find_workspace_root(root)
    if ws_root is None:
        print("workspace: none discoverable")
    else:
        print("workspace: %s" % ws_root)
    return 0


def _format_pipeline_entry(entry):
    """Render one resolved pipeline entry as a single human-readable line
    stating its form and any bindings with their fallbacks (spec-status
    pipeline-show-verb)."""
    if "custom" in entry:
        return "custom '%s'  command: %s" % (
            entry.get("custom"), entry.get("command"))
    stage = entry.get("stage")
    if entry.get("skip") is True:
        return "%s  (skipped)" % stage
    if "tools" in entry:
        bindings = ", ".join(
            "%s (fallback=%s)" % (t.get("name"), t.get("fallback"))
            for t in entry["tools"])
        return "%s  tools: %s" % (stage, bindings)
    if "replace" in entry:
        rep = entry["replace"]
        kind = "command" if rep.get("command") else "tool"
        return "%s  replaced by %s '%s' (fallback=%s)" % (
            stage, kind, rep.get(kind), rep.get("fallback"))
    return stage


def cmd_pipeline_show(root):
    """Print the effective autonomous pipeline: one line per resolved entry
    (form + bindings with fallbacks) plus the provenance of the
    ``autonomous-pipeline`` key — the supplying config file path, or
    ``[default]`` when no layer declares it (spec-status pipeline-show-verb).
    Requires no workspace and no selected change; a defaults-only resolution
    exits zero. A pipeline that fails validation raises, printing every
    validation error and exiting non-zero."""
    try:
        entries, provenance = sc.resolve_pipeline(root)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    source = "[default]" if provenance == "default" else provenance
    print("pipeline (source: %s):" % source)
    for i, entry in enumerate(entries, 1):
        print("  %d. %s" % (i, _format_pipeline_entry(entry)))
    return 0


def _cat_files(root, paths):
    """Print each path in ``paths`` preceded by a ``--- <relpath>`` separator
    line (relpath relative to ``root``), resolving nothing itself — callers pass
    the engine-resolved locations (spec-io mediated-read-verb)."""
    for path in paths:
        rel = os.path.relpath(path, root)
        print("--- %s" % rel)
        with open(path, encoding="utf-8") as fh:
            sys.stdout.write(fh.read())


def cmd_cat(root, kind, slug, personal=False):
    """Print a named artifact's content through the engine's resolved locations
    (spec-io mediated-read-verb). For a change: its ``plan.md``, every delta
    spec, and ``tasks.md``, resolved from ``planned/<slug>/`` and falling back
    to the newest archived ``completed/*-<slug>/`` so a reference survives the
    merge/archive. For a ``wiki`` page, ``personal`` selects the personal
    memory store instead of the workspace store. An unknown name exits
    non-zero."""
    if kind == "change":
        cdir = _readable_change_dir(root, slug)
        if cdir is None:
            raise StatusError("change '%s' not found (%s)"
                              % (slug, _change_dir(root, slug)))
        paths = []
        plan = os.path.join(cdir, "plan.md")
        if os.path.isfile(plan):
            paths.append(plan)
        specs_root = os.path.join(cdir, "specs")
        if os.path.isdir(specs_root):
            for capability in sorted(os.listdir(specs_root)):
                spec = os.path.join(specs_root, capability, "spec.md")
                if os.path.isfile(spec):
                    paths.append(spec)
        tasks = os.path.join(cdir, "tasks.md")
        if os.path.isfile(tasks):
            paths.append(tasks)
        if not paths:
            raise StatusError("change '%s' has no artifacts (%s)" % (slug, cdir))
        _cat_files(root, paths)
        return 0
    if kind == "verified":
        path = os.path.join(sc.specs_dir(root), "verified", slug, "spec.md")
        if not os.path.isfile(path):
            raise StatusError(
                "capability '%s' not found (%s)" % (slug, path))
        _cat_files(root, [path])
        return 0
    if kind == "epic":
        path = _epic_path(root, slug)
        if not os.path.isfile(path):
            raise StatusError("epic '%s' not found (%s)" % (slug, path))
        _cat_files(root, [path])
        return 0
    if kind == "initiative":
        ws_root = _resolve_workspace(root)
        path = sc.initiative_brief_path(ws_root, slug)
        if not os.path.isfile(path):
            raise StatusError("initiative '%s' not found (%s)" % (slug, path))
        _cat_files(root, [path])
        return 0
    if kind == "research":
        path = os.path.join(
            sc.specs_dir(root), "research", slug, "report.md")
        if not os.path.isfile(path):
            raise StatusError("research '%s' not found (%s)" % (slug, path))
        _cat_files(root, [path])
        return 0
    if kind == "video":
        path = os.path.join(sc.specs_dir(root), "video", slug, "brief.md")
        if not os.path.isfile(path):
            raise StatusError("video '%s' not found (%s)" % (slug, path))
        _cat_files(root, [path])
        return 0
    if kind == "wiki":
        wiki = _wiki_store(root, personal)
        # The reserved slugs resolve to the store's top-level files; every other
        # slug names a `wiki/<slug>.md` page.
        if slug in ("index", "log", "queue", "schema"):
            path = os.path.join(wiki, slug + ".md")
        else:
            path = os.path.join(wiki, "wiki", slug + ".md")
        if not os.path.isfile(path):
            raise StatusError("wiki page '%s' not found (%s)" % (slug, path))
        _cat_files(root, [path])
        return 0
    raise StatusError(
        "unknown cat kind '%s' (expected "
        "change|verified|epic|initiative|research|video|wiki)" % kind)


def _lint_epic_errors(root, slug):
    errors = []
    lint_epic(root, slug, errors)
    return errors


# ---------------------------------------------------------------------------
# Initiative status verbs (spec-status initiative-status-verbs)
# ---------------------------------------------------------------------------


def _resolve_workspace(root):
    """Return the workspace root discoverable from ``root``, or raise a
    :class:`StatusError` when none is found. Initiative briefs live in the
    workspace (discovered by the nearest ancestor whose ``.shipd-config.json``
    declares ``workspace``), so every initiative verb needs one."""
    ws_root = sc.find_workspace_root(root)
    if ws_root is None:
        raise StatusError(
            "no workspace found from %s (an initiative brief lives in the "
            "workspace, discovered by the nearest ancestor whose "
            ".shipd-config.json declares `workspace`)" % root)
    return ws_root


def _wiki_store(root, personal):
    """Resolve the wiki store directory a verb operates on (spec-status
    wiki-status-verbs). When ``personal`` is set, resolve the personal memory
    store at ``<memory_dir>/wiki`` by fixed path (bypassing workspace
    discovery); otherwise resolve the workspace store through workspace
    discovery. This single branch point selects the store — the rest of each
    verb is store-agnostic."""
    if personal:
        return sc.memory_store_dir(root)
    return sc.wiki_dir(_resolve_workspace(root))


def read_initiative_status(path):
    """Return a brief's status value, or None when the file is missing or
    carries no valid ``Status:`` line. A value outside the three initiative
    statuses is treated as invalid (None)."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    for line in text.splitlines():
        m = STATUS_LINE_RE.match(line)
        if m:
            val = m.group(1)
            return val if val in sc.INITIATIVE_STATUSES else None
    return None


def write_initiative_status(path, status):
    """Rewrite a brief's ``Status:`` line in place (the linter guarantees one)."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if STATUS_LINE_RE.match(line):
            lines[i] = "Status: %s" % status
            _write_lines(path, lines, text)
            return
    raise StatusError("brief has no `Status:` line to rewrite (%s)" % path)


def count_brief_requirements(text):
    """Return ``(done, total)`` requirement-checkbox counts, reusing the
    tasks.md checkbox conventions: ``- [x]`` is done; ``- [ ]`` and ``- [~]``
    count as unticked."""
    done = total = 0
    for line in text.splitlines():
        m = CHECKBOX_RE.match(line)
        if not m:
            continue
        total += 1
        if m.group(1) in ("x", "X"):
            done += 1
    return done, total


def _brief_path(root, slug):
    ws_root = _resolve_workspace(root)
    path = sc.initiative_brief_path(ws_root, slug)
    if not os.path.isfile(path):
        raise StatusError("initiative '%s' has no brief (%s)" % (slug, path))
    return path


def cmd_initiative_show(root, slug):
    path = _brief_path(root, slug)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    print("%s: %s" % (slug, read_initiative_status(path) or "?"))
    for key, value in sc.parse_plan_metadata(text):
        if key in sc.BRIEF_METADATA_KEYS:
            print("%s: %s" % (key, value))
    done, total = count_brief_requirements(text)
    print("Requirements: %d/%d" % (done, total))
    for line in text.splitlines():
        if CHECKBOX_RE.match(line):
            print(line.rstrip())
    return 0


def cmd_initiative_sync(root, slug):
    path = _brief_path(root, slug)
    current = read_initiative_status(path)
    # Never re-derive a dropped brief — abandonment is a manual, sticky act.
    if current == "dropped":
        print(current)
        return 0
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    done, total = count_brief_requirements(text)
    derived = "achieved" if total > 0 and done == total else "open"
    write_initiative_status(path, derived)
    print(derived)
    return 0


def cmd_initiative_set_status(root, status, slug):
    if status not in sc.INITIATIVE_STATUSES:
        raise StatusError(
            "invalid initiative status '%s' (expected one of: %s)"
            % (status, ", ".join(sc.INITIATIVE_STATUSES)))
    path = _brief_path(root, slug)
    write_initiative_status(path, status)
    print(status)
    return 0


# ---------------------------------------------------------------------------
# Workspace / project status verbs (spec-status workspace-status-verbs)
# ---------------------------------------------------------------------------


def _load_projects(ws_root):
    """Return the workspace registry's ``projects`` map (a dict), or ``{}`` when
    the registry is absent, unloadable, or declares no object ``projects`` map.
    Display must never crash on an invalid registry — validation lives in the
    linter (``--workspace``)."""
    try:
        registry = sc.load_workspace(ws_root)
    except sc.ConfigError:
        return {}
    projects = registry.get("projects")
    return projects if isinstance(projects, dict) else {}


def _repo_display(ws_root, repo):
    """Annotate a repo entry for display: ``(absent)`` when its path is not a
    directory on this machine, and ``[url]`` when the entry carries a clone URL
    (both display-only — absence is never an error). Paths are read uniformly
    from string and object entry shapes via ``repo_entry_path``."""
    path = sc.repo_entry_path(repo)
    if path is None:
        return None
    text = path if os.path.isdir(os.path.join(ws_root, path)) else \
        "%s (absent)" % path
    if isinstance(repo, dict) and repo.get("url"):
        text = "%s [url]" % text
    return text


def _project_repo_lines(ws_root, entry):
    """Yield the annotated repo display lines of one project registry entry,
    skipping malformed entries defensively."""
    repos = entry.get("repos") if isinstance(entry, dict) else None
    if not isinstance(repos, list):
        return
    for repo in repos:
        line = _repo_display(ws_root, repo)
        if line is not None:
            yield line


def _context_path(ws_root, slug):
    return sc.project_context_path(ws_root, slug)


def _iter_initiatives(ws_root):
    """Yield ``(slug, status, project)`` for each brief under
    ``<ws_root>/<content-dir>/initiatives/<slug>/brief.md``, in sorted slug
    order. ``project`` is the brief's ``Project:`` scope (or ``None`` when
    unscoped)."""
    idir = sc.initiatives_dir(ws_root)
    if not os.path.isdir(idir):
        return
    for slug in sorted(os.listdir(idir)):
        path = sc.initiative_brief_path(ws_root, slug)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        status = read_initiative_status(path) or "?"
        project = None
        for key, value in sc.parse_plan_metadata(text):
            if key == "Project":
                project = value
                break
        yield slug, status, project


def cmd_workspace_show(root):
    ws_root = _resolve_workspace(root)
    print("workspace: %s" % ws_root)
    try:
        registry = sc.load_workspace(ws_root)
    except sc.ConfigError:
        registry = {}
    focus = registry.get("focus")
    if isinstance(focus, str) and focus:
        print("focus: %s" % focus)
    projects = _load_projects(ws_root)
    for slug in sorted(projects):
        print("project %s:" % slug)
        for line in _project_repo_lines(ws_root, projects[slug]):
            print("  repo: %s" % line)
        present = os.path.isfile(_context_path(ws_root, slug))
        print("  context: %s" % ("yes" if present else "no"))
    initiatives = list(_iter_initiatives(ws_root))
    if initiatives:
        print("initiatives:")
        for slug, status, project in initiatives:
            scope = "Project: %s" % project if project else "unscoped"
            print("  %s: %s (%s)" % (slug, status, scope))
    if sc.project_of(ws_root, root) is None:
        print("(this repository falls under the implicit default project)")
    return 0


def cmd_workspace_init(path, git=False):
    """Initialize a workspace at ``path`` through the engine and print the
    created root (spec-status workspace-init-verb). Unlike the other workspace
    verbs, this does NOT resolve a workspace from ``--root`` — it runs precisely
    when none is discoverable. When ``git`` is set, requests the engine's git
    option (git-init when the target is not already inside a work tree, plus the
    seeded member-repos ``.gitignore`` block). A refusal or error (an existing
    workspace already discoverable from the target, or a missing target
    directory) surfaces as a :class:`StatusError`, exiting non-zero."""
    try:
        created = sc.init_workspace(path, git=git)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    print(created)
    return 0


def cmd_project_show(root, slug):
    ws_root = _resolve_workspace(root)
    projects = _load_projects(ws_root)
    if slug not in projects:
        declared = ", ".join(sorted(projects)) or "(none)"
        raise StatusError(
            "unknown project '%s' (declared slugs: %s)" % (slug, declared))
    print("project %s:" % slug)
    for line in _project_repo_lines(ws_root, projects[slug]):
        print("  repo: %s" % line)
    ctx_path = _context_path(ws_root, slug)
    if os.path.isfile(ctx_path):
        with open(ctx_path, encoding="utf-8") as fh:
            first = fh.readline().strip()
        print("  context: yes (%s)" % first if first else "  context: yes")
    else:
        print("  context: no")
    scoped = [(s, st) for s, st, project in _iter_initiatives(ws_root)
              if project == slug]
    if scoped:
        print("initiatives:")
        for s, st in scoped:
            print("  %s: %s" % (s, st))
    return 0


def _render_member_block(record):
    """Print one member record as an indented keyed block (spec-status
    workspace-sync-verb)."""
    print("member: %s" % record["member"])
    print("  path: %s" % record["path"])
    print("  state: %s" % record["state"])
    print("  action: %s" % record["action"])
    for key in ("source", "url", "branch", "command", "drift", "reason"):
        if key in record:
            print("  %s: %s" % (key, record[key]))


def cmd_workspace_sync(root, as_json=False, write_gitignore=False):
    """Print the workspace's materialization plan and, with
    ``--write-gitignore``, reconcile the marked member-repos block (spec-status
    workspace-sync-verb).

    Resolves the workspace from ``root`` (erroring when none is discoverable),
    loads and validates its registry (exiting non-zero and printing the findings
    when it fails ``validate_workspace``), then computes the engine's plan from
    the resolved layered configuration. A computed plan exits zero regardless of
    drift or unmaterializable members. Renders one keyed block per member
    followed by a ``gitignore:`` section, or — with ``--json`` — one JSON object
    per record carrying a ``kind`` field. Without ``--write-gitignore`` it writes
    nothing; with it, it additionally rewrites only the marked member-repos block
    to match the manifest's member paths. A malformed ``clone_sources`` value
    surfaces as a :class:`StatusError` naming the key."""
    ws_root = _resolve_workspace(root)
    try:
        registry = sc.load_workspace(ws_root)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    errors = sc.validate_workspace(registry)
    if errors:
        raise StatusError(
            "workspace registry is invalid:\n" + "\n".join(errors))
    config, _prov = sc.resolve_config(ws_root)
    try:
        records = sc.plan_workspace_sync(ws_root, config)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))

    if as_json:
        for record in records:
            print(json.dumps(record))
    else:
        gitignore = None
        for record in records:
            if record.get("kind") == "gitignore":
                gitignore = record
                continue
            _render_member_block(record)
        print("gitignore:")
        missing = gitignore["missing"] if gitignore else []
        stale = gitignore["stale"] if gitignore else []
        print("  missing: %s" % (", ".join(missing) if missing else "(none)"))
        print("  stale: %s" % (", ".join(stale) if stale else "(none)"))

    if write_gitignore:
        member_paths = [r["path"] for r in records if r.get("kind") == "member"]
        sc.write_members_gitignore_block(ws_root, member_paths)
    return 0


# ---------------------------------------------------------------------------
# Wiki status verbs (spec-status wiki-status-verbs)
# ---------------------------------------------------------------------------

WIKI_SCHEMA_SEED = """# Wiki schema

The workspace knowledge store. Conventions (enforced by `spec_lint.py --wiki`):

- **Pages** live at `wiki/<slug>.md` with kebab-case slugs. The slugs `index`,
  `log`, `queue`, `schema`, and `sources` are reserved.
- **Wikilinks** `[[slug]]` in a page or in `index.md` (outside fenced code
  blocks) must resolve to an existing page.
- **Index** — `index.md` catalogs every page as `- [[slug]] — <summary>`; the
  entry set and the page set must match exactly.
- **Log** — `log.md` records append-only entries as level-2 headers
  `## [YYYY-MM-DD] <op> | <subject>`.
- **Queue** — `queue.md` holds pending questions as `## q-<slug>` blocks, each
  with non-empty `- Asked:`, `- Question:`, `- Options:`, `- Recommendation:`,
  and `- Answer:` lines (`Answer: pending` until answered).
- **Sources** under `sources/` are immutable: add-only, never overwritten.
"""


def _write_text(path, text):
    """Write ``text`` to ``path``, creating parent directories as needed."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def cmd_wiki_init(root, personal=False):
    """Scaffold the wiki store layout (spec-status wiki-status-verbs). Resolves
    the workspace store by default, or the personal memory store under
    ``personal``; refuses when the wiki directory already exists (mirroring
    ``init_workspace``'s refuse-to-nest guard). Seeds ``schema.md`` with the
    grammar conventions, an empty ``index.md`` and ``queue.md``, a first dated
    ``log.md`` entry, and empty ``sources/`` and ``wiki/`` directories, then
    prints the created store root."""
    wiki = _wiki_store(root, personal)
    if os.path.exists(wiki):
        raise StatusError(
            "wiki store already exists at %s; refusing to overwrite" % wiki)
    os.makedirs(os.path.join(wiki, "wiki"))
    os.makedirs(os.path.join(wiki, "sources"))
    today = datetime.date.today().isoformat()
    _write_text(os.path.join(wiki, "schema.md"), WIKI_SCHEMA_SEED)
    _write_text(os.path.join(wiki, "index.md"), "# Index\n")
    _write_text(os.path.join(wiki, "queue.md"), "# Queue\n")
    _write_text(
        os.path.join(wiki, "log.md"),
        "# Log\n\n## [%s] wiki-init | initialized the wiki store\n\n"
        "Seeded the empty store layout.\n" % today)
    print(wiki)
    return 0


def cmd_wiki_show(root, personal=False):
    """Print the wiki store's health (spec-status wiki-status-verbs): the store
    root, a ``base:`` line reporting the resolved ``wiki_base`` store, the page
    count, index-coverage health, the pending-question count, and the last log
    entry. Resolves the workspace store by default, or the personal memory store
    under ``personal``, and errors when no store exists. A personal store
    participates in no base layering, so its ``base:`` line is always ``none``."""
    wiki = _wiki_store(root, personal)
    if not os.path.isdir(wiki):
        raise StatusError("no wiki store at %s (run `wiki-init`)" % wiki)
    print("wiki: %s" % wiki)

    # The layered `wiki_base` store, if declared (shipd-config wiki-base-key). A
    # malformed value surfaces as a ConfigError → the verb's error exit. A base
    # resolving to this store's own directory is treated as no base, so running
    # inside the base workspace itself never double-layers. The personal store
    # participates in no base layering, so it always reports `base: none`.
    if personal:
        print("base: none")
    else:
        base = sc.wiki_base_dir(_resolve_workspace(root))
        if base is None or os.path.realpath(base) == os.path.realpath(wiki):
            print("base: none")
        elif os.path.isdir(base):
            print("base: %s (present)" % base)
        else:
            print("base: %s (absent)" % base)

    pages_dir = os.path.join(wiki, "wiki")
    page_slugs = set()
    if os.path.isdir(pages_dir):
        for fname in os.listdir(pages_dir):
            if fname.endswith(".md") and os.path.isfile(
                    os.path.join(pages_dir, fname)):
                page_slugs.add(fname[:-3])
    print("pages: %d" % len(page_slugs))

    index_path = os.path.join(wiki, "index.md")
    entry_slugs = set()
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as fh:
            for slug, _summary in sc.parse_index_entries(fh.read()):
                entry_slugs.add(slug)
    unindexed = page_slugs - entry_slugs
    orphaned = entry_slugs - page_slugs
    if not unindexed and not orphaned:
        print("coverage: ok")
    else:
        print("coverage: %d unindexed page(s), %d orphaned entry(ies)"
              % (len(unindexed), len(orphaned)))

    queue_path = os.path.join(wiki, "queue.md")
    pending = 0
    if os.path.isfile(queue_path):
        with open(queue_path, encoding="utf-8") as fh:
            for _qid, fields in sc.parse_queue_blocks(fh.read()):
                if fields.get("Answer", "").strip() == "pending":
                    pending += 1
    print("pending questions: %d" % pending)

    log_path = os.path.join(wiki, "log.md")
    last = None
    if os.path.isfile(log_path):
        with open(log_path, encoding="utf-8") as fh:
            for line in fh.read().splitlines():
                if sc.WIKI_LOG_HEADER_RE.match(line):
                    last = line.strip()
    print("last log: %s" % (last if last else "(none)"))
    return 0


def _validate_queue_text(text):
    """Return a list of error strings for a ``queue.md`` body, using the
    spec_common queue parser: every ``## q-<slug>`` block must be unique and
    carry all five non-empty fields. Empty when the queue is valid."""
    errors = []
    seen = set()
    for qid, fields in sc.parse_queue_blocks(text):
        if qid in seen:
            errors.append("duplicate block '%s'" % qid)
        seen.add(qid)
        for field in sc.WIKI_QUEUE_FIELDS:
            if field not in fields:
                errors.append("block '%s' is missing the `- %s:` field"
                              % (qid, field))
            elif fields[field].strip() == "":
                errors.append("block '%s' has an empty `- %s:` field"
                              % (qid, field))
    return errors


def cmd_wiki_queue_add(root, slug, question, options, recommendation, origin):
    """Append a pending-question block to the wiki queue (spec-status
    wiki-status-verbs, shipd-wiki wiki-question-queue). Builds a ``## q-<slug>``
    block carrying the given ``--question``/``--options``/``--recommendation``,
    an ``Asked: <today> [origin]`` line, and ``Answer: pending``; appends it to
    ``queue.md`` and re-validates the resulting queue with the spec_common
    parser. A duplicate slug or an invalid result restores the prior
    ``queue.md`` and exits non-zero."""
    if not sc.KEBAB_RE.match(slug):
        raise StatusError("queue slug '%s' is not a kebab-case slug" % slug)
    ws_root = _resolve_workspace(root)
    wiki = sc.wiki_dir(ws_root)
    queue_path = os.path.join(wiki, "queue.md")
    if not os.path.isfile(queue_path):
        raise StatusError("no wiki store at %s (run `wiki-init`)" % wiki)
    with open(queue_path, encoding="utf-8") as fh:
        before = fh.read()

    qid = "q-%s" % slug
    existing = {q for q, _f in sc.parse_queue_blocks(before)}
    if qid in existing:
        # Duplicate: never write, so queue.md stays byte-identical.
        raise StatusError("queue already has a block '%s'" % qid)

    asked = datetime.date.today().isoformat()
    if origin:
        asked = "%s %s" % (asked, origin)
    block = (
        "## %s\n"
        "- Asked: %s\n"
        "- Question: %s\n"
        "- Options: %s\n"
        "- Recommendation: %s\n"
        "- Answer: pending\n"
        % (qid, asked, question, options, recommendation))
    new_text = before.rstrip("\n") + "\n\n" + block
    _write_text(queue_path, new_text)

    errors = _validate_queue_text(new_text)
    if errors:
        _write_text(queue_path, before)  # restore prior content
        raise StatusError(
            "queue would become invalid; nothing appended (%s)"
            % "; ".join(errors))
    # A successful append auto-commits queue.md when the store sits inside a git
    # work tree (shipd-wiki wiki-autocommit); a no-op outside git, and a commit
    # failure never fails the write.
    sc.wiki_autocommit(wiki, [queue_path], "shipd-wiki: queue-add %s" % qid)
    print(qid)
    return 0


def _remove_index_entry(index_text, slug):
    """Return ``index_text`` with any ``- [[slug]] — …`` catalog entry for
    ``slug`` dropped (shipd-wiki wiki-index-and-log). Non-entry lines and entries
    for other slugs are preserved verbatim, including their line endings."""
    kept = []
    for line in index_text.splitlines(keepends=True):
        m = sc.WIKI_INDEX_ENTRY_RE.match(line.rstrip("\n"))
        if m and m.group(1) == slug:
            continue
        kept.append(line)
    return "".join(kept)


def cmd_wiki_remove(root, slug, personal=False):
    """Remove a wiki page from the store (spec-status wiki-remove-verb).

    Resolves the workspace store by default, or the personal memory store under
    ``personal``. Refuses a reserved slug (``index``/``log``/``queue``/
    ``schema``/``sources``) and a missing ``wiki/<slug>.md`` up front, writing
    nothing. Otherwise backs up ``wiki/<slug>.md``, ``index.md``, and
    ``log.md``; deletes the page; drops the page's ``index.md`` catalog entry;
    and appends a ``## [YYYY-MM-DD] remove | <slug>`` entry to ``log.md``. The
    resulting store is validated with the whole-store wiki lint; on any finding
    the backed-up files are restored byte-for-byte and the verb exits non-zero
    naming the reason. On a clean removal the touched files auto-commit inside a
    git work tree."""
    wiki = _wiki_store(root, personal)
    if not os.path.isdir(wiki):
        raise StatusError("no wiki store at %s (run `wiki-init`)" % wiki)
    if slug in sc.WIKI_RESERVED_SLUGS:
        raise StatusError(
            "'%s' is a reserved slug and cannot be removed (reserved: %s)"
            % (slug, ", ".join(sc.WIKI_RESERVED_SLUGS)))
    page_path = os.path.join(wiki, "wiki", slug + ".md")
    if not os.path.isfile(page_path):
        raise StatusError("wiki page '%s' not found (%s)" % (slug, page_path))
    index_path = os.path.join(wiki, "index.md")
    log_path = os.path.join(wiki, "log.md")

    # Back up every file we may touch (bytes, or None when absent) so the store
    # can be restored byte-for-byte if the lint rejects the result.
    backup = {}
    for p in (page_path, index_path, log_path):
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                backup[p] = fh.read()
        else:
            backup[p] = None

    # Delete the page, drop its index entry, and log the removal.
    os.remove(page_path)
    if backup[index_path] is not None:
        _write_text(
            index_path,
            _remove_index_entry(backup[index_path].decode("utf-8"), slug))
    log_text = (backup[log_path].decode("utf-8")
                if backup[log_path] is not None else "# Log\n")
    today = datetime.date.today().isoformat()
    _write_text(
        log_path,
        log_text.rstrip("\n") + "\n\n## [%s] remove | %s\n" % (today, slug))

    # Validate the whole resulting store with the wiki lint (the same entry
    # point emit_wiki uses). On any finding — e.g. the removal would strand an
    # inbound [[slug]] wikilink in another page — restore the backed-up files
    # byte-for-byte and exit non-zero naming the reason (the finding's location
    # names the linking page for a stranded wikilink).
    errors = []
    lint_wiki(None, errors, wiki=wiki)
    if errors:
        for p, original in backup.items():
            if original is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                with open(p, "wb") as fh:
                    fh.write(original)
        raise StatusError(
            "removing '%s' would leave the store invalid; nothing removed (%s)"
            % (slug, "; ".join(str(e) for e in errors)))

    # A clean removal auto-commits exactly the touched files when the store sits
    # inside a git work tree (shipd-wiki wiki-autocommit); a no-op outside git, and
    # a commit failure never fails the removal.
    sc.wiki_autocommit(
        wiki, [page_path, index_path, log_path], "shipd-wiki: remove %s" % slug)
    print(slug)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read/write spec lifecycle status and the current-spec "
                    "selection for the shipd spec engine.")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repo root containing am/ (default: cwd)")
    sub = parser.add_subparsers(dest="verb")

    p_use = sub.add_parser("use", help="record the spec being worked on")
    p_use.add_argument("change")

    sub.add_parser("current", help="print the selected change name")

    p_show = sub.add_parser(
        "show",
        help="print a change's status and progress (the workspace board "
             "report with no change given and none selected)")
    p_show.add_argument("change", nargs="?", default=None)

    p_status = sub.add_parser("status", help="print the bare status value")
    p_status.add_argument("change", nargs="?", default=None)

    p_validate = sub.add_parser(
        "validate", help="structurally validate the change")
    p_validate.add_argument("change", nargs="?", default=None)

    p_set = sub.add_parser(
        "set-status", help="write a validated status value (guarded)")
    p_set.add_argument("status")
    p_set.add_argument("change", nargs="?", default=None)
    p_set.add_argument("--force", action="store_true",
                       help="bypass the transition guards (not value checks)")

    p_sync = sub.add_parser("sync", help="re-derive status from tasks.md")
    p_sync.add_argument("change", nargs="?", default=None)

    p_locate = sub.add_parser(
        "locate",
        help="find an installed change across the root and its worktrees")
    p_locate.add_argument("change", nargs="?", default=None)

    p_check_base = sub.add_parser(
        "check-base",
        help="compare a change's deltas against the master library (read-only)")
    p_check_base.add_argument("change", nargs="?", default=None)

    p_epic_show = sub.add_parser(
        "epic-show",
        help="print an epic's board-shaped report (status, metadata, shipped "
             "progress, members grouped into the board's lanes)")
    p_epic_show.add_argument("slug")

    p_epic_sync = sub.add_parser(
        "epic-sync", help="re-derive an epic's status from member states")
    p_epic_sync.add_argument("slug")

    p_epic_set = sub.add_parser(
        "epic-set-status",
        help="write a validated epic status (ready guarded by lint)")
    p_epic_set.add_argument("status")
    p_epic_set.add_argument("slug")

    p_epic_set_init = sub.add_parser(
        "epic-set-initiative",
        help="tag an epic with one initiative (Initiative: header line)")
    p_epic_set_init.add_argument("slug")
    p_epic_set_init.add_argument("initiative")

    sub.add_parser(
        "config-show",
        help="print the resolved layered configuration and its provenance")

    sub.add_parser(
        "pipeline-show",
        help="print the effective autonomous pipeline and its provenance")

    p_cat = sub.add_parser(
        "cat",
        help="print an artifact's content with `--- <relpath>` separators")
    p_cat.add_argument("kind",
                       choices=("change", "verified", "epic", "initiative",
                                "research", "video", "wiki"))
    p_cat.add_argument("slug")
    p_cat.add_argument(
        "--personal", action="store_true",
        help="for a `wiki` page, read from the personal memory store "
             "(<memory_dir>/wiki) instead of the workspace store")

    p_init_show = sub.add_parser(
        "initiative-show",
        help="print a brief's status, metadata, and requirement progress")
    p_init_show.add_argument("slug")

    p_init_sync = sub.add_parser(
        "initiative-sync",
        help="re-derive an initiative's status from its requirement checkboxes")
    p_init_sync.add_argument("slug")

    p_init_set = sub.add_parser(
        "initiative-set-status",
        help="write a validated initiative status (open/achieved/dropped)")
    p_init_set.add_argument("status")
    p_init_set.add_argument("slug")

    p_ws_init = sub.add_parser(
        "workspace-init",
        help="initialize a workspace at the given directory")
    p_ws_init.add_argument("path")
    p_ws_init.add_argument(
        "--git", action="store_true",
        help="git-init the target when needed and seed a marked member-repos "
             ".gitignore block")

    sub.add_parser(
        "workspace-show",
        help="print the workspace root, its projects, and its initiatives")

    p_proj_show = sub.add_parser(
        "project-show",
        help="print one project's repos, context, and scoped initiatives")
    p_proj_show.add_argument("slug")

    p_ws_sync = sub.add_parser(
        "workspace-sync",
        help="print the per-member materialization plan (keyed blocks or "
             "--json); --write-gitignore reconciles the marked member block")
    p_ws_sync.add_argument(
        "--json", action="store_true", dest="json",
        help="emit one JSON object per record (kind: member/gitignore)")
    p_ws_sync.add_argument(
        "--write-gitignore", action="store_true", dest="write_gitignore",
        help="rewrite only the marked member-repos .gitignore block to match "
             "the manifest's member paths")

    p_wiki_init = sub.add_parser(
        "wiki-init",
        help="scaffold the workspace wiki store layout")
    p_wiki_init.add_argument(
        "--personal", action="store_true",
        help="scaffold the personal memory store (<memory_dir>/wiki) by fixed "
             "path instead of the workspace store")

    p_wiki_show = sub.add_parser(
        "wiki-show",
        help="print the wiki store's root, page count, coverage, and last log")
    p_wiki_show.add_argument(
        "--personal", action="store_true",
        help="report the personal memory store (<memory_dir>/wiki) instead of "
             "the workspace store")

    p_wiki_remove = sub.add_parser(
        "wiki-remove",
        help="remove a wiki page, its index entry, and log the removal")
    p_wiki_remove.add_argument("slug")
    p_wiki_remove.add_argument(
        "--personal", action="store_true",
        help="remove from the personal memory store (<memory_dir>/wiki) "
             "instead of the workspace store")

    p_wiki_qadd = sub.add_parser(
        "wiki-queue-add",
        help="append a pending-question block to the wiki queue")
    p_wiki_qadd.add_argument("slug")
    p_wiki_qadd.add_argument("--question", required=True)
    p_wiki_qadd.add_argument("--options", required=True)
    p_wiki_qadd.add_argument("--recommendation", required=True)
    p_wiki_qadd.add_argument("--origin", default=None)

    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.verb is None:
        parser.print_help(sys.stderr)
        return 2

    try:
        if args.verb == "use":
            return cmd_use(root, args.change)
        if args.verb == "current":
            return cmd_current(root)
        if args.verb == "show":
            return cmd_show(root, args.change)
        if args.verb == "status":
            return cmd_status(root, args.change)
        if args.verb == "validate":
            return cmd_validate(root, args.change)
        if args.verb == "set-status":
            return cmd_set_status(root, args.status, args.change, args.force)
        if args.verb == "sync":
            return cmd_sync(root, args.change)
        if args.verb == "locate":
            return cmd_locate(root, args.change)
        if args.verb == "check-base":
            return cmd_check_base(root, args.change)
        if args.verb == "epic-show":
            return cmd_epic_show(root, args.slug)
        if args.verb == "epic-sync":
            return cmd_epic_sync(root, args.slug)
        if args.verb == "epic-set-status":
            return cmd_epic_set_status(root, args.status, args.slug)
        if args.verb == "epic-set-initiative":
            return cmd_epic_set_initiative(root, args.slug, args.initiative)
        if args.verb == "config-show":
            return cmd_config_show(root)
        if args.verb == "pipeline-show":
            return cmd_pipeline_show(root)
        if args.verb == "cat":
            return cmd_cat(root, args.kind, args.slug, args.personal)
        if args.verb == "initiative-show":
            return cmd_initiative_show(root, args.slug)
        if args.verb == "initiative-sync":
            return cmd_initiative_sync(root, args.slug)
        if args.verb == "initiative-set-status":
            return cmd_initiative_set_status(root, args.status, args.slug)
        if args.verb == "workspace-init":
            return cmd_workspace_init(args.path, args.git)
        if args.verb == "workspace-show":
            return cmd_workspace_show(root)
        if args.verb == "project-show":
            return cmd_project_show(root, args.slug)
        if args.verb == "workspace-sync":
            return cmd_workspace_sync(
                root, as_json=args.json,
                write_gitignore=args.write_gitignore)
        if args.verb == "wiki-init":
            return cmd_wiki_init(root, args.personal)
        if args.verb == "wiki-show":
            return cmd_wiki_show(root, args.personal)
        if args.verb == "wiki-remove":
            return cmd_wiki_remove(root, args.slug, args.personal)
        if args.verb == "wiki-queue-add":
            return cmd_wiki_queue_add(
                root, args.slug, args.question, args.options,
                args.recommendation, args.origin)
    except RefusalError as exc:
        print("Refused: %s" % exc.reason, file=sys.stderr)
        for detail in exc.details:
            print(detail, file=sys.stderr)
        return 3
    except StatusError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1
    except sc.ConfigError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
