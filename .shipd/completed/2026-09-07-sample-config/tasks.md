# Tasks — sample-config

## 1. Recognized-key registry and full-coverage sample

- [x] 1.1 [req: config-sample-coverage] Add
      `plugins/s/skills/build/tests/test_config_sample.py`: load
      `plugins/s/skills/build/references/shipd.config.example.json` with strict
      `json.load` and assert (a) it is a JSON object; (b) the set of top-level
      keys it documents — declared keys plus the `<key>` parsed from each
      `"// <key>"` entry, the bare `"//"` header entry excluded — equals
      `spec_common.RECOGNIZED_CONFIG_KEYS` exactly, both directions; (c) every
      module-level `*_KEY` string constant in `spec_common` is a member of
      that registry; (d) each declared (non-comment) value equals its built-in
      default (the `build` object compared against
      `build_report.DEFAULT_BUILD_CONFIG`). Run the module with
      `python3 -m unittest` and observe it fail — the registry constant does
      not exist yet and the sample is incomplete.
- [x] 1.2 [req: config-sample-coverage] In
      `plugins/s/skills/build/scripts/spec_common.py`, near the layered-config
      constants (around `CONFIG_FILENAME`), add `RECOGNIZED_CONFIG_KEYS`: a
      tuple of the 13 recognized top-level key names — `autonomous-pipeline`,
      `build`, `clone_sources`, `completed_retention_days`, `dir`,
      `guardrails`, `memory_dir`, `post-worktree-scripts`, `pr-mode`,
      `store_root`, `valid_themes`, `wiki_base`, `workspace` — with a comment
      naming it the authoritative registry that is extended, together with the
      example JSON, whenever a new top-level key is recognized.
- [x] 1.3 [req: config-sample-coverage] Rewrite
      `plugins/s/skills/build/references/shipd.config.example.json` as the
      full-surface reference: rework the `"//"` header from a /s:build-scoped
      note to a general "copy to .shipd-config.json and edit; all keys
      optional; layered nearest-wins resolution" note; keep the existing
      `"// autonomous-pipeline"`, `"// pr-mode"`, and `"// guardrails"`
      entries (their content is bound by verified requirements); add
      `"// <key>"` entries with a one-or-two-line purpose-and-default comment
      for `dir` (default `.shipd`), `completed_retention_days` (default 30;
      `0`/`null` disable), `store_root` (external store; `~` expands, relative
      resolves against the declaring file), `wiki_base` (absolute path, no
      default), `memory_dir` (default `~/.shipd-memory`), `valid_themes`
      (lint's `Theme:` vocabulary), `workspace` (marks a workspace root;
      `projects`/`focus` registry), `post-worktree-scripts` (ordered command
      list run after worktree creation; register via `shipd worktree hooks
      add`), and `clone_sources` (directories the workspace sync planner
      probes); keep the `build` object's four declared defaults and add,
      inside the `build` object, one `"// <subkey>"` comment entry each for
      `design_dir` (default `~/.shipd/designs`), `video_dir` (default
      `~/.shipd/video`), `video_asr` (default `parakeet`), `video_vocabulary`
      (default `[]`), `video_max_frames` (default 24), `video_scene_floor`,
      and `video_cursor` (default `true`). Confirm the test from task 1.1 now
      passes.

## 2. init installs the sample

- [x] 2.1 [req: layout-init-verb] Extend `TestInitVerb` in
      `plugins/s/skills/build/tests/test_spec_status.py` with three tests:
      a fresh `init` installs `<content-dir>/shipd.config.example.json` with
      content identical to the plugin reference and prints
      `created .shipd/shipd.config.example.json` between the directory lines
      and the summary; a re-run against a root whose copy was modified leaves
      the file byte-for-byte unchanged and prints the matching `exists` line;
      and a missing source reference (patch the resolved source path, or run
      the script from a temp copy without `references/`) still creates the
      four directories, prints one stderr warning naming the probed source
      path, installs nothing, and exits `0`. Run them and observe them fail —
      `cmd_init` does not install the sample yet.
- [x] 2.2 [req: layout-init-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend `cmd_init`:
      resolve the source as
      `os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
      "references", "shipd.config.example.json")` (normalized); after the four
      directory lines, when nothing exists at
      `<content-dir>/shipd.config.example.json`, copy the source there and
      print `created <relpath>`; when any filesystem object exists there,
      touch nothing and print `exists <relpath>` (no trailing separator —
      it is a file); when the source is missing, print one stderr warning
      naming the probed path, skip installation, and leave the exit code
      unchanged; keep the schema-marker stamp and the
      `all shipd directories are ready` summary last. Confirm the tests from
      task 2.1 pass.
- [x] 2.3 [req: *] Run the full engine suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests`, and
      confirm it passes with no regression (notably the existing
      `TestInitVerb` line-position assertions).

## 3. Ship prep

- [x] 3.1 [req: *] Bump the plugin version from 0.6.185 to 0.6.186 in
      `plugins/s/.claude-plugin/plugin.json`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 92 | 14.6k |
| Monitor | 1 | 1.9k |
| Write | 2 | 1.8k |
| Agent | 2 | 393 |
| SendMessage | 1 | 389 |
| ToolSearch | 3 | 327 |
| Read | 10 | 325 |
| (no tool) | 0 | 257 |
| Edit | 8 | 97 |
| TaskStop | 1 | 57 |
| **Total** | 120 | 20.2k |
