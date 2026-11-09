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
    os.path.join(HERE, "..", "..", "ask", "references", "oracle-contract.md"))
ORACLE_AGENT_FILES = (
    os.path.normpath(os.path.join(HERE, "..", "..", "..", "agents",
                                  "oracle.md")),
    os.path.normpath(os.path.join(HERE, "..", "..", "..", "harness", "agents",
                                  "oracle.md")),
)
TEACHER_CONTRACT = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "agents", "teacher.md"))
BUILD_SKILL = os.path.normpath(os.path.join(HERE, "..", "SKILL.md"))


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


class OracleInlineContractTest(unittest.TestCase):
    """The oracle is an inline consultation (shipd-ask
    oracle-consultation-contract): the contract reference exists within 120
    lines, carries the judging rules, and no oracle agent file ships."""

    def setUp(self):
        self.assertTrue(os.path.isfile(ORACLE_CONTRACT),
                        "oracle-contract.md is missing")
        with open(ORACLE_CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read()

    def test_is_at_most_120_lines(self):
        self.assertLessEqual(len(self.text.splitlines()), 120)

    def test_names_the_judging_rules(self):
        for needle in ("oracle-lookup", "INSUFFICIENT", "Cited:",
                       "Evidence:", "Authority: advisory"):
            self.assertIn(needle, self.text)

    def test_no_oracle_agent_file_ships(self):
        for path in ORACLE_AGENT_FILES:
            self.assertFalse(os.path.exists(path), path)


class ForegroundClaimDisciplineContractTest(unittest.TestCase):
    """The worker contract's loop section (foreground-claim-discipline,
    claim-wait-foreground) forbids ending a turn while still holding a
    claim: before stopping for any reason — including to await a
    long-running verification — the worker completes the task or releases
    it, so a held task never outlives the agent watching it."""

    def setUp(self):
        with open(CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read()

    def loop_section(self):
        """The '## Your loop' section body: from its heading up to the next
        top-level `## ` heading (or end of file)."""
        m = re.search(r"^## Your loop\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(
            m, "contract is missing a '## Your loop' section heading")
        start = m.start()
        nxt = re.search(r"^## ", self.text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(self.text)
        return self.text[start:end]

    def test_forbids_ending_turn_while_holding_a_claim(self):
        section = self.loop_section().lower()
        self.assertIn("never end", section)
        self.assertIn("holding a claim", section)
        self.assertIn("complete", section)
        self.assertIn("release", section)

    def test_names_awaiting_long_running_verification_as_a_stop(self):
        section = self.loop_section().lower()
        self.assertIn("long-running verification", section)

    def test_wait_timeout_default_matches_script(self):
        """The `--wait` default this contract quotes to the worker must
        match claim_task.sh's own TIMEOUT= (pinned by
        test_claim_task.py::test_wait_default_is_90_seconds), so the two
        can't silently drift apart."""
        self.assertIn("default 90", self.text)
        self.assertNotIn("default 600", self.text)


class OrchestratorStaleClaimCheckContractTest(unittest.TestCase):
    """The build skill's fan-out phase (foreground-claim-discipline,
    claim-wait-foreground) directs the orchestrator to check for stale
    claims between fan-out rounds with `status <change> --stale-after
    <mins>` and to act on any claim the check reports stale; reclamation
    stays operator-driven via `release --stale`, never automatic in
    `claim`."""

    def setUp(self):
        with open(BUILD_SKILL, encoding="utf-8") as fh:
            self.text = fh.read()

    def phase3_section(self):
        """The '## Phase 3' section body: from its heading up to the next
        top-level `## ` heading (or end of file)."""
        m = re.search(r"^## Phase 3\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(
            m, "build skill is missing a '## Phase 3' section heading")
        start = m.start()
        nxt = re.search(r"^## ", self.text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(self.text)
        return self.text[start:end]

    def test_directs_stale_check_between_fan_out_rounds(self):
        section = self.phase3_section().lower()
        self.assertIn("--stale-after", section)
        self.assertIn("between fan-out rounds", section)
        self.assertIn("status", section)

    def test_directs_acting_on_a_reported_stale_claim(self):
        section = self.phase3_section().lower()
        self.assertIn("[stale]", section)
        self.assertIn("release --stale", section)

    def test_claim_never_reclaims_on_its_own(self):
        section = self.phase3_section().lower()
        self.assertIn("never reclaim", section)

    def test_wait_timeout_default_matches_script(self):
        """The coordinator script reference's own `--timeout <secs>`
        default must match claim_task.sh's TIMEOUT= (pinned by
        test_claim_task.py::test_wait_default_is_90_seconds), so the two
        can't silently drift apart."""
        self.assertRegex(self.text, r"--timeout <secs>`\s*\(default\s+90\)")
        self.assertNotRegex(self.text, r"\(default\s+600\)")


class TaskGroupAuthoringGuidanceContractTest(unittest.TestCase):
    """The build skill's Phase 2 task-authoring guidance
    (build-task-coordination parallel-task-group-format): an unsatisfiable
    `[P<n>]` configuration passes the linter's structural checks but leaves
    the coordinator with nothing claimable, and the old advice — "when in
    doubt, leave a task untagged (a safe barrier)" — is what steers an
    author into it, since a barrier sitting between a higher-numbered group
    and a lower-numbered one makes both unreachable. The guidance must name
    the two configurations that cannot contradict themselves instead, and
    must not call an untagged task unconditionally safe.

    Written test-first; expected to FAIL until the sentence is replaced in
    `SKILL.md` (task 3.2)."""

    def setUp(self):
        with open(BUILD_SKILL, encoding="utf-8") as fh:
            self.text = fh.read()

    def phase2_section(self):
        """The '## Phase 2' section body: from its heading up to the next
        top-level `## ` heading (or end of file), with internal whitespace
        (including markdown hard-wraps) collapsed to single spaces so a
        multi-word assertion never breaks on a line-wrap that carries no
        semantic meaning."""
        m = re.search(r"^## Phase 2\b.*$", self.text, re.MULTILINE)
        self.assertIsNotNone(
            m, "build skill is missing a '## Phase 2' section heading")
        start = m.start()
        nxt = re.search(r"^## ", self.text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(self.text)
        return re.sub(r"\s+", " ", self.text[start:end])

    def test_directs_to_a_fully_untagged_file(self):
        section = self.phase2_section().lower()
        self.assertIn("every task untagged", section)
        self.assertIn("fully sequential", section)

    def test_directs_to_non_decreasing_group_numbers(self):
        section = self.phase2_section().lower()
        self.assertIn("group numbers that never decrease down the file",
                      section)

    def test_explains_the_barrier_versus_group_contradiction(self):
        section = self.phase2_section().lower()
        self.assertIn("file position", section)
        self.assertIn("number", section)
        self.assertIn("unreachable", section)

    def test_no_longer_calls_an_untagged_task_unconditionally_safe(self):
        section = self.phase2_section().lower()
        self.assertNotIn("when in doubt, leave a task untagged", section)
        self.assertNotIn("a safe barrier).", section)


HARNESS_DIR = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "harness", "agents"))


def _agent_body(path):
    """The body of an agent definition: after the closing frontmatter ``---``
    for ``agents/``, after the ``<!-- description: ... -->`` line for the
    ``harness/agents/`` twin; leading blank lines stripped."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    if lines[0] == "---":
        body = lines[lines.index("---", 1) + 1:]
    else:
        idx = next(i for i, line in enumerate(lines)
                   if line.startswith("<!-- description:"))
        body = lines[idx + 1:]
    return "\n".join(body).lstrip("\n")


class SandboxContractTest(unittest.TestCase):
    def test_validator_sandbox_section(self):
        with open(VALIDATOR_CONTRACT, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("\n## Sandbox\n", text)
        section = text.split("\n## Sandbox\n", 1)[1].split("\n## ", 1)[0]
        for needle in ("<SANDBOX_RUN>", "one quoted string",
                       "contract violation"):
            self.assertIn(needle, section)

    def test_sub_agent_names_wrapper(self):
        with open(CONTRACT, encoding="utf-8") as fh:
            self.assertIn("<SANDBOX_RUN>", fh.read())

    def test_harness_twins_match_bodies(self):
        for name in ("sub-agent.md", "validator.md", "teacher.md"):
            agent = _agent_body(os.path.join(os.path.dirname(CONTRACT), name))
            twin = _agent_body(os.path.join(HARNESS_DIR, name))
            self.assertEqual(agent, twin, name)


class TeacherContractTest(unittest.TestCase):
    """Pins the s:teacher role contract (requirement teacher-agent-contract)."""

    def setUp(self):
        with open(TEACHER_CONTRACT, encoding="utf-8") as fh:
            self.text = fh.read()

    def frontmatter(self):
        lines = self.text.split("\n")
        self.assertEqual(lines[0], "---")
        return lines[1:lines.index("---", 1)]

    def test_frontmatter_names_teacher_without_model_pin(self):
        front = self.frontmatter()
        self.assertIn("name: teacher", front)
        self.assertTrue(any(line.startswith("description: ")
                            for line in front))
        self.assertFalse(any(line.startswith("model:") for line in front))

    def test_body_names_the_flow(self):
        for needle in ("cat change", "wiki-show --json", "cat wiki index",
                       "cat wiki queue", "capture-rubric.md", "spec_emit.py",
                       "wiki --from", "wiki-queue-add",
                       '--origin "build/<change>"', "at most five"):
            self.assertIn(needle, self.text)

    def test_write_carries_the_gate_fingerprint(self):
        for needle in ("--expect", "fingerprint",
                       "failed \u2014 store changed during the run"):
            self.assertIn(needle, self.text)

    def test_cat_change_reads_only_the_plan(self):
        self.assertIn("read **only the `plan.md` portion**", self.text)
        self.assertIn("those\n  are not inputs", self.text)

    def test_output_contract_line_heads(self):
        for head in ("taught \u2014", "drained \u2014", "withheld \u2014",
                     "queued \u2014", "skipped \u2014", "failed \u2014",
                     "nothing durable"):
            self.assertIn(head, self.text)

    def test_guardrails_forbid_in_place_edits_answers_and_git(self):
        self.assertIn("\n## Guardrails\n", self.text)
        section = self.text.split("\n## Guardrails\n", 1)[1].split(
            "\n## ", 1)[0]
        for needle in ("never", "in place", "wiki-queue-answer", "git"):
            self.assertIn(needle, section)


class BuildTeacherWiringTest(unittest.TestCase):
    """Pins the build skill's post-verify teacher spawn (post-verify-teach)."""

    def setUp(self):
        with open(BUILD_SKILL, encoding="utf-8") as fh:
            self.text = fh.read()

    def test_spawn_gate_and_observation_lines(self):
        for needle in ("subagent_type: s:teacher", "teacher \u00b7 <change>",
                       "wiki-show --json",
                       "wiki: skipped \u2014 no workspace store",
                       "wiki: skipped \u2014 teach disabled by pipeline",
                       "never blocks"):
            self.assertIn(needle, self.text)

    def test_phase7_wiki_line_covers_queued_and_skipped(self):
        phase7 = self.text.split("## Phase 7", 1)[1].split("\n## ", 1)[0]
        for needle in ("queued \u2014", "queued q-",
                       "wiki: skipped \u2014 <reason>",
                       "single `skipped \u2014 <reason>`"):
            self.assertIn(needle, phase7)


if __name__ == "__main__":
    unittest.main()
