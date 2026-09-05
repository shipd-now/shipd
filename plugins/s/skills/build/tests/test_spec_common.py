#!/usr/bin/env python3
"""Unit tests for spec_common: parser, content hashing, and serialization."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


@contextlib.contextmanager
def home_set_to(path):
    """Override ``$HOME`` (the ``expanduser`` seam) for the duration of the
    block, so config resolution never reads the real home directory."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = path
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


@contextlib.contextmanager
def schema_version_set_to(value):
    """Lift ``spec_common.SCHEMA_VERSION`` for the duration of the block, so the
    comparison rules can be exercised on both sides of the grammar's current
    floor without waiting for a real bump."""
    old = sc.SCHEMA_VERSION
    sc.SCHEMA_VERSION = value
    try:
        yield
    finally:
        sc.SCHEMA_VERSION = old


class _BlockedFinder:
    """A ``sys.meta_path`` finder that makes importing the named modules raise
    :class:`ModuleNotFoundError`, whether or not they are installed."""

    def __init__(self, names):
        self.names = set(names)

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.names:
            raise ModuleNotFoundError(
                "No module named %r" % fullname, name=fullname)
        return None


@contextlib.contextmanager
def imports_blocked(*names):
    """Block imports of ``names`` for the duration of the block, so a test of
    the missing-dependency path is deterministic on machines that have the
    dependency installed as well as on those that do not."""
    saved = {n: sys.modules.pop(n) for n in names if n in sys.modules}
    finder = _BlockedFinder(names)
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        sys.modules.update(saved)


HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
FIXTURES = os.path.join(HERE, "fixtures")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_common as sc  # noqa: E402

SAMPLE_MASTER = os.path.join(
    FIXTURES, "sample", ".shipd", "verified", "auth", "spec.md")
SAMPLE_DELTA = os.path.join(
    FIXTURES, "sample", ".shipd", "planned", "sample-change",
    "specs", "auth", "spec.md")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ParserTest(unittest.TestCase):
    def test_parse_master_requirements(self):
        spec = sc.parse_spec(read(SAMPLE_MASTER))
        self.assertEqual(spec.preamble, "# auth")
        ids = [r.id for r in spec.requirements]
        self.assertEqual(
            ids,
            ["enforce-sso-timeout", "legacy-cookie-fallback",
             "password-complexity"])

    def test_parse_metadata_and_scenarios(self):
        spec = sc.parse_spec(read(SAMPLE_MASTER))
        req = spec.requirements[0]
        self.assertEqual(req.title, "Enforce SSO session timeout")
        self.assertEqual(req.id, "enforce-sso-timeout")
        self.assertIsNone(req.base)
        self.assertEqual(len(req.scenarios), 1)
        self.assertEqual(req.scenarios[0].level, 4)
        self.assertEqual(req.scenarios[0].title, "Idle session is ended")
        self.assertIn("SHALL", req.body)

    def test_parse_delta_operations(self):
        delta = sc.parse_delta(read(SAMPLE_DELTA))
        self.assertEqual([r.id for r in delta.added], ["rate-limit-login"])
        self.assertEqual([r.id for r in delta.modified], ["enforce-sso-timeout"])
        self.assertEqual([r.id for r in delta.removed],
                         ["legacy-cookie-fallback"])
        self.assertEqual([(r.from_id, r.to_id) for r in delta.renamed],
                         [("password-complexity", "password-strength")])
        self.assertEqual(delta.unknown_ops, [])

    def test_delta_base_reason_migration(self):
        delta = sc.parse_delta(read(SAMPLE_DELTA))
        mod = delta.modified[0]
        self.assertEqual(mod.base, "3c1af58513af")
        rem = delta.removed[0]
        self.assertIsNotNone(rem.base)
        self.assertIsNotNone(rem.reason)
        self.assertIsNotNone(rem.migration)

    def test_unknown_operation_header_is_captured(self):
        delta = sc.parse_delta(read(os.path.join(
            FIXTURES, "bad", ".shipd", "planned", "unknown-op",
            "specs", "auth", "spec.md")))
        self.assertEqual(delta.unknown_ops, ["## CHANGED Requirements"])

    def test_missing_id_yields_none(self):
        delta = sc.parse_delta(read(os.path.join(
            FIXTURES, "bad", ".shipd", "planned", "missing-id",
            "specs", "auth", "spec.md")))
        self.assertIsNone(delta.added[0].id)

    def test_mis_leveled_scenario_records_level(self):
        delta = sc.parse_delta(read(os.path.join(
            FIXTURES, "bad", ".shipd", "planned", "scenario-level",
            "specs", "auth", "spec.md")))
        req = delta.added[0]
        self.assertEqual(len(req.scenarios), 1)
        self.assertEqual(req.scenarios[0].level, 3)


class ContentHashTest(unittest.TestCase):
    def test_cosmetic_whitespace_same_hash(self):
        a = sc.parse_requirement_block(
            "### Requirement: X\nid: x\n\n"
            "The system SHALL do it.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b")
        b = sc.parse_requirement_block(
            "### Requirement: X reworded\nid: x\nbase: deadbeef01\n\n"
            "The system SHALL do it.   \n\n\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b   ")
        self.assertEqual(sc.content_hash(a), sc.content_hash(b))

    def test_id_and_base_excluded_from_hash(self):
        a = sc.parse_requirement_block(
            "### Requirement: X\nid: alpha\n\n"
            "The system SHALL do it.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b")
        b = sc.parse_requirement_block(
            "### Requirement: X\nid: beta\nbase: 999999999999\n\n"
            "The system SHALL do it.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b")
        # Different id (a rename) must not change the content hash.
        self.assertEqual(sc.content_hash(a), sc.content_hash(b))

    def test_hash_is_truncated_hex(self):
        spec = sc.parse_spec(read(SAMPLE_MASTER))
        h = sc.content_hash(spec.requirements[0])
        self.assertEqual(len(h), sc.HASH_LENGTH)
        int(h, 16)  # raises if not hex

    def test_content_change_changes_hash(self):
        a = sc.parse_requirement_block(
            "### Requirement: X\nid: x\n\nThe system SHALL do A.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b")
        b = sc.parse_requirement_block(
            "### Requirement: X\nid: x\n\nThe system SHALL do B.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b")
        self.assertNotEqual(sc.content_hash(a), sc.content_hash(b))

    def test_delta_base_matches_master_hash(self):
        master = sc.parse_spec(read(SAMPLE_MASTER))
        by_id = {r.id: r for r in master.requirements}
        delta = sc.parse_delta(read(SAMPLE_DELTA))
        # The delta was authored against the current master, so the recorded
        # base hashes match the master content hashes.
        for entry in delta.modified + delta.removed:
            self.assertEqual(entry.base, sc.content_hash(by_id[entry.id]))


class SerializationTest(unittest.TestCase):
    def test_master_roundtrip_is_exact(self):
        original = read(SAMPLE_MASTER)
        rendered = sc.render_spec(sc.parse_spec(original))
        self.assertEqual(rendered, original)

    def test_parse_render_parse_is_stable(self):
        spec1 = sc.parse_spec(read(SAMPLE_MASTER))
        spec2 = sc.parse_spec(sc.render_spec(spec1))
        self.assertEqual([r.id for r in spec1.requirements],
                         [r.id for r in spec2.requirements])
        for a, b in zip(spec1.requirements, spec2.requirements):
            self.assertEqual(sc.content_hash(a), sc.content_hash(b))

    def test_render_drops_delta_metadata(self):
        delta = sc.parse_delta(read(SAMPLE_DELTA))
        rendered = sc.render_requirement(delta.modified[0])
        self.assertNotIn("base:", rendered)
        self.assertIn("id: enforce-sso-timeout", rendered)


class PlanMetadataParserTest(unittest.TestCase):
    """parse_plan_metadata: the contiguous ``Key: value`` block right after the
    ``Status:`` line (shipd-spec-format plan-header-metadata-lines)."""

    def test_all_keys_parsed_in_order(self):
        pairs = sc.parse_plan_metadata(
            "# c\nStatus: draft\nTheme: reliability\n"
            "Epic: reporting-overhaul\n\n## Idea\nWhy.\n")
        self.assertEqual(
            pairs, [("Theme", "reliability"), ("Epic", "reporting-overhaul")])

    def test_metadata_free_header_yields_empty(self):
        self.assertEqual(
            sc.parse_plan_metadata("# c\nStatus: ready\n\n## Idea\nWhy.\n"), [])

    def test_no_status_line_yields_empty(self):
        self.assertEqual(
            sc.parse_plan_metadata("# c\nTheme: reliability\n"), [])

    def test_unrecognized_key_is_included(self):
        pairs = sc.parse_plan_metadata("# c\nStatus: draft\nThem: reliability\n")
        self.assertEqual(pairs, [("Them", "reliability")])

    def test_block_ends_at_blank_line(self):
        pairs = sc.parse_plan_metadata(
            "# c\nStatus: draft\nProfile: lite\n\nTheme: reliability\n")
        self.assertEqual(pairs, [("Profile", "lite")])

    def test_block_ends_at_heading(self):
        pairs = sc.parse_plan_metadata(
            "# c\nStatus: draft\nProfile: lite\n## Idea\nWhy.\n")
        self.assertEqual(pairs, [("Profile", "lite")])

    def test_module_constants(self):
        self.assertEqual(
            sc.METADATA_KEYS,
            ("Profile", "Epic", "Initiative", "Theme", "Fixes"))
        self.assertEqual(sc.PROFILES, ("full", "lite"))


