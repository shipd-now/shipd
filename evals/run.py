#!/usr/bin/env python3
"""run.py — local eval harness for the s plugin's LLM-facing skills.

Each eval *case* is a directory under ``evals/cases/<name>/`` holding a
``prompt.md`` (the request handed to a headless Claude Code session) and a
``fixture/`` (a minimal repo tree with a ``.shipd/`` layout). For every run the
harness copies the fixture to a scratch directory, launches a real headless
session against the working tree's plugin (``--plugin-dir``), and grades the
result with the host repo's own ``spec_lint.py`` plus a couple of structural
assertions.

The runner is Python 3 standard library only (no third-party imports, no
network beyond the ``claude`` subprocess it spawns), matching the repo's
stdlib-only engine constraint. Its discovery, grading, and aggregation logic
are unit-tested under ``evals/tests/`` without a live session.
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

# The host repository root — two directories up from this file
# (``evals/run.py`` → ``evals/`` → repo root). The live plugin and the
# ``spec_lint.py`` oracle are located relative to this.
HOST_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(HOST_REPO, "evals", "cases")

# The plugin's build scripts host the shared session driver (the grade-gated
# resume loop) and the ``spec_lint.py`` grading oracle. Path-insert that dir so
# the turn/resume loop is imported rather than re-implemented here.
SCRIPTS_DIR = os.path.join(
    HOST_REPO, "plugins", "s", "skills", "build", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import session_driver  # noqa: E402


@dataclasses.dataclass
class Case:
    """A discovered eval case."""
    name: str
    prompt_path: str
    fixture_path: str


@dataclasses.dataclass
class RunResult:
    """The graded outcome of a single case run. ``failure`` names the first
    failing assertion, or is ``None`` when the run passed."""
    passed: bool
    failure: str | None = None


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

def discover_cases(cases_dir, case_filter=None):
    """Return the sorted list of :class:`Case` under ``cases_dir``.

    A directory qualifies as a case only when it contains both a ``prompt.md``
    file and a ``fixture/`` subdirectory; anything else is skipped silently.
    When ``case_filter`` is given, only the case of that exact name is
    returned (an empty list if it does not exist or does not qualify).
    """
    if not os.path.isdir(cases_dir):
        return []
    cases = []
    for name in sorted(os.listdir(cases_dir)):
        if case_filter is not None and name != case_filter:
            continue
        case_dir = os.path.join(cases_dir, name)
        if not os.path.isdir(case_dir):
            continue
        prompt_path = os.path.join(case_dir, "prompt.md")
        fixture_path = os.path.join(case_dir, "fixture")
        if not os.path.isfile(prompt_path):
            continue
        if not os.path.isdir(fixture_path):
            continue
        cases.append(Case(name=name, prompt_path=prompt_path,
                          fixture_path=fixture_path))
    return cases


# ---------------------------------------------------------------------------
# Scratch assembly
# ---------------------------------------------------------------------------

def _git(scratch, *args):
    """Run a git command inside ``scratch``, raising on failure."""
    subprocess.run(
        ["git", *args], cwd=scratch, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def assemble_scratch(case, host_repo=HOST_REPO):
    """Build an isolated scratch copy of a case's fixture and return its path.

    The fixture tree is copied to a fresh ``tempfile.mkdtemp`` directory, the
    fixture's ``.shipd/README.md`` is overwritten with the host repo's copy (the
    grammar authority must not drift inside a fixture), and the scratch dir is
    turned into a git repo with a single baseline commit so the session sees a
    clean working tree.
    """
    scratch = tempfile.mkdtemp(prefix="s-eval-%s-" % case.name)
    # Copy the fixture contents into the (already-created) scratch root.
    for entry in os.listdir(case.fixture_path):
        src = os.path.join(case.fixture_path, entry)
        dst = os.path.join(scratch, entry)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # The host repo's .shipd/README.md is the single grammar authority; overwrite
    # whatever placeholder the fixture shipped so sessions plan against the
    # real format guide.
    host_readme = os.path.join(host_repo, ".shipd", "README.md")
    scratch_readme = os.path.join(scratch, ".shipd", "README.md")
    os.makedirs(os.path.dirname(scratch_readme), exist_ok=True)
    shutil.copy2(host_readme, scratch_readme)

    _git(scratch, "init", "-q")
    _git(scratch, "add", "-A")
    _git(scratch,
         "-c", "user.email=eval@shipd.local",
         "-c", "user.name=s eval",
         "commit", "-q", "-m", "fixture baseline")
    return scratch


# ---------------------------------------------------------------------------
# Headless session invocation
# ---------------------------------------------------------------------------

# A generous ceiling: a real /s:plan session investigates the fixture and
# emits several artifacts, and each can take minutes.
SESSION_TIMEOUT_SECONDS = 20 * 60
TRANSCRIPT_NAME = "eval-transcript.json"

# The plan skill's findings checkpoint (the go-ahead prompt) no longer fires —
# a digest whose readiness attestation holds proceeds straight through
# emission in the same turn. What still stops the skill for the user is a
# genuine typed decision round (an OPEN QUESTIONS ending, a depth-path grill
# round, or a fast-path question round). Headless runs answer every such stop
# with this one generic reply — accept the session's own recommendations and
# drive to a gradable terminal state — though a clean case is now expected to
# reach a gradable state on the first turn, with no resume needed.
GOAHEAD_REPLY = (
    "Proceed. For any open question or decision, now or in later rounds, "
    "take the option you yourself recommend. Complete the plan through "
    "emission, lint, and promotion to ready.")

# How many resumed turns a run may spend answering stops before the
# structural grade decides the outcome.
MAX_RESUMES_DEFAULT = 4


# The session-id extraction lives in the shared driver; kept aliased here under
# the historical name for callers and tests that reference it.
_session_id_from_transcript = session_driver.session_id_from_transcript


def _run_turn(prompt, scratch, resume_id=None, turn_index=1,
              claude_bin="claude", host_repo=HOST_REPO,
              timeout=SESSION_TIMEOUT_SECONDS):
    """Run one turn of a headless Claude Code conversation inside ``scratch``.

    Launches ``<claude_bin> -p <prompt> --plugin-dir <host>/plugins/s
    --permission-mode bypassPermissions --output-format json`` with the scratch
    directory as cwd — plus ``--resume <resume_id>`` when continuing an
    existing session. The captured stdout is written to
    ``<scratch>/eval-transcript.json`` for turn 1 and
    ``eval-transcript-turn<N>.json`` for resumed turns.

    Returns ``(ok, failure, session_id)``: ``ok`` is True only when the CLI
    exits 0 within ``timeout``; ``session_id`` is parsed from the turn's JSON
    transcript (``None`` when unavailable).
    """
    plugin_dir = os.path.join(host_repo, "plugins", "s")
    cmd = [claude_bin, "-p", prompt,
           "--plugin-dir", plugin_dir,
           "--permission-mode", "bypassPermissions",
           "--output-format", "json"]
    if resume_id is not None:
        cmd += ["--resume", resume_id]
    name = (TRANSCRIPT_NAME if turn_index == 1
            else "eval-transcript-turn%d.json" % turn_index)
    transcript_path = os.path.join(scratch, name)
    try:
        proc = subprocess.run(
            cmd, cwd=scratch, timeout=timeout, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired as exc:
        _write_text(transcript_path, exc.stdout or "")
        return False, "session timed out after %d s" % timeout, None
    _write_text(transcript_path, proc.stdout or "")
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else ""
        return (False, "session CLI exited %d: %s" % (proc.returncode, tail),
                None)
    return True, None, _session_id_from_transcript(proc.stdout or "")


def run_conversation(case, scratch, claude_bin="claude", host_repo=HOST_REPO,
                     timeout=SESSION_TIMEOUT_SECONDS,
                     max_resumes=MAX_RESUMES_DEFAULT, turn_runner=None):
    """Drive ``case`` as a bounded headless conversation inside ``scratch``.

    Turn 1 sends the case prompt. The plan skill's findings checkpoint (the
    go-ahead prompt) no longer fires, so a clean case is expected to reach a
    gradable state on the first turn. Afterwards, while :func:`grade` has not
    passed and fewer than ``max_resumes`` resumed turns have run, the same
    session is resumed with :data:`GOAHEAD_REPLY` — answering only genuine
    typed decision rounds (an OPEN QUESTIONS ending, a depth-path grill round,
    or a fast-path question round) by accepting the session's own
    recommendations. Resuming stops early when a turn yields no session id
    (the final grade then decides the run).

    Returns ``(ok, failure)``: ``ok`` is False only when a turn itself failed
    (timeout / non-zero exit); grading verdicts are the caller's job.
    """
    with open(case.prompt_path, encoding="utf-8") as fh:
        prompt = fh.read()

    if turn_runner is not None:
        runner = turn_runner
    else:
        # The live turn function needs the eval-specific plugin dir and
        # transcript writing, so bind those and adapt to the driver's runner
        # contract (``timeout`` arrives as a keyword from :func:`drive`).
        def runner(prompt_, cwd, resume_id, turn_index, **kwargs):
            return _run_turn(
                prompt_, cwd, resume_id, turn_index,
                claude_bin=claude_bin, host_repo=host_repo, timeout=timeout)

    ok, _session_id, failure = session_driver.drive(
        prompt, scratch, lambda: grade(scratch, host_repo=host_repo).passed,
        GOAHEAD_REPLY, max_resumes=max_resumes, timeout=timeout, runner=runner)
    return ok, failure


def _write_text(path, text):
    # The scratch dir can be disturbed by the session it hosts (a bypass-
    # permissions session runs arbitrary commands in its own cwd), so recreate
    # the parent before writing rather than crashing the whole eval.
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# Deterministic structural grading
# ---------------------------------------------------------------------------

_STATUS_RE = re.compile(r"^Status:\s*(.*)$")


def _plan_status(plan_path):
    """Return the ``Status:`` value from a plan.md (the first match among the
    first five non-blank lines), or ``None`` if absent/unreadable."""
    try:
        with open(plan_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    non_blank = [ln.strip() for ln in text.splitlines() if ln.strip()][:5]
    for line in non_blank:
        m = _STATUS_RE.match(line)
        if m:
            return m.group(1).strip()
    return None


@dataclasses.dataclass
class _Candidate:
    """A discovered change directory and the tree it lives in. ``root`` is the
    path ``spec_lint.py --root`` and the ``plan.md`` read must target — the
    scratch root for a root change, the containing worktree for a worktree
    change."""
    name: str
    change_dir: str
    root: str


def _collect_candidates(scratch_dir):
    """Return the changes the workflow may leave, across both sanctioned
    storage locations: the scratch root's ``.shipd/planned/`` and one level of
    ``.worktrees/*/.shipd/planned/``.

    Each returned :class:`_Candidate` carries the tree (``root``) it lints
    against, so a worktree change is graded against its own branch's tree
    rather than the scratch root. The list is sorted by change directory path
    for stable, diagnosable failure messages.
    """
    candidates = []
    root_glob = os.path.join(scratch_dir, ".shipd", "planned", "*")
    for change_dir in glob.glob(root_glob):
        if os.path.isdir(change_dir):
            candidates.append(_Candidate(
                name=os.path.basename(change_dir),
                change_dir=change_dir, root=scratch_dir))
    wt_glob = os.path.join(
        scratch_dir, ".worktrees", "*", ".shipd", "planned", "*")
    for change_dir in glob.glob(wt_glob):
        if os.path.isdir(change_dir):
            # ``.worktrees/<wt>/.shipd/planned/<change>`` → the worktree root is
            # three levels up from the change directory.
            worktree = os.path.dirname(os.path.dirname(
                os.path.dirname(change_dir)))
            candidates.append(_Candidate(
                name=os.path.basename(change_dir),
                change_dir=change_dir, root=worktree))
    candidates.sort(key=lambda c: c.change_dir)
    return candidates


def grade(scratch_dir, host_repo=HOST_REPO):
    """Grade a completed session's scratch repo with three structural
    assertions and return a :class:`RunResult`.

    A run passes only if all hold, in order: exactly one change directory
    exists across the two sanctioned storage locations — the scratch root's
    ``.shipd/planned/`` and one level of ``.worktrees/*/.shipd/planned/``; the host
    repo's ``spec_lint.py`` exits 0 for that change against the tree it lives
    in (the scratch root, or the containing worktree); and the change's
    ``plan.md`` carries ``Status: ready``. The first failing assertion is named
    in ``RunResult.failure``, which names the inspected locations.
    """
    candidates = _collect_candidates(scratch_dir)

    if not candidates:
        return RunResult(
            False, "no change directory under .shipd/planned/ "
                   "(scratch root or worktrees)")
    if len(candidates) != 1:
        paths = ", ".join(
            os.path.relpath(c.change_dir, scratch_dir) for c in candidates)
        return RunResult(
            False, "expected exactly one change under .shipd/planned/ (scratch "
                   "root or worktrees), found %d (%s)"
                   % (len(candidates), paths))
    candidate = candidates[0]
    location = os.path.relpath(candidate.change_dir, scratch_dir)

    lint = os.path.join(host_repo, "plugins", "s", "skills", "build",
                        "scripts", "spec_lint.py")
    proc = subprocess.run(
        [sys.executable, lint, candidate.name, "--root", candidate.root],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        return RunResult(
            False, "spec_lint failed for change '%s' at %s:\n%s"
                   % (candidate.name, location, proc.stdout.strip()))

    plan_path = os.path.join(candidate.change_dir, "plan.md")
    status = _plan_status(plan_path)
    if status != "ready":
        return RunResult(
            False, "plan.md Status at %s is %r, expected 'ready'"
                   % (location, status))

    return RunResult(True, None)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Run s skill eval cases as headless Claude Code sessions "
                    "and grade the result structurally.")
    parser.add_argument(
        "--case", default=None,
        help="run only the named case (default: all discovered cases)")
    parser.add_argument(
        "--runs", type=int, default=1,
        help="repeat each case N times (default: 1)")
    parser.add_argument(
        "--claude-bin", default="claude",
        help="the Claude Code CLI binary to invoke (default: claude)")
    parser.add_argument(
        "--keep-scratch", action="store_true",
        help="retain each run's scratch directory for inspection")
    parser.add_argument(
        "--max-resumes", type=int, default=MAX_RESUMES_DEFAULT,
        help="maximum resumed turns spent answering a session's stops "
             "(default: %d; 0 restores single-shot behavior)"
             % MAX_RESUMES_DEFAULT)
    return parser


def execute_case(case, runs, claude_bin, keep_scratch,
                 max_resumes=MAX_RESUMES_DEFAULT):
    """Run ``case`` ``runs`` times, returning the list of :class:`RunResult`.

    Each run assembles a fresh scratch repo, drives the headless conversation
    (initial turn plus bounded go-ahead resumes), and grades it (a failed
    turn short-circuits to a failed run without grading). Scratch dirs are
    removed afterward unless ``keep_scratch``.
    """
    results = []
    for i in range(1, runs + 1):
        scratch = assemble_scratch(case)
        try:
            try:
                ok, failure = run_conversation(
                    case, scratch, claude_bin=claude_bin,
                    max_resumes=max_resumes)
                result = RunResult(False, failure) if not ok else grade(scratch)
            except Exception as exc:  # noqa: BLE001 — one bad run must not
                # abort the whole eval; record it as failed and continue.
                result = RunResult(False, "harness error: %s" % exc)
            results.append(result)
            if result.passed:
                print("  [%s %d/%d] PASS" % (case.name, i, runs))
            else:
                first = (result.failure or "").splitlines()
                print("  [%s %d/%d] FAIL — %s"
                      % (case.name, i, runs, first[0] if first else ""))
        finally:
            if keep_scratch:
                print("    scratch kept: %s" % scratch)
            else:
                shutil.rmtree(scratch, ignore_errors=True)
    return results


def summarize(results):
    """Build the per-case pass-rate summary from ``results`` (a mapping of case
    name to its list of :class:`RunResult`). Returns ``(lines, exit_code)``;
    ``exit_code`` is 0 only when every executed case passed every run, else 1.
    """
    lines = []
    all_perfect = bool(results)
    for name in sorted(results):
        runs = results[name]
        passed = sum(1 for r in runs if r.passed)
        total = len(runs)
        lines.append("%-32s %d/%d" % (name, passed, total))
        if passed < total:
            all_perfect = False
            for i, r in enumerate(runs, 1):
                if not r.passed:
                    first = (r.failure or "").splitlines()
                    lines.append("    run %d failed: %s"
                                 % (i, first[0] if first else ""))
    return lines, (0 if all_perfect else 1)


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    cases = discover_cases(CASES_DIR, case_filter=args.case)
    if not cases:
        where = args.case or CASES_DIR
        print("no eval cases found (%s)" % where)
        return 1
    results = {}
    for case in cases:
        plural = "" if args.runs == 1 else "s"
        print("== case: %s (%d run%s) ==" % (case.name, args.runs, plural))
        results[case.name] = execute_case(
            case, args.runs, args.claude_bin, args.keep_scratch,
            max_resumes=args.max_resumes)
    print()
    print("Summary:")
    lines, exit_code = summarize(results)
    for ln in lines:
        print("  " + ln)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
