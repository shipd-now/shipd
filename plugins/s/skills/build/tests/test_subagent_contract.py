#!/usr/bin/env python3
"""Tests for agents/sub-agent.md and agents/validator.md — the execution
sub-agent and validator role contracts.

The contracts are Markdown files read by the model, so they can't be
exercised as code; instead these tests pin their load-bearing text the way
test_statusline.py pins the statusline's behavior. They assert the workspace
gate section (sub-agent), the design-fidelity handoff text (both), and the
research-report artifact-set bullet (sub-agent) carry each required element,
so a contract regression (a dropped or reworded clause) fails CI.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "agents", "sub-agent.md"))
VALIDATOR_CONTRACT = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "agents", "validator.md"))
ORACLE_CONTRACT = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "agents", "oracle.md"))


class WorkspaceGateContractTest(unittest.TestCase):
    def setUp(self):
        with open(CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read()

    def gate_section(self):
        """The workspace-gate section body: from its `## Workspace gate`
        heading up to the next top-level `## ` heading (or end of file)."""
        m = re.search(r"^## Workspace gate\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(
            m, "contract is missing a '## Workspace gate' section heading")
        start = m.start()
        nxt = re.search(r"^## ", self.text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(self.text)
        return self.text[start:end]

    def test_has_gate_heading_scoped_before_claim_or_edit(self):
        heading = re.search(r"^## Workspace gate\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(heading)
        self.assertIn("before any claim or edit", heading.group(0).lower())

    def test_requires_branch_check(self):
        section = self.gate_section().lower()
        self.assertIn("git rev-parse --abbrev-ref head", section)
        self.assertIn("change/", section)

    def test_requires_worktree_root_check(self):
        self.assertIn("worktree root", self.gate_section().lower())

    def test_requires_stop_and_report_on_mismatch(self):
        section = self.gate_section().lower()
        self.assertIn("mismatch", section)
        self.assertIn("stop", section)
        self.assertIn("report", section)

    def test_requires_paths_inside_the_worktree(self):
        section = self.gate_section().lower()
        # Every edited/passed path stays inside the worktree, never an absolute
        # path into another checkout.
        self.assertIn("never an absolute path", section)


class DesignReferenceContractTest(unittest.TestCase):
    """The design-fidelity handoff (design-reference-consumed): when
    plan.md's ## Implementation names a design scratch directory, the
    sub-agent reads it as a read-only reference and builds to match it,
    rather than reconstructing the design from a prose summary."""

    def setUp(self):
        with open(CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read().lower()

    def test_reads_plan_named_design_scratch_dir(self):
        self.assertIn("design scratch dir", self.text)
        self.assertIn("## implementation", self.text)

    def test_treats_it_as_read_only_and_never_edits_it(self):
        self.assertIn("read-only", self.text)
        self.assertIn("never edit it", self.text)

    def test_builds_to_match_it(self):
        self.assertIn("match it", self.text)


class ResearchReferenceContractTest(unittest.TestCase):
    """The research-report handoff (build-subagent-handoff
    artifact-compiled-context-handoff): when plan.md's ## Implementation names
    an installed research report by its content-directory research/ path, the
    sub-agent's step-1 artifact-set list sends it to that path as a read-only
    reference, so the report travels by path rather than as spawn-message
    prose. Where no report is named, the step is a no-op."""

    def setUp(self):
        with open(CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read().lower()

    def research_bullet(self):
        """The artifact-set bullet naming the research report: from the list
        marker opening the item that mentions an installed research report, up
        to the next list marker or numbered step (or end of file). Scoping to
        the bullet keeps the assertions from passing on the sibling
        design-scratch bullet's wording."""
        lines = self.text.splitlines()
        start = None
        for idx, line in enumerate(lines):
            if line.lstrip().startswith("- ") and "research report" in line:
                start = idx
                break
        self.assertIsNotNone(
            start,
            "contract's artifact-set list is missing a research-report bullet")
        end = len(lines)
        for idx in range(start + 1, len(lines)):
            stripped = lines[idx].lstrip()
            if stripped.startswith("- ") or re.match(r"^\d+\. ", stripped):
                end = idx
                break
        return "\n".join(lines[start:end])

    def test_reads_the_plan_named_installed_research_report(self):
        bullet = self.research_bullet()
        self.assertIn("installed research report", bullet)
        self.assertIn("## implementation", bullet)
        self.assertIn("research/", bullet)

    def test_treats_it_as_read_only_and_never_edits_it(self):
        bullet = self.research_bullet()
        self.assertIn("read-only", bullet)
        self.assertIn("never edit it", bullet)

    def test_naming_no_report_makes_the_step_a_no_op(self):
        self.assertIn("no-op", self.research_bullet())


