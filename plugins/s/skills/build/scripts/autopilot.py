#!/usr/bin/env python3
"""autopilot.py — the epic autopilot: plan → gate → build → PR, per member.

Given an approved epic (``ready`` or ``active``), the autopilot drives its
unplanned member changes to shipped PRs without human interaction. Members are
selected and ordered risk-ascending; each is driven through the resolved
``autonomous-pipeline`` (skips, replacements, custom steps honored) in its own
worktree/branch. Gate rejections park a member for human enrichment; other
stage failures get re-driven up to the entry's fresh-attempt budget (its
``autopilot.attempts``, three by default) before parking the member as
``needs-human`` with a resumable session id. Every run ends with a report —
machine-readable JSON plus a human summary.

Standard library only. Live sessions, the gate, and external commands are all
reached through injectable seams so the orchestration is unit-testable without
spending model time.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import signal
import subprocess
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from heartbeat import RunHeartbeat  # noqa: E402
import session_driver  # noqa: E402
import spec_common as sc  # noqa: E402
import spec_status as ss  # noqa: E402
from spec_lint import lint_change  # noqa: E402

# The plugin root (``plugins/am``), four directories up from this script, is the
# ``--plugin-dir`` handed to driven sessions so ``/s:*`` skills load.
PLUGIN_DIR = os.path.normpath(os.path.join(SCRIPTS_DIR, "..", "..", ".."))
WORKTREE_SH = os.path.join(SCRIPTS_DIR, "worktree.sh")
GATE_PY = os.path.join(SCRIPTS_DIR, "spec_gate.py")
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
GOAHEAD_REPLY = (
    "Proceed. For any undecided point or decision, now or in later rounds: "
    "shape it into a compact question (the decision, the options, your "
    "recommendation) and consult the ask-mikk oracle by spawning agent "
    "`s:oracle` with that question and this repo's root; adopt its ANSWER, "
    "and on INSUFFICIENT — or if the oracle is unavailable — take the option "
    "you yourself recommend. Never wait for a human. Complete the work through "
    "to its terminal state.")


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


@dataclasses.dataclass
class MemberResult:
    """The outcome of driving one member. ``outcome`` is one of ``shipped``,
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
        header, rows = sc.parse_epic_changes(fh.read())
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
            state=ss._member_state(root, slug), order=order))
    return members


def select_and_order(members):
    """Split ``members`` into ``(to_drive, skipped)``. ``to_drive`` is the
    ``unplanned`` members ordered by Risk ascending (``low`` < ``medium`` <
    ``high``), ties broken by table order; ``skipped`` is every other member,
    left in table order under its state."""
    to_drive = sorted(
        (m for m in members if m.state == "unplanned"),
        key=lambda m: (RISK_RANK.get(m.risk, len(RISK_RANK)), m.order))
    skipped = [m for m in members if m.state != "unplanned"]
    return to_drive, skipped


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
    dry run — which the in-session drive parses — shows them."""
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


def _default_gate_fn(member, cwd):
    """Run the context-sufficiency gate for ``member`` in ``cwd``; return its
    exit code (0 pass, 2 rejected, other error)."""
    rc, _out, _err = _run_command(
        [sys.executable, GATE_PY, member, "--root", cwd], cwd)
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


def _make_session_fn(claude_bin):
    """Build the production session seam: drive a headless ``claude`` session
    for a stage and return ``(ok, session_id, failure)`` where ``ok`` reflects
    the stage grade, not merely a clean exit.

    ``model`` (a concrete model id already resolved through
    :func:`spec_common.resolve_model_tier`) becomes the session's ``--model``
    argument; ``None`` passes no flag, so the CLI's own default decides."""
    base_extra = ["--plugin-dir", PLUGIN_DIR,
                  "--permission-mode", "bypassPermissions"]

    def session_fn(stage, member, cwd, prompt, timeout, max_resumes,
                   on_session=None, model=None):
        extra = list(base_extra)
        if model:
            extra += ["--model", model]

        def runner(prompt_, cwd_, resume_id, turn_index,
                   timeout=TIMEOUT_DEFAULT):
            return session_driver.run_turn(
                prompt_, cwd_, resume_id=resume_id, timeout=timeout,
                claude_bin=claude_bin, extra_args=extra)

        if stage == "plan" or stage == "enrich":
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
        resolved = sc.resolve_model_tier(sub, model_anchor)
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