class EpicChangesParserTest(unittest.TestCase):
    """parse_epic_changes: the ``## Changes`` stub table of an epic
    (shipd-spec-format epic-artifact-layout / epic-header-metadata)."""

    EPIC = (
        "# reporting-overhaul\n"
        "Status: draft\n"
        "Theme: reliability\n"
        "\n"
        "## Decisions\n\nWhy.\n\n"
        "## Design\n\nHow.\n\n"
        "## Changes\n\n"
        "| Change | Description | Code | Integration | Unknowns | Risk |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| csv-export | Export as CSV | low | medium | low | low |\n"
        "| pdf-export | Export as PDF | high | high | medium | high |\n"
    )

    def test_epic_constants(self):
        self.assertEqual(
            sc.EPIC_STATUSES, ("draft", "ready", "active", "complete"))
        self.assertEqual(sc.EPIC_METADATA_KEYS, ("Theme", "Initiative"))
        self.assertEqual(sc.EPIC_RATINGS, ("low", "medium", "high"))
        self.assertEqual(
            sc.EPIC_CHANGES_COLUMNS,
            ("Change", "Description", "Code", "Integration", "Unknowns",
             "Risk"))

    def test_parses_header_and_rows(self):
        header, rows = sc.parse_epic_changes(self.EPIC)
        self.assertEqual(
            header,
            ["Change", "Description", "Code", "Integration", "Unknowns",
             "Risk"])
        self.assertEqual(rows, [
            ("csv-export", "Export as CSV",
             ("low", "medium", "low", "low")),
            ("pdf-export", "Export as PDF",
             ("high", "high", "medium", "high")),
        ])

    def test_separator_row_is_skipped(self):
        # The `| --- | ... |` alignment row is not returned as a data row.
        _header, rows = sc.parse_epic_changes(self.EPIC)
        self.assertNotIn("---", [slug for slug, _d, _r in rows])

    def test_table_without_separator_row_parses(self):
        text = (
            "## Changes\n\n"
            "| Change | Description | Code | Integration | Unknowns | Risk |\n"
            "| csv-export | Export as CSV | low | medium | low | low |\n")
        _header, rows = sc.parse_epic_changes(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "csv-export")

    def test_missing_changes_section_returns_none(self):
        text = "# e\nStatus: draft\n\n## Decisions\n\nWhy.\n"
        self.assertEqual(sc.parse_epic_changes(text), (None, []))

    def test_changes_section_without_table_returns_none(self):
        text = "## Changes\n\nNo table here yet.\n"
        self.assertEqual(sc.parse_epic_changes(text), (None, []))

    def test_section_ends_at_next_heading(self):
        text = (
            "## Changes\n\n"
            "| Change | Description | Code | Integration | Unknowns | Risk |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| csv-export | Export as CSV | low | medium | low | low |\n"
            "\n## Appendix\n\n| not | a | stub | table | row | here |\n")
        _header, rows = sc.parse_epic_changes(text)
        self.assertEqual([slug for slug, _d, _r in rows], ["csv-export"])


def _write_ws_config(root, workspace=None, extra=None):
    """Write ``<root>/.shipd-config.json`` declaring a ``workspace`` object (plus
    any ``extra`` top-level keys) and return ``root``. Pass ``workspace=None``
    to write a config with no ``workspace`` key at all."""
    data = dict(extra or {})
    if workspace is not None:
        data["workspace"] = workspace
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, sc.CONFIG_FILENAME), "w",
              encoding="utf-8") as fh:
        json.dump(data, fh)
    return root


def _write_raw_config(root, payload):
    """Write raw text as ``<root>/.shipd-config.json`` and return ``root``."""
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, sc.CONFIG_FILENAME), "w",
              encoding="utf-8") as fh:
        fh.write(payload)
    return root


class WorkspaceDiscoveryTest(unittest.TestCase):
    """find_workspace_root and load_workspace on the ``.shipd-config.json``
    ``workspace``-key convention (shipd-workspace workspace-root-discovery,
    workspace-registry-loading). ``$HOME`` is overridden so the real home
    config never masquerades as an ancestor workspace."""

    def test_nearest_ancestor_wins(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, {})
            nested = os.path.join(ws, "nested")
            _write_ws_config(nested, {})
            start = os.path.join(nested, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.find_workspace_root(start), nested)

    def test_no_declaration_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.join(os.path.realpath(tmp), "a", "b")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(sc.find_workspace_root(start))

    def test_config_without_workspace_is_not_a_root(self):
        # A config declaring only `dir` (no `workspace`) is not a workspace root.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            repo = os.path.realpath(tmp)
            _write_ws_config(repo, workspace=None, extra={"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(sc.find_workspace_root(repo))

    def test_starting_directory_is_the_root(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, {})
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.find_workspace_root(ws), ws)

    def test_works_from_non_git_directory(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, {})
            start = os.path.join(ws, "sub", "dir")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.find_workspace_root(start), ws)

    def test_registry_is_the_workspace_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, {"projects": {}, "future-key": {"x": 1}})
            data = sc.load_workspace(ws)
            self.assertEqual(data["projects"], {})
            self.assertEqual(data["future-key"], {"x": 1})

    def test_load_non_object_workspace_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, [])
            with self.assertRaises(sc.ConfigError) as cm:
                sc.load_workspace(ws)
            self.assertIn(sc.CONFIG_FILENAME, str(cm.exception))

    def test_load_invalid_json_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            _write_raw_config(ws, "{ not json")
            with self.assertRaises(sc.ConfigError) as cm:
                sc.load_workspace(ws)
            self.assertIn(sc.CONFIG_FILENAME, str(cm.exception))

    def test_load_missing_workspace_key_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, workspace=None, extra={"dir": "specs"})
            with self.assertRaises(sc.ConfigError) as cm:
                sc.load_workspace(ws)
            self.assertIn(sc.CONFIG_FILENAME, str(cm.exception))


class WorkspaceChainTest(unittest.TestCase):
    """workspace_chain on the ``.shipd-config.json`` ``workspace``-key
    convention (shipd-workspace workspace-root-discovery). ``$HOME`` is
    overridden so the real home config never masquerades as an ancestor
    workspace."""

    def test_two_nested_declaring_directories_yield_both_nearest_first(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_chain(start), [inner, outer])

    def test_single_declaring_ancestor_yields_one(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, {})
            start = os.path.join(ws, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_chain(start), [ws])

    def test_no_declaring_ancestor_yields_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.join(os.path.realpath(tmp), "a", "b")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_chain(start), [])

    def test_find_workspace_root_is_the_chains_first_member(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                chain = sc.workspace_chain(start)
                self.assertEqual(sc.find_workspace_root(start), chain[0])

    def test_find_workspace_root_is_none_on_empty_chain(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.join(os.path.realpath(tmp), "a", "b")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_chain(start), [])
                self.assertIsNone(sc.find_workspace_root(start))


class WorkspaceChainFacilitiesTest(unittest.TestCase):
    """resolve_wiki_stores, resolve_initiative_brief, and registry_root, each
    built on workspace_chain (shipd-workspace workspace-chain-facilities).
    ``$HOME`` is overridden so the real home config never masquerades as an
    ancestor workspace."""

    def test_resolve_wiki_stores_lists_existing_chain_stores_nearest_first(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            os.makedirs(sc.wiki_dir(outer), exist_ok=True)
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            os.makedirs(sc.wiki_dir(inner), exist_ok=True)
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.resolve_wiki_stores(start),
                    [sc.wiki_dir(inner), sc.wiki_dir(outer)])

    def test_resolve_wiki_stores_skips_members_with_no_store(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            os.makedirs(sc.wiki_dir(outer), exist_ok=True)
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            # inner declares no wiki store on disk.
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.resolve_wiki_stores(start), [sc.wiki_dir(outer)])

    def test_resolve_wiki_stores_empty_chain_yields_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.join(os.path.realpath(tmp), "a", "b")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.resolve_wiki_stores(start), [])

    def test_resolve_initiative_brief_finds_nearest_member_holding_it(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            brief = sc.initiative_brief_path(outer, "mvp-readiness")
            os.makedirs(os.path.dirname(brief), exist_ok=True)
            with open(brief, "w", encoding="utf-8") as fh:
                fh.write("# mvp-readiness\n")
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.resolve_initiative_brief(start, "mvp-readiness"), brief)

    def test_resolve_initiative_brief_none_when_no_member_holds_it(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            _write_ws_config(ws, {})
            start = os.path.join(ws, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(
                    sc.resolve_initiative_brief(start, "mvp-readiness"))

    def test_resolve_initiative_brief_empty_chain_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.join(os.path.realpath(tmp), "a", "b")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(
                    sc.resolve_initiative_brief(start, "mvp-readiness"))

    def test_registry_root_is_nearest_member_declaring_projects(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {"projects": {"alpha": {}}})
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.registry_root(start), outer)

    def test_registry_root_falls_back_to_chains_first_member(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            inner = os.path.join(outer, "nested")
            _write_ws_config(inner, {})
            start = os.path.join(inner, "repo")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.registry_root(start), inner)

    def test_registry_root_none_on_empty_chain(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.join(os.path.realpath(tmp), "a", "b")
            os.makedirs(start, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(sc.registry_root(start))


class InitWorkspaceTest(unittest.TestCase):
    """init_workspace on the config-file convention (shipd-workspace
    workspace-initialization)."""

    def test_creates_workspace_declaration(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            target = os.path.realpath(tmp)
            with home_set_to(os.path.realpath(home)):
                root = sc.init_workspace(target)
            self.assertEqual(root, target)
            cfg = os.path.join(target, sc.CONFIG_FILENAME)
            self.assertTrue(os.path.isfile(cfg))
            with open(cfg, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["workspace"], {})

    def test_preserves_existing_keys(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            target = os.path.realpath(tmp)
            _write_ws_config(target, workspace=None, extra={"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                sc.init_workspace(target)
            with open(os.path.join(target, sc.CONFIG_FILENAME),
                      encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["dir"], "specs")
            self.assertEqual(data["workspace"], {})

    def test_refuses_under_existing_workspace(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = _write_ws_config(os.path.realpath(tmp), {})
            nested = os.path.join(ws, "sub")
            os.makedirs(nested, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.init_workspace(nested)
            self.assertIn(ws, str(cm.exception))
            self.assertFalse(
                os.path.exists(os.path.join(nested, sc.CONFIG_FILENAME)))

    def test_refuses_when_target_is_itself_a_workspace(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = _write_ws_config(os.path.realpath(tmp), {})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.init_workspace(ws)
            self.assertIn(ws, str(cm.exception))

    def test_missing_target_directory_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            missing = os.path.join(os.path.realpath(tmp), "nope")
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError):
                    sc.init_workspace(missing)
            self.assertFalse(os.path.exists(missing))

    def test_nested_declares_workspace_beneath_an_enclosing_one(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = _write_ws_config(os.path.realpath(tmp), {})
            inner = os.path.join(outer, "nested")
            os.makedirs(inner, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                created, enclosing = sc.init_workspace(inner, nested=True)
            self.assertEqual(created, inner)
            self.assertEqual(enclosing, outer)
            cfg = os.path.join(inner, sc.CONFIG_FILENAME)
            self.assertTrue(os.path.isfile(cfg))
            with open(cfg, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["workspace"], {})

    def test_nested_still_refuses_a_self_declaring_target(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = _write_ws_config(os.path.realpath(tmp), {})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.init_workspace(ws, nested=True)
            self.assertIn(ws, str(cm.exception))

    def test_bare_call_still_refuses_under_an_enclosing_workspace(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = _write_ws_config(os.path.realpath(tmp), {})
            nested = os.path.join(ws, "sub")
            os.makedirs(nested, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.init_workspace(nested, nested=False)
            self.assertIn(ws, str(cm.exception))
            self.assertFalse(
                os.path.exists(os.path.join(nested, sc.CONFIG_FILENAME)))


class ValidateWorkspaceTest(unittest.TestCase):
    """validate_workspace shape checks (shipd-workspace
    project-registry-semantics). Validation is shape-only: a listed repo path
    absent on disk is never an error; an exact duplicate path across projects
    is an ambiguous-ownership error."""

    def test_conforming_registry_validates_clean(self):
        # Neither path exists on disk — shape-only validation ignores that.
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": ["shipd", "apps/backend"]}}})
        self.assertEqual(errors, [])

    def test_no_projects_key_is_clean(self):
        self.assertEqual(sc.validate_workspace({}), [])

    def test_non_object_projects_errors(self):
        errors = sc.validate_workspace({"projects": []})
        self.assertTrue(errors)

    def test_non_kebab_slug_errors(self):
        errors = sc.validate_workspace(
            {"projects": {"Alpha_1": {"repos": ["shipd"]}}})
        self.assertTrue(any("Alpha_1" in e for e in errors))

    def test_non_list_repos_errors(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": "shipd"}}})
        self.assertTrue(any("alpha" in e for e in errors))

    def test_empty_string_repo_entry_errors(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": ["shipd", ""]}}})
        self.assertTrue(errors)

    def test_duplicate_path_across_projects_errors_naming_path(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": ["shared-lib"]},
                          "beta": {"repos": ["shared-lib"]}}})
        self.assertTrue(any("shared-lib" in e for e in errors))

    def test_mixed_string_and_object_entries_validate_clean(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": [
                "shipd",
                {"path": "apps/backend",
                 "url": "git@example.com:backend.git",
                 "branch": "main"}]}}})
        self.assertEqual(errors, [])

    def test_object_entry_without_path_errors_naming_project(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": [
                {"url": "git@example.com:x.git"}]}}})
        self.assertTrue(any("alpha" in e for e in errors))

    def test_object_entry_empty_path_errors_naming_project(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": [{"path": ""}]}}})
        self.assertTrue(any("alpha" in e for e in errors))

    def test_object_entry_non_string_path_errors_naming_project(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": [{"path": 3}]}}})
        self.assertTrue(any("alpha" in e for e in errors))

    def test_object_entry_empty_url_errors_naming_project(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": [
                {"path": "apps/backend", "url": ""}]}}})
        self.assertTrue(any("alpha" in e for e in errors))

    def test_object_entry_non_string_branch_errors_naming_project(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": [
                {"path": "apps/backend", "branch": 7}]}}})
        self.assertTrue(any("alpha" in e for e in errors))

    def test_duplicate_path_across_shapes_errors_naming_path(self):
        errors = sc.validate_workspace(
            {"projects": {"alpha": {"repos": ["shared-lib"]},
                          "beta": {"repos": [{"path": "shared-lib"}]}}})
        self.assertTrue(any("shared-lib" in e for e in errors))

    def test_declared_focus_validates_clean(self):
        errors = sc.validate_workspace(
            {"focus": "documents",
             "projects": {"documents": {"repos": ["shipd"]}}})
        self.assertEqual(errors, [])

    def test_unknown_focus_errors_naming_slugs(self):
        errors = sc.validate_workspace(
            {"focus": "missing",
             "projects": {"alpha": {"repos": ["shipd"]}}})
        self.assertTrue(errors)
        self.assertTrue(any("alpha" in e for e in errors))

    def test_non_kebab_focus_errors(self):
        errors = sc.validate_workspace(
            {"focus": "Not_Kebab",
             "projects": {"alpha": {"repos": ["shipd"]}}})
        self.assertTrue(errors)


