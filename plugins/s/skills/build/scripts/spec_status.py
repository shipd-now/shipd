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

  init               create the content directory's verified/, planned/,
                     completed/, and research/ directories (parents included),
                     printing one `created`/`exists` line per directory and the
                     summary `all shipd directories are ready`. Never modifies
                     or removes anything that already exists, so it is safe to
                     re-run; refuses without creating anything when the content
                     directory or a target exists as a non-directory
  use <change>       record the spec being worked on in .shipd/state.json (the content dir)
  current            print the selected change name (nothing if none)
  show [change]      print "<change>: <status> (<done>/<total> tasks)"; with no
                     change given and none selected, print the workspace board
                     report instead — totals, shipped progress, and the four
                     board lanes over every epic's members plus the standalone
                     changes. Run from a root inside no declared project repo,
                     that board additionally aggregates every declared
                     `workspace.projects` repo present on disk, each exactly as
                     a root is, its rows carrying a `[<project>]` marker; run
                     from inside a declared project repo (or with no registry
                     discoverable) it stays scoped to the invocation root
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
  related <term> [<term>...]
                     rank the spec library's artifacts (verified capabilities,
                     planned changes, completed archives, research reports,
                     epics, and — where a workspace is discoverable — the
                     workspace wiki's pages) by case-insensitive term-hit
                     count, printing a keyed block (kind/slug/score/path) per
                     match, top ten first plus a remainder line; the wiki and
                     any missing corpus directory are skipped silently
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
  pipeline-show [--expand PRESET] [--json]
                     print the effective autonomous pipeline: one line per
                     resolved entry (form, bindings with fallbacks, declared
                     per-stage options) plus the provenance of the
                     `autonomous-pipeline` key. With --expand, print the named
                     built-in preset's entry list as indented JSON — the value
                     to declare to fork it — resolving no config. With --json,
                     emit the machine contract instead of the text report: one
                     JSON object whose `source` is the raw provenance
                     (`default`, a config file path, or `preset:<name>
                     (<path>)`) and whose `entries` are the resolved entry
                     dicts; --expand --json prints the same entry-list array
                     flagless expand does
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
  workspace-init <path> [--git] [--nested]
                     initialize a workspace at <path> (declaring `workspace`
                     in <path>/.shipd-config.json), printing the created
                     root; refuses when a workspace is already discoverable
                     from the target or the target directory is missing. With
                     --git, git-init the target when it is not already inside a
                     work tree and seed a marked member-repos .gitignore block.
                     With --nested, permit creating the workspace beneath an
                     enclosing one and additionally print the enclosing root;
                     still refuses when the target itself already declares
                     `workspace`. Unlike the other workspace verbs it does not
                     require (or resolve) an existing workspace
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

The six read verbs — ``show``, ``status``, ``locate``, ``related``,
``epic-show``, and
``workspace-show`` — additionally accept ``--json``, emitting exactly one JSON
document on stdout in place of their text report, derived from the same data
(spec-status json-output); ``pipeline-show`` accepts it on the same terms, as
the machine contract its skill consumers read instead of the rendered labels.
Exit codes and the ``Error:`` stderr paths are the same in both modes.

The initiative, workspace, and project verbs resolve the workspace from
``--root`` and exit non-zero when no workspace is discoverable.

Where ``[change]`` is omitted it defaults to the currently-selected spec; the
CLI exits non-zero with an error when none is selected — except ``show``, which
reports the workspace board instead (aggregating the declared workspace
projects when the invocation root lies inside none of them). All paths are
resolved under ``--root`` (default: the current working directory), matching
spec_lint.

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
import build_report  # noqa: E402
import cli_common as cc  # noqa: E402
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

# The content directory's layout: the master library, the in-flight changes,
# the applied archives, and the research reports' home. Everything else under
# the content directory is created lazily by the emit and merge engines, so
# ``init`` makes these four and nothing else.
LAYOUT_DIRS = ("verified", "planned", "completed", "research")


def cmd_init(root):
    """Create ``root``'s content-directory layout — ``verified/``,
    ``planned/``, ``completed/``, and ``research/`` — and report its readiness
    (spec-status layout-init-verb).

    The content directory resolves through the layered configuration, so a
    declared ``dir`` key is honored. Check-then-create: every target is probed
    before the first directory is made, so a non-directory anywhere on the
    layout's paths refuses the whole run rather than leaving it half-created.
    Creation is ``exist_ok``, so an existing directory — and everything already
    inside it — is left exactly as it was, and a re-run is a no-op that still
    exits ``0``."""
    specs = sc.specs_dir(root)
    targets = [os.path.join(specs, name) for name in LAYOUT_DIRS]
    for path in [specs] + targets:
        if os.path.exists(path) and not os.path.isdir(path):
            raise StatusError(
                "%s exists but is not a directory — move it aside and re-run"
                % path)
    for path in targets:
        existed = os.path.isdir(path)
        os.makedirs(path, exist_ok=True)
        print("%s %s%s" % ("exists" if existed else "created",
                           os.path.relpath(path, root), os.sep))
    print("all shipd directories are ready")
    return 0


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
    """The root hosting the epic ``name`` falls back to, or ``None`` when
    ``name`` names a change or no candidate hosts such an epic — the ``status``
    epic fallback (spec-status status-cli). Resolution lives here at the CLI
    rather than in a skill so every caller (the ``shipd`` dispatcher included)
    gains it.

    Discovery goes through :func:`_epic_hosting_root`, so an epic authored
    inside a ``.worktrees/<name>`` worktree and not yet merged falls back
    exactly as a root-hosted one does. Scoped to the invocation root's own
    universe: ``status`` reports a bare status value carrying no project
    context, so — unlike ``show``'s board-shaped fallback, which resolves
    through :func:`_epic_hosting_universe` — it never reaches a declared
    project repo."""
    if _is_change(root, name):
        return None
    return _epic_hosting_root(root, name)


def _change_report_data(root, change):
    """The ``show`` report for a change as a JSON-ready dict (spec-status
    json-output): its name, the ``change`` kind discriminator, its status,
    its ``tasks`` counts (``None`` when the change carries no checklist), and
    its plan metadata. The single source both renderings below read, so the
    text and JSON forms cannot drift."""
    counts = count_tasks(root, change)
    tasks = None
    if counts is not None:
        done, in_progress, total = counts
        tasks = {"done": done, "in_progress": in_progress, "total": total}
    return {
        "name": change,
        "kind": "change",
        "status": read_status(root, change) or "?",
        "tasks": tasks,
        # Ordered pairs, never a dict: `Fixes:` is repeatable (shipd-spec-format
        # plan-header-metadata), and collapsing it would drop lines from the
        # text report. :func:`_json_ready` groups them for the JSON document.
        "metadata": _plan_metadata(root, change),
    }


def _change_report_lines(data):
    """The text ``show`` report for a change, rendered from
    :func:`_change_report_data`."""
    tasks = data["tasks"]
    if tasks is None:
        lines = ["%s: %s" % (data["name"], data["status"])]
    else:
        lines = ["%s: %s (%d/%d tasks)"
                 % (data["name"], data["status"], tasks["done"],
                    tasks["total"])]
    for key, value in data["metadata"]:
        lines.append("%s: %s" % (key, value))
    return lines


def _metadata_object(pairs):
    """Group ordered ``(key, value)`` header-metadata pairs into the JSON
    ``metadata`` object (spec-status json-output): a key appearing once maps to
    its string value, a key appearing more than once maps to the array of its
    values in file order.

    Metadata keys are not unique — ``Fixes:`` is explicitly repeatable
    (shipd-spec-format plan-header-metadata) — so the data layer keeps the
    ordered pair list the parsers yield and the text renderer prints one line
    per pair. Only this projection, on the JSON path, ever groups them, which
    is why a repeated key survives both renderings."""
    counts = {}
    for key, _value in pairs:
        counts[key] = counts.get(key, 0) + 1
    grouped = {}
    for key, value in pairs:
        if counts[key] == 1:
            grouped[key] = value
        else:
            grouped.setdefault(key, []).append(value)
    return grouped


def _json_ready(data):
    """Project one read verb's data onto its JSON document: the ordered
    ``metadata`` pair list the data layer carries becomes the grouped object
    (:func:`_metadata_object`). Every other key passes through untouched, and a
    verb whose data carries no metadata is returned as-is."""
    if "metadata" not in data:
        return data
    projected = dict(data)
    projected["metadata"] = _metadata_object(data["metadata"])
    return projected


def _emit(data, lines, as_json):
    """Render one read verb's result: the JSON document when ``as_json``, else
    the text ``lines``. The one place the two modes part company (spec-status
    json-output) — everything above it computes the same values for both."""
    if as_json:
        print(json.dumps(_json_ready(data)))
    else:
        for line in lines:
            print(line)
    return 0


def cmd_show(root, change, as_json=False):
    # No name and no selection: the board's own no-argument view is the whole
    # workspace, so report it rather than erroring (spec-status
    # workspace-board-report). Checked ahead of `_resolve_change`, which keeps
    # raising for `status`/`validate`/`set-status`/`sync`.
    if not change and read_current(root) is None:
        data = _workspace_report_data(root)
        return _emit(data, _workspace_report_lines(data), as_json)
    change = _resolve_change(root, change)
    # The epic fallback resolves across universes exactly as `epic-show` does,
    # so the two verbs keep printing byte-identical reports; `_is_change` is
    # the same guard :func:`_epic_fallback` applies for `status`.
    hosted = (None if _is_change(root, change)
              else _epic_hosting_universe(root, change))
    if hosted is not None:
        project, universe_root, _hosting_root = hosted
        data = _epic_report_data(universe_root, change, project=project)
        return _emit(data, _epic_report_lines(data), as_json)
    data = _change_report_data(root, change)
    return _emit(data, _change_report_lines(data), as_json)


