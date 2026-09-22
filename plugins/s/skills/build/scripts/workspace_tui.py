#!/usr/bin/env python3
"""workspace_tui.py — the interactive ``shipd workspace team`` wizard
(stdlib only, no network, no third-party imports).

Building the blessed nested team layout by hand means naming teams,
initializing a nested workspace per team, declaring each team's repos in the
project registry, and mapping any checkout the engineer already has —
several ``shipd workspace`` invocations a human has to sequence correctly.
This module is that sequencing, asked once as a guided round.

Three layers, deliberately separated so all but the last is testable without
a terminal (mirroring ``install_tui.py``):

  * :func:`plan_teams` — the whole behaviour of turning a collected answer
    set into an ordered action plan, a pure reducer that only *reads* disk
    (to notice a team directory that already declares a workspace) and never
    writes;
  * :func:`execute_plan` and its per-kind ``_execute_*`` helpers — the file
    surfaces, each performing exactly one planned action by calling
    ``os.makedirs`` or one of ``spec_status``'s engine-owned writers
    (``cmd_workspace_init``, ``cmd_workspace_project``, ``cmd_workspace_map``);
  * :func:`collect_answers` and :func:`run` — the interactive loop on
    ``/dev/tty`` that collects the answers :func:`plan_teams` consumes, then
    plans, executes, and reports. Unlike ``install_tui``'s picker, every
    answer here is free text (a team name, a repo path, an optional url,
    branch, or existing local checkout), so the loop is a sequence of line
    prompts rather than a raw-mode reducer — there is no raw terminal state
    to restore, only the opened ``/dev/tty`` handle to close, which
    :func:`run` does in a ``finally`` exactly as ``install_tui.run`` closes
    its own opened handle. The headless gate is ``sys.stdin.isatty()``: a
    scripted or piped invocation of this verb must never block on a prompt
    it cannot answer.

Executing a plan reaches the network never and clones nothing — every
planned action is local.
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_common as sc  # noqa: E402
import spec_status as ss  # noqa: E402


# ---------------------------------------------------------------------------
# The pure planner
# ---------------------------------------------------------------------------


def _declares_workspace(directory):
    """True when ``directory``'s own ``.shipd-config.json`` declares a
    ``workspace`` key — the same self-declaration test
    :func:`spec_common.init_workspace` uses to refuse nesting beneath itself,
    reimplemented here since that check is a private helper of
    ``spec_common``. Tolerant by design: a missing or malformed config reads
    as "not a workspace" rather than raising, so planning never crashes on a
    broken sibling directory."""
    path = os.path.join(directory, sc.CONFIG_FILENAME)
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and "workspace" in data


def plan_teams(base, answers):
    """Turn a collected answer set into an ordered action plan (shipd-workspace
    workspace-team-wizard) — the wizard's pure layer: it reads disk only to
    notice an already-initialized team directory, never writes, and needs no
    terminal.

    ``base`` is the discovered base workspace root. ``answers`` is a list of
    collected-team dicts, in collection order:
    ``{"name": <team name>, "repos": [<repo>, ...]}``, where each ``<repo>``
    is ``{"path": <manifest-relative path>, "url": <url or None>,
    "branch": <branch or None>, "local": <existing local checkout path or
    None>}``.

    Returns an ordered list of action tuples:

    * ``("mkdir", name, team_dir)`` — create the team directory, when absent;
    * ``("init", name, team_dir)`` — initialize it as a nested, git-seeded
      workspace;
    * ``("project", name, team_dir, path, url, branch)`` — declare one repo
      under the project named for the team, through the registry writer;
    * ``("map", name, team_dir, path, local)`` — record a member map entry
      for a repo whose existing local checkout was given;
    * ``("skip", name, team_dir)`` — a team directory that already declares a
      workspace: reported, never re-initialized, and no further action is
      planned for it.

    A team name failing ``PROJECT_NAME_RE`` (project-registry-semantics — the
    same pattern the registry itself enforces, so every planned directory is
    a safe component and a legal project name) or repeating an
    already-accepted name in this same call emits no action at all; re-asking
    for a better name is the interactive layer's job, not this one's."""
    plan = []
    seen = set()
    for team in answers:
        name = team.get("name") if isinstance(team, dict) else None
        if not isinstance(name, str) or not sc.PROJECT_NAME_RE.match(name):
            continue
        if name in seen:
            continue
        seen.add(name)
        team_dir = os.path.join(base, name)
        if _declares_workspace(team_dir):
            plan.append(("skip", name, team_dir))
            continue
        plan.append(("mkdir", name, team_dir))
        plan.append(("init", name, team_dir))
        for repo in team.get("repos") or ():
            path = repo.get("path") if isinstance(repo, dict) else None
            if not path:
                continue
            url = repo.get("url")
            branch = repo.get("branch")
            plan.append(("project", name, team_dir, path, url, branch))
            local = repo.get("local")
            if local:
                plan.append(("map", name, team_dir, path, local))
    return plan


# ---------------------------------------------------------------------------
# The pure executors
# ---------------------------------------------------------------------------


def _execute_mkdir(team_dir):
    """Create the team directory, tolerating an already-existing one — the
    planner only emits this action when it was absent at plan time, but a
    concurrent creation between planning and execution must not fail the
    run."""
    os.makedirs(team_dir, exist_ok=True)


def _execute_init(team_dir):
    """Initialize ``team_dir`` as a nested, git-seeded workspace through the
    engine's own writer — never a hand-written ``.shipd-config.json``."""
    ss.cmd_workspace_init(team_dir, git=True, nested=True)


