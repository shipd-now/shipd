## 1. Rename the skill

- [x] 1.1 [req: remember-skill, git-backing-flow] Rename the skill directory with
      `git mv plugins/s/skills/preferences plugins/s/skills/remember`, then edit
      the moved `plugins/s/skills/remember/SKILL.md`: update the frontmatter
      `name` and `description` (trigger phrases toward "remember I…", "note that…",
      "save to memory", "/s:remember"), the version-announce example line (to
      `am:remember v<version>`), and every in-body reference — replacing
      `am:preferences` → `am:remember` and `skills/preferences` →
      `skills/remember` throughout (including the git-backing flow section). Do not
      change any behavior; only names, paths, and references.
- [x] 1.2 [req: remember-skill] Update the cross-references in the sibling skills
      and the roster: in `plugins/s/skills/memory/SKILL.md` and
      `plugins/s/skills/forget/SKILL.md`, replace `/s:preferences` with
      `/s:remember`; in `AGENTS.md`, change the skill-roster sentence entry from
      `/s:preferences` to `/s:remember` (keep the "capture … into the personal
      memory store" wording).

## 2. Verify and package

- [x] 2.1 [req: remember-skill] Confirm no stale references remain: run
      `grep -rn "am:preferences\|skills/preferences" plugins/ .shipd/verified AGENTS.md`
      and ensure it returns nothing (leave the immutable `.shipd/completed/` archive
      untouched). Fix any straggler it surfaces.
- [x] 2.2 [req: remember-skill] Bump the plugin version to `0.6.26` in
      `plugins/s/.claude-plugin/plugin.json` (this change touches `plugins/s/`),
      then run the engine unit suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and confirm
      it still passes (no engine code changed, so it must remain green).
