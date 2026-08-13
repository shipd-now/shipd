## 1. Version stamp

- [x] 1.1 [req: version-announcement] In `plugins/s/skills/plan/SKILL.md`,
      add a "Announce the version first" rule to the preamble (before the
      Flow section): read `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`
      and include `am:plan v<version>` in the first user-visible status
      sentence of the session.

## 2. Version

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.2.10 to 0.2.11 (plugin content changed: plan skill edited).