def cmd_status(root, change, as_json=False):
    change = _resolve_change(root, change)
    hosting_root = _epic_fallback(root, change)
    if hosting_root is not None:
        # The status is read from the root that hosts the epic — a worktree's
        # when the epic was authored there and has not merged yet.
        kind = "epic"
        status = read_epic_status(hosting_root, change) or "?"
    else:
        kind = "change"
        status = read_status(root, change) or "?"
    return _emit({"name": change, "kind": kind, "status": status},
                 [status], as_json)


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
    # A status write into an external store auto-commits locally, scoped to the
    # rewritten plan (shipd-config store-autocommit); a no-op for an in-repo
    # plan, and a commit failure never fails the transition.
    sc.store_autocommit(root, [_plan_path(root, change)],
                        "shipd: set-status %s %s" % (change, status))
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


def cmd_locate(root, change, as_json=False):
    """Search for an installed ``change`` across the universes the engine's
    shared universe-discovery seam yields (spec-status locate-verb;
    shipd-workspace workspace-universe-discovery), in seam order — the
    invocation root's own universe first, then each declared project repo in
    slug order. Within each universe it probes that universe's resolved
    ``planned/`` first, then each ``.worktrees/<name>`` directory under it in
    sorted name order (:func:`_epic_candidate_roots`, the single-level walk
    every probe in this file shares). Where ``change`` is omitted, falls back
    to the currently selected spec via ``_resolve_change``, raising when none
    is selected. The content directory is resolved independently per candidate
    root, so a worktree may carry its own ``.shipd-config.json``. Print one
    keyed block per match — ``change:``, ``root:`` (absolute), ``dir:``
    (relative to that root), ``status:`` (``?`` when missing or invalid), and
    — for a match from a declared project universe only — ``project:`` (the
    owning project's slug) — separated by a blank line, the invocation root's
    own match first. Exit 0 on at least one match; raise (exit 1) naming the
    probed locations when none. With ``as_json``, the same rows are emitted as
    one JSON array instead, every row carrying ``project`` (slug or ``null``)
    (spec-status json-output). No git, model, or network calls."""
    change = _resolve_change(root, change)
    probed = []
    matches = []

    def _probe(project, candidate):
        probed.append(candidate)
        try:
            cdir = os.path.join(sc.specs_dir(candidate), "planned", change)
        except sc.ConfigError:
            return
        if os.path.isdir(cdir):
            matches.append((project, candidate))

    # Each universe in seam order; within one, its root first, then each of its
    # worktree directories in sorted name order.
    for project, universe_root in sc.aggregation_universes(root):
        for candidate in _epic_candidate_roots(universe_root):
            _probe(project, candidate)

    if not matches:
        raise StatusError(
            "change '%s' not found; probed: %s"
            % (change, ", ".join(probed)))

    rows = []
    for project, candidate in matches:
        cdir = os.path.join(sc.specs_dir(candidate), "planned", change)
        rows.append({
            "change": change,
            "root": os.path.abspath(candidate),
            "dir": os.path.relpath(cdir, candidate),
            "status": read_status(candidate, change) or "?",
            "project": project,
        })
    if as_json:
        print(json.dumps(rows))
        return 0
    print("\n\n".join(
        "change: %s\nroot: %s\ndir: %s\nstatus: %s%s"
        % (row["change"], row["root"], row["dir"], row["status"],
           "\nproject: %s" % row["project"] if row["project"] else "")
        for row in rows))
    return 0


# ---------------------------------------------------------------------------
# Related-artifacts search (spec-status related-verb)
# ---------------------------------------------------------------------------

# Archived change directories are ``<YYYY-MM-DD>-<slug>``; the date prefix is
# stripped from the printed slug so it feeds ``cat change <slug>`` directly
# (the same shape ``bin/shipd``'s ``ARCHIVE_DIR_RE`` matches).
ARCHIVE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")

# ``related`` prints at most this many keyed blocks, then a remainder line.
RELATED_MAX_BLOCKS = 10


def _dir_names(parent):
    """The sorted names of ``parent``'s subdirectories, or an empty list when
    it does not exist — a missing corpus directory is skipped, not an error."""
    if not os.path.isdir(parent):
        return []
    return sorted(name for name in os.listdir(parent)
                  if os.path.isdir(os.path.join(parent, name)))


def _change_artifact_files(cdir):
    """The files a change directory contributes to the search corpus: its
    ``plan.md``, its ``tasks.md``, and every delta ``specs/*/spec.md``."""
    paths = []
    for name in ("plan.md", "tasks.md"):
        path = os.path.join(cdir, name)
        if os.path.isfile(path):
            paths.append(path)
    specs_root = os.path.join(cdir, "specs")
    if os.path.isdir(specs_root):
        for capability in sorted(os.listdir(specs_root)):
            spec = os.path.join(specs_root, capability, "spec.md")
            if os.path.isfile(spec):
                paths.append(spec)
    return paths


def _related_wiki_artifacts(root):
    """The workspace wiki's ``wiki/<slug>.md`` pages as corpus records. The
    store is resolved through workspace discovery, and *any* resolution failure
    — no discoverable workspace, a malformed config, an unreadable store —
    yields no pages, so the wiki surface degrades silently while every other
    surface still searches (spec-status related-verb)."""
    try:
        pages = os.path.join(_wiki_store(root, personal=False), "wiki")
        names = sorted(os.listdir(pages))
    except (StatusError, sc.ConfigError, OSError):
        return []
    artifacts = []
    for name in names:
        path = os.path.join(pages, name)
        if name.endswith(".md") and os.path.isfile(path):
            artifacts.append(("wiki", name[:-len(".md")], path, [path]))
    return artifacts


def _related_corpus(root):
    """One ``(kind, slug, path, files)`` record per searchable artifact: the
    resolved content directory's verified capabilities, planned changes,
    completed archives (slug date-stripped), research reports, and epics, plus
    the workspace wiki's pages where one is discoverable. ``path`` identifies
    the artifact — its single file for the one-file kinds, its directory for a
    change — while ``files`` is everything the score sums over."""
    specs = sc.specs_dir(root)
    artifacts = []

    for slug in _dir_names(os.path.join(specs, "verified")):
        path = os.path.join(specs, "verified", slug, "spec.md")
        if os.path.isfile(path):
            artifacts.append(("verified", slug, path, [path]))

    for slug in _dir_names(os.path.join(specs, "planned")):
        cdir = os.path.join(specs, "planned", slug)
        files = _change_artifact_files(cdir)
        if files:
            artifacts.append(("planned", slug, cdir, files))

    completed = os.path.join(specs, "completed")
    for name in _dir_names(completed):
        cdir = os.path.join(completed, name)
        files = _change_artifact_files(cdir)
        if files:
            match = ARCHIVE_DIR_RE.match(name)
            artifacts.append(
                ("completed", match.group(1) if match else name, cdir, files))

    for slug in _dir_names(os.path.join(specs, "research")):
        path = os.path.join(specs, "research", slug, "report.md")
        if os.path.isfile(path):
            artifacts.append(("research", slug, path, [path]))

    for slug in _dir_names(os.path.join(specs, "epics")):
        path = os.path.join(specs, "epics", slug, "epic.md")
        if os.path.isfile(path):
            artifacts.append(("epic", slug, path, [path]))

    artifacts.extend(_related_wiki_artifacts(root))
    return artifacts


def _related_score(files, terms):
    """The artifact's hit count: for every term, its case-insensitive substring
    occurrences, summed over every one of the artifact's files. An unreadable
    file contributes nothing rather than raising."""
    total = 0
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read().lower()
        except OSError:
            continue
        for term in terms:
            total += text.count(term)
    return total


def _related_path(root, path):
    """An artifact's reported path: relative to ``root`` when it lives inside
    it, absolute otherwise (a wiki store hosted outside the repo)."""
    rel = os.path.relpath(path, root)
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return os.path.abspath(path)
    return rel


def cmd_related(root, terms, as_json=False):
    """Rank the spec library's artifacts by case-insensitive term-hit count
    (spec-status related-verb) — the retrieval step ``/s:fix`` runs before it
    reads any code. Artifacts with no hits are dropped; the rest sort by score
    descending, then kind, then slug, so the ordering is fully deterministic.
    At most :data:`RELATED_MAX_BLOCKS` keyed blocks print (``kind:``, ``slug:``,
    ``score:``, ``path:``), followed by a single line naming the remaining
    matches when more matched. With ``as_json``, the same capped rows are
    emitted as one JSON array instead. No match raises (exit 1). Read-only: no
    git, model, or network calls."""
    lowered = [term.lower() for term in terms]
    rows = []
    for kind, slug, path, files in _related_corpus(root):
        score = _related_score(files, lowered)
        if score:
            rows.append({"kind": kind, "slug": slug, "score": score,
                         "path": _related_path(root, path)})
    if not rows:
        raise StatusError(
            "no artifacts match %s"
            % ", ".join("'%s'" % term for term in terms))
    rows.sort(key=lambda row: (-row["score"], row["kind"], row["slug"]))
    shown = rows[:RELATED_MAX_BLOCKS]
    remaining = len(rows) - len(shown)
    if as_json:
        print(json.dumps(shown))
        return 0
    print("\n\n".join(
        "kind: %s\nslug: %s\nscore: %d\npath: %s"
        % (row["kind"], row["slug"], row["score"], row["path"])
        for row in shown))
    if remaining:
        print("… and %d more" % remaining)
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


