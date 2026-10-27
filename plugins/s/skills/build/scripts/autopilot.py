#!/usr/bin/env python3
"""autopilot.py — the epic autopilot: plan → gate → build → PR, per member.

Given an approved epic (``ready`` or ``active``), the autopilot drives its
unplanned member changes to shipped PRs without human interaction. Members are
selected and ordered by the stub table's ``After`` dependency layers, then
risk-ascending within a layer (an ``After`` cycle refuses the run); each is
driven through the resolved
``autonomous-pipeline`` (skips, replacements, custom steps honored) in its own
worktree/branch. Gate rejections park a member for human enrichment; other
stage failures get re-driven up to the entry's fresh-attempt budget (its
``autopilot.attempts``, three by default) before parking the member as
``needs-human`` with a resumable session id. Every run ends with a report —
machine-readable JSON plus a human summary.

A ``--waves`` mode computes, from on-disk state and the local git refs alone,
the waves of members the in-session drive may run concurrently — plan waves
over the unplanned members in ``After`` dependency layers, then build waves
over the ready ones whose planned delta capabilities are pairwise disjoint,
each capped at ``--parallel N`` — and drives nothing. A ready member whose
``After`` dependency has not yet merged into the base branch joins no wave and
is reported as blocked.

A ``--preflight`` mode prints a read-only launch rubric — ``ok|warn|fail
<check> — <detail>`` lines in the ``shipd doctor`` format, then ``preflight:
ok`` or ``preflight: <n> problem(s)`` (or one JSON object with ``--json``) —
checking the epic's lint and status, its ``After`` cycles, member planning,
gate and gated-hash state, drift, requirement and file overlap, the pipeline,
and relaying ``shipd doctor``; it exits non-zero on any ``fail`` and drives
nothing.

Before a member's built-in ``build`` stage, the driver runs a pre-build drift
step: it resolves the base ref (``origin/main`` where it resolves, else
``main``), parks the member if an ``After`` dependency has not merged into it,
merges the ref into the member's worktree, and runs ``spec_status.py drift``.
A drifted plan is judged by a headless ``/s:drift --json`` turn: ``holds``
builds, ``conflict`` parks the member, and ``revise`` re-plans through a
``replan`` session and re-gates against the synced ref. A member whose
``After`` dependency parked earlier in the run is not driven at all.

Standard library only. Live sessions, the gate, and external commands are all
reached through injectable seams so the orchestration is unit-testable without
spending model time.
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import json
import os
import re
import signal
import subprocess
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from heartbeat import RunHeartbeat  # noqa: E402
import session_driver  # noqa: E402
import spec_common as sc  # noqa: E402
import spec_status as ss  # noqa: E402
from spec_lint import lint_change, lint_epic  # noqa: E402

# The plugin root (``plugins/s``), four directories up from this script, is the
# ``--plugin-dir`` handed to driven sessions so ``/s:*`` skills load.
PLUGIN_DIR = os.path.normpath(os.path.join(SCRIPTS_DIR, "..", "..", ".."))
WORKTREE_SH = os.path.join(SCRIPTS_DIR, "worktree.sh")
# The engine's worktree create path: the git mechanics of ``worktree.sh`` plus
# the repo's configured ``post-worktree-scripts``, so a driven member's
# worktree is already set up before its first stage runs. Creation goes
# through here; the guarded teardown stays on the bash helper above.
WORKTREE_PY = os.path.join(SCRIPTS_DIR, "worktree.py")
GATE_PY = os.path.join(SCRIPTS_DIR, "spec_gate.py")
STATUS_PY = os.path.join(SCRIPTS_DIR, "spec_status.py")
SHIPD_BIN = os.path.join(PLUGIN_DIR, "bin", "shipd")
# A ``shipd doctor`` report line, relayed by the launch preflight.
DOCTOR_LINE_RE = re.compile(r"^(ok|warn|fail) (\S+) — (.*)$")
PREFLIGHT_CHECKS = (
    "epic-lint", "epic-status", "after-cycle", "members", "gate-check",
    "gated-hash", "drift", "overlap-requirements", "overlap-files",
    "pipeline")
REVIEW_GATE_PY = os.path.join(
    PLUGIN_DIR, "skills", "review", "scripts", "review_gate.py")

# Stages the autopilot drives with built-in behavior; the rest of the registry
# is pre-approval (noted and ignored).
DRIVEN_STAGES = ("plan", "gate", "build", "review")
PRE_APPROVAL_STAGES = ("research", "epic")

# Risk ordering for member selection (unknown ratings sort last).
RISK_RANK = {"low": 0, "medium": 1, "high": 2}

TIMEOUT_DEFAULT = session_driver.TIMEOUT_DEFAULT
MAX_RESUMES_DEFAULT = session_driver.MAX_RESUMES_DEFAULT

# Every driven session's canned reply — accept the session's own
# recommendations and drive to the stage's gradable terminal state.
# The oracle is consulted inline: the session runs the lookup verb and judges
# its output under the contract reference (no agent is spawned).
ORACLE_CONTRACT_PATH = os.path.join(
    PLUGIN_DIR, "skills", "ask", "references", "oracle-contract.md")
ORACLE_LOOKUP_CMD = ("python3 %s --root <repo> oracle-lookup <terms>"
                     % STATUS_PY)
ORACLE_JUDGE_NOTE = ("judge its output per the contract at %s"
                     % ORACLE_CONTRACT_PATH)

GOAHEAD_REPLY = (
    "Proceed. For any undecided point or decision, now or in later rounds: "
    "shape it into a compact question (the decision, the options, your "
    "recommendation) and consult the oracle inline by running `%s` with this "
    "repo's root, then %s; adopt its ANSWER, "
    "and on INSUFFICIENT — or if the lookup fails — take the option "
    "you yourself recommend. Never wait for a human. Complete the work through "
    "to its terminal state." % (ORACLE_LOOKUP_CMD, ORACLE_JUDGE_NOTE))


class AutopilotError(Exception):
    """A run-blocking condition (bad epic, failed preflight)."""


@dataclasses.dataclass
class Member:
    """One epic stub-table member and its derived state."""
    slug: str
    description: str
    risk: str
    state: str
    order: int
    after: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class MemberResult:
    """The outcome of driving one member. ``outcome`` is one of ``shipped``,
    ``drafted`` (draft mode's terminal open PR — shipd-config pr-mode-key),
    ``rejected`` (gate bounced the plan), or ``needs_human`` (parked)."""
    outcome: str
    pr_url: str = None
    merged: bool = False
    stage: str = None
    reason: str = None
    session_id: str = None


def _noop(*_args, **_kwargs):
    pass


# ---------------------------------------------------------------------------
# Member selection and ordering
# ---------------------------------------------------------------------------

def _epic_file(root, epic):
    return os.path.join(sc.specs_dir(root), "epics", epic, "epic.md")


def parse_members(root, epic):
    """Parse the epic's ``## Changes`` stub table into :class:`Member`s, each
    carrying its Risk rating and its derived lifecycle state (``spec_status``
    internals: ``unplanned`` until planned, then the plan status, ``archived``
    once completed)."""
    with open(_epic_file(root, epic), encoding="utf-8") as fh:
        text = fh.read()
    header, rows = sc.parse_epic_changes(text)
    after_map = sc.parse_epic_after(text)
    risk_idx = None
    if header:
        for i, cell in enumerate(header):
            if cell.strip().lower() == "risk":
                # Ratings are the cells after slug + description (columns 2+).
                risk_idx = i - 2
                break
    members = []
    for order, (slug, description, ratings) in enumerate(rows):
        if risk_idx is not None and 0 <= risk_idx < len(ratings):
            risk = ratings[risk_idx].strip().lower()
        elif ratings:
            risk = ratings[-1].strip().lower()
        else:
            risk = ""
        members.append(Member(
            slug=slug, description=description, risk=risk,
            state=ss._member_state(root, slug), order=order,
            after=list(after_map.get(slug, []))))
    return members


def select_and_order(members):
    """Split ``members`` into ``(to_drive, skipped)``. ``to_drive`` is the
    ``unplanned`` members in ``After`` dependency layers (:func:`_plan_layers`,
    flattened), each layer ordered by Risk ascending (``low`` < ``medium`` <
    ``high``) with ties broken by table order — without an ``After`` column
    every member sits in one layer, so the order is plain risk-ascending.
    ``skipped`` is every other member, left in table order under its state.

    Raises :class:`AutopilotError` naming the cycle when the ``After`` column
    holds a dependency cycle."""
    cycle = sc.find_after_cycle({m.slug: m.after for m in members})
    if cycle:
        raise AutopilotError(
            "After column has a dependency cycle: %s; fix the stub table "
            "(spec_lint.py --epic <epic>)" % " -> ".join(cycle))
    unplanned = [m for m in members if m.state == "unplanned"]
    to_drive = [m for layer in _plan_layers(unplanned, max(len(unplanned), 1))
                for m in layer]
    skipped = [m for m in members if m.state != "unplanned"]
    return to_drive, skipped


def member_capabilities(root, slug):
    """The delta capability directory names of ``slug``'s planned change, read
    from the root that hosts it — a ``.worktrees/<name>`` checkout as readily as
    ``root`` itself (``spec_status._member_state_with_root``). Only a ``ready``
    member has a planned delta to read; every other state yields no
    capabilities, so nothing about it constrains a wave."""
    state, hosting = ss._member_state_with_root(root, slug)
    if state != "ready":
        return []
    specs = os.path.join(sc.specs_dir(hosting), "planned", slug, "specs")
    if not os.path.isdir(specs):
        return []
    return sorted(name for name in os.listdir(specs)
                  if os.path.isfile(os.path.join(specs, name, "spec.md")))


def _plan_layers(to_drive, parallel):
    """Dependency layers over the unplanned ``to_drive`` members (Kahn's
    algorithm). An edge runs from a member to each ``after`` slug that is
    itself unplanned; a dependency in any other state is satisfied. Each layer
    sorts risk-ascending then by table order and is chunked to ``parallel``.
    A cycle never reaches here — :func:`select_and_order` refuses it first."""
    pending = {m.slug: m for m in to_drive}
    deps = {m.slug: {a for a in m.after if a in pending and a != m.slug}
            for m in to_drive}
    key = lambda m: (RISK_RANK.get(m.risk, len(RISK_RANK)), m.order)
    chunks = []
    while pending:
        free = sorted((pending[s] for s in pending if not deps[s]), key=key)
        if not free:  # unreachable: select_and_order refuses a cycle
            break
        for start in range(0, len(free), parallel):
            chunks.append(free[start:start + parallel])
        for m in free:
            del pending[m.slug]
        for s in deps:
            deps[s] -= {m.slug for m in free}
    return chunks


def compute_waves(root, epic, parallel, command_fn=None):
    """The waves of members the in-session drive may run concurrently, computed
    from on-disk state and the local git refs alone (epic-autopilot
    member-wave-scheduling). An ``After`` cycle raises :class:`AutopilotError`
    (via :func:`select_and_order`) before any wave is computed.

    Plan waves come first: the ``unplanned`` members in ``After`` dependency
    layers (risk-ascending without the column), chunked into slices of at most
    ``parallel``. Build waves follow over the ``ready`` members, walked
    risk-ascending: a member with an ``After`` dependency not yet merged into
    the base branch (:func:`_merged_into_base`, cached per dependency within
    this call) joins no wave and is listed under ``blocked`` with its
    ``waiting_on`` slugs; every other member joins the earliest wave whose
    members' capabilities are all disjoint from its own and whose size is
    below ``parallel``, else it opens a new one — the shared verified library
    being the one write that makes two members unsafe to build side by side.
    Members in any other state are reported as skipped under their state. Wave
    indexes run from 1 across both kinds, and the result is deterministic for
    a given tree and set of refs. ``command_fn`` (default
    :func:`_run_command`) is the git seam.
    """
    command_fn = command_fn or _run_command
    if not os.path.isfile(_epic_file(root, epic)):
        raise AutopilotError("epic not found: %s" % epic)
    members = parse_members(root, epic)
    to_drive, skipped = select_and_order(members)

    def _entry(member, capabilities):
        return {"slug": member.slug, "risk": member.risk,
                "capabilities": capabilities, "after": list(member.after)}

    waves = []
    if any(m.after for m in to_drive):
        for chunk in _plan_layers(to_drive, parallel):
            waves.append({"index": len(waves) + 1, "stage": "plan",
                          "members": [_entry(m, []) for m in chunk]})
    else:
        for start in range(0, len(to_drive), parallel):
            chunk = to_drive[start:start + parallel]
            waves.append({"index": len(waves) + 1, "stage": "plan",
                          "members": [_entry(m, []) for m in chunk]})

    ready = sorted(
        (m for m in skipped if m.state == "ready"),
        key=lambda m: (RISK_RANK.get(m.risk, len(RISK_RANK)), m.order))
    # Each open build wave as ``(member entries, the union of their
    # capabilities)`` — the union is what the next member must be disjoint from.
    build_waves = []
    blocked = []
    merged_cache = {}

    def merged(dep):
        if dep not in merged_cache:
            merged_cache[dep] = _merged_into_base(command_fn, root, dep)
        return merged_cache[dep]

    for member in ready:
        waiting_on = [d for d in member.after if not merged(d)]
        if waiting_on:
            blocked.append({"member": member.slug, "waiting_on": waiting_on})
            continue
        caps = member_capabilities(root, member.slug)
        for entries, union in build_waves:
            if len(entries) < parallel and union.isdisjoint(caps):
                entries.append(_entry(member, caps))
                union.update(caps)
                break
        else:
            build_waves.append(([_entry(member, caps)], set(caps)))
    for entries, _union in build_waves:
        waves.append({"index": len(waves) + 1, "stage": "build",
                      "members": entries})

    return {
        "epic": epic,
        "parallel": parallel,
        "waves": waves,
        "blocked": blocked,
        "skipped": [{"member": m.slug, "state": m.state}
                    for m in skipped if m.state != "ready"],
    }


# ---------------------------------------------------------------------------
# Launch preflight (epic-autopilot launch-preflight)
# ---------------------------------------------------------------------------

def _after_reach(after_map):
    """``{slug: every slug reachable through After edges}``."""
    reach = {}
    for slug in after_map:
        seen = set()
        stack = list(after_map.get(slug, []))
        while stack:
            dep = stack.pop()
            if dep in seen:
                continue
            seen.add(dep)
            stack.extend(after_map.get(dep, []))
        reach[slug] = seen
    return reach


def _pf_ordered(reach, a, b):
    """Whether the After graph orders ``a`` and ``b`` in either direction."""
    return b in reach.get(a, ()) or a in reach.get(b, ())


def _first_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _member_delta_targets(hosting, slug):
    """The ordered ``<capability>/<id>`` master requirements the member's
    delta specs modify, remove, or rename."""
    out = []
    pattern = os.path.join(sc.specs_dir(hosting), "planned", slug, "specs",
                           "*", "spec.md")
    for path in sorted(glob.glob(pattern)):
        cap = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf-8") as fh:
            delta = sc.parse_delta(fh.read())
        ids = [r.id for r in delta.modified] + [r.id for r in delta.removed] \
            + [r.from_id for r in delta.renamed]
        for rid in ids:
            target = "%s/%s" % (cap, rid)
            if rid and target not in out:
                out.append(target)
    return out


def _member_cited_paths(hosting, slug):
    """The ordered paths the member's plan, tasks, and delta specs cite,
    without ``artefacts/`` references and the version-bump exempt paths."""
    base = os.path.join(sc.specs_dir(hosting), "planned", slug)
    files = [os.path.join(base, "plan.md"), os.path.join(base, "tasks.md")]
    files += sorted(glob.glob(os.path.join(base, "specs", "*", "spec.md")))
    out = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        for token in sc.cited_paths(text, strip_line_suffix=True):
            if token.startswith("artefacts/") \
                    or token in sc.VERSION_BUMP_EXEMPT_PATHS \
                    or token in out:
                continue
            out.append(token)
    return out


def compute_preflight(root, epic, command_fn=None):
    """The launch rubric for ``epic``: ordered ``ok|warn|fail`` checks
    composed from on-disk state, local git, and the engine's own verbs
    (epic-autopilot launch-preflight). Read-only; never calls
    :func:`select_and_order`, so a cyclic epic still prints every check.
    ``command_fn`` (default :func:`_run_command`) is the only seam."""
    command_fn = command_fn or _run_command
    if not os.path.isfile(_epic_file(root, epic)):
        raise AutopilotError("epic not found: %s" % epic)
    with open(_epic_file(root, epic), encoding="utf-8") as fh:
        text = fh.read()
    members = parse_members(root, epic)
    hosting = {m.slug: ss._member_state_with_root(root, m.slug)[1]
               for m in members}
    after_map = sc.parse_epic_after(text)
    checks = []

    def add(level, check, detail):
        checks.append({"level": level, "check": check, "detail": detail})

    # epic-lint
    errors = []
    lint_epic(root, epic, errors)
    if errors:
        add("fail", "epic-lint", "%d error(s); first: %s"
            % (len(errors), errors[0]))
    else:
        add("ok", "epic-lint", "epic lints clean")

    # epic-status
    status = ss.read_epic_status(root, epic)
    if status in ("ready", "active"):
        add("ok", "epic-status", status)
    elif status == "draft":
        add("fail", "epic-status",
            "draft; approve it with spec_status.py epic-set-status %s ready"
            % epic)
    elif status == "complete":
        add("fail", "epic-status", "complete; nothing left to drive")
    else:
        add("fail", "epic-status", "no valid Status line")

    # after-cycle
    cycle = sc.find_after_cycle(after_map)
    if cycle:
        add("fail", "after-cycle",
            "After column has a dependency cycle: %s" % " -> ".join(cycle))
    else:
        add("ok", "after-cycle", "no dependency cycle")

    # members
    by_state = {}
    for m in members:
        by_state.setdefault(m.state, []).append(m.slug)
    failing = []
    for state in ("unplanned", "draft", "rejected"):
        if by_state.get(state):
            failing.append("%s: %s" % (state, ", ".join(by_state[state])))
    mid = [s for st in ("active", "complete", "verified")
           for s in by_state.get(st, [])]
    counts = ", ".join("%d %s" % (len(by_state[st]), st)
                       for st in ("ready", "archived") if by_state.get(st))
    if failing:
        hints = []
        if by_state.get("unplanned") or by_state.get("draft"):
            hints.append("run /s:epic-grill %s" % epic)
        for slug in by_state.get("rejected", []):
            hints.append("enrich with /s:plan %s" % slug)
        add("fail", "members", "; ".join(failing + hints))
    elif mid:
        add("warn", "members",
            "mid-build, left undriven: %s" % ", ".join(mid))
    else:
        add("ok", "members", counts or "no members")

    # gate-check and gated-hash from one --check run per ready member
    ready = [m.slug for m in members if m.state == "ready"]
    other, mismatch, unstamped = [], [], []
    for slug in ready:
        host = hosting[slug]
        rc, out, err = command_fn(
            [sys.executable, GATE_PY, slug, "--root", host, "--check"], host)
        if rc not in (0, 2):
            other.append("%s: spec_gate.py --check exit %d %s"
                         % (slug, rc, _first_line(err)))
        elif rc == 2:
            findings = [ln[2:].strip() for ln in out.splitlines()
                        if ln.startswith("- ")]
            rest = [f for f in findings if "gated-hash mismatch" not in f]
            if len(rest) != len(findings):
                mismatch.append(slug)
            if rest:
                other.append("%s: %s" % (slug, rest[0]))
        try:
            with open(os.path.join(sc.specs_dir(host), "planned", slug,
                                   "plan.md"), encoding="utf-8") as fh:
                if sc.read_plan_stamp(fh.read())[1] is None:
                    unstamped.append(slug)
        except OSError:
            pass
    if other:
        add("fail", "gate-check", "; ".join(other))
    elif ready:
        add("ok", "gate-check",
            "%d ready member(s) pass spec_gate.py --check" % len(ready))
    else:
        add("ok", "gate-check", "no ready member")
    if mismatch:
        add("fail", "gated-hash", "; ".join(
            "%s: plan.md edited after it was gated; re-gate with "
            "spec_gate.py %s" % (s, s) for s in mismatch))
    elif unstamped:
        add("warn", "gated-hash", "; ".join(
            "%s: no Gated-hash stamp; gate it with spec_gate.py %s" % (s, s)
            for s in unstamped))
    else:
        add("ok", "gated-hash", "%d stamped member(s) match" % len(ready))

    # drift
    rc, out, err = command_fn(
        [sys.executable, STATUS_PY, "--root", root, "drift", "--epic", epic,
         "--json"], root)
    if rc == 0:
        add("ok", "drift", "no drift since the plan stamps")
    else:
        payload = None
        if rc == 4:
            try:
                payload = json.loads(out)
            except ValueError:
                payload = None
        if payload is None:
            add("fail", "drift", "drift verb exit %d: %s"
                % (rc, _first_line(err) or _first_line(out)))
        else:
            parts = []
            for entry in payload.get("members", []):
                kinds = {}
                for finding in entry.get("findings", []):
                    kinds[finding.get("kind")] = \
                        kinds.get(finding.get("kind"), 0) + 1
                if kinds:
                    parts.append("%s (%s)" % (entry.get("change"), ", ".join(
                        "%s %d" % (k, n) for k, n in kinds.items())))
            add("warn", "drift", "%s — judge with /s:drift %s"
                % (", ".join(parts), epic))

    # overlap-requirements and overlap-files over planned members
    planned = [m.slug for m in members
               if m.state not in ("unplanned", "archived")]
    reach = _after_reach(after_map)
    targets = {s: _member_delta_targets(hosting[s], s) for s in planned}
    paths = {s: _member_cited_paths(hosting[s], s) for s in planned}
    req_hits, file_hits = [], []
    for i, a in enumerate(planned):
        for b in planned[i + 1:]:
            if _pf_ordered(reach, a, b):
                continue
            req_hits += ["%s & %s: %s" % (a, b, t)
                         for t in targets[a] if t in targets[b]]
            file_hits += ["%s & %s: %s" % (a, b, p)
                          for p in paths[a] if p in paths[b]]
    if req_hits:
        add("fail", "overlap-requirements", "; ".join(req_hits))
    else:
        add("ok", "overlap-requirements",
            "no shared master requirement among unordered members")
    if file_hits:
        add("warn", "overlap-files", "; ".join(file_hits))
    else:
        add("ok", "overlap-files",
            "no shared cited file among unordered members")

    # pipeline
    try:
        entries, provenance = sc.resolve_pipeline(root)
        add("ok", "pipeline", "%d entries (source: %s)"
            % (len(entries), provenance))
    except sc.ConfigError as exc:
        add("fail", "pipeline", str(exc))

    # doctor relay
    rc, out, err = command_fn([sys.executable, SHIPD_BIN, "doctor"], root)
    relayed = 0
    for line in out.splitlines():
        m = DOCTOR_LINE_RE.match(line)
        if m:
            add(m.group(1), "doctor:" + m.group(2), m.group(3))
            relayed += 1
    if not relayed:
        add("fail", "doctor", "shipd doctor exit %d: %s"
            % (rc, _first_line(err) or _first_line(out)))

    problems = sum(1 for c in checks if c["level"] != "ok")
    return {"epic": epic, "checks": checks, "problems": problems,
            "failed": any(c["level"] == "fail" for c in checks)}


def _print_preflight(result, as_json=False, out=print):
    """Render :func:`compute_preflight`'s result — one JSON object, else one
    ``<level> <check> — <detail>`` line per check and a summary line."""
    if as_json:
        out(json.dumps(result))
        return
    for c in result["checks"]:
        out("%s %s — %s" % (c["level"], c["check"], c["detail"]))
    out("preflight: ok" if not result["problems"]
        else "preflight: %d problem(s)" % result["problems"])


# ---------------------------------------------------------------------------
# Pipeline rendering (dry-run) and entry classification
# ---------------------------------------------------------------------------

# The declared per-stage options a dry-run label renders, in a fixed order so
# a label is stable whatever order the entry's author wrote its keys in.
# ``off``/``on`` renders the boolean options; the rest render their value.
_LABEL_OPTIONS = ("model", "subagent_model", "validator", "telemetry",
                  "parallelism", "disposition")
_LABEL_AUTOPILOT = ("attempts", "timeout", "max_resumes")


def _entry_options(entry):
    """The declared options of ``entry`` as ``"<key> <value>"`` fragments, in
    :data:`_LABEL_OPTIONS` then ``autopilot``-block order. Only declared keys
    appear — a bare entry yields none, so its label is unchanged."""
    parts = []
    for key in _LABEL_OPTIONS:
        if key not in entry:
            continue
        value = entry[key]
        if isinstance(value, bool):
            parts.append("%s %s" % (key, "on" if value else "off"))
        else:
            parts.append("%s %s" % (key, value))
    for key in _LABEL_AUTOPILOT:
        opts = entry.get("autopilot") or {}
        if key in opts:
            parts.append("%s %s" % (key, opts[key]))
    return parts


def _entry_label(entry):
    """A one-line human label for a resolved pipeline entry, rendering the
    entry's declared options (epic-autopilot stage-options-in-prompts) so the
    dry run shows them. Display only: the in-session drive reads its options
    from `spec_status.py pipeline-show --json`, never from these labels."""
    if "custom" in entry:
        base = "custom:%s -> %s" % (entry.get("custom"), entry.get("command"))
    else:
        stage = entry.get("stage")
        if entry.get("skip"):
            # A skipped stage carries no other option by schema.
            return "%s [skip]" % stage
        if "replace" in entry:
            rep = entry["replace"]
            target = rep.get("command") or ("tool:" + str(rep.get("tool")))
            base = "%s [replace -> %s, fallback %s]" % (
                stage, target, rep.get("fallback"))
        elif "tools" in entry:
            binds = ", ".join(
                "%s (fallback %s)" % (t.get("name"), t.get("fallback"))
                for t in entry["tools"])
            base = "%s [tools: %s]" % (stage, binds)
        else:
            base = stage
    options = _entry_options(entry)
    if options:
        return "%s [%s]" % (base, ", ".join(options))
    return base


# ---------------------------------------------------------------------------
# Default (production) seams — live sessions, the gate, and shell commands
# ---------------------------------------------------------------------------

def _run_command(cmd, cwd):
    """Run ``cmd`` (a list, or a string via the shell) in ``cwd``; return
    ``(returncode, stdout, stderr)``. A missing executable surfaces as a
    non-zero code rather than an exception."""
    shell = isinstance(cmd, str)
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, shell=shell, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return 127, "", str(exc)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _merged_into_base(command_fn, root, slug):
    """True when ``slug`` has merged into the base branch: the base branch's
    tree — ``origin/<base>`` where that ref resolves, else ``<base>``
    (``spec_status.DEFAULT_AMEND_BASE``) — holds a ``completed/`` entry named
    by a leading digits-and-dashes prefix then ``-<slug>``. Read with ``git
    ls-tree`` from ``root``; any git failure counts as not merged, so a stale
    or missing ref blocks a dependent rather than admitting it."""
    base = ss.DEFAULT_AMEND_BASE
    ref = None
    for candidate in ("origin/" + base, base):
        rc, _out, _err = command_fn(
            ["git", "rev-parse", "--verify", "--quiet", candidate], root)
        if rc == 0:
            ref = candidate
            break
    if ref is None:
        return False
    completed = os.path.relpath(
        os.path.join(sc.specs_dir(root), "completed"), root)
    completed = completed.replace(os.sep, "/") + "/"
    rc, out, _err = command_fn(
        ["git", "ls-tree", "--name-only", ref, "--", completed], root)
    if rc != 0:
        return False
    pattern = re.compile(r"^[0-9][0-9-]*-%s$" % re.escape(slug))
    return any(pattern.match(line.strip().rstrip("/").rsplit("/", 1)[-1])
               for line in out.splitlines() if line.strip())


def _default_gate_fn(member, cwd, base=None):
    """Run the context-sufficiency gate for ``member`` in ``cwd``; return its
    exit code (0 pass, 2 rejected, other error). ``base`` (when given) is
    appended as ``--base <base>`` so the stamp anchors on that ref."""
    cmd = [sys.executable, GATE_PY, member, "--root", cwd]
    if base:
        cmd += ["--base", base]
    rc, _out, _err = _run_command(cmd, cwd)
    return rc


def _plan_grade(cwd, member):
    def grade():
        if ss.read_status(cwd, member) != "ready":
            return False
        try:
            return not lint_change(cwd, member)
        except Exception:
            return False
    return grade


def _build_grade(cwd, member):
    def grade():
        completed = os.path.join(sc.specs_dir(cwd), "completed")
        archived = os.path.isdir(completed) and any(
            name.endswith("-" + member)
            for name in os.listdir(completed))
        if not archived:
            return False
        rc, out, _err = _run_command(
            ["gh", "pr", "view", "change/" + member,
             "--json", "url", "-q", ".url"], cwd)
        return rc == 0 and bool(out.strip())
    return grade


def _review_grade(cwd, member, command_fn=None):
    """The review stage passes iff **both** the member PR's head SHA carries a
    `semantic-review` commit status of state `success` (the gate the poster
    sets) **and** every gate-authored finding thread is dispositioned — i.e.
    `review_gate.py resolve --check` reports `unresolved=0`. A green status with
    dangling finding threads does not pass: the findings must be implemented or
    answered, not merged as ignored advice. Reads the head SHA via ``gh pr
    view`` and the combined status via the commits/{sha}/status API (gh fills
    the {owner}/{repo} template)."""
    cf = command_fn or _run_command

    def grade():
        rc, out, _err = cf(
            ["gh", "pr", "view", "change/" + member,
             "--json", "headRefOid", "-q", ".headRefOid"], cwd)
        sha = out.strip()
        if rc != 0 or not sha:
            return False
        rc, out, _err = cf(
            ["gh", "api", "repos/{owner}/{repo}/commits/%s/status" % sha], cwd)
        if rc != 0:
            return False
        try:
            data = json.loads(out)
        except (ValueError, TypeError):
            return False
        green = any(s.get("context") == "semantic-review"
                    and s.get("state") == "success"
                    for s in data.get("statuses", []))
        if not green:
            return False
        # Green is necessary but not sufficient: no gate thread may dangle.
        rc, out, _err = cf(
            [sys.executable, REVIEW_GATE_PY, "resolve",
             "change/" + member, "--check"], cwd)
        return rc == 0 and "unresolved=0" in out

    return grade


def _pr_url(command_fn, cwd, member):
    """Read the member branch's PR ``(url, merged)`` by running ``gh pr view``
    through ``command_fn`` in ``cwd`` (the repo root for a vanished worktree —
    ``gh`` needs any dir in the repo, never the deleted one)."""
    rc, out, _err = command_fn(
        ["gh", "pr", "view", "change/" + member,
         "--json", "url,state", "-q", "[.url, .state] | @tsv"], cwd)
    if rc != 0:
        return None, False
    parts = out.strip().split("\t")
    url = parts[0] if parts and parts[0] else None
    merged = len(parts) > 1 and parts[1].upper() == "MERGED"
    return url, merged


def _resolve_vanished(root, slug, last_session_id, stage, command_fn):
    """Resolve a member whose worktree vanished mid-run from the repo ``root``
    via its PR: a merged PR records an early ship (URL kept, remaining stages
    skipped); anything else (no PR, open PR, ``gh`` failure) parks the member as
    ``needs_human`` with a worktree-vanished reason and the last session id."""
    url, merged = _pr_url(command_fn, root, slug)
    if merged:
        return MemberResult(outcome="shipped", pr_url=url, merged=True)
    return MemberResult(
        outcome="needs_human", stage=stage,
        reason="worktree vanished mid-run", session_id=last_session_id)


def _make_session_fn(binary, harness, model_base=None):
    """Build the production session seam: drive a headless session in the
    selected ``harness`` for a stage and return ``(ok, session_id, failure)``
    where ``ok`` reflects the stage grade, not merely a clean exit.

    ``harness`` names the session driver's runner; ``binary`` overrides that
    runner's default executable. ``model`` (a concrete model id already
    resolved through :func:`spec_common.resolve_model_tier`) becomes the
    session's ``--model`` argument; ``None`` passes no flag, so the harness's
    own default decides."""
    def session_fn(stage, member, cwd, prompt, timeout, max_resumes,
                   on_session=None, effort=None):
        def runner(prompt_, cwd_, resume_id, turn_index,
                   timeout=TIMEOUT_DEFAULT):
            return session_driver.run_turn(
                prompt_, cwd_, resume_id=resume_id, timeout=timeout,
                harness=harness, binary=binary, effort=effort,
                plugin_dir=PLUGIN_DIR)

        if stage in ("plan", "enrich", "replan"):
            grade = _plan_grade(cwd, member)
        elif stage == "build":
            grade = _build_grade(cwd, member)
        elif stage == "review":
            grade = _review_grade(cwd, member)
        else:
            grade = lambda: True
        ok, session_id, failure = session_driver.drive(
            prompt, cwd, grade, GOAHEAD_REPLY,
            max_resumes=max_resumes, timeout=timeout, runner=runner,
            on_session=on_session)
        if not ok:
            return False, session_id, failure
        if not grade():
            return (False, session_id,
                    "%s grade unmet after %d resumes" % (stage, max_resumes))
        return True, session_id, None

    return session_fn


# ---------------------------------------------------------------------------
# Per-member driving
# ---------------------------------------------------------------------------

def _build_option_lines(entry, model_anchor):
    """The declared build options as prompt lines (epic-autopilot
    stage-options-in-prompts). Only declared keys produce a line, so a bare
    entry renders today's prompt unchanged. ``subagent_model`` resolves
    against ``model_anchor`` — the build session's own resolved model, falling
    back to the run's tier anchor — and is named as the concrete value with
    its symbolic provenance alongside."""
    lines = []
    if entry.get("validator") is False:
        lines.append("- Skip the adversarial validator phase: do not spawn the "
                     "`s:validator` sub-agent; the mechanical verification "
                     "still runs.")
    if entry.get("telemetry") is False:
        lines.append("- Skip the token telemetry: do not persist the per-tool "
                     "token breakdown and do not render the token report.")
    if entry.get("parallelism") is not None:
        lines.append("- Cap concurrent execution sub-agents at %s."
                     % entry["parallelism"])
    sub = entry.get("subagent_model")
    if sub:
        resolved = sub
        if resolved is None:
            lines.append("- Spawn execution sub-agents on this session's own "
                         "model (the pipeline's `session` tier).")
        elif resolved == sub:
            lines.append("- Spawn execution sub-agents with the Agent tool's "
                         "`model` set to `%s`." % resolved)
        else:
            lines.append("- Spawn execution sub-agents with the Agent tool's "
                         "`model` set to `%s` (the pipeline's `%s`)."
                         % (resolved, sub))
    if not lines:
        return ""
    return ("\n\nStage options for this build, overriding the skill's "
            "defaults:\n" + "\n".join(lines))


def _review_prompt(member, entry):
    """The review stage's prompt: the poster invocation carrying the entry's
    declared `--disposition`/`--model`, plus the disposition-loop paragraph
    matching the scope (epic-autopilot stage-options-in-prompts). The grade is
    unchanged in every scope — a green `semantic-review` status and
    `unresolved=0`."""
    poster_opts = ""
    if "disposition" in entry:
        poster_opts += " --disposition %s" % entry["disposition"]
    if entry.get("model"):
        poster_opts += " --model %s" % entry["model"]
    head = (
        "Post the semantic-review gate for the change `%s` and disposition "
        "its findings. Run /s:review on branch `change/%s` against `main` "
        "(merge-base semantics), then publish the verdict to the member's "
        "PR with the poster: emit the `--json` object to a temp file and "
        "run\n"
        "  python3 \"$CLAUDE_PLUGIN_ROOT/skills/review/scripts/"
        "review_gate.py\" post change/%s --from <that file>%s\n"
        "so the summary comment, anchored inline comments, and the "
        "`semantic-review` commit status all land on the PR's head SHA.\n"
        % (member, member, member, poster_opts))
    grade = ("Finish with `review_gate.py resolve change/%s` so every gate "
             "thread resolves; the stage is graded on the `semantic-review` "
             "status being green AND `resolve --check` reporting "
             "`unresolved=0`." % member)
    scope = entry.get("disposition", "all")
    if scope == "high-only":
        loop = (
            "Then run the disposition loop under the `high-only` scope: "
            "implement every high-severity finding (edit, commit, push, and "
            "re-review so the status tracks the new head), then dispose of "
            "the rest in one call — `review_gate.py autoreply change/%s "
            "--disposition high-only` — which posts the canonical policy "
            "reply onto every medium and low gate thread. " % member)
    elif scope == "none":
        loop = (
            "Then dispose of every posted finding by policy rather than by "
            "judgement: run `review_gate.py autoreply change/%s --disposition "
            "none`, which posts the canonical policy reply onto every gate "
            "thread; implement nothing. " % member)
    else:
        loop = (
            "Then run the disposition loop over every posted finding, low "
            "included: implement the suggestion (edit, commit, push, and "
            "re-review so the status tracks the new head) when it is correct, "
            "otherwise reply on the finding's thread with the concrete reason "
            "via `review_gate.py reply change/%s <comment-id> --body <reason>` "
            "— never leave a finding with neither. " % member)
    return head + loop + grade


def _stage_prompt(stage, member, entry, model_anchor=None, pr_mode="auto",
                  drift=None):
    """The prompt driving ``stage`` for ``member``, conveying the resolved
    ``entry``'s declared options (epic-autopilot stage-options-in-prompts).
    ``model_anchor`` is the anchor a declared `subagent_model` resolves
    against — the stage's own resolved model, falling back to the run's tier
    anchor. ``pr_mode`` is the run's resolved PR mode (shipd-config
    pr-mode-key): under ``draft`` the build stage names the draft-PR ship
    instead of the auto-merging one. An entry declaring no options renders
    today's prompt unchanged."""
    entry = entry or {}
    if stage == "plan":
        base = ("Run /s:plan for the change `%s` — a member of an approved "
                "epic. Investigate, spec it, and promote it to Status: ready."
                % member)
    elif stage == "build":
        ship = ("open its draft PR with `/s:pr --draft` (draft mode — do "
                "not enable auto-merge)"
                if pr_mode == "draft"
                else "open its auto-merging PR with `/s:pr`")
        base = ("Run /s:build for the change `%s`: implement every task, then "
                "merge and archive it and %s.\n\n"
                "If a sub-agent escalates a QUESTION: that the spec artifacts "
                "and code cannot answer, consult the oracle (run `%s`, "
                "then %s) before answering "
                "on your own authority; on INSUFFICIENT, answer with your own "
                "recommendation — never leave the sub-agent blocked."
                % (member, ship, ORACLE_LOOKUP_CMD, ORACLE_JUDGE_NOTE))
        base += _build_option_lines(entry, model_anchor)
    elif stage == "enrich":
        base = (
            "The context-sufficiency gate rejected the change `%s`. Run "
            "/s:plan %s — it locates the rejected change and enters "
            "enrichment mode. Resolve repository-answerable findings by "
            "editing the change's artifacts in place. For gaps the repository "
            "genuinely cannot answer, consult the oracle instead of a "
            "human — the session is unattended: run `%s` "
            "once per gap (the decision, the options, your "
            "recommendation) with this repo's root and %s; fold an ANSWER "
            "verdict in, "
            "and on INSUFFICIENT — or a failed lookup — adopt your own "
            "recommendation. Exit through the re-gate so the change returns to "
            "Status: ready, lint-clean."
            % (member, member, ORACLE_LOOKUP_CMD, ORACLE_JUDGE_NOTE))
    elif stage == "replan":
        base = _replan_prompt(member, drift or {})
    elif stage == "review":
        base = _review_prompt(member, entry)
    else:
        base = "Drive the `%s` stage for change `%s`." % (stage, member)
    tools = entry.get("tools")
    if tools:
        binds = "; ".join(
            "%s (fallback: %s)" % (t.get("name"), t.get("fallback"))
            for t in tools)
        base += ("\n\nPreferred tools for this stage, use when available: %s."
                 % binds)
    return base


