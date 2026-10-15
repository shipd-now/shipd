#!/usr/bin/env python3
"""spec_gate.py — the context-sufficiency gate for the shipd spec engine
(stdlib only, no network, no third-party imports).

The gate is the autonomous pipeline's decision point on whether a freshly
planned change carries enough context to build against the codebase. It runs
the structural linter plus four deterministic, repository-local context checks
and a provisional-entry check, and settles the change's status:

  * every check passes  → any ``## Context insufficient`` section is removed
    from ``plan.md``, the plan stamp is written into its header (see below),
    the plan is promoted ``draft`` → ``ready`` (a ``ready`` plan is left
    ``ready``), a pass line and a ``stamp:`` line print, and the exit code is 0.
  * any check fails      → the findings are written into ``plan.md`` as a single
    ``## Context insufficient`` section (after the header metadata, before
    ``## Idea``), the status is set to ``rejected``, the findings print, and the
    exit code is 2.
  * a general error (unknown change, missing plan, unreadable tree) → exit 1.

The four context checks (see the context-gate capability):

  1. Stale base — every ``base:`` hash on a MODIFIED/REMOVED delta entry must
     equal the current master requirement's content hash.
  2. Placeholders — ``TBD``, ``TODO``, ``FIXME``, ``XXX``, ``???`` and
     ``OPEN QUESTION`` (case-insensitive, word-bounded) anywhere in ``plan.md``,
     the delta specs, or ``tasks.md``.
  3. Task file references — every backticked, path-shaped token in ``tasks.md``
     containing ``/`` must resolve to an existing file or directory, or have an
     existing parent or grandparent directory (the new-file / one-new-directory
     case, e.g. a new skill or test tree). The tokens come from the shared
     ``spec_common.cited_paths`` helper the drift verb also reads.
  4. Delta targets — every MODIFIED/REMOVED/RENAMED delta operation must target
     a capability whose master spec exists; ADDED-only new capabilities pass.

After the four context checks, a fifth check (context-gate
provisional-entry-check) rejects any ``## Questions and answers`` entry in
``plan.md`` whose ``**Answered by:**`` field holds ``PLANNER``: a provisional
default still awaits a human answer.

The plan stamp (context-gate plan-stamp-write): on a pass the gate writes
``Planned-at: <sha>`` — ``git merge-base HEAD <base>`` resolved from the plan's
own directory, ``--base`` defaulting to ``main`` — and ``Gated-hash: <hash>`` —
:func:`spec_common.plan_gated_hash` of the stripped plan — as the last lines of
the header metadata block, replacing existing stamp lines in place. When the
base cannot be resolved (no git, no work tree, unresolvable ref) the
``Planned-at`` line is omitted (a stale one removed) and one ``note:`` line
prints on stderr; the gate still passes. A rejecting run leaves any existing
stamp lines untouched.

Check mode (context-gate gate-check-mode): ``spec_gate.py <change> --check``
runs the same checks plus, on a stamped plan, a ``Gated-hash`` mismatch check
(the plan was edited after it was gated), prints ``PASS (check): ...`` (exit 0)
or ``REJECTED (check): ...`` with one dot-point per finding (exit 2), and is
read-only by construction: it writes no file, moves no status, runs no store
autocommit, and records no flow snapshot. An unstamped plan gets no mismatch
finding.

Status writes go through :mod:`spec_status`'s metadata-preserving writer, never
ad-hoc edits, so the title, ``Status:`` line, and header metadata survive. The
gate never invokes a model or the network.

Exit codes: 0 pass (promoted to ``ready``), 2 rejected (findings written), 1
general error. Distinct from ``set-status``'s refusal code 3, which the gate
never uses.
"""

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402
import spec_lint as sl  # noqa: E402
import spec_status as ss  # noqa: E402

# The gate-owned ephemeral section header (shipd-spec-format plan-document-sections).
GATE_SECTION = "## Context insufficient"