def _epic_candidate_roots(root):
    """The candidate roots epic discovery probes, in order: ``root`` itself,
    then each ``.worktrees/<name>`` directory under it in sorted name order —
    the same single-level walk :func:`_member_state_with_root` and
    :func:`cmd_locate` use, so every probe in this file agrees on where a
    change or epic may live."""
    candidates = [root]
    worktrees_dir = os.path.join(root, ".worktrees")
    if os.path.isdir(worktrees_dir):
        for name in sorted(os.listdir(worktrees_dir)):
            wt = os.path.join(worktrees_dir, name)
            if os.path.isdir(wt):
                candidates.append(wt)
    return candidates


def _epic_hosting_root(root, slug):
    """The first candidate root whose content directory holds
    ``epics/<slug>/epic.md``, or ``None`` when no candidate does (spec-status
    epic-status-verbs; delivery-dashboard board-aggregation).

    Probes :func:`_epic_candidate_roots` in order — the invocation root first,
    then each worktree in sorted name order — resolving each candidate's
    content directory independently (``sc.specs_dir(candidate)``) and skipping
    any candidate whose configuration is unreadable (``sc.ConfigError``). The
    invocation root therefore always shadows a worktree's copy of the same
    slug, mirroring ``_member_state_with_root``'s root-first precedence.

    The shared read-side seam: the status CLI's epic surfaces and the
    dashboard's board aggregation both resolve epics through it, so the two
    can never disagree about where an epic lives."""
    for candidate in _epic_candidate_roots(root):
        try:
            specs_dir = sc.specs_dir(candidate)
        except sc.ConfigError:
            continue
        if os.path.isfile(os.path.join(specs_dir, "epics", slug, "epic.md")):
            return candidate
    return None


def _epic_hosting_universe(root, slug):
    """The universe hosting the epic ``slug``, as
    ``(project, universe_root, hosting_root)``, or ``None`` when no universe
    hosts it (spec-status epic-status-verbs; shipd-workspace
    workspace-universe-discovery).

    Probes the universes the engine's shared universe-discovery seam
    (``sc.aggregation_universes``) yields, in seam order — the invocation
    root's own universe first, then each declared project repo in slug order —
    resolving each with the existing :func:`_epic_hosting_root`, so every
    universe keeps its own root-then-worktrees precedence and the invocation
    root's universe wins a slug hosted in more than one. ``project`` is the
    owning declared project's slug (``None`` for the invocation root's own
    universe), ``universe_root`` the repo the report derives against, and
    ``hosting_root`` the candidate whose content directory holds the epic file.

    Read-only resolution: the mutating epic verbs (``epic-sync``,
    ``epic-set-status``) deliberately keep resolving the invocation root alone,
    so no verb ever writes into another project's repo."""
    for project, universe_root in sc.aggregation_universes(root):
        hosting_root = _epic_hosting_root(universe_root, slug)
        if hosting_root is not None:
            return project, universe_root, hosting_root
    return None


def all_epic_slugs_with_roots(root):
    """Every discoverable epic as ``(slug, hosting_root)`` pairs (spec-status
    epic-status-verbs; delivery-dashboard board-aggregation).

    The invocation root's own epics come first in slug order, then the epics
    hosted only under a worktree in slug order, each paired with the first
    worktree hosting it in sorted name order. A slug hosted in more than one
    candidate appears exactly once, the invocation root winning. Candidates
    whose configuration is unreadable are skipped, never raised."""
    def _slugs(candidate):
        try:
            pattern = os.path.join(
                sc.specs_dir(candidate), "epics", "*", "epic.md")
        except sc.ConfigError:
            return []
        return sorted(os.path.basename(os.path.dirname(path))
                      for path in glob.glob(pattern))

    candidates = _epic_candidate_roots(root)
    pairs = [(slug, root) for slug in _slugs(root)]
    seen = {slug for slug, _r in pairs}
    worktree_pairs = {}
    for candidate in candidates[1:]:
        for slug in _slugs(candidate):
            if slug not in seen and slug not in worktree_pairs:
                worktree_pairs[slug] = candidate
    pairs.extend((slug, worktree_pairs[slug]) for slug in sorted(worktree_pairs))
    return pairs


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


def _epic_report_data(root, slug, project=None):
    """The board-shaped epic report as a JSON-ready dict (spec-status
    epic-status-verbs, json-output) — the single computation ``epic-show`` and
    ``show``'s epic fallback both consume, in text and in JSON, so no two of
    those outputs can drift.

    Carries the epic's ``name``, the ``epic`` kind discriminator, its
    ``status`` and header ``metadata``, the hosting ``worktree`` name (``None``
    when ``root`` itself hosts it), the owning declared ``project``'s slug
    (``None`` for the invocation root's own universe), ``shipped`` counts over
    every stub member, and the four board ``lanes``, each a list of
    ``{"slug", "state", "risk", "worktree"}`` members in stub-table order. A
    member's lane comes from :func:`board_lane` — the projection the dashboard
    shares — its risk from the last rating cell of its stub-table row (``?``
    when the row carries none), and its ``worktree`` flag is set when its state
    was derived from a worktree rather than ``root``.

    ``root`` is the **owning universe's** root, which the read verbs resolve
    through :func:`_epic_hosting_universe`: the invocation root's own for a
    root-hosted epic, a declared project repo's for a project-hosted one. The
    epic's file and status are read from the root :func:`_epic_hosting_root`
    resolves within that universe — a worktree's when the epic was authored
    there and has not merged yet — while member states derive from the
    universe root itself, whose own worktree probe reaches every checkout, so
    a worktree-hosted epic reports the same board the merged one will."""
    epic_root = _epic_hosting_root(root, slug) or root
    path = _epic_path(epic_root, slug)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    _header, rows = sc.parse_epic_changes(text)
    lanes = {lane: [] for lane in _BOARD_LANES}
    total = 0
    for mslug, _desc, ratings in rows:
        state, member_root = _member_state_with_root(root, mslug)
        lanes[board_lane(state)].append({
            "slug": mslug,
            "state": state,
            "risk": (ratings[-1].strip()
                     if ratings and ratings[-1].strip() else "?"),
            "worktree": member_root != root,
        })
        total += 1
    return {
        "name": slug,
        "kind": "epic",
        "status": read_epic_status(epic_root, slug) or "?",
        # Ordered pairs for the same reason as the change path — the epic header
        # reuses the plan header grammar, so no key here may be collapsed.
        "metadata": _epic_metadata(text),
        "worktree": (os.path.basename(epic_root)
                     if epic_root != root else None),
        "project": project,
        "shipped": {"done": len(lanes["shipped"]), "total": total},
        "lanes": lanes,
    }


def _epic_report_lines(data):
    """The board-shaped epic report as a list of lines, rendered from
    :func:`_epic_report_data` (spec-status epic-status-verbs).

    In order: the ``<slug>: <status>`` line and the epic's header metadata
    lines (unchanged from before this report existed — the autopilot skill
    reads that status line); a ``worktree: <name>`` line when the epic resolved
    from a worktree of its owning universe; a ``project: <slug>`` line — after
    any ``worktree:`` line — when the epic resolved from a declared project
    universe; a ``shipped <n>/<m>`` line counting the members whose
    derived state is ``archived`` against every stub member; a blank line; then
    the four board lanes in board order, each as a ``<LANE> (<count>)`` header
    even when empty, followed by one indented row per member in it, carrying a
    ``[worktree]`` marker when its state came from a worktree."""
    lines = ["%s: %s" % (data["name"], data["status"])]
    for key, value in data["metadata"]:
        lines.append("%s: %s" % (key, value))
    if data["worktree"] is not None:
        lines.append("worktree: %s" % data["worktree"])
    if data.get("project") is not None:
        lines.append("project: %s" % data["project"])
    lines.append("shipped %d/%d"
                 % (data["shipped"]["done"], data["shipped"]["total"]))
    lines.append("")
    for lane in _BOARD_LANES:
        in_lane = data["lanes"][lane]
        lines.append("%s (%d)" % (lane.upper(), len(in_lane)))
        for member in in_lane:
            lines.append(
                "  %-22s %-12s risk %s%s"
                % (member["slug"], member["state"], member["risk"],
                   " [worktree]" if member["worktree"] else ""))
    return lines


def _workspace_epic_slugs(root):
    """Every discoverable epic as ``(slug, hosting_root)`` pairs — the epics the
    workspace report enumerates, in :func:`all_epic_slugs_with_roots` order
    (the invocation root's own first, then the worktree-only ones), so an epic
    authored inside a worktree counts exactly as the board counts it. An
    unreadable candidate configuration yields none of its epics rather than
    raising."""
    return all_epic_slugs_with_roots(root)