class RepoEntryPathTest(unittest.TestCase):
    """repo_entry_path reads the path from either the string or object entry
    shape, returning None for malformed entries (shipd-workspace
    project-registry-semantics)."""

    def test_string_entry_returns_path(self):
        self.assertEqual(sc.repo_entry_path("shipd"), "shipd")

    def test_object_entry_returns_path(self):
        self.assertEqual(
            sc.repo_entry_path({"path": "apps/backend", "url": "x"}),
            "apps/backend")

    def test_empty_string_entry_is_none(self):
        self.assertIsNone(sc.repo_entry_path(""))

    def test_object_without_path_is_none(self):
        self.assertIsNone(sc.repo_entry_path({"url": "x"}))

    def test_object_non_string_path_is_none(self):
        self.assertIsNone(sc.repo_entry_path({"path": 3}))

    def test_non_string_non_dict_entry_is_none(self):
        self.assertIsNone(sc.repo_entry_path(5))


class ProjectOfTest(unittest.TestCase):
    """project_of containment resolution (shipd-workspace project-resolution):
    the longest (most specific) matching entry wins across projects; an
    unmatched path resolves to None (the anonymous implicit default)."""

    def _marker(self, root, registry):
        """Declare ``registry`` as the workspace object in ``.shipd-config.json``."""
        return _write_ws_config(root, registry)

    def test_most_specific_entry_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._marker(ws, {"projects": {
                "alpha": {"repos": ["apps"]},
                "beta": {"repos": ["apps/backend"]}}})
            self.assertEqual(
                sc.project_of(ws, "apps/backend/repo-x"), "beta")

    def test_exact_entry_match_returns_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._marker(ws, {"projects": {
                "alpha": {"repos": ["shipd", "apps/backend"]}}})
            self.assertEqual(sc.project_of(ws, "shipd"), "alpha")

    def test_unmatched_path_is_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._marker(ws, {"projects": {
                "alpha": {"repos": ["apps/backend"]}}})
            self.assertIsNone(sc.project_of(ws, "services/other"))

    def test_object_entry_containment_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._marker(ws, {"projects": {
                "alpha": {"repos": [
                    {"path": "apps/backend",
                     "url": "git@example.com:backend.git"}]}}})
            self.assertEqual(
                sc.project_of(ws, "apps/backend/repo-x"), "alpha")

    def test_most_specific_wins_across_string_and_object_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._marker(ws, {"projects": {
                "alpha": {"repos": ["apps"]},
                "beta": {"repos": [{"path": "apps/backend"}]}}})
            self.assertEqual(
                sc.project_of(ws, "apps/backend/repo-x"), "beta")


class WorkspaceUniverseSeamTest(unittest.TestCase):
    """workspace_project_roots / aggregation_universes: the single shared
    universe-discovery seam every board-shaped read surface consumes
    (shipd-workspace workspace-universe-discovery). ``$HOME`` is overridden so
    the real home config never masquerades as an ancestor workspace."""

    def _workspace(self, tmp, projects, repo_dirs=()):
        """Declare ``projects`` as the registry of a workspace root at ``tmp``
        and create ``repo_dirs`` (workspace-root-relative) on disk."""
        ws = os.path.realpath(tmp)
        _write_ws_config(ws, {"projects": projects})
        for name in repo_dirs:
            os.makedirs(os.path.join(ws, name), exist_ok=True)
        return ws

    def test_workspace_level_yields_declared_repos_in_slug_order(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "zeta": {"repos": ["repos/zeta"]},
                "alpha": {"repos": ["repos/alpha"]},
            }, ("repos/zeta", "repos/alpha"))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/alpha")),
                     ("zeta", os.path.join(ws, "repos/zeta"))])

    def test_repos_of_one_project_keep_declaration_order(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/web", {"path": "repos/api"}]},
            }, ("repos/web", "repos/api"))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/web")),
                     ("alpha", os.path.join(ws, "repos/api"))])

    def test_aggregation_universes_lists_the_invocation_root_first(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/alpha"]},
            }, ("repos/alpha",))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.aggregation_universes(ws),
                    [(None, ws), ("alpha", os.path.join(ws, "repos/alpha"))])

    def test_inside_a_member_repo_the_seam_yields_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/alpha"]},
                "beta": {"repos": ["repos/beta"]},
            }, ("repos/alpha", "repos/beta"))
            repo = os.path.join(ws, "repos/alpha")
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_project_roots(repo), [])
                self.assertEqual(sc.aggregation_universes(repo), [(None, repo)])

    def test_absent_repo_directory_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/alpha"]},
                "gone": {"repos": ["repos/gone"]},
            }, ("repos/alpha",))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/alpha"))])

    def test_duplicate_real_path_via_symlink_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/alpha"]},
                "beta": {"repos": ["repos/alpha-link"]},
            }, ("repos/alpha",))
            os.symlink(os.path.join(ws, "repos/alpha"),
                       os.path.join(ws, "repos/alpha-link"))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/alpha"))])

    def test_entry_resolving_to_the_invocation_root_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/alpha"]},
                "self": {"repos": [{"path": "."}]},
            }, ("repos/alpha",))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/alpha"))])

    def test_non_object_project_entry_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": ["repos/alpha"]},
                "broken": "not-an-object",
            }, ("repos/alpha",))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/alpha"))])

    def test_malformed_repo_entry_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = self._workspace(tmp, {
                "alpha": {"repos": [5, {"url": "x"}, "repos/alpha"]},
                "listless": {"repos": "repos/alpha"},
            }, ("repos/alpha",))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.workspace_project_roots(ws),
                    [("alpha", os.path.join(ws, "repos/alpha"))])

    def test_unparseable_registry_yields_the_single_universe(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            _write_raw_config(ws, "{ not json")
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_project_roots(ws), [])
                self.assertEqual(sc.aggregation_universes(ws), [(None, ws)])

    def test_no_workspace_discoverable_yields_the_single_universe(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.join(os.path.realpath(tmp), "repo")
            os.makedirs(root, exist_ok=True)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.workspace_project_roots(root), [])
                self.assertEqual(sc.aggregation_universes(root), [(None, root)])


