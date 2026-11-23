## MODIFIED Requirements

### Requirement: Skill registration surfaces
id: document-registration
base: 6c548f2bbf21

The plugin SHALL register the skill on its standard surfaces: an
`/s:document` row in `docs/cheatsheet.md`'s command table, an `AGENTS.md` rule
that documentation under `docs/` is authored and revised through
`/s:document` plus a mention in its skill list, a CI `unittest discover`
line for `plugins/s/skills/document/tests`, a harness body template at
`plugins/s/harness/bodies/document.md` opening with a
`<!-- description: ... -->` marker (per the harness-command-bodies
capability), and a plugin version bump in
`plugins/s/.claude-plugin/plugin.json`.

#### Scenario: The surfaces name the skill
- **WHEN** the change is merged
- **THEN** `docs/cheatsheet.md`'s command table has an `/s:document` row, `AGENTS.md`
  names `/s:document` for docs authoring, `ci.yml` discovers the skill's
  tests, and the plugin version is bumped