def _workspace_report_data(root):
    """The workspace board report as a JSON-ready dict (spec-status
    workspace-board-report, json-output) — what ``show`` reports with no name
    given and no spec selected, derived from the spec tree alone (no heartbeat
    reads).

    Carries the ``workspace`` kind discriminator; ``totals`` mirroring the
    board's filter-strip totals (``dashboard._board_totals_text``) — members
    summed across every epic (standalone changes excluded, as on the board),
    the epic count, and the distinct ``Initiative:`` slugs; ``shipped`` counts
    over every rendered row (epic members plus standalone changes); and the
    four board ``lanes``, each a list of ``{"epic", "slug", "state", "risk",
    "worktree", "project"}`` rows. A row's ``epic`` is its epic's slug, or
    ``standalone`` for a change planned outside any epic; its risk is the
    stub-table row's last rating cell (``?`` when absent — always ``?`` for a
    standalone change, which has no stub row); its ``worktree`` flag is set
    when the state came from a worktree of its own universe; and its
    ``project`` is the declared project owning that universe (``None`` for the
    invocation root's own).

    The report aggregates one **universe** per repo: the invocation root's own
    always, plus — for a workspace-level invocation — each declared project
    repo the engine's shared universe-discovery seam
    (:func:`spec_common.aggregation_universes`, shipd-workspace
    workspace-universe-discovery) yields, aggregated exactly as a root is (its
    epics, its worktrees, its member states, its standalone changes, all
    relative to that repo). Member-slug exclusion sets are per universe, so
    one project's epic never suppresses another's standalone change, and epic
    slugs are never deduplicated across universes — separate repos are separate
    spec universes, told apart by their ``project``. Totals sum across
    universes; ``initiatives`` counts distinct slugs across them.

    Rows are collected epic by epic in epic order and the standalone changes
    last — all universes' epic rows first (the invocation root's, then each
    project's in slug order), then all universes' standalone rows in the same
    order — a grouping the text renderer's ``SHIPPED`` rollups rely on. Lanes
    come from :func:`board_lane`, the shared projection the epic report and the
    dashboard use, and standalone changes from :func:`standalone_changes`, the
    discovery the board consumes. The epics themselves come from
    :func:`_workspace_epic_slugs`, the worktree-aware seam the board's
    aggregation shares, each read from its hosting root, so a worktree-authored
    epic counts here exactly as it does on the board. An unreadable epic file is
    skipped, never raised."""
    universes = sc.aggregation_universes(root)
    epic_count = 0
    initiatives = set()
    specs = 0
    epic_rows = []
    standalone_rows = []
    for project, universe_root in universes:
        member_slugs = set()
        for eslug, epic_root in _workspace_epic_slugs(universe_root):
            try:
                with open(_epic_path(epic_root, eslug), encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, sc.ConfigError):
                continue
            meta = dict(_epic_metadata(text))
            if meta.get("Initiative"):
                initiatives.add(meta["Initiative"])
            _header, stub_rows = sc.parse_epic_changes(text)
            for mslug, _desc, ratings in stub_rows:
                member_slugs.add(mslug)
                state, hosting_root = _member_state_with_root(
                    universe_root, mslug)
                epic_rows.append({
                    "epic": eslug,
                    "slug": mslug,
                    "state": state,
                    "risk": (ratings[-1].strip()
                             if ratings and ratings[-1].strip() else "?"),
                    "worktree": hosting_root != universe_root,
                    "project": project,
                })
                specs += 1
            epic_count += 1

        # Changes planned outside any epic fold in under the epic column
        # `standalone`; their hosting location, not a stub table, marks a
        # worktree — of their own universe, not of the invocation root.
        universe_abs = os.path.abspath(universe_root)
        for entry in standalone_changes(universe_root, member_slugs):
            standalone_rows.append({
                "epic": "standalone",
                "slug": entry["slug"],
                "state": entry["state"],
                "risk": entry.get("risk") or "?",
                "worktree": entry.get("location") != universe_abs,
                "project": project,
            })

    all_rows = epic_rows + standalone_rows
    lanes = {lane: [] for lane in _BOARD_LANES}
    for row in all_rows:
        lanes[board_lane(row["state"])].append(row)
    return {
        "kind": "workspace",
        "totals": {"specs": specs, "epics": epic_count,
                   "initiatives": len(initiatives)},
        "shipped": {"done": len(lanes["shipped"]), "total": len(all_rows)},
        "lanes": lanes,
    }


def _project_marker(project):
    """The `` [<project>]`` display marker for a workspace-report row's owning
    project — the empty string for the invocation root's own rows (``None``),
    so a single-universe board renders exactly as it always has."""
    return " [%s]" % project if project else ""


def _workspace_report_lines(data):
    """The workspace board report as a list of lines, rendered from
    :func:`_workspace_report_data` (spec-status workspace-board-report).

    In order: a ``N specs · N epics · N initiatives`` totals line; a
    ``shipped <n>/<m>`` line; a blank line; then the four board lanes in board
    order, each as a ``<LANE> (<count>)`` header even when empty.

    A non-shipped lane prints one indented row per entry carrying its epic
    column, the member slug, its derived state, its risk, a ``[worktree]``
    marker when the state came from a worktree, and — for a row aggregated from
    a declared project's repo — a ``[<project>]`` marker after it. ``SHIPPED``
    instead prints rollup rows counted per epic *per owning project* —
    ``<epic-slug> (<n>)`` for the invocation root's own rows,
    ``<epic-slug> [<project>] (<n>)`` for a project's — in row order, plus
    ``standalone (<n>)`` last within each universe's grouping when any
    standalone change is archived, mirroring the board's collapsed per-epic
    shipped groups. The rollups read straight off the shipped rows, whose
    epic-then-standalone grouping the data preserves.

    With no project universes every row carries ``project`` ``None``, no marker
    prints, and the rendering is byte-identical to the single-universe board."""
    totals = data["totals"]
    lines = ["%d specs · %d epics · %d initiatives"
             % (totals["specs"], totals["epics"], totals["initiatives"]),
             "shipped %d/%d"
             % (data["shipped"]["done"], data["shipped"]["total"]),
             ""]
    for lane in _BOARD_LANES:
        in_lane = data["lanes"][lane]
        lines.append("%s (%d)" % (lane.upper(), len(in_lane)))
        if lane == "shipped":
            # (epic column, owning project) -> shipped row count, in order: a
            # slug hosted by two projects rolls up once per project.
            counts = {}
            for row in in_lane:
                key = (row["epic"], row.get("project"))
                counts[key] = counts.get(key, 0) + 1
            for (ecol, project), count in counts.items():
                lines.append("  %s%s (%d)"
                             % (ecol, _project_marker(project), count))
            continue
        for row in in_lane:
            lines.append(
                "  %-20s %-22s %-12s risk %s%s%s"
                % (row["epic"], row["slug"], row["state"], row["risk"],
                   " [worktree]" if row["worktree"] else "",
                   _project_marker(row.get("project"))))
    return lines


def cmd_epic_show(root, slug, as_json=False):
    # Read-only, so it resolves across every universe the shared seam yields —
    # the invocation root and its worktrees, then each declared project repo;
    # the mutating verbs below deliberately stay invocation-root-only.
    hosted = _epic_hosting_universe(root, slug)
    if hosted is None:
        raise StatusError(
            "epic '%s' not found (%s)" % (slug, _epic_path(root, slug)))
    project, universe_root, _hosting_root = hosted
    data = _epic_report_data(universe_root, slug, project=project)
    return _emit(data, _epic_report_lines(data), as_json)


# --- the epic's per-tool token breakdown (spec-status epic-token-breakdown) --
#
# Each built change persists a trailing ``## Token usage breakdown`` section in
# its ``tasks.md`` before the merge archives it; ``epic-sync`` sums its members'
# archived tables into the same section at the bottom of ``epic.md``. The
# grammar is exactly what ``build_report.render_tool_table`` writes, so the
# rendering (and its number formatting) is reused rather than re-invented.

_TOKEN_ROW_RE = re.compile(
    r"^\|\s*(?P<tool>.+?)\s*\|\s*(?P<calls>\d[\d,]*)\s*\|"
    r"\s*(?P<output>[\d,]+(?:\.\d+)?\s*[kMB]?)\s*\|\s*$")

_TOKEN_SUFFIXES = {"k": 1_000, "M": 1_000_000, "B": 1_000_000_000}


def _parse_token_count(text):
    """Invert ``build_report.human``: ``'962'`` -> 962, ``'5.6k'`` -> 5600.

    Returns ``None`` when the cell is not a number the writer could have
    produced, so an unparseable row disqualifies its whole table."""
    cell = text.strip().replace(",", "")
    if not cell:
        return None
    multiplier = 1
    if cell[-1] in _TOKEN_SUFFIXES:
        multiplier = _TOKEN_SUFFIXES[cell[-1]]
        cell = cell[:-1]
    try:
        value = float(cell)
    except ValueError:
        return None
    return int(round(value * multiplier))


def _trailing_tool_table_start(text):
    """The offset at which ``text``'s **trailing** ``## Token usage breakdown``
    section begins, or ``None`` when it has none.

    Deliberately conservative: a heading match counts only when everything from
    it to EOF is the breakdown block itself — blank lines and table lines
    (starting with ``|``) and nothing else. A document that merely *mentions*
    the heading mid-prose, with real sections after it, therefore reports no
    trailing section, so the rewrite below can never swallow content it did not
    write. Only the last occurrence is tested: an earlier one's tail would
    contain the later heading, which is not a table line."""
    heading = build_report.TOOL_TABLE_HEADING
    if text.startswith(heading):
        index = 0
    else:
        found = text.rfind("\n" + heading)
        if found < 0:
            return None
        index = found + 1
    # The heading must be a whole line of its own, not a prefix of a longer one.
    line_end = text.find("\n", index)
    first = text[index:] if line_end < 0 else text[index:line_end]
    if first.strip() != heading:
        return None
    tail = "" if line_end < 0 else text[line_end + 1:]
    for line in tail.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("|"):
            return None
    return index