class ValidatorDesignReferenceContractTest(unittest.TestCase):
    """The design-fidelity handoff (adversarial-validation-gates-verified):
    the validator's inputs list the plan-named design scratch directory, so
    it can refute design-fidelity scenarios against the real design."""

    def setUp(self):
        with open(VALIDATOR_CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read().lower()

    def inputs_section(self):
        """The 'Your inputs' section body: from its heading up to the next
        top-level `## ` heading (or end of file)."""
        m = re.search(r"^## your inputs\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(
            m, "contract is missing a '## Your inputs' section heading")
        start = m.start()
        nxt = re.search(r"^## ", self.text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(self.text)
        return self.text[start:end]

    def test_lists_plan_named_design_scratch_dir_among_inputs(self):
        section = self.inputs_section()
        self.assertIn("design scratch dir", section)
        self.assertIn("## implementation", section)

    def test_treats_it_as_read_only_for_refuting_design_fidelity(self):
        section = self.inputs_section()
        self.assertIn("read-only", section)
        self.assertIn("design-fidelity", section)


class OracleChainRungContractTest(unittest.TestCase):
    """The oracle's search ladder carries a workspace-chain rung between the
    personal and base rungs (shipd-ask oracle-agent-contract,
    oracle-cited-answers): it reads `wiki-show`'s `chain:` line, searches each
    listed store nearest first with the same engine reads and read-only grep,
    skips a chain member holding no store, and the base rung still follows it.
    Also pins the `Cited: [[slug]] (inherited <ws-root>)` citation marker."""

    def setUp(self):
        with open(ORACLE_CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read()
        self.lower = self.text.lower()

    def ladder_section(self):
        """The '## The search ladder' section body: from its heading up to
        the next top-level `## ` heading (or end of file)."""
        m = re.search(
            r"^## The search ladder\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(
            m, "contract is missing a '## The search ladder' section heading")
        start = m.start()
        nxt = re.search(r"^## ", self.text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(self.text)
        return self.text[start:end]

    def test_ladder_reads_the_chain_line(self):
        section = self.ladder_section().lower()
        self.assertIn("chain:", section)

    def test_ladder_searches_chain_stores_nearest_first(self):
        section = self.ladder_section().lower()
        self.assertIn("nearest first", section)

    def test_ladder_skips_a_chain_member_with_no_store(self):
        section = self.ladder_section().lower()
        self.assertIn("no store", section)

    def test_base_rung_still_follows_the_chain_rung(self):
        section = self.ladder_section().lower()
        chain_pos = section.find("chain:")
        base_pos = section.find("base wiki")
        self.assertGreater(chain_pos, -1)
        self.assertGreater(base_pos, -1)
        self.assertLess(chain_pos, base_pos)

    def test_documents_the_inherited_citation_marker(self):
        self.assertIn("Cited: [[slug]] (inherited <ws-root>)", self.text)

    def test_ladder_requires_copying_the_separators_provenance_annotation(self):
        """The inherited marker must be copied verbatim from what the engine
        already printed on the page's separator line — not derived by the
        agent comparing paths itself. The ladder section must instruct
        copying the `(inherited <ws-root>)` annotation verbatim onto the
        citation."""
        section = self.ladder_section().lower()
        self.assertIn("verbatim", section)
        self.assertIn("separator line", section)
        self.assertIn("(inherited <ws-root>)", section)


if __name__ == "__main__":
    unittest.main()