# Placeholder markers (context-sufficiency-checks). Alphabetic markers are
# matched case-insensitively and word-bounded; ``???`` is all non-word
# characters, so it is a literal substring match instead.
PLACEHOLDER_WORDS = ("TBD", "TODO", "FIXME", "XXX", "OPEN QUESTION")
PLACEHOLDER_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in PLACEHOLDER_WORDS) + r")\b",
    re.IGNORECASE)
QMARK_MARKER = "???"

# A backticked token in tasks.md that is shaped like a repository path. The
# patterns live in spec_common (shared with the drift verb through
# ``sc.cited_paths``); they are rebound here for existing callers.
BACKTICK_RE = sc.BACKTICK_RE
PATH_TOKEN_RE = sc.PATH_TOKEN_RE


class GateError(Exception):
    """A general error: printed as ``Error: ...`` to stderr, exit 1."""


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _rel(root, path):
    return os.path.relpath(path, root)


# ---------------------------------------------------------------------------
# Plan paths
# ---------------------------------------------------------------------------


def _planned_dir(root, change):
    return os.path.join(sc.specs_dir(root), "planned", change)


def _plan_path(root, change):
    return os.path.join(_planned_dir(root, change), "plan.md")


def _tasks_path(root, change):
    return os.path.join(_planned_dir(root, change), "tasks.md")


def _deltas_dir(root, change):
    return os.path.join(_planned_dir(root, change), "specs")


def _master_path(root, capability):
    return os.path.join(sc.specs_dir(root), "verified", capability, "spec.md")


# ---------------------------------------------------------------------------
# Gate-owned section (insert / strip)
# ---------------------------------------------------------------------------


def _strip_gate_section(text):
    """Return ``text`` with any ``## Context insufficient`` section removed
    (from its header up to, but not including, the next ``## `` heading). Any
    blank line preceding the header is preserved, so a stripped plan reads
    cleanly."""
    lines = text.splitlines()
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == GATE_SECTION:
            i += 1
            while i < n and not lines[i].startswith("## "):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    result = "\n".join(out)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _render_section(findings):
    """Render the gate-owned section: a summary paragraph followed by one
    dot-point per finding, ending with a trailing blank line."""
    lines = [GATE_SECTION, "",
             "The context-sufficiency gate found this plan lacking the context "
             "needed to build against the codebase. Resolve the findings below, "
             "then re-gate.", ""]
    for finding in findings:
        lines.append("- %s" % finding)
    lines.append("")
    return lines


def _insert_gate_section(text, findings):
    """Return ``text`` with a fresh gate-owned section inserted after the header
    metadata block and before ``## Idea``. Any existing gate section is stripped
    first, so repeated failing runs replace rather than accumulate. The title,
    ``Status:`` line, and header metadata are untouched."""
    text = _strip_gate_section(text)
    lines = text.splitlines()
    section = _render_section(findings)
    idea_idx = next((i for i, ln in enumerate(lines)
                     if ln.strip() == "## Idea"), None)
    if idea_idx is not None:
        insert_at = idea_idx
    else:
        insert_at = _header_end(lines)
    new = lines[:insert_at] + section + lines[insert_at:]
    result = "\n".join(new)
    if not result.endswith("\n"):
        result += "\n"
    return result


def _header_end(lines):
    """Return the index just past the plan's header metadata block: the
    ``Status:`` line plus the contiguous run of ``Key: value`` metadata lines
    after it. Falls back to just after the title (or the top) when no
    ``Status:`` line is present."""
    status_idx = next((i for i, ln in enumerate(lines)
                       if sc.PLAN_STATUS_LINE_RE.match(ln)), None)
    if status_idx is None:
        return 1 if lines else 0
    end = status_idx + 1
    while end < len(lines):
        ln = lines[end]
        if ln.strip() == "" or ln.lstrip().startswith("#"):
            break
        if not sc.METADATA_LINE_RE.match(ln):
            break
        end += 1
    return end


# ---------------------------------------------------------------------------
# Context checks
# ---------------------------------------------------------------------------