def _parse_tool_table(text):
    """Parse the trailing ``## Token usage breakdown`` table out of a change's
    ``tasks.md`` body into ``{tool: {"calls": int, "output": int}}``.

    Returns ``{}`` when the section is absent, and ``None`` when it is present
    but unparseable — a hand-edited table contributes nothing rather than
    failing the sync. The bold ``**Total**`` row is a rendered aggregate, not an
    input, so it is skipped."""
    start = _trailing_tool_table_start(text)
    if start is None:
        return {}
    section = text[start:]
    by_tool = {}
    seen_header = False
    # The locator guarantees every remaining line is blank or a table line.
    for line in section.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        if not seen_header:
            # The column header and its separator, in that order.
            if line.startswith("| Tool "):
                seen_header = True
                continue
            return None
        if set(line) <= set("| -:"):
            continue                    # the header separator row
        match = _TOKEN_ROW_RE.match(line)
        if match is None:
            return None
        tool = match.group("tool")
        if tool.startswith("**"):
            continue                    # the rendered **Total** row
        output = _parse_token_count(match.group("output"))
        if output is None:
            return None
        row = by_tool.setdefault(tool, {"calls": 0, "output": 0})
        row["calls"] += int(match.group("calls").replace(",", ""))
        row["output"] += output
    if not seen_header:
        return None
    return by_tool


def _member_tool_table(root, slug):
    """The per-tool breakdown a member contributes: its archived change's
    ``tasks.md`` table, or ``{}`` when the member is not archived, carries no
    table, or its table cannot be parsed.

    The member is resolved exactly the way :func:`_member_state_with_root`
    resolves its state, so the archive read follows the same root-first,
    then-each-worktree precedence the status derivation uses."""
    state, hosting_root = _member_state_with_root(root, slug)
    if state != "archived":
        return {}
    try:
        specs_dir = sc.specs_dir(hosting_root)
    except sc.ConfigError:
        return {}
    for path in sorted(glob.glob(
            os.path.join(specs_dir, "completed", "*-" + slug))):
        tasks = os.path.join(path, "tasks.md")
        try:
            with open(tasks, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        return _parse_tool_table(text) or {}
    return {}


def _epic_tool_table(root, slug):
    """Sum every member's archived per-tool table into one
    ``{tool: {"calls": int, "output": int}}`` map for the epic."""
    totals = {}
    for mslug, _desc, _ratings in _epic_rows(root, slug):
        for tool, row in _member_tool_table(root, mslug).items():
            entry = totals.setdefault(tool, {"calls": 0, "output": 0})
            entry["calls"] += row["calls"]
            entry["output"] += row["output"]
    return totals


def _apply_tool_table(text, by_tool):
    """Return ``text`` with its trailing ``## Token usage breakdown`` section
    replaced by the one rendered from ``by_tool`` — or removed entirely when
    ``by_tool`` is empty. Every other byte of the epic file is preserved, so a
    re-run over unchanged members is byte-identical.

    The section to replace comes from :func:`_trailing_tool_table_start`, which
    only ever matches a verified trailing table block — so a heading that merely
    appears inside the epic's prose is left alone and the generated section is
    appended after it, never eating the sections that follow."""
    start = _trailing_tool_table_start(text)
    section = build_report.render_tool_table(by_tool)
    if start is None and not section:
        return text  # nothing to add or remove: a pure no-op stays a no-op
    body = (text if start is None else text[:start]).rstrip("\n")
    if not section:
        return body + "\n"
    return body + "\n\n" + section + "\n"


def _sync_epic_tool_table(root, slug):
    """Rewrite the epic file's trailing breakdown section from its members'
    archived tables. Best-effort: any failure leaves the file untouched, so a
    hand-edited member table never fails the status derivation."""
    path = _epic_path(root, slug)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        updated = _apply_tool_table(text, _epic_tool_table(root, slug))
    except (OSError, sc.ConfigError):
        return
    if updated == text:
        return
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(updated)


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
    # Then the members' persisted per-tool token tables, summed into the epic's
    # own trailing section (epic-token-breakdown). Idempotent, and skipped
    # entirely for a draft epic by the guard above.
    _sync_epic_tool_table(root, slug)
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
    none-note). When the resolved configuration declares ``store_root``,
    additionally prints a ``store:`` line carrying the resolved absolute
    external content directory, so a mis-declared store is inspectable at a
    glance (shipd-config store-root-key). When the resolved workspace chain
    carries more than one member, additionally prints a ``chain:`` line listing
    the whole chain, nearest first (shipd-workspace
    workspace-chain-facilities). Does not require a workspace; exits zero on a
    default-only resolution (spec-status config-show-verb)."""
    try:
        config, provenance = sc.resolve_config(root)
        content_dir = sc.specs_dirname(config)
        # `specs_dir` is the resolution funnel, so the printed path is the very
        # one every verb writes to — never a re-derivation that could drift.
        store_content = (sc.specs_dir(root)
                         if sc.store_root_dir(root) is not None else None)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    print("config (resolved from %s):" % os.path.abspath(root))
    for key in sorted(config):
        src = provenance.get(key, "default")
        print("  %s = %s  [%s]" % (key, json.dumps(config[key]), src))
    print("content-dir: %s" % content_dir)
    if store_content is not None:
        print("store: %s" % store_content)
    chain = sc.workspace_chain(root)
    if not chain:
        print("workspace: none discoverable")
    else:
        print("workspace: %s" % chain[0])
        if len(chain) > 1:
            print("chain: %s" % ", ".join(chain))
    return 0


# The declared per-stage option fields rendered after a pipeline entry's form
# label, in this order (spec-status pipeline-show-verb). `autopilot` is an
# object and renders as `autopilot.<key>=<value>` per declared sub-key.
_PIPELINE_OPTION_KEYS = ("model", "subagent_model", "validator", "telemetry",
                         "parallelism", "disposition")


def _render_option(value):
    """Render one option value: booleans as JSON-style ``true``/``false``, so
    the printed pair reads back as the config value it came from."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _pipeline_options_suffix(entry):
    """Render an entry's declared per-stage options as ``key=value`` pairs
    joined with ``", "``, empty when the entry declares none — so an entry
    without options renders exactly as it did before options existed."""
    pairs = []
    for key in _PIPELINE_OPTION_KEYS:
        if key in entry:
            pairs.append("%s=%s" % (key, _render_option(entry[key])))
    for key, value in (entry.get("autopilot") or {}).items():
        pairs.append("autopilot.%s=%s" % (key, _render_option(value)))
    return ", ".join(pairs)


def _format_pipeline_entry(entry):
    """Render one resolved pipeline entry as a single human-readable line
    stating its form, any bindings with their fallbacks, and any declared
    per-stage options (spec-status pipeline-show-verb)."""
    if "custom" in entry:
        label = "custom '%s'  command: %s" % (
            entry.get("custom"), entry.get("command"))
    else:
        stage = entry.get("stage")
        if entry.get("skip") is True:
            label = "%s  (skipped)" % stage
        elif "tools" in entry:
            bindings = ", ".join(
                "%s (fallback=%s)" % (t.get("name"), t.get("fallback"))
                for t in entry["tools"])
            label = "%s  tools: %s" % (stage, bindings)
        elif "replace" in entry:
            rep = entry["replace"]
            kind = "command" if rep.get("command") else "tool"
            label = "%s  replaced by %s '%s' (fallback=%s)" % (
                stage, kind, rep.get(kind), rep.get("fallback"))
        else:
            label = stage
    options = _pipeline_options_suffix(entry)
    return "%s  %s" % (label, options) if options else label


def _expand_pipeline_preset(name):
    """Return the named preset's entry list — the exact value a config may
    declare as its own `autonomous-pipeline` list (spec-status
    pipeline-show-verb).

    An unknown name is a :class:`StatusError` listing the known presets, raised
    before any import; ``default`` expands from the stdlib stage registry, so it
    needs no third-party package. Every other known name expands through
    ``pipeline_schema``, imported lazily here — the module is stdlib-only, so
    expanding it never depends on a third-party package either."""
    if name not in sc.PIPELINE_PRESETS:
        raise StatusError(
            "unknown pipeline preset '%s'; known presets: %s"
            % (name, ", ".join(sorted(sc.PIPELINE_PRESETS))))
    if name == "default":
        return [{"stage": stage} for stage in sc.PIPELINE_STAGES]
    import pipeline_schema
    try:
        return pipeline_schema.expand_preset(name)
    except ValueError as exc:
        raise StatusError(str(exc))


def cmd_pipeline_show(root, expand=None, as_json=False):
    """Print the effective autonomous pipeline: one line per resolved entry
    (form + bindings with fallbacks + declared per-stage options) plus the
    provenance of the ``autonomous-pipeline`` key — the supplying config file
    path, ``preset:<name>`` with that path for a preset-resolved pipeline, or
    ``[default]`` when no layer declares it (spec-status pipeline-show-verb).
    Requires no workspace and no selected change; a defaults-only resolution
    exits zero. A pipeline that fails validation raises, printing every
    validation error and exiting non-zero.

    With ``expand`` naming a preset, no config is resolved at all: the preset's
    entry list prints as indented JSON — the value to paste as the key to fork
    it into a custom list — and the verb exits zero.

    With ``as_json`` the resolution prints as the machine contract instead of
    the text report: one JSON object holding the raw provenance under ``source``
    (``default`` undecorated) and the resolved entries — the validated dicts,
    carrying exactly the keys each entry declared — under ``entries``. Combined
    with ``expand`` it changes nothing: expand's output already is the one JSON
    document the flag would ask for. Errors raise identically either way."""
    if expand is not None:
        print(json.dumps(_expand_pipeline_preset(expand), indent=2))
        return 0
    try:
        entries, provenance = sc.resolve_pipeline(root)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    if as_json:
        print(json.dumps({"source": provenance, "entries": entries}, indent=2))
        return 0
    source = "[default]" if provenance == "default" else provenance
    print("pipeline (source: %s):" % source)
    for i, entry in enumerate(entries, 1):
        print("  %d. %s" % (i, _format_pipeline_entry(entry)))
    return 0


