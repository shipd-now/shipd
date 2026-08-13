## 1. Git-backing flow in /s:preferences

- [x] 1.1 [req: git-backing-flow] In `plugins/s/skills/preferences/SKILL.md`,
      add a git-backing flow section covering the first-run path: after resolving
      the store, detect whether the git root `<memory_dir>` (the parent of the
      `<memory_dir>/wiki` store) is inside a git work tree with `git -C
      <memory_dir> rev-parse --is-inside-work-tree`; when it is not, offer — in a
      typed round — to `git init <memory_dir>` and run it before the staged emit,
      so the capture's `wiki_autocommit` includes the first captured page.
- [x] 1.2 [req: git-backing-flow] In that section, specify the remote + push
      steps: only on the user's confirmation and where `gh` is available and
      authenticated, offer `gh repo create shipd-memory --private` and `git remote
      add origin <url>`, then offer a confirmed `git push -u origin <branch>`;
      when `gh` is absent or the user declines the remote, complete the local
      `git init` and print the manual `gh repo create` / `git remote add` /
      `git push` commands. State that a failed `gh`/`push` is non-fatal — it is
      reported and the local commit remains the durable outcome.
- [x] 1.3 [req: git-backing-flow] In that section, specify the already-git-backed
      path: when `<memory_dir>` is already a git work tree with an `origin` remote
      and unpushed commits, the capture autocommits locally (as today) and the
      skill then offers a confirmed `git push`. Emphasize every git/gh/push step
      is a typed round (no AskUserQuestion) and the engine never pushes.
- [x] 1.4 [req: git-backing-flow] Update the existing SKILL.md line that says the
      skill "adds no git logic" to reflect the new git-backing flow, and add the
      config-as-convention note (the personal repo MAY also hold
      `~/.shipd-config.json`, symlinked; no engine reads or syncs settings).

## 2. Packaging

- [x] 2.1 [req: git-backing-flow] Bump the plugin version to `0.6.25` in
      `plugins/s/.claude-plugin/plugin.json` (this change touches
      `plugins/s/`), then run the engine unit suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it still passes (no engine code changed, so it must remain green).
