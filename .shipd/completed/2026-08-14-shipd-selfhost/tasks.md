## 1. Set up the exercise change in shipd

- [x] 1.1 [req: selfhost-full-lifecycle] In `/Users/mikkelbergmann/projects/shipd`,
      create the exercise change's worktree with shipd's own worktree script at
      `plugins/s/skills/build/scripts/worktree.sh`, named
      `locate-current-fallback`, based on `change/shipd-evals-port` (shipd's
      `main` is still the initial commit and carries no engine).
- [x] 1.2 [req: selfhost-full-lifecycle] In that worktree, author the exercise
      change's artifacts under `.shipd/planned/locate-current-fallback/`:
      `plan.md` (header `Status: draft`, `Theme: developer-experience`),
      `specs/spec-status/spec.md` carrying a `## MODIFIED Requirements` block for
      requirement id `locate-verb` with a correct `base:` hash, and `tasks.md`.
      The change makes `spec_status.py locate` fall back to the current selection
      like every sibling change-taking verb.
- [x] 1.3 [req: selfhost-full-lifecycle] Lint the exercise change clean with
      shipd's own linter (`plugins/s/skills/build/scripts/spec_lint.py`) and
      promote it to `ready` with shipd's own status CLI.

## 2. Build the exercise change

- [x] 2.1 [req: selfhost-full-lifecycle] In
      `plugins/s/skills/build/scripts/spec_status.py`, give the `locate`
      subparser's `change` argument `nargs="?", default=None` and resolve it
      through `_resolve_change` in `cmd_locate`, matching every sibling verb.
      Update `cmd_locate`'s docstring to state the fallback.
- [x] 2.2 [req: selfhost-full-lifecycle] Add a matching test to
      `plugins/s/skills/build/tests/test_spec_status.py` covering both the
      fallback (a selection exists) and the error path (no argument, no
      selection).
- [x] 2.3 [req: selfhost-full-lifecycle] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 2.4 [req: selfhost-full-lifecycle] Run shipd's stdlib test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) from the
      exercise worktree and confirm it is green.
- [x] 2.5 [req: selfhost-full-lifecycle] Re-derive the exercise change's status
      from its checklist with shipd's status CLI and stamp it `verified`.

## 3. Merge and archive with shipd's engine

- [x] 3.1 [req: selfhost-full-lifecycle] Merge and archive the exercise change
      with shipd's merge engine at
      `plugins/s/skills/build/scripts/spec_merge.py`.
- [x] 3.2 [req: selfhost-full-lifecycle] Confirm the merged requirement text now
      appears in shipd's master library at `.shipd/verified/spec-status/spec.md`
      and the change directory appears under `.shipd/completed/` with a dated
      name.
- [x] 3.3 [req: selfhost-full-lifecycle] Commit the exercise change (code plus
      merged specs) on its branch and push it to the shipd remote.

## 4. Verification

- [x] 4.1 [req: selfhost-full-lifecycle] Review the commands run during tasks
      1.1–3.3 and confirm none resolved to a path inside
      `/Users/mikkelbergmann/projects/shipd` or to an `/s:` skill.
- [x] 4.2 [req: selfhost-full-lifecycle] Re-derive the `shipd-port` epic's status
      in the shipd exercise worktree with shipd's own status CLI
      (`plugins/s/skills/build/scripts/spec_status.py epic-sync shipd-port`) and
      report what it derived from shipd's own library.
- [x] 4.3 [P1] [req: selfhost-full-lifecycle] Confirm `s@shipd` is still
      installed and enabled alongside `s@shipd`, so both plugins coexist as the
      epic requires.
- [x] 4.4 [P1] [req: selfhost-full-lifecycle] Confirm the exercise change's own
      lifecycle artifacts are consistent: its archived directory carries
      `plan.md`, `tasks.md` with every box checked, and its delta spec.