def _cat_files(root, paths, provenance=None):
    """Print each path in ``paths`` preceded by a ``--- <relpath>`` separator
    line (relpath relative to ``root``), resolving nothing itself — callers pass
    the engine-resolved locations (spec-io mediated-read-verb).

    ``provenance``, when given, maps a path to the workspace root of the
    inherited chain store that supplied it; that path's separator line carries
    a trailing ``(inherited <ws-root>)`` annotation naming it, so a reader
    never has to derive provenance by comparing a root-relative separator
    against an absolute store path (shipd-wiki wiki-status-verbs). A path
    absent from ``provenance``, or ``provenance`` left ``None``, gets an
    unannotated separator — this is how the nearest store's own files, and
    every non-wiki ``cat`` kind, are printed."""
    for path in paths:
        rel = os.path.relpath(path, root)
        ws_root = provenance.get(path) if provenance else None
        if ws_root:
            print("--- %s  (inherited %s)" % (rel, ws_root))
        else:
            print("--- %s" % rel)
        with open(path, encoding="utf-8") as fh:
            sys.stdout.write(fh.read())


def _cat_artefacts_listing(root, cdir):
    """Print a change's ``artefacts/`` tree as a listing, never its content
    (spec-io mediated-read-verb): a ``--- artefacts`` header followed by one
    sorted line per file giving its path relative to ``root`` and its size in
    bytes. A change carrying no such directory, or one holding no files,
    prints nothing. An entry whose size cannot be read (a dangling symlink,
    an unreadable file) is skipped rather than raised: a mediated read is a
    listing aid and must never fail on a change that lints clean."""
    adir = os.path.join(cdir, "artefacts")
    if not os.path.isdir(adir):
        return
    entries = []
    for dirpath, _dirnames, filenames in os.walk(adir):
        for name in filenames:
            entries.append(os.path.join(dirpath, name))
    if not entries:
        return
    lines = []
    for path in sorted(entries):
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        lines.append("%s (%d bytes)" % (os.path.relpath(path, root), size))
    if not lines:
        return
    print("--- artefacts")
    for line in lines:
        print(line)


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
        _cat_artefacts_listing(root, cdir)
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
        # Resolves to the nearest workspace-chain member holding the brief
        # (shipd-workspace workspace-chain-facilities), not the nearest
        # workspace root alone.
        path = sc.resolve_initiative_brief(root, slug)
        if path is None:
            expected = sc.initiative_brief_path(ws_root, slug)
            raise StatusError(
                "initiative '%s' not found (%s)" % (slug, expected))
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
        # Personal is a fixed single store, bypassing the chain entirely. The
        # workspace store resolves across the chain (shipd-wiki
        # wiki-store-layout): `index`/`queue` aggregate every chain store's
        # file nearest first; `log`/`schema` and a page slug resolve to the
        # nearest chain store that holds one, a member holding no store
        # skipped silently. `stores` is never empty for the workspace case —
        # `_resolve_workspace` already raises when no chain exists at all.
        if personal:
            stores = [_wiki_store(root, personal)]
            store_roots = [None]
            nearest_root = None
        else:
            ws_root = _resolve_workspace(root)
            chain_roots = sc.workspace_chain(root)
            nearest_root = chain_roots[0] if chain_roots else ws_root
            existing = [(r, sc.wiki_dir(r)) for r in chain_roots
                        if os.path.isdir(sc.wiki_dir(r))]
            if existing:
                store_roots, stores = (list(t) for t in zip(*existing))
            else:
                stores = [sc.wiki_dir(ws_root)]
                store_roots = [ws_root]
        # "Nearest" is the chain's own nearest member, not merely the nearest
        # store that happens to exist on disk — a file resolved from any
        # other chain member is inherited and gets its root as an annotation,
        # so a reader copies it verbatim rather than deriving it (shipd-wiki
        # wiki-status-verbs).
        provenance = {}
        if slug in ("index", "queue"):
            paths = []
            for s, r in zip(stores, store_roots):
                p = os.path.join(s, slug + ".md")
                if os.path.isfile(p):
                    paths.append(p)
                    if r != nearest_root:
                        provenance[p] = r
        elif slug in ("log", "schema"):
            path = os.path.join(stores[0], slug + ".md")
            paths = [path] if os.path.isfile(path) else []
            if paths and store_roots[0] != nearest_root:
                provenance[path] = store_roots[0]
        else:
            paths = []
            for s, r in zip(stores, store_roots):
                path = os.path.join(s, "wiki", slug + ".md")
                if os.path.isfile(path):
                    paths = [path]
                    if r != nearest_root:
                        provenance[path] = r
                    break
        if not paths:
            near = sc.wiki_dir(nearest_root) if nearest_root else stores[0]
            if slug in ("index", "log", "queue", "schema"):
                rep = os.path.join(near, slug + ".md")
            else:
                rep = os.path.join(near, "wiki", slug + ".md")
            raise StatusError("wiki page '%s' not found (%s)" % (slug, rep))
        _cat_files(root, paths, provenance)
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


def _repo_entry_data(ws_root, repo):
    """One repo registry entry as a JSON-ready dict — its ``path``, whether it
    is ``present`` (a directory on this machine; absence is never an error),
    and its declared clone ``url`` (``None`` when it declares none) — or
    ``None`` when the entry declares no path at all. Paths are read uniformly
    from string and object entry shapes via ``repo_entry_path``."""
    path = sc.repo_entry_path(repo)
    if path is None:
        return None
    url = repo.get("url") if isinstance(repo, dict) else None
    return {
        "path": path,
        "present": os.path.isdir(os.path.join(ws_root, path)),
        "url": url if url else None,
    }


def _repo_display(entry):
    """Annotate a :func:`_repo_entry_data` record for display: ``(absent)``
    when its path is not a directory on this machine, and ``[url]`` when the
    entry carries a clone URL (both display-only)."""
    text = entry["path"] if entry["present"] \
        else "%s (absent)" % entry["path"]
    if entry["url"]:
        text = "%s [url]" % text
    return text


def _project_repo_entries(ws_root, entry):
    """Yield the :func:`_repo_entry_data` records of one project registry
    entry, skipping malformed entries defensively."""
    repos = entry.get("repos") if isinstance(entry, dict) else None
    if not isinstance(repos, list):
        return
    for repo in repos:
        record = _repo_entry_data(ws_root, repo)
        if record is not None:
            yield record


def _project_repo_lines(ws_root, entry):
    """Yield the annotated repo display lines of one project registry entry."""
    for record in _project_repo_entries(ws_root, entry):
        yield _repo_display(record)


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


def _workspace_show_data(root):
    """The ``workspace-show`` report as a JSON-ready dict (spec-status
    workspace-status-verbs, json-output): the resolved ``workspace`` root, the
    declared ``focus`` project (``None`` when undeclared), each declared
    ``project`` in slug order with its repo records and ``context`` presence,
    each ``initiative`` in slug order with its status and ``Project:`` scope,
    and whether this repository falls under the implicit default project. The
    registry (projects, focus, repos, context) resolves from the workspace
    chain's ``registry_root`` — the nearest chain member declaring ``projects``,
    falling back to the workspace root when none does (shipd-workspace
    workspace-chain-facilities) — and ``registry`` names that root's own path
    when it differs from the workspace root, so the provenance is inspectable.
    An unloadable registry displays as an empty one — validation lives in the
    linter (``--workspace``)."""
    ws_root = _resolve_workspace(root)
    reg_root = sc.registry_root(root) or ws_root
    try:
        registry = sc.load_workspace(reg_root)
    except sc.ConfigError:
        registry = {}
    focus = registry.get("focus")
    projects = _load_projects(reg_root)
    return {
        "workspace": ws_root,
        "registry": reg_root if reg_root != ws_root else None,
        "focus": focus if isinstance(focus, str) and focus else None,
        "projects": [
            {"slug": slug,
             "repos": list(_project_repo_entries(reg_root, projects[slug])),
             "context": os.path.isfile(_context_path(reg_root, slug))}
            for slug in sorted(projects)],
        "initiatives": [
            {"slug": slug, "status": status, "project": project}
            for slug, status, project in _iter_initiatives(ws_root)],
        "implicit_default_project": sc.project_of(reg_root, root) is None,
    }


def _workspace_show_lines(data):
    """The ``workspace-show`` text report, rendered from
    :func:`_workspace_show_data`."""
    lines = ["workspace: %s" % data["workspace"]]
    if data["registry"]:
        lines.append("registry: %s" % data["registry"])
    if data["focus"]:
        lines.append("focus: %s" % data["focus"])
    for project in data["projects"]:
        lines.append("project %s:" % project["slug"])
        for repo in project["repos"]:
            lines.append("  repo: %s" % _repo_display(repo))
        lines.append("  context: %s" % ("yes" if project["context"] else "no"))
    if data["initiatives"]:
        lines.append("initiatives:")
        for initiative in data["initiatives"]:
            scope = ("Project: %s" % initiative["project"]
                     if initiative["project"] else "unscoped")
            lines.append("  %s: %s (%s)"
                         % (initiative["slug"], initiative["status"], scope))
    if data["implicit_default_project"]:
        lines.append(
            "(this repository falls under the implicit default project)")
    return lines


def cmd_workspace_show(root, as_json=False):
    data = _workspace_show_data(root)
    return _emit(data, _workspace_show_lines(data), as_json)


