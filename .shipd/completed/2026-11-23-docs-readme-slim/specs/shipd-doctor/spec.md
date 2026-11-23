## MODIFIED Requirements

### Requirement: Doctor skill registration
id: doctor-skill-registration
base: 895df18aaf14

The skill SHALL live at `plugins/s/skills/doctor/SKILL.md` with `name` and
`description` frontmatter whose description carries the `/s:doctor` trigger,
and SHALL be listed in `docs/cheatsheet.md`'s command table and in
`AGENTS.md`'s skill enumeration.

#### Scenario: Skill is discoverable and documented
- **WHEN** the plugin's skills and the cheatsheet's command table are compared
- **THEN** `doctor` appears in both, with `/s:doctor` as its invocation
