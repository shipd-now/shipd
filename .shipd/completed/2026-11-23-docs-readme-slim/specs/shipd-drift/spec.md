## MODIFIED Requirements

### Requirement: Skill registration
id: drift-skill-registration
base: eb01487e09ac

The plugin SHALL ship `plugins/s/skills/drift/SKILL.md` (frontmatter
`name: drift`, trigger phrases `"drift"`, `"check drift"`, `"has the plan
drifted"`, `"/s:drift"`, claimed by no other skill), an ungated body template
`plugins/s/harness/bodies/drift.md` opening with a description marker and
containing none of `subagent`, `sub-agent`, or `AskUserQuestion`, a `/s:drift`
row in `docs/cheatsheet.md`'s command table and Unattended group, a mention in `AGENTS.md`'s skill roll, a
shipped-text contract test, and a `plugin.json` version bump.

#### Scenario: Body parity and token rules pass
- **WHEN** `test_harness_bodies` runs
- **THEN** the body ids still equal the `SKILL.md`-bearing skill directories,
  and `drift` rendered with no features carries no forbidden token

#### Scenario: The contract test pins the vocabulary
- **WHEN** `test_drift_skill_contract` runs
- **THEN** it asserts the skill and body name the verb, `--epic`, `--base`,
  `--json`, all three verdicts, the `## Drift verdicts` block, the
  `verdicts:` tally, and that `/s:drift` appears in `docs/cheatsheet.md` and `AGENTS.md`, the two registry
  files