def _command_action(command_fn, command, cwd):
    """A three-strike action that runs ``command`` in ``cwd`` via ``command_fn``,
    succeeding on exit 0."""
    def action(_attempt, _prev_failure):
        rc, out_text, err = command_fn(command, cwd)
        if rc == 0:
            return True, None, None
        return (False, None,
                "command exited %d: %s" % (rc, (err or out_text).strip()))
    return action


def _strike_loop(action, out, label, attempts=3, on_attempt=None):
    """Run ``action(attempt, prev_failure) -> (ok, session_id, failure)`` up to
    ``attempts`` times, appending the prior failure each retry.
    ``on_attempt(attempt)`` (when given) is called at the start of each attempt
    — the heartbeat hook. ``attempts`` is the entry's fresh-attempt budget
    (:func:`_stage_opts`), three unless the entry declares otherwise. Returns
    ``(ok, last_session_id, failure)``."""
    last_session_id = None
    failure = None
    for attempt in range(1, attempts + 1):
        if on_attempt is not None:
            on_attempt(attempt)
        ok, session_id, failure = action(attempt, failure)
        if session_id is not None:
            last_session_id = session_id
        if ok:
            return True, last_session_id, None
        out("  %s attempt %d/%d failed: %s"
            % (label, attempt, attempts, failure))
    return False, last_session_id, failure