def _stage_prompt(stage, member, entry, model_anchor=None):
    """The prompt driving ``stage`` for ``member``, conveying the resolved
    ``entry``'s declared options (epic-autopilot stage-options-in-prompts).
    ``model_anchor`` is the anchor a declared `subagent_model` resolves
    against — the stage's own resolved model, falling back to the run's tier
    anchor. An entry declaring no options renders today's prompt unchanged."""
    entry = entry or {}
    if stage == "plan":
        base = ("Run /s:plan for the change `%s` — a member of an approved "
                "epic. Investigate, spec it, and promote it to Status: ready."
                % member)
    elif stage == "build":
        base = ("Run /s:build for the change `%s`: implement every task, then "
                "merge and archive it and open its auto-merging PR.\n\n"
                "If a sub-agent escalates a QUESTION: that the spec artifacts "
                "and code cannot answer, consult the ask-mikk oracle (spawn "
                "agent `s:oracle` with a compact question) before answering "
                "on your own authority; on INSUFFICIENT, answer with your own "
                "recommendation — never leave the sub-agent blocked." % member)
        base += _build_option_lines(entry, model_anchor)
    elif stage == "enrich":
        base = (
            "The context-sufficiency gate rejected the change `%s`. Run "
            "/s:plan %s — it locates the rejected change and enters "
            "enrichment mode. Resolve repository-answerable findings by "
            "editing the change's artifacts in place. For gaps the repository "
            "genuinely cannot answer, consult the ask-mikk oracle instead of a "
            "human — the session is unattended: spawn agent `s:oracle` with "
            "one compact question per gap (the decision, the options, your "
            "recommendation) and this repo's root; fold an ANSWER verdict in, "
            "and on INSUFFICIENT — or an unavailable oracle — adopt your own "
            "recommendation. Exit through the re-gate so the change returns to "
            "Status: ready, lint-clean." % (member, member))
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


def _tier_anchor(session_model):
    """The anchor a run's symbolic tiers actually resolve against: the named
    ``session_model``, or the ladder top when none was named. Printed in the
    dry run and recorded in the report so the anchor is never implicit."""
    return session_model or sc.MODEL_LADDER[0]


