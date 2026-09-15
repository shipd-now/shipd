#!/usr/bin/env python3
"""run.py — local eval harness for the s plugin's LLM-facing skills.

Each eval *case* is a directory under ``evals/cases/<name>/`` holding a
``prompt.md`` (the request handed to a headless Claude Code session) and a
``fixture/`` (a minimal repo tree with a ``.shipd/`` layout). For every run the
harness copies the fixture to a scratch directory and launches a real
headless session against the working tree's plugin (``--plugin-dir``). Which
grader then judges the result is selected per case by an optional
``expect.json`` (``{"grader": ...}``, default ``"structural"``):

- ``"structural"`` (:func:`grade`) — grades a spec-authoring session against
  the host repo's own ``spec_lint.py`` plus a couple of structural
  assertions (one change directory, lint-clean, ``Status: ready``).
- ``"behavior"`` (:func:`grade_behavior`) — grades whether the produced
  software actually works, against a held-out oracle: the case's
  ``verify/`` tree, kept out of the session-visible ``fixture/`` and copied
  into the scratch repo's ``tests/`` only after the session ends, alongside
  the shipped ``fixture/tests/`` tree restored over any session edit.
  :func:`check_behavior_fixture` sanity-checks that oracle before a session
  is even spawned.

The runner is Python 3 standard library only (no third-party imports, no
network beyond the ``claude`` subprocess it spawns), matching the repo's
stdlib-only engine constraint. Its discovery, grading, and aggregation logic
are unit-tested under ``evals/tests/`` without a live session.
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import json
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
    grader: str = "structural"


@dataclasses.dataclass
class RunResult:
    """The graded outcome of a single case run. ``failure`` names the first
    failing assertion, or is ``None`` when the run passed. ``refused`` is
    True when the run was turned away before any session spawned — a
    baseline-bearing arm refused for a structural case or an unparseable
    ``prompt.md`` — as opposed to a baseline arm that genuinely ran and
    failed, which is an expected, informative outcome and not a refusal."""
    passed: bool
    failure: str | None = None
    refused: bool = False


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

RECOGNIZED_GRADERS = ("structural", "behavior")


def read_expect(case_dir):
    """Return the grader name a case's ``expect.json`` selects.

    An absent ``expect.json``, or one present without a ``grader`` key,
    selects ``"structural"``. A file declaring ``{"grader": "behavior"}``
    selects ``"behavior"``. Raises :class:`ValueError`, naming the case
    (``os.path.basename(case_dir)``) and the offending value, when the file
    is unreadable (missing/invalid JSON) or declares a grader outside
    :data:`RECOGNIZED_GRADERS`.
    """
    name = os.path.basename(case_dir.rstrip(os.sep))
    expect_path = os.path.join(case_dir, "expect.json")
    if not os.path.isfile(expect_path):
        return "structural"
    try:
        with open(expect_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ValueError(
            "case '%s': expect.json is unreadable: %s" % (name, exc))
    if not isinstance(data, dict):
        raise ValueError(
            "case '%s': expect.json must be a JSON object" % name)
    grader = data.get("grader", "structural")
    if grader not in RECOGNIZED_GRADERS:
        raise ValueError(
            "case '%s': unrecognized grader %r in expect.json"
            % (name, grader))
    return grader


def discover_cases(cases_dir, case_filter=None):
    """Return the sorted list of :class:`Case` under ``cases_dir``.

    A directory qualifies as a case only when it contains both a ``prompt.md``
    file and a ``fixture/`` subdirectory; anything else is skipped silently.
    When ``case_filter`` is given, only the case of that exact name is
    returned (an empty list if it does not exist or does not qualify). Each
    returned case's ``grader`` is populated from the case directory's
    ``expect.json`` via :func:`read_expect`. A case whose ``expect.json`` is
    unreadable or names an unrecognized grader is not dropped from discovery
    (dropping it would silently skip its runs rather than failing them); its
    ``grader`` field instead carries :func:`read_expect`'s ``ValueError``
    message verbatim — already naming the case and the offending value — so
    ``execute_case`` can fail its runs with that message without spawning a
    session.
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
        try:
            grader = read_expect(case_dir)
        except ValueError as exc:
            grader = str(exc)
        cases.append(Case(name=name, prompt_path=prompt_path,
                          fixture_path=fixture_path, grader=grader))
    return cases


