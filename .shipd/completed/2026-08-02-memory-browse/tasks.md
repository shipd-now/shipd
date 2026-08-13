## 1. The /s:memory skill

- [x] 1.1 [req: memory-list-skill] Create `plugins/s/skills/memory/SKILL.md`
      for `/s:memory`, following a sibling skill's structure (read
      `plugins/s/skills/ask/SKILL.md` and the new
      `plugins/s/skills/preferences/SKILL.md` first): frontmatter (`name`,
      `description` with trigger phrases), a version-announce first status
      sentence reading `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`,
      resolve the personal store with `wiki-show --personal`, read `cat wiki
      index --personal` and print the entries whose slug begins with `memory-`,
      and report "no memories stored" when the store is absent or holds none.
      State that the skill is read-only and mutates nothing.

## 2. The /s:forget skill

- [x] 2.1 [req: forget-skill] Create `plugins/s/skills/forget/SKILL.md` for
      `/s:forget <description>`, following the same conventions: frontmatter
      with trigger phrases, version announce, resolve the personal store, and
      locate the matching `memory-*` page by reading `cat wiki index --personal`
      and grepping the personal store's `wiki/` dir (the directory `wiki-show
      --personal` prints) for the description's terms.
- [x] 2.2 [req: forget-skill] In that SKILL.md, specify the confirm-then-remove
      flow: on exactly one match, issue a single AskUserQuestion in a prose-free
      turn (matched page slug and summary inside the dialog fields) and only on
      an affirmative selection run `wiki-remove <slug> --personal`; on no match
      report the miss and remove nothing; on multiple matches present the
      candidates for the user to pick before confirming.
- [x] 2.3 [req: forget-skill, question-rejection-recovery] In that SKILL.md,
      include the question rejection recovery rule verbatim from another
      interactive skill (e.g. `plugins/s/skills/status/SKILL.md`), so a
      rejected or interrupted confirmation dialog is treated as a harness
      misfire, not a decline.

## 3. Roster and packaging

- [x] 3.1 [req: question-rejection-recovery] Confirm the eight interactive
      SKILL.md files (plan, build, epic, initiative, status, onboard, research,
      forget) each carry the question rejection recovery rule — add it to any
      missing it — matching the modified shipd-interaction roster requirement.
- [x] 3.2 [req: memory-list-skill, forget-skill] Add one-line `/s:memory` and
      `/s:forget` entries to the skill roster sentence in `AGENTS.md`, alongside
      the existing `/s:preferences` / `/s:teach` entries.
- [x] 3.3 [req: memory-list-skill] Bump the plugin version to `0.6.24` in
      `plugins/s/.claude-plugin/plugin.json` (this change touches
      `plugins/s/`), then run the engine unit suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it still passes (no engine code changed, so it must remain green).