def _execute_project(team_dir, name, path, url, branch):
    """Declare one repo under the project named for the team, through the
    engine's registry writer (spec-status workspace-project-verbs)."""
    ss.cmd_workspace_project(
        team_dir, "add", name, path, url=url, branch=branch)


def _execute_map(team_dir, path, local):
    """Record a member map entry for a repo whose existing local checkout
    was given, through the engine's map writer — never a clone."""
    ss.cmd_workspace_map(team_dir, member=path, local=local)


def execute_plan(plan):
    """Execute a planned action list in order (shipd-workspace
    workspace-team-wizard): local operations only, one ``_execute_*`` call
    per action — no network call, no clone, no member materialization.

    Returns one report record per team-affecting action, in plan order, for
    the wizard's completion report: ``("team", name, team_dir)`` for each
    team created, ``("repo", name, team_dir, path)`` for each repo declared,
    ``("map", name, team_dir, path, local)`` for each member mapped, or
    ``("skip", name, team_dir)`` for a team directory left untouched because
    it already declared a workspace. A bare ``mkdir`` action contributes no
    record of its own — the ``init`` action that follows it reports the
    team."""
    report = []
    for action in plan:
        kind = action[0]
        if kind == "mkdir":
            _, _name, team_dir = action
            _execute_mkdir(team_dir)
        elif kind == "init":
            _, name, team_dir = action
            _execute_init(team_dir)
            report.append(("team", name, team_dir))
        elif kind == "project":
            _, name, team_dir, path, url, branch = action
            _execute_project(team_dir, name, path, url, branch)
            report.append(("repo", name, team_dir, path))
        elif kind == "map":
            _, name, team_dir, path, local = action
            _execute_map(team_dir, path, local)
            report.append(("map", name, team_dir, path, local))
        elif kind == "skip":
            _, name, team_dir = action
            report.append(("skip", name, team_dir))
        else:
            raise ValueError("unknown planned action kind %r" % (kind,))
    return report


# ---------------------------------------------------------------------------
# The interactive loop
# ---------------------------------------------------------------------------

# The headless degradation, printed when standard input is not a terminal —
# writes nothing, exits non-zero (shipd-workspace workspace-team-wizard).
NON_INTERACTIVE_NOTE = (
    "workspace-team is interactive: it asks for team names and repos one at "
    "a time on a terminal. Run `shipd workspace team` from a terminal; "
    "nothing was written.\n")

TEAM_NAME_PROMPT = "Team name (blank to finish naming teams): "
TEAM_NAME_INVALID = (
    "not a valid team name (ASCII letters and digits joined by '-', '_' or "
    "'.'); try again\n")
TEAM_NAME_DUPLICATE = "'%s' was already entered; try again\n"
REPO_PATH_PROMPT = "  repo path for %s (blank to finish this team's repos): "
REPO_URL_PROMPT = "    clone url (optional, blank for none): "
REPO_BRANCH_PROMPT = "    branch (optional, blank for none): "
REPO_LOCAL_PROMPT = (
    "    existing local checkout path (optional, blank for none): ")


def wrap_tty(fd, closefd=True):
    """A text handle that reads *and* writes terminal descriptor ``fd`` —
    the same construction as ``install_tui.wrap_tty``, duplicated here so
    this module stays a self-contained layer."""
    return io.TextIOWrapper(io.FileIO(fd, "r+", closefd=closefd),
                            errors="replace", line_buffering=True)


def open_tty():
    """A read-write handle on the controlling terminal, or ``None`` when
    there is none."""
    try:
        fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError:
        return None
    return wrap_tty(fd)


def _prompt(handle, text):
    """Write ``text`` and read the next whole line. Returns the raw line —
    including its trailing newline when one was read — so the caller can
    tell a deliberate blank submission (``"\\n"``) apart from end-of-input
    (``""``), exactly as ``install_tui.line_prompt`` does."""
    handle.write(text)
    handle.flush()
    return handle.readline()


def _ask_team_name(handle, taken):
    """Collect one team name from ``handle``, re-asking on a name that fails
    ``PROJECT_NAME_RE`` (project-registry-semantics) or repeats one already
    in ``taken``. Returns ``(name, aborted)``: ``name`` is ``None`` both on a
    deliberate blank submission (finished naming teams) and on abort — the
    caller tells them apart via ``aborted``."""
    while True:
        line = _prompt(handle, TEAM_NAME_PROMPT)
        if not line:
            return None, True
        name = line.strip()
        if name == "":
            return None, False
        if not sc.PROJECT_NAME_RE.match(name):
            handle.write(TEAM_NAME_INVALID)
            continue
        if name in taken:
            handle.write(TEAM_NAME_DUPLICATE % name)
            continue
        return name, False