def _check_delta_targets_and_base(root, change):
    """Checks (1) stale base and (4) delta targets. A MODIFIED/REMOVED/RENAMED
    delta operation against a capability with no master spec is a finding; when
    the master exists, every MODIFIED/REMOVED ``base:`` hash must equal the
    matching master requirement's current content hash."""
    findings = []
    deltas_dir = _deltas_dir(root, change)
    if not os.path.isdir(deltas_dir):
        return findings
    for capability in sorted(os.listdir(deltas_dir)):
        path = os.path.join(deltas_dir, capability, "spec.md")
        if not os.path.isfile(path):
            continue
        delta = sc.parse_delta(_read(path))
        needs_master = bool(delta.modified or delta.removed or delta.renamed)
        master_path = _master_path(root, capability)
        master_exists = os.path.isfile(master_path)
        if needs_master and not master_exists:
            findings.append(
                "delta capability '%s' edits (MODIFIED/REMOVED/RENAMED) a "
                "requirement, but its master spec does not exist (%s)"
                % (capability, _rel(root, master_path)))
            continue
        if not master_exists:
            continue
        master = sc.parse_spec(_read(master_path))
        by_id = {r.id: r for r in master.requirements if r.id}
        for req in delta.modified + delta.removed:
            if req.base is None:
                continue  # missing base is a lint error, reported separately
            mreq = by_id.get(req.id)
            if mreq is None:
                findings.append(
                    "stale context: requirement '%s' (capability '%s') has no "
                    "matching requirement in the current master"
                    % (req.id or "<untitled>", capability))
                continue
            if sc.content_hash(mreq) != req.base:
                findings.append(
                    "stale context: `base:` hash of requirement '%s' "
                    "(capability '%s') no longer matches the current master"
                    % (req.id, capability))
    return findings


def _placeholders_in(text):
    """Return the ordered, de-duplicated canonical placeholder markers present
    in ``text`` (word-bounded and case-insensitive for the alphabetic markers;
    a literal substring match for ``???``)."""
    found = []
    for m in PLACEHOLDER_RE.finditer(text):
        canonical = m.group(1).upper()
        if canonical not in found:
            found.append(canonical)
    if QMARK_MARKER in text and QMARK_MARKER not in found:
        found.append(QMARK_MARKER)
    return found


def _check_placeholders(root, change):
    """Check (2): placeholder markers anywhere in plan.md (minus the gate-owned
    section), the delta specs, or tasks.md."""
    findings = []
    targets = []

    plan_path = _plan_path(root, change)
    if os.path.isfile(plan_path):
        # Scan the plan without its own ephemeral gate section: a prior run's
        # findings live there and must not re-trigger the placeholder check.
        targets.append((plan_path, _strip_gate_section(_read(plan_path))))

    deltas_dir = _deltas_dir(root, change)
    if os.path.isdir(deltas_dir):
        for capability in sorted(os.listdir(deltas_dir)):
            path = os.path.join(deltas_dir, capability, "spec.md")
            if os.path.isfile(path):
                targets.append((path, _read(path)))

    tasks_path = _tasks_path(root, change)
    if os.path.isfile(tasks_path):
        targets.append((tasks_path, _read(tasks_path)))

    for path, text in targets:
        for marker in _placeholders_in(text):
            findings.append(
                "placeholder marker '%s' found in %s" % (marker, _rel(root, path)))
    return findings


def _check_task_paths(root, change):
    """Check (3): every backticked, path-shaped token in tasks.md must resolve
    to an existing file or directory, or have an existing parent or grandparent
    directory (tolerating one new directory level)."""
    findings = []
    tasks_path = _tasks_path(root, change)
    if not os.path.isfile(tasks_path):
        return findings
    text = _read(tasks_path)
    for token in sc.cited_paths(text):
        full = os.path.join(root, token)
        if os.path.exists(full):
            continue
        if token.startswith("artefacts/") and os.path.exists(
                os.path.join(_planned_dir(root, change), token)):
            continue  # change-relative artefact reference
        parent = os.path.dirname(token)
        if parent and os.path.isdir(os.path.join(root, parent)):
            continue  # the new-file-in-an-existing-directory case
        grandparent = os.path.dirname(parent)
        if grandparent and os.path.isdir(os.path.join(root, grandparent)):
            continue  # one new directory deep: the new-skill / new-test-tree case
        findings.append(
            "task file reference `%s` resolves to no existing file or "
            "directory (neither its parent nor grandparent directory exists)"
            % token)
    return findings


