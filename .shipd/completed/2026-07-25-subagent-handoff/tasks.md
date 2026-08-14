## 1. Traceability lint rule (test-first)

- [x] 1.1 [P1] [req: traceability-tag-enforcement] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add failing tests for
      the `[req: ...]` tag rule against inline/temp tasks fixtures: a task with
      no tag errors; an unresolvable id errors naming the id; two tags on one
      task error; `[req: *, some-id]` errors; a fully tagged file (ids present
      in the change's deltas) passes; a lone `[req: *]` barrier passes; a task
      carrying both `[P2]` and a req tag parses without disturbing existing
      group behavior. These tests are expected to fail until 2.1 lands.
- [x] 1.2 [P1] [req: task-traceability-tags] In
      `plugins/s/skills/plan/references/emission.md`: add the traceability
      tag to the task-discipline rules (grammar `[req: <id>[, <id>...]]` /
      lone `[req: *]`, placement after the `[P<n>]` tag, ids resolve against
      the change's own deltas) and update the worked `tasks.md` example to
      carry tags.

## 2. Implement rule, handoff docs, validator

- [x] 2.1 [P2] [req: traceability-tag-enforcement] In
      `plugins/s/skills/build/scripts/spec_lint.py`, implement the tag rule
      per the delta spec: error per violating task naming its ordinal —
      missing tag, malformed tag, multiple tags, wildcard combined with ids,
      or an id not declared in the change's delta specs. Stdlib only. The 1.1
      tests must now pass.
- [x] 2.2 [P2] [req: artifact-compiled-context-handoff, adversarial-validation-gates-verified]
      In `plugins/s/skills/build/SKILL.md`: add the handoff rules to Phase 3
      (clean context, artifacts are the compiled context, no restated globals,
      addenda slot by reference) and insert the validator step into Phase 5
      between the suite-green check and `set-status verified` (spawn per
      `references/validator-prompt.md`, per-scenario verdicts, refutation →
      fix loop, only a fully confirmed report allows `verified`).
- [x] 2.3 [P2] [req: orchestrator-addenda-slot] In
      `plugins/s/skills/build/references/subagent-prompt.md`: add an explicit
      optional "## Orchestrator addenda" section (fill-in slot with a
      one-line rule: build-specific binding context only, omit when empty)
      and a note that tasks carry `[req: ...]` tags naming the delta
      requirements they satisfy.
- [x] 2.4 [P2] [req: adversarial-validation-gates-verified] Create
      `plugins/s/skills/build/references/validator-prompt.md`: a validator
      sub-agent template mirroring the sub-agent prompt's structure — role
      (independent adversarial validator, same tier as builders), inputs
      (change name, delta specs, relevant masters, the code; explicitly no
      builder summaries or orchestrator history), posture (attempt to refute
      each `#### Scenario:` by exercising real behavior), output contract
      (one `confirmed`/`refuted` verdict per scenario with evidence),
      and guardrails (read-only with respect to specs; never marks tasks,
      merges, or commits).

## 3. Verify

- [x] 3.1 [req: *] Run the full suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) —
      everything passes including the 1.1 tests; run
      `python3 plugins/s/skills/build/scripts/spec_lint.py subagent-handoff`
      and confirm exit 0 (this change's own tags resolve — the rule
      self-hosts); then break a tag in a scratch copy of a change under a temp
      root and confirm the linter errors name the task ordinal and the
      unresolvable id.