class LayeredConfigTest(unittest.TestCase):
    """load_layered_config / resolve_config / specs_dirname / specs_dir: the
    ``.shipd-config.json`` layered resolution (shipd-config config-file-discovery,
    layered-key-merge, content-dir-key). ``$HOME`` is always overridden to an
    empty directory so the real home config never leaks into a test."""

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            if isinstance(payload, str):
                fh.write(payload)
            else:
                json.dump(payload, fh)
        return d

    def test_chain_walk_to_fs_root(self):
        # Files at /ws and /ws/repo both participate; nearest (repo) is first.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            self._write_config(ws, {"dir": ".shipd"})
            self._write_config(repo, {"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                layers = sc.load_layered_config(repo)
            paths = [p for p, _d in layers]
            self.assertEqual(
                paths[0], os.path.join(repo, sc.CONFIG_FILENAME))
            self.assertIn(os.path.join(ws, sc.CONFIG_FILENAME), paths)

    def test_home_layer_appended_when_not_in_chain(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.realpath(tmp)
            home_dir = os.path.realpath(home)
            self._write_config(home_dir, {"valid_themes": ["reliability"]})
            with home_set_to(home_dir):
                layers = sc.load_layered_config(start)
                config, _prov = sc.resolve_config(start)
            paths = [p for p, _d in layers]
            self.assertIn(os.path.join(home_dir, sc.CONFIG_FILENAME), paths)
            self.assertEqual(config["valid_themes"], ["reliability"])

    def test_defaults_when_no_files(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.realpath(tmp)
            with home_set_to(os.path.realpath(home)):
                layers = sc.load_layered_config(start)
                config, _prov = sc.resolve_config(start)
            self.assertEqual(layers, [])
            self.assertEqual(sc.specs_dirname(config), ".shipd")

    def test_malformed_file_errors_naming_its_path(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.realpath(tmp)
            self._write_config(start, "{ not json")
            bad = os.path.join(start, sc.CONFIG_FILENAME)
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.load_layered_config(start)
            self.assertIn(bad, str(cm.exception))

    def test_non_object_top_level_errors_naming_its_path(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.realpath(tmp)
            self._write_config(start, "[1, 2, 3]")
            bad = os.path.join(start, sc.CONFIG_FILENAME)
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.load_layered_config(start)
            self.assertIn(bad, str(cm.exception))

    def test_nearest_wins_per_top_level_key(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            self._write_config(ws, {"dir": ".shipd"})
            self._write_config(repo, {"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                config, _prov = sc.resolve_config(repo)
            self.assertEqual(config["dir"], "specs")

    def test_distinct_keys_combine_across_layers(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            home_dir = os.path.realpath(home)
            self._write_config(repo, {"valid_themes": ["reliability"]})
            self._write_config(home_dir, {"build": {"log": False}})
            with home_set_to(home_dir):
                config, _prov = sc.resolve_config(repo)
            self.assertEqual(config["valid_themes"], ["reliability"])
            self.assertEqual(config["build"], {"log": False})

    def test_unknown_keys_preserved(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            start = os.path.realpath(tmp)
            self._write_config(start, {"future-key": {"x": 1}})
            with home_set_to(os.path.realpath(home)):
                config, _prov = sc.resolve_config(start)
            self.assertEqual(config["future-key"], {"x": 1})

    def test_dir_default_is_dot_am(self):
        self.assertEqual(sc.specs_dirname({}), ".shipd")

    def test_dir_override(self):
        self.assertEqual(sc.specs_dirname({"dir": "specs"}), "specs")

    def test_specs_dir_joins_root_and_dirname(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.specs_dir(root), os.path.join(root, "specs"))

    def test_separator_in_dir_errors_naming_value(self):
        with self.assertRaises(sc.ConfigError) as cm:
            sc.specs_dirname({"dir": "nested/specs"})
        self.assertIn("nested/specs", str(cm.exception))


class ExternalStoreRootTest(unittest.TestCase):
    """store_root_dir / repo_store_folder / specs_dir's external branch: the
    optional `store_root` key relocating a repo's content directory into an
    external store, with a worktree-stable per-repo folder name (shipd-config
    store-root-key, store-repo-folder-name). ``$HOME`` is always overridden so
    the real home config never leaks in."""

    def setUp(self):
        # The git probe is memoized per resolved root; a fresh tempdir per test
        # cannot collide, but clearing keeps the tests order-independent.
        getattr(sc, "_STORE_FOLDER_CACHE", {}).clear()

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)
        return d

    def test_workspace_declaration_governs_member_repo(self):
        # A workspace-level store_root, a member repo with no config of its
        # own: the member's content directory lands under the shared store.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "cai-backend")
            os.makedirs(repo)
            self._write_config(ws, {"store_root": "shipd-store"})
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.store_root_dir(repo), os.path.join(ws, "shipd-store"))
                self.assertEqual(
                    sc.specs_dir(repo),
                    os.path.join(ws, "shipd-store", "cai-backend"))

    def test_relative_value_resolves_against_declaring_file(self):
        # `artefacts` declared at /ws resolves to /ws/artefacts even when the
        # resolution starts three directories deeper.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "team", "repo")
            os.makedirs(repo)
            self._write_config(ws, {"store_root": "artefacts"})
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.store_root_dir(repo), os.path.join(ws, "artefacts"))
                self.assertEqual(
                    sc.specs_dir(repo),
                    os.path.join(ws, "artefacts", "repo"))

    def test_tilde_expands(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            home_dir = os.path.realpath(home)
            self._write_config(root, {"store_root": "~/stores/shipd"})
            with home_set_to(home_dir):
                self.assertEqual(
                    sc.store_root_dir(root),
                    os.path.join(home_dir, "stores", "shipd"))

    def test_absolute_value_used_as_is(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as store, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            store_root = os.path.realpath(store)
            self._write_config(root, {"store_root": store_root})
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.store_root_dir(root), store_root)
                self.assertEqual(
                    sc.specs_dir(root),
                    os.path.join(store_root, os.path.basename(root)))

    def test_empty_value_errors_naming_the_key(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"store_root": ""})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.store_root_dir(root)
            self.assertIn("store_root", str(cm.exception))

    def test_non_string_value_errors_naming_the_key(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"store_root": 7})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.store_root_dir(root)
            self.assertIn("store_root", str(cm.exception))

    def test_undeclared_key_keeps_in_repo_resolution(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(sc.store_root_dir(root))
                self.assertEqual(
                    sc.specs_dir(root), os.path.join(root, "specs"))

    def test_store_root_supersedes_dir(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(
                root, {"dir": "specs", "store_root": "store"})
            with home_set_to(os.path.realpath(home)):
                resolved = sc.specs_dir(root)
            self.assertEqual(
                resolved,
                os.path.join(root, "store", os.path.basename(root)))
            self.assertNotIn("specs", resolved.split(os.sep))

    def test_worktree_resolves_the_main_checkouts_folder(self):
        # A real repo plus a real linked worktree: both resolve one store
        # folder, named for the main checkout's directory.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "cai-backend")
            os.makedirs(repo)
            _git("init", "-q", repo)
            _git("-C", repo, "config", "user.email", "test@example.com")
            _git("-C", repo, "config", "user.name", "Test")
            with open(os.path.join(repo, "README.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("hi\n")
            _git("-C", repo, "add", "-A")
            _git("-C", repo, "commit", "-q", "-m", "init")
            wt = os.path.join(repo, ".worktrees", "some-change")
            _git("-C", repo, "worktree", "add", "-q", "-b", "some-change", wt)
            self._write_config(ws, {"store_root": "store"})
            expected = os.path.join(ws, "store", "cai-backend")
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.repo_store_folder(repo), "cai-backend")
                self.assertEqual(sc.repo_store_folder(wt), "cai-backend")
                self.assertEqual(sc.specs_dir(repo), expected)
                self.assertEqual(sc.specs_dir(wt), expected)

    def test_non_git_root_falls_back_to_its_basename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(os.path.realpath(tmp), "plain-dir")
            os.makedirs(root)
            self.assertEqual(sc.repo_store_folder(root), "plain-dir")

    def test_probe_is_cached_per_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(os.path.realpath(tmp), "plain-dir")
            os.makedirs(root)
            self.assertEqual(sc.repo_store_folder(root), "plain-dir")
            self.assertIn(os.path.realpath(root), sc._STORE_FOLDER_CACHE)
            sc._STORE_FOLDER_CACHE[os.path.realpath(root)] = "memoized"
            self.assertEqual(sc.repo_store_folder(root), "memoized")


class SchemaMarkerTest(unittest.TestCase):
    """SCHEMA_VERSION / read_schema_marker / stamp_schema_marker: the artifact
    grammar's declared semver and the one-line `schema` marker in the resolved
    content directory (schema-versioning schema-version-declaration,
    schema-marker-stamping). ``$HOME`` is always overridden so the real home
    config never leaks in."""

    def setUp(self):
        getattr(sc, "_STORE_FOLDER_CACHE", {}).clear()

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)
        return d

    def _write_marker(self, content_dir, value):
        os.makedirs(content_dir, exist_ok=True)
        path = os.path.join(content_dir, "schema")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(value)
        return path

    def _read_marker(self, content_dir):
        with open(os.path.join(content_dir, "schema"), encoding="utf-8") as fh:
            return fh.read()

    # --- the constant -----------------------------------------------------

    def test_schema_version_is_three_part_semver(self):
        parts = sc.SCHEMA_VERSION.split(".")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit(), sc.SCHEMA_VERSION)

    # --- reading ----------------------------------------------------------

    def test_absent_marker_reads_as_the_baseline(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            os.makedirs(os.path.join(root, ".shipd", "verified"))
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.read_schema_marker(root), "1.0.0")

    def test_marker_value_is_read_and_trimmed(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_marker(os.path.join(root, ".shipd"), "1.4.0\n")
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.read_schema_marker(root), "1.4.0")

    def test_marker_in_an_external_store_is_honored(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "cai-backend")
            os.makedirs(repo)
            self._write_config(ws, {"store_root": "shipd-store"})
            self._write_marker(
                os.path.join(ws, "shipd-store", "cai-backend"), "1.7.2\n")
            # The in-repo location must not be consulted at all.
            self._write_marker(os.path.join(repo, ".shipd"), "9.9.9\n")
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.read_schema_marker(repo), "1.7.2")

    def test_malformed_marker_errors_naming_the_file(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            path = self._write_marker(os.path.join(root, ".shipd"), "one.two\n")
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.read_schema_marker(root)
            self.assertIn(path, str(cm.exception))

    def test_two_part_marker_errors_naming_the_file(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            path = self._write_marker(os.path.join(root, ".shipd"), "1.2\n")
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.read_schema_marker(root)
            self.assertIn(path, str(cm.exception))

    # --- stamping ---------------------------------------------------------

    def test_stamp_writes_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            content = os.path.join(root, ".shipd")
            os.makedirs(content)
            with home_set_to(os.path.realpath(home)):
                sc.stamp_schema_marker(root)
                self.assertEqual(
                    self._read_marker(content), sc.SCHEMA_VERSION + "\n")
                self.assertEqual(sc.read_schema_marker(root), sc.SCHEMA_VERSION)

    def test_stamp_advances_a_same_major_older_marker(self):
        # At the grammar's floor (1.0.0) no same-major-older value exists, so
        # the advancement rule is exercised against a lifted engine version.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            content = os.path.join(root, ".shipd")
            major = sc.SCHEMA_VERSION.split(".")[0]
            self._write_marker(content, "%s.0.0\n" % major)
            lifted = "%s.4.0" % major
            with home_set_to(os.path.realpath(home)), \
                    schema_version_set_to(lifted):
                sc.stamp_schema_marker(root)
            self.assertEqual(self._read_marker(content), lifted + "\n")

    def test_stamp_leaves_a_cross_major_marker_untouched(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            content = os.path.join(root, ".shipd")
            future = "%d.0.0" % (int(sc.SCHEMA_VERSION.split(".")[0]) + 1,)
            self._write_marker(content, future + "\n")
            with home_set_to(os.path.realpath(home)):
                sc.stamp_schema_marker(root)
            self.assertEqual(self._read_marker(content), future + "\n")

    def test_stamp_leaves_a_same_major_newer_marker_untouched(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            content = os.path.join(root, ".shipd")
            major, minor, _patch = sc.SCHEMA_VERSION.split(".")
            ahead = "%s.%d.0" % (major, int(minor) + 1)
            self._write_marker(content, ahead + "\n")
            with home_set_to(os.path.realpath(home)):
                sc.stamp_schema_marker(root)
            self.assertEqual(self._read_marker(content), ahead + "\n")

    def test_stamp_creates_the_content_directory_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            with home_set_to(os.path.realpath(home)):
                sc.stamp_schema_marker(root)
            self.assertEqual(
                self._read_marker(os.path.join(root, ".shipd")),
                sc.SCHEMA_VERSION + "\n")

    def test_stamp_into_an_external_store_lands_beside_the_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "cai-backend")
            os.makedirs(repo)
            self._write_config(ws, {"store_root": "shipd-store"})
            with home_set_to(os.path.realpath(home)):
                sc.stamp_schema_marker(repo)
            self.assertEqual(
                self._read_marker(
                    os.path.join(ws, "shipd-store", "cai-backend")),
                sc.SCHEMA_VERSION + "\n")
            self.assertFalse(
                os.path.exists(os.path.join(repo, ".shipd", "schema")))

    # --- the compatibility gate ------------------------------------------

    def test_compat_is_silent_on_a_matching_marker(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_marker(
                os.path.join(root, ".shipd"), sc.SCHEMA_VERSION + "\n")
            stderr = io.StringIO()
            with home_set_to(os.path.realpath(home)), \
                    contextlib.redirect_stderr(stderr):
                sc.check_schema_compat(root)
            self.assertEqual(stderr.getvalue(), "")

    def test_compat_is_silent_with_no_marker(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            os.makedirs(os.path.join(root, ".shipd", "verified"))
            stderr = io.StringIO()
            with home_set_to(os.path.realpath(home)), \
                    contextlib.redirect_stderr(stderr):
                sc.check_schema_compat(root)
            self.assertEqual(stderr.getvalue(), "")

    def test_compat_warns_once_when_the_repo_minor_is_ahead(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            major, minor, _patch = sc.SCHEMA_VERSION.split(".")
            ahead = "%s.%d.0" % (major, int(minor) + 1)
            self._write_marker(os.path.join(root, ".shipd"), ahead + "\n")
            stderr = io.StringIO()
            with home_set_to(os.path.realpath(home)), \
                    contextlib.redirect_stderr(stderr):
                sc.check_schema_compat(root)
            out = stderr.getvalue()
            self.assertEqual(len(out.strip().splitlines()), 1)
            self.assertIn(ahead, out)
            self.assertIn(sc.SCHEMA_VERSION, out)

    def test_compat_raises_on_a_major_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            future = "%d.0.0" % (int(sc.SCHEMA_VERSION.split(".")[0]) + 1,)
            self._write_marker(os.path.join(root, ".shipd"), future + "\n")
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.check_schema_compat(root)
            message = str(cm.exception)
            self.assertIn(future, message)
            self.assertIn(sc.SCHEMA_VERSION, message)
            self.assertIn("upgrade", message)


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


class SchemaCompatCliTest(unittest.TestCase):
    """The compatibility gate at the engine's entry points, driven as
    subprocesses against a throwaway repo root (schema-versioning
    schema-compat-gate, schema-marker-stamping). ``$HOME`` and the flow log dir
    are isolated so no test reads or writes the real ones."""

    STATUS = os.path.join(SCRIPTS, "spec_status.py")
    EMIT = os.path.join(SCRIPTS, "spec_emit.py")
    MERGE = os.path.join(SCRIPTS, "spec_merge.py")
    LINT = os.path.join(SCRIPTS, "spec_lint.py")
    GATE = os.path.join(SCRIPTS, "spec_gate.py")

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="schema-gate-root-")
        self.stage = tempfile.mkdtemp(prefix="schema-gate-stage-")
        self.home = tempfile.mkdtemp(prefix="schema-gate-home-")
        self.flow_dir = tempfile.mkdtemp(prefix="schema-gate-flow-")

    def tearDown(self):
        for d in (self.root, self.stage, self.home, self.flow_dir):
            shutil.rmtree(d, ignore_errors=True)

    # -- fixtures ----------------------------------------------------------

    def content_dir(self):
        return os.path.join(self.root, ".shipd")

    def make_layout(self):
        for name in ("verified", "planned", "completed", "research"):
            os.makedirs(os.path.join(self.content_dir(), name), exist_ok=True)

    def write_marker(self, value):
        os.makedirs(self.content_dir(), exist_ok=True)
        path = os.path.join(self.content_dir(), "schema")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(value + "\n")
        return path

    def marker(self):
        path = os.path.join(self.content_dir(), "schema")
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def future_major(self):
        return "%d.0.0" % (int(sc.SCHEMA_VERSION.split(".")[0]) + 1,)

    def newer_minor(self):
        major, minor, _patch = sc.SCHEMA_VERSION.split(".")
        return "%s.%d.0" % (major, int(minor) + 1)

    def stage_change(self):
        with open(os.path.join(self.stage, "plan.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(CLEAN_PLAN)
        cap = os.path.join(self.stage, "specs", "auth")
        os.makedirs(cap, exist_ok=True)
        with open(os.path.join(cap, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(CLEAN_DELTA)
        with open(os.path.join(self.stage, "tasks.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(CLEAN_TASKS)

    def install_change(self, name="my-change"):
        """Install a clean planned change through the emit CLI, from a repo
        state the gate lets through."""
        self.stage_change()
        r = self.cli(self.EMIT, "change", name, "--from", self.stage)
        self.assertEqual(r.returncode, 0, r.stderr)
        return os.path.join(self.content_dir(), "planned", name)

    def cli(self, script, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        env["AM_FLOW_LOG_DIR"] = self.flow_dir
        return subprocess.run(
            ["python3", script, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def assertRefused(self, result, repo_version):
        self.assertNotEqual(result.returncode, 0,
                            "expected a refusal, got:\n%s" % result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(repo_version, combined)
        self.assertIn(sc.SCHEMA_VERSION, combined)

    # -- major mismatch refuses at every entry point -----------------------

    def test_status_read_verb_refuses_on_a_major_mismatch(self):
        self.make_layout()
        self.install_change()
        future = self.future_major()
        self.write_marker(future)
        self.assertRefused(self.cli(self.STATUS, "status", "my-change"), future)

    def test_emit_refuses_on_a_major_mismatch_and_installs_nothing(self):
        self.make_layout()
        future = self.future_major()
        self.write_marker(future)
        self.stage_change()
        r = self.cli(self.EMIT, "change", "my-change", "--from", self.stage)
        self.assertRefused(r, future)
        self.assertFalse(os.path.exists(
            os.path.join(self.content_dir(), "planned", "my-change")))

    def test_merge_refuses_on_a_major_mismatch_and_touches_nothing(self):
        self.make_layout()
        self.install_change()
        future = self.future_major()
        self.write_marker(future)
        r = self.cli(self.MERGE, "my-change")
        self.assertRefused(r, future)
        # Neither merged into the master library nor archived away.
        self.assertEqual(
            os.listdir(os.path.join(self.content_dir(), "verified")), [])
        self.assertTrue(os.path.isdir(
            os.path.join(self.content_dir(), "planned", "my-change")))

    def test_lint_refuses_on_a_major_mismatch(self):
        self.make_layout()
        future = self.future_major()
        self.write_marker(future)
        self.assertRefused(self.cli(self.LINT), future)

    def test_gate_refuses_on_a_major_mismatch(self):
        self.make_layout()
        self.install_change()
        future = self.future_major()
        self.write_marker(future)
        self.assertRefused(self.cli(self.GATE, "my-change"), future)

    # -- newer minor warns, matching version is silent ---------------------

    def test_newer_minor_warns_once_and_proceeds(self):
        self.make_layout()
        self.install_change()
        ahead = self.newer_minor()
        self.write_marker(ahead)
        r = self.cli(self.STATUS, "status", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "draft")
        warnings = [line for line in r.stderr.splitlines() if line.strip()]
        self.assertEqual(len(warnings), 1, r.stderr)
        self.assertIn(ahead, warnings[0])
        self.assertIn(sc.SCHEMA_VERSION, warnings[0])

    def test_matching_marker_is_silent(self):
        self.make_layout()
        self.install_change()
        self.write_marker(sc.SCHEMA_VERSION)
        r = self.cli(self.STATUS, "status", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")

    def test_unmarked_repo_is_silent(self):
        self.make_layout()
        self.install_change()
        os.remove(os.path.join(self.content_dir(), "schema"))
        r = self.cli(self.STATUS, "status", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")

    # -- init: exempt from the gate, and the stamping path -----------------

    def test_init_stamps_a_fresh_repo(self):
        r = self.cli(self.STATUS, "init")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.marker(), sc.SCHEMA_VERSION + "\n")

    def test_init_is_exempt_from_the_gate(self):
        self.make_layout()
        future = self.future_major()
        self.write_marker(future)
        r = self.cli(self.STATUS, "init")
        self.assertEqual(r.returncode, 0, r.stderr)
        # Exempt, and a cross-major marker is never rewritten.
        self.assertEqual(self.marker(), future + "\n")

    # -- stamping on emit and merge ---------------------------------------

    def test_emit_stamps_the_marker(self):
        self.make_layout()
        self.assertIsNone(self.marker())
        self.install_change()
        self.assertEqual(self.marker(), sc.SCHEMA_VERSION + "\n")

    def test_merge_stamps_the_marker(self):
        self.make_layout()
        self.install_change()
        os.remove(os.path.join(self.content_dir(), "schema"))
        r = self.cli(self.MERGE, "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.marker(), sc.SCHEMA_VERSION + "\n")


class ResolvePipelineTest(unittest.TestCase):
    """resolve_pipeline's stdlib-only surface: the autonomous-pipeline stage
    registry, the no-key default, and resolution with no third-party package
    installed at all (shipd-config autonomous-pipeline-key,
    pipeline-stage-registry, pipeline-entry-validation). The full closed-grammar
    entry validation lives in ``tests/test_resolve_pipeline.py``. ``$HOME`` is
    always overridden to an empty directory so the real home config never
    leaks into a test."""

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)
        return d

    # --- the registry -----------------------------------------------------

    def test_registry_is_canonical_ordered_names(self):
        self.assertEqual(
            sc.PIPELINE_STAGES,
            ("research", "epic", "plan", "gate", "build", "review"))

    def test_absent_key_yields_full_default(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            with home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(os.path.realpath(tmp))
            self.assertEqual(
                [e["stage"] for e in entries], list(sc.PIPELINE_STAGES))
            # Default entries are plain built-ins: no skips, no bindings.
            for e in entries:
                self.assertEqual(set(e.keys()), {"stage"})
            self.assertEqual(prov, "default")

    # --- the preset names and the string form -----------------------------

    def test_preset_names_are_the_stdlib_constant(self):
        self.assertEqual(sc.PIPELINE_PRESETS, ("default", "eco", "basic"))

    def test_default_preset_resolves_with_no_third_party_package(self):
        # `"default"` is the absent key's pipeline with preset provenance, and
        # it never touches the schema module.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"autonomous-pipeline": "default"})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(root)
            self.assertEqual(
                [e["stage"] for e in entries], list(sc.PIPELINE_STAGES))
            for e in entries:
                self.assertEqual(set(e.keys()), {"stage"})
            self.assertEqual(
                prov,
                "preset:default (%s)"
                % os.path.join(root, sc.CONFIG_FILENAME))

    def test_unknown_preset_lists_known_names(self):
        # The name check precedes the import, so an unknown name reports the
        # roster without ever importing the schema module.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"autonomous-pipeline": "ecoo"})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.resolve_pipeline(root)
            msg = str(cm.exception)
            self.assertIn("ecoo", msg)
            self.assertIn(os.path.join(root, sc.CONFIG_FILENAME), msg)
            for name in ("basic", "default", "eco"):
                self.assertIn(name, msg)

    def test_non_default_preset_resolves_with_no_third_party_package(self):
        # Validation is stdlib-only, so a non-default preset expands and
        # resolves in full with every third-party distribution unimportable
        # (shipd-config pipeline-presets).
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"autonomous-pipeline": "eco"})
            with imports_blocked("pydantic"), \
                    home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(root)
            self.assertTrue(prov.startswith("preset:eco"))
            self.assertEqual(
                [e.get("stage") for e in entries], list(sc.PIPELINE_STAGES))

    def test_non_list_non_string_value_names_both_forms(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"autonomous-pipeline": 7})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.resolve_pipeline(root)
            msg = str(cm.exception)
            self.assertIn(sc.PIPELINE_KEY, msg)
            self.assertIn("list", msg)
            self.assertIn("preset name string", msg)

    # --- resolution needs no third-party package --------------------------

    def test_absent_key_resolves_with_no_third_party_package(self):
        # The default pipeline never touches the schema module, so it resolves
        # with the schema module itself unimportable.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(os.path.realpath(tmp))
            self.assertEqual(
                [e["stage"] for e in entries], list(sc.PIPELINE_STAGES))
            self.assertEqual(prov, "default")

    def test_declared_pipeline_resolves_with_no_third_party_package(self):
        # The validator is stdlib-only, so a declared list resolves in full
        # with every third-party distribution unimportable, and no error
        # names a package or an install hint (shipd-config
        # pipeline-entry-validation).
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(
                root, {"autonomous-pipeline": [{"stage": "plan"}]})
            with imports_blocked("pydantic"), \
                    home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(root)
            self.assertEqual(entries, [{"stage": "plan"}])
            self.assertEqual(prov, os.path.join(root, sc.CONFIG_FILENAME))


class ResolvePrModeTest(unittest.TestCase):
    """resolve_pr_mode: the layered `pr-mode` key governing change-shipping PR
    flows (shipd-config pr-mode-key). Stdlib-only — no third-party package on
    any path. ``$HOME`` is always overridden to an empty directory so the real
    home config never leaks into a test."""

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)
        return d

    def test_key_constant(self):
        self.assertEqual(sc.PR_MODE_KEY, "pr-mode")

    def test_absent_key_defaults_to_auto(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.resolve_pr_mode(os.path.realpath(tmp)), "auto")

    def test_workspace_layer_governs_a_member_repo(self):
        # A workspace root declaring the key governs every repo beneath it, and
        # provenance names the workspace layer (what `config-show` prints).
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            self._write_config(ws, {"workspace": {}, "pr-mode": "draft"})
            os.makedirs(repo, exist_ok=True)
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.resolve_pr_mode(repo), "draft")
                _config, prov = sc.resolve_config(repo)
            self.assertEqual(
                prov[sc.PR_MODE_KEY], os.path.join(ws, sc.CONFIG_FILENAME))

    def test_nearest_layer_wins(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            self._write_config(ws, {"pr-mode": "draft"})
            self._write_config(repo, {"pr-mode": "auto"})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                self.assertEqual(sc.resolve_pr_mode(repo), "auto")

    def test_invalid_value_errors_naming_key_and_values(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"pr-mode": "always"})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.resolve_pr_mode(root)
            msg = str(cm.exception)
            self.assertIn(sc.PR_MODE_KEY, msg)
            self.assertIn("always", msg)
            self.assertIn("auto", msg)
            self.assertIn("draft", msg)
            self.assertIn(os.path.join(root, sc.CONFIG_FILENAME), msg)

    def test_declared_null_errors_rather_than_defaulting(self):
        # Declaredness is key presence, never the value: an explicit JSON null
        # is a bad value, not an absent key, so it fails like any other.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"pr-mode": None})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.resolve_pr_mode(root)
            msg = str(cm.exception)
            self.assertIn(sc.PR_MODE_KEY, msg)
            self.assertIn("None", msg)
            self.assertIn("auto", msg)
            self.assertIn("draft", msg)
            self.assertIn(os.path.join(root, sc.CONFIG_FILENAME), msg)

    def test_non_string_value_errors_naming_key(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            self._write_config(root, {"pr-mode": ["draft"]})
            with imports_blocked("pipeline_schema"), \
                    home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.resolve_pr_mode(root)
            self.assertIn(sc.PR_MODE_KEY, str(cm.exception))


class ResolveModelTierTest(unittest.TestCase):
    """The stdlib model-tier authority the pipeline's consumers resolve a
    `model`/`subagent_model` option through (epic-autopilot
    stage-model-resolution). Pure: no config, no filesystem, no import."""

    def test_ladder_is_strongest_first(self):
        self.assertEqual(sc.MODEL_LADDER,
                         ("fable", "opus", "sonnet", "haiku"))

    def test_session_without_anchor_inherits_the_cli_default(self):
        # None means "pass no --model" — the CLI's own default decides.
        self.assertIsNone(sc.resolve_model_tier("session"))

    def test_below_tiers_step_down_from_the_ladder_top_by_default(self):
        self.assertEqual(sc.resolve_model_tier("tier-below"), "opus")
        self.assertEqual(sc.resolve_model_tier("tier-two-below"), "sonnet")

    def test_anchored_stepping_clamps_at_the_ladder_bottom(self):
        self.assertEqual(
            sc.resolve_model_tier("tier-below", session_model="sonnet"),
            "haiku")
        self.assertEqual(
            sc.resolve_model_tier("tier-two-below", session_model="sonnet"),
            "haiku")

    def test_anchored_stepping_from_a_mid_ladder_anchor(self):
        self.assertEqual(
            sc.resolve_model_tier("tier-below", session_model="opus"),
            "sonnet")
        self.assertEqual(
            sc.resolve_model_tier("tier-two-below", session_model="opus"),
            "haiku")

    def test_session_returns_the_anchor(self):
        self.assertEqual(
            sc.resolve_model_tier("session", session_model="sonnet"),
            "sonnet")

    def test_concrete_ids_pass_through_verbatim(self):
        self.assertEqual(sc.resolve_model_tier("claude-fable-5"),
                         "claude-fable-5")
        self.assertEqual(
            sc.resolve_model_tier("claude-fable-5", session_model="sonnet"),
            "claude-fable-5")

    def test_non_ladder_anchor_steps_from_the_ladder_top(self):
        # An anchor that is not a ladder alias cannot be positioned on the
        # ladder, so stepping falls back to the top — fail expensive.
        self.assertEqual(
            sc.resolve_model_tier("tier-below",
                                  session_model="claude-fable-5"),
            "opus")
        self.assertEqual(
            sc.resolve_model_tier("tier-two-below",
                                  session_model="claude-fable-5"),
            "sonnet")


class WikiPathsTest(unittest.TestCase):
    """wiki_dir and the reserved-slug constant (shipd-wiki wiki-store-layout,
    wiki-page-grammar). ``$HOME`` is overridden so content-dir resolution never
    reads the real home config."""

    def test_wiki_dir_under_content_dir(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.wiki_dir(root),
                    os.path.join(sc.specs_dir(root), "wiki"))

    def test_wiki_dir_respects_content_dir_override(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_ws_config(root, {}, extra={"dir": "specs"})
            with home_set_to(os.path.realpath(home)):
                self.assertEqual(
                    sc.wiki_dir(root), os.path.join(root, "specs", "wiki"))

    def test_reserved_slugs_cover_the_five(self):
        self.assertEqual(
            set(sc.WIKI_RESERVED_SLUGS),
            {"index", "log", "queue", "schema", "sources"})


class WikiBaseDirTest(unittest.TestCase):
    """wiki_base_dir resolves the optional ``wiki_base`` config key
    (shipd-config wiki-base-key). ``$HOME`` is overridden so ``~`` expansion is
    deterministic and content-dir resolution never reads the real home
    config."""

    def test_declared_tilde_path_resolves_expanded(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            home = os.path.realpath(home)
            _write_ws_config(root, {}, extra={"wiki_base": "~/projects/.shipd/wiki"})
            with home_set_to(home):
                self.assertEqual(
                    sc.wiki_base_dir(root),
                    os.path.join(home, "projects", ".shipd", "wiki"))

    def test_undeclared_key_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_ws_config(root, {})
            with home_set_to(os.path.realpath(home)):
                self.assertIsNone(sc.wiki_base_dir(root))

    def test_empty_string_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_ws_config(root, {}, extra={"wiki_base": ""})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.wiki_base_dir(root)
            self.assertIn("wiki_base", str(cm.exception))

    def test_non_string_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_ws_config(root, {}, extra={"wiki_base": 42})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.wiki_base_dir(root)
            self.assertIn("wiki_base", str(cm.exception))

    def test_relative_value_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            _write_ws_config(root, {}, extra={"wiki_base": "relative/wiki"})
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as cm:
                    sc.wiki_base_dir(root)
            self.assertIn("wiki_base", str(cm.exception))

    def test_self_referential_base_is_none(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            with home_set_to(os.path.realpath(home)):
                _write_ws_config(
                    root, {}, extra={"wiki_base": sc.wiki_dir(root)})
                self.assertIsNone(sc.wiki_base_dir(root))

    def test_base_equal_to_enclosing_chain_members_store_is_none(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            outer = os.path.realpath(tmp)
            _write_ws_config(outer, {})
            inner = os.path.join(outer, "nested")
            with home_set_to(os.path.realpath(home)):
                _write_ws_config(
                    inner, {}, extra={"wiki_base": sc.wiki_dir(outer)})
                self.assertIsNone(sc.wiki_base_dir(inner))


class WikiGrammarHelpersTest(unittest.TestCase):
    """Grammar parse helpers for the wiki store (shipd-wiki wiki-page-grammar,
    wiki-index-and-log, wiki-question-queue)."""

    def test_extract_wikilinks_skips_fenced_code(self):
        text = (
            "See [[alpha]] and [[beta]].\n"
            "```\n"
            "not a [[link]] in code\n"
            "```\n"
            "Also [[gamma]].\n")
        self.assertEqual(
            sc.extract_wikilinks(text), ["alpha", "beta", "gamma"])

    def test_parse_index_entries_ignores_non_matching_lines(self):
        text = (
            "# Index\n"
            "\n"
            "- [[alpha]] — The alpha page.\n"
            "- not an entry\n"
            "- [[beta]] — The beta page.\n"
            "random prose\n")
        self.assertEqual(
            sc.parse_index_entries(text),
            [("alpha", "The alpha page."), ("beta", "The beta page.")])

    def test_log_header_matches_dated_shape(self):
        self.assertTrue(sc.WIKI_LOG_HEADER_RE.match(
            "## [2026-07-30] wiki-init | seeded the store"))
        self.assertFalse(sc.WIKI_LOG_HEADER_RE.match(
            "## seeded the store"))
        self.assertFalse(sc.WIKI_LOG_HEADER_RE.match(
            "## [2026-07-30] no-subject-pipe"))

    def test_parse_queue_blocks_reads_five_fields(self):
        text = (
            "# Queue\n"
            "\n"
            "## q-stale-cache\n"
            "- Asked: 2026-07-30 teach-session\n"
            "- Question: Is the cache stale?\n"
            "- Options: yes | no\n"
            "- Recommendation: yes\n"
            "- Answer: pending\n"
            "\n"
            "## q-other-thing\n"
            "- Asked: 2026-07-30\n"
            "- Question: Q2?\n"
            "- Options: a | b\n"
            "- Recommendation: a\n"
            "- Answer: b\n")
        blocks = sc.parse_queue_blocks(text)
        self.assertEqual([qid for qid, _f in blocks],
                         ["q-stale-cache", "q-other-thing"])
        fields = dict(blocks)
        self.assertEqual(fields["q-stale-cache"]["Question"],
                         "Is the cache stale?")
        self.assertEqual(fields["q-stale-cache"]["Answer"], "pending")
        self.assertEqual(set(fields["q-stale-cache"]),
                         set(sc.WIKI_QUEUE_FIELDS))


def _git(*args):
    """Run a local git command, asserting success. Never touches the network —
    only init / remote-add / worktree on tempdir repos."""
    subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def _make_worktree_repo(path, url):
    """Create a work-tree git repo at ``path`` with ``origin`` set to ``url``
    (a fake path URL — no network, no commits needed for the probes)."""
    os.makedirs(path, exist_ok=True)
    _git("init", "-q", path)
    _git("-C", path, "remote", "add", "origin", url)
    return path


def _make_bare_repo(path, url):
    """Create a bare git repo at ``path`` with ``origin`` set to ``url``."""
    _git("init", "-q", "--bare", path)
    _git("-C", path, "remote", "add", "origin", url)
    return path


def _one(records, path):
    """Return the single member record whose ``path`` matches."""
    matches = [r for r in records
               if r.get("kind") == "member" and r.get("path") == path]
    assert len(matches) == 1, (path, records)
    return matches[0]


def _gitignore_record(records):
    matches = [r for r in records if r.get("kind") == "gitignore"]
    assert len(matches) == 1, records
    return matches[0]


class WorkspaceSyncPlanTest(unittest.TestCase):
    """plan_workspace_sync computes the per-member materialization plan from the
    manifest, resolved config, and local disk, using only local git probes
    (shipd-workspace sync-materialization-planning, shipd-config clone-sources-key)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sync-plan-test-")
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.ws = os.path.join(self.tmp, "ws")
        os.makedirs(self.ws)

    def _declare(self, registry, extra=None):
        _write_ws_config(self.ws, registry, extra=extra)

    def test_present_work_tree_member_is_none(self):
        url = "https://example.invalid/backend.git"
        _make_worktree_repo(os.path.join(self.ws, "backend"), url)
        self._declare({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": url}]}}})
        rec = _one(sc.plan_workspace_sync(self.ws, {}), "backend")
        self.assertEqual(rec["member"], "alpha")
        self.assertEqual(rec["state"], "present")
        self.assertEqual(rec["action"], "none")
        self.assertNotIn("drift", rec)

    def test_present_member_mismatched_origin_drifts(self):
        _make_worktree_repo(os.path.join(self.ws, "backend"),
                            "https://example.invalid/OTHER.git")
        manifest_url = "https://example.invalid/backend.git"
        self._declare({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": manifest_url}]}}})
        rec = _one(sc.plan_workspace_sync(self.ws, {}), "backend")
        self.assertEqual(rec["state"], "present")
        self.assertEqual(rec["action"], "none")
        self.assertIn("drift", rec)
        self.assertIn("https://example.invalid/OTHER.git", rec["drift"])
        self.assertIn(manifest_url, rec["drift"])

    def test_present_non_git_directory_is_occupied(self):
        occupied = os.path.join(self.ws, "backend")
        os.makedirs(occupied)
        with open(os.path.join(occupied, "README"), "w") as fh:
            fh.write("not a repo\n")
        self._declare({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": "https://example.invalid/backend.git"}]}}})
        rec = _one(sc.plan_workspace_sync(self.ws, {}), "backend")
        self.assertEqual(rec["state"], "occupied")
        self.assertEqual(rec["action"], "none")
        self.assertIn("drift", rec)

    def test_absent_member_with_worktree_candidate_is_worktree(self):
        url = "https://example.invalid/backend.git"
        src = _make_worktree_repo(os.path.join(self.tmp, "src", "backend"), url)
        self._declare(
            {"projects": {"alpha": {"repos": [
                {"path": "backend", "url": url}]}}},
            extra={"clone_sources": [os.path.join(self.tmp, "src")]})
        config, _ = sc.resolve_config(self.ws)
        rec = _one(sc.plan_workspace_sync(self.ws, config), "backend")
        self.assertEqual(rec["state"], "absent")
        self.assertEqual(rec["action"], "worktree")
        self.assertEqual(rec["source"], src)
        self.assertIn("command", rec)
        self.assertIn("worktree add", rec["command"])
        self.assertIn(src, rec["command"])

    def test_absent_member_with_bare_candidate_is_reference_clone(self):
        url = "https://example.invalid/backend.git"
        src = _make_bare_repo(os.path.join(self.tmp, "src", "backend.git"), url)
        self._declare(
            {"projects": {"alpha": {"repos": [
                {"path": "backend", "url": url}]}}},
            extra={"clone_sources": [os.path.join(self.tmp, "src")]})
        config, _ = sc.resolve_config(self.ws)
        rec = _one(sc.plan_workspace_sync(self.ws, config), "backend")
        self.assertEqual(rec["action"], "reference-clone")
        self.assertEqual(rec["source"], src)
        self.assertIn("--reference", rec["command"])

    def test_absent_member_with_url_and_no_candidate_is_clone(self):
        url = "https://example.invalid/backend.git"
        self._declare(
            {"projects": {"alpha": {"repos": [
                {"path": "backend", "url": url}]}}},
            extra={"clone_sources": [os.path.join(self.tmp, "empty")]})
        os.makedirs(os.path.join(self.tmp, "empty"))
        config, _ = sc.resolve_config(self.ws)
        rec = _one(sc.plan_workspace_sync(self.ws, config), "backend")
        self.assertEqual(rec["action"], "clone")
        self.assertEqual(rec["url"], url)
        self.assertIn("clone", rec["command"])

    def test_path_only_absent_member_is_unmaterializable(self):
        self._declare({"projects": {"alpha": {"repos": ["backend"]}}})
        rec = _one(sc.plan_workspace_sync(self.ws, {}), "backend")
        self.assertEqual(rec["action"], "unmaterializable")
        self.assertIn("reason", rec)

    def test_undeclared_clone_sources_means_no_probing(self):
        # A matching candidate exists on disk, but with no clone_sources
        # declared the planner never probes — the member falls to clone.
        url = "https://example.invalid/backend.git"
        _make_worktree_repo(os.path.join(self.tmp, "src", "backend"), url)
        self._declare({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": url}]}}})
        rec = _one(sc.plan_workspace_sync(self.ws, {}), "backend")
        self.assertEqual(rec["action"], "clone")

    def test_first_match_wins_across_two_source_dirs(self):
        url = "https://example.invalid/backend.git"
        first = _make_worktree_repo(
            os.path.join(self.tmp, "src1", "backend"), url)
        _make_worktree_repo(os.path.join(self.tmp, "src2", "backend"), url)
        self._declare(
            {"projects": {"alpha": {"repos": [
                {"path": "backend", "url": url}]}}},
            extra={"clone_sources": [os.path.join(self.tmp, "src1"),
                                     os.path.join(self.tmp, "src2")]})
        config, _ = sc.resolve_config(self.ws)
        rec = _one(sc.plan_workspace_sync(self.ws, config), "backend")
        self.assertEqual(rec["source"], first)

    def test_gitignore_record_reports_missing_and_stale(self):
        self._declare({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": "https://example.invalid/backend.git"}]}}})
        # The marked block lists a stale extra line and omits the member path.
        with open(os.path.join(self.ws, ".gitignore"), "w") as fh:
            fh.write("keep-me\n%s\nstale-extra\n%s\n" % (
                sc.GITIGNORE_MEMBERS_BEGIN, sc.GITIGNORE_MEMBERS_END))
        gi = _gitignore_record(sc.plan_workspace_sync(self.ws, {}))
        self.assertIn("backend", gi["missing"])
        self.assertIn("stale-extra", gi["stale"])


class CloneSourcesConfigTest(unittest.TestCase):
    """resolve_clone_sources reads the optional clone_sources config key: a
    list of non-empty directory strings (``~`` expanded); undeclared → empty;
    malformed → ConfigError naming the key (shipd-config clone-sources-key)."""

    def test_undeclared_is_empty(self):
        self.assertEqual(sc.resolve_clone_sources({}), [])

    def test_declared_list_expands_home(self):
        with home_set_to("/home/tester"):
            resolved = sc.resolve_clone_sources({"clone_sources": ["~/src"]})
        self.assertEqual(resolved, ["/home/tester/src"])

    def test_string_value_errors_naming_key(self):
        with self.assertRaises(sc.ConfigError) as cm:
            sc.resolve_clone_sources({"clone_sources": "/src"})
        self.assertIn("clone_sources", str(cm.exception))

    def test_empty_string_entry_errors(self):
        with self.assertRaises(sc.ConfigError) as cm:
            sc.resolve_clone_sources({"clone_sources": ["/src", ""]})
        self.assertIn("clone_sources", str(cm.exception))


@contextlib.contextmanager
def _no_git_identity():
    """Run the block with any git identity blocked so a ``git commit`` fails with
    an unknown-identity error: ``$HOME`` pointed at an empty tempdir (no
    ``~/.gitconfig``), ``GIT_CONFIG_NOSYSTEM=1`` (no ``/etc/gitconfig``), the
    author/committer env identities cleared, and a global config that sets
    ``user.useConfigOnly=true`` so git refuses to auto-detect a name/email from
    the OS username and hostname."""
    keys = ["HOME", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL",
            "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
            "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"]
    saved = {k: os.environ.get(k) for k in keys}
    with tempfile.TemporaryDirectory() as empty_home:
        global_cfg = os.path.join(empty_home, "gitconfig")
        with open(global_cfg, "w", encoding="utf-8") as fh:
            fh.write("[user]\n\tuseConfigOnly = true\n")
        os.environ["HOME"] = empty_home
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
        os.environ["GIT_CONFIG_GLOBAL"] = global_cfg
        for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                  "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
            os.environ.pop(k, None)
        try:
            yield
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class WikiAutocommitTest(unittest.TestCase):
    """wiki_autocommit makes a local, path-scoped commit for a successful wiki
    write when the store sits inside a git work tree, and is a quiet no-op
    otherwise (shipd-wiki wiki-autocommit)."""

    def _init_repo(self, root):
        """git init at ``root`` with an in-repo identity so commits succeed."""
        _git("init", "-q", root)
        _git("-C", root, "config", "user.email", "test@example.com")
        _git("-C", root, "config", "user.name", "Test")

    def _commit_all(self, root, subject):
        _git("-C", root, "add", "-A")
        _git("-C", root, "commit", "-q", "-m", subject)

    def _log_subject(self, root):
        result = subprocess.run(
            ["git", "-C", root, "log", "-1", "--format=%s"],
            capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _commit_files(self, root):
        """Files touched by HEAD relative to its parent, as repo-relative paths."""
        result = subprocess.run(
            ["git", "-C", root, "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True)
        return sorted(p for p in result.stdout.split("\n") if p.strip())

    def _commit_count(self, root):
        result = subprocess.run(
            ["git", "-C", root, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True)
        return int(result.stdout.strip())

    def _write(self, path, body):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)

    def test_non_git_directory_returns_false_no_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            page = os.path.join(root, "page.md")
            self._write(page, "hello\n")
            self.assertFalse(sc.wiki_autocommit(root, [page], "shipd-wiki: emit"))

    def test_nested_store_commits_written_files_with_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._init_repo(ws)
            store = os.path.join(ws, ".shipd", "wiki")
            index = os.path.join(store, "index.md")
            self._write(index, "v1\n")
            self._commit_all(ws, "seed")
            # One modified (index.md) and one new (page.md) in the store.
            self._write(index, "v2\n")
            page = os.path.join(store, "page.md")
            self._write(page, "new page\n")
            subject = "shipd-wiki: emit 2 file(s)"
            made = sc.wiki_autocommit(store, [index, page], subject)
            self.assertTrue(made)
            self.assertEqual(self._log_subject(ws), subject)
            self.assertEqual(
                self._commit_files(ws),
                [".shipd/wiki/index.md", ".shipd/wiki/page.md"])

    def test_byte_identical_write_returns_false_no_new_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._init_repo(ws)
            store = os.path.join(ws, ".shipd", "wiki")
            index = os.path.join(store, "index.md")
            self._write(index, "same\n")
            self._commit_all(ws, "seed")
            before = self._commit_count(ws)
            # Re-write byte-identical content: nothing changed on disk.
            self._write(index, "same\n")
            made = sc.wiki_autocommit(store, [index], "shipd-wiki: emit 1 file(s)")
            self.assertFalse(made)
            self.assertEqual(self._commit_count(ws), before)

    def test_unrelated_staged_file_is_not_swept(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            self._init_repo(ws)
            store = os.path.join(ws, ".shipd", "wiki")
            index = os.path.join(store, "index.md")
            self._write(index, "v1\n")
            self._commit_all(ws, "seed")
            # An unrelated file, staged but not committed.
            unrelated = os.path.join(ws, "unrelated.txt")
            self._write(unrelated, "not mine\n")
            _git("-C", ws, "add", "unrelated.txt")
            # A wiki write.
            page = os.path.join(store, "page.md")
            self._write(page, "page\n")
            made = sc.wiki_autocommit(store, [page], "shipd-wiki: emit 1 file(s)")
            self.assertTrue(made)
            self.assertEqual(self._commit_files(ws), [".shipd/wiki/page.md"])
            status = subprocess.run(
                ["git", "-C", ws, "status", "--porcelain", "--", "unrelated.txt"],
                capture_output=True, text=True, check=True).stdout
            self.assertEqual(status.strip(), "A  unrelated.txt")

    def test_identity_less_repo_returns_false_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.realpath(tmp)
            _git("init", "-q", ws)  # no in-repo identity configured
            store = os.path.join(ws, ".shipd", "wiki")
            page = os.path.join(store, "page.md")
            self._write(page, "content\n")
            stderr = io.StringIO()
            with _no_git_identity(), \
                    contextlib.redirect_stderr(stderr):
                made = sc.wiki_autocommit(store, [page], "shipd-wiki: emit 1 file(s)")
            self.assertFalse(made)
            self.assertIn("wiki auto-commit skipped", stderr.getvalue())
            # The written file is intact.
            with open(page, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "content\n")


if __name__ == "__main__":
    unittest.main()