# ---------------------------------------------------------------------------
# Derived baseline prompt
# ---------------------------------------------------------------------------

_SKILL_TOKEN_RE = re.compile(r"^/s:([A-Za-z0-9_-]+)(\s|$)")


def baseline_prompt(text):
    """Derive a baseline run's prompt from a case's ``prompt.md`` text.

    Strips a leading ``/s:<skill>`` token from the first line and returns the
    remainder of the text verbatim (the rest of that first line, plus every
    following line unchanged), so both arms receive identical wording. Raises
    :class:`ValueError`, naming the offending first line, when it carries no
    such leading token.
    """
    lines = text.splitlines(keepends=True)
    first = lines[0] if lines else ""
    m = _SKILL_TOKEN_RE.match(first)
    if not m:
        raise ValueError(
            "prompt does not open with a '/s:<skill>' token: %r"
            % (first.strip(),))
    return first[m.end():] + "".join(lines[1:])


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

# The skill-neutral counterpart for a behavior-graded case: it answers a
# stop the same way (accept the session's own recommendation and keep
# going), but carries no mention of emitting, linting, or promoting a
# change — that instruction is specific to /s:plan's artifact, and a
# behavior case may be driving any skill (e.g. /s:fix) toward a working
# fix instead.
BEHAVIOR_GOAHEAD_REPLY = (
    "Proceed. For any open question or decision, now or in later rounds, "
    "take the option you yourself recommend.")

# How many resumed turns a run may spend answering stops before the grade
# decides the outcome.
MAX_RESUMES_DEFAULT = 4


# The session-id extraction lives in the shared driver; kept aliased here under
# the historical name for callers and tests that reference it.
_session_id_from_transcript = session_driver.session_id_from_transcript


