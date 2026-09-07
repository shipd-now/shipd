## 1. The config key

- [x] 1.1 [req: workspaces-root-key] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add a
      `WorkspacesRootDirTest` class (pattern: the existing wiki_base/memory_dir
      tests, isolating `$HOME` with `home_set_to`) covering: a declared
      `workspaces_root: "~/workflows"` resolves to the expanded absolute path;
      an undeclared key returns `None` with no error; a relative path, empty
      string, and non-string each raise `ConfigError` naming
      `workspaces_root`. Run it and observe it fail — the accessor does not
      exist yet.
- [x] 1.2 [req: workspaces-root-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `WORKSPACES_ROOT_KEY = "workspaces_root"` and
      `workspaces_root_dir(root)` next to the other path-key accessors
      (`memory_store_dir` area): resolve the layered config from `root`,
      return `None` when undeclared; otherwise require a non-empty string,
      `os.path.expanduser` it, require the expansion absolute
      (`ConfigError` naming `workspaces_root` otherwise), and return
      `os.path.normpath` of it. Confirm the 1.1 tests pass.
- [x] 1.3 [req: config-sample-coverage] Add `"workspaces_root"` to
      `RECOGNIZED_CONFIG_KEYS` in
      `plugins/s/skills/build/scripts/spec_common.py` (alphabetical position,
      after `workspace`) and a `"// workspaces_root"` comment entry to
      `plugins/s/skills/build/references/shipd.config.example.json` stating
      what the key does (mandated parent directory for job workspaces,
      enforced by `workspace-init` and `/s:workspace clone`), that `~`
      expands to an absolute path, and that it has no default (no mandate).
      Run `plugins/s/skills/build/tests/test_config_sample.py` and confirm
      the drift suite passes.

## 2. Engine enforcement in init_workspace

- [x] 2.1 [req: workspace-initialization] In
      `plugins/s/skills/build/tests/test_spec_common.py`'s
      `InitWorkspaceTest` (or a sibling class), add tests — each isolating
      `$HOME` via `home_set_to` and declaring `workspaces_root` in the fake
      home's `.shipd-config.json`, comparing `os.path.realpath` on both sides —
      for: a bare name creates and returns
      `<workspaces_root>/<name>` (leaf created, `workspace` declared); an
      explicit absolute target outside the root raises `ConfigError` whose
      message contains the target path, the declared root, and
      `workspaces_root`, writing nothing; an explicit target beneath the root
      succeeds unchanged; a bare name with a nonexistent declared root raises
      `ConfigError` naming `workspaces_root`; with no key declared, a bare
      name resolving to an existing cwd-relative directory behaves exactly as
      before. Run them and observe the new ones fail.
- [x] 2.2 [req: workspace-initialization] In
      `plugins/s/skills/build/scripts/spec_common.py`'s `init_workspace`,
      before the existing guards: resolve
      `config, _ = resolve_config(os.path.abspath(path))` and the declared
      root via the shared value logic of `workspaces_root_dir` (factor a
      config-taking helper if needed so config is resolved once); when
      declared and `path` is a bare name (no `os.sep`, no `/`, not absolute,
      not `.`/`..`), set the target to `<root>/<name>` — `ConfigError` naming
      `workspaces_root` and the root when the root is not an existing
      directory, `os.mkdir` the leaf when absent; when declared and the
      final target's `os.path.realpath` is not the root or beneath it
      (`os.path.commonpath` check against the root's realpath), raise
      `ConfigError` naming the target, the root, and `workspaces_root`.
      Leave every existing guard and option running unchanged on the final
      target. Confirm the 2.1 tests pass and the whole
      `test_spec_common.py` stays green.

## 3. CLI verb surfacing

- [x] 3.1 [req: workspace-init-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`'s workspace-init
      test class, add CLI tests (declaring `workspaces_root` in the isolated
      home layer): `workspace-init acme-job` exits 0 and prints
      `<workspaces_root>/acme-job` (realpath-compared); `workspace-init
      <outside-dir>` exits non-zero with stderr naming the target, the root,
      and `workspaces_root`. Run them and observe them fail until 2.2 lands
      (they pass through the engine — no new CLI logic).
- [x] 3.2 [req: workspace-init-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, update
      `cmd_workspace_init`'s docstring and the `workspace-init` parser's
      `path` help text to state the declared-root behavior: a bare name
      resolves into a declared `workspaces_root`, and a target outside it is
      refused. No signature change. Confirm the 3.1 tests pass.

## 4. Doctor fold-in

- [x] 4.1 [req: doctor-workspaces-root-check] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, next to the pr-mode
      config-check tests, add `check_config` tests for: a declared
      `"workspaces_root": "relative/path"` returning `fail` with a detail
      naming `workspaces_root`; a declared key naming a missing directory
      returning `warn` naming `workspaces_root` and the path; a declared key
      naming an existing directory returning the usual `ok`
      content-directory detail; an undeclared key leaving reporting
      unchanged. Run them and observe the new ones fail.
- [x] 4.2 [req: doctor-workspaces-root-check] In `plugins/s/bin/shipd`'s
      `check_config`, inside the existing try, additionally resolve
      `sc.workspaces_root_dir(root)` (a `ConfigError` flows to the existing
      `fail` return); after the try, when the resolved value is not `None`
      and not an existing directory, return a `warn` triad naming
      `workspaces_root` and the missing path; otherwise leave the existing
      returns untouched. Update `check_config`'s docstring to name the new
      validation alongside pr-mode. Confirm the 4.1 tests pass.

## 5. Skill doc

- [x] 5.1 [req: workspace-setup-skill] In
      `plugins/s/skills/workspace/SKILL.md`'s `init` section (steps 2–3) and
      question-contract section, add the declared-root behavior: read the
      resolved config first (`config-show`); when `workspaces_root` is
      declared, name the declared root in the round, offer target candidates
      inside it — substituting `<workspaces_root>/<repo-name>` for a natural
      candidate lying outside the root — and pass a chosen bare name through
      to `workspace-init` unchanged (the engine resolves and creates it).
      Note the verb refuses outside targets naming the key. Undeclared key:
      flow unchanged.
- [x] 5.2 [req: workspace-clone-sync-flows] In
      `plugins/s/skills/workspace/SKILL.md`'s `clone` section (steps 1–2),
      add: when the resolved configuration declares `workspaces_root`, a
      dest-less clone resolves its destination to
      `<workspaces_root>/<derived-name>`, and an explicit dest resolving
      outside the declared root is refused before cloning with an error
      naming the dest, the declared root, and `workspaces_root`; undeclared
      key leaves destination resolution as today. Update the `Ending`
      section's `clone` line to mention the new refusal cause.

## 6. Ship gate

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` from
      `0.6.187` to `0.6.188` (repo convention: every `plugins/s/` change
      bumps in the same PR).
- [x] 6.2 [req: *] Run the full engine suite exactly as CI does —
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v` —
      and confirm it passes with no `textual` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 114 | 29.5k |
| Read | 19 | 1.7k |
| Edit | 20 | 1.5k |
| (no tool) | 0 | 451 |
| Agent | 2 | 19 |
| Monitor | 1 | 3 |
| ToolSearch | 1 | 2 |
| **Total** | 157 | 33.2k |