def _stage_opts(entry, timeout, max_resumes):
    """The driver knobs for ``entry`` (epic-autopilot per-stage-driver-knobs):
    ``(attempts, timeout, max_resumes)`` read from its ``autopilot`` block,
    defaulting to three attempts and the run-global ``timeout`` /
    ``max_resumes`` when the block or a key is absent. Applies to stage,
    custom, and replacement entries alike. Pure."""
    opts = (entry or {}).get("autopilot") or {}
    attempts = opts.get("attempts")
    entry_timeout = opts.get("timeout")
    entry_resumes = opts.get("max_resumes")
    return (3 if attempts is None else attempts,
            timeout if entry_timeout is None else entry_timeout,
            max_resumes if entry_resumes is None else entry_resumes)


def _attempts_phrase(attempts):
    """``"3 attempts"`` / ``"1 attempt"`` — for reasons and log lines."""
    return "%d attempt%s" % (attempts, "" if attempts == 1 else "s")


def _anchor(session_model):
    """The model a stage declaring ``session`` inherits: the named
    ``session_model``, or ``None`` so the harness's own default decides.
    Printed in the dry run and recorded in the report so the anchor is never
    implicit."""
    return session_model or None


def _resolve_model_config(root):
    """``(models, model_base)`` the run's configuration declares: the
    per-level override map and the base a variant harness appends a level to.
    Both default to nothing, so an unconfigured repository needs no models."""
    config, _provenance = sc.resolve_config(root)
    return sc.resolve_models(config), sc.resolve_model_base(config)


