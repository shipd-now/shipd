#!/usr/bin/env python3
"""Unit tests for spec_lint: each structural and delta check against good and
malformed fixtures, plus the gating exit code."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
FIXTURES = os.path.join(HERE, "fixtures")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_lint as sl  # noqa: E402
import spec_common as sc  # noqa: E402

SAMPLE_ROOT = os.path.join(FIXTURES, "sample")
BAD_ROOT = os.path.join(FIXTURES, "bad")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def lint_delta_text(text):
    errors = []
    sl.lint_delta_spec(text, "<test>", errors)
    return [str(e) for e in errors]


def bad_delta_errors(name):
    path = os.path.join(BAD_ROOT, ".shipd", "planned", name,
                        "specs", "auth", "spec.md")
    return lint_delta_text(read(path))


def has(errors, needle):
    return any(needle in e for e in errors)


def declare_workspace(ws, registry=None):
    """Declare ``registry`` (default ``{}``) as the ``workspace`` object in
    ``<ws>/.shipd-config.json`` — the config-file workspace marker."""
    data = {"workspace": registry if registry is not None else {}}
    with open(os.path.join(ws, sc.CONFIG_FILENAME), "w",
              encoding="utf-8") as fh:
        json.dump(data, fh)


class StructuralCheckTest(unittest.TestCase):
    def test_missing_id(self):
        errors = bad_delta_errors("missing-id")
        self.assertTrue(has(errors, "has no `id:` line"))

    def test_duplicate_id(self):
        errors = bad_delta_errors("duplicate-id")
        self.assertTrue(has(errors, "duplicate id 'rate-limit-login'"))

    def test_missing_shall_statement(self):
        errors = lint_delta_text(
            "## ADDED Requirements\n\n"
            "### Requirement: No norm\nid: no-norm\n\n"
            "This describes a thing without a normative keyword.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertTrue(has(errors, "no SHALL/MUST normative statement"))

    def test_missing_scenario(self):
        errors = lint_delta_text(
            "## ADDED Requirements\n\n"
            "### Requirement: No scenario\nid: no-scenario\n\n"
            "The system SHALL do something.\n")
        self.assertTrue(has(errors, "has no `#### Scenario:` block"))

    def test_wellformed_requirement_passes(self):
        errors = lint_delta_text(
            "## ADDED Requirements\n\n"
            "### Requirement: Good\nid: good\n\n"
            "The system SHALL be good.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertEqual(errors, [])


class DeltaCheckTest(unittest.TestCase):
    def test_unknown_operation_header(self):
        errors = bad_delta_errors("unknown-op")
        self.assertTrue(has(errors, "unknown operation header"))

    def test_mis_leveled_scenario(self):
        errors = bad_delta_errors("scenario-level")
        self.assertTrue(has(errors, "uses 3 hashtags, expected 4"))

    def test_missing_base(self):
        errors = bad_delta_errors("missing-base")
        self.assertTrue(has(errors, "has no `base:` line"))

    def test_removal_without_migration(self):
        errors = bad_delta_errors("removal-no-migration")
        self.assertTrue(has(errors, "has no `Migration:` note"))
        self.assertFalse(has(errors, "has no `Reason:` note"))

    def test_removal_without_reason(self):
        errors = lint_delta_text(
            "## REMOVED Requirements\n\n"
            "### Requirement: Legacy\nid: legacy\nbase: 000000000000\n"
            "Migration: none\n")
        self.assertTrue(has(errors, "has no `Reason:` note"))

    def test_rename_missing_target(self):
        errors = lint_delta_text(
            "## RENAMED Requirements\n\n- FROM: old-id\n")
        self.assertTrue(has(errors, "is missing a `TO:` id"))

    def test_rename_missing_source(self):
        errors = lint_delta_text(
            "## RENAMED Requirements\n\n- FROM:\n  TO: new-id\n")
        self.assertTrue(has(errors, "is missing a `FROM:` id"))

    def test_rename_invalid_kebab_target(self):
        errors = lint_delta_text(
            "## RENAMED Requirements\n\n- FROM: old-id\n  TO: Not_Kebab\n")
        self.assertTrue(has(errors, "not a valid kebab-case slug"))


class ValidFixtureTest(unittest.TestCase):
    def test_valid_change_is_clean(self):
        self.assertEqual(sl.lint_change(SAMPLE_ROOT, "sample-change"), [])

    def test_valid_master_library_is_clean(self):
        self.assertEqual(sl.lint_library(SAMPLE_ROOT), [])


class PlanHeaderTest(unittest.TestCase):
    """Plan-header and section validation (shipd-spec-lint
    proposal-header-validation)."""

    VALID_BODY = ("\n## Idea\nOne-sentence summary.\n\n"
                  "### Motivation\nBecause.\n\n"
                  "### Details\nThe concrete changes.\n\n"
                  "### Non-goals\nNot that.\n\n"
                  "## Implementation\nLike so.\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _header_errors(self, change, plan_text=None):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(cdir, exist_ok=True)
        if plan_text is not None:
            with open(os.path.join(cdir, "plan.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(plan_text)
        errors = []
        sl.check_plan_header(self.root, change, errors)
        return [str(e) for e in errors]

    def test_valid_header_passes(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n" + self.VALID_BODY)
        self.assertEqual(errors, [])

    def test_missing_status_line_fails(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\n" + self.VALID_BODY)
        self.assertTrue(has(errors, "no `Status:` line"))

    def test_invalid_status_value_fails(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: in-progress\n" + self.VALID_BODY)
        self.assertTrue(has(errors, "in-progress"))

    def test_mismatched_title_fails(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode\nStatus: ready\n" + self.VALID_BODY)
        self.assertTrue(has(errors, "expected title '# dark-mode-toggle'"))

    def test_missing_plan_fails(self):
        errors = self._header_errors("dark-mode-toggle", plan_text=None)
        self.assertTrue(has(errors, "no plan.md"))

    def test_missing_idea_section_fails(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n\n## Implementation\nHow.\n")
        self.assertTrue(has(errors, "no level-2 `## Idea` section"))

    def test_missing_implementation_section_fails(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n\n## Idea\nWhy.\n")
        self.assertTrue(has(errors, "no level-2 `## Implementation` section"))

    def test_missing_non_goals_subsection_fails(self):
        # Both level-2 sections present, but no `### Non-goals` heading.
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n\n## Idea\nWhy.\n\n"
            "## Implementation\nHow.\n")
        self.assertTrue(has(errors, "### Non-goals"))

    def test_missing_motivation_subsection_fails(self):
        # Both level-2 sections and `### Details`/`### Non-goals` present, but
        # no `### Motivation` heading. Expected to FAIL until the rule lands
        # (task 1.2).
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n\n## Idea\nSummary.\n\n"
            "### Details\nThe changes.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nHow.\n")
        self.assertTrue(has(errors, "### Motivation"))

    def test_missing_details_subsection_fails(self):
        # Both level-2 sections and `### Motivation`/`### Non-goals` present,
        # but no `### Details` heading. Expected to FAIL until the rule lands
        # (task 1.2).
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n\n## Idea\nSummary.\n\n"
            "### Motivation\nBecause.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nHow.\n")
        self.assertTrue(has(errors, "### Details"))

    def test_all_three_subsections_pass(self):
        # A plan carrying `### Motivation`, `### Details`, and `### Non-goals`
        # lints clean.
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: ready\n" + self.VALID_BODY)
        self.assertEqual(errors, [])

    def test_sample_fixture_carries_non_goals(self):
        # The updated sample fixture has a `### Non-goals` subsection, so its
        # plan header lints clean.
        errors = []
        sl.check_plan_header(SAMPLE_ROOT, "sample-change", errors)
        self.assertEqual([str(e) for e in errors], [])

    def test_rejected_status_with_gate_section_passes(self):
        # `rejected` is the sixth valid status, and the gate-owned
        # `## Context insufficient` section preceding `## Idea` is tolerated in
        # any status (shipd-spec-lint proposal-header-validation). Expected to FAIL
        # until `rejected` joins VALID_STATUSES (task 1.2).
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: rejected\n\n"
            "## Context insufficient\n\n"
            "Missing context.\n\n- No master for the target capability.\n"
            + self.VALID_BODY)
        self.assertEqual(errors, [])

    def test_unknown_status_still_fails(self):
        errors = self._header_errors(
            "dark-mode-toggle",
            "# dark-mode-toggle\nStatus: parked\n" + self.VALID_BODY)
        self.assertTrue(has(errors, "parked"))


class PlanQuestionsAndAnswersTest(unittest.TestCase):
    """Optional ``## Questions and answers`` plan-section validation
    (shipd-spec-lint qa-section-validation, shipd-spec-format
    plan-document-sections). An absent section produces no finding; a present
    section must hold `### Q<n>:` entries numbered sequentially from `Q1`, each
    carrying `**Question:**`, `**Answered by:**`, and `**Answer:**` fields."""

    HEADER = "# dark-mode-toggle\nStatus: ready\n"
    BODY = ("\n## Idea\nOne-sentence summary.\n\n"
            "### Motivation\nBecause.\n\n"
            "### Details\nThe concrete changes.\n\n"
            "### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n")

    ENTRY_1 = ("### Q1: Which store holds the toggle?\n"
               "- **Question:** Should the toggle live in the settings store "
               "or the theme store? Options: (1) settings; (2) theme. "
               "Recommendation: (1).\n"
               "- **Verdict:** ANSWER\n"
               "- **Answered by:** ORACLE\n"
               "- **Answer:** The settings store — option 1. It already "
               "persists user-scoped display preferences.\n"
               "- **Cited:** verified/settings-store\n")
    ENTRY_2 = ("### Q2: What does the report call the toggle?\n"
               "- **Question:** Should the report name the toggle 'dark mode' "
               "or 'theme'? Options: (1) dark mode; (2) theme.\n"
               "- **Verdict:** INSUFFICIENT\n"
               "- **Answered by:** USER\n"
               "- **Answer:** Call it 'dark mode' everywhere in the report.\n"
               "- **Queued:** q-report-format\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _qa_errors(self, section=None, change="dark-mode-toggle"):
        """Write a valid plan for ``change``, optionally carrying a
        ``## Questions and answers`` section holding ``section``, and return
        the questions-and-answers findings as strings."""
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(cdir, exist_ok=True)
        text = self.HEADER + self.BODY
        if section is not None:
            text += "\n## Questions and answers\n\n" + section
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        errors = []
        sl.check_plan_qa_section(self.root, change, errors)
        return [str(e) for e in errors]

    def test_absent_section_is_clean(self):
        self.assertEqual(self._qa_errors(section=None), [])

    def test_empty_section_errors(self):
        errors = self._qa_errors("")
        self.assertTrue(has(errors, "Questions and answers"))

    def test_non_sequential_first_entry_errors(self):
        # The first entry is headed `### Q2:`, so the numbering does not start
        # at Q1; the error names the offending entry.
        errors = self._qa_errors(self.ENTRY_2)
        self.assertTrue(has(errors, "Q2"))

    def test_missing_question_field_errors(self):
        entry = "\n".join(
            ln for ln in self.ENTRY_1.splitlines()
            if not ln.startswith("- **Question:**")) + "\n"
        errors = self._qa_errors(entry)
        self.assertTrue(has(errors, "Q1"))
        self.assertTrue(has(errors, "**Question:**"))

    def test_missing_answered_by_field_errors(self):
        entry = "\n".join(
            ln for ln in self.ENTRY_1.splitlines()
            if not ln.startswith("- **Answered by:**")) + "\n"
        errors = self._qa_errors(entry)
        self.assertTrue(has(errors, "Q1"))
        self.assertTrue(has(errors, "**Answered by:**"))

    def test_missing_answer_field_errors(self):
        entry = "\n".join(
            ln for ln in self.ENTRY_1.splitlines()
            if not ln.startswith("- **Answer:**")) + "\n"
        errors = self._qa_errors(entry)
        self.assertTrue(has(errors, "Q1"))
        self.assertTrue(has(errors, "**Answer:**"))

    def test_malformed_entry_header_errors(self):
        errors = self._qa_errors(
            "### Which store holds the toggle?\n"
            "- **Question:** Settings or theme store?\n"
            "- **Verdict:** ANSWER\n"
            "- **Answered by:** ORACLE\n"
            "- **Answer:** The settings store.\n")
        self.assertTrue(has(errors, "### Q<n>:"))

    def test_conforming_two_entry_section_is_clean(self):
        errors = self._qa_errors(self.ENTRY_1 + "\n" + self.ENTRY_2)
        self.assertEqual(errors, [])

    def test_conforming_section_is_clean_through_lint_change(self):
        # The pass is wired into the change lint, so a conforming section
        # produces no finding there either.
        change = "dark-mode-toggle"
        self._qa_errors(self.ENTRY_1 + "\n" + self.ENTRY_2, change=change)
        errors = [str(e) for e in sl.lint_change(self.root, change)]
        self.assertFalse(has(errors, "Questions and answers"))

    def test_malformed_section_errors_through_lint_change(self):
        change = "dark-mode-toggle"
        self._qa_errors(self.ENTRY_2, change=change)
        errors = [str(e) for e in sl.lint_change(self.root, change)]
        self.assertTrue(has(errors, "Q2"))


class PlanMetadataTest(unittest.TestCase):
    """Header-metadata validation (shipd-spec-lint plan-metadata-validation,
    plan-profile-values, initiative-attaches-through-epic). The optional
    metadata block is the contiguous ``Key: value`` run immediately after the
    ``Status:`` line.

    These tests are written test-first and are expected to FAIL until
    ``check_plan_metadata`` lands in ``spec_lint.py`` (task 1.3)."""

    BODY = ("\n## Idea\nBecause.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _errors(self, change, header):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(header + self.BODY)
        errors = []
        sl.check_plan_metadata(self.root, change, errors)
        return [str(e) for e in errors]

    def test_metadata_free_plan_lints_clean(self):
        errors = self._errors("c", "# c\nStatus: ready\n")
        self.assertEqual(errors, [])

    def test_all_recognized_keys_lint_clean(self):
        errors = self._errors(
            "c",
            "# c\nStatus: ready\nProfile: lite\nEpic: reporting-overhaul\n"
            "Theme: reliability\n")
        self.assertEqual(errors, [])

    def test_standalone_initiative_lints_clean(self):
        errors = self._errors(
            "c", "# c\nStatus: ready\nInitiative: mvp-readiness\n")
        self.assertEqual(errors, [])

    def test_unrecognized_key_errors(self):
        errors = self._errors("c", "# c\nStatus: ready\nThem: reliability\n")
        self.assertTrue(has(errors, "Them"))

    def test_invalid_profile_value_errors(self):
        errors = self._errors("c", "# c\nStatus: ready\nProfile: quick\n")
        self.assertTrue(has(errors, "quick"))

    def test_non_kebab_value_errors(self):
        errors = self._errors("c", "# c\nStatus: ready\nTheme: Not Kebab\n")
        self.assertTrue(has(errors, "Not Kebab"))

    def test_epic_with_initiative_errors(self):
        errors = self._errors(
            "c",
            "# c\nStatus: ready\nEpic: reporting-overhaul\n"
            "Initiative: mvp-readiness\n")
        self.assertTrue(has(errors, "epic"))

    def test_repeated_fixes_lines_lint_clean(self):
        # `Fixes:` is a recognized, repeatable key naming shipped changes this
        # plan remediates; two kebab-case values lint clean.
        errors = self._errors(
            "c",
            "# c\nStatus: ready\nFixes: some-shipped-slug\n"
            "Fixes: another-shipped-slug\n")
        self.assertEqual(errors, [])

    def test_non_kebab_fixes_value_errors(self):
        errors = self._errors("c", "# c\nStatus: ready\nFixes: Not_Kebab\n")
        self.assertTrue(has(errors, "Not_Kebab"))


class ThemeVocabularyTest(unittest.TestCase):
    """Theme vocabulary validation against the resolved layered configuration's
    ``valid_themes`` key, declared in ``.shipd-config.json`` (shipd-spec-lint
    plan-metadata-validation / shipd-spec-format theme-vocabulary-config). ``$HOME``
    is overridden so the real home config never leaks into resolution."""

    BODY = ("\n## Idea\nBecause.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_config(self, text):
        with open(os.path.join(self.root, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def _errors(self, theme):
        change = "c"
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# c\nStatus: ready\nTheme: %s\n" % theme + self.BODY)
        errors = []
        sl.check_plan_metadata(self.root, change, errors)
        return [str(e) for e in errors]

    def test_theme_outside_vocabulary_errors(self):
        self._write_config('{"valid_themes": ["reliability"]}')
        self.assertTrue(has(self._errors("speed"), "speed"))

    def test_theme_in_vocabulary_passes(self):
        self._write_config('{"valid_themes": ["reliability"]}')
        self.assertEqual(self._errors("reliability"), [])

    def test_no_config_accepts_any_kebab_theme(self):
        # No .shipd-config.json written anywhere in the resolved chain.
        self.assertEqual(self._errors("any-label"), [])

    def test_malformed_config_errors_naming_the_file(self):
        self._write_config('{"valid_themes": [')
        self.assertTrue(has(self._errors("reliability"), sc.CONFIG_FILENAME))


class ContextEconomyWarningTest(unittest.TestCase):
    """Context-economy warning (shipd-spec-lint context-economy-warning):
    oversized plan.md warns on stderr but never affects the exit code."""

    DELTA = ("## ADDED Requirements\n\n"
             "### Requirement: Good\nid: good\n\n"
             "The system SHALL be good.\n\n"
             "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_change(self, change, plan_text):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(plan_text)
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self.DELTA)

    def _run(self, change):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main([change, "--root", self.root])
        return code, err.getvalue()

    def test_oversized_plan_warns_and_exits_zero(self):
        filler = "filler text " * 800  # ~9,600 chars, over the ~8,000 budget
        self._write_change(
            "big-change",
            "# big-change\nStatus: ready\n\n## Idea\n%s\n\n"
            "### Motivation\nBecause.\n\n### Details\nThe changes.\n\n"
            "### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n" % filler)
        code, err = self._run("big-change")
        self.assertEqual(code, 0)
        self.assertIn("WARNING:", err)
        self.assertIn("plan.md", err)
        self.assertIn("context-economy budget", err)

    def test_lean_change_emits_no_warning(self):
        self._write_change(
            "lean-change",
            "# lean-change\nStatus: ready\n\n## Idea\nA summary.\n\n"
            "### Motivation\nWhy.\n\n### Details\nThe changes.\n\n"
            "### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n")
        code, err = self._run("lean-change")
        self.assertEqual(code, 0)
        self.assertNotIn("WARNING:", err)


class TaskTraceabilityTest(unittest.TestCase):
    """Traceability tag enforcement (shipd-spec-lint traceability-tag-enforcement):
    every checkbox task in tasks.md carries exactly one well-formed
    ``[req: ...]`` tag whose ids resolve against the change's own delta specs.

    These tests are written test-first and are expected to FAIL until the rule
    lands in ``spec_lint.py`` (task 2.1)."""

    IDS = ("export-report-csv", "wire-up-flag")

    # The pending checkbox marker, assembled by concatenation so no
    # checkbox-shaped marker ever lands at the start of a line in this file.
    BOX = "- " + "[ ]"
    DONE_BOX = "- " + "[x]"

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _delta(self, ids):
        """A delta spec declaring one ADDED requirement per id, so those ids
        resolve as the change's own requirement ids."""
        parts = ["## ADDED Requirements"]
        for rid in ids:
            parts.append(
                "### Requirement: %s\nid: %s\n\n"
                "The system SHALL provide %s.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b" % (rid, rid, rid))
        return "\n\n".join(parts) + "\n"

    def _write_change(self, change, task_lines, ids=IDS, with_plan=False):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self._delta(ids))
        with open(os.path.join(cdir, "tasks.md"), "w", encoding="utf-8") as fh:
            fh.write("## 1. Work\n\n" + "\n".join(task_lines) + "\n")
        if with_plan:
            with open(os.path.join(cdir, "plan.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("# %s\nStatus: ready\n\n## Idea\nA summary.\n\n"
                         "### Motivation\nWhy.\n\n### Details\nThe changes.\n\n"
                         "### Non-goals\nNot that.\n\n"
                         "## Implementation\nHow.\n" % change)

    def _errors(self, task_lines, ids=IDS):
        change = "trace-change"
        self._write_change(change, task_lines, ids)
        errors = []
        sl.check_task_traceability(self.root, change, errors)
        return [str(e) for e in errors]

    def test_missing_tag_is_an_error(self):
        errors = self._errors(["- [ ] 1.1 Do the thing"])
        self.assertTrue(errors)

    def test_unresolvable_id_names_the_id(self):
        errors = self._errors(["- [ ] 1.1 [req: no-such-requirement] Do it"])
        self.assertTrue(has(errors, "no-such-requirement"))

    def test_two_tags_on_one_task_is_an_error(self):
        errors = self._errors(
            ["- [ ] 1.1 [req: export-report-csv] [req: wire-up-flag] Do it"])
        self.assertTrue(errors)

    def test_wildcard_combined_with_id_is_an_error(self):
        errors = self._errors(["- [ ] 1.1 [req: *, export-report-csv] Do it"])
        self.assertTrue(errors)

    def test_fully_tagged_file_passes(self):
        errors = self._errors([
            "- [ ] 1.1 [req: export-report-csv] Add the exporter",
            "- [ ] 1.2 [req: wire-up-flag] Wire it up",
        ])
        self.assertEqual(errors, [])

    def test_lone_wildcard_barrier_passes(self):
        errors = self._errors([
            "- [ ] 1.1 [req: export-report-csv] Add the exporter",
            "- [ ] 1.2 [req: *] Run the whole suite",
        ])
        self.assertEqual(errors, [])

    def test_group_tag_and_req_tag_coexist(self):
        # A task carrying both `[P2]` (coordination) and a `[req: ...]` tag
        # parses cleanly: the linter finds the requirement tag and it resolves,
        # while the `[P2]` group tag is left untouched.
        errors = self._errors(
            ["- [ ] 2.1 [P2] [req: export-report-csv] Add the flag"])
        self.assertEqual(errors, [])

    def test_error_names_the_task_ordinal(self):
        # Only the second checkbox task (ordinal 2) violates the rule.
        errors = self._errors([
            "- [ ] 1.1 [req: export-report-csv] Fine",
            "- [ ] 1.2 Missing the tag",
        ])
        self.assertTrue(any("2" in e for e in errors))

    # The anchored checkbox grammar (shipd-spec-lint
    # traceability-tag-enforcement): a checkbox line's content begins, after
    # optional leading blanks, with the marker; a marker-shaped substring
    # further along the line is prose.

    def test_prose_literal_on_a_continuation_line_is_not_a_task(self):
        # One real, correctly tagged task whose wrapped description quotes
        # checkbox markers on its continuation lines: the literals are prose,
        # so they neither count as tasks nor need a tag of their own.
        errors = self._errors([
            self.BOX + " 1.1 [req: export-report-csv] Add the exporter and",
            "      document that a pending task reads `" + self.BOX + "` while",
            "      a finished one reads `" + self.DONE_BOX + "`.",
        ])
        self.assertEqual(errors, [])

    def test_ordinal_is_not_shifted_by_a_preceding_prose_literal(self):
        # The second real task is genuinely untagged. Its ordinal is 2 — the
        # literals on task 1's continuation lines must not shift it.
        errors = self._errors([
            self.BOX + " 1.1 [req: export-report-csv] Add the exporter and",
            "      document the `" + self.BOX + "` marker plus the",
            "      `" + self.DONE_BOX + "` marker.",
            self.BOX + " 1.2 Missing the tag",
        ])
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "task 2 has no"))

    def test_bare_marker_line_counts_as_a_task_like_the_coordinator(self):
        # A degenerate marker-only line (no text after the box) is still a
        # checkbox line for `claim_task.sh` and `spec_status.py`, so the linter
        # must count it too — otherwise its ordinals drift out of step with the
        # coordinator's ids. It is ordinal 1 (and untagged, so an error); the
        # real tagged task after it is ordinal 2 and lints clean.
        errors = self._errors([
            self.BOX,
            self.BOX + " 1.1 [req: export-report-csv] Add the exporter",
        ])
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "task 1 has no"))

    def test_indented_checkbox_line_still_counts_as_a_task(self):
        # Leading blanks before the marker are tolerated: the indented line is
        # a real task, so it is ordinal 2 and its missing tag is an error.
        errors = self._errors([
            self.BOX + " 1.1 [req: export-report-csv] Add the exporter",
            "  " + self.BOX + " 1.2 Missing the tag",
        ])
        self.assertTrue(has(errors, "task 2 has no"))

    def test_bad_tag_gates_lint_change(self):
        # The rule must participate in lint_change so it gates the build: a
        # change whose only defect is an unresolvable tag lints with an error.
        change = "gated-change"
        self._write_change(
            change,
            ["- [ ] 1.1 [req: no-such-requirement] Do it"],
            with_plan=True)
        errors = [str(e) for e in sl.lint_change(self.root, change)]
        self.assertTrue(has(errors, "no-such-requirement"))


