## 1. Design scratch tool (`design.py`)

- [x] 1.1 [req: design-scratch-area, design-scratch-cleanup] Add
      `plugins/s/skills/build/tests/test_design.py` covering `design.py path
      <change>` (prints the absolute `<designs-root>/<change>` under a
      tmp `HOME`/config, creates it, and honors a `build.design_dir` config
      override) and `design.py clean <change>` (removes the dir; exits `0` and
      warns when the dir is absent or unremovable). Run it and observe it fail —
      `design.py` does not exist yet.
- [x] 1.2 [req: design-scratch-area, design-scratch-cleanup] Add
      `plugins/s/skills/build/scripts/design.py` (stdlib only) with `path` and
      `clean` verbs resolving `<designs-root>/<change>` (default `~/.shipd/designs`,
      overridable via the resolved config's `build.design_dir`, home-expanded —
      mirror `build_report.py::build_log_dir`); `path` creates the dir
      (`makedirs exist_ok`), `clean` `shutil.rmtree`s it fail-soft (warn on
      stderr, always exit `0`, mirroring `heartbeat.py`). Confirm
      `test_design.py` passes.

## 2. Worker contracts read the design reference

- [x] 2.1 [req: design-reference-consumed] Extend
      `plugins/s/skills/build/tests/test_subagent_contract.py` with a test
      asserting `plugins/s/agents/sub-agent.md` instructs the sub-agent to read
      the plan-named design scratch directory as a read-only reference. Run it,
      observe failure.
- [x] 2.2 [req: adversarial-validation-gates-verified] Add a contract test
      (same suite) asserting `plugins/s/agents/validator.md` lists the
      plan-named design scratch directory among the validator's inputs. Run it,
      observe failure.
- [x] 2.3 [P2] [req: design-reference-consumed] Edit
      `plugins/s/agents/sub-agent.md`: when `plan.md`'s `## Implementation`
      names a design scratch directory, read it verbatim as a read-only,
      out-of-worktree reference and build to match it (never edit it). Confirm
      2.1 passes.
- [x] 2.4 [P2] [req: adversarial-validation-gates-verified] Edit
      `plugins/s/agents/validator.md`: add the plan-named design scratch
      directory to the validator's inputs so it can refute design-fidelity
      scenarios against the real design. Confirm 2.2 passes.

## 3. Emission convention and build orchestration wiring

- [x] 3.1 [req: design-fidelity-scenarios, design-reference-consumed] Edit
      `plugins/s/skills/plan/references/emission.md`: document the design
      scratch convention — reference the design dir by absolute path in
      `plan.md`'s `## Implementation`, and author design-fidelity `#### Scenario:`
      blocks that assert conformance against that design.
- [x] 3.2 [req: artifact-compiled-context-handoff] Edit
      `plugins/s/skills/build/SKILL.md` Phase 3 handoff: state that when
      `plan.md` names a design scratch directory, it is part of the artifact set
      the sub-agent reads (the path travels inside `plan.md`; a read-only
      out-of-worktree reference), leaving the clean-context contract intact.
- [x] 3.3 [req: adversarial-validation-gates-verified] Edit
      `plugins/s/skills/build/SKILL.md` Phase 5: have the validator read the
      plan-named design scratch directory so design-fidelity scenarios are
      refuted against the design.
- [x] 3.4 [req: design-scratch-cleanup] Edit
      `plugins/s/skills/build/SKILL.md` Phase 7 close-out: run `design.py clean
      <change>` to delete the scratch dir (fail-soft), so a design never lingers
      or reaches the repo/PR.

## 4. Ship-readiness

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump) so the versioned
      plugin cache picks up the changed skills, agents, and scripts.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the full suite — including
      `test_design.py` and the new contract assertions — passes without
      `textual`.