# ---------------------------------------------------------------------------
# Pre-build drift step (epic-autopilot detached-pre-build-drift)
# ---------------------------------------------------------------------------

def _make_judge_fn(binary, harness, model_base=None):
    """Build the production judge seam: one headless turn returning
    ``(ok, session_id, failure, text)`` where ``text`` is the turn's
    result — the reply carrying ``/s:drift --json``'s one object.
    ``on_session`` fires with the session id when the turn yields one."""
    def judge_fn(member, cwd, prompt, timeout, model=None, on_session=None):
        ok, failure, session_id, text = session_driver.run_turn_result(
            prompt, cwd, timeout=timeout, harness=harness, binary=binary,
            effort=effort, model_base=model_base,
            plugin_dir=PLUGIN_DIR)
        if session_id is not None and on_session is not None:
            on_session(session_id)
        return ok, session_id, failure, text
    return judge_fn


def _sync_base_ref(command_fn, root):
    """Resolve the base ref the pre-build step syncs and measures against: a
    best-effort ``git fetch origin main`` from ``root`` (exit code ignored),
    then ``origin/main`` where it resolves, else ``main``
    (``spec_status.DEFAULT_AMEND_BASE``) — the rule :func:`_merged_into_base`
    uses."""
    base = ss.DEFAULT_AMEND_BASE
    command_fn(["git", "fetch", "origin", base], root)
    rc, _out, _err = command_fn(
        ["git", "rev-parse", "--verify", "--quiet", "origin/" + base], root)
    return "origin/" + base if rc == 0 else base


