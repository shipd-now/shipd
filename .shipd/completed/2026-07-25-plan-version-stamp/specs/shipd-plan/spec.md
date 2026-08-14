## ADDED Requirements

### Requirement: Version announcement
id: version-announcement

When the skill starts, it SHALL read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`am:plan v<version>` in its first user-visible status sentence, so a session
always displays which plugin snapshot it is running and a stale snapshot is
recognizable on sight.

#### Scenario: First status line names the running version
- **WHEN** `/s:plan` starts in any repository
- **THEN** the first user-visible sentence includes `am:plan v<version>` with
  the version read from the running snapshot's `plugin.json`

#### Scenario: Stale snapshot is recognizable
- **WHEN** the plugin cache holds an older snapshot than the repo's
  `plugins/s/` source
- **THEN** the announced version exposes the mismatch to the user