# The bullet and backticks are optional: spec_lint accepts the field anywhere
# in the entry body, so the gate must not let a format variant slip through.
PROVISIONAL_RE = re.compile(
    r"^\s*(?:-\s*)?\*\*Answered by:\*\*\s*`?PLANNER\b")


def _check_provisional_entries(root, change):
    """Check (5): every ``## Questions and answers`` entry whose
    ``**Answered by:**`` field holds ``PLANNER`` is a finding naming the
    entry."""
    findings = []
    plan_path = _plan_path(root, change)
    if not os.path.isfile(plan_path):
        return findings
    section = sl._section_lines(_read(plan_path), sl.QA_SECTION)
    if section is None:
        return findings
    label = None
    for line in section:
        if line.startswith("### "):
            m = sl.QA_ENTRY_RE.match(line.rstrip())
            label = "Q%s" % m.group(1) if m else None
        elif label and PROVISIONAL_RE.match(line):
            findings.append(
                "ledger entry %s is provisional (**Answered by:** PLANNER) "
                "and awaits a human answer" % label)
            label = None
    return findings


def collect_findings(root, change):
    """Run the structural linter, the four context checks, and the
    provisional-entry check, returning the ordered list of finding strings
    (empty when the change has sufficient context)."""
    findings = [str(e) for e in sl.lint_change(root, change)]
    findings += _check_delta_targets_and_base(root, change)
    findings += _check_placeholders(root, change)
    findings += _check_task_paths(root, change)
    findings += _check_provisional_entries(root, change)
    return findings


# ---------------------------------------------------------------------------
# Gate driver
# ---------------------------------------------------------------------------


def _resolve_planned_at(plan_path, base):
    """Return ``(sha, reason)``: the full commit id of ``git merge-base HEAD
    <base>`` run from the plan's own directory (so a linked worktree or an
    external store anchors correctly), or ``(None, reason)`` when git is
    absent, the directory is not in a work tree, or the ref is unresolvable.
    Never raises: the gate's verdict is about context, not git."""
    try:
        r = subprocess.run(
            ["git", "-C", os.path.dirname(os.path.abspath(plan_path)),
             "merge-base", "HEAD", base],
            capture_output=True, text=True)
    except OSError as exc:
        return None, "git unavailable: %s" % exc
    sha = r.stdout.strip()
    if r.returncode != 0 or not re.match(r"^[0-9a-f]{40}$", sha):
        detail = (r.stderr.strip().splitlines() or ["exit %d" % r.returncode])[0]
        return None, "git merge-base HEAD %s failed: %s" % (base, detail)
    return sha, None


def _validate_change(root, change):
    """Return the change's ``plan.md`` path, raising :class:`GateError` for an
    unknown change or a missing plan."""
    if not os.path.isdir(_planned_dir(root, change)):
        raise GateError(
            "unknown change '%s' (no directory under %s)"
            % (change, os.path.join(sc.specs_dir(root), "planned")))
    plan_path = _plan_path(root, change)
    if not os.path.isfile(plan_path):
        raise GateError("plan.md not found for change '%s'" % change)
    return plan_path