def _ask_repo(handle, team_name):
    """Collect one repo entry for ``team_name`` from ``handle``: a path,
    then an optional url, branch, and existing local checkout path. Returns
    ``(repo, aborted)`` with the same blank-vs-abort split as
    :func:`_ask_team_name`."""
    line = _prompt(handle, REPO_PATH_PROMPT % team_name)
    if not line:
        return None, True
    path = line.strip()
    if path == "":
        return None, False
    fields = []
    for prompt in (REPO_URL_PROMPT, REPO_BRANCH_PROMPT, REPO_LOCAL_PROMPT):
        line = _prompt(handle, prompt)
        if not line:
            return None, True
        fields.append(line.strip() or None)
    url, branch, local = fields
    return {"path": path, "url": url, "branch": branch, "local": local}, False


def collect_answers(handle):
    """Collect the wizard's whole answer set from ``handle`` (shipd-workspace
    workspace-team-wizard): one or more team names, holding each to
    ``PROJECT_NAME_RE`` and re-asking on a malformed or duplicate one, then
    per team its repos until a blank path ends that team's list.

    Returns ``(answers, aborted)`` — ``answers`` is the list :func:`plan_teams`
    consumes; ``aborted`` is True on end-of-input (Ctrl-D or a closed pipe)
    at any prompt, which the caller treats as "write nothing", exactly as a
    multiselect abort does in ``install_tui``."""
    handle.write(
        "Building a nested team workspace. Leave a team name blank when "
        "you are done naming teams.\n")
    answers = []
    taken = set()
    while True:
        name, aborted = _ask_team_name(handle, taken)
        if aborted:
            return answers, True
        if name is None:
            return answers, False
        taken.add(name)
        repos = []
        while True:
            repo, aborted = _ask_repo(handle, name)
            if aborted:
                return answers, True
            if repo is None:
                break
            repos.append(repo)
        answers.append({"name": name, "repos": repos})


def _render_report(handle, report):
    """Render the wizard's completion report on ``handle`` (shipd-workspace
    workspace-team-wizard): each team created, each repo declared, each
    member mapped, each already-initialized team directory skipped, and
    ``shipd workspace sync`` named as the way to materialize the rest."""
    if not report:
        handle.write("No teams were created.\n")
        return
    for kind, name, team_dir, *rest in report:
        if kind == "team":
            handle.write("created team %s at %s\n" % (name, team_dir))
        elif kind == "skip":
            handle.write(
                "%s already declares a workspace at %s; skipped\n"
                % (name, team_dir))
        elif kind == "repo":
            path, = rest
            handle.write(
                "declared repo %s under project %s (%s)\n"
                % (path, name, team_dir))
        elif kind == "map":
            path, local = rest
            handle.write(
                "mapped %s -> %s for %s\n" % (path, local, name))
    if any(kind in ("team", "repo", "map") for kind, *_ in report):
        handle.write(
            "Run `shipd workspace sync` in each team directory to "
            "materialize the members not already mapped.\n")


def _non_interactive(out):
    """The headless degradation: one note, nothing written."""
    out.write(NON_INTERACTIVE_NOTE)
    flush = getattr(out, "flush", None)
    if flush is not None:
        flush()


def run(base, tty=None, out=None):
    """The ``workspace-team`` wizard, against the already-resolved base
    workspace root ``base`` (shipd-workspace workspace-team-wizard). Returns
    the verb's exit code.

    ``tty`` is the controlling-terminal handle, opened here (via ``/dev/tty``)
    when the caller passes none; ``out`` receives the headless note only.
    While standard input is not a terminal, writes nothing, prints
    :data:`NON_INTERACTIVE_NOTE`, and returns non-zero — checked against
    ``sys.stdin.isatty()`` rather than the ``/dev/tty`` probe alone, so a
    scripted or piped invocation degrades immediately rather than blocking on
    a prompt it cannot answer. An explicitly passed ``tty`` skips that gate,
    for a caller driving the loop directly.

    On abort (end-of-input at any prompt) or an empty answer set, nothing is
    planned or executed and the exit code is 0 — there is nothing to refuse,
    only nothing to do. Otherwise plans, executes, and reports: every planned
    action is local, so this reaches the network never and clones nothing."""
    out = sys.stdout if out is None else out
    opened = None
    if tty is None:
        if not sys.stdin.isatty():
            _non_interactive(out)
            return 1
        tty = opened = open_tty()
        if tty is None:
            _non_interactive(out)
            return 1
    try:
        answers, aborted = collect_answers(tty)
        if aborted:
            tty.write("\nAborted — nothing was written.\n")
            tty.flush()
            return 0
        if not answers:
            tty.write("\nNo teams entered — nothing was written.\n")
            tty.flush()
            return 0
        plan = plan_teams(base, answers)
        report = execute_plan(plan)
        tty.write("\n")
        _render_report(tty, report)
        tty.flush()
        return 0
    finally:
        if opened is not None:
            opened.close()
