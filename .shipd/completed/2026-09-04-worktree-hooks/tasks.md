## 1. Engine worktree script

- [x] 1.1 [req: engine-worktree-create, post-worktree-execution] Add
      `plugins/s/skills/build/tests/test_worktree_engine.py` covering the
      create path in a temp git repo: fresh create runs two configured
      scripts in order with cwd = the new worktree and env
      `SHIPD_WORKTREE`/`SHIPD_ROOT`/`SHIPD_CHANGE`; reuse of an existing
      worktree skips the scripts; a failing middle script stops the chain,
      exits `3`, and leaves the worktree on disk; `post-worktree-scripts: 42`
      fails naming the key with no worktree created; no key configured means
      create succeeds with no script run; `remove`/`prune-branches` arguments
      pass through to `worktree.sh` (assert via a stub `worktree.sh` on the
      test's script dir or by observing the real refusal exit `2`). Run it
      and observe it fail — `worktree.py` does not exist yet.
- [x] 1.2 [req: engine-worktree-create, post-worktree-execution] Add
      `plugins/s/skills/build/scripts/worktree.py` (stdlib-only): dispatch
      first argument (`remove`/`prune-branches` -> subprocess `worktree.sh`
      verbatim with exit passthrough, `hooks` -> the verbs of task 1.4, else
      create path with optional `--fresh` and `--root DIR` defaulting to
      cwd); create path validates `post-worktree-scripts` via
      `spec_common.resolve_config` before any git mutation, records whether
      `.worktrees/<name>` pre-exists, runs `worktree.sh` with cwd = root and
      inherited output, and on success runs the hooks only for a
      fresh/attached worktree: announce `post-worktree: running <item>`, run
      each via `subprocess.run(item, shell=True, cwd=<worktree>)` with the
      extended env, stop on first non-zero with the failing item and exit
      `3`. Confirm the 1.1 create-path tests pass.
- [x] 1.3 [req: worktree-hooks-verbs] Extend
      `plugins/s/skills/build/tests/test_worktree_engine.py` with the hooks
      verbs: `hooks add` creates file/key preserving unrelated keys
      (2-space-indented JSON, trailing newline); exact duplicate refused
      non-zero; `hooks list` prints index + item + declaring config path and
      `--json` emits the same machine-readably; `hooks remove <index>` and
      `hooks remove <item>` delete exactly one entry; `hooks run` executes
      the effective list in cwd with the same stop-on-failure exit `3`. Run
      and observe the new tests fail.
- [x] 1.4 [req: worktree-hooks-verbs] Implement the `hooks` verb family in
      `plugins/s/skills/build/scripts/worktree.py`: `list [--json]` from
      `spec_common.resolve_config` provenance, `add <item>` /
      `remove <item-or-index>` editing `<root>/.shipd-config.json` only
      (warn on stderr when the add shadows an outer layer's declared list),
      `run` executing the effective list with cwd = root. Confirm all 1.3
      tests pass.

## 2. Binary verb

- [x] 2.1 [P2] [req: cli-dispatch] Extend
      `plugins/s/skills/build/tests/test_shipd_cli.py`: the `shipd --help`
      banner lists `worktree` among the verbs, and `shipd worktree` with no
      trailing arguments prints `worktree.py`'s own usage (not the shipd
      banner) and exits non-zero. Run and observe the new tests fail.
- [x] 2.2 [P3] [req: cli-dispatch] Add the `worktree` verb to
      `plugins/s/bin/shipd`: banner line, and delegation via the existing
      `os.execv` table to `python3 worktree.py` with trailing arguments
      verbatim. Confirm the 2.1 tests pass.

## 3. Autopilot create path

- [x] 3.1 [P2] [req: engine-worktree-create] Extend
      `plugins/s/skills/build/tests/test_autopilot.py`: the member worktree
      creation invokes `worktree.py` (via `sys.executable`) with the member
      slug instead of `worktree.sh` directly; the stale-reclaim `remove`
      invocation still uses `worktree.sh`. Run and observe the new
      assertions fail.
- [x] 3.2 [P3] [req: engine-worktree-create] In
      `plugins/s/skills/build/scripts/autopilot.py`, add a `WORKTREE_PY`
      constant beside `WORKTREE_SH` and switch the create invocation at the
      member-delivery step to `[sys.executable, WORKTREE_PY, slug]`, leaving
      the two `remove` invocations on `WORKTREE_SH`. Confirm 3.1 passes.

## 4. Skill and harness body

- [x] 4.1 [P2] [req: worktree-hooks-setup-flow, worktree-hooks-browse-remove]
      Add `plugins/s/skills/worktree-hooks/SKILL.md`: frontmatter description
      per the sibling skills; flows exactly as the `shipd-worktree-hooks`
      delta requirements state — author `<content-dir>/hooks/<slug>.sh`
      (resolve the directory name from `spec_status.py config-show`'s `dir`,
      repo-local regardless of `store_root`), `chmod +x`, register the
      repo-relative path via `shipd worktree hooks add` (binary resolved as
      PATH `shipd`, else `${CLAUDE_PLUGIN_ROOT}/bin/shipd`), verify via
      `hooks list`; direct command-line registration for one-liners; list
      flow flags dangling script paths; removal confirms before
      `hooks remove` and offers deleting an authored script file.
- [x] 4.2 [P3] [req: worktree-hooks-setup-flow] Add
      `plugins/s/harness/bodies/worktree-hooks.md` following the existing
      body grammar (`<!-- description: ... -->` first line,
      `<!-- include:preamble -->`, numbered engine-verb steps mirroring
      4.1's flows); confirm
      `plugins/s/skills/build/tests/test_harness_bodies.py` and
      `test_harness_generate.py` still pass with the new body enumerated.

## 5. Invocation-site and doc switch

- [x] 5.1 [P2] [req: change-worktree-isolation] Switch worktree *creation*
      invocations from `worktree.sh <name>` to
      `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree <name>` (flags preserved,
      `remove`/`prune-branches` references untouched) in:
      `plugins/s/skills/build/SKILL.md`, `plugins/s/skills/plan/SKILL.md`,
      `plugins/s/skills/epic/SKILL.md`,
      `plugins/s/skills/research/SKILL.md`,
      `plugins/s/skills/autopilot/SKILL.md`,
      `plugins/s/skills/initiative/SKILL.md`, and the matching harness
      bodies `plugins/s/harness/bodies/{build,plan,epic,research,autopilot,
      initiative}.md`.
- [x] 5.2 [P2] [req: change-worktree-isolation] Update `AGENTS.md`'s Workflow
      section: worktree creation is
      `plugins/s/bin/shipd worktree <change>` (running any configured
      `post-worktree-scripts`); the guarded `remove`, `prune-branches`, and
      `epic-close --fresh` guidance keeps naming `worktree.sh` verbs through
      the same front door or directly, unchanged in behavior.

## 6. Version and verification

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.6.173` -> `0.6.174`.
- [x] 6.2 [req: *] Run the full engine suite
      `python3 -m pytest plugins/s/skills/build/tests/ -q` (no `textual`
      installed) and confirm it passes; then create a throwaway change
      worktree via `plugins/s/bin/shipd worktree tmp-hook-probe` in a scratch
      clone with a configured echo hook, observe the hook output and exit
      `0`, and remove the probe worktree with
      `plugins/s/skills/build/scripts/worktree.sh remove tmp-hook-probe`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 155 | 29.6k |
| Edit | 28 | 9.4k |
| (no tool) | 0 | 6.9k |
| Read | 15 | 2.1k |
| SendMessage | 2 | 1.4k |
| Agent | 2 | 680 |
| ToolSearch | 1 | 524 |
| Write | 4 | 14 |
| **Total** | 207 | 50.6k |
