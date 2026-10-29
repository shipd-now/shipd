## MODIFIED Requirements

### Requirement: Doctor skill registration
id: doctor-skill-registration
base: 4ad72b74fd95
Dropped: Recovery rule is carried

The skill SHALL live at `plugins/s/skills/doctor/SKILL.md` with `name` and
`description` frontmatter whose description carries the `/s:doctor` trigger,
and SHALL be listed in the repository `README.md` skills table and in
`AGENTS.md`'s skill enumeration.

#### Scenario: Skill is discoverable and documented
- **WHEN** the plugin's skills and the README table are compared
- **THEN** `doctor` appears in both, with `/s:doctor` as its invocation