class TaskReadinessHelperTest(unittest.TestCase):
    """The readiness mirror (shipd-spec-lint task-group-satisfiability):
    ``ready_task_ordinals`` reproduces ``claim_task.sh``'s `first_ready_line`
    awk rule over a tasks file's parsed checkbox states and `[P<n>]` group
    tags — a barrier is ready only when every task before it in file order is
    done; a grouped task only when every barrier before it is done and every
    task in a strictly-lower-numbered group anywhere in the file is done.

    These tests are written test-first and are expected to FAIL until
    ``parse_task_states``/``ready_task_ordinals`` land in ``spec_lint.py``
    (task 1.2)."""

    def _ready(self, task_lines):
        """Parse ``task_lines`` (a list of checkbox-line strings) and return
        the set of 1-based ordinals `ready_task_ordinals` reports ready."""
        text = "## 1. Work\n\n" + "\n".join(task_lines) + "\n"
        states = sl.parse_task_states(text)
        return sl.ready_task_ordinals(states)

    def test_barrier_idiom_readies_only_the_first_group(self):
        # [P1] [P1] barrier [P2] [P2]: only the P1 pair is ready to start;
        # the barrier and the P2 pair are blocked behind it.
        ready = self._ready([
            "- [ ] 1.1 [P1] Add the exporter",
            "- [ ] 1.2 [P1] Add the parser",
            "- [ ] 1.3 Wire them together",
            "- [ ] 1.4 [P2] Add the CLI flag",
            "- [ ] 1.5 [P2] Add the docs",
        ])
        self.assertEqual(ready, {1, 2})

    def test_barrier_becomes_ready_once_its_group_is_done(self):
        ready = self._ready([
            "- [x] 1.1 [P1] Add the exporter",
            "- [x] 1.2 [P1] Add the parser",
            "- [ ] 1.3 Wire them together",
            "- [ ] 1.4 [P2] Add the CLI flag",
        ])
        self.assertEqual(ready, {3})

    def test_fully_grouped_monotonic_readies_the_lowest_group(self):
        ready = self._ready([
            "- [ ] 1.1 [P1] a",
            "- [ ] 1.2 [P1] b",
            "- [ ] 1.3 [P2] c",
            "- [ ] 1.4 [P3] d",
        ])
        self.assertEqual(ready, {1, 2})

    def test_fully_grouped_monotonic_advances_once_lower_group_is_done(self):
        ready = self._ready([
            "- [x] 1.1 [P1] a",
            "- [x] 1.2 [P1] b",
            "- [ ] 1.3 [P2] c",
            "- [ ] 1.4 [P3] d",
        ])
        self.assertEqual(ready, {3})

    def test_fully_sequential_readies_only_the_first_task(self):
        ready = self._ready([
            "- [ ] 1.1 a",
            "- [ ] 1.2 b",
            "- [ ] 1.3 c",
        ])
        self.assertEqual(ready, {1})

    def test_fully_sequential_advances_one_at_a_time(self):
        ready = self._ready([
            "- [x] 1.1 a",
            "- [ ] 1.2 b",
            "- [ ] 1.3 c",
        ])
        self.assertEqual(ready, {2})

    def test_cycle_shape_readies_nothing(self):
        # A [P3] task precedes an untagged barrier that itself precedes a
        # [P2] task: the barrier waits on the [P3] task (file position), and
        # the [P3] task waits on the [P2] task (group number) — neither can
        # ever go first.
        ready = self._ready([
            "- [ ] 1.1 [P3] Do the higher-numbered thing first",
            "- [ ] 1.2 A barrier in between",
            "- [ ] 1.3 [P2] Do the lower-numbered thing after the barrier",
        ])
        self.assertEqual(ready, set())

    def test_group_ready_scans_lower_groups_across_the_whole_file(self):
        # The lower-group check is not limited to tasks before the candidate
        # in file order — a [P1] task appearing *after* a [P2] task still
        # blocks the [P2] task until it is done.
        ready = self._ready([
            "- [ ] 1.1 [P2] appears first but is not lowest-numbered",
            "- [ ] 1.2 [P1] appears second but is lowest-numbered",
        ])
        self.assertEqual(ready, {2})

    def test_in_progress_task_blocks_a_barrier_like_pending(self):
        # A `[~]` (in-progress) task is not done, so it blocks a later
        # barrier exactly as a pending task would.
        ready = self._ready([
            "- [~] 1.1 [P1] claimed but not finished",
            "- [ ] 1.2 A barrier",
        ])
        self.assertEqual(ready, set())