def cmd_workspace_init(path, git=False, nested=False):
    """Initialize a workspace at ``path`` through the engine and print the
    created root (spec-status workspace-init-verb). Unlike the other workspace
    verbs, this does NOT resolve a workspace from ``--root`` — it runs precisely
    when none is discoverable. When ``git`` is set, requests the engine's git
    option (git-init when the target is not already inside a work tree, plus the
    seeded member-repos ``.gitignore`` block). When ``nested`` is set, requests
    the engine's nested option, permitting creation beneath an enclosing
    workspace and additionally printing the enclosing root it nests under. A
    refusal or error (an existing workspace already discoverable from the
    target without ``nested``, a target that itself already declares
    ``workspace``, or a missing target directory) surfaces as a
    :class:`StatusError`, exiting non-zero."""
    try:
        result = sc.init_workspace(path, git=git, nested=nested)
    except sc.ConfigError as exc:
        raise StatusError(str(exc))
    if nested:
        created, enclosing = result
        print(created)
        if enclosing is not None:
            print(enclosing)
    else:
        print(result)
    return 0


def cmd_project_show(root, slug):
    """Print one declared project's repos, context presence, and scoped
    initiatives (spec-status workspace-status-verbs). The registry resolves
    from the workspace chain's ``registry_root`` (shipd-workspace
    workspace-chain-facilities) exactly as ``workspace-show`` does, so a
    project declared only in an enclosing workspace still resolves here."""
    ws_root = _resolve_workspace(root)
    reg_root = sc.registry_root(root) or ws_root
    projects = _load_projects(reg_root)
    if slug not in projects:
        declared = ", ".join(sorted(projects)) or "(none)"
        raise StatusError(
            "unknown project '%s' (declared slugs: %s)" % (slug, declared))
    print("project %s:" % slug)
    for line in _project_repo_lines(reg_root, projects[slug]):
        print("  repo: %s" % line)
    ctx_path = _context_path(reg_root, slug)
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


def _scaffold_wiki_store(wiki):
    """Seed the wiki store layout at ``wiki`` (spec-status wiki-status-verbs):
    ``schema.md`` with the grammar conventions, an empty ``index.md`` and
    ``queue.md``, a first dated ``log.md`` entry, and empty ``sources/`` and
    ``wiki/`` directories. Shared by ``wiki-init`` and every write verb that
    scaffolds the nearest workspace's store on demand (``wiki-queue-add``,
    ``wiki-queue-answer``, ``wiki-queue-discard``) rather than erroring when it
    does not yet exist."""
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
    _scaffold_wiki_store(wiki)
    print(wiki)
    return 0


