# Tasks — unified-storage-config

## 1. Config foundation

- [x] 1.1 [req: config-file-discovery, layered-key-merge, content-dir-key] In `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests for `.shipd-config.json` resolution: chain walk to fs root, home layer appended when not in chain, defaults when no files, malformed file error naming its path, nearest-wins per top-level key, distinct keys combining, unknown keys preserved, `dir` default `.am`, `dir` override, separator-in-`dir` error.
- [x] 1.2 [req: config-file-discovery, layered-key-merge, content-dir-key] In `plugins/s/skills/build/scripts/spec_common.py`, add `CONFIG_FILENAME = ".shipd-config.json"`, `load_layered_config(start)` (list of (path, dict) nearest-first), `resolve_config(start)` (shallow per-key merge + provenance map), and `specs_dirname(config)` / `specs_dir(root)` (default `.am`, single-component validation). Leave the old `load_config` in place until 3.3. Tests from 1.1 pass.

## 2. Workspace re-rooting

- [x] 2.1 [req: workspace-root-discovery, workspace-registry-loading, workspace-initialization] In `test_spec_common.py`, add failing tests: root = nearest ancestor whose config declares `workspace`; config without `workspace` is not a root; registry = the `workspace` object (non-object errors naming `.shipd-config.json`); `init_workspace` creates the file with `{"workspace": {}}`, preserves existing keys, refuses under an existing workspace, errors on missing target.
- [x] 2.2 [req: workspace-root-discovery, workspace-registry-loading, workspace-initialization, initiative-brief-format, project-context-convention] In `spec_common.py`, rewrite `find_workspace_root`, `load_workspace`, `init_workspace`, `initiative_brief_path` (`<ws>/<content-dir>/initiatives/<slug>/brief.md`), and the project context path helper (`<ws>/<content-dir>/projects/<slug>/context.md`) on the config-file convention; delete `WORKSPACE_MARKER`. Tests from 2.1 pass.

## 3. Engine path sweep

- [x] 3.1 [req: master-spec-library-layout, per-change-artifact-layout, archive-of-applied-changes, epic-artifact-layout] Update the fixtures and path helpers in `plugins/s/skills/build/tests/` (all test modules and `fixtures/`) from `am/` to `.shipd/`; run the suite and observe the hardcoded-path failures.
- [x] 3.2 [req: master-spec-library-layout, per-change-artifact-layout, archive-of-applied-changes, epic-artifact-layout] Replace every `os.path.join(root, "am", ...)` in `spec_status.py`, `spec_lint.py`, and `spec_merge.py` with `sc.specs_dir(root)`-based helpers, and update the `TASKS`/`LOCK` paths in `claim_task.sh` to `.shipd/planned/`; suite from 3.1 passes. Then create a transitional worktree-root symlink `ln -s am .am` so task coordination and repo-tree engine calls keep working until task 8.1 replaces it (never committed — 8.1 removes it).
- [x] 3.3 [req: theme-vocabulary-config, plan-metadata-validation] In `test_spec_lint.py`, add failing tests: theme vocabulary read from the resolved config's `valid_themes` (declared in a fixture `.shipd-config.json`), any kebab theme accepted when undeclared, malformed config error naming `.shipd-config.json`; then point the theme lookup in `spec_lint.py` at `resolve_config` and delete `load_config` and its `am/config.json` path from `spec_common.py`. Tests pass.
- [x] 3.4 [req: initiative-lint-mode, workspace-lint-mode, initiative-reference-resolution] In `test_spec_lint.py`, update the workspace-dependent tests to the config-file convention (briefs under `<ws>/.shipd/initiatives/`, registry findings naming `.shipd-config.json`, reference-resolution expected paths); adjust `spec_lint.py` messages accordingly. Tests pass.

## 4. New status verbs

- [x] 4.1 [req: config-show-verb, epic-set-initiative-verb] In `test_spec_status.py`, add failing tests: `config-show` prints per-key provenance, the content dir, the workspace root or a none-note, exits zero on defaults-only; `epic-set-initiative` writes/replaces exactly one `Initiative:` line preserving other header metadata and body, and errors on an unknown epic or non-kebab value.
- [x] 4.2 [req: config-show-verb, epic-set-initiative-verb] Implement both verbs in `plugins/s/skills/build/scripts/spec_status.py`. Tests from 4.1 pass.

## 5. spec_emit.py

- [x] 5.1 [req: staged-emission] Add `plugins/s/skills/build/tests/test_spec_emit.py` with failing tests: clean staged change installs to the resolved `planned/<name>/`; invalid staged change prints findings, exits non-zero, leaves no directory; existing destination refused without `--replace` and replaced with it; `initiative`/`epic` modes install to resolved paths with the same remove-on-failure rule.
- [x] 5.2 [req: staged-emission] Implement `plugins/s/skills/build/scripts/spec_emit.py` (stdlib-only): copy staged content to the resolved destination, run `spec_lint`'s change/initiative/epic checks in-process, remove installed content and exit non-zero on findings. Tests from 5.1 pass.
- [x] 5.3 [req: mediated-read-verb] In `test_spec_status.py`, add failing tests for `cat change|verified|epic|initiative <slug>`: `--- <relpath>` separator per file, change mode prints plan.md + every delta + tasks.md, unknown names exit non-zero; then implement `cat` in `spec_status.py`. Tests pass.

## 6. Statusline and repo state

- [x] 6.1 [req: current-spec-selection] In `test_spec_status.py` and `test_statusline.py`, update state-path expectations to `<content-dir>/state.json` (`.shipd/state.json` default); adjust `STATE_DIRNAME` usage in `spec_status.py` to derive from `specs_dirname`. Tests pass.
- [x] 6.2 [req: statusline-rendering] Update `plugins/s/integrations/statusline.sh` to read `.shipd/planned/` and `.shipd/state.json` (literal default, no config resolution, still bash 3.2 POSIX); update `test_statusline.py` fixtures, including a renamed-dir repo rendering nothing. Tests pass.

## 7. Build reporting

- [x] 7.1 [req: persistent-build-log, user-configuration-file] In `test_build_report.py`, add failing tests: log entries land under the resolved build log dir (default `~/.shipd/builds/`), created on demand; settings read from the resolved config's `build` key with defaults when absent; no `~/.shipd/` path read or written.
- [x] 7.2 [req: persistent-build-log, user-configuration-file] In `plugins/s/skills/build/scripts/build_report.py`, replace the `~/.shipd` config/log code with `resolve_config`'s `build` key and `~/.shipd/builds/`; update the committed example config it documents. Tests from 7.1 pass.

## 8. Repo migration

- [x] 8.1 [req: master-spec-library-layout] From the worktree root: remove the transitional symlink from 3.2 (`rm .am`), then `git mv am .am`; write `.shipd-config.json` at the repo root declaring `valid_themes` from the old `am/config.json`; delete `.shipd/config.json`; add `.shipd/state.json` to `.gitignore`.
- [x] 8.2 [req: per-change-artifact-layout] Update `evals/run.py` (change discovery and grading assertions) and every `evals/cases/*/fixture/` layout from `am/` to `.shipd/`; run `uvx pytest evals/tests/ -q` and fix until green.
- [x] 8.3 [req: spec-library-path-notation] Repo-wide grep for `\.shipd|am/planned|am/verified|am/completed|am/epics|am/config` and fix every live reference outside `.shipd/completed/` and `openspec/` (frozen archives stay untouched): `AGENTS.md`, `scripts/worktree.sh` if hit, `.claude/settings.json`, CI workflow.

## 9. Skill docs and plugin

- [x] 9.1 [req: engine-mediated-skill-access, silent-lean-emission, missing-layout-guard] Rewrite `plugins/s/skills/plan/SKILL.md` and its `references/emission.md` to stage artifacts and install via `spec_emit.py change`, scaffold via the resolved content dir, and reference `.shipd/README.md`.
- [x] 9.2 [req: engine-mediated-skill-access, initiative-workflow-skill, initiative-attachment] Rewrite `plugins/s/skills/initiative/SKILL.md` (brief authoring via `spec_emit.py initiative`, attachment via `epic-set-initiative`) and `plugins/s/skills/workspace/SKILL.md` (config-file marker wording).
- [x] 9.3 [req: engine-mediated-skill-access] Sweep the remaining skill docs — `plugins/s/skills/{build,epic,status,onboard}/` including onboard chapters and build references — replacing every literal `am/` storage path with engine-verb usage or `.shipd/` where illustrative; update the layout examples inside `.shipd/README.md` (renamed by 8.1).
- [x] 9.4 [req: readme-documents-spec-engine] Update `README.md` per the project-readme delta and bump `plugins/s/.claude-plugin/plugin.json` to `0.3.0`.

## 10. Verification

- [x] 10.1 [req: *] Migrate the live workspace at `~/projects`: create `~/projects/.shipd-config.json` with the `workspace` section from `.shipd/workspace.json`, move `initiatives/` to `.shipd/initiatives/`, delete `.shipd/`; verify with `workspace-show` and `--initiative better-onboarding`.
- [x] 10.2 [req: *] Full barrier: run the unittest suite (`python3 -m unittest discover -s plugins/s/skills/build/tests`), the library lint on the migrated tree, `config-show` at repo root and `~/projects`, and a repo-wide grep proving no live `.shipd` or hardcoded `am/` storage path remains.