def _drift_prompt(member, base_ref):
    """The judge turn's prompt: run the drift skill and reply with its JSON."""
    return ("Run `/s:drift %s --base %s --json` for the change `%s` in this "
            "worktree and reply with exactly its JSON object — no fence, no "
            "prose. Edit no file, run no gate, open no question."
            % (member, base_ref, member))


def _parse_drift_verdict(text, member):
    """Parse the judge reply for ``member``. Tolerates a code fence or
    surrounding prose by reading the outermost braces. Returns ``"holds"`` for
    a member listed under ``clean``, else ``(verdict, reason, contradicts,
    revise)``. Raises :class:`ValueError` on unparseable text, an ``error``, a
    missing member entry, or an unknown verdict word."""
    text = text or ""
    lo, hi = text.find("{"), text.rfind("}")
    if lo < 0 or hi <= lo:
        raise ValueError("no JSON object in the judge reply")
    try:
        data = json.loads(text[lo:hi + 1])
    except ValueError as exc:
        raise ValueError("unparseable judge reply: %s" % exc)
    if not isinstance(data, dict):
        raise ValueError("judge reply is not a JSON object")
    if data.get("error"):
        raise ValueError("drift skill error: %s" % data["error"])
    if member in (data.get("clean") or []):
        return "holds"
    entry = next((v for v in (data.get("verdicts") or [])
                  if isinstance(v, dict) and v.get("member") == member), None)
    if entry is None:
        raise ValueError("no verdict for member '%s'" % member)
    verdict = entry.get("verdict")
    if verdict not in ("holds", "revise", "conflict"):
        raise ValueError("unknown verdict word: %r" % (verdict,))
    return (verdict, entry.get("reason"), entry.get("contradicts"),
            entry.get("revise"))


def _drift_summary(payload):
    """``"file-drift 2, symbol-gone 1"`` — the verb's finding kinds with
    counts, in first-seen order."""
    counts = {}
    for finding in (payload or {}).get("findings") or []:
        kind = finding.get("kind") if isinstance(finding, dict) else None
        if kind:
            counts[kind] = counts.get(kind, 0) + 1
    return ", ".join("%s %d" % (k, n) for k, n in counts.items())


def _replan_prompt(member, drift):
    """The re-plan session's prompt (``drift`` carries ``base_ref``,
    ``reason``, ``revise``, ``summary``, and optionally ``cwd``)."""
    ref = drift.get("base_ref") or ss.DEFAULT_AMEND_BASE
    return (
        "The plan for the change `%s` has drifted from `%s` since it was "
        "gated. Reason: %s\nRevise: %s\nDrift findings: %s\n\n"
        "Revise the installed artifacts (plan.md, delta specs, tasks.md) in "
        "place so they match the code now on `%s`. Keep every "
        "`**Answered by:** USER` answer and every epic Decision untouched. "
        "For decisions the repository cannot answer, consult the oracle "
        "instead of a human — run `%s` once per gap and %s; "
        "no human is present, so never wait for one. "
        "Finish by running `python3 %s %s --root %s --base %s` so the change "
        "returns to Status: ready, lint-clean."
        % (member, ref, drift.get("reason") or "(none given)",
           drift.get("revise") or "(none given)",
           drift.get("summary") or "(none)", ref, ORACLE_LOOKUP_CMD,
           ORACLE_JUDGE_NOTE, GATE_PY, member, drift.get("cwd") or ".", ref))


def _first_text_line(*texts):
    for text in texts:
        for line in (text or "").splitlines():
            if line.strip():
                return line.strip()
    return ""


def _pre_build_step(root, member, cwd, entry, knobs, command_fn, session_fn,
                    judge_fn, gate_fn, out, hook, on_sess):
    """Run the pre-build drift step before a built-in ``build`` stage: resolve
    the base ref, check ``After`` dependencies merged, merge the ref into the
    worktree, run the drift verb, judge drift with a headless ``/s:drift``,
    and re-plan and re-gate on ``revise``. ``knobs`` is ``(attempts, timeout,
    resumes, effort)`` from the build entry. Returns ``(outcome, stage, reason,
    session_id)`` with ``outcome`` in ``proceed``, ``needs_human``,
    ``rejected``."""
    slug = member.slug
    attempts, timeout, resumes, effort = knobs
    ref = _sync_base_ref(command_fn, root)

    waiting = [d for d in member.after
               if not _merged_into_base(command_fn, root, d)]
    if waiting:
        return ("needs_human", "dependency",
                "waiting on %s: not merged into %s; re-run with --member "
                "%s once merged" % (", ".join(waiting), ref, slug), None)

    rc, mout, merr = command_fn(["git", "merge", "--no-edit", ref], cwd)
    if rc != 0:
        command_fn(["git", "merge", "--abort"], cwd)
        return ("needs_human", "sync",
                "merge of %s failed: %s"
                % (ref, _first_text_line(mout, merr) or "exit %d" % rc), None)

    rc, vout, verr = command_fn(
        [sys.executable, STATUS_PY, "--root", cwd, "drift", slug,
         "--base", ref, "--json"], cwd)
    if rc == 0:
        out("  drift [clean]")
        return "proceed", None, None, None
    payload = None
    if rc == 4:
        try:
            payload = json.loads(vout)
        except (ValueError, TypeError):
            payload = None
    if rc != 4 or not isinstance(payload, dict):
        return ("needs_human", "drift",
                "drift verb exit %d: %s" % (rc, _first_text_line(verr, vout)),
                None)
    summary = _drift_summary(payload)
    out("  drift [%s] — judging" % summary)

    prompt = _drift_prompt(slug, ref)
    box = {}

    def judge_action(_attempt, _prev):
        ok, sid, failure, text = judge_fn(
            slug, cwd, prompt, timeout, effort=effort, on_session=on_sess)
        if not ok:
            return False, sid, failure
        try:
            box["verdict"] = _parse_drift_verdict(text, slug)
        except ValueError as exc:
            return False, sid, str(exc)
        return True, sid, None

    ok, judge_sid, failure = _strike_loop(
        judge_action, out, "drift", attempts=attempts,
        on_attempt=hook("drift"))
    if not ok:
        return ("needs_human", "drift",
                "drift judgment failed after %s: %s"
                % (_attempts_phrase(attempts), failure), judge_sid)
    verdict = box["verdict"]
    if verdict == "holds":
        out("  drift [holds]")
        return "proceed", None, None, judge_sid
    _word, reason, contradicts, revise = verdict
    if _word == "conflict":
        return ("needs_human", "drift",
                "plan conflicts with %s: %s" % (contradicts, reason),
                judge_sid)

    # revise: re-plan through the enrichment machinery, then re-gate.
    out("  drift [revise: %s] — re-planning" % reason)
    replan_prompt = _stage_prompt(
        "replan", slug, entry,
        drift={"base_ref": ref, "reason": reason, "revise": revise,
               "summary": summary, "cwd": cwd})

    def replan_action(_attempt, prev_failure):
        p = replan_prompt
        if prev_failure:
            p += ("\n\nA prior re-plan attempt failed: %s\nDiagnose and "
                  "finish revising the plan." % prev_failure)
        return session_fn("replan", slug, cwd, p, timeout, resumes,
                          on_session=on_sess, effort=effort)

    ok, sid, failure = _strike_loop(
        replan_action, out, "replan", attempts=attempts,
        on_attempt=hook("replan"))
    sid = sid or judge_sid
    if not ok:
        return ("needs_human", "replan",
                "drift re-plan failed after %s: %s"
                % (_attempts_phrase(attempts), failure), sid)
    if not os.path.isdir(cwd):
        return "proceed", None, None, sid
    verdict_g, greason = _run_gate(
        lambda m, c: gate_fn(m, c, base=ref), slug, cwd, attempts=attempts,
        on_attempt=hook("gate"))
    if verdict_g == "pass":
        out("  gate [passed after drift re-plan]")
        return "proceed", None, None, sid
    if verdict_g == "failed":
        return "needs_human", "replan", greason, sid
    return ("rejected", "replan",
            "context insufficient after drift re-plan (gate exit 2)", sid)


