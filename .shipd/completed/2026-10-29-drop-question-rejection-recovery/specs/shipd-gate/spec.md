## MODIFIED Requirements

### Requirement: Gate skill registration
id: gate-skill-registration
base: 13f3972f23d6
Dropped: Recovery rule is carried

The skill SHALL live at `plugins/s/skills/gate/SKILL.md` with `name` and
`description` frontmatter whose description carries the `/s:gate`
trigger, and SHALL be listed in the repository `README.md` skills table and
in `AGENTS.md`'s skill enumeration. A body template SHALL exist at
`plugins/s/harness/bodies/gate.md` opening with a
`<!-- description: … -->` marker, so the bodies/skills id-set equality the
harness-command-bodies capability enforces holds.

#### Scenario: Skill is discoverable and documented
- **WHEN** the plugin's skills and the README table are compared
- **THEN** `gate` appears in both, with `/s:gate` as its invocation

#### Scenario: Body template keeps the id-set equality
- **WHEN** the bodies directory listing is compared to the skills directory
  listing
- **THEN** `gate` appears in both sets