class TaskSatisfiabilityTest(unittest.TestCase):
    """Task group satisfiability (shipd-spec-lint task-group-satisfiability):
    the linter refuses a change whose tasks.md `[P<n>]` group configuration
    leaves some pending task unreachable, by draining readiness to a
    fixpoint with `ready_task_ordinals` and reporting every task still
    pending when the drain stalls.

    These tests are written test-first and are expected to FAIL until
    ``check_task_satisfiability`` lands in ``spec_lint.py`` (task 2.2)."""

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _delta(self):
        return ("## ADDED Requirements\n\n"
                "### Requirement: Do the thing\n"
                "id: do-the-thing\n\n"
                "The system SHALL do the thing.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")

    def _write_change(self, change, task_lines=None, with_plan=False):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self._delta())
        if task_lines is not None:
            with open(os.path.join(cdir, "tasks.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("## 1. Work\n\n" + "\n".join(task_lines) + "\n")
        if with_plan:
            with open(os.path.join(cdir, "plan.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("# %s\nStatus: ready\n\n## Idea\nA summary.\n\n"
                         "### Motivation\nWhy.\n\n### Details\nThe changes.\n\n"
                         "### Non-goals\nNot that.\n\n"
                         "## Implementation\nHow.\n" % change)
        return cdir

    def _errors(self, task_lines):
        change = "sat-change"
        self._write_change(change, task_lines)
        errors = []
        sl.check_task_satisfiability(self.root, change, errors)
        return [str(e) for e in errors]

    def test_cycle_shape_names_every_unreachable_task(self):
        # A [P3] task, an untagged barrier, then a [P2] task: the drain
        # stalls immediately, so all three stay pending and are all named.
        errors = self._errors([
            "- [ ] 1.1 [P3] higher group first",
            "- [ ] 1.2 a barrier in between",
            "- [ ] 1.3 [P2] lower group after the barrier",
        ])
        self.assertEqual(len(errors), 3)
        self.assertTrue(has(errors, "task 1"))
        self.assertTrue(has(errors, "task 2"))
        self.assertTrue(has(errors, "task 3"))

    def test_barrier_idiom_produces_no_finding(self):
        errors = self._errors([
            "- [ ] 1.1 [P1] a",
            "- [ ] 1.2 [P1] b",
            "- [ ] 1.3 a barrier",
            "- [ ] 1.4 [P2] c",
            "- [ ] 1.5 [P2] d",
        ])
        self.assertEqual(errors, [])

    def test_monotonic_grouping_produces_no_finding(self):
        errors = self._errors([
            "- [ ] 1.1 [P1] a",
            "- [ ] 1.2 [P1] b",
            "- [ ] 1.3 [P2] c",
            "- [ ] 1.4 [P3] d",
        ])
        self.assertEqual(errors, [])

    def test_fully_sequential_produces_no_finding(self):
        errors = self._errors([
            "- [ ] 1.1 a",
            "- [ ] 1.2 b",
            "- [ ] 1.3 c",
        ])
        self.assertEqual(errors, [])

    def test_already_done_earlier_tasks_do_not_mask_a_later_cycle(self):
        # Task 1 is unrelated and already done; tasks 2-4 reproduce the cycle
        # shape shifted down by one ordinal. The drain still stalls on them.
        errors = self._errors([
            "- [x] 1.1 an unrelated, already-done barrier",
            "- [ ] 1.2 [P3] higher group first",
            "- [ ] 1.3 a barrier in between",
            "- [ ] 1.4 [P2] lower group after the barrier",
        ])
        self.assertEqual(len(errors), 3)
        self.assertFalse(has(errors, "task 1 "))
        self.assertTrue(has(errors, "task 2"))
        self.assertTrue(has(errors, "task 3"))
        self.assertTrue(has(errors, "task 4"))

    def test_in_progress_claim_produces_no_finding(self):
        # A build in progress: the [P1] task is done and the [P2] task is
        # claimed, with a barrier behind them. The claim is not done, so a
        # state-dependent drain would stall on the barrier; reading the
        # group configuration alone, the file is sound and reports nothing.
        errors = self._errors([
            "- [x] 1.1 [P1] a",
            "- [~] 1.2 [P2] b",
            "- [ ] 1.3 a barrier",
        ])
        self.assertEqual(errors, [])

    def test_broken_configuration_is_reported_even_when_all_done(self):
        # The cycle shape with every task already marked done: the finding
        # is a property of the configuration, not of how far the build got.
        errors = self._errors([
            "- [x] 1.1 [P3] higher group first",
            "- [x] 1.2 a barrier in between",
            "- [x] 1.3 [P2] lower group after the barrier",
        ])
        self.assertEqual(len(errors), 3)
        self.assertTrue(has(errors, "task 1"))
        self.assertTrue(has(errors, "task 2"))
        self.assertTrue(has(errors, "task 3"))

    def test_no_tasks_file_is_a_noop(self):
        change = "no-tasks-change"
        self._write_change(change, task_lines=None)
        errors = []
        sl.check_task_satisfiability(self.root, change, errors)
        self.assertEqual(errors, [])

    def test_cycle_gates_lint_change_with_a_nonzero_exit(self):
        # The whole-CLI path: a change whose only defect is the readiness
        # cycle must lint with an error and exit non-zero, just like the
        # traceability check does.
        change = "gated-cycle-change"
        self._write_change(
            change,
            [
                "- [ ] 1.1 [P3] [req: do-the-thing] higher group first",
                "- [ ] 1.2 [req: do-the-thing] a barrier in between",
                "- [ ] 1.3 [P2] [req: do-the-thing] lower group after "
                "the barrier",
            ],
            with_plan=True)
        errors = [str(e) for e in sl.lint_change(self.root, change)]
        self.assertTrue(errors)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main([change, "--root", self.root])
        self.assertEqual(code, 1)


class ArtefactReferenceLintTest(unittest.TestCase):
    """Artefact reference enforcement (shipd-spec-lint
    artefact-reference-enforcement): every file under a change's
    ``artefacts/`` directory must be referenced by its change-relative path
    from plan.md, tasks.md, or a delta spec, or the linter errors — not warns.

    These tests are written test-first and are expected to FAIL until
    ``check_artefact_references`` lands in ``spec_lint.py`` (task 1.2)."""

    def _delta(self):
        return ("## ADDED Requirements\n\n"
                "### Requirement: Do the thing\n"
                "id: do-the-thing\n\n"
                "The system SHALL do the thing.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_change(self, change, plan_text="A plan mentioning nothing.\n",
                       tasks_text="## 1. Work\n\n"
                                  "- [ ] 1.1 [req: do-the-thing] Do it\n",
                       artefacts=None):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self._delta())
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(plan_text)
        with open(os.path.join(cdir, "tasks.md"), "w", encoding="utf-8") as fh:
            fh.write(tasks_text)
        if artefacts:
            for relpath, content in artefacts.items():
                path = os.path.join(cdir, "artefacts", relpath)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(content)
        return cdir

    def _errors(self, change, **kwargs):
        self._write_change(change, **kwargs)
        errors = []
        sl.check_artefact_references(self.root, change, errors)
        return [str(e) for e in errors]

    def test_unreferenced_artefact_is_an_error(self):
        # (a) policy.md sits in artefacts/ but is named nowhere in plan.md,
        # tasks.md, or the delta: the linter errors, naming the
        # change-relative path.
        errors = self._errors(
            "art-unreferenced", artefacts={"policy.md": "Do this.\n"})
        self.assertTrue(has(errors, "artefacts/policy.md"))

    def test_referenced_artefact_lints_clean(self):
        # (b) the same change, but plan.md now names the artefact's
        # change-relative path: no finding.
        errors = self._errors(
            "art-referenced",
            plan_text="A plan referencing `artefacts/policy.md`.\n",
            artefacts={"policy.md": "Do this.\n"})
        self.assertEqual(errors, [])

    def test_nested_artefact_referenced_by_full_path_lints_clean(self):
        # (c) a nested artefact one directory deep is matched by its full
        # change-relative path.
        errors = self._errors(
            "art-nested-referenced",
            plan_text="See `artefacts/sub/policy.md` for the policy.\n",
            artefacts={"sub/policy.md": "Do this.\n"})
        self.assertEqual(errors, [])

    def test_nested_unreferenced_artefact_names_full_path(self):
        # (c) the unreferenced counterpart: the finding names the nested
        # file's full change-relative path, not just its basename.
        errors = self._errors(
            "art-nested-unreferenced",
            artefacts={"sub/policy.md": "Do this.\n"})
        self.assertTrue(has(errors, "artefacts/sub/policy.md"))

    def test_no_artefacts_directory_is_a_no_op(self):
        # (d) a change with no artefacts directory keeps its current
        # findings: the check contributes nothing.
        errors = self._errors("art-none")
        self.assertEqual(errors, [])

    def test_unreferenced_artefact_gates_lint_change(self):
        # The check must be wired into lint_change so an otherwise-valid
        # change with an unreferenced artefact fails to lint.
        change = "art-gated"
        self._write_change(
            change,
            plan_text=("# %s\nStatus: ready\n\n## Idea\nA summary.\n\n"
                       "### Motivation\nWhy.\n\n### Details\nThe changes.\n\n"
                       "### Non-goals\nNot that.\n\n"
                       "## Implementation\nHow.\n" % change),
            artefacts={"policy.md": "Do this.\n"})
        errors = [str(e) for e in sl.lint_change(self.root, change)]
        self.assertTrue(has(errors, "artefacts/policy.md"))


class ModifiedScenarioRetentionTest(unittest.TestCase):
    """MODIFIED scenario retention (shipd-spec-lint
    modified-scenario-retention): a MODIFIED entry that omits a scenario title
    its base master requirement carries is an error unless a ``Dropped:`` line
    names that title, scenarios are matched by exact title so rewording a body
    is silent, a ``Dropped:`` title absent from the base is itself an error,
    and an entry whose id has no master requirement is skipped.

    These tests are written test-first and are expected to FAIL until the
    ``Dropped:`` grammar lands in ``spec_common.py`` (task 2.1) and
    ``check_modified_scenario_retention`` lands in ``spec_lint.py``
    (task 2.2)."""

    REQ_ID = "session-timeout"
    TITLES = ("Alpha", "Beta", "Gamma", "Delta")

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _scenario(self, title, body="- **WHEN** a\n- **THEN** b\n"):
        return "#### Scenario: %s\n%s" % (title, body)

    def _master(self, req_id=REQ_ID, titles=TITLES):
        return ("# auth\n\n"
                "### Requirement: Session timeout\n"
                "id: %s\n\n"
                "The system SHALL expire idle sessions.\n\n"
                "%s" % (req_id,
                        "\n".join(self._scenario(t) for t in titles)))

    def _delta(self, titles, dropped=(), bodies=None):
        """A one-entry MODIFIED delta restating ``titles``, optionally with a
        ``Dropped:`` line per entry in ``dropped`` and per-title body
        overrides from the ``bodies`` mapping."""
        bodies = bodies or {}
        meta = "".join("Dropped: %s\n" % t for t in dropped)
        blocks = [self._scenario(t, bodies[t]) if t in bodies
                  else self._scenario(t) for t in titles]
        return ("## MODIFIED Requirements\n\n"
                "### Requirement: Session timeout\n"
                "id: %s\n"
                "base: 0123456789ab\n"
                "%s\n"
                "The system SHALL expire idle sessions.\n\n"
                "%s" % (self.REQ_ID, meta, "\n".join(blocks)))

    def _write(self, change, delta_text, master_text=None, plan_text=None,
               capability="auth"):
        verified = os.path.join(self.root, ".shipd", "verified", capability)
        os.makedirs(verified, exist_ok=True)
        with open(os.path.join(verified, "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self._master() if master_text is None else master_text)
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", capability), exist_ok=True)
        with open(os.path.join(cdir, "specs", capability, "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(delta_text)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(plan_text if plan_text is not None
                     else "A plan.\n")
        with open(os.path.join(cdir, "tasks.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("## 1. Work\n\n- [ ] 1.1 [req: %s] Do it\n" % self.REQ_ID)
        return cdir

    def _errors(self, change, delta_text, **kwargs):
        self._write(change, delta_text, **kwargs)
        errors = []
        sl.check_modified_scenario_retention(self.root, change, errors)
        return [str(e) for e in errors]

    def test_silently_dropped_scenarios_are_refused(self):
        # (a) the master carries four scenarios; the entry restates two and
        # names no `Dropped:` line, so merging it would delete Gamma and
        # Delta. One error per omitted title, each naming the requirement id.
        errors = self._errors("ret-silent",
                              self._delta(["Alpha", "Beta"]))
        self.assertEqual(len(errors), 2, errors)
        for title in ("Gamma", "Delta"):
            self.assertTrue(
                any(self.REQ_ID in e and title in e for e in errors),
                "no error names %r and %r: %r" % (self.REQ_ID, title, errors))

    def test_named_drop_is_allowed(self):
        # (b) the entry restates three scenarios and names the fourth in a
        # `Dropped:` line: the removal is deliberate, so no finding.
        errors = self._errors(
            "ret-named",
            self._delta(["Alpha", "Beta", "Gamma"], dropped=["Delta"]))
        self.assertEqual(errors, [])

    def test_several_named_drops_are_allowed(self):
        # (b) `Dropped:` repeats, one title per line, so an entry dropping
        # two scenarios names them both.
        errors = self._errors(
            "ret-named-two",
            self._delta(["Alpha", "Beta"], dropped=["Gamma", "Delta"]))
        self.assertEqual(errors, [])

    def test_rewording_a_scenario_body_is_not_a_drop(self):
        # (c) every base title is restated but one scenario's WHEN/THEN text
        # is rewritten: matching is by exact title, so this is silent.
        errors = self._errors(
            "ret-reworded",
            self._delta(list(self.TITLES),
                        bodies={"Beta": "- **WHEN** the session idles\n"
                                        "- **THEN** it expires\n"}))
        self.assertEqual(errors, [])

    def test_stale_dropped_line_is_refused(self):
        # (d) `Dropped:` names a title the base requirement does not carry, so
        # it licenses nothing while looking like it does.
        errors = self._errors(
            "ret-stale",
            self._delta(list(self.TITLES), dropped=["Epsilon"]))
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(has(errors, "Epsilon"))

    def test_modified_entry_with_no_master_is_skipped(self):
        # (e) the entry's id matches no master requirement, so there are no
        # base scenarios to retain and the check contributes nothing.
        errors = self._errors(
            "ret-no-master",
            self._delta(["Alpha"]),
            master_text=self._master(req_id="something-else"))
        self.assertEqual(errors, [])

    def test_silent_drop_gates_lint_change(self):
        # The check must be wired into lint_change so an otherwise-valid
        # change that silently drops a scenario fails to lint — and so the
        # CLI exits non-zero on it.
        change = "ret-gated"
        self._write(
            change, self._delta(["Alpha", "Beta"]),
            plan_text=("# %s\nStatus: ready\n\n## Idea\nA summary.\n\n"
                       "### Motivation\nWhy.\n\n### Details\nThe changes.\n\n"
                       "### Non-goals\nNot that.\n\n"
                       "## Implementation\nHow.\n" % change))
        errors = [str(e) for e in sl.lint_change(self.root, change)]
        self.assertTrue(any(self.REQ_ID in e and "Gamma" in e
                            for e in errors), errors)


class EpicLintTest(unittest.TestCase):
    """Epic structural validation (shipd-spec-lint epic-structural-validation,
    shipd-spec-format epic-artifact-layout / epic-header-metadata): an epic under
    ``.shipd/epics/<slug>/epic.md`` is validated in library lint and via the
    ``--epic <slug>`` mode.

    Written test-first; expected to FAIL until ``lint_epic``, the epic library
    walk, and the ``--epic`` CLI mode land (tasks 1.2, 1.3)."""

    VALID_EPIC = (
        "# reporting-overhaul\n"
        "Status: draft\n"
        "Theme: reliability\n"
        "Initiative: mvp-readiness\n"
        "\n"
        "## Introduction\n"
        "\n"
        "Reports drift from the source data, so teams stop trusting them.\n"
        "This overhaul rebuilds every export around one shared module.\n"
        "\n"
        "### Non-goals\n"
        "\n"
        "- No new report types.\n"
        "\n"
        "## Decisions\n"
        "\n"
        "Export lives behind a flag.\n"
        "\n"
        "## Design\n"
        "\n"
        "A shared exporter module feeds every format.\n"
        "\n"
        "## Changes\n"
        "\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_config(self, text):
        with open(os.path.join(self.root, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def _epic_errors(self, slug):
        errors = []
        sl.lint_epic(self.root, slug, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def test_conforming_epic_passes_library_and_epic_mode(self):
        self._write_epic("reporting-overhaul", self.VALID_EPIC)
        # Direct lint_epic is clean.
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])
        # Library lint walks .shipd/epics/ and stays clean.
        self.assertEqual(
            [str(e) for e in sl.lint_library(self.root)], [])
        # The --epic CLI mode exits zero.
        code, _err = self._run_cli(["--epic", "reporting-overhaul",
                                    "--root", self.root])
        self.assertEqual(code, 0)

    def test_missing_changes_section_errors(self):
        no_changes = self.VALID_EPIC[:self.VALID_EPIC.index("## Changes")]
        self._write_epic("reporting-overhaul", no_changes)
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "## Changes"))

    def test_missing_introduction_errors(self):
        # Drop the whole Introduction block; Decisions becomes the first
        # level-2 section.
        no_intro = (self.VALID_EPIC[:self.VALID_EPIC.index("## Introduction")]
                    + self.VALID_EPIC[self.VALID_EPIC.index("## Decisions"):])
        self._write_epic("reporting-overhaul", no_intro)
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "## Introduction"))

    def test_introduction_not_first_errors(self):
        # Move the Introduction block to the end so `## Decisions` is the first
        # level-2 section and Introduction appears later.
        intro = self.VALID_EPIC[self.VALID_EPIC.index("## Introduction"):
                                self.VALID_EPIC.index("## Decisions")]
        reordered = (self.VALID_EPIC[:self.VALID_EPIC.index("## Introduction")]
                     + self.VALID_EPIC[self.VALID_EPIC.index("## Decisions"):]
                     + intro)
        self._write_epic("reporting-overhaul", reordered)
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "first level-2 section"))

    def test_introduction_without_non_goals_errors(self):
        no_non_goals = self.VALID_EPIC.replace(
            "### Non-goals\n\n- No new report types.\n\n", "")
        self._write_epic("reporting-overhaul", no_non_goals)
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "Non-goals"))

    def test_verified_status_errors(self):
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC.replace("Status: draft", "Status: verified"))
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "verified"))

    def test_invalid_rating_errors(self):
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC.replace("| low | medium | low | low |",
                                    "| huge | medium | low | low |"))
        self.assertTrue(has(self._epic_errors("reporting-overhaul"), "huge"))

    def test_non_kebab_stub_slug_errors(self):
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC.replace("| csv-export |", "| Csv_Export |"))
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "Csv_Export"))

    def test_duplicate_stub_slug_errors(self):
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC
            + "| csv-export | Export again | low | low | low | low |\n")
        self.assertTrue(has(self._epic_errors("reporting-overhaul"),
                            "duplicate"))

    def test_profile_key_on_epic_is_unrecognized(self):
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC.replace("Status: draft\n",
                                    "Status: draft\nProfile: lite\n"))
        errors = self._epic_errors("reporting-overhaul")
        self.assertTrue(has(errors, "Profile"))
        self.assertTrue(has(errors, "unrecognized"))

    def test_non_kebab_prd_value_errors(self):
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC.replace("Status: draft\n",
                                    "Status: draft\nPRD: Mobile_Push\n"))
        errors = self._epic_errors("reporting-overhaul")
        self.assertTrue(has(errors, "Mobile_Push"))
        self.assertTrue(has(errors, "kebab"))

    def test_epic_without_a_prd_line_lints_as_before(self):
        # Regression: recognizing the new key leaves an epic carrying no `PRD:`
        # line untouched — no resolution runs, no new error.
        self._write_epic("reporting-overhaul", self.VALID_EPIC)
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_theme_outside_vocabulary_errors(self):
        self._write_config('{"valid_themes": ["reliability"]}')
        self._write_epic(
            "reporting-overhaul",
            self.VALID_EPIC.replace("Theme: reliability", "Theme: speed"))
        self.assertTrue(has(self._epic_errors("reporting-overhaul"), "speed"))

    def test_no_epics_directory_lints_as_before(self):
        # A repo carrying a valid master library but no .shipd/epics/ directory
        # lints exactly as today: no epic errors, no crash.
        specs = os.path.join(self.root, ".shipd", "verified", "auth")
        os.makedirs(specs, exist_ok=True)
        with open(os.path.join(specs, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(
                "# auth\n\n"
                "### Requirement: Good\nid: good\n\n"
                "The system SHALL be good.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertFalse(
            os.path.isdir(os.path.join(self.root, ".shipd", "epics")))
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])