def drive_member(root, epic, member, pipeline, *, timeout=TIMEOUT_DEFAULT,
                 max_resumes=MAX_RESUMES_DEFAULT, binary=None, harness="claude",
                 session_model=None, models=None, model_base=None,
                 pr_mode=None, session_fn=None,
                 gate_fn=None, command_fn=None, judge_fn=None, out=_noop,
                 heartbeat=None):
    """Drive a single member through the resolved ``pipeline`` in its own
    worktree. Returns a :class:`MemberResult`.

    ``heartbeat`` is the run's :class:`heartbeat.RunHeartbeat` (or ``None`` for
    no live writes — the default, keeping existing callers unchanged). When
    present, this member's start, each stage attempt, and the outcome are
    recorded.

    ``session_model`` is the model a stage declaring ``session`` inherits
    (``None`` leaves the harness's own default in force). ``models`` is the
    per-level override map and ``model_base`` the base a variant harness
    appends a level to.

    ``pr_mode`` is the run's resolved PR mode (shipd-config pr-mode-key), which
    the callers resolve once per run and thread in; ``None`` resolves it from
    ``root`` here, so a direct caller still honors the configuration."""
    if command_fn is None:
        command_fn = _run_command
    if gate_fn is None:
        gate_fn = _default_gate_fn
    if session_fn is None:
        session_fn = _make_session_fn(binary, harness, model_base)
    if judge_fn is None:
        judge_fn = _make_judge_fn(binary, harness, model_base)
    if pr_mode is None:
        pr_mode = sc.resolve_pr_mode(root)

    slug = member.slug
    cwd = os.path.join(root, ".worktrees", slug)

    def _hook(label):
        if heartbeat is None:
            return None
        return lambda attempt: heartbeat.stage_started(slug, label, attempt)

    # Record the driven session's id on the roster entry the moment its first
    # turn yields one — a `driving` card then already carries a resume handle.
    on_sess = (None if heartbeat is None
               else lambda sid: heartbeat.member_session(slug, sid))

    def _finish(result):
        if heartbeat is not None:
            heartbeat.member_finished(slug, result)
        return result

    def _park(stage_label, reason):
        """Park a failed stage as needs-human — unless the worktree vanished,
        in which case resolve the member's true outcome from its PR."""
        if not os.path.isdir(cwd):
            return _finish(_resolve_vanished(
                root, slug, last_session_id, stage_label, command_fn))
        return _finish(MemberResult(
            outcome="needs_human", stage=stage_label, reason=reason,
            session_id=last_session_id))

    if heartbeat is not None:
        heartbeat.member_started(slug)
    out("Member %s (risk %s): creating worktree" % (slug, member.risk))
    rc, _o, err = command_fn([sys.executable, WORKTREE_PY, slug], root)
    if rc != 0 and "already exists" in err:
        # A dead run left the worktree/branch behind; reclaim before parking.
        # Guarded remove (activity guard disabled, every other guard in force),
        # merged-only branch delete, then one retried create. A guard refusal
        # or an unmerged-branch delete failure parks with that output as reason.
        branch = "change/%s" % slug
        out("  worktree exists — reclaiming stale leftover")
        if os.path.isdir(os.path.join(root, ".worktrees", slug)):
            rrc, rout, rerr = command_fn(
                ["env", "SHIPD_WORKTREE_IDLE_MINUTES=0", WORKTREE_SH,
                 "remove", slug], root)
            if rrc != 0:
                return _finish(MemberResult(
                    outcome="needs_human", stage="worktree",
                    reason="stale worktree remove refused: %s"
                           % (rerr.strip() or rout.strip() or rrc)))
        srrc, _sro, _sre = command_fn(
            ["git", "show-ref", "--verify", "--quiet",
             "refs/heads/%s" % branch], root)
        if srrc == 0:
            brc, bout, berr = command_fn(
                ["git", "branch", "-d", branch], root)
            if brc != 0:
                return _finish(MemberResult(
                    outcome="needs_human", stage="worktree",
                    reason="stale branch delete failed: %s"
                           % (berr.strip() or bout.strip() or brc)))
        rc, _o, err = command_fn([sys.executable, WORKTREE_PY, slug], root)
    if rc != 0:
        return _finish(MemberResult(
            outcome="needs_human", stage="worktree",
            reason="worktree creation failed: %s" % (err.strip() or rc)))

    last_session_id = None
    for entry in pipeline:
        # A driven session may legitimately remove this worktree while shipping
        # the member; resolve the outcome from the PR instead of driving on.
        if not os.path.isdir(cwd):
            return _finish(_resolve_vanished(
                root, slug, last_session_id,
                entry.get("stage") or entry.get("custom"), command_fn))

        # Every entry's own knobs: its fresh-attempt budget, the session
        # budgets its stage runs under (run-global unless declared), and the
        # model its sessions launch with (None -> the CLI default).
        attempts, entry_timeout, entry_resumes = _stage_opts(
            entry, timeout, max_resumes)
        entry_model = sc.resolve_effort(entry.get("stage"),
                                        entry.get("model"))
        entry_model = (models or {}).get(entry_model, entry_model)
        if entry_model == "session":
            entry_model = session_model

        # Custom step: run its command at this position in the worktree.
        if "custom" in entry:
            name = entry.get("custom")
            label = "custom:%s" % name
            ok, _sid, failure = _strike_loop(
                _command_action(command_fn, entry["command"], cwd),
                out, label, attempts=attempts, on_attempt=_hook(label))
            if not ok:
                return _park(label, failure)
            continue

        stage = entry.get("stage")
        if entry.get("skip"):
            out("  %s [skipped]" % stage)
            continue
        if stage in PRE_APPROVAL_STAGES:
            out("  %s [pre-approval, ignored]" % stage)
            continue

        # A replacement runs instead of any built-in behavior.
        if "replace" in entry:
            rep = entry["replace"]
            command = rep.get("command")
            if not command:
                out("  %s [replace has no command; skipped]" % stage)
                continue
            ok, _sid, failure = _strike_loop(
                _command_action(command_fn, command, cwd),
                out, "%s(replace)" % stage, attempts=attempts,
                on_attempt=_hook(stage))
            if not ok:
                return _park(stage, failure)
            continue

        # Built-in gate. A context rejection (exit 2) triggers the entry's
        # budget of oracle-backed enrichment attempts (a transient CLI/API
        # fault on one attempt must not permanently park the member), then a
        # deterministic re-gate whose verdict decides; other non-zero codes
        # keep needs-human semantics.
        if stage == "gate":
            verdict, reason = _run_gate(gate_fn, slug, cwd, attempts=attempts,
                                        on_attempt=_hook("gate"))
            if verdict == "pass":
                out("  gate [passed]")
                continue
            if verdict == "failed":
                return _park("gate", reason)

            # verdict == "rejected": up to the entry's budget of enrichment
            # attempts (each a fresh session — the change's artifacts are the
            # durable state and the re-gate is deterministic, so a fresh
            # attempt resumes from disk), then re-gate.
            out("  gate [rejected: %s] — oracle-backed enrichment "
                "(up to %s)" % (reason, _attempts_phrase(attempts)))
            enrich_prompt = _stage_prompt("enrich", slug, entry)

            def enrich_action(_attempt, prev_failure, _prompt=enrich_prompt,
                              _effort=entry_model):
                p = _prompt
                if prev_failure:
                    p = _prompt + ("\n\nA prior enrichment attempt failed: %s"
                                   "\nDiagnose and finish resolving the gate "
                                   "findings." % prev_failure)
                return session_fn("enrich", slug, cwd, p, entry_timeout,
                                  entry_resumes, on_session=on_sess,
                                  effort=_effort)

            ok, session_id, failure = _strike_loop(
                enrich_action, out, "enrich", attempts=attempts,
                on_attempt=_hook("enrich"))
            if session_id is not None:
                last_session_id = session_id
            if not ok:
                if not os.path.isdir(cwd):
                    return _finish(_resolve_vanished(
                        root, slug, last_session_id, "gate", command_fn))
                out("  enrichment failed after %s: %s"
                    % (_attempts_phrase(attempts), failure))
                return _finish(MemberResult(
                    outcome="rejected", stage="gate",
                    reason="context insufficient (gate exit 2); oracle "
                           "enrichment failed after %s: %s"
                           % (_attempts_phrase(attempts), failure),
                    session_id=last_session_id))
            # The session may have shipped the member and removed its worktree.
            if not os.path.isdir(cwd):
                return _finish(_resolve_vanished(
                    root, slug, last_session_id, "gate", command_fn))
            verdict, reason = _run_gate(gate_fn, slug, cwd, attempts=attempts,
                                        on_attempt=_hook("gate"))
            if verdict == "pass":
                out("  gate [passed after enrichment]")
                continue
            if verdict == "failed":
                return _park("gate", reason)
            out("  gate [rejected after enrichment]")
            return _finish(MemberResult(
                outcome="rejected", stage="gate",
                reason="context insufficient after oracle enrichment",
                session_id=last_session_id))

        # Built-in build: the pre-build drift step first (sync, dependency
        # check, drift verb, judgment, re-plan) — never for a skipped or
        # replaced entry, which is the whole stage.
        if stage == "build":
            outcome, step_stage, step_reason, step_sid = _pre_build_step(
                root, member, cwd, entry,
                (attempts, entry_timeout, entry_resumes, entry_model),
                command_fn, session_fn, judge_fn, gate_fn, out, _hook,
                on_sess)
            if step_sid is not None:
                last_session_id = step_sid
            if not os.path.isdir(cwd):
                return _finish(_resolve_vanished(
                    root, slug, last_session_id, "build", command_fn))
            if outcome == "needs_human" and step_stage == "dependency":
                # Waiting on an unmerged dependency is not a session to
                # resume: the park carries no session id.
                return _finish(MemberResult(
                    outcome="needs_human", stage=step_stage,
                    reason=step_reason))
            if outcome == "needs_human":
                return _park(step_stage, step_reason)
            if outcome == "rejected":
                return _finish(MemberResult(
                    outcome="rejected", stage=step_stage, reason=step_reason,
                    session_id=last_session_id))

        # Built-in plan / build: drive a graded headless session. A declared
        # `subagent_model` resolves against this stage's own model, falling
        # back to the run's anchor.
        prompt = _stage_prompt(stage, slug, entry,
                               entry_model, pr_mode=pr_mode)

        def action(_attempt, prev_failure, _stage=stage, _prompt=prompt,
                   _timeout=entry_timeout, _resumes=entry_resumes,
                   _effort=entry_model):
            p = _prompt
            if prev_failure:
                p = _prompt + ("\n\nA prior attempt failed: %s\nDiagnose and "
                               "finish the stage." % prev_failure)
            return session_fn(_stage, slug, cwd, p, _timeout, _resumes,
                              on_session=on_sess, effort=_effort)

        ok, session_id, failure = _strike_loop(action, out, stage,
                                               attempts=attempts,
                                               on_attempt=_hook(stage))
        if session_id is not None:
            last_session_id = session_id
        if not ok:
            return _park(stage, failure)
        out("  %s [ok]" % stage)

    # All stages passed: read the member's PR from the repo root. Under the
    # default `auto` mode the driven build waits for its own PR to merge before
    # returning (build-spec-lifecycle ship-changes-as-prs), so an unmerged PR
    # here means the ship stalled or timed out — park it rather than record a
    # false `shipped`. Under `draft` mode that premise is false: the ship's
    # terminal state *is* an open unmerged PR, so record it `drafted`. Either
    # way, no PR at all still parks at `merge`.
    url, merged = _pr_url(command_fn, root, slug)
    if merged:
        return _finish(MemberResult(outcome="shipped", pr_url=url, merged=True))
    if pr_mode == "draft" and url:
        return _finish(MemberResult(outcome="drafted", pr_url=url))
    return _finish(MemberResult(
        outcome="needs_human", stage="merge", pr_url=url,
        reason="pipeline completed but PR not merged: %s"
               % (url or "no PR found"),
        session_id=last_session_id))


