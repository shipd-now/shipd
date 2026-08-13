#!/usr/bin/env python3
"""Tests for integrations/statusline.sh — the Claude Code status line.

The script is driven as a black box via subprocess: session JSON is fed on
stdin (carrying ``workspace.current_dir``) and the single rendered line is
asserted against. Each test builds a throwaway temp workspace laid out as
``.shipd/planned/<change>/`` — never the real repo change dirs. ANSI color
codes are stripped before substring assertions so the tests care only about
the rendered text.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "integrations", "statusline.sh"))

# U+2615 HOT BEVERAGE — emoji presentation by default, no variation selector.
COFFEE = "☕"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    return ANSI_RE.sub("", text)


# A `stat` shim that emulates GNU coreutils semantics, used to prove the
# script's mtime probe is portable to Linux CI:
#   * `-c %Y <file>`  -> GNU "format" mode: prints a per-path epoch. The path
#     is keyed so *newer* sorts above *older*.
#   * `-f %m <file>`  -> GNU "filesystem status" mode: `-f` is NOT "format"
#     there; it prints a multi-line block on stdout and exits 0. If the script
#     probed `-f` first (as an earlier version did) this junk would poison the
#     integer mtime comparison and no active change would be picked.
GNU_STAT_SHIM = """#!/usr/bin/env bash
if [ "$1" = "-c" ]; then
  file="$3"
  case "$file" in
    *newer*) echo 222 ;;
    *older*) echo 111 ;;
    *)       echo 0 ;;
  esac
  exit 0
fi
if [ "$1" = "-f" ]; then
  printf '  File: "%s"\\n  ID: 0 Namelen: 255 Type: apfs\\n  Blocks: 0\\n' "$2"
  exit 0