def _check_gated_hash(root, change):
    """The ``--check`` mode's edited-after-gate finding (context-gate
    gate-check-mode): when the plan carries a ``Gated-hash`` stamp that no
    longer matches :func:`spec_common.plan_gated_hash` of the plan with its
    gate section stripped, return one finding naming both hashes; otherwise an
    empty list (an unstamped plan is never a finding)."""
    text = _read(_plan_path(root, change))
    _planned_at, stamped = sc.read_plan_stamp(text)
    if stamped is None:
        return []
    current = sc.plan_gated_hash(_strip_gate_section(text))
    if current == stamped:
        return []
    return ["gated-hash mismatch: plan.md was edited after it was gated "
            "(stamp %s, content %s); re-gate with spec_gate.py %s"
            % (stamped, current, change)]


def run_check(root, change):
    """Run every gate check plus the ``Gated-hash`` mismatch check, read-only.
    Returns the process exit code (0 pass, 2 findings). Raises
    :class:`GateError` for a general error. Writes nothing."""
    _validate_change(root, change)
    findings = collect_findings(root, change) + _check_gated_hash(root, change)
    if not findings:
        print("PASS (check): change '%s' has sufficient context; nothing "
              "written." % change)
        return 0
    print("REJECTED (check): change '%s' lacks sufficient context (%d "
          "finding(s)):" % (change, len(findings)))
    for finding in findings:
        print("- %s" % finding)
    return 2


def run_gate(root, change, base="main"):
    """Evaluate ``change`` and settle its status. Returns the process exit code
    (0 pass, 2 rejected). Raises :class:`GateError` for a general error.
    ``base`` is the ref the plan stamp's ``Planned-at`` merge-base is taken
    against."""
    plan_path = _validate_change(root, change)

    findings = collect_findings(root, change)

    if not findings:
        # Pass: remove any stale gate section, stamp the plan, promote to
        # ready (context-gate plan-stamp-write).
        text = _strip_gate_section(_read(plan_path))
        sha, reason = _resolve_planned_at(plan_path, base)
        gated_hash = sc.plan_gated_hash(text)
        text = sc.write_plan_stamp(text, sha, gated_hash)
        if sha is None:
            print("note: Planned-at omitted (%s)" % reason, file=sys.stderr)
        with open(plan_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        ss.write_status(root, change, "ready")
        # The gate's plan rewrite into an external store auto-commits locally,
        # scoped to the plan (shipd-config store-autocommit); a no-op for an
        # in-repo plan, and a commit failure never fails the gate.
        sc.store_autocommit(root, [plan_path],
                            "shipd: gate change %s (ready)" % change)
        print("PASS: change '%s' has sufficient context; status is now ready."
              % change)
        print("stamp: Planned-at %s Gated-hash %s" % (sha or "none", gated_hash))
        return 0

    # Reject: set status, then write the findings into the plan.
    ss.write_status(root, change, "rejected")
    text = _insert_gate_section(_read(plan_path), findings)
    with open(plan_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    sc.store_autocommit(root, [plan_path],
                        "shipd: gate change %s (rejected)" % change)
    print("REJECTED: change '%s' lacks sufficient context (%d finding(s)):"
          % (change, len(findings)))
    for finding in findings:
        print("- %s" % finding)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Context-sufficiency gate: evaluate a planned change and "
                    "settle its status (ready on pass, rejected on fail).")
    parser.add_argument("change", help="the planned change to gate")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repo root containing the .shipd/ content directory "
                             "(default: cwd)")
    parser.add_argument("--base", default="main",
                        help="ref the plan stamp's Planned-at merge-base is "
                             "taken against (default: main)")
    parser.add_argument("--check", action="store_true",
                        help="run every check (plus the Gated-hash mismatch "
                             "check) read-only: write nothing, move no status")
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)

    try:
        # The schema compatibility gate (schema-versioning schema-compat-gate):
        # refuse a repo whose artifacts declare a different grammar major
        # before the change is evaluated or its status settled.
        sc.check_schema_compat(root)
        if args.check:
            return run_check(root, args.change)
        return run_gate(root, args.change, base=args.base)
    except GateError as exc:
        cc.err(str(exc))
        return 1
    except (OSError, sc.ConfigError, ss.StatusError) as exc:
        cc.err(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