# ---------------------------------------------------------------------------
# Targeted single-member drive
# ---------------------------------------------------------------------------

# A member's current lifecycle state maps to the pipeline stage a targeted
# drive enters at, skipping the stages already satisfied.
_ENTRY_STAGE = {"unplanned": "plan", "ready": "build"}


def entry_stage(member_state):
    """The pipeline stage a targeted drive enters at for a member in
    ``member_state``: ``unplanned`` -> ``plan``, ``ready`` -> ``build``. Any
    other state returns ``None`` (not drivable by a targeted drive). Pure."""
    return _ENTRY_STAGE.get(member_state)


def _pipeline_from_stage(pipeline, stage):
    """Return the resolved ``pipeline`` sliced to start at the first entry whose
    stage is ``stage`` — dropping the (already-satisfied) stages before it. When
    no entry matches, the whole pipeline is returned unchanged."""
    for i, entry in enumerate(pipeline):
        if entry.get("stage") == stage:
            return pipeline[i:]
    return pipeline


def drive_single_member(root, epic, slug, *, timeout=TIMEOUT_DEFAULT,
                        max_resumes=MAX_RESUMES_DEFAULT, binary=None, harness="claude",
                        session_model=None, models=None, model_base=None,
                        session_fn=None,
                        gate_fn=None,
                        command_fn=None, judge_fn=None, out=_noop,
                        heartbeat=None):
    """Drive exactly the one epic member named by ``slug`` — independent of the
    ``member-selection-and-order`` auto-selection — entering the resolved
    pipeline at the stage matching its current lifecycle (``unplanned`` ->
    ``plan``, ``ready`` -> ``build``), skipping the already-satisfied stages. Reuses ``drive_member``'s
    worktree, graded stage loop, heartbeat, and park/ship semantics, so it backs
    the board's per-card ``run`` action. Returns a :class:`MemberResult`.

    Raises :class:`AutopilotError` when ``slug`` is not an epic member or its
    state has no targeted entry stage (already in flight or archived)."""
    member = next((m for m in parse_members(root, epic) if m.slug == slug),
                  None)
    if member is None:
        raise AutopilotError(
            "member '%s' is not a change in epic '%s'" % (slug, epic))
    stage = entry_stage(member.state)
    if stage is None:
        raise AutopilotError(
            "member '%s' is %s — a targeted drive enters only an unplanned "
            "(plan) or ready (build) member" % (slug, member.state or "?"))
    pipeline, _provenance = sc.resolve_pipeline(root)
    sliced = _pipeline_from_stage(pipeline, stage)
    return drive_member(
        root, epic, member, sliced, timeout=timeout, max_resumes=max_resumes,
        binary=binary, harness=harness, session_model=session_model,
        models=models, model_base=model_base,
        pr_mode=sc.resolve_pr_mode(root), session_fn=session_fn,
        gate_fn=gate_fn, command_fn=command_fn, judge_fn=judge_fn, out=out,
        heartbeat=heartbeat)


def _run_gate(gate_fn, member, cwd, attempts=3, on_attempt=None):
    """Run the gate (exit 2 is a no-retry rejection); other non-zero codes are
    retried up to ``attempts`` times — the gate entry's fresh-attempt budget,
    three by default. ``on_attempt(attempt)`` (when given) is the heartbeat
    hook, called at the start of each attempt. Returns ``(verdict, reason)``
    where verdict is ``pass``, ``rejected``, or ``failed``."""
    reason = None
    for attempt in range(1, attempts + 1):
        if on_attempt is not None:
            on_attempt(attempt)
        rc = gate_fn(member, cwd)
        if rc == 0:
            return "pass", None
        if rc == 2:
            return "rejected", "context insufficient (gate exit 2)"
        reason = "gate exited %d" % rc
    return "failed", reason


# ---------------------------------------------------------------------------
# Run orchestration and reporting
# ---------------------------------------------------------------------------

def _default_sync_fn(root, epic, out):
    """Close out the epic after at least one PR merged: re-derive its status in
    a fresh worktree, exactly as the build skill's Phase 7 prescribes."""
    slug = "epic-close-%s" % epic
    # `--fresh`: the derivation must start from the base branch, never from a
    # stale local change/epic-close-<slug> branch an earlier run left behind.
    rc, _o, err = _run_command([WORKTREE_SH, slug, "--fresh"], root)
    if rc != 0:
        out("epic close-out skipped: worktree failed: %s" % (err.strip() or rc))
        return
    wt = os.path.join(root, ".worktrees", slug)
    rc, out_text, err = _run_command(
        [sys.executable, os.path.join(SCRIPTS_DIR, "spec_status.py"),
         "--root", wt, "epic-sync", epic], wt)
    out("epic-sync: %s" % (out_text.strip() or err.strip() or rc))
    if rc != 0:
        return
    st_rc, porcelain, _st_err = _run_command(
        ["git", "status", "--porcelain"], wt)
    if st_rc != 0:
        return
    if porcelain.strip():
        out("epic close-out wrote a status change; ship it from %s" % wt)
        return
    rm_rc, _rm_out, rm_err = _run_command(
        ["git", "worktree", "remove", wt], root)
    if rm_rc == 0:
        _run_command(["git", "branch", "-D", "change/%s" % slug], root)
    else:
        out("epic close-out cleanup failed: %s" % (rm_err.strip() or rm_rc))


def _write_report(root, epic, report):
    path = os.path.join(sc.specs_dir(root), "autopilot", "%s-report.json" % epic)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    return path


def _summarize(report, out):
    out("")
    out("=== autopilot report: %s ===" % report["epic"])
    for r in report["shipped"]:
        out("shipped:    %s  %s" % (r["member"], r.get("pr_url") or "(no PR url)"))
    # `drafted` is read defensively: a report dict written before the bucket
    # existed still summarizes.
    for r in report.get("drafted") or []:
        out("drafted:    %s  %s"
            % (r["member"], r.get("pr_url") or "(no PR url)"))
    for r in report["rejected"]:
        line = "rejected:   %s  [%s] %s" % (r["member"], r["stage"], r["reason"])
        if r.get("session_id"):
            line += "  -> claude --resume %s" % r["session_id"]
        out(line)
    for r in report["needs_human"]:
        line = "needs-human: %s  [%s] %s" % (
            r["member"], r["stage"], r["reason"])
        if r.get("session_id"):
            line += "  -> claude --resume %s" % r["session_id"]
        out(line)
    for r in report["skipped"]:
        out("skipped:    %s  (%s)" % (r["member"], r["state"]))
    for r in report["unreached"]:
        out("unreached:  %s" % r["member"])


def _terminate_process(signum):
    """Re-raise ``signum``'s default disposition on this process: restore the
    default handler and re-send the signal to self. Called by an installed
    ``SIGTERM`` handler after its guarded heartbeat write, so the process
    still actually terminates on ``SIGTERM`` (its default disposition)
    instead of hanging until a later ``SIGKILL`` — a private, module-level
    seam so tests can stub out the real self-signal."""
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


class _SigtermAbortGuard:
    """Installs a ``SIGTERM`` handler for the duration of a run: on receipt,
    writes ``hb``'s terminal ``aborted`` state (guarded by the same
    ``finished`` flag the caller's ``try/finally`` uses, so a signal arriving
    after the clean finish never overwrites it) and re-raises the signal's
    default disposition. Restores whatever handler was previously installed
    when the guard exits, so a nested or subsequent run is unaffected."""

    def __init__(self, hb, is_finished):
        self._hb = hb
        self._is_finished = is_finished
        self._prev_handler = None

    def _on_sigterm(self, signum, _frame):
        if not self._is_finished():
            self._hb.run_aborted()
        _terminate_process(signum)

    def __enter__(self):
        self._prev_handler = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, self._on_sigterm)
        return self

    def __exit__(self, exc_type, exc, tb):
        signal.signal(signal.SIGTERM, self._prev_handler)
        return False


