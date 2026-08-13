# Tasks

## 1. Skill flows (SKILL.md)

- [x] 1.1 [req: workspace-clone-sync-flows] In
      `plugins/s/skills/workspace/SKILL.md`, extend the frontmatter
      description and trigger phrases with the clone/sync flows ("clone a
      workspace", "sync the workspace", "materialize members") and add
      `clone <url> [dest]` and `sync` to the verb-dispatch list.
- [x] 1.2 [req: workspace-clone-sync-flows] Add the `clone` section to
      `plugins/s/skills/workspace/SKILL.md`: run `git clone <url> [dest]`;
      when a workspace root resolves from the destination's parent, proceed
      and report a one-line note naming the enclosing root; refuse only
      when the destination's immediate parent itself declares `workspace`
      in its own `.shipd-config.json`; then continue with the `sync` section's
      flow from inside the created root.
- [x] 1.3 [req: workspace-clone-sync-flows] Add the `sync` section to
      `plugins/s/skills/workspace/SKILL.md`: run `workspace-sync --json`
      via the status CLI; execute each member record by action (`none` →
      report with any `drift:` verbatim, touch nothing; `worktree` /
      `reference-clone` / `clone` → run the record's `command:` as printed;
      `unmaterializable` → report the `reason:`, skip); report a failed
      command against its member and continue; then re-run `workspace-sync
      --json --write-gitignore` to reconcile the marked block and confirm
      each executed member is now `none` without drift; end with the
      roster via `workspace-show`. State explicitly: no confirmation
      round, and on no discoverable workspace report the CLI error
      verbatim pointing at `init` or `clone`.
- [x] 1.4 [req: workspace-setup-skill] In
      `plugins/s/skills/workspace/SKILL.md`, update the `init` section and
      the question contract: one AskUserQuestion call carrying the
      target-root choice and a portable-git-seeding choice (plain init the
      recommended default), mapping seeding to `workspace-init <path>
      --git`; update the Ending section to cover all four verbs.

## 2. Version

- [x] 2.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      the version on remote main (0.6.17 at planning time — re-check before
      editing; other changes merge concurrently).

## 3. Verification

- [x] 3.1 [req: workspace-clone-sync-flows] Scenario-run the flows with
      local path URLs in a scratch directory (no network): build a source
      workspace repo via `workspace-init --git` whose manifest declares two
      members with local-path `url`s, commit it, clone it per the skill's
      `clone` flow, run the `sync` flow, and observe both members
      materialized as git work trees, the marked gitignore block matching
      the manifest, and a drift note reported (not repaired) after mutating
      one member's origin URL.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and observe an
      all-green run (no engine change expected — sanity gate).
