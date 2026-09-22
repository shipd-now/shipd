#!/usr/bin/env python3
"""Tests for the nested team-workspace setup (shipd-workspace
workspace-project-verbs, workspace-team-wizard).

The ``workspace-project`` verb is driven as a black box via subprocess
against a throwaway temp workspace root, mirroring the
subprocess-against-temp-roots style of ``test_spec_status.py``. The team
wizard's pure planner (``workspace_tui.plan_teams``) is exercised in-process
instead, since it is the layer the constitution's three-way split makes
testable without a terminal."""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "spec_status.py"))

sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import spec_common as sc  # noqa: E402
import workspace_tui as wt  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "..", "document", "scripts"))
import docs_lint  # noqa: E402

DOCS_DIR = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "..", "..", "docs"))
WORKSPACES_DOCS_DIR = os.path.join(DOCS_DIR, "workspaces")


class WorkspaceTeamTestBase(unittest.TestCase):
    """Shared harness: an isolated temp workspace root and ``$HOME``, plus a
    subprocess ``cli`` helper against ``spec_status.py --root <root>``."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="workspace-team-test-")
        self._base_home = tempfile.mkdtemp(prefix="workspace-team-basehome-")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self._base_home
        self.flow_dir = tempfile.mkdtemp(prefix="workspace-team-flow-")
        self._old_flow = os.environ.get("AM_FLOW_LOG_DIR")
        os.environ["AM_FLOW_LOG_DIR"] = self.flow_dir

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        if self._old_flow is None:
            os.environ.pop("AM_FLOW_LOG_DIR", None)
        else:
            os.environ["AM_FLOW_LOG_DIR"] = self._old_flow
        shutil.rmtree(self.flow_dir, ignore_errors=True)
        shutil.rmtree(self._base_home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    def cli(self, *args, root=None, stdin=None):
        return subprocess.run(
            ["python3", SCRIPT, "--root", root or self.root, *args],
            capture_output=True, text=True, stdin=stdin)

    def config_path(self, root=None):
        return os.path.join(root or self.root, ".shipd-config.json")

    def declare_workspace(self, registry=None, root=None, extra=None):
        """Declare ``registry`` (default ``{}``) as the ``workspace`` object
        in ``<root>/.shipd-config.json``, plus any ``extra`` top-level
        keys — the config-file workspace marker."""
        target = root if root is not None else self.root
        data = dict(extra or {})
        data["workspace"] = registry if registry is not None else {}
        with open(self.config_path(target), "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def read_config(self, root=None):
        with open(self.config_path(root), encoding="utf-8") as fh:
            return json.load(fh)

    def read_config_bytes(self, root=None):
        with open(self.config_path(root), "rb") as fh:
            return fh.read()

    def read_registry(self, root=None):
        return self.read_config(root)["workspace"]


class WorkspaceProjectVerbTests(WorkspaceTeamTestBase):
    """The ``workspace-project`` verb — the engine-owned writer for the
    workspace registry's ``projects`` map (shipd-workspace
    workspace-project-verbs)."""

    # -- bare form -----------------------------------------------------

    def test_bare_form_prints_no_projects_when_none_declared(self):
        self.declare_workspace()
        r = self.cli("workspace-project")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("(no projects)", r.stdout)

    def test_bare_form_lists_project_and_repo(self):
        self.declare_workspace({
            "projects": {
                "main-app": {"repos": [
                    {"path": "api", "url": "https://example.com/api.git"},
                ]},
            },
        })
        r = self.cli("workspace-project")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("main-app: api https://example.com/api.git", r.stdout)

    def test_bare_form_lists_a_plain_path_entry_without_url(self):
        self.declare_workspace({
            "projects": {"main-app": {"repos": ["api"]}},
        })
        r = self.cli("workspace-project")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("main-app: api", r.stdout)
        self.assertNotIn("main-app: api ", r.stdout.replace(
            "main-app: api\n", ""))

    # -- add -------------------------------------------------------------

    def test_add_declares_a_repo_under_a_new_project(self):
        self.declare_workspace()
        r = self.cli(
            "workspace-project", "add", "main-app", "api",
            "--url", "https://example.com/api.git")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertEqual(
            registry["projects"]["main-app"]["repos"],
            [{"path": "api", "url": "https://example.com/api.git"}])

    def test_add_stores_url_and_branch_verbatim(self):
        self.declare_workspace()
        r = self.cli(
            "workspace-project", "add", "main-app", "api",
            "--url", "https://example.com/api.git", "--branch", "release")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertEqual(
            registry["projects"]["main-app"]["repos"],
            [{
                "path": "api",
                "url": "https://example.com/api.git",
                "branch": "release",
            }])

    def test_add_with_no_url_or_branch_stores_a_plain_path(self):
        self.declare_workspace()
        r = self.cli("workspace-project", "add", "main-app", "api")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertEqual(registry["projects"]["main-app"]["repos"], ["api"])

    def test_add_appends_to_an_existing_project(self):
        self.declare_workspace({"projects": {"main-app": {"repos": ["api"]}}})
        r = self.cli("workspace-project", "add", "main-app", "web")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertEqual(
            registry["projects"]["main-app"]["repos"], ["api", "web"])

    # -- remove ------------------------------------------------------------

    def test_remove_repo_drops_a_single_entry(self):
        self.declare_workspace({
            "projects": {"main-app": {"repos": ["api", "web"]}},
        })
        r = self.cli(
            "workspace-project", "remove", "main-app", "--repo", "web")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertEqual(registry["projects"]["main-app"]["repos"], ["api"])

    def test_remove_last_repo_drops_the_whole_project(self):
        self.declare_workspace({"projects": {"main-app": {"repos": ["api"]}}})
        r = self.cli(
            "workspace-project", "remove", "main-app", "--repo", "api")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertNotIn("main-app", registry.get("projects", {}))

    def test_remove_without_repo_drops_the_whole_project(self):
        self.declare_workspace({
            "projects": {"main-app": {"repos": ["api", "web"]}},
        })
        r = self.cli("workspace-project", "remove", "main-app")
        self.assertEqual(r.returncode, 0, r.stderr)
        registry = self.read_registry()
        self.assertNotIn("main-app", registry.get("projects", {}))

    # -- validation refusal --------------------------------------------

    def test_ambiguous_repo_path_refuses_and_writes_nothing(self):
        self.declare_workspace({"projects": {"alpha": {"repos": ["api"]}}})
        before = self.read_config_bytes()
        r = self.cli("workspace-project", "add", "beta", "api")
        self.assertNotEqual(r.returncode, 0)
        after = self.read_config_bytes()
        self.assertEqual(before, after)

    # -- other keys survive -------------------------------------------

    def test_other_config_keys_survive_a_write(self):
        self.declare_workspace(extra={"dir": "custom-dir"})
        r = self.cli("workspace-project", "add", "main-app", "api")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = self.read_config()
        self.assertEqual(data["dir"], "custom-dir")


class WorkspaceTeamPlannerTests(WorkspaceTeamTestBase):
    """The wizard's pure planner, ``workspace_tui.plan_teams(base, answers)``
    (shipd-workspace workspace-team-wizard) — turns a collected answer set
    into an ordered action plan, with no execution and no terminal, so it is
    exercised in-process rather than via ``cli()``.

    ``answers`` is a list of collected-team dicts, in collection order:
    ``{"name": <team name>, "repos": [<repo>, ...]}``, where each ``<repo>``
    is ``{"path": <manifest path>, "url": <url or None>,
    "branch": <branch or None>, "local": <existing checkout path or None>}``.

    ``plan_teams`` returns an ordered list of action tuples, one of:
    ``("mkdir", name, team_dir)``, ``("init", name, team_dir)``,
    ``("project", name, team_dir, path, url, branch)``,
    ``("map", name, team_dir, path, local)``, or
    ``("skip", name, team_dir)`` for a team directory that already declares
    a workspace."""

    def setUp(self):
        super().setUp()
        self.declare_workspace()  # the base workspace itself

    def team_dir(self, name):
        return os.path.join(self.root, name)

    def test_answers_become_an_ordered_action_plan(self):
        answers = [{
            "name": "fortress",
            "repos": [{"path": "api", "url": "https://example.com/api.git",
                       "branch": None, "local": None}],
        }]
        plan = wt.plan_teams(self.root, answers)
        self.assertEqual(
            [action[0] for action in plan], ["mkdir", "init", "project"])
        team_dir = self.team_dir("fortress")
        self.assertEqual(plan[0], ("mkdir", "fortress", team_dir))
        self.assertEqual(plan[1], ("init", "fortress", team_dir))
        self.assertEqual(
            plan[2],
            ("project", "fortress", team_dir, "api",
             "https://example.com/api.git", None))

    def test_existing_local_checkout_adds_a_map_action(self):
        answers = [{
            "name": "fortress",
            "repos": [{"path": "api", "url": None, "branch": None,
                       "local": "/existing/checkout"}],
        }]
        plan = wt.plan_teams(self.root, answers)
        self.assertEqual(
            [action[0] for action in plan],
            ["mkdir", "init", "project", "map"])
        team_dir = self.team_dir("fortress")
        self.assertEqual(
            plan[-1],
            ("map", "fortress", team_dir, "api", "/existing/checkout"))

    def test_malformed_team_name_yields_no_action(self):
        answers = [
            {"name": "bad name!", "repos": []},
            {"name": "fortress", "repos": []},
        ]
        plan = wt.plan_teams(self.root, answers)
        names = {action[1] for action in plan}
        self.assertNotIn("bad name!", names)
        self.assertIn("fortress", names)

    def test_duplicate_name_yields_no_second_action(self):
        answers = [
            {"name": "fortress", "repos": []},
            {"name": "fortress",
             "repos": [{"path": "api", "url": None, "branch": None,
                        "local": None}]},
        ]
        plan = wt.plan_teams(self.root, answers)
        # Only the first occurrence's actions appear: no `project` action
        # from the second, duplicate entry's repo, and no second
        # `mkdir`/`init` pair.
        self.assertEqual([action[0] for action in plan], ["mkdir", "init"])

    def test_already_declaring_team_directory_is_skipped(self):
        existing = self.team_dir("fortress")
        os.makedirs(existing)
        self.declare_workspace(root=existing)
        plan = wt.plan_teams(self.root, [{"name": "fortress", "repos": []}])
        self.assertEqual(plan, [("skip", "fortress", existing)])


class WorkspaceTeamExecutorTests(WorkspaceTeamTestBase):
    """The wizard's executor layer, ``workspace_tui.execute_plan(plan)``
    (shipd-workspace workspace-team-wizard) — executing a planned action
    list against a real tmpdir base workspace, local operations only: no
    network call, and no clone (a repo path with a declared url is never
    materialized on disk)."""

    def setUp(self):
        super().setUp()
        self.declare_workspace()  # the base workspace itself

    def existing_checkout(self):
        path = tempfile.mkdtemp(prefix="workspace-team-checkout-")
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        return path

    def test_execute_plan_builds_the_nested_team_layout(self):
        before_base = self.read_config_bytes()
        local = self.existing_checkout()
        answers = [{
            "name": "fortress",
            "repos": [
                {"path": "api", "url": "https://example.com/api.git",
                 "branch": None, "local": None},
                {"path": "web", "url": None, "branch": None,
                 "local": local},
            ],
        }]
        plan = wt.plan_teams(self.root, answers)
        report = wt.execute_plan(plan)

        team_dir = os.path.join(self.root, "fortress")

        # The team directory declares its own nested workspace, discoverable
        # as nested beneath the base: the upward chain from the team
        # directory carries the team first, then the base.
        self.assertTrue(os.path.isfile(self.config_path(team_dir)))
        chain = sc.workspace_chain(team_dir)
        self.assertEqual(chain[0], os.path.abspath(team_dir))
        self.assertIn(os.path.abspath(self.root), chain[1:])

        # The team's own projects entry is written under the project named
        # for the team...
        team_registry = self.read_registry(team_dir)
        self.assertEqual(
            team_registry["projects"]["fortress"]["repos"],
            [{"path": "api", "url": "https://example.com/api.git"}, "web"])
        # ...while the base registry — and its whole config file — is
        # untouched.
        self.assertNotIn("projects", self.read_registry())
        self.assertEqual(before_base, self.read_config_bytes())

        # A member map entry is recorded for the repo whose existing local
        # checkout was given, and nothing was cloned: the other repo's path
        # was never materialized under the team directory.
        repos_map = sc.load_repo_map(team_dir)
        self.assertEqual(repos_map, {"web": local})
        self.assertFalse(os.path.isdir(os.path.join(team_dir, "api")))
        self.assertFalse(os.path.isdir(os.path.join(team_dir, "web")))

        # The report names the team created, each repo declared, and the
        # one member mapped, in plan order.
        self.assertEqual(
            [record[0] for record in report],
            ["team", "repo", "repo", "map"])
        self.assertEqual(report[0], ("team", "fortress", team_dir))
        self.assertEqual(report[-1], ("map", "fortress", team_dir, "web", local))

    def test_completion_report_names_teams_repos_maps_and_sync(self):
        local = self.existing_checkout()
        answers = [
            {
                "name": "fortress",
                "repos": [
                    {"path": "api", "url": "https://example.com/api.git",
                     "branch": None, "local": None},
                    {"path": "web", "url": None, "branch": None,
                     "local": local},
                ],
            },
            {"name": "already-there", "repos": []},
        ]
        # A second, already-initialized team directory so the report also
        # covers the skip case.
        skipped_dir = self.team_dir_for("already-there")
        os.makedirs(skipped_dir)
        self.declare_workspace(root=skipped_dir)

        plan = wt.plan_teams(self.root, answers)
        report = wt.execute_plan(plan)
        handle = io.StringIO()
        wt._render_report(handle, report)
        text = handle.getvalue()

        team_dir = os.path.join(self.root, "fortress")
        self.assertIn("fortress", text)
        self.assertIn(team_dir, text)
        self.assertIn("api", text)
        self.assertIn("web", text)
        self.assertIn(local, text)
        self.assertIn("already-there", text)
        self.assertIn(skipped_dir, text)
        self.assertIn("shipd workspace sync", text)

    def team_dir_for(self, name):
        return os.path.join(self.root, name)


class WorkspaceTeamVerbTests(WorkspaceTeamTestBase):
    """The ``workspace-team`` verb (shipd-workspace workspace-team-wizard) —
    driven as a black box via subprocess, exactly like
    ``WorkspaceProjectVerbTests``. Its interactive terminal loop is layer
    three of ``workspace_tui`` and untestable without a real terminal; these
    two cases cover what needs none: the headless degradation and the
    no-workspace refusal."""

    def test_headless_writes_nothing_and_exits_non_zero(self):
        self.declare_workspace()
        before = sorted(os.listdir(self.root))
        r = self.cli("workspace-team", stdin=subprocess.DEVNULL)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("interactive", r.stdout + r.stderr)
        self.assertEqual(sorted(os.listdir(self.root)), before)

    def test_no_workspace_discoverable_names_init_as_the_remedy(self):
        # No declare_workspace() call: self.root declares no workspace.
        r = self.cli("workspace-team", stdin=subprocess.DEVNULL)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("workspace-init", r.stderr)
        self.assertFalse(os.path.isfile(self.config_path()))


class WorkspaceGuideDriftTests(unittest.TestCase):
    """A doc convention is real only when a test can refuse its violation
    (plan.md Q3, oracle-answered) — the workspaces guide presents exactly one
    blessed team shape, `teams.md` and `multi-workspace-repos.md` both name
    the wizard, and every page stays within its doc-type line cap."""

    # Phrasing the removed sibling-workspaces shape used to use — none of it
    # may survive in the guide once the nested shape is the only one
    # documented.
    FORBIDDEN_PHRASES = (
        "Shape A",
        "Shape B",
        "sibling workspaces",
        "sibling-workspaces",
        "plain-container-repo",
        "container repo",
    )

    def guide_pages(self):
        pages = [os.path.join(DOCS_DIR, "workspaces.md")]
        for name in sorted(os.listdir(WORKSPACES_DOCS_DIR)):
            if name.endswith(".md"):
                pages.append(os.path.join(WORKSPACES_DOCS_DIR, name))
        return pages

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def test_no_page_presents_the_sibling_shape(self):
        for path in self.guide_pages():
            text = self.read(path)
            for phrase in self.FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase, text,
                    "%s still mentions the removed sibling shape (%r)"
                    % (path, phrase))

    def test_teams_and_multi_workspace_repos_name_the_team_verb(self):
        for name in ("teams.md", "multi-workspace-repos.md"):
            path = os.path.join(WORKSPACES_DOCS_DIR, name)
            self.assertIn("shipd workspace team", self.read(path), path)

    def test_every_guide_page_stays_within_its_doc_type_cap(self):
        for path in self.guide_pages():
            lines = self.read(path).splitlines()
            self.assertTrue(lines, "%s is empty" % path)
            match = docs_lint.MARKER_RE.match(lines[0])
            self.assertIsNotNone(
                match, "%s has no `<!-- doc-type: ... -->` marker" % path)
            doc_type = match.group(1)
            cap = docs_lint.LINE_CAPS.get(doc_type)
            self.assertIsNotNone(
                cap, "%s declares unknown doc-type %r" % (path, doc_type))
            self.assertLessEqual(
                len(lines), cap,
                "%s has %d lines; the %s cap is %d"
                % (path, len(lines), doc_type, cap))


class NestedTeamLayoutTests(WorkspaceTeamTestBase):
    """Builds the blessed layout with the real verbs — a base workspace at
    ``self.root`` holding two nested team workspaces, ``alpha`` (declaring
    its own project registry) and ``beta`` (declaring none) — and simulates
    usage across it: read-through, write-nearest, registry shadowing, a
    sync plan scoped to one team, and the wiki queue's write-nearest split
    (shipd-workspace workspace-team-wizard, workspace-chain-facilities,
    project-registry-semantics)."""

    def setUp(self):
        super().setUp()
        r = self.cli("workspace-init", self.root, "--git")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.alpha = os.path.join(self.root, "alpha")
        self.beta = os.path.join(self.root, "beta")
        for team_dir in (self.alpha, self.beta):
            os.makedirs(team_dir, exist_ok=True)
            r = self.cli("workspace-init", team_dir, "--nested", "--git")
            self.assertEqual(r.returncode, 0, r.stderr)
        r = self.cli(
            "workspace-project", "add", "main-app", "api", root=self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.cli(
            "workspace-project", "add", "team-app", "web", root=self.alpha)
        self.assertEqual(r.returncode, 0, r.stderr)
        # beta declares no project of its own.

    def wiki_of(self, ws_root):
        return os.path.join(ws_root, ".shipd", "wiki")

    def write_page(self, ws_root, slug, text):
        pages = os.path.join(self.wiki_of(ws_root), "wiki")
        os.makedirs(pages, exist_ok=True)
        with open(os.path.join(pages, slug + ".md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    # -- read-through / write-nearest -----------------------------------

    def test_base_page_reads_from_a_team_and_is_reported_as_inherited(self):
        self.write_page(self.root, "conventions", "# Conventions\n\nBase.\n")
        r = self.cli("cat", "wiki", "conventions", root=self.alpha)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Base.", r.stdout)
        self.assertIn("(inherited %s)" % self.root, r.stdout)

    def test_page_written_from_a_team_lands_only_in_its_own_store(self):
        self.write_page(self.alpha, "team-notes", "# Team notes\n\nAlpha.\n")
        self.assertTrue(os.path.isfile(
            os.path.join(self.wiki_of(self.alpha), "wiki", "team-notes.md")))
        self.assertFalse(os.path.isfile(
            os.path.join(self.wiki_of(self.root), "wiki", "team-notes.md")))
        r = self.cli("cat", "wiki", "team-notes", root=self.alpha)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Alpha.", r.stdout)
        self.assertNotIn("inherited", r.stdout)

    # -- registry shadowing -----------------------------------------------

    def test_a_teams_own_registry_shadows_the_base(self):
        r = self.cli("workspace-show", root=self.alpha)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("project team-app:", r.stdout)
        self.assertNotIn("project main-app:", r.stdout)
        self.assertNotIn("registry:", r.stdout)

    def test_a_team_declaring_none_inherits_the_base_registry(self):
        r = self.cli("workspace-show", root=self.beta)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("project main-app:", r.stdout)
        self.assertNotIn("project team-app:", r.stdout)
        self.assertIn("registry: %s" % self.root, r.stdout)

    # -- sync plan scoped to one team ---------------------------------

    def test_sync_plan_from_a_team_lists_only_that_teams_members(self):
        r = self.cli("workspace-sync", root=self.alpha)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("path: web", r.stdout)
        self.assertNotIn("path: api", r.stdout)

    # -- wiki queue write-nearest --------------------------------------

    def test_base_filed_question_answers_only_from_the_base(self):
        r = self.cli("wiki-init", root=self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.cli(
            "wiki-queue-add", "base-question",
            "--question", "Which registry wins?",
            "--options", "base or team",
            "--recommendation", "base",
            root=self.root)
        self.assertEqual(r.returncode, 0, r.stderr)

        r = self.cli(
            "wiki-queue-answer", "base-question", "--answer", "base",
            root=self.beta)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("queue has no block", r.stderr)

        r = self.cli(
            "wiki-queue-answer", "base-question", "--answer", "base",
            root=self.root)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