def _run_turn(prompt, scratch, resume_id=None, turn_index=1,
              claude_bin="claude", host_repo=HOST_REPO,
              timeout=SESSION_TIMEOUT_SECONDS, arm="treatment"):
    """Run one turn of a headless Claude Code conversation inside ``scratch``.

    Launches ``<claude_bin> -p <prompt> --plugin-dir <host>/plugins/s
    --permission-mode bypassPermissions --output-format json`` with the scratch
    directory as cwd — plus ``--resume <resume_id>`` when continuing an
    existing session. Under ``arm="baseline"``, the ``--plugin-dir`` pair is
    omitted and nothing else about the command changes — the session runs
    with no plugin loaded. The captured stdout is written to
    ``<scratch>/eval-transcript.json`` for turn 1 and
    ``eval-transcript-turn<N>.json`` for resumed turns.

    Returns ``(ok, failure, session_id)``: ``ok`` is True only when the CLI
    exits 0 within ``timeout``; ``session_id`` is parsed from the turn's JSON
    transcript (``None`` when unavailable).
    """
    cmd = [claude_bin, "-p", prompt]
    if arm != "baseline":
        plugin_dir = os.path.join(host_repo, "plugins", "s")
        cmd += ["--plugin-dir", plugin_dir]
    cmd += ["--permission-mode", "bypassPermissions",
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


def _behavior_gate_passed(case, scratch):
    """Evaluate the behavior grade for the resume gate without disturbing the
    scratch tree the session is still operating in.

    Copies ``scratch`` to a throwaway directory and grades that copy with
    :func:`grade_behavior`, so probing the gate mid-conversation never copies
    the case's held-out ``verify/`` tree into the working tree itself.
    """
    throwaway = tempfile.mkdtemp(prefix="s-eval-gate-%s-" % case.name)
    try:
        shutil.copytree(scratch, throwaway, dirs_exist_ok=True)
        return grade_behavior(case, throwaway).passed
    finally:
        shutil.rmtree(throwaway, ignore_errors=True)


def run_conversation(case, scratch, claude_bin="claude", host_repo=HOST_REPO,
                     timeout=SESSION_TIMEOUT_SECONDS,
                     max_resumes=MAX_RESUMES_DEFAULT, turn_runner=None,
                     arm="treatment"):
    """Drive ``case`` as a bounded headless conversation inside ``scratch``.

    Turn 1 sends the case prompt — :func:`baseline_prompt` of it under
    ``arm="baseline"``, unmodified under ``arm="treatment"``. Afterwards,
    while the case's gate has not passed and fewer than ``max_resumes``
    resumed turns have run, the same session is resumed with the case's
    reply. Both are selected from ``case.grader``: a structural case (the
    default) keeps the existing :func:`grade` gate and :data:`GOAHEAD_REPLY`
    — the plan skill's findings checkpoint no longer fires, so a clean case
    is expected to reach a gradable state on the first turn, and any resume
    only answers a genuine typed decision round (an OPEN QUESTIONS ending, a
    depth-path grill round, or a fast-path question round) by accepting the
    session's own recommendations. A behavior case instead gates on
    :func:`_behavior_gate_passed` (the behavior grade evaluated against a
    throwaway copy of ``scratch``, never ``scratch`` itself) and sends
    :data:`BEHAVIOR_GOAHEAD_REPLY`, which carries no emission/lint/promotion
    instruction specific to /s:plan's artifact. Resuming stops early when a
    turn yields no session id (the final grade then decides the run).

    Returns ``(ok, failure)``: ``ok`` is False only when a turn itself failed
    (timeout / non-zero exit); grading verdicts are the caller's job.
    """
    with open(case.prompt_path, encoding="utf-8") as fh:
        prompt = fh.read()
    if arm == "baseline":
        prompt = baseline_prompt(prompt)

    if turn_runner is not None:
        runner = turn_runner
    else:
        # The live turn function needs the eval-specific plugin dir and
        # transcript writing, so bind those and adapt to the driver's runner
        # contract (``timeout`` arrives as a keyword from :func:`drive`).
        # ``arm`` threads through so a baseline run's turns omit
        # ``--plugin-dir``.
        def runner(prompt_, cwd, resume_id, turn_index, **kwargs):
            return _run_turn(
                prompt_, cwd, resume_id, turn_index,
                claude_bin=claude_bin, host_repo=host_repo, timeout=timeout,
                arm=arm)

    if case.grader == "behavior":
        gate = lambda: _behavior_gate_passed(case, scratch)
        reply = BEHAVIOR_GOAHEAD_REPLY
    else:
        gate = lambda: grade(scratch, host_repo=host_repo).passed
        reply = GOAHEAD_REPLY

    ok, _session_id, failure = session_driver.drive(
        prompt, scratch, gate, reply, max_resumes=max_resumes, timeout=timeout,
        runner=runner)
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
# Behavior grading
# ---------------------------------------------------------------------------

def _tree_files(root):
    """Return the set of file paths under ``root``, relative to ``root``.

    Never descends into a ``__pycache__`` directory, so compiled bytecode is
    never treated as a known source file.
    """
    found = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            found.add(os.path.relpath(os.path.join(dirpath, name), root))
    return found


def _prune_to_known(root, known_relpaths):
    """Remove every file under ``root`` whose path relative to ``root`` is
    not in ``known_relpaths``, then remove any directory left empty as a
    result (``root`` itself is never removed).

    This also discards stray ``__pycache__`` directories, since bytecode
    caches are never members of ``known_relpaths``.
    """
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        for name in filenames:
            filepath = os.path.join(dirpath, name)
            if os.path.relpath(filepath, root) not in known_relpaths:
                os.remove(filepath)
        if dirpath != root and not os.listdir(dirpath):
            os.rmdir(dirpath)


def grade_behavior(case, scratch_dir):
    """Grade a completed behavior-graded session's scratch repo and return a
    :class:`RunResult`.

    Restores the case's shipped ``fixture/tests/`` tree over ``<scratch>/
    tests/`` — reverting any session edit to a shipped test while leaving any
    new file the session added in place — then copies the case's held-out
    ``verify/`` tree over the same ``tests/`` directory. Any file under
    ``<scratch>/tests/`` that belongs to neither the shipped ``fixture/
    tests/`` tree nor the held-out ``verify/`` tree — including a test file a
    session wrote of its own accord — is then removed, so grading exercises
    only the known file set and a session cannot fail its own run by shipping
    a subtly wrong regression test (nor pass one by shipping a lenient one).
    It then runs ``python3 -m unittest discover -s tests`` with
    ``scratch_dir`` as the working directory, and the run passes only if that
    command exits 0.
    """
    case_dir = os.path.dirname(case.fixture_path)
    fixture_tests = os.path.join(case.fixture_path, "tests")
    verify_dir = os.path.join(case_dir, "verify")
    scratch_tests = os.path.join(scratch_dir, "tests")

    known_files = set()
    if os.path.isdir(fixture_tests):
        shutil.copytree(fixture_tests, scratch_tests, dirs_exist_ok=True)
        known_files |= _tree_files(fixture_tests)
    if os.path.isdir(verify_dir):
        shutil.copytree(verify_dir, scratch_tests, dirs_exist_ok=True)
        known_files |= _tree_files(verify_dir)
    _prune_to_known(scratch_tests, known_files)

    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=scratch_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    if proc.returncode != 0:
        return RunResult(False, proc.stdout)
    return RunResult(True, None)


def check_behavior_fixture(case, scratch_dir):
    """Sanity-check a behavior case's fixture before a session runs.

    Probes a throwaway copy of ``scratch_dir`` (so probing never disturbs the
    real scratch tree the session is about to work in) twice: first the
    shipped suite alone, which must exit 0 — a fixture whose own tests don't
    pass against its original code is mis-seeded; then, with the case's
    ``verify/`` tree overlaid onto ``tests/``, which must exit non-zero — a
    held-out test that already passes means the seeded bug is absent.

    Returns ``None`` when both probes hold, else a message naming the case,
    which check failed, and the captured output.
    """
    throwaway = tempfile.mkdtemp(prefix="s-eval-sanity-%s-" % case.name)
    try:
        shutil.copytree(scratch_dir, throwaway, dirs_exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=throwaway, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True)
        if proc.returncode != 0:
            return (
                "behavior fixture sanity check failed for case '%s': the "
                "shipped suite did not exit 0 before the session:\n%s"
                % (case.name, proc.stdout))

        verify_dir = os.path.join(
            os.path.dirname(case.fixture_path), "verify")
        throwaway_tests = os.path.join(throwaway, "tests")
        if os.path.isdir(verify_dir):
            shutil.copytree(verify_dir, throwaway_tests, dirs_exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=throwaway, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True)
        if proc.returncode == 0:
            return (
                "behavior fixture sanity check failed for case '%s': the "
                "held-out test already passes against the fixture's "
                "original code:\n%s" % (case.name, proc.stdout))
        return None
    finally:
        shutil.rmtree(throwaway, ignore_errors=True)


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
    parser.add_argument(
        "--arm", choices=("treatment", "baseline", "both"),
        default="treatment",
        help="'treatment' loads the plugin as today (default); 'baseline' "
             "runs with no plugin loaded, against a prompt derived from the "
             "case's own prompt.md; 'both' runs --runs N of each arm and "
             "reports the two pass rates together")
    return parser


def _arm_refusal(case, arm):
    """Return the refusal message for ``case`` under ``arm``, or ``None`` when
    the arm may proceed.

    A baseline-bearing arm (``"baseline"`` or ``"both"``) is refused for
    three reasons, checked before any scratch repo is assembled: a
    ``"structural"`` grader could never pass without the plugin session that
    produces its artifacts, so the comparison would carry no information; a
    ``prompt.md`` that cannot be read (``OSError`` — missing file, permission
    error, etc.); and a ``prompt.md`` whose first line carries no leading
    ``/s:<skill>`` token, so it cannot be turned into a baseline prompt via
    :func:`baseline_prompt`. Every message names the case; the structural
    refusal also names the grader. The unreadable-prompt case is caught here,
    rather than left to propagate, so one case's bad file fails that case
    alone instead of aborting the run — mirroring how :func:`execute_case`'s
    broad ``except Exception`` keeps one bad run from aborting the whole eval.
    """
    if arm == "treatment":
        return None
    if case.grader == "structural":
        return ("case '%s': baseline arm refused — grader is 'structural', "
                 "which only a plugin session can produce; the comparison "
                 "would carry no information" % case.name)
    try:
        with open(case.prompt_path, encoding="utf-8") as fh:
            prompt_text = fh.read()
    except OSError as exc:
        return ("case '%s': baseline arm refused — could not read "
                 "prompt.md: %s" % (case.name, exc))
    try:
        baseline_prompt(prompt_text)
    except ValueError as exc:
        return "case '%s': baseline arm refused — %s" % (case.name, exc)
    return None


def _refused_results(case, runs, refusal):
    """Build ``runs`` failed, ``refused=True`` :class:`RunResult`\\ s for
    ``case``, printing the same per-run ``FAIL`` line a spawned-and-failed run
    would print. Used both by :func:`execute_case` (a lone arm refused on its
    own) and by :func:`main` (a ``both`` request refused as a whole before
    either concrete arm executes) so the two refusal paths render identically.
    """
    results = []
    for i in range(1, runs + 1):
        result = RunResult(False, refusal, refused=True)
        results.append(result)
        first = (result.failure or "").splitlines()
        print("  [%s %d/%d] FAIL — %s"
              % (case.name, i, runs, first[0] if first else ""))
    return results


def execute_case(case, runs, claude_bin, keep_scratch,
                 max_resumes=MAX_RESUMES_DEFAULT, arm="treatment"):
    """Run ``case`` ``runs`` times under ``arm``, returning the list of
    :class:`RunResult`.

    Each run assembles a fresh scratch repo, drives the headless conversation
    (initial turn plus bounded go-ahead resumes), and grades it (a failed
    turn short-circuits to a failed run without grading). Scratch dirs are
    removed afterward unless ``keep_scratch``.

    Grading dispatches on ``case.grader``: ``"structural"`` calls :func:`grade`,
    ``"behavior"`` calls :func:`grade_behavior`. A ``case.grader`` outside
    those two values — set by :func:`discover_cases` to the offending
    ``expect.json``'s error message when it is unreadable or names an
    unrecognized grader — fails every run immediately with that message,
    spawning no session. A behavior case is additionally sanity-checked with
    :func:`check_behavior_fixture` immediately after ``assemble_scratch``; a
    reported failure fails the run before ``run_conversation`` is invoked, so
    a mis-seeded fixture never spawns a session.

    Before any of that, :func:`_arm_refusal` is consulted: a baseline-bearing
    ``arm`` (``"baseline"`` or ``"both"``) against a structural case, or a
    ``prompt.md`` :func:`baseline_prompt` cannot parse, fails every requested
    run immediately with the naming message and spawns no session — no
    scratch repo is even assembled. Each such result is additionally marked
    ``refused=True`` so :func:`summarize` can distinguish "nothing was
    measured" from a baseline arm that genuinely ran and failed.
    """
    refusal = _arm_refusal(case, arm)
    if refusal is not None:
        return _refused_results(case, runs, refusal)

    if case.grader not in ("structural", "behavior"):
        results = []
        for i in range(1, runs + 1):
            result = RunResult(False, case.grader)
            results.append(result)
            first = (result.failure or "").splitlines()
            print("  [%s %d/%d] FAIL — %s"
                  % (case.name, i, runs, first[0] if first else ""))
        return results

    results = []
    for i in range(1, runs + 1):
        scratch = assemble_scratch(case)
        try:
            try:
                sanity_failure = (
                    check_behavior_fixture(case, scratch)
                    if case.grader == "behavior" else None)
                if sanity_failure is not None:
                    result = RunResult(False, sanity_failure)
                else:
                    ok, failure = run_conversation(
                        case, scratch, claude_bin=claude_bin,
                        max_resumes=max_resumes, arm=arm)
                    if not ok:
                        result = RunResult(False, failure)
                    elif case.grader == "behavior":
                        result = grade_behavior(case, scratch)
                    else:
                        result = grade(scratch)
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


# Fixed row order when more than one arm is present: treatment first,
# baseline second, anything else — e.g. "refused", an invocation-level
# refusal filed under neither concrete arm — sorted after by name.
_ARM_ORDER = {"treatment": 0, "baseline": 1}


def summarize(results):
    """Build the per-case (per-arm) pass-rate summary from ``results``.
    Returns ``(lines, exit_code)``.

    ``results`` maps either a case name (the legacy, single-arm shape) or a
    ``(case, arm)`` tuple to its list of :class:`RunResult`; a plain
    case-name key is treated as the implicit ``"treatment"`` arm. When at
    most one arm is represented across ``results`` — always true for the
    legacy shape, and for a tupled mapping carrying only one arm — rendering
    is byte-identical to the original single-arm summary: one
    ``"<case> <passed>/<total>"`` row per case, sorted by case name, so the
    default single-arm invocation is unchanged. When more than one arm is
    represented, each case renders one row per arm instead, labelled
    ``"<case> [<arm>]"`` and sorted by case then the fixed arm order above.

    ``exit_code`` is 0 only when every **treatment**-arm row passed every
    run (a case with no treatment row at all does not block it) AND no row,
    in any arm, is a refused run (:attr:`RunResult.refused`). A baseline-arm
    row that actually ran never affects the exit code on its own — a failing
    baseline is the expected outcome of a working comparison, not a harness
    regression — but a refused row means nothing was measured, which is a
    usage error and always exits non-zero, whatever arm it is filed under. An
    empty ``results`` is not perfect (mirrors the original behavior) and
    exits 1.
    """
    normalized = {
        (key if isinstance(key, tuple) else (key, "treatment")): runs
        for key, runs in results.items()}
    arms_present = {arm for _case, arm in normalized}
    multi_arm = len(arms_present) > 1

    def _sort_key(item):
        (case_name, arm), _runs = item
        return (case_name, _ARM_ORDER.get(arm, len(_ARM_ORDER)), arm)

    lines = []
    treatment_perfect = True
    any_refused = any(
        r.refused for runs in normalized.values() for r in runs)
    for (case_name, arm), runs in sorted(normalized.items(), key=_sort_key):
        passed = sum(1 for r in runs if r.passed)
        total = len(runs)
        label = "%s [%s]" % (case_name, arm) if multi_arm else case_name
        lines.append("%-32s %d/%d" % (label, passed, total))
        if passed < total:
            if arm == "treatment":
                treatment_perfect = False
            for i, r in enumerate(runs, 1):
                if not r.passed:
                    first = (r.failure or "").splitlines()
                    lines.append("    run %d failed: %s"
                                 % (i, first[0] if first else ""))
    exit_code = 1 if not normalized else (
        0 if (treatment_perfect and not any_refused) else 1)
    return lines, exit_code


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    cases = discover_cases(CASES_DIR, case_filter=args.case)
    if not cases:
        where = args.case or CASES_DIR
        print("no eval cases found (%s)" % where)
        return 1
    # 'both' executes --runs N of each concrete arm per case; any other
    # selection is that one arm alone. The default ('treatment', alone)
    # keeps every printed line byte-identical to before --arm existed.
    arms = ("treatment", "baseline") if args.arm == "both" else (args.arm,)
    results = {}
    for case in cases:
        # Decide once, for the whole selected arm set, whether this case can
        # support a baseline at all — before either concrete arm executes.
        # Checking per concrete arm inside execute_case (as arms are looped
        # below) lets a 'both' request's treatment sub-call slip through:
        # _arm_refusal(case, "treatment") always returns None, so it would
        # run — and spawn a real session — before the baseline sub-call
        # refused. Computing the refusal here, against a representative
        # non-treatment arm, and applying it to every arm in the selected
        # set closes that gap. A 'treatment'-only invocation never reaches
        # this check (args.arm == "treatment" short-circuits to None), so it
        # is unaffected.
        invocation_refusal = (
            _arm_refusal(case, "baseline") if args.arm != "treatment"
            else None)
        plural = "" if args.runs == 1 else "s"
        if invocation_refusal is not None:
            # A 'both' request refused before either concrete arm executes:
            # the treatment arm never ran, so it must not be scored as a
            # failed 0/N alongside the baseline refusal. Report the refusal
            # once for the case, under a synthetic "refused" arm rather than
            # "treatment" or "baseline", so the summary row (or its absence
            # of an [arm] tag, when this is the only row) is never mistaken
            # for a treatment pass-rate measurement.
            print("== case: %s (%d run%s) =="
                  % (case.name, args.runs, plural))
            results[(case.name, "refused")] = _refused_results(
                case, args.runs, invocation_refusal)
            continue
        for arm in arms:
            if len(arms) == 1:
                print("== case: %s (%d run%s) =="
                      % (case.name, args.runs, plural))
            else:
                print("== case: %s [%s] (%d run%s) =="
                      % (case.name, arm, args.runs, plural))
            results[(case.name, arm)] = execute_case(
                case, args.runs, args.claude_bin, args.keep_scratch,
                max_resumes=args.max_resumes, arm=arm)
    print()
    print("Summary:")
    lines, exit_code = summarize(results)
    for ln in lines:
        print("  " + ln)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