class EpicResearchLintTest(unittest.TestCase):
    """Epic ``## Research`` section validation (shipd-spec-format
    epic-research-section, shipd-spec-lint epic-research-link-validation): the
    optional section links research files under the content dir's ``research/``
    folder. When present it holds at least one markdown list entry whose link
    resolves — epic-dir-first, then repo-root — to an existing file under
    ``<content-dir>/research/``. Absent, the epic is exactly as valid as before;
    the linter never walks ``research/`` on its own.

    Written test-first; expected to FAIL until the research-link check lands in
    ``lint_epic`` (task 1.2)."""

    BASE_EPIC = (
        "# reporting-overhaul\n"
        "Status: draft\n"
        "\n"
        "## Introduction\n"
        "\n"
        "Reports drift from the source data, so teams stop trusting them.\n"
        "\n"
        "### Non-goals\n"
        "\n"
        "- No new report types.\n"
        "\n"
        "## Decisions\n"
        "\n"
        "Export lives behind a flag.\n"
        "\n"
        "## Design\n"
        "\n"
        "A shared exporter module feeds every format.\n"
        "\n"
        "## Changes\n"
        "\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_research(self, relpath, text="# report\n"):
        p = os.path.join(self.root, ".shipd", "research", relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _epic_with_research(self, *entries):
        return self.BASE_EPIC + "\n## Research\n\n" + "".join(
            e + "\n" for e in entries)

    def _epic_errors(self, slug):
        errors = []
        sl.lint_epic(self.root, slug, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def test_epic_relative_link_resolves(self):
        # A link relative to the epic's own directory
        # (.shipd/epics/<slug>/ -> ../../research/...).
        self._write_research("payment-apis/report.md")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_research(
                "- [Payment APIs](../../research/payment-apis/report.md)"))
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_repo_root_relative_link_resolves(self):
        # A link relative to the repository root.
        self._write_research("payment-apis/report.md")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_research(
                "- [Payment APIs](.shipd/research/payment-apis/report.md)"))
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_dead_link_errors_naming_it(self):
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_research(
                "- [Missing](../../research/missing/report.md)"))
        errors = self._epic_errors("reporting-overhaul")
        self.assertTrue(
            has(errors, "../../research/missing/report.md"), errors)
        # The dead link makes the --epic CLI mode exit non-zero.
        code, _err = self._run_cli(["--epic", "reporting-overhaul",
                                    "--root", self.root])
        self.assertEqual(code, 1)

    def test_link_outside_research_folder_errors(self):
        # A link that resolves (epic-relative) to a real file that does not
        # live under the content dir's research/ folder.
        edir = os.path.join(self.root, ".shipd", "epics", "reporting-overhaul")
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("# notes\n")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_research("- [Notes](notes.md)"))
        self.assertTrue(
            has(self._epic_errors("reporting-overhaul"), "notes.md"))

    def test_empty_research_section_errors(self):
        self._write_epic(
            "reporting-overhaul", self.BASE_EPIC + "\n## Research\n")
        self.assertTrue(
            has(self._epic_errors("reporting-overhaul"), "Research"))

    def test_no_research_section_produces_no_finding(self):
        self._write_epic("reporting-overhaul", self.BASE_EPIC)
        errors = self._epic_errors("reporting-overhaul")
        self.assertEqual(errors, [])
        self.assertFalse(has([e.lower() for e in errors], "research"))

    def test_unlinked_malformed_research_file_ignored(self):
        # A malformed file under research/ that no epic links produces no
        # library-lint finding — the linter never walks research/ on its own.
        self._write_research("orphan.md", "not a valid anything @@@\n")
        self._write_epic("reporting-overhaul", self.BASE_EPIC)
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])


class EpicVideoLintTest(unittest.TestCase):
    """Epic ``## Video`` section validation (shipd-spec-format
    epic-video-section, shipd-spec-lint epic-video-link-validation): the
    optional section links video intent briefs under the content dir's
    ``video/`` folder. When present it holds at least one markdown list entry
    whose link resolves — epic-dir-first, then repo-root — to an existing file
    under ``<content-dir>/video/``. Absent, the epic is exactly as valid as
    before; the linter never walks ``video/`` on its own. The check is the
    research check, parameterized (`_check_epic_link_section`), so this mirrors
    ``EpicResearchLintTest`` exactly.

    Written test-first; expected to FAIL until the video-link check lands in
    ``lint_epic`` (task 1.2)."""

    BASE_EPIC = (
        "# reporting-overhaul\n"
        "Status: draft\n"
        "\n"
        "## Introduction\n"
        "\n"
        "Reports drift from the source data, so teams stop trusting them.\n"
        "\n"
        "### Non-goals\n"
        "\n"
        "- No new report types.\n"
        "\n"
        "## Decisions\n"
        "\n"
        "Export lives behind a flag.\n"
        "\n"
        "## Design\n"
        "\n"
        "A shared exporter module feeds every format.\n"
        "\n"
        "## Changes\n"
        "\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_video(self, relpath, text="# brief\n"):
        p = os.path.join(self.root, ".shipd", "video", relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_research(self, relpath, text="# report\n"):
        p = os.path.join(self.root, ".shipd", "research", relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _epic_with_video(self, *entries):
        return self.BASE_EPIC + "\n## Video\n\n" + "".join(
            e + "\n" for e in entries)

    def _epic_errors(self, slug):
        errors = []
        sl.lint_epic(self.root, slug, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def test_epic_relative_link_resolves(self):
        # A link relative to the epic's own directory
        # (.shipd/epics/<slug>/ -> ../../video/...).
        self._write_video("kickoff-call/brief.md")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_video(
                "- [Kickoff call](../../video/kickoff-call/brief.md)"))
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_repo_root_relative_link_resolves(self):
        # A link relative to the repository root.
        self._write_video("kickoff-call/brief.md")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_video(
                "- [Kickoff call](.shipd/video/kickoff-call/brief.md)"))
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_dead_link_errors_naming_it(self):
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_video(
                "- [Missing](../../video/missing/brief.md)"))
        errors = self._epic_errors("reporting-overhaul")
        self.assertTrue(
            has(errors, "../../video/missing/brief.md"), errors)
        # The dead link makes the --epic CLI mode exit non-zero.
        code, _err = self._run_cli(["--epic", "reporting-overhaul",
                                    "--root", self.root])
        self.assertEqual(code, 1)

    def test_link_outside_video_folder_errors(self):
        # A link that resolves (epic-relative) to a real file that does not
        # live under the content dir's video/ folder.
        edir = os.path.join(self.root, ".shipd", "epics", "reporting-overhaul")
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("# notes\n")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_video("- [Notes](notes.md)"))
        self.assertTrue(
            has(self._epic_errors("reporting-overhaul"), "notes.md"))

    def test_empty_video_section_errors(self):
        self._write_epic(
            "reporting-overhaul", self.BASE_EPIC + "\n## Video\n")
        self.assertTrue(
            has(self._epic_errors("reporting-overhaul"), "Video"))

    def test_no_video_section_produces_no_finding(self):
        self._write_epic("reporting-overhaul", self.BASE_EPIC)
        errors = self._epic_errors("reporting-overhaul")
        self.assertEqual(errors, [])
        self.assertFalse(has([e.lower() for e in errors], "video"))

    def test_unlinked_malformed_video_file_ignored(self):
        # A malformed file under video/ that no epic links produces no
        # library-lint finding — the linter never walks video/ on its own.
        self._write_video("orphan.md", "not a valid anything @@@\n")
        self._write_epic("reporting-overhaul", self.BASE_EPIC)
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])

    def test_context_sections_are_independent(self):
        # Each context section is validated against its own reserved folder,
        # and neither section's contents affect the other's findings
        # (shipd-spec-format epic-video-section).
        self._write_research("payment-apis/report.md")
        self._write_video("kickoff-call/brief.md")
        both = (
            self.BASE_EPIC
            + "\n## Research\n\n"
            + "- [Payment APIs](../../research/payment-apis/report.md)\n"
            + "\n## Video\n\n"
            + "- [Kickoff call](../../video/kickoff-call/brief.md)\n")
        self._write_epic("reporting-overhaul", both)
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

        # Cross-linked: the brief under `## Research` and the report under
        # `## Video`. Each link is an error against its own folder, and each
        # finding names its own section — the sections do not cover for one
        # another.
        crossed = (
            self.BASE_EPIC
            + "\n## Research\n\n"
            + "- [Kickoff call](../../video/kickoff-call/brief.md)\n"
            + "\n## Video\n\n"
            + "- [Payment APIs](../../research/payment-apis/report.md)\n")
        self._write_epic("reporting-overhaul", crossed)
        errors = self._epic_errors("reporting-overhaul")
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(has(errors, "`## Research` link "
                                    "'../../video/kickoff-call/brief.md'"),
                        errors)
        self.assertTrue(has(errors, "`## Video` link "
                                    "'../../research/payment-apis/report.md'"),
                        errors)


