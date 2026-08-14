## 1. The /s:preferences skill

- [x] 1.1 [req: preferences-skill, memory-page-family] Create
      `plugins/s/skills/preferences/SKILL.md` for `/s:preferences`, following
      the structure of a sibling skill (read `plugins/s/skills/teach/SKILL.md`
      and `plugins/s/skills/ask/SKILL.md` first): frontmatter (`name`,
      `description` with trigger phrases), a first-status-sentence version
      announce reading `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, a
      "resolve the personal store" step (`wiki-show --personal`, scaffolding with
      `wiki-init --personal` when it reports no store), and the
      `memory-<subject>` page grammar (line-1 title, one-line statement, then
      `- Origin:` and `- Captured:` provenance).
- [x] 1.2 [req: preferences-skill] In that SKILL.md, specify the
      extract → reconcile → confirm → install flow: extract preference
      candidates from the invocation argument or the session; reconcile each
      against existing `memory-*` pages via `cat wiki index --personal` and
      read-only grep of the personal store's `wiki/` dir, classifying add /
      update / skip-duplicate; present the proposed set (each with its
      classification and target slug) and proceed only on a typed go-ahead (no
      AskUserQuestion); then install through ONE staged `spec_emit.py wiki
      --personal` call over a throwaway staging dir holding the touched
      `wiki/memory-<subject>.md` pages, the full `index.md` (existing entries
      plus one per touched page), and the full `log.md` with a dated
      `## [YYYY-MM-DD] preferences | <subject>` entry appended. State that store
      files are never edited in place and an update re-emits the page.

## 2. Roster and packaging

- [x] 2.1 [req: preferences-skill] Add a one-line `/s:preferences` entry to the
      skill roster sentence in `AGENTS.md`, alongside the existing `/s:ask` /
      `/s:teach` entries.
- [x] 2.2 [req: preferences-skill] Bump the plugin version to `0.6.23` in
      `plugins/s/.claude-plugin/plugin.json` (this change touches
      `plugins/s/`), then run the engine unit suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it still passes (no engine code changed, so it must remain green).