def run(root, epic, *, max_members=None, dry_run=False,
        timeout=TIMEOUT_DEFAULT, max_resumes=MAX_RESUMES_DEFAULT,
        binary=None, harness="claude", session_model=None, models=None,
        model_base=None,
        member_driver=None,
        sync_fn=None, heartbeat=None, out=print):
    """Drive ``epic``'s unplanned members and return the run report dict.

    ``member_driver`` and ``sync_fn`` are injectable seams (defaults do live
    work). ``dry_run`` prints the member order and resolved pipeline and drives
    nothing — and writes no heartbeat. ``heartbeat`` is an injectable
    :class:`heartbeat.RunHeartbeat` seam; when ``None`` a live one is
    constructed for a real run (never for ``--dry-run``). ``session_model`` is
    the model a ``session`` stage inherits (``None`` uses the harness's own
    default)."""
    if not os.path.isfile(_epic_file(root, epic)):
        raise AutopilotError("epic '%s' not found under %s"
                             % (epic, sc.specs_dir(root)))
    status = ss.read_epic_status(root, epic)
    if status not in ("ready", "active"):
        raise AutopilotError(
            "epic '%s' is %s, not ready/active — approve it first"
            % (epic, status or "unapproved"))

    members = parse_members(root, epic)
    to_drive, skipped = select_and_order(members)
    pipeline, provenance = sc.resolve_pipeline(root)
    # Resolved once per run and threaded into every member drive, so a bad
    # `pr-mode` value fails the run before any member is driven.
    pr_mode = sc.resolve_pr_mode(root)
    if models is None:
        models, model_base = _resolve_model_config(root)

    report = {
        "epic": epic,
        "pipeline_source": provenance,
        "harness": harness,
        "session_model": session_model,
        "models": models or {},
        "model_base": model_base,
        "stage_effort": dict(sc.STAGE_EFFORT),
        "shipped": [],
        "drafted": [],
        "rejected": [],
        "needs_human": [],
        "skipped": [{"member": m.slug, "state": m.state} for m in skipped],
        "unreached": [],
    }

    if dry_run:
        out("Dry run for epic '%s' (pipeline from %s):" % (epic, provenance))
        out("Model tier anchor: %s%s"
            % (_anchor(session_model) or "(the harness's own default)",
               "" if session_model else " (--session-model names another)"))
        out("Stage levels: %s" % ", ".join(
            "%s: %s" % (stage, level)
            for stage, level in sorted(sc.STAGE_EFFORT.items())))
        out("Harness: %s" % harness)
        out("Member order (After, then risk ascending):")
        for m in to_drive:
            out("  %s (risk %s)" % (m.slug, m.risk or "?"))
        out("Resolved pipeline:")
        for entry in pipeline:
            out("  - %s" % _entry_label(entry))
        _summarize(report, out)
        return report

    if member_driver is None:
        def member_driver(root_, epic_, member_, pipeline_, heartbeat_=None):
            return drive_member(
                root_, epic_, member_, pipeline_, timeout=timeout,
                max_resumes=max_resumes, binary=binary, harness=harness,
                session_model=session_model, models=models,
                model_base=model_base, pr_mode=pr_mode,
                out=out,
                heartbeat=heartbeat_)

    reached = to_drive if max_members is None else to_drive[:max_members]
    report["unreached"] = [{"member": m.slug} for m in to_drive[len(reached):]]

    hb = heartbeat if heartbeat is not None else RunHeartbeat(
        root, epic, out=out)
    hb.run_started(reached, skipped, provenance)

    any_merged = False
    finished = False
    outcomes = {}
    with _SigtermAbortGuard(hb, lambda: finished):
        try:
            for member in reached:
                waiting = [(d, outcomes[d]) for d in member.after
                           if d in outcomes and outcomes[d] != "shipped"]
                if waiting:
                    result = MemberResult(
                        outcome="needs_human", stage="dependency",
                        reason="waiting on %s" % ", ".join(
                            "%s (%s)" % w for w in waiting))
                    hb.member_finished(member.slug, result)
                    out("Member %s: not driven — %s"
                        % (member.slug, result.reason))
                else:
                    result = member_driver(root, epic, member, pipeline, hb)
                outcomes[member.slug] = result.outcome
                if result.outcome == "shipped":
                    report["shipped"].append(
                        {"member": member.slug, "pr_url": result.pr_url})
                    any_merged = any_merged or result.merged
                elif result.outcome == "drafted":
                    # An open draft PR is a terminal success, never a merge:
                    # `any_merged` stays keyed off actual merges, so a
                    # draft-only run runs no epic-sync close-out.
                    report["drafted"].append(
                        {"member": member.slug, "pr_url": result.pr_url})
                elif result.outcome == "rejected":
                    report["rejected"].append(
                        {"member": member.slug, "stage": result.stage,
                         "reason": result.reason,
                         "session_id": result.session_id})
                else:  # needs_human
                    report["needs_human"].append(
                        {"member": member.slug, "stage": result.stage,
                         "reason": result.reason,
                         "session_id": result.session_id})

            path = _write_report(root, epic, report)
            hb.run_finished(path)
            finished = True
        finally:
            # A catchably-terminated run (AutopilotError, KeyboardInterrupt)
            # never reaches the clean run_finished write above; write a
            # terminal aborted state so the heartbeat doesn't freeze at
            # "running". Never overwrites a clean finish. A received SIGTERM
            # rides the same guard via _SigtermAbortGuard above.
            if not finished:
                hb.run_aborted()

    _summarize(report, out)
    out("report written: %s" % path)

    if any_merged:
        (sync_fn or _default_sync_fn)(root, epic, out)

    return report


def run_member(root, epic, slug, *, timeout=TIMEOUT_DEFAULT,
               max_resumes=MAX_RESUMES_DEFAULT, binary=None, harness="claude",
               session_model=None, models=None, model_base=None, driver=None,
               heartbeat=None,
               out=print):
    """Targeted drive of a single epic member with a live heartbeat and run
    report — the board-observable wrapper the detached ``run`` action spawns.
    Seeds the epic heartbeat with just this member, drives it via
    :func:`drive_single_member`, then writes a one-member report and finishes
    the heartbeat. ``driver`` is an injectable seam (the default does live
    work). Returns the :class:`MemberResult`."""
    if not os.path.isfile(_epic_file(root, epic)):
        raise AutopilotError("epic '%s' not found under %s"
                             % (epic, sc.specs_dir(root)))
    member = next((m for m in parse_members(root, epic) if m.slug == slug),
                  None)
    if member is None:
        raise AutopilotError(
            "member '%s' is not a change in epic '%s'" % (slug, epic))
    if entry_stage(member.state) is None:
        raise AutopilotError(
            "member '%s' is %s — a targeted drive enters only an unplanned "
            "(plan) or ready (build) member" % (slug, member.state or "?"))
    _pipeline, provenance = sc.resolve_pipeline(root)
    if models is None:
        models, model_base = _resolve_model_config(root)

    hb = heartbeat if heartbeat is not None else RunHeartbeat(
        root, epic, out=out)
    hb.run_started([member], [], provenance)

    if driver is None:
        def driver():
            return drive_single_member(
                root, epic, slug, timeout=timeout, max_resumes=max_resumes,
                binary=binary, harness=harness, session_model=session_model,
                models=models, model_base=model_base, out=out,
                heartbeat=hb)

    finished = False
    with _SigtermAbortGuard(hb, lambda: finished):
        try:
            result = driver()

            report = {
                "epic": epic,
                "pipeline_source": provenance,
                "harness": harness,
                "session_model": session_model,
                "models": models or {},
                "model_base": model_base,
                "stage_effort": dict(sc.STAGE_EFFORT),
                "shipped": [],
                "drafted": [],
                "rejected": [],
                "needs_human": [],
                "skipped": [],
                "unreached": [],
            }
            if result.outcome == "shipped":
                report["shipped"].append(
                    {"member": slug, "pr_url": result.pr_url})
            elif result.outcome == "drafted":
                report["drafted"].append(
                    {"member": slug, "pr_url": result.pr_url})
            elif result.outcome == "rejected":
                report["rejected"].append(
                    {"member": slug, "stage": result.stage,
                     "reason": result.reason, "session_id": result.session_id})
            else:  # needs_human
                report["needs_human"].append(
                    {"member": slug, "stage": result.stage,
                     "reason": result.reason, "session_id": result.session_id})

            path = _write_report(root, epic, report)
            hb.run_finished(path)
            finished = True
        finally:
            # See the matching comment in `run`: a catchable abnormal exit
            # (including a received SIGTERM, via _SigtermAbortGuard above)
            # never reaches the clean run_finished write, so write a terminal
            # aborted state instead, and never overwrite a clean finish.
            if not finished:
                hb.run_aborted()

    _summarize(report, out)
    out("report written: %s" % path)
    return result


def _print_waves(result, as_json=False, out=print):
    """Render :func:`compute_waves`'s result — one JSON object for a machine
    reader, else one ``wave <index> [<stage>]:`` line per wave naming its members
    (a build wave's members carry their capabilities), one ``blocked:`` line
    per ready member waiting on an unmerged ``After`` dependency, and one
    ``skipped:`` line per undrivable member."""
    if as_json:
        out(json.dumps(result))
        return
    out("Waves for epic '%s' (cap %d):" % (result["epic"], result["parallel"]))
    for wave in result["waves"]:
        parts = []
        for member in wave["members"]:
            if wave["stage"] == "build":
                detail = " ".join(member["capabilities"])
            else:
                detail = "risk %s" % member["risk"]
                if member.get("after"):
                    detail += ", after %s" % ", ".join(member["after"])
            parts.append("%s (%s)" % (member["slug"], detail))
        out("  wave %d [%s]: %s"
            % (wave["index"], wave["stage"], ", ".join(parts)))
    for entry in result.get("blocked", []):
        out("  blocked: %s (waiting on %s)"
            % (entry["member"], ", ".join(entry["waiting_on"])))
    for entry in result["skipped"]:
        out("  skipped: %s (%s)" % (entry["member"], entry["state"]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Drive an approved epic's unplanned members to shipped PRs.")
    parser.add_argument("epic", help="the epic slug to deliver")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repository root (default: cwd)")
    parser.add_argument("--member", default=None,
                        help="drive only this one member (a targeted "
                             "single-member drive), backing the board run action")
    parser.add_argument("--max-members", type=int, default=None,
                        help="drive at most N members (default: unlimited)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print member order + resolved pipeline; drive nothing")
    parser.add_argument("--waves", action="store_true",
                        help="print the waves the in-session drive may run "
                             "concurrently; drive nothing")
    parser.add_argument("--preflight", action="store_true",
                        help="print the launch rubric (ok|warn|fail per "
                             "check); drive nothing")
    parser.add_argument("--parallel", type=int, default=3,
                        help="how many members one wave may hold "
                             "(default: 3; 1 is a serial walk)")
    parser.add_argument("--json", action="store_true",
                        help="with --waves or --preflight, print one JSON object")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_DEFAULT,
                        help="per-session wall-clock budget in seconds")
    parser.add_argument("--max-resumes", type=int, default=MAX_RESUMES_DEFAULT,
                        help="resumed turns per session before the grade decides")
    parser.add_argument("--harness", default=session_driver.DEFAULT_HARNESS,
                        help="the harness to drive headless sessions in "
                             "(default: %s)" % session_driver.DEFAULT_HARNESS)
    parser.add_argument("--claude-bin", default=None,
                        help="the harness CLI binary to invoke (default: the "
                             "selected harness's own)")
    parser.add_argument("--session-model", default=None,
                        help="the model a stage declaring `session` inherits "
                             "(default: the harness's own)")
    args = parser.parse_args(argv)

    if args.parallel < 1:
        parser.error("--parallel must be at least 1")
    if args.waves and (args.dry_run or args.member):
        parser.error("--waves drives nothing; it cannot be combined with "
                     "--dry-run or --member")

    if args.preflight and (args.waves or args.dry_run or args.member):
        parser.error("--preflight drives nothing; it cannot be combined "
                     "with --waves, --dry-run or --member")

    try:
        if args.preflight:
            result = compute_preflight(os.path.abspath(args.root), args.epic)
            _print_preflight(result, as_json=args.json)
            return 1 if result["failed"] else 0
        if args.waves:
            _print_waves(
                compute_waves(os.path.abspath(args.root), args.epic,
                              args.parallel),
                as_json=args.json)
        elif args.member:
            run_member(os.path.abspath(args.root), args.epic, args.member,
                       timeout=args.timeout, max_resumes=args.max_resumes,
                       binary=args.claude_bin, harness=args.harness,
                       session_model=args.session_model)
        else:
            run(os.path.abspath(args.root), args.epic,
                max_members=args.max_members, dry_run=args.dry_run,
                timeout=args.timeout, max_resumes=args.max_resumes,
                binary=args.claude_bin, harness=args.harness,
                session_model=args.session_model)
    except AutopilotError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