fi
exit 1
"""


class StatuslineTestBase(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="statusline-test-")
        self.changes_dir = os.path.join(
            self.workspace, ".shipd", "planned")

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    # --- fixture helpers --------------------------------------------------
    def make_change(self, name, plan=None, tasks=None):
        cdir = os.path.join(self.changes_dir, name)
        os.makedirs(cdir)
        if plan is not None:
            with open(os.path.join(cdir, "plan.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(plan)
        if tasks is not None:
            with open(os.path.join(cdir, "tasks.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(tasks)
        return cdir

    def make_worktree_change(self, worktree, name, plan=None, tasks=None):
        cdir = os.path.join(
            self.workspace, ".worktrees", worktree, ".shipd", "planned", name)
        os.makedirs(cdir)
        if plan is not None:
            with open(os.path.join(cdir, "plan.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(plan)
        if tasks is not None:
            with open(os.path.join(cdir, "tasks.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(tasks)
        return cdir

    def make_epic(self, slug, members, worktree=None):
        # Fabricate an epic file with a `| Change | ... |` members table, one
        # row per name in `members`, either in the workspace root's
        # `.shipd/epics/` or a worktree's own `.shipd/epics/`.
        if worktree:
            base = os.path.join(
                self.workspace, ".worktrees", worktree, ".shipd")
        else:
            base = os.path.join(self.workspace, ".shipd")
        edir = os.path.join(base, "epics", slug)
        os.makedirs(edir, exist_ok=True)
        lines = ["# " + slug, "", "| Change | Description |", "| --- | --- |"]
        for m in members:
            lines.append("| %s | desc |" % m)
        with open(os.path.join(edir, "epic.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return os.path.join(edir, "epic.md")

    def set_tasks_mtime(self, change_dir, mtime):
        # Set an explicit mtime on a change's tasks.md so mtime tie-breaks are
        # deterministic (no sleeping).
        tasks = os.path.join(change_dir, "tasks.md")
        os.utime(tasks, (mtime, mtime))

    def select(self, name):
        state_dir = os.path.join(self.workspace, ".shipd")
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "state.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"current_spec": name}, fh)

    # --- driver -----------------------------------------------------------
    def run_line(self, workspace=None, path_prepend=None):
        payload = json.dumps(
            {"workspace": {"current_dir": workspace or self.workspace}})
        env = None
        if path_prepend is not None:
            env = dict(os.environ)
            env["PATH"] = path_prepend + os.pathsep + env.get("PATH", "")
        return subprocess.run(
            ["bash", SCRIPT], input=payload,
            capture_output=True, text=True, env=env)

    def rendered(self, workspace=None, path_prepend=None):
        r = self.run_line(workspace=workspace, path_prepend=path_prepend)
        self.assertEqual(r.returncode, 0, r.stderr)
        return strip_ansi(r.stdout).strip()


class SilenceTest(StatuslineTestBase):
    def test_silent_outside_spec_repo(self):
        # No .shipd/planned directory at all -> nothing, exit 0.
        r = self.run_line()
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.returncode, 0)

    def test_silent_when_workspace_missing_dir_falls_back_and_stays_silent(self):
        # A plain temp dir with no .shipd/planned -> silent.
        plain = tempfile.mkdtemp(prefix="statusline-plain-")
        try:
            r = self.run_line(workspace=plain)
            self.assertEqual(r.stdout, "")
            self.assertEqual(r.returncode, 0)
        finally:
            shutil.rmtree(plain, ignore_errors=True)


class RenderTest(StatuslineTestBase):
    def test_selected_change_renders_name_status_counts(self):
        self.make_change(
            "dark-mode-toggle",
            plan="# dark-mode-toggle\nStatus: active\n\n## Why\n",
            tasks=("## 1. Work\n"
                   "- [x] 1.1 a\n- [x] 1.2 b\n- [x] 1.3 c\n"
                   "- [ ] 1.4 d\n- [ ] 1.5 e\n- [ ] 1.6 f\n- [~] 1.7 g\n"))
        self.select("dark-mode-toggle")
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("dark-mode-toggle", line)
        self.assertIn("active", line)
        self.assertIn("3/7", line)

    def test_missing_status_renders_question_mark(self):
        # Plan present but no valid Status line -> "?".
        self.make_change(
            "no-status",
            plan="# no-status\n\n## Why\nNothing here.\n",
            tasks="## 1. Work\n- [ ] 1.1 a\n")
        self.select("no-status")
        line = self.rendered()
        self.assertIn("no-status", line)
        self.assertIn("?", line)
        self.assertIn("0/1", line)

    def test_rejected_change_renders_red_status_segment(self):
        # The gate's parking state renders with a red status segment
        # (\033[31m). Expected to FAIL until `rejected` joins the statusline's
        # status vocabulary and status_color (task 1.3).
        self.make_change(
            "starved-change",
            plan="# starved-change\nStatus: rejected\n",
            tasks="## 1. Work\n- [ ] 1.1 a\n")
        self.select("starved-change")
        r = self.run_line()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("rejected", strip_ansi(r.stdout))
        self.assertIn("\x1b[31m", r.stdout)

    def test_task_segment_omitted_without_tasks_file(self):
        self.make_change(
            "no-tasks",
            plan="# no-tasks\nStatus: ready\n",
            tasks=None)
        self.select("no-tasks")
        line = self.rendered()
        self.assertIn("no-tasks", line)
        self.assertIn("ready", line)
        self.assertNotIn("/", line)


class SelectionFallbackTest(StatuslineTestBase):
    def test_sole_change_is_auto_selected(self):
        # No state.json; exactly one non-archive change -> rendered as selected.
        self.make_change(
            "only-one",
            plan="# only-one\nStatus: complete\n",
            tasks="## 1. Work\n- [x] 1.1 a\n- [x] 1.2 b\n")
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("only-one", line)
        self.assertIn("complete", line)
        self.assertIn("2/2", line)

    def test_no_changes_prints_no_active_specs(self):
        os.makedirs(self.changes_dir)
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("no active specs", line)

    def test_several_changes_none_selected(self):
        self.make_change("alpha", plan="# alpha\nStatus: draft\n")
        self.make_change("beta", plan="# beta\nStatus: draft\n")
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("2 specs", line)
        self.assertIn("none selected", line)

    def test_completed_excluded_from_auto_select(self):
        # One live change + a sibling completed/ dir -> completed ignored,
        # sole live change selected (planned/ holds only live changes).
        self.make_change(
            "real-change",
            plan="# real-change\nStatus: active\n",
            tasks="## 1\n- [ ] 1.1 a\n")
        os.makedirs(os.path.join(
            self.workspace, ".shipd", "completed", "2026-01-01-old-change"))
        line = self.rendered()
        self.assertIn("real-change", line)
        self.assertIn("active", line)

    def test_selected_but_missing_falls_back(self):
        # state.json points at a change dir that does not exist -> fall back.
        self.make_change("present", plan="# present\nStatus: ready\n")
        self.select("ghost")
        line = self.rendered()
        # Sole remaining change auto-selected.
        self.assertIn("present", line)
        self.assertIn("ready", line)


class RenamedDirTest(StatuslineTestBase):
    """The statusline reads the literal default `.shipd/planned` and never resolves
    `.shipd-config.json`, so a repo that renames its content directory renders
    nothing (statusline-rendering: renamed content dir is out of scope)."""

    def test_renamed_content_dir_renders_nothing(self):
        # Config renames the content dir to `specs`, and the change lives there;
        # there is no `.shipd/planned`, so the statusline stays silent.
        with open(os.path.join(self.workspace, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"dir": "specs"}, fh)
        cdir = os.path.join(self.workspace, "specs", "planned", "dark-mode")
        os.makedirs(cdir)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# dark-mode\nStatus: active\n")
        r = self.run_line()
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.returncode, 0)


class WorktreeAwareTest(StatuslineTestBase):
    """The statusline scans the workspace root's `.shipd/planned/` plus
    `.worktrees/*/.shipd/planned/` (one level deep), prefers an `active` change
    wherever it lives, and renders position/aggregate brackets when several
    changes are live (statusline-rendering)."""

    def test_active_worktree_change_rendered_from_empty_root(self):
        # Root .shipd/planned/ is empty; the only live change lives in a worktree.
        os.makedirs(self.changes_dir)
        self.make_worktree_change(
            "w1", "dark-mode-toggle",
            plan="# dark-mode-toggle\nStatus: active\n",
            tasks=("## 1. Work\n"
                   "- [x] 1.1 a\n- [x] 1.2 b\n- [x] 1.3 c\n"
                   "- [ ] 1.4 d\n- [ ] 1.5 e\n- [ ] 1.6 f\n- [ ] 1.7 g\n"))
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("dark-mode-toggle", line)
        self.assertIn("active", line)
        self.assertIn("3/7", line)

    def test_multiple_live_specs_render_position_and_aggregate(self):
        # An active change (5/13) in a worktree and a second live change with
        # 7 tasks in the root -> position (1 of 2) and aggregate (13 of 20).
        thirteen = "## 1\n" + "".join(
            "- [x] 1.%d a\n" % i for i in range(1, 6)) + "".join(
            "- [ ] 2.%d b\n" % i for i in range(1, 9))
        seven = "## 1\n" + "".join("- [ ] 1.%d a\n" % i for i in range(1, 8))
        self.make_worktree_change(
            "w1", "active-one",
            plan="# active-one\nStatus: active\n", tasks=thirteen)
        self.make_change(
            "ready-two", plan="# ready-two\nStatus: ready\n", tasks=seven)
        line = self.rendered()
        self.assertIn("active-one", line)
        self.assertIn("(1 of 2)", line)
        self.assertIn("5/13", line)
        self.assertIn("(13 of 20)", line)

    def test_active_worktree_beats_ready_root_selection(self):
        # A root selection points at a ready change; a worktree change is
        # active -> the active worktree change owns the line.
        self.make_change(
            "root-ready", plan="# root-ready\nStatus: ready\n",
            tasks="## 1\n- [ ] 1.1 a\n")
        self.select("root-ready")
        self.make_worktree_change(
            "w1", "wt-active", plan="# wt-active\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        line = self.rendered()
        self.assertIn("wt-active", line)
        self.assertIn("active", line)
        self.assertNotIn("root-ready", line)

    def test_two_active_changes_pick_newer_tasks_mtime(self):
        # Two active changes; the one with the newer tasks.md mtime wins.
        older = self.make_change(
            "older-active", plan="# older-active\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        newer = self.make_worktree_change(
            "w1", "newer-active", plan="# newer-active\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [x] 1.2 b\n- [ ] 1.3 c\n")
        self.set_tasks_mtime(older, 1_000_000)
        self.set_tasks_mtime(newer, 2_000_000)
        line = self.rendered()
        self.assertIn("newer-active", line)
        self.assertNotIn("older-active", line)

    def test_am_dir_without_planned_reports_no_active_specs(self):
        # `.shipd/` exists (with verified/) but no planned/ dir -> report, not
        # silence.
        os.makedirs(os.path.join(self.workspace, ".shipd", "verified"))
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("no active specs", line)

    def test_no_am_dir_prints_nothing(self):
        # Workspace with no `.shipd/` at all -> silent, exit 0.
        r = self.run_line()
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.returncode, 0)

    def test_active_pick_survives_gnu_stat_semantics(self):
        # Under a GNU-coreutils `stat` shim (where `-f` prints a multi-line
        # filesystem block instead of an mtime), the active-pick tie-break must
        # still resolve to the newer `tasks.md` — proving the `-c %Y`-first
        # probe and numeric guard survive Linux CI.
        shim_dir = os.path.join(self.workspace, "shim-bin")
        os.makedirs(shim_dir)
        shim = os.path.join(shim_dir, "stat")
        with open(shim, "w", encoding="utf-8") as fh:
            fh.write(GNU_STAT_SHIM)
        os.chmod(shim, 0o755)
        self.make_change(
            "older-active", plan="# older-active\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.make_worktree_change(
            "w1", "newer-active", plan="# newer-active\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [x] 1.2 b\n- [ ] 1.3 c\n")
        line = self.rendered(path_prepend=shim_dir)
        self.assertIn("newer-active", line)
        self.assertNotIn("older-active", line)

    def test_several_live_none_pickable_counts_worktree_specs(self):
        # A draft root change and a draft worktree change, no active, no
        # selection -> `2 specs · none selected`, counting the worktree spec.
        self.make_change("alpha", plan="# alpha\nStatus: draft\n")
        self.make_worktree_change(
            "w1", "beta", plan="# beta\nStatus: draft\n")
        line = self.rendered()
        self.assertIn(COFFEE, line)
        self.assertIn("2 specs", line)
        self.assertIn("none selected", line)


class EpicMarkerTest(StatuslineTestBase):
    """When the picked change's `plan.md` header carries an `Epic:` line, the
    name segment appends an epic marker after the change name and before any
    `(1 of X)` position bracket: `(EPIC: <slug>, spec <pos>/<total>)` when the
    change resolves to a row in its epic file's members table, degrading to the
    literal `(EPIC)` when the epic file is missing or the change is absent from
    the table (statusline-rendering)."""

    def test_epic_member_renders_table_position(self):
        # Picked change listed as the 2nd of 3 member rows -> enriched marker.
        self.make_change(
            "epic-member",
            plan="# epic-member\nStatus: active\nEpic: some-epic\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("epic-member")
        self.make_epic("some-epic", ["first-one", "epic-member", "third-one"])
        line = self.rendered()
        self.assertIn("epic-member (EPIC: some-epic, spec 2/3)", line)

    def test_missing_epic_file_degrades_to_bare_marker(self):
        # Epic header present but no epic file -> literal `(EPIC)`.
        self.make_change(
            "epic-member",
            plan="# epic-member\nStatus: active\nEpic: some-epic\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("epic-member")
        line = self.rendered()
        self.assertIn("epic-member (EPIC)", line)
        self.assertNotIn("EPIC:", line)

    def test_change_absent_from_table_degrades_to_bare_marker(self):
        # Epic file exists but its table has no row for the change -> `(EPIC)`.
        self.make_change(
            "epic-member",
            plan="# epic-member\nStatus: active\nEpic: some-epic\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("epic-member")
        self.make_epic("some-epic", ["other-one", "other-two"])
        line = self.rendered()
        self.assertIn("epic-member (EPIC)", line)
        self.assertNotIn("EPIC:", line)

    def test_worktree_candidate_reads_its_own_epic_file(self):
        # The active change lives in a worktree whose epic snapshot lists it 3rd
        # of 3; the root's epic file lists it 1st of 2. The worktree's position
        # must win (the epic file is resolved from the candidate's own dir).
        self.make_worktree_change(
            "w1", "epic-member",
            plan="# epic-member\nStatus: active\nEpic: some-epic\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.make_epic("some-epic", ["epic-member", "root-other"])
        self.make_epic("some-epic", ["a-one", "b-two", "epic-member"],
                       worktree="w1")
        line = self.rendered()
        self.assertIn("epic-member (EPIC: some-epic, spec 3/3)", line)

    def test_standalone_change_renders_no_marker(self):
        self.make_change(
            "standalone",
            plan="# standalone\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("standalone")
        line = self.rendered()
        self.assertNotIn("(EPIC", line)

    def test_marker_precedes_position_bracket(self):
        # Two live changes -> the picked (active) change carries the marker
        # before its `(1 of 2)` position bracket.
        self.make_change(
            "epic-active",
            plan="# epic-active\nStatus: active\nEpic: some-epic\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.make_change(
            "ready-two",
            plan="# ready-two\nStatus: ready\n",
            tasks="## 1\n- [ ] 1.1 a\n")
        line = self.rendered()
        self.assertIn("epic-active (EPIC) (1 of 2)", line)


class RunDotTest(StatuslineTestBase):
    """While a fresh `.shipd/autopilot/*-heartbeat.json` in the workspace root
    records a `running` state and the picked change is `active`, the status
    segment is prefixed with the U+25CF dot; a stale, finished, or absent
    heartbeat — or a non-active pick — renders no dot (statusline-rendering)."""

    DOT = "●"  # U+25CF BLACK CIRCLE

    def make_heartbeat(self, name, body, age=0):
        # Fabricate `.shipd/autopilot/<name>-heartbeat.json` in the workspace root
        # and optionally age its mtime by `age` seconds (os.utime, no clock).
        hb_dir = os.path.join(self.workspace, ".shipd", "autopilot")
        os.makedirs(hb_dir, exist_ok=True)
        path = os.path.join(hb_dir, name + "-heartbeat.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        if age:
            when = os.path.getmtime(path) - age
            os.utime(path, (when, when))
        return path

    def test_fresh_running_state_lights_dot(self):
        self.make_change(
            "runner",
            plan="# runner\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("runner")
        self.make_heartbeat("e", '{"state": "running"}')
        line = self.rendered()
        self.assertIn(self.DOT, line)

    def test_fresh_run_state_key_variant_lights_dot(self):
        self.make_change(
            "runner",
            plan="# runner\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("runner")
        self.make_heartbeat("e", '{"run_state": "running"}')
        line = self.rendered()
        self.assertIn(self.DOT, line)

    def test_finished_heartbeat_renders_no_dot(self):
        self.make_change(
            "runner",
            plan="# runner\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("runner")
        self.make_heartbeat("e", '{"state": "finished"}')
        line = self.rendered()
        self.assertNotIn(self.DOT, line)

    def test_stale_running_heartbeat_renders_no_dot(self):
        self.make_change(
            "runner",
            plan="# runner\nStatus: active\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("runner")
        self.make_heartbeat("e", '{"state": "running"}', age=4000)
        line = self.rendered()
        self.assertNotIn(self.DOT, line)

    def test_non_active_pick_renders_no_dot(self):
        self.make_change(
            "ready-one",
            plan="# ready-one\nStatus: ready\n",
            tasks="## 1\n- [x] 1.1 a\n- [ ] 1.2 b\n")
        self.select("ready-one")
        self.make_heartbeat("e", '{"state": "running"}')
        line = self.rendered()
        self.assertNotIn(self.DOT, line)


if __name__ == "__main__":
    unittest.main()
