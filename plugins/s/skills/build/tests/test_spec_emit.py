#!/usr/bin/env python3
"""Tests for spec_emit.py — staged validate-then-install of spec content
(spec-io staged-emission).

The CLI is driven as a black box via subprocess against a throwaway temp repo
root, with ``$HOME`` isolated so config resolution never reads the real home.
Written test-first; expected to FAIL until ``spec_emit.py`` lands."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "spec_emit.py"))


CLEAN_PLAN = (
    "# my-change\n"
    "Status: draft\n"
    "\n"
    "## Idea\n\nA one-sentence summary.\n\n"
    "### Motivation\n\nBecause it matters.\n\n"
    "### Details\n\nThe concrete changes.\n\n"
    "### Non-goals\n\n- Not that.\n\n"
    "## Implementation\n\nCarefully.\n"
)

CLEAN_DELTA = (
    "## ADDED Requirements\n\n"
    "### Requirement: Example\n"
    "id: example\n\n"
    "The system SHALL do a thing.\n\n"
    "#### Scenario: It works\n"
    "- **WHEN** something happens\n"
    "- **THEN** it is handled\n"
)

CLEAN_TASKS = "# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n"

CLEAN_BRIEF = (
    "# my-goal\n"
    "Status: open\n"
    "\n"
    "Get there.\n"
    "\n"
    "## Requirements\n"
    "\n"
    "- [ ] Do it\n"
)

CLEAN_EPIC = (
    "# reporting-overhaul\n"
    "Status: draft\n"
    "\n"
    "## Introduction\n\nWhy it matters.\n\n"
    "### Non-goals\n\n- Not that.\n\n"
    "## Decisions\n\nWhy.\n\n"
    "## Design\n\nHow.\n\n"
    "## Changes\n\n"
    "| Change | Description | Code | Integration | Unknowns | Risk |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
    "| csv-export | Export as CSV | low | medium | low | low |\n"
)


CLEAN_REPORT = (
    "# Payment API landscape\n"
    "\n"
    "## Summary\n"
    "\n"
    "Stripe leads on developer experience [1].\n"
    "\n"
    "## Sources\n"
    "\n"
    "1. Stripe docs — https://stripe.com/docs\n"
)

CLEAN_VIDEO_BRIEF = (
    "# Board walkthrough\n"
    "Video: board-walkthrough.mp4\n"
    "\n"
    "## Speakers\n"
    "\n"
    "- Ada — product lead\n"
    "\n"
    "## Intents\n"
    "\n"
    "### Explain the parked-member signal\n"
    "\n"
    "The board should surface parked members clearly [1].\n"
    "\n"
    "## Sources\n"
    "\n"
    "1. [00:14:22.4] Ada: parked members need a visible signal.\n"
)


class SpecEmitTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="spec-emit-test-")
        self.stage = tempfile.mkdtemp(prefix="spec-emit-stage-")
        self.home = tempfile.mkdtemp(prefix="spec-emit-home-")
        # Redirect flow-time-series capture (the change-install hook) to a
        # throwaway dir so no test writes to the real ~/.shipd/builds/flow.jsonl.
        # cli() copies os.environ, so the subprocess inherits this.
        self.flow_dir = tempfile.mkdtemp(prefix="spec-emit-flow-")
        self._old_flow = os.environ.get("AM_FLOW_LOG_DIR")
        os.environ["AM_FLOW_LOG_DIR"] = self.flow_dir

    def tearDown(self):
        if self._old_flow is None:
            os.environ.pop("AM_FLOW_LOG_DIR", None)
        else:
            os.environ["AM_FLOW_LOG_DIR"] = self._old_flow
        for d in (self.root, self.stage, self.home, self.flow_dir):
            shutil.rmtree(d, ignore_errors=True)

    def flow_records(self):
        """Every flow.jsonl record captured under this test's flow dir."""
        path = os.path.join(self.flow_dir, "flow.jsonl")
        records = []
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except OSError:
            pass
        return records

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def declare_workspace(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}}, fh)

    def stage_change(self, plan=CLEAN_PLAN, delta=CLEAN_DELTA,
                     tasks=CLEAN_TASKS):
        with open(os.path.join(self.stage, "plan.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(plan)
        cap = os.path.join(self.stage, "specs", "auth")
        os.makedirs(cap, exist_ok=True)
        with open(os.path.join(cap, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(delta)
        with open(os.path.join(self.stage, "tasks.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(tasks)

    def stage_file(self, text):
        path = os.path.join(self.stage, "artifact.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def planned_dir(self, name):
        return os.path.join(self.root, ".shipd", "planned", name)


class ChangeEmitTest(SpecEmitTestBase):
    def test_clean_change_installs(self):
        self.stage_change()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        dest = self.planned_dir("my-change")
        self.assertTrue(os.path.isfile(os.path.join(dest, "plan.md")))
        self.assertTrue(os.path.isfile(
            os.path.join(dest, "specs", "auth", "spec.md")))
        self.assertTrue(os.path.isfile(os.path.join(dest, "tasks.md")))

    def test_invalid_change_leaves_no_directory(self):
        # A plan missing its `### Non-goals` subsection is a lint error.
        bad_plan = CLEAN_PLAN.replace("### Non-goals\n\n- Not that.\n\n", "")
        self.stage_change(plan=bad_plan)
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(r.stdout + r.stderr)  # findings printed
        self.assertFalse(os.path.exists(self.planned_dir("my-change")))

    def test_existing_destination_refused_without_replace(self):
        self.stage_change()
        self.assertEqual(
            self.cli("change", "my-change", "--from", self.stage).returncode, 0)
        # Mark the installed copy so we can prove it was untouched.
        sentinel = os.path.join(self.planned_dir("my-change"), "sentinel")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("keep")
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(os.path.isfile(sentinel))

    def test_existing_destination_replaced_with_flag(self):
        self.stage_change()
        self.assertEqual(
            self.cli("change", "my-change", "--from", self.stage).returncode, 0)
        sentinel = os.path.join(self.planned_dir("my-change"), "sentinel")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("stale")
        r = self.cli("change", "my-change", "--from", self.stage, "--replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        # The stale sentinel is gone; the fresh artifacts are present.
        self.assertFalse(os.path.exists(sentinel))
        self.assertTrue(os.path.isfile(
            os.path.join(self.planned_dir("my-change"), "plan.md")))

    def stage_artefact(self, relpath="policy.md", content="Do this.\n"):
        path = os.path.join(self.stage, "artefacts", relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def test_referenced_artefact_installs(self):
        # A staging directory carrying an artefacts/ directory installs
        # whole-tree — the referenced file lands under the installed change
        # (shipd-spec-format per-change-artifact-layout).
        plan = CLEAN_PLAN.replace(
            "### Non-goals\n\n- Not that.\n\n",
            "### Non-goals\n\n- Not that.\n\n"
            "See `artefacts/policy.md` for the policy.\n\n")
        self.stage_change(plan=plan)
        self.stage_artefact()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(
            self.planned_dir("my-change"), "artefacts", "policy.md")))

    def test_unreferenced_artefact_is_refused(self):
        # The same staging directory with the reference removed: the linter's
        # artefact-reference-enforcement check refuses the install outright
        # (shipd-spec-lint artefact-reference-enforcement).
        self.stage_change()
        self.stage_artefact()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("artefacts/policy.md", r.stdout + r.stderr)
        self.assertFalse(os.path.exists(self.planned_dir("my-change")))


class InitiativeEmitTest(SpecEmitTestBase):
    def _brief_path(self, slug):
        return os.path.join(
            self.root, ".shipd", "initiatives", slug, "brief.md")

    def test_clean_brief_installs(self):
        self.declare_workspace()
        src = self.stage_file(CLEAN_BRIEF)
        r = self.cli("initiative", "my-goal", "--from", src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(self._brief_path("my-goal")))

    def test_invalid_brief_leaves_no_file(self):
        self.declare_workspace()
        bad = CLEAN_BRIEF.replace(
            "## Requirements\n\n- [ ] Do it\n", "")  # no requirements section
        src = self.stage_file(bad)
        r = self.cli("initiative", "my-goal", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(
            os.path.join(self.root, ".shipd", "initiatives", "my-goal")))

    # -- Nested workspace (shipd-workspace workspace-chain-facilities) --

    def cli_at(self, cwd, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True, env=env)

    def test_installs_into_nearest_workspace_never_an_enclosing_one(self):
        # self.root doubles as an outer, enclosing workspace; `inner` nests
        # beneath it and holds no initiatives of its own yet.
        self.declare_workspace()
        inner = os.path.join(self.root, "nested")
        os.makedirs(inner, exist_ok=True)
        with open(os.path.join(inner, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}}, fh)
        repo = os.path.join(inner, "repo")
        os.makedirs(repo, exist_ok=True)

        src = self.stage_file(CLEAN_BRIEF)
        r = self.cli_at(repo, "initiative", "my-goal", "--from", src)
        self.assertEqual(r.returncode, 0, r.stderr)

        inner_brief = os.path.join(
            inner, ".shipd", "initiatives", "my-goal", "brief.md")
        outer_brief = os.path.join(
            self.root, ".shipd", "initiatives", "my-goal", "brief.md")
        self.assertTrue(os.path.isfile(inner_brief))
        self.assertFalse(os.path.exists(outer_brief))


class EpicEmitTest(SpecEmitTestBase):
    def _epic_path(self, slug):
        return os.path.join(self.root, ".shipd", "epics", slug, "epic.md")

    def test_clean_epic_installs(self):
        src = self.stage_file(CLEAN_EPIC)
        r = self.cli("epic", "reporting-overhaul", "--from", src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(self._epic_path("reporting-overhaul")))

    def test_invalid_epic_leaves_no_file(self):
        bad = CLEAN_EPIC[:CLEAN_EPIC.index("## Changes")]  # drop Changes table
        src = self.stage_file(bad)
        r = self.cli("epic", "reporting-overhaul", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(
            os.path.join(self.root, ".shipd", "epics", "reporting-overhaul")))


class ResearchEmitTest(SpecEmitTestBase):
    def _report_path(self, slug):
        return os.path.join(
            self.root, ".shipd", "research", slug, "report.md")

    def test_clean_report_installs(self):
        src = self.stage_file(CLEAN_REPORT)
        r = self.cli("research", "payment-apis", "--from", src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(self._report_path("payment-apis")))

    def test_invalid_report_leaves_no_directory(self):
        # An unresolved citation marker ([4] over one source) is a lint error.
        bad = CLEAN_REPORT.replace(
            "developer experience [1].", "developer experience [4].")
        src = self.stage_file(bad)
        r = self.cli("research", "payment-apis", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(r.stdout + r.stderr)  # findings printed
        self.assertFalse(os.path.exists(
            os.path.join(self.root, ".shipd", "research", "payment-apis")))

    def test_supplied_uncited_document_installs(self):
        # A user-supplied context document — titled, but with no `## Sources`
        # section and no `[n]` markers — carries no citation signal, so the
        # skeleton checks never fire and the install is clean
        # (shipd-spec-format research-report-format).
        src = self.stage_file(
            "# Payments strategy brief\n"
            "\n"
            "## Context\n"
            "\n"
            "We move to a single processor next quarter.\n")
        r = self.cli("research", "payments-strategy", "--from", src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(self._report_path("payments-strategy")))

    def test_untitled_document_leaves_no_directory(self):
        # The title check always runs, citation signal or not.
        src = self.stage_file("Not a title.\n\nJust prose.\n")
        r = self.cli("research", "payments-strategy", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("line 1", r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(
            self.root, ".shipd", "research", "payments-strategy")))

    def test_existing_destination_refused_without_replace(self):
        src = self.stage_file(CLEAN_REPORT)
        self.assertEqual(
            self.cli("research", "payment-apis", "--from", src).returncode, 0)
        sentinel = os.path.join(
            os.path.dirname(self._report_path("payment-apis")), "sentinel")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("keep")
        r = self.cli("research", "payment-apis", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(os.path.isfile(sentinel))

    def test_existing_destination_replaced_with_flag(self):
        src = self.stage_file(CLEAN_REPORT)
        self.assertEqual(
            self.cli("research", "payment-apis", "--from", src).returncode, 0)
        sentinel = os.path.join(
            os.path.dirname(self._report_path("payment-apis")), "sentinel")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("stale")
        r = self.cli("research", "payment-apis", "--from", src, "--replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(sentinel))
        self.assertTrue(os.path.isfile(self._report_path("payment-apis")))


class VideoEmitTest(SpecEmitTestBase):
    """The staged ``video`` emit subcommand (spec-io staged-emission),
    installing a video intent brief at ``<content-dir>/video/<slug>/
    brief.md`` under the validate-then-install rule.

    Written test-first; expected to FAIL until ``video`` lands in
    ``spec_emit.py`` (task 3.2/3.3)."""

    def _brief_path(self, slug):
        return os.path.join(self.root, ".shipd", "video", slug, "brief.md")

    def test_clean_brief_installs(self):
        src = self.stage_file(CLEAN_VIDEO_BRIEF)
        r = self.cli("video", "board-walkthrough", "--from", src)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(self._brief_path("board-walkthrough")))

    def test_uncited_intent_leaves_no_directory(self):
        # Dropping the intent's [1] marker is a lint error.
        bad = CLEAN_VIDEO_BRIEF.replace(
            "The board should surface parked members clearly [1].",
            "The board should surface parked members clearly.")
        src = self.stage_file(bad)
        r = self.cli("video", "board-walkthrough", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(r.stdout + r.stderr)  # findings printed
        self.assertFalse(os.path.exists(
            os.path.join(self.root, ".shipd", "video", "board-walkthrough")))

    def test_existing_destination_refused_without_replace(self):
        src = self.stage_file(CLEAN_VIDEO_BRIEF)
        self.assertEqual(
            self.cli("video", "board-walkthrough", "--from", src).returncode,
            0)
        sentinel = os.path.join(
            os.path.dirname(self._brief_path("board-walkthrough")),
            "sentinel")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("keep")
        r = self.cli("video", "board-walkthrough", "--from", src)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(os.path.isfile(sentinel))


class WikiEmitTest(SpecEmitTestBase):
    """The staged ``wiki`` emit subcommand (spec-io wiki-emission).

    ``self.root`` doubles as the workspace root; the store lives at
    ``<root>/.shipd/wiki/``. A staging dir mirrors a store subset."""

    def wiki(self):
        return os.path.join(self.root, ".shipd", "wiki")

    def _w(self, rel, text):
        path = os.path.join(self.wiki(), rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def seed_store(self):
        """A clean seeded store: one page cataloged by a matching index."""
        os.makedirs(os.path.join(self.wiki(), "sources"), exist_ok=True)
        os.makedirs(os.path.join(self.wiki(), "wiki"), exist_ok=True)
        self._w("schema.md", "# Wiki schema\n\nConventions.\n")
        self._w("index.md", "# Index\n\n- [[welcome]] — The welcome page.\n")
        self._w("log.md",
                "# Log\n\n## [2026-07-30] wiki-init | seeded the store\n\n"
                "Init.\n")
        self._w("queue.md", "# Queue\n")
        self._w("wiki/welcome.md", "# Welcome\n\nHello.\n")

    def stage_wiki(self, files):
        """Write ``{relpath: text}`` into the staging directory."""
        for rel, text in files.items():
            path = os.path.join(self.stage, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)

    def _snapshot(self):
        snap = {}
        for dirpath, _dirs, names in os.walk(self.wiki()):
            for name in names:
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as fh:
                    snap[os.path.relpath(path, self.wiki())] = fh.read()
        return snap

    def test_page_install_with_index_update(self):
        self.declare_workspace()
        self.seed_store()
        self.stage_wiki({
            "wiki/intro.md": "# Intro\n\nThe intro page.\n",
            "index.md": ("# Index\n\n- [[welcome]] — The welcome page.\n"
                         "- [[intro]] — Introduction.\n"),
        })
        r = self.cli("wiki", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.wiki(), "wiki", "intro.md")))
        with open(os.path.join(self.wiki(), "index.md"),
                  encoding="utf-8") as fh:
            self.assertIn("[[intro]]", fh.read())

    def test_invalid_result_rolls_back(self):
        self.declare_workspace()
        self.seed_store()
        before = self._snapshot()
        # An orphan page (no index entry) plus a dead wikilink.
        self.stage_wiki({"wiki/orphan.md": "# Orphan\n\nSee [[ghost]].\n"})
        r = self.cli("wiki", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(r.stdout + r.stderr)  # findings printed
        self.assertEqual(self._snapshot(), before)  # byte-for-byte restore
        self.assertFalse(os.path.exists(
            os.path.join(self.wiki(), "wiki", "orphan.md")))

    def test_source_overwrite_refused(self):
        self.declare_workspace()
        self.seed_store()
        self._w("sources/notes.md", "original notes\n")
        before = self._snapshot()
        self.stage_wiki({
            "sources/notes.md": "new notes\n",
            "wiki/intro.md": "# Intro\n\nThe intro page.\n",
        })
        r = self.cli("wiki", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("source", r.stderr.lower())
        self.assertEqual(self._snapshot(), before)  # nothing installed
        self.assertFalse(os.path.exists(
            os.path.join(self.wiki(), "wiki", "intro.md")))

    def test_requires_workspace(self):
        # No workspace declared → the mode fails naming the missing workspace.
        self.stage_wiki({"wiki/intro.md": "# Intro\n\nHi.\n"})
        r = self.cli("wiki", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no workspace", r.stderr.lower())

    # -- Nested workspace (shipd-workspace workspace-chain-facilities) --

    def cli_at(self, cwd, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True, env=env)

    def _seed_wiki_at(self, wiki_dir):
        """A clean seeded store at an arbitrary ``wiki_dir``: one page
        cataloged by a matching index — mirrors :meth:`seed_store`, which is
        fixed to ``self.wiki()``."""
        os.makedirs(os.path.join(wiki_dir, "sources"), exist_ok=True)
        os.makedirs(os.path.join(wiki_dir, "wiki"), exist_ok=True)

        def w(rel, text):
            path = os.path.join(wiki_dir, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)

        w("schema.md", "# Wiki schema\n\nConventions.\n")
        w("index.md", "# Index\n\n- [[welcome]] — The welcome page.\n")
        w("log.md",
          "# Log\n\n## [2026-07-30] wiki-init | seeded the store\n\n"
          "Init.\n")
        w("queue.md", "# Queue\n")
        w("wiki/welcome.md", "# Welcome\n\nHello.\n")

    def test_wiki_installs_into_nearest_workspace_never_an_enclosing_one(self):
        # self.root doubles as an outer, enclosing workspace, seeded with its
        # own store; `inner` nests beneath it with its own, separately seeded
        # store.
        self.declare_workspace()
        self.seed_store()
        outer_before = self._snapshot()

        inner = os.path.join(self.root, "nested")
        os.makedirs(inner, exist_ok=True)
        with open(os.path.join(inner, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}}, fh)
        inner_wiki = os.path.join(inner, ".shipd", "wiki")
        self._seed_wiki_at(inner_wiki)
        repo = os.path.join(inner, "repo")
        os.makedirs(repo, exist_ok=True)

        self.stage_wiki({
            "wiki/intro.md": "# Intro\n\nThe intro page.\n",
            "index.md": ("# Index\n\n- [[welcome]] — The welcome page.\n"
                         "- [[intro]] — Introduction.\n"),
        })
        r = self.cli_at(repo, "wiki", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)

        self.assertTrue(os.path.isfile(
            os.path.join(inner_wiki, "wiki", "intro.md")))
        self.assertFalse(os.path.exists(
            os.path.join(self.wiki(), "wiki", "intro.md")))
        self.assertEqual(self._snapshot(), outer_before)  # outer untouched

    # -- Auto-commit (shipd-wiki wiki-autocommit) --

    def _git(self, *args):
        subprocess.run(["git", "-C", self.root, *args],
                       capture_output=True, text=True, check=True)

    def _init_git(self):
        subprocess.run(["git", "init", "-q", self.root],
                       capture_output=True, text=True, check=True)
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")

    def _commit_baseline(self):
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "baseline")

    def _commit_count(self):
        r = subprocess.run(
            ["git", "-C", self.root, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True)
        return int(r.stdout.strip())

    def _head_subject(self):
        r = subprocess.run(
            ["git", "-C", self.root, "log", "-1", "--format=%s"],
            capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def _head_files(self):
        r = subprocess.run(
            ["git", "-C", self.root, "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True)
        return sorted(p for p in r.stdout.split("\n") if p.strip())

    def test_successful_emit_commits_installed_files(self):
        self.declare_workspace()
        self.seed_store()
        self._init_git()
        self._commit_baseline()
        before = self._commit_count()
        self.stage_wiki({
            "wiki/intro.md": "# Intro\n\nThe intro page.\n",
            "index.md": ("# Index\n\n- [[welcome]] — The welcome page.\n"
                         "- [[intro]] — Introduction.\n"),
        })
        r = self.cli("wiki", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._commit_count(), before + 1)
        self.assertEqual(self._head_subject(), "shipd-wiki: emit 2 file(s)")
        self.assertEqual(
            self._head_files(),
            [".shipd/wiki/index.md", ".shipd/wiki/wiki/intro.md"])

    def test_non_git_workspace_installs_without_git(self):
        self.declare_workspace()
        self.seed_store()
        self.stage_wiki({
            "wiki/intro.md": "# Intro\n\nThe intro page.\n",
            "index.md": ("# Index\n\n- [[welcome]] — The welcome page.\n"
                         "- [[intro]] — Introduction.\n"),
        })
        r = self.cli("wiki", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.wiki(), "wiki", "intro.md")))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".git")))

    def test_lint_failing_emit_makes_no_commit(self):
        self.declare_workspace()
        self.seed_store()
        self._init_git()
        self._commit_baseline()
        before = self._commit_count()
        # An orphan page (no index entry) plus a dead wikilink → lint fails.
        self.stage_wiki({"wiki/orphan.md": "# Orphan\n\nSee [[ghost]].\n"})
        r = self.cli("wiki", "--from", self.stage)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self._commit_count(), before)


class ChangeInstallFlowHookTest(SpecEmitTestBase):
    """A change install appends a best-effort flow snapshot
    (delivery-metrics flow-timeseries)."""

    def _seed_epic(self):
        # An epic referencing my-change so, once installed (draft), the snapshot
        # lists it in the draft band.
        epic_dir = os.path.join(self.root, ".shipd", "epics", "e1")
        os.makedirs(epic_dir)
        with open(os.path.join(epic_dir, "epic.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# e1\nStatus: active\n\n## Changes\n\n"
                     "| Change | Description | Risk |\n| --- | --- | --- |\n"
                     "| my-change | the member | low |\n")

    def test_change_install_appends_a_flow_record(self):
        self._seed_epic()
        self.stage_change()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        records = self.flow_records()
        self.assertTrue(records)
        rec = records[-1]
        self.assertEqual(rec["root"], os.path.abspath(self.root))
        self.assertEqual(rec["states"].get("draft"), ["my-change"])

    def test_unwritable_flow_dest_does_not_fail_install(self):
        self.stage_change()
        blocker = os.path.join(self.root, "blocker")
        os.makedirs(self.root, exist_ok=True)
        with open(blocker, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.environ["AM_FLOW_LOG_DIR"] = os.path.join(blocker, "nope")
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.planned_dir("my-change"), "plan.md")))


class ChangeInstallStoreAutocommitTest(SpecEmitTestBase):
    """A change installed into an externally resolved content directory
    auto-commits locally in the store, scoped to the installed files; an
    in-repo content directory never does (shipd-config store-autocommit)."""

    def setUp(self):
        super().setUp()
        self.store = tempfile.mkdtemp(prefix="spec-emit-store-")
        self.addCleanup(shutil.rmtree, self.store, True)
        # The per-repo folder under the store is the repo directory's basename
        # (the non-git fallback — this throwaway root is not a git repo).
        self.repo_folder = os.path.basename(self.root)

    def declare_store(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"store_root": self.store}, fh)

    def _git(self, target, *args):
        subprocess.run(["git", "-C", target, *args],
                       capture_output=True, text=True, check=True)

    def _init_git(self, target):
        subprocess.run(["git", "init", "-q", target],
                       capture_output=True, text=True, check=True)
        self._git(target, "config", "user.email", "test@example.com")
        self._git(target, "config", "user.name", "Test")
        with open(os.path.join(target, "README.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("store\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "baseline")

    def _commit_count(self, target):
        r = subprocess.run(
            ["git", "-C", target, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True)
        return int(r.stdout.strip())

    def _head_files(self, target):
        r = subprocess.run(
            ["git", "-C", target, "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True)
        return sorted(p for p in r.stdout.split("\n") if p.strip())

    def test_install_into_git_store_commits_the_installed_files(self):
        self._init_git(self.store)
        self.declare_store()
        before = self._commit_count(self.store)
        self.stage_change()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        dest = os.path.join(self.store, self.repo_folder, "planned",
                            "my-change")
        self.assertTrue(os.path.isfile(os.path.join(dest, "plan.md")))
        self.assertEqual(self._commit_count(self.store), before + 1)
        prefix = "%s/planned/my-change/" % self.repo_folder
        committed = self._head_files(self.store)
        # The install's own files, plus the `schema` marker this first install
        # stamps beside them (schema-versioning schema-marker-stamping) — one
        # commit, scoped to exactly what the verb wrote.
        self.assertEqual(
            committed,
            sorted([prefix + "plan.md", prefix + "specs/auth/spec.md",
                    prefix + "tasks.md", "%s/schema" % self.repo_folder]))

    def test_in_repo_install_never_commits(self):
        # No store_root: the content directory is in-repo, so the install is
        # the skill/PR workflow's to commit, never the engine's.
        self._init_git(self.root)
        before = self._commit_count(self.root)
        self.stage_change()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(
            os.path.join(self.planned_dir("my-change"), "plan.md")))
        self.assertEqual(self._commit_count(self.root), before)

    def test_non_git_store_installs_without_a_commit(self):
        self.declare_store()
        self.stage_change()
        r = self.cli("change", "my-change", "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(
            self.store, self.repo_folder, "planned", "my-change", "plan.md")))
        self.assertFalse(os.path.exists(os.path.join(self.store, ".git")))
        self.assertEqual(r.stderr.strip(), "")


if __name__ == "__main__":
    unittest.main()