def drive_member(root, epic, member, pipeline, *, timeout=TIMEOUT_DEFAULT,
                 max_resumes=MAX_RESUMES_DEFAULT, claude_bin="claude",
                 session_model=None, session_fn=None, gate_fn=None,
                 command_fn=None, out=_noop, heartbeat=None):
    """Drive a single member through the resolved ``pipeline`` in its own
    worktree. Returns a :class:`MemberResult`.

    ``heartbeat`` is the run's :class:`heartbeat.RunHeartbeat` (or ``None`` for
    no live writes — the default, keeping existing callers unchanged). When
    present, this member's start, each stage attempt, and the outcome are
    recorded.

    ``session_model`` is the run's model-tier anchor: every entry's declared
    ``model`` resolves against it through
    :func:`spec_common.resolve_model_tier` (``None`` anchors at the ladder
    top)."""
    if command_fn is None:
        command_fn = _run_command
    if gate_fn is None:
        gate_fn = _default_gate_fn
    if session_fn is None:
        session_fn = _make_session_fn(claude_bin)

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
    rc, _o, err = command_fn([WORKTREE_SH, slug], root)
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
        rc, _o, err = command_fn([WORKTREE_SH, slug], root)
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
        entry_model = sc.resolve_model_tier(entry.get("model"), session_model)

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
                              _model=entry_model):
                p = _prompt
                if prev_failure:
                    p = _prompt + ("\n\nA prior enrichment attempt failed: %s"
                                   "\nDiagnose and finish resolving the gate "
                                   "findings." % prev_failure)
                return session_fn("enrich", slug, cwd, p, entry_timeout,
                                  entry_resumes, on_session=on_sess,
                                  model=_model)

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

        # Built-in plan / build: drive a graded headless session. A declared
        # `subagent_model` resolves against this stage's own model, falling
        # back to the run's anchor.
        prompt = _stage_prompt(stage, slug, entry,
                               entry_model or session_model)

        def action(_attempt, prev_failure, _stage=stage, _prompt=prompt,
                   _timeout=entry_timeout, _resumes=entry_resumes,
                   _model=entry_model):
            p = _prompt
            if prev_failure:
                p = _prompt + ("\n\nA prior attempt failed: %s\nDiagnose and "
                               "finish the stage." % prev_failure)
            return session_fn(_stage, slug, cwd, p, _timeout, _resumes,
                              on_session=on_sess, model=_model)

        ok, session_id, failure = _strike_loop(action, out, stage,
                                               attempts=attempts,
                                               on_attempt=_hook(stage))
        if session_id is not None:
            last_session_id = session_id
        if not ok:
            return _park(stage, failure)
        out("  %s [ok]" % stage)

    # All stages passed: read the member's PR from the repo root. Because the
    # driven build waits for its own PR to merge before returning
    # (build-spec-lifecycle ship-changes-as-prs), an unmerged PR here means the
    # ship stalled or timed out — park it rather than record a false `shipped`.
    url, merged = _pr_url(command_fn, root, slug)
    if merged:
        return _finish(MemberResult(outcome="shipped", pr_url=url, merged=True))
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
                        max_resumes=MAX_RESUMES_DEFAULT, claude_bin="claude",
                        session_model=None, session_fn=None, gate_fn=None,
                        command_fn=None, out=_noop, heartbeat=None):
    """Drive exactly the one epic member named by ``slug`` — independent of the
    risk-ascending auto-selection — entering the resolved pipeline at the stage
    matching its current lifecycle (``unplanned`` -> ``plan``, ``ready`` ->
    ``build``), skipping the already-satisfied stages. Reuses ``drive_member``'s
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
        claude_bin=claude_bin, session_model=session_model,
        session_fn=session_fn, gate_fn=gate_fn, command_fn=command_fn,
        out=out, heartbeat=heartbeat)


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
    rc, _o, err = _run_command([WORKTREE_SH, slug], root)
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
        claude_bin="claude", session_model=None, member_driver=None,
        sync_fn=None, heartbeat=None, out=print):
    """Drive ``epic``'s unplanned members and return the run report dict.

    ``member_driver`` and ``sync_fn`` are injectable seams (defaults do live
    work). ``dry_run`` prints the member order and resolved pipeline and drives
    nothing — and writes no heartbeat. ``heartbeat`` is an injectable
    :class:`heartbeat.RunHeartbeat` seam; when ``None`` a live one is
    constructed for a real run (never for ``--dry-run``). ``session_model`` is
    the run's model-tier anchor (``None`` anchors at the ladder top)."""
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

    report = {
        "epic": epic,
        "pipeline_source": provenance,
        "tier_anchor": _tier_anchor(session_model),
        "shipped": [],
        "rejected": [],
        "needs_human": [],
        "skipped": [{"member": m.slug, "state": m.state} for m in skipped],
        "unreached": [],
    }

    if dry_run:
        out("Dry run for epic '%s' (pipeline from %s):" % (epic, provenance))
        out("Model tier anchor: %s%s"
            % (_tier_anchor(session_model),
               "" if session_model else " (ladder top; --session-model "
                                        "names another)"))
        out("Member order (risk ascending):")
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
                max_resumes=max_resumes, claude_bin=claude_bin,
                session_model=session_model, out=out, heartbeat=heartbeat_)

    reached = to_drive if max_members is None else to_drive[:max_members]
    report["unreached"] = [{"member": m.slug} for m in to_drive[len(reached):]]

    hb = heartbeat if heartbeat is not None else RunHeartbeat(
        root, epic, out=out)
    hb.run_started(reached, skipped, provenance)

    any_merged = False
    finished = False
    with _SigtermAbortGuard(hb, lambda: finished):
        try:
            for member in reached:
                result = member_driver(root, epic, member, pipeline, hb)
                if result.outcome == "shipped":
                    report["shipped"].append(
                        {"member": member.slug, "pr_url": result.pr_url})
                    any_merged = any_merged or result.merged
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
               max_resumes=MAX_RESUMES_DEFAULT, claude_bin="claude",
               session_model=None, driver=None, heartbeat=None, out=print):
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

    hb = heartbeat if heartbeat is not None else RunHeartbeat(
        root, epic, out=out)
    hb.run_started([member], [], provenance)

    if driver is None:
        def driver():
            return drive_single_member(
                root, epic, slug, timeout=timeout, max_resumes=max_resumes,
                claude_bin=claude_bin, session_model=session_model, out=out,
                heartbeat=hb)

    finished = False
    with _SigtermAbortGuard(hb, lambda: finished):
        try:
            result = driver()

            report = {
                "epic": epic,
                "pipeline_source": provenance,
                "tier_anchor": _tier_anchor(session_model),
                "shipped": [],
                "rejected": [],
                "needs_human": [],
                "skipped": [],
                "unreached": [],
            }
            if result.outcome == "shipped":
                report["shipped"].append(
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
    parser.add_argument("--timeout", type=int, default=TIMEOUT_DEFAULT,
                        help="per-session wall-clock budget in seconds")
    parser.add_argument("--max-resumes", type=int, default=MAX_RESUMES_DEFAULT,
                        help="resumed turns per session before the grade decides")
    parser.add_argument("--claude-bin", default="claude",
                        help="the Claude Code CLI binary to invoke")
    parser.add_argument("--session-model", default=None,
                        help="the model-tier anchor a stage's symbolic `model` "
                             "resolves against (default: the ladder top, %s)"
                             % sc.MODEL_LADDER[0])
    args = parser.parse_args(argv)

    try:
        if args.member:
            run_member(os.path.abspath(args.root), args.epic, args.member,
                       timeout=args.timeout, max_resumes=args.max_resumes,
                       claude_bin=args.claude_bin,
                       session_model=args.session_model)
        else:
            run(os.path.abspath(args.root), args.epic,
                max_members=args.max_members, dry_run=args.dry_run,
                timeout=args.timeout, max_resumes=args.max_resumes,
                claude_bin=args.claude_bin,
                session_model=args.session_model)
    except AutopilotError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
