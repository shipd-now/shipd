# Tasks — workspace-discovery

## 1. Discovery primitives

- [x] 1.1 [req: workspace-root-discovery, workspace-registry-loading] Add
      failing tests in `plugins/s/skills/build/tests/test_spec_common.py`
      (temp-dir fixtures): `find_workspace_root` resolves the nearest
      ancestor when nested markers exist; returns `None` with no marker in
      any ancestor; resolves the starting directory itself when it carries
      the marker; works from a non-git directory. `load_workspace` returns
      the parsed dict preserving an unrecognized `future-key`; raises
      `ConfigError` naming the file on invalid JSON, on a JSON-array top
      level, and on a missing file. Run and observe the new tests fail.
- [x] 1.2 [req: workspace-root-discovery, workspace-registry-loading] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `WORKSPACE_MARKER = os.path.join(".shipd", "workspace.json")`,
      `find_workspace_root(start)` (absolute-path upward walk via
      `os.path.dirname` until the path stops changing, returning the first
      directory whose marker is a file, else `None`), and
      `load_workspace(ws_root)` (read the marker file, parse with `json`,
      raise `ConfigError` naming the file when missing/unparseable/not an
      object, return the dict unchanged), per the plan's Implementation.
      Confirm the 1.1 tests pass.

## 2. Docs and version

- [x] 2.1 [P2] [req: workspace-root-discovery, workspace-registry-loading] Add
      a brief Workspace subsection to `am/README.md`: the
      `.shipd/workspace.json` marker-and-registry role, nearest-ancestor
      discovery from the repo, the forward-compatibility rule (unknown keys
      tolerated), and the caveat that a marker belongs only at the intended
      workspace root.
- [x] 2.2 [P2] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.2.1` → `0.2.2`.

## 3. Verification

- [x] 3.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py workspace-discovery`;
      everything green.
