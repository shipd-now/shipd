#!/usr/bin/env python3
"""Unit tests for spec_merge: the four operations, base-hash match/mismatch,
warning summary shape, deterministic ordering, and the archive move."""

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

import spec_common as sc  # noqa: E402
import spec_merge as sm  # noqa: E402

SAMPLE_ROOT = os.path.join(FIXTURES, "sample")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


MASTER = read(os.path.join(SAMPLE_ROOT, ".shipd", "verified", "auth",
                           "spec.md"))


def master_spec():
    return sc.parse_spec(MASTER)


def ids(spec):
    return [r.id for r in spec.requirements]


def apply(delta_text):
    warnings = []
    spec = sm.apply_delta_to_spec(master_spec(), sc.parse_delta(delta_text),
                                  warnings, "auth")
    return spec, warnings


class AddedTest(unittest.TestCase):
    def test_new_id_appended(self):
        spec, w = apply(
            "## ADDED Requirements\n\n"
            "### Requirement: New\nid: brand-new\n\n"
            "The system SHALL be new.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertEqual(ids(spec)[-1], "brand-new")
        self.assertEqual(w, [])

    def test_collision_overwrites_and_warns(self):
        spec, w = apply(
            "## ADDED Requirements\n\n"
            "### Requirement: Clashing\nid: enforce-sso-timeout\n\n"
            "The system SHALL clash.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0].kind, "added-collision")
        self.assertEqual(w[0].id, "enforce-sso-timeout")
        req = spec.requirements[ids(spec).index("enforce-sso-timeout")]
        self.assertIn("SHALL clash", req.body)


class ModifiedTest(unittest.TestCase):
    def test_existing_replaced(self):
        h = sc.content_hash(
            {r.id: r for r in master_spec().requirements}["enforce-sso-timeout"])
        spec, w = apply(
            "## MODIFIED Requirements\n\n"
            "### Requirement: Enforce SSO session timeout\n"
            "id: enforce-sso-timeout\nbase: %s\n\n"
            "The system SHALL end an SSO session after 5 minutes.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n" % h)
        req = spec.requirements[ids(spec).index("enforce-sso-timeout")]
        self.assertIn("5 minutes", req.body)
        self.assertEqual(w, [])

    def test_missing_target_inserts_and_warns(self):
        spec, w = apply(
            "## MODIFIED Requirements\n\n"
            "### Requirement: Ghost\nid: ghost\nbase: 000000000000\n\n"
            "The system SHALL haunt.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        self.assertIn("ghost", ids(spec))
        self.assertEqual([x.kind for x in w], ["modified-missing"])


class RemovedTest(unittest.TestCase):
    def test_existing_deleted(self):
        h = sc.content_hash({r.id: r for r in master_spec().requirements}
                            ["legacy-cookie-fallback"])
        spec, w = apply(
            "## REMOVED Requirements\n\n"
            "### Requirement: Legacy cookie fallback\n"
            "id: legacy-cookie-fallback\nbase: %s\n"
            "Reason: gone\nMigration: none\n" % h)
        self.assertNotIn("legacy-cookie-fallback", ids(spec))
        self.assertEqual(w, [])

    def test_missing_target_noop_and_warns(self):
        spec, w = apply(
            "## REMOVED Requirements\n\n"
            "### Requirement: Ghost\nid: ghost\nbase: 000000000000\n"
            "Reason: gone\nMigration: none\n")
        self.assertEqual(ids(spec), ids(master_spec()))
        self.assertEqual([x.kind for x in w], ["removed-missing"])


class RenamedTest(unittest.TestCase):
    def test_rekey(self):
        spec, w = apply(
            "## RENAMED Requirements\n\n"
            "- FROM: password-complexity\n  TO: password-strength\n")
        self.assertIn("password-strength", ids(spec))
        self.assertNotIn("password-complexity", ids(spec))
        self.assertEqual(w, [])

    def test_source_missing_warns(self):
        spec, w = apply(
            "## RENAMED Requirements\n\n- FROM: nope\n  TO: whatever\n")
        self.assertEqual([x.kind for x in w], ["rename-source-missing"])
        self.assertEqual(ids(spec), ids(master_spec()))

    def test_target_exists_takes_newer_and_warns(self):
        spec, w = apply(
            "## RENAMED Requirements\n\n"
            "- FROM: password-complexity\n  TO: enforce-sso-timeout\n")
        self.assertEqual([x.kind for x in w], ["rename-target-exists"])
        # Only one requirement carries the target id after take-newer.
        self.assertEqual(ids(spec).count("enforce-sso-timeout"), 1)
        self.assertNotIn("password-complexity", ids(spec))


class BaseHashTest(unittest.TestCase):
    def test_match_produces_no_warning(self):
        _, w = apply(read(os.path.join(
            SAMPLE_ROOT, ".shipd", "planned", "sample-change",
            "specs", "auth", "spec.md")))
        self.assertEqual([x for x in w if x.kind == "stale-base"], [])

    def test_mismatch_warns_with_hashes(self):
        spec, w = apply(
            "## MODIFIED Requirements\n\n"
            "### Requirement: Enforce SSO session timeout\n"
            "id: enforce-sso-timeout\nbase: ffffffffffff\n\n"
            "The system SHALL end an SSO session after 5 minutes.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        stale = [x for x in w if x.kind == "stale-base"]
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0].id, "enforce-sso-timeout")
        self.assertEqual(stale[0].detail["expected"], "ffffffffffff")
        self.assertEqual(stale[0].detail["actual"],
                         sc.content_hash({r.id: r for r in
                                          master_spec().requirements}
                                         ["enforce-sso-timeout"]))
        # Take-newer: applied despite the mismatch.
        req = spec.requirements[ids(spec).index("enforce-sso-timeout")]
        self.assertIn("5 minutes", req.body)


class WarningSummaryTest(unittest.TestCase):
    def test_json_lines_are_parseable(self):
        _, w = apply(
            "## ADDED Requirements\n\n"
            "### Requirement: Clashing\nid: enforce-sso-timeout\n\n"
            "The system SHALL clash.\n\n"
            "#### Scenario: s\n- **WHEN** a\n- **THEN** b\n")
        buf = io.StringIO()
        n = sm.report_warnings(w, as_json=True, out=buf)
        self.assertEqual(n, 1)
        lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        obj = json.loads(lines[0])
        self.assertEqual(obj["id"], "enforce-sso-timeout")
        self.assertEqual(obj["kind"], "added-collision")

    def test_human_output_has_warning_and_count(self):
        _, w = apply(
            "## REMOVED Requirements\n\n"
            "### Requirement: Ghost\nid: ghost\nbase: 000000000000\n"
            "Reason: gone\nMigration: none\n")
        buf = io.StringIO()
        sm.report_warnings(w, as_json=False, out=buf)
        text = buf.getvalue()
        self.assertIn("WARNING:", text)
        self.assertIn("1 merge warning(s).", text)


class DeterministicOrderTest(unittest.TestCase):
    def test_existing_order_preserved_added_appended(self):
        spec, _ = apply(read(os.path.join(
            SAMPLE_ROOT, ".shipd", "planned", "sample-change",
            "specs", "auth", "spec.md")))
        # enforce (modified in place) stays first; legacy removed; password
        # renamed in place; rate-limit (added) appended last.
        self.assertEqual(
            ids(spec),
            ["enforce-sso-timeout", "password-strength", "rate-limit-login"])

    def test_merge_is_reproducible(self):
        delta_text = read(os.path.join(
            SAMPLE_ROOT, ".shipd", "planned", "sample-change",
            "specs", "auth", "spec.md"))
        out1 = sc.render_spec(apply(delta_text)[0])
        out2 = sc.render_spec(apply(delta_text)[0])
        self.assertEqual(out1, out2)


class MergeAndArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(SAMPLE_ROOT, ".shipd"),
                        os.path.join(self.tmp, ".shipd"))
        # Redirect flow-time-series capture (the archive_change hook) to a
        # throwaway dir so no test writes to the real ~/.shipd/builds/flow.jsonl.
        self.flow_dir = tempfile.mkdtemp()
        self._old_flow = os.environ.get("AM_FLOW_LOG_DIR")
        os.environ["AM_FLOW_LOG_DIR"] = self.flow_dir

    def tearDown(self):
        if self._old_flow is None:
            os.environ.pop("AM_FLOW_LOG_DIR", None)
        else:
            os.environ["AM_FLOW_LOG_DIR"] = self._old_flow
        shutil.rmtree(self.flow_dir, ignore_errors=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def flow_records(self):
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

    def test_merge_change_writes_master(self):
        warnings = []
        affected = sm.merge_change(self.tmp, "sample-change", warnings)
        self.assertEqual(affected, ["auth"])
        spec = sc.parse_spec(read(sm.master_path(self.tmp, "auth")))
        self.assertEqual(
            ids(spec),
            ["enforce-sso-timeout", "password-strength", "rate-limit-login"])
        self.assertEqual([w for w in warnings if w.kind == "stale-base"], [])

    def test_archive_moves_change_directory(self):
        warnings = []
        sm.merge_change(self.tmp, "sample-change", warnings)
        dst = sm.archive_change(self.tmp, "sample-change", date="2026-07-22")
        self.assertFalse(os.path.exists(sm.change_dir(self.tmp,
                                                      "sample-change")))
        self.assertTrue(os.path.isdir(dst))
        self.assertTrue(os.path.isfile(os.path.join(dst, "plan.md")))
        self.assertIn("2026-07-22-sample-change", dst)

    def test_archive_appends_a_flow_record(self):
        sm.merge_change(self.tmp, "sample-change", [])
        sm.archive_change(self.tmp, "sample-change", date="2026-07-22")
        records = self.flow_records()
        self.assertTrue(records)
        self.assertEqual(records[-1]["root"], os.path.abspath(self.tmp))

    def test_unwritable_flow_dest_does_not_fail_archive(self):
        sm.merge_change(self.tmp, "sample-change", [])
        blocker = os.path.join(self.tmp, "blocker")
        with open(blocker, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.environ["AM_FLOW_LOG_DIR"] = os.path.join(blocker, "nope")
        dst = sm.archive_change(self.tmp, "sample-change", date="2026-07-22")
        self.assertTrue(os.path.isdir(dst))


if __name__ == "__main__":
    unittest.main()
