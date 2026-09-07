## 1. Document workspaces_root in the guide

- [x] 1.1 [req: workspaces-doc] In `docs/workspaces.md` §1 ("One-time machine
      setup"), add `workspaces_root` to the `~/.shipd-config.json` coverage:
      extend the example JSON block with `"workspaces_root": "~/workspaces"`
      and add a dash-list entry (matching the `clone_sources`/`wiki_base`
      entries' voice) stating it mandates the guide's parent-directory
      convention — a bare name to `shipd workspace init` resolves to
      `<workspaces_root>/<name>` with the leaf created; an explicit init
      target or `/s:workspace clone` destination outside the root is refused
      with an error naming the target, the declared root, and
      `workspaces_root`; `--nested` job workspaces inside the root stay
      legal; undeclared = no mandate, nothing changes. Note in the same entry
      that `shipd config` reports the raw declared value (`~` unexpanded),
      that the installed sample config documents the key, and that the doctor
      `config` check fails on a malformed value and warns when the declared
      root directory is missing. Adjust §1's surrounding prose ("Both keys
      tune…") only as far as grammatical correctness requires.
- [x] 1.2 [req: workspaces-doc] In `docs/workspaces.md` §2 ("Create a job
      workspace"), after the existing `mkdir -p` + `shipd workspace init`
      example, add a short note that with `workspaces_root` declared (§1) the
      bare name suffices — `shipd workspace init documents-linking` creates
      and initializes `~/workspaces/documents-linking` — keeping the existing
      explicit-path example as the undeclared-key flow. Change nothing else
      in the guide.

## 2. Verify

- [x] 2.1 [req: *] Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py workspaces-doc-root`
      from the worktree root and confirm it reports no errors; confirm
      `git diff --stat` shows `docs/workspaces.md` as the only file outside
      `.shipd/` touched by the change.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 42 | 10.9k |
| Edit | 6 | 788 |
| Read | 4 | 464 |
| (no tool) | 0 | 12 |
| Agent | 2 | 5 |
| ToolSearch | 1 | 2 |
| **Total** | 55 | 12.1k |