class EpicReferencesLintTest(unittest.TestCase):
    """Epic ``## References`` section validation (shipd-spec-format
    epic-references-section, shipd-spec-lint epic-references-link-lint): the
    optional superset shelf links reference documents of any installed kind
    — research reports, video briefs, and supplied docs — under the content
    dir's ``research/``, ``video/``, or ``docs/`` folders. When present it
    holds at least one markdown list entry whose link resolves — epic-dir-
    first, then repo-root — to an existing file under one of those three
    folders; entries of the three kinds mix freely in the one section.
    Absent, the epic is exactly as valid as before; the linter never walks
    any of the three folders on its own. The section is additive: the
    ``## Research`` and ``## Video`` sections keep their existing findings
    unchanged whether or not ``## References`` is present. The check is the
    research/video check, generalized to accept a tuple of folders
    (`_check_epic_link_section`), so this mirrors ``EpicResearchLintTest``
    and ``EpicVideoLintTest``.

    Written test-first; expected to FAIL until the References-link check
    lands in ``lint_epic`` (task 1.2)."""

    BASE_EPIC = (
        "# reporting-overhaul\n"
        "Status: draft\n"
        "\n"
        "## Introduction\n"
        "\n"
        "Reports drift from the source data, so teams stop trusting them.\n"
        "\n"
        "### Non-goals\n"
        "\n"
        "- No new report types.\n"
        "\n"
        "## Decisions\n"
        "\n"
        "Export lives behind a flag.\n"
        "\n"
        "## Design\n"
        "\n"
        "A shared exporter module feeds every format.\n"
        "\n"
        "## Changes\n"
        "\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_research(self, relpath, text="# report\n"):
        p = os.path.join(self.root, ".shipd", "research", relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_video(self, relpath, text="# brief\n"):
        p = os.path.join(self.root, ".shipd", "video", relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_docs(self, relpath, text="# doc\n"):
        p = os.path.join(self.root, ".shipd", "docs", relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _epic_with_references(self, *entries):
        return self.BASE_EPIC + "\n## References\n\n" + "".join(
            e + "\n" for e in entries)

    def _epic_errors(self, slug):
        errors = []
        sl.lint_epic(self.root, slug, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def test_docs_entry_resolves(self):
        self._write_docs("strategy-notes/doc.md")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_references(
                "- [Strategy notes](../../docs/strategy-notes/doc.md)"))
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_mixed_kind_entries_resolve(self):
        self._write_research("payment-apis/report.md")
        self._write_video("kickoff-call/brief.md")
        self._write_docs("strategy-notes/doc.md")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_references(
                "- [Payment APIs](../../research/payment-apis/report.md)",
                "- [Kickoff call](../../video/kickoff-call/brief.md)",
                "- [Strategy notes](../../docs/strategy-notes/doc.md)"))
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])

    def test_dead_link_errors_naming_it(self):
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_references(
                "- [Missing](../../docs/missing/doc.md)"))
        errors = self._epic_errors("reporting-overhaul")
        self.assertTrue(
            has(errors, "../../docs/missing/doc.md"), errors)
        # The dead link makes the --epic CLI mode exit non-zero.
        code, _err = self._run_cli(["--epic", "reporting-overhaul",
                                    "--root", self.root])
        self.assertEqual(code, 1)

    def test_link_outside_reference_folders_errors(self):
        # A link that resolves (epic-relative) to a real file that does not
        # live under any of research/, video/, or docs/.
        edir = os.path.join(self.root, ".shipd", "epics", "reporting-overhaul")
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("# notes\n")
        self._write_epic(
            "reporting-overhaul",
            self._epic_with_references("- [Notes](notes.md)"))
        self.assertTrue(
            has(self._epic_errors("reporting-overhaul"), "notes.md"))

    def test_empty_references_section_errors(self):
        self._write_epic(
            "reporting-overhaul", self.BASE_EPIC + "\n## References\n")
        self.assertTrue(
            has(self._epic_errors("reporting-overhaul"), "References"))

    def test_no_references_section_produces_no_finding(self):
        self._write_epic("reporting-overhaul", self.BASE_EPIC)
        errors = self._epic_errors("reporting-overhaul")
        self.assertEqual(errors, [])
        self.assertFalse(has([e.lower() for e in errors], "references"))

    def test_dead_research_link_reported_unchanged_alongside_references(self):
        # A dead `## Research` link is reported exactly as it is without a
        # `## References` section, whether or not that section is present
        # and resolving (shipd-spec-lint epic-references-link-lint).
        self._write_docs("strategy-notes/doc.md")
        text = (
            self.BASE_EPIC
            + "\n## Research\n\n"
            + "- [Missing](../../research/missing/report.md)\n"
            + "\n## References\n\n"
            + "- [Strategy notes](../../docs/strategy-notes/doc.md)\n")
        self._write_epic("reporting-overhaul", text)
        errors = self._epic_errors("reporting-overhaul")
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(
            has(errors, "`## Research` link "
                        "'../../research/missing/report.md'"),
            errors)


class ResearchReportLintTest(unittest.TestCase):
    """Research report validation (shipd-spec-format research-report-format,
    shipd-spec-lint research-report-validation): ``lint_research(root, slug,
    errors)`` always enforces a non-empty ``# <title>`` on line 1, and enforces
    the citation skeleton — a ``## Sources`` section with at least one numbered
    entry, at least one inline ``[n]`` marker, and every marker (outside fenced
    code blocks) resolving to a listed source — only when the report carries a
    citation signal (a ``## Sources`` section, or at least one marker). A
    titled report carrying neither signal is accepted, so a supplied document
    installs clean. Library linting never walks ``research/`` on its own."""

    CONFORMING = (
        "# Payment API landscape\n"
        "\n"
        "## Summary\n"
        "\n"
        "Stripe leads on developer experience [1], and Adyen on coverage [2].\n"
        "\n"
        "## Sources\n"
        "\n"
        "1. Stripe docs — https://stripe.com/docs\n"
        "2. Adyen coverage — https://adyen.com/coverage\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_report(self, slug, text):
        rdir = os.path.join(self.root, ".shipd", "research", slug)
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, "report.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def _errors(self, slug):
        errors = []
        sl.lint_research(self.root, slug, errors)
        return [str(e) for e in errors]

    def test_conforming_report_passes(self):
        self._write_report("payment-apis", self.CONFORMING)
        self.assertEqual(self._errors("payment-apis"), [])

    def test_uncited_titled_document_passes(self):
        # A supplied document — titled, no `## Sources` section, no `[n]`
        # markers — carries no citation signal, so only the title check runs.
        text = (
            "# Payments strategy brief\n"
            "\n"
            "## Context\n"
            "\n"
            "We move to a single processor next quarter.\n"
        )
        self._write_report("payments-strategy", text)
        self.assertEqual(self._errors("payments-strategy"), [])

    def test_uncited_untitled_document_still_errors(self):
        # The title check always runs, citation signal or not.
        self._write_report("payments-strategy", "Not a title.\n")
        errors = self._errors("payments-strategy")
        self.assertTrue(has(errors, "line 1"), errors)

    def test_missing_sources_section_errors(self):
        # The marker is the citation signal, so the full skeleton applies.
        text = (
            "# Payment API landscape\n"
            "\n"
            "Stripe leads on developer experience [1].\n"
        )
        self._write_report("payment-apis", text)
        errors = self._errors("payment-apis")
        self.assertTrue(has(errors, "Sources"), errors)

    def test_unresolved_marker_errors_naming_it(self):
        text = (
            "# Payment API landscape\n"
            "\n"
            "Only three sources exist, yet this cites [4].\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. One — https://one.example\n"
            "2. Two — https://two.example\n"
            "3. Three — https://three.example\n"
        )
        self._write_report("payment-apis", text)
        errors = self._errors("payment-apis")
        self.assertTrue(has(errors, "[4]"), errors)

    def test_zero_markers_errors(self):
        text = (
            "# Payment API landscape\n"
            "\n"
            "A summary that anchors nothing at all.\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. One — https://one.example\n"
        )
        self._write_report("payment-apis", text)
        errors = self._errors("payment-apis")
        self.assertTrue(errors, "expected a no-marker finding")

    def test_code_block_index_never_trips(self):
        # `items[0]` inside a fenced code block is not a citation marker; the
        # prose citation [1] resolves, so the report is clean.
        text = (
            "# Payment API landscape\n"
            "\n"
            "The client exposes an array [1]:\n"
            "\n"
            "```python\n"
            "print(items[0])\n"
            "```\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. Client docs — https://client.example\n"
        )
        self._write_report("payment-apis", text)
        self.assertEqual(self._errors("payment-apis"), [])

    def test_library_lint_ignores_research_files(self):
        # An invalid report under research/ produces no library-lint finding —
        # the linter never walks research/ on its own.
        self._write_report("broken", "not a valid report @@@\n")
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])


class VideoBriefLintTest(unittest.TestCase):
    """Video intent brief validation (shipd-spec-format video-brief-format,
    shipd-spec-lint video-brief-validation): ``lint_video(root, slug, errors)``
    enforces the title line, the required ``Video:`` header, the
    ``## Intents`` and ``## Sources`` sections, the
    per-intent citation rule, the timestamped source-entry rule, and citation
    marker resolution (fenced code blocks skipped). Library linting never
    walks the content directory's ``video/`` folder on its own, and
    ``spec_lint.py`` exposes no command-line mode for these checks.

    Written test-first; expected to FAIL until ``lint_video`` lands in
    ``spec_lint.py`` (task 2.2)."""

    CONFORMING = (
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

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_brief(self, slug, text):
        vdir = os.path.join(self.root, ".shipd", "video", slug)
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "brief.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def _errors(self, slug):
        errors = []
        sl.lint_video(self.root, slug, errors)
        return [str(e) for e in errors]

    def test_conforming_brief_passes(self):
        self._write_brief("board-walkthrough", self.CONFORMING)
        self.assertEqual(self._errors("board-walkthrough"), [])

    def test_missing_video_header_errors(self):
        text = (
            "# Board walkthrough\n"
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
        self._write_brief("board-walkthrough", text)
        errors = self._errors("board-walkthrough")
        self.assertTrue(has(errors, "Video"), errors)

    def test_uncited_intent_errors_naming_it(self):
        text = (
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
            "### Explain the retry gate\n"
            "\n"
            "The retry gate enriches after three strikes.\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. [00:14:22.4] Ada: parked members need a visible signal.\n"
        )
        self._write_brief("board-walkthrough", text)
        errors = self._errors("board-walkthrough")
        self.assertTrue(has(errors, "Explain the retry gate"), errors)

    def test_untimestamped_source_errors_naming_it(self):
        text = (
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
            "1. Ada: parked members need a visible signal.\n"
        )
        self._write_brief("board-walkthrough", text)
        errors = self._errors("board-walkthrough")
        self.assertTrue(
            has(errors, "Ada: parked members need a visible signal"),
            errors)

    def test_unresolved_marker_errors_naming_it(self):
        text = (
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
            "Only three sources exist, yet this cites [4].\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. [00:14:22.4] Ada: one.\n"
            "2. [00:15:01.0] Ada: two.\n"
            "3. [00:15:40.2] Ada: three.\n"
        )
        self._write_brief("board-walkthrough", text)
        errors = self._errors("board-walkthrough")
        self.assertTrue(has(errors, "[4]"), errors)

    def test_code_block_index_never_trips(self):
        # `items[0]` inside a fenced code block is not a citation marker; the
        # prose citation [1] resolves, so the brief is clean.
        text = (
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
            "The client exposes an array [1]:\n"
            "\n"
            "```python\n"
            "print(items[0])\n"
            "```\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. [00:14:22.4] Ada: parked members need a visible signal.\n"
        )
        self._write_brief("board-walkthrough", text)
        self.assertEqual(self._errors("board-walkthrough"), [])

    def test_extra_section_produces_no_finding(self):
        text = self.CONFORMING + (
            "\n## Gaps & caveats\n"
            "\n"
            "- Nothing outstanding.\n"
        )
        self._write_brief("board-walkthrough", text)
        self.assertEqual(self._errors("board-walkthrough"), [])

    def test_no_speakers_section_produces_no_finding(self):
        text = (
            "# Board walkthrough\n"
            "Video: board-walkthrough.mp4\n"
            "\n"
            "## Intents\n"
            "\n"
            "### Explain the parked-member signal\n"
            "\n"
            "The board should surface parked members clearly [1].\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. [00:14:22.4] Parked members need a visible signal.\n"
        )
        self._write_brief("board-walkthrough", text)
        self.assertEqual(self._errors("board-walkthrough"), [])

    def test_speaker_free_source_entry_produces_no_finding(self):
        text = (
            "# Board walkthrough\n"
            "Video: board-walkthrough.mp4\n"
            "\n"
            "## Intents\n"
            "\n"
            "### Explain the parked-member signal\n"
            "\n"
            "The board should surface parked members clearly [1].\n"
            "\n"
            "## Sources\n"
            "\n"
            "1. [00:14:22.4] Parked members need a visible signal.\n"
        )
        self._write_brief("board-walkthrough", text)
        errors = self._errors("board-walkthrough")
        self.assertFalse(
            has(errors, "Parked members need a visible signal"), errors)

    def test_undeclared_project_errors_naming_it(self):
        declare_workspace(
            self.root, {"projects": {"alpha": {"repos": ["repo"]}}})
        text = self.CONFORMING.replace(
            "Video: board-walkthrough.mp4\n",
            "Video: board-walkthrough.mp4\nProject: beta\n")
        self._write_brief("board-walkthrough", text)
        errors = self._errors("board-walkthrough")
        self.assertTrue(has(errors, "beta"), errors)

    def test_no_project_line_skips_registry_validation(self):
        # A broken registry (non-object `projects` map) would fail
        # `validate_workspace` if consulted; a brief with no `Project:` line
        # never loads the registry, so no finding is produced.
        declare_workspace(self.root, {"projects": []})
        self._write_brief("board-walkthrough", self.CONFORMING)
        self.assertEqual(self._errors("board-walkthrough"), [])

    def test_library_lint_ignores_video_files(self):
        # An invalid brief under video/ produces no library-lint finding —
        # the linter never walks video/ on its own.
        self._write_brief("broken", "not a valid brief @@@\n")
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])

    def test_no_command_line_mode_for_video_checks(self):
        # spec_lint.py exposes no --video flag (unlike --epic/--initiative);
        # argparse rejects the unrecognized option with SystemExit(2).
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                sl.main(["--video", "board-walkthrough"])