def cmd_wiki_show(root, personal=False):
    """Print the wiki store's health (spec-status wiki-status-verbs): the store
    root, a ``chain:`` line naming the inherited chain stores that exist
    (nearest first, or ``chain: none``), a ``base:`` line reporting the
    resolved ``wiki_base`` store, the page count, index-coverage health, the
    pending-question count, and the last log entry. Resolves the workspace
    store by default, or the personal memory store under ``personal``. Under
    ``personal`` the store participates in no chain or base layering, so
    ``chain:`` and ``base:`` are always ``none``, and it errors when that
    store does not exist. For the workspace store, the nearest workspace's
    store may be absent while an enclosing chain member's is not: in that case
    the nearest store is reported absent rather than erroring, and the verb
    errors only when no chain member holds a store at all."""
    wiki = _wiki_store(root, personal)
    chain_stores = [] if personal else sc.resolve_wiki_stores(root)
    if not os.path.isdir(wiki):
        if personal or not chain_stores:
            raise StatusError("no wiki store at %s (run `wiki-init`)" % wiki)
        print("wiki: %s (absent)" % wiki)
    else:
        print("wiki: %s" % wiki)

    # The chain's remaining (inherited) stores, nearest first — every chain
    # store that is not this store itself (shipd-wiki wiki-store-layout). A
    # personal store participates in no chain, so it always reports
    # `chain: none`.
    if personal:
        print("chain: none")
    else:
        inherited = [s for s in chain_stores
                     if os.path.realpath(s) != os.path.realpath(wiki)]
        print("chain: %s" % (", ".join(inherited) if inherited else "none"))

    # The layered `wiki_base` store, if declared (shipd-config wiki-base-key). A
    # malformed value surfaces as a ConfigError → the verb's error exit.
    # `wiki_base_dir` itself treats a base resolving to any workspace-chain
    # member's store directory as undeclared, so running inside the base
    # workspace itself (or an enclosing one) never double-layers. The personal
    # store participates in no base layering, so it always reports `base: none`.
    if personal:
        print("base: none")
    else:
        base = sc.wiki_base_dir(_resolve_workspace(root))
        if base is None:
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
    wiki-status-verbs, shipd-wiki wiki-question-queue, wiki-store-layout).
    Builds a ``## q-<slug>`` block carrying the given
    ``--question``/``--options``/``--recommendation``, an
    ``Asked: <today> [origin]`` line, and ``Answer: pending``; appends it to
    ``queue.md`` and re-validates the resulting queue with the spec_common
    parser. A duplicate slug or an invalid result restores the prior
    ``queue.md`` and exits non-zero. Every write targets the *nearest*
    workspace's store alone — never an inherited chain member's — scaffolding
    that store's layout on demand when it does not yet exist, rather than
    erroring."""
    if not sc.KEBAB_RE.match(slug):
        raise StatusError("queue slug '%s' is not a kebab-case slug" % slug)
    ws_root = _resolve_workspace(root)
    wiki = sc.wiki_dir(ws_root)
    queue_path = os.path.join(wiki, "queue.md")
    if not os.path.isfile(queue_path):
        _scaffold_wiki_store(wiki)
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


def cmd_wiki_queue_answer(root, slug, answer, advisory=False):
    """Write a user's answer into a still-pending queue block (shipd-wiki
    wiki-queue-answer-verb, wiki-store-layout). Resolves the workspace store
    exactly as ``wiki-queue-add`` does — scaffolding the nearest workspace's
    store on demand when it does not yet exist, rather than erroring — accepts
    the bare slug (prefixing ``q-`` itself), and replaces the ``## q-<slug>``
    block's ``- Answer: pending`` line with ``- Answer: <answer>``, printing
    the block id. Under ``advisory`` the answer is stored with an
    ``advisory: `` prefix — ``- Answer: advisory: <answer>`` — marking the
    captured knowledge as a recommendation the oracle relays rather than a
    binding position; without the flag it is stored unprefixed. A missing
    block, or a block whose answer is no longer ``pending``, writes nothing and
    exits non-zero — an answered block belongs to the `/s:teach` drain and is
    never overwritten."""
    if not sc.KEBAB_RE.match(slug):
        raise StatusError("queue slug '%s' is not a kebab-case slug" % slug)
    answer = answer.strip()
    if not answer:
        raise StatusError("--answer must not be empty")
    if advisory:
        answer = "advisory: %s" % answer
    ws_root = _resolve_workspace(root)
    wiki = sc.wiki_dir(ws_root)
    queue_path = os.path.join(wiki, "queue.md")
    if not os.path.isfile(queue_path):
        _scaffold_wiki_store(wiki)
    with open(queue_path, encoding="utf-8") as fh:
        before = fh.read()

    qid = "q-%s" % slug
    fields = dict(sc.parse_queue_blocks(before)).get(qid)
    if fields is None:
        raise StatusError("queue has no block '%s'" % qid)
    if fields.get("Answer", "").strip() != "pending":
        raise StatusError(
            "block '%s' is already answered ('%s'); correcting an answer is "
            "`/s:teach`'s job" % (qid, fields.get("Answer", "")))

    # Rewrite only the target block's Answer line; every other line — including
    # other blocks' `- Answer: pending` — is preserved verbatim.
    lines = before.splitlines(keepends=True)
    in_block = False
    written = False
    for i, line in enumerate(lines):
        header = sc.WIKI_QUEUE_HEADER_RE.match(line.rstrip("\n"))
        if header:
            in_block = header.group(1) == qid
            continue
        if line.startswith("## "):
            in_block = False
            continue
        if not in_block:
            continue
        fm = sc.WIKI_QUEUE_FIELD_RE.match(line.rstrip("\n"))
        if fm and fm.group(1) == "Answer":
            newline = "\n" if line.endswith("\n") else ""
            lines[i] = "- Answer: %s%s" % (answer, newline)
            written = True
            break
    if not written:  # defensive: the parser found the field, so this is a bug
        raise StatusError("block '%s' has no `- Answer:` line" % qid)
    new_text = "".join(lines)

    _write_text(queue_path, new_text)
    errors = _validate_queue_text(new_text)
    if errors:
        _write_text(queue_path, before)  # restore prior content
        raise StatusError(
            "queue would become invalid; nothing written (%s)"
            % "; ".join(errors))
    # A successful write auto-commits queue.md when the store sits inside a git
    # work tree (shipd-wiki wiki-autocommit); a no-op outside git, and a commit
    # failure never fails the write.
    sc.wiki_autocommit(wiki, [queue_path], "shipd-wiki: queue-answer %s" % qid)
    print(qid)
    return 0


def cmd_wiki_queue_discard(root, slug, reason):
    """Remove a still-pending queue block (shipd-wiki wiki-queue-discard-verb,
    wiki-store-layout). Resolves the workspace store exactly as
    ``wiki-queue-add`` does — scaffolding the nearest workspace's store on
    demand when it does not yet exist, rather than erroring — accepts the bare
    slug (prefixing ``q-`` itself), and deletes the whole ``## q-<slug>``
    block, printing the block id. The ``--reason`` text is required and
    non-empty; it is echoed to the caller on stderr, never stored. A missing
    block, or a block whose answer is no longer ``pending``, writes nothing and
    exits non-zero — an answered block belongs to the `/s:teach` drain and is
    never discarded. Every other queue block is preserved verbatim."""
    if not sc.KEBAB_RE.match(slug):
        raise StatusError("queue slug '%s' is not a kebab-case slug" % slug)
    reason = (reason or "").strip()
    if not reason:
        raise StatusError("--reason must not be empty")
    ws_root = _resolve_workspace(root)
    wiki = sc.wiki_dir(ws_root)
    queue_path = os.path.join(wiki, "queue.md")
    if not os.path.isfile(queue_path):
        _scaffold_wiki_store(wiki)
    with open(queue_path, encoding="utf-8") as fh:
        before = fh.read()

    qid = "q-%s" % slug
    fields = dict(sc.parse_queue_blocks(before)).get(qid)
    if fields is None:
        raise StatusError("queue has no block '%s'" % qid)
    if fields.get("Answer", "").strip() != "pending":
        raise StatusError(
            "block '%s' is already answered ('%s'); discarding an answered "
            "block is never right — it belongs to the `/s:teach` drain"
            % (qid, fields.get("Answer", "")))

    # Cut the block's own lines out; every other line is preserved verbatim.
    # The block runs from its header to the next `## ` header (or EOF), so its
    # trailing blank separator travels with it — except for a trailing block,
    # whose *preceding* blank separator is consumed instead, leaving the file
    # exactly as it read before that block was appended.
    lines = before.splitlines(keepends=True)
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        header = sc.WIKI_QUEUE_HEADER_RE.match(line.rstrip("\n"))
        if start is None:
            if header and header.group(1) == qid:
                start = i
            continue
        if line.startswith("## "):
            end = i
            break
    if start is None:  # defensive: the parser found the block, so this is a bug
        raise StatusError("queue has no block '%s'" % qid)
    if end == len(lines):
        while start > 0 and lines[start - 1].strip() == "":
            start -= 1
    new_text = "".join(lines[:start] + lines[end:])

    _write_text(queue_path, new_text)
    errors = _validate_queue_text(new_text)
    if errors:
        _write_text(queue_path, before)  # restore prior content
        raise StatusError(
            "queue would become invalid; nothing discarded (%s)"
            % "; ".join(errors))
    # A successful discard auto-commits queue.md when the store sits inside a
    # git work tree (shipd-wiki wiki-autocommit); a no-op outside git, and a
    # commit failure never fails the write.
    sc.wiki_autocommit(wiki, [queue_path], "shipd-wiki: queue-discard %s" % qid)
    print("discarded %s: %s" % (qid, reason), file=sys.stderr)
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


def _add_json_flag(subparser, help_text=None):
    """Give one read verb's subparser the ``--json`` machine-output flag
    (spec-status json-output). The six read verbs and ``pipeline-show`` get it
    — the mutating and guarded verbs stay text-only. ``help_text`` overrides the
    generic help for a verb whose JSON document warrants describing."""
    subparser.add_argument(
        "--json", action="store_true", dest="json",
        help=help_text or
        "emit one JSON document on stdout instead of the text report")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read/write spec lifecycle status and the current-spec "
                    "selection for the shipd spec engine.")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repo root containing the .shipd/ content directory (default: cwd)")
    sub = parser.add_subparsers(dest="verb")

    p_init = sub.add_parser(
        "init",
        help="create the content directory layout (safe to re-run)")
    # Repeated on the subparser so `init --root DIR` — the form the `shipd
    # init` delegation produces — resolves the same way `--root DIR init`
    # does. SUPPRESS keeps the shared top-level default: without the flag here
    # the namespace value the top-level option already resolved stands.
    p_init.add_argument(
        "--root", default=argparse.SUPPRESS,
        help="repo root to initialize (default: the shared --root)")

    p_use = sub.add_parser("use", help="record the spec being worked on")
    p_use.add_argument("change")

    sub.add_parser("current", help="print the selected change name")

    p_show = sub.add_parser(
        "show",
        help="print a change's status and progress (the workspace board "
             "report with no change given and none selected — aggregating the "
             "declared workspace projects when the invocation root lies "
             "inside none of them)")
    p_show.add_argument("change", nargs="?", default=None)
    _add_json_flag(p_show)

    p_status = sub.add_parser("status", help="print the bare status value")
    p_status.add_argument("change", nargs="?", default=None)
    _add_json_flag(p_status)

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
    _add_json_flag(p_locate)

    p_related = sub.add_parser(
        "related",
        help="rank the spec library's artifacts by term-hit count (keyed "
             "blocks, top ten plus a remainder line)")
    p_related.add_argument("terms", nargs="+", metavar="term")
    _add_json_flag(p_related)

    p_check_base = sub.add_parser(
        "check-base",
        help="compare a change's deltas against the master library (read-only)")
    p_check_base.add_argument("change", nargs="?", default=None)

    p_epic_show = sub.add_parser(
        "epic-show",
        help="print an epic's board-shaped report (status, metadata, shipped "
             "progress, members grouped into the board's lanes)")
    p_epic_show.add_argument("slug")
    _add_json_flag(p_epic_show)

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

    p_pipeline_show = sub.add_parser(
        "pipeline-show",
        help="print the effective autonomous pipeline and its provenance")
    p_pipeline_show.add_argument(
        "--expand", metavar="PRESET",
        help="print the named built-in preset's entry list as JSON (the value "
             "to declare to fork it into a custom list) instead of resolving "
             "this repo's pipeline; with --json the same entry-list array "
             "prints")
    _add_json_flag(
        p_pipeline_show,
        help_text="emit the machine contract instead of the text report: one "
                  "JSON object with `source` (the raw provenance) and "
                  "`entries` (the resolved entry dicts)")

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
    p_ws_init.add_argument(
        "--nested", action="store_true",
        help="permit creating the workspace beneath an enclosing one")

    p_ws_show = sub.add_parser(
        "workspace-show",
        help="print the workspace root, its projects, and its initiatives")
    _add_json_flag(p_ws_show)

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

    p_wiki_qanswer = sub.add_parser(
        "wiki-queue-answer",
        help="write an answer into a still-pending wiki queue block")
    p_wiki_qanswer.add_argument("slug")
    p_wiki_qanswer.add_argument("--answer", required=True)
    p_wiki_qanswer.add_argument(
        "--advisory", action="store_true",
        help="store the answer as advisory (`advisory: <text>`) rather than "
             "binding knowledge")

    p_wiki_qdiscard = sub.add_parser(
        "wiki-queue-discard",
        help="remove a still-pending wiki queue block")
    p_wiki_qdiscard.add_argument("slug")
    p_wiki_qdiscard.add_argument(
        "--reason", required=True,
        help="why the answer is not worth capturing; echoed, not stored")

    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.verb is None:
        parser.print_help(sys.stderr)
        return 2

    try:
        if args.verb == "init":
            return cmd_init(root)
        if args.verb == "use":
            return cmd_use(root, args.change)
        if args.verb == "current":
            return cmd_current(root)
        if args.verb == "show":
            return cmd_show(root, args.change, as_json=args.json)
        if args.verb == "status":
            return cmd_status(root, args.change, as_json=args.json)
        if args.verb == "validate":
            return cmd_validate(root, args.change)
        if args.verb == "set-status":
            return cmd_set_status(root, args.status, args.change, args.force)
        if args.verb == "sync":
            return cmd_sync(root, args.change)
        if args.verb == "locate":
            return cmd_locate(root, args.change, as_json=args.json)
        if args.verb == "related":
            return cmd_related(root, args.terms, as_json=args.json)
        if args.verb == "check-base":
            return cmd_check_base(root, args.change)
        if args.verb == "epic-show":
            return cmd_epic_show(root, args.slug, as_json=args.json)
        if args.verb == "epic-sync":
            return cmd_epic_sync(root, args.slug)
        if args.verb == "epic-set-status":
            return cmd_epic_set_status(root, args.status, args.slug)
        if args.verb == "epic-set-initiative":
            return cmd_epic_set_initiative(root, args.slug, args.initiative)
        if args.verb == "config-show":
            return cmd_config_show(root)
        if args.verb == "pipeline-show":
            return cmd_pipeline_show(root, expand=args.expand,
                                     as_json=args.json)
        if args.verb == "cat":
            return cmd_cat(root, args.kind, args.slug, args.personal)
        if args.verb == "initiative-show":
            return cmd_initiative_show(root, args.slug)
        if args.verb == "initiative-sync":
            return cmd_initiative_sync(root, args.slug)
        if args.verb == "initiative-set-status":
            return cmd_initiative_set_status(root, args.status, args.slug)
        if args.verb == "workspace-init":
            return cmd_workspace_init(args.path, args.git, args.nested)
        if args.verb == "workspace-show":
            return cmd_workspace_show(root, as_json=args.json)
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
        if args.verb == "wiki-queue-answer":
            return cmd_wiki_queue_answer(root, args.slug, args.answer,
                                         args.advisory)
        if args.verb == "wiki-queue-discard":
            return cmd_wiki_queue_discard(root, args.slug, args.reason)
    except RefusalError as exc:
        print("Refused: %s" % exc.reason, file=sys.stderr)
        for detail in exc.details:
            print(detail, file=sys.stderr)
        return 3
    except StatusError as exc:
        cc.err(str(exc))
        return 1
    except sc.ConfigError as exc:
        cc.err(str(exc))
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