class DocsDocumentLintTest(unittest.TestCase):
    """Docs document validation (shipd-spec-format docs-document-format,
    shipd-spec-lint docs-document-validation): ``lint_docs(root, slug,
    errors)`` enforces exactly one rule on
    ``<content-dir>/docs/<slug>/doc.md`` — a non-empty ``# <title>`` on line
    1 — and never demands a citation skeleton, header metadata, or section
    structure, so a supplied document (strategy notes, meeting minutes, an
    API excerpt) installs without pretending to a grammar it does not have.
    A missing document file is itself a finding naming the expected path.
    Library linting never walks the content directory's ``docs/`` folder on
    its own, and ``spec_lint.py`` exposes no command-line mode for these
    checks.

    Written test-first; expected to FAIL until ``lint_docs`` lands in
    ``spec_lint.py`` (task 1.2)."""

    CONFORMING = (
        "# Payments strategy\n"
        "\n"
        "## Context\n"
        "\n"
        "We move to a single processor next quarter [3], per the board's\n"
        "own minutes, and the migration runs through Q2.\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _doc_path(self, slug):
        return os.path.join(self.root, ".shipd", "docs", slug, "doc.md")

    def _write_doc(self, slug, text):
        ddir = os.path.join(self.root, ".shipd", "docs", slug)
        os.makedirs(ddir, exist_ok=True)
        with open(os.path.join(ddir, "doc.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _errors(self, slug):
        errors = []
        sl.lint_docs(self.root, slug, errors)
        return [str(e) for e in errors]

    def test_titled_free_form_document_passes(self):
        # A `[3]`-style bracket marker and no `## Sources` section: free-form
        # body, so the citation grammar never applies.
        self._write_doc("payments-strategy", self.CONFORMING)
        self.assertEqual(self._errors("payments-strategy"), [])

    def test_untitled_document_errors_naming_the_file(self):
        self._write_doc("payments-strategy", "Not a title.\n")
        errors = self._errors("payments-strategy")
        self.assertTrue(has(errors, "line 1"), errors)
        self.assertTrue(
            has(errors, self._doc_path("payments-strategy")), errors)

    def test_missing_document_errors_naming_the_path(self):
        errors = self._errors("no-such-doc")
        self.assertTrue(has(errors, "no-such-doc"), errors)
        self.assertTrue(has(errors, self._doc_path("no-such-doc")), errors)

    def test_library_lint_ignores_docs_files(self):
        # An untitled file under docs/ produces no library-lint finding —
        # the linter never walks docs/ on its own.
        self._write_doc("broken", "not a valid document @@@\n")
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])

    def test_no_command_line_mode_for_docs_checks(self):
        # spec_lint.py exposes no --docs flag (unlike --epic/--initiative);
        # argparse rejects the unrecognized option with SystemExit(2).
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                sl.main(["--docs", "payments-strategy"])


class EpicReferenceLintTest(unittest.TestCase):
    """Epic reference resolution on a change plan (shipd-spec-lint
    epic-reference-resolution): a change's ``Epic:`` line must resolve to an
    existing epic (error), and a resolved epic whose stub table lacks the
    change's slug warns but does not fail.

    Written test-first; expected to FAIL until ``check_epic_reference`` lands in
    ``spec_lint.py`` (task 1.4)."""

    BODY = ("\n## Idea\nA summary.\n\n### Motivation\nBecause.\n\n"
            "### Details\nThe changes.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n")

    EPIC = (
        "# reporting-overhaul\n"
        "Status: ready\n"
        "\n"
        "## Introduction\n\nWhy it matters.\n\n### Non-goals\n\n- Not that.\n\n"
        "## Decisions\n\nWhy.\n\n"
        "## Design\n\nHow.\n\n"
        "## Changes\n\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_change(self, change, epic_slug):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: ready\nEpic: %s\n" % (change, epic_slug)
                     + self.BODY)
        # A lint-clean delta so lint_change's other checks stay silent.
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(
                "## ADDED Requirements\n\n"
                "### Requirement: Good\nid: good\n\n"
                "The system SHALL be good.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")

    def _errors(self, change):
        errors = []
        sl.check_epic_reference(self.root, change, errors)
        return [str(e) for e in errors]

    def _warnings(self, change):
        warnings = []
        sl.check_epic_reference(self.root, change, [], warnings)
        return [str(w) for w in warnings]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def test_dangling_reference_errors(self):
        self._write_change("csv-export", "no-such-epic")
        self.assertTrue(has(self._errors("csv-export"), "no-such-epic"))
        # It gates the build through lint_change.
        self.assertTrue(has([str(e) for e in
                             sl.lint_change(self.root, "csv-export")],
                            "no-such-epic"))

    def test_missing_stub_row_warns_but_exits_zero(self):
        # Epic exists but its stub table has no `orphan-change` row.
        self._write_epic("reporting-overhaul", self.EPIC)
        self._write_change("orphan-change", "reporting-overhaul")
        self.assertEqual(self._errors("orphan-change"), [])
        self.assertTrue(self._warnings("orphan-change"))
        code, err = self._run_cli(["orphan-change", "--root", self.root])
        self.assertEqual(code, 0)
        self.assertIn("WARNING:", err)

    def test_listed_member_passes_silently(self):
        self._write_epic("reporting-overhaul", self.EPIC)
        self._write_change("csv-export", "reporting-overhaul")
        self.assertEqual(self._errors("csv-export"), [])
        self.assertEqual(self._warnings("csv-export"), [])

    def test_no_epic_line_is_a_noop(self):
        cdir = os.path.join(self.root, ".shipd", "planned", "solo")
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# solo\nStatus: ready\n" + self.BODY)
        self.assertEqual(self._errors("solo"), [])
        self.assertEqual(self._warnings("solo"), [])


class InitiativeBriefLintTest(unittest.TestCase):
    """Initiative brief structural validation and the ``--initiative <slug>``
    mode (shipd-workspace initiative-brief-format, shipd-spec-lint
    initiative-lint-mode).

    The repo fixture lives *inside* a fake workspace (``<tmp>/repo`` with the
    marker at ``<tmp>/.shipd-config.json`` declaring ``workspace``) so
    ``find_workspace_root`` walking up from the repo finds the temp marker and
    never escapes into the real filesystem. Briefs live at
    ``<tmp>/.shipd/initiatives/<slug>/brief.md``. ``$HOME`` is overridden so the
    real home config never leaks into resolution."""

    VALID_BRIEF = (
        "# mvp-readiness\n"
        "Status: open\n"
        "\n"
        "Get the product ready for its first real users.\n"
        "\n"
        "## Requirements\n"
        "\n"
        "- [ ] Ship onboarding\n"
        "- [ ] Document the public API\n"
    )

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.root = os.path.join(self.ws, "repo")
        os.makedirs(self.root, exist_ok=True)
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        declare_workspace(self.ws)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_brief(self, slug, text):
        bdir = os.path.join(self.ws, ".shipd", "initiatives", slug)
        os.makedirs(bdir, exist_ok=True)
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_registry(self, payload):
        """Overwrite the workspace declaration in ``.shipd-config.json``.
        ``payload`` is the ``workspace`` object (a dict)."""
        declare_workspace(self.ws, payload)

    def _errors(self, slug):
        errors = []
        sl.lint_initiative(self.ws, slug, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def test_conforming_brief_lints_clean(self):
        self._write_brief("mvp-readiness", self.VALID_BRIEF)
        self.assertEqual(self._errors("mvp-readiness"), [])
        code, _err = self._run_cli(
            ["--initiative", "mvp-readiness", "--root", self.root])
        self.assertEqual(code, 0)

    def test_missing_requirements_section_errors(self):
        no_reqs = self.VALID_BRIEF[
            :self.VALID_BRIEF.index("## Requirements")]
        self._write_brief("mvp-readiness", no_reqs)
        self.assertTrue(has(self._errors("mvp-readiness"), "## Requirements"))

    def test_requirements_without_checkbox_errors(self):
        empty_reqs = (self.VALID_BRIEF[
            :self.VALID_BRIEF.index("- [ ] Ship onboarding")]
            + "Prose, no checkboxes.\n")
        self._write_brief("mvp-readiness", empty_reqs)
        self.assertTrue(has(self._errors("mvp-readiness"), "checkbox"))

    def test_invalid_status_value_errors(self):
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace("Status: open", "Status: pending"))
        self.assertTrue(has(self._errors("mvp-readiness"), "pending"))

    def test_unknown_metadata_key_errors(self):
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace(
                "Status: open\n", "Status: open\nTheme: reliability\n"))
        errors = self._errors("mvp-readiness")
        self.assertTrue(has(errors, "Theme"))
        self.assertTrue(has(errors, "unrecognized"))

    def test_project_names_declared_slug_passes(self):
        # (Adapted from the pre-project-groups test that accepted
        # `Project: alpha` on key shape alone.) A `Project:` value must now name
        # a declared project slug; `alpha` is declared, so the brief lints clean.
        self._write_registry({"projects": {"alpha": {"repos": ["repo"]}}})
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace(
                "Status: open\n", "Status: open\nProject: alpha\n"))
        self.assertEqual(self._errors("mvp-readiness"), [])

    def test_mixed_case_project_name_passes(self):
        # Project names are identifier-style, not kebab (shipd-workspace
        # project-registry-semantics): `APISchema` is declared, so a brief
        # scoped to it lints clean.
        self._write_registry({"projects": {"APISchema": {"repos": ["repo"]}}})
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace(
                "Status: open\n", "Status: open\nProject: APISchema\n"))
        self.assertEqual(self._errors("mvp-readiness"), [])

    def test_project_not_declared_errors_listing_slugs(self):
        self._write_registry({"projects": {"alpha": {"repos": ["repo"]}}})
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace(
                "Status: open\n", "Status: open\nProject: beta\n"))
        errors = self._errors("mvp-readiness")
        self.assertTrue(has(errors, "beta"))
        self.assertTrue(has(errors, "alpha"))

    def test_project_with_no_declared_projects_errors(self):
        # setUp's registry is `{}` — no projects declared.
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace(
                "Status: open\n", "Status: open\nProject: alpha\n"))
        errors = self._errors("mvp-readiness")
        self.assertTrue(has(errors, "no projects declared"))

    def test_broken_registry_surfaces_when_brief_has_project(self):
        self._write_registry({"projects": []})  # non-object projects map
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace(
                "Status: open\n", "Status: open\nProject: alpha\n"))
        errors = self._errors("mvp-readiness")
        self.assertTrue(has(errors, "projects"))

    def test_broken_registry_ignored_without_project_line(self):
        self._write_registry({"projects": []})  # non-object projects map
        # A brief with no `Project:` line never loads the registry.
        self._write_brief("mvp-readiness", self.VALID_BRIEF)
        self.assertEqual(self._errors("mvp-readiness"), [])

    def test_title_must_match_slug(self):
        self._write_brief(
            "mvp-readiness",
            self.VALID_BRIEF.replace("# mvp-readiness", "# something-else"))
        self.assertTrue(has(self._errors("mvp-readiness"), "expected title"))

    def test_no_workspace_fails_the_mode(self):
        # A root with no discoverable workspace anywhere above it.
        bare = tempfile.mkdtemp()
        try:
            code, err = self._run_cli(
                ["--initiative", "mvp-readiness", "--root", bare])
            self.assertNotEqual(code, 0)
            self.assertIn("no workspace", err.lower())
        finally:
            shutil.rmtree(bare, ignore_errors=True)

    def test_library_lint_ignores_briefs(self):
        # A malformed brief that no epic or change references must not surface
        # in library lint (library lint never walks initiatives/).
        self._write_brief(
            "mvp-readiness", "# wrong-title\nStatus: bogus\nnonsense\n")
        specs = os.path.join(self.root, ".shipd", "verified", "auth")
        os.makedirs(specs, exist_ok=True)
        with open(os.path.join(specs, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(
                "# auth\n\n"
                "### Requirement: Good\nid: good\n\n"
                "The system SHALL be good.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])


class PrdLintTest(unittest.TestCase):
    """PRD structural validation and the ``--prd <slug>`` mode (shipd-prd
    prd-store-format, prd-tier-registry; shipd-spec-lint prd-lint-mode).

    The repo fixture lives *inside* a fake workspace (``<tmp>/repo`` with the
    marker at ``<tmp>/.shipd-config.json`` declaring ``workspace``) so
    ``find_workspace_root`` walking up from the repo finds the temp marker and
    never escapes into the real filesystem. PRDs live at
    ``<tmp>/.shipd/prds/<slug>/prd.md``. ``$HOME`` is overridden so the real
    home config never leaks into resolution."""

    SLUG = "mobile-push"

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.root = os.path.join(self.ws, "repo")
        os.makedirs(self.root, exist_ok=True)
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        declare_workspace(self.ws)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _prd_text(self, tier="standard", slug=None, status="draft",
                  metadata="", sections=None, template_line=None):
        """Compose a PRD body: the header, then one level-2 section per entry
        in ``sections`` (default: exactly the tier's required sections)."""
        if sections is None:
            sections = sc.PRD_TIER_SECTIONS[tier]
        if template_line is None:
            template_line = "Template: %s\n" % tier
        body = "".join(
            "%s\n\nProse for %s.\n\n" % (heading, heading) for heading in sections)
        return (
            "# %s\n" % (slug or self.SLUG)
            + "Status: %s\n" % status
            + template_line
            + metadata
            + "\n"
            + body)

    def _write_prd(self, text, slug=None):
        pdir = os.path.join(self.ws, ".shipd", "prds", slug or self.SLUG)
        os.makedirs(pdir, exist_ok=True)
        path = os.path.join(pdir, "prd.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def _write_brief(self, slug):
        bdir = os.path.join(self.ws, ".shipd", "initiatives", slug)
        os.makedirs(bdir, exist_ok=True)
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: open\n\n## Requirements\n\n- [ ] Ship\n"
                     % slug)

    def _errors(self, slug=None):
        errors = []
        sl.lint_prd(self.ws, slug or self.SLUG, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = sl.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_conforming_prd_lints_clean_at_every_tier(self):
        for tier in sc.PRD_TEMPLATE_TIERS:
            with self.subTest(tier=tier):
                self._write_prd(self._prd_text(tier=tier))
                self.assertEqual(self._errors(), [])
                code, out, _err = self._run_cli(
                    ["--prd", self.SLUG, "--root", self.root])
                self.assertEqual(code, 0)
                self.assertIn("OK", out)

    def test_missing_prd_is_reported(self):
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, self.SLUG))
        self.assertTrue(has(errors, "prd.md"))

    def test_title_must_match_the_directory(self):
        path = self._write_prd(self._prd_text(slug="push-notifications"))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "expected title"))
        self.assertTrue(has(errors, path))

    def test_unknown_status_reports_the_vocabulary(self):
        path = self._write_prd(self._prd_text(status="shipped"))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "shipped"))
        self.assertTrue(has(errors, "superseded"))
        self.assertTrue(has(errors, path))

    def test_missing_template_line_is_not_defaulted(self):
        path = self._write_prd(self._prd_text(template_line=""))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "Template"))
        self.assertTrue(has(errors, path))

    def test_unknown_template_value_errors(self):
        path = self._write_prd(
            self._prd_text(template_line="Template: exhaustive\n"))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "exhaustive"))
        self.assertTrue(has(errors, "comprehensive"))
        self.assertTrue(has(errors, path))

    def test_unrecognized_metadata_key_errors(self):
        path = self._write_prd(self._prd_text(metadata="Project: alpha\n"))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "Project"))
        self.assertTrue(has(errors, "unrecognized"))
        self.assertTrue(has(errors, path))

    def test_resolvable_initiative_passes(self):
        self._write_brief("mvp-readiness")
        self._write_prd(self._prd_text(metadata="Initiative: mvp-readiness\n"))
        self.assertEqual(self._errors(), [])

    def test_unresolvable_initiative_errors(self):
        path = self._write_prd(self._prd_text(metadata="Initiative: no-such-goal\n"))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "no-such-goal"))
        self.assertTrue(has(errors, path))

    def test_missing_tier_section_errors(self):
        sections = [s for s in sc.PRD_TIER_SECTIONS["standard"]
                    if s != "## Non-goals"]
        path = self._write_prd(self._prd_text(sections=sections))
        errors = self._errors()
        self.assertEqual(len(errors), 1)
        self.assertTrue(has(errors, "## Non-goals"))
        self.assertTrue(has(errors, path))

    def test_lower_tier_is_not_held_to_higher_sections(self):
        # The basic tier's three sections only — no `## Users`, no
        # `## Requirements`, no `## Non-goals`.
        self._write_prd(self._prd_text(tier="basic"))
        self.assertEqual(self._errors(), [])

    def test_extra_sections_are_allowed(self):
        sections = list(sc.PRD_TIER_SECTIONS["comprehensive"]) + ["## Pricing"]
        self._write_prd(self._prd_text(tier="comprehensive", sections=sections))
        self.assertEqual(self._errors(), [])

    def test_cli_reports_the_finding_and_exits_non_zero(self):
        sections = [s for s in sc.PRD_TIER_SECTIONS["standard"]
                    if s != "## Non-goals"]
        path = self._write_prd(self._prd_text(sections=sections))
        code, _out, err = self._run_cli(
            ["--prd", self.SLUG, "--root", self.root])
        self.assertNotEqual(code, 0)
        self.assertIn("## Non-goals", err)
        self.assertIn(path, err)
        self.assertIn(self.SLUG, err)

    def test_no_workspace_fails_the_mode(self):
        bare = tempfile.mkdtemp()
        try:
            code, _out, err = self._run_cli(["--prd", self.SLUG, "--root", bare])
            self.assertNotEqual(code, 0)
            self.assertIn("no workspace", err.lower())
            self.assertIn("--prd", err)
        finally:
            shutil.rmtree(bare, ignore_errors=True)

    def test_library_lint_ignores_prds(self):
        # A malformed PRD must not surface in library lint (library lint never
        # walks the workspace's prds/ directory).
        self._write_prd("# wrong-title\nStatus: bogus\nnonsense\n")
        specs = os.path.join(self.root, ".shipd", "verified", "auth")
        os.makedirs(specs, exist_ok=True)
        with open(os.path.join(specs, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(
                "# auth\n\n"
                "### Requirement: Good\nid: good\n\n"
                "The system SHALL be good.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertEqual([str(e) for e in sl.lint_library(self.root)], [])


class WorkspaceLintModeTest(unittest.TestCase):
    """The ``--workspace`` lint mode (shipd-spec-lint workspace-lint-mode): resolves
    the workspace from ``--root`` and reports ``validate_workspace`` findings
    against ``.shipd-config.json``.

    The repo fixture lives inside a fake workspace (``<tmp>/repo`` with the
    marker at ``<tmp>/.shipd-config.json`` declaring ``workspace``) so
    ``find_workspace_root`` resolves inside the temp tree."""

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.root = os.path.join(self.ws, "repo")
        os.makedirs(self.root, exist_ok=True)
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        declare_workspace(self.ws)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_registry(self, payload):
        declare_workspace(self.ws, payload)

    def _run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = sl.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_clean_registry_passes(self):
        self._write_registry(
            {"projects": {"alpha": {"repos": ["repo", "apps/backend"]}}})
        code, out, _err = self._run_cli(["--workspace", "--root", self.root])
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_registry_findings_reported(self):
        # alpha + beta share `shared-lib` (duplicate-path error); gamma's repos
        # is a string (shape error).
        self._write_registry({"projects": {
            "alpha": {"repos": ["shared-lib"]},
            "beta": {"repos": ["shared-lib"]},
            "gamma": {"repos": "not-a-list"}}})
        code, _out, err = self._run_cli(["--workspace", "--root", self.root])
        self.assertNotEqual(code, 0)
        self.assertIn("shared-lib", err)
        self.assertIn("gamma", err)
        self.assertIn(".shipd-config.json", err)

    def test_no_workspace_fails_the_mode(self):
        bare = tempfile.mkdtemp()
        try:
            code, _out, err = self._run_cli(["--workspace", "--root", bare])
            self.assertNotEqual(code, 0)
            self.assertIn("no workspace", err.lower())
        finally:
            shutil.rmtree(bare, ignore_errors=True)


class InitiativeReferenceLintTest(unittest.TestCase):
    """CI-safe ``Initiative:`` reference resolution on epics and standalone
    changes (shipd-workspace initiative-reference-resolution).

    The repo fixture lives inside a fake workspace so the workspace is
    discoverable from ``self.root``; briefs live at
    ``<ws>/.shipd/initiatives/<slug>/brief.md``. ``$HOME`` is overridden so the
    real home config never leaks into resolution."""

    BODY = ("\n## Idea\nA summary.\n\n### Motivation\nBecause.\n\n"
            "### Details\nThe changes.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nLike so.\n")

    EPIC = (
        "# reporting-overhaul\n"
        "Status: ready\n"
        "Initiative: mvp-readiness\n"
        "\n"
        "## Introduction\n\nWhy it matters.\n\n### Non-goals\n\n- Not that.\n\n"
        "## Decisions\n\nWhy.\n\n"
        "## Design\n\nHow.\n\n"
        "## Changes\n\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.root = os.path.join(self.ws, "repo")
        os.makedirs(self.root, exist_ok=True)
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        declare_workspace(self.ws)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_brief(self, slug):
        bdir = os.path.join(self.ws, ".shipd", "initiatives", slug)
        os.makedirs(bdir, exist_ok=True)
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: open\n\nGoal.\n\n## Requirements\n\n"
                     "- [ ] Do it\n" % slug)

    def _write_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _write_change(self, change, initiative):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: ready\nInitiative: %s\n"
                     % (change, initiative) + self.BODY)
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(
                "## ADDED Requirements\n\n"
                "### Requirement: Good\nid: good\n\n"
                "The system SHALL be good.\n\n"
                "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")

    def _ref_errors(self, metadata, root=None):
        errors = []
        sl.check_initiative_reference(root or self.root, metadata, errors)
        return [str(e) for e in errors]

    def test_missing_brief_errors_naming_the_path(self):
        errors = self._ref_errors([("Initiative", "mvp-readiness")])
        self.assertTrue(has(errors, "mvp-readiness"))
        self.assertTrue(has(errors, "brief.md"))

    def test_resolved_brief_passes(self):
        self._write_brief("mvp-readiness")
        self.assertEqual(
            self._ref_errors([("Initiative", "mvp-readiness")]), [])

    def test_no_workspace_skips_silently(self):
        bare = tempfile.mkdtemp()
        try:
            self.assertEqual(
                self._ref_errors([("Initiative", "mvp-readiness")], root=bare),
                [])
        finally:
            shutil.rmtree(bare, ignore_errors=True)

    def _nested_repo(self):
        """A nested workspace (``<self.ws>/nested``) with a repo beneath it,
        declared beside ``self.ws`` and holding no brief of its own."""
        inner = os.path.join(self.ws, "nested")
        os.makedirs(inner, exist_ok=True)
        declare_workspace(inner)
        repo = os.path.join(inner, "repo")
        os.makedirs(repo, exist_ok=True)
        return repo

    def test_inherited_brief_from_enclosing_workspace_resolves_clean(self):
        # Only self.ws (the enclosing workspace) holds the brief.
        self._write_brief("mvp-readiness")
        repo = self._nested_repo()
        self.assertEqual(
            self._ref_errors([("Initiative", "mvp-readiness")], root=repo), [])

    def test_still_errors_when_no_chain_member_holds_the_brief(self):
        repo = self._nested_repo()
        errors = self._ref_errors(
            [("Initiative", "mvp-readiness")], root=repo)
        self.assertTrue(has(errors, "mvp-readiness"))
        self.assertTrue(has(errors, "brief.md"))

    def _write_epic_at(self, root, slug, text):
        edir = os.path.join(root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_epic_under_nested_workspace_resolves_via_inherited_brief(self):
        # Only self.ws (the enclosing workspace) holds the brief.
        self._write_brief("mvp-readiness")
        repo = self._nested_repo()
        self._write_epic_at(repo, "reporting-overhaul", self.EPIC)
        errors = [str(e) for e in
                  self._collect(lambda errs:
                                sl.lint_epic(repo, "reporting-overhaul", errs))]
        self.assertFalse(has(errors, "brief.md"))

    def test_epic_under_nested_workspace_errors_with_no_brief_anywhere(self):
        repo = self._nested_repo()
        self._write_epic_at(repo, "reporting-overhaul", self.EPIC)
        errors = [str(e) for e in
                  self._collect(lambda errs:
                                sl.lint_epic(repo, "reporting-overhaul", errs))]
        self.assertTrue(has(errors, "mvp-readiness"))
        self.assertTrue(has(errors, "brief.md"))

    def test_epic_reference_errors_when_brief_missing(self):
        self._write_epic("reporting-overhaul", self.EPIC)
        errors = [str(e) for e in
                  self._collect(lambda errs:
                                sl.lint_epic(self.root, "reporting-overhaul",
                                             errs))]
        self.assertTrue(has(errors, "mvp-readiness"))
        self.assertTrue(has(errors, "brief.md"))

    def test_epic_reference_passes_when_brief_exists(self):
        self._write_brief("mvp-readiness")
        self._write_epic("reporting-overhaul", self.EPIC)
        errors = [str(e) for e in
                  self._collect(lambda errs:
                                sl.lint_epic(self.root, "reporting-overhaul",
                                             errs))]
        self.assertFalse(has(errors, "brief.md"))

    def test_change_reference_errors_when_brief_missing(self):
        self._write_change("solo-change", "mvp-readiness")
        errors = [str(e) for e in
                  sl.lint_change(self.root, "solo-change")]
        self.assertTrue(has(errors, "mvp-readiness"))
        self.assertTrue(has(errors, "brief.md"))

    def test_change_reference_passes_when_brief_exists(self):
        self._write_brief("mvp-readiness")
        self._write_change("solo-change", "mvp-readiness")
        self.assertEqual([str(e) for e in
                          sl.lint_change(self.root, "solo-change")], [])

    def _collect(self, fn):
        errors = []
        fn(errors)
        return errors


class EpicPrdReferenceLintTest(unittest.TestCase):
    """``PRD:`` reference resolution on epics (shipd-spec-format
    epic-header-metadata; shipd-prd prd-store-format).

    The repo fixture lives inside a fake workspace so the workspace is
    discoverable from ``self.root``; PRDs live at
    ``<ws>/.shipd/prds/<slug>/prd.md``. ``$HOME`` is overridden so the real
    home config never leaks into resolution."""

    EPIC = (
        "# reporting-overhaul\n"
        "Status: draft\n"
        "PRD: mobile-push\n"
        "\n"
        "## Introduction\n\nWhy it matters.\n\n### Non-goals\n\n- Not that.\n\n"
        "## Decisions\n\nWhy.\n\n"
        "## Design\n\nHow.\n\n"
        "## Changes\n\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
    )

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.root = os.path.join(self.ws, "repo")
        os.makedirs(self.root, exist_ok=True)
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        declare_workspace(self.ws)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _write_prd(self, slug, ws=None):
        pdir = os.path.join(ws or self.ws, ".shipd", "prds", slug)
        os.makedirs(pdir, exist_ok=True)
        with open(os.path.join(pdir, "prd.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: draft\nTemplate: standard\n\n"
                     "## Problem\n\nProse.\n" % slug)

    def _write_epic(self, slug, text, root=None):
        edir = os.path.join(root or self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _epic_errors(self, slug, root=None):
        errors = []
        sl.lint_epic(root or self.root, slug, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = sl.main(argv)
        return code, err.getvalue()

    def _ref_errors(self, metadata, root=None):
        errors = []
        sl.check_prd_reference(root or self.root, metadata, errors)
        return [str(e) for e in errors]

    def test_resolved_prd_passes(self):
        self._write_prd("mobile-push")
        self.assertEqual(self._ref_errors([("PRD", "mobile-push")]), [])

    def test_missing_prd_errors_naming_the_path(self):
        errors = self._ref_errors([("PRD", "mobile-push")])
        self.assertTrue(has(errors, "mobile-push"))
        self.assertTrue(has(errors, "prd.md"))

    def test_no_prd_line_is_a_no_op(self):
        self.assertEqual(self._ref_errors([("Theme", "reliability")]), [])

    def test_epic_carrying_a_resolving_prd_lints_clean(self):
        self._write_prd("mobile-push")
        self._write_epic("reporting-overhaul", self.EPIC)
        self.assertEqual(self._epic_errors("reporting-overhaul"), [])
        code, _err = self._run_cli(["--epic", "reporting-overhaul",
                                    "--root", self.root])
        self.assertEqual(code, 0)

    def test_epic_with_an_unresolvable_prd_errors_naming_the_path(self):
        self._write_epic(
            "reporting-overhaul",
            self.EPIC.replace("PRD: mobile-push", "PRD: no-such-prd"))
        errors = self._epic_errors("reporting-overhaul")
        self.assertTrue(has(errors, "no-such-prd"))
        self.assertTrue(has(errors, "prd.md"))
        code, _err = self._run_cli(["--epic", "reporting-overhaul",
                                    "--root", self.root])
        self.assertNotEqual(code, 0)

    def test_inherited_prd_from_enclosing_workspace_resolves_clean(self):
        # Only the enclosing workspace holds the PRD; the epic lives under a
        # nested workspace that holds none of its own.
        self._write_prd("mobile-push")
        inner = os.path.join(self.ws, "nested")
        os.makedirs(inner, exist_ok=True)
        declare_workspace(inner)
        repo = os.path.join(inner, "repo")
        os.makedirs(repo, exist_ok=True)
        self._write_epic("reporting-overhaul", self.EPIC, root=repo)
        self.assertEqual(self._epic_errors("reporting-overhaul", root=repo), [])

    def test_no_workspace_skips_silently(self):
        # CI-safe, exactly as `Initiative:` is: a bare checkout (a GitHub
        # runner) has no workspace, so resolution is skipped rather than
        # failing the required `ci` check on files outside the repository.
        bare = tempfile.mkdtemp()
        try:
            self.assertEqual(
                self._ref_errors([("PRD", "mobile-push")], root=bare), [])
        finally:
            shutil.rmtree(bare, ignore_errors=True)

    def test_epic_in_a_workspace_less_checkout_carries_no_prd_error(self):
        bare = tempfile.mkdtemp()
        try:
            self._write_epic("reporting-overhaul", self.EPIC, root=bare)
            errors = self._epic_errors("reporting-overhaul", root=bare)
            self.assertFalse(has(errors, "prd.md"))
            self.assertEqual(errors, [])
        finally:
            shutil.rmtree(bare, ignore_errors=True)


class WikiLintModeTest(unittest.TestCase):
    """``lint_wiki`` and the ``--wiki`` lint mode (shipd-spec-lint wiki-lint-mode,
    shipd-wiki wiki-page-grammar, wiki-index-and-log, wiki-question-queue).

    The repo fixture lives inside a fake workspace (``<tmp>/repo`` with the
    marker at ``<tmp>/.shipd-config.json`` declaring ``workspace``) so
    ``find_workspace_root`` resolves inside the temp tree. The store lives at
    ``<tmp>/.shipd/wiki/``. ``$HOME`` is overridden so the real home config never
    leaks into resolution."""

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self.root = os.path.join(self.ws, "repo")
        os.makedirs(self.root, exist_ok=True)
        self.home = tempfile.mkdtemp()
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        declare_workspace(self.ws)
        self._seed_store()

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.ws, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def _wiki(self):
        return os.path.join(self.ws, ".shipd", "wiki")

    def _write(self, relpath, text):
        path = os.path.join(self._wiki(), relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _seed_store(self):
        """A clean store: two pages (welcome links to intro), an index
        cataloging both, a dated log entry, an empty queue, and empty
        sources/wiki dirs."""
        self._write("schema.md", "# Wiki schema\n\nConventions live here.\n")
        self._write(
            "index.md",
            "# Index\n\n"
            "- [[welcome]] — The welcome page.\n"
            "- [[intro]] — Introduction.\n")
        self._write(
            "log.md",
            "# Log\n\n## [2026-07-30] wiki-init | seeded the store\n\n"
            "Initialized.\n")
        self._write("queue.md", "# Queue\n")
        self._write("wiki/welcome.md",
                    "# Welcome\n\nStart here, then read [[intro]].\n")
        self._write("wiki/intro.md", "# Intro\n\nThe intro page.\n")
        os.makedirs(os.path.join(self._wiki(), "sources"), exist_ok=True)

    def _errors(self):
        errors = []
        sl.lint_wiki(self.ws, errors)
        return [str(e) for e in errors]

    def _run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = sl.main(argv)
        return code, out.getvalue(), err.getvalue()

    # -- clean store -------------------------------------------------------

    def test_clean_store_has_no_errors(self):
        self.assertEqual(self._errors(), [])

    # -- layout presence ---------------------------------------------------

    def test_missing_layout_file_errors(self):
        os.remove(os.path.join(self._wiki(), "schema.md"))
        self.assertTrue(has(self._errors(), "schema.md"))

    # -- reserved slug -----------------------------------------------------

    def test_reserved_page_slug_errors(self):
        self._write("wiki/index.md", "# Index page\n\nOops.\n")
        errors = self._errors()
        self.assertTrue(has(errors, "reserved"))
        self.assertTrue(has(errors, "index"))

    # -- wikilink resolution ----------------------------------------------

    def test_dead_wikilink_errors_but_fenced_link_ignored(self):
        self._write(
            "wiki/dangling.md",
            "# Dangling\n\nSee [[nonexistent]].\n\n"
            "```\nnot a [[fenced-link]] in code\n```\n")
        self._write(
            "index.md",
            "# Index\n\n"
            "- [[welcome]] — The welcome page.\n"
            "- [[intro]] — Introduction.\n"
            "- [[dangling]] — Dangling page.\n")
        errors = self._errors()
        self.assertTrue(has(errors, "nonexistent"))
        self.assertTrue(has(errors, "dangling"))
        self.assertFalse(has(errors, "fenced-link"))

    # -- bidirectional index coverage -------------------------------------

    def test_unindexed_page_errors(self):
        self._write("wiki/orphan.md", "# Orphan\n\nNo index entry.\n")
        self.assertTrue(has(self._errors(), "orphan"))

    def test_index_entry_with_no_page_errors(self):
        self._write(
            "index.md",
            "# Index\n\n"
            "- [[welcome]] — The welcome page.\n"
            "- [[intro]] — Introduction.\n"
            "- [[ghost]] — A page that does not exist.\n")
        self.assertTrue(has(self._errors(), "ghost"))

    # -- log header format -------------------------------------------------

    def test_malformed_log_header_errors(self):
        self._write("log.md", "# Log\n\n## just a header\n\nBody.\n")
        self.assertTrue(has(self._errors(), "just a header"))

    # -- queue block fields ------------------------------------------------

    def test_queue_block_missing_field_errors(self):
        self._write(
            "queue.md",
            "# Queue\n\n## q-stale-cache\n"
            "- Asked: 2026-07-30 teach-session\n"
            "- Question: Is it stale?\n"
            "- Options: yes | no\n"
            "- Answer: pending\n")  # no Recommendation line
        errors = self._errors()
        self.assertTrue(has(errors, "q-stale-cache"))
        self.assertTrue(has(errors, "Recommendation"))

    # -- CLI mode ----------------------------------------------------------

    def test_cli_clean_store_exits_zero(self):
        code, out, _err = self._run_cli(["--wiki", "--root", self.root])
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_cli_violations_gate(self):
        self._write("wiki/orphan.md", "# Orphan\n\nSee [[missing]].\n")
        code, _out, err = self._run_cli(["--wiki", "--root", self.root])
        self.assertNotEqual(code, 0)
        self.assertIn("orphan", err)

    def test_cli_no_workspace_fails_the_mode(self):
        bare = tempfile.mkdtemp()
        try:
            code, _out, err = self._run_cli(["--wiki", "--root", bare])
            self.assertNotEqual(code, 0)
            self.assertIn("no workspace", err.lower())
        finally:
            shutil.rmtree(bare, ignore_errors=True)


class GatingExitCodeTest(unittest.TestCase):
    def _run(self, argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            return sl.main(argv)

    def test_clean_change_exits_zero(self):
        self.assertEqual(self._run(["sample-change", "--root", SAMPLE_ROOT]), 0)

    def test_clean_library_exits_zero(self):
        self.assertEqual(self._run(["--root", SAMPLE_ROOT]), 0)

    def test_errors_exit_nonzero(self):
        self.assertEqual(self._run(["unknown-op", "--root", BAD_ROOT]), 1)

    def test_missing_id_change_exits_nonzero(self):
        self.assertEqual(self._run(["missing-id", "--root", BAD_ROOT]), 1)


class JsonOutputTest(unittest.TestCase):
    """The ``--json`` machine-output flag (shipd-spec-lint lint-json): one
    JSON object on stdout carrying ``ok``, ``errors``, and ``warnings``, with
    the flagless exit code and no text report on stdout.

    Written test-first; expected to FAIL until the flag lands in
    ``spec_lint.py`` (task 3.2)."""

    DELTA = ("## ADDED Requirements\n\n"
             "### Requirement: Good\nid: good\n\n"
             "The system SHALL be good.\n\n"
             "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="spec-lint-json-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, argv):
        """``(exit code, stdout, stderr)`` for one ``main`` invocation."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = sl.main(argv)
        return code, out.getvalue(), err.getvalue()

    def _write_change(self, change, plan_text, delta=None):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(os.path.join(cdir, "specs", "auth"), exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(plan_text)
        with open(os.path.join(cdir, "specs", "auth", "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self.DELTA if delta is None else delta)

    def _plan(self, change, idea="A summary."):
        return ("# %s\nStatus: ready\n\n## Idea\n%s\n\n"
                "### Motivation\nWhy.\n\n### Details\nThe changes.\n\n"
                "### Non-goals\nNot that.\n\n"
                "## Implementation\nLike so.\n" % (change, idea))

    def test_clean_library_is_an_ok_object_exiting_zero(self):
        code, out, _err = self._run(["--root", SAMPLE_ROOT, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out),
                         {"ok": True, "errors": [], "warnings": []})

    def test_clean_change_is_an_ok_object_exiting_zero(self):
        self._write_change("lean-change", self._plan("lean-change"))
        code, out, _err = self._run(
            ["lean-change", "--root", self.root, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out),
                         {"ok": True, "errors": [], "warnings": []})

    def test_findings_land_in_the_errors_array(self):
        code, out, _err = self._run(["missing-id", "--root", BAD_ROOT,
                                     "--json"])
        # The exit code is the flagless one for the same findings.
        self.assertEqual(code, self._run(["missing-id", "--root", BAD_ROOT])[0])
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertFalse(data["ok"])
        self.assertTrue(any("has no `id:` line" in err
                            for err in data["errors"]),
                        data["errors"])

    def test_error_strings_match_the_texts_the_text_mode_prints(self):
        _code, _out, err = self._run(["missing-id", "--root", BAD_ROOT])
        text_errors = [line[len("ERROR: "):] for line in err.splitlines()
                       if line.startswith("ERROR: ")]
        _code, out, _err = self._run(["missing-id", "--root", BAD_ROOT,
                                      "--json"])
        self.assertEqual(json.loads(out)["errors"], text_errors)

    def test_warnings_are_carried_in_the_warnings_array(self):
        filler = "filler text " * 800  # ~9,600 chars, over the ~8,000 budget
        self._write_change("big-change", self._plan("big-change", filler))
        code, out, _err = self._run(
            ["big-change", "--root", self.root, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertTrue(data["ok"])
        self.assertEqual(data["errors"], [])
        self.assertTrue(any("context-economy budget" in warning
                            for warning in data["warnings"]),
                        data["warnings"])

    def test_nothing_but_the_object_is_written_to_stdout(self):
        _code, out, _err = self._run(["missing-id", "--root", BAD_ROOT,
                                      "--json"])
        self.assertNotIn("ERROR:", out)
        self.assertNotIn("error(s) in", out)
        json.loads(out)  # the whole of stdout is the one document

    def test_text_mode_is_unchanged_without_the_flag(self):
        self._write_change("lean-change", self._plan("lean-change"))
        code, out, err = self._run(["lean-change", "--root", self.root])
        self.assertEqual(code, 0)
        self.assertEqual(out, "OK: change 'lean-change' is valid.\n")
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
