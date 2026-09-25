# ignore-local-state
Status: verified

## Idea

Enforce the git-ignore the spec already mandates for the engine's local state files, so sibling epic members stop conflicting on `.shipd/state.json`.

### Motivation

Every epic member build rewrites the one key in `.shipd/state.json` and commits it with `git add -A`, so the second member's pull request conflicts on that line and autopilot stalls until a human resolves it, as on talky pull request 91. The `statusline` capability already requires the file to be git-ignored, but neither `init` nor `use` ever writes the ignore rule, and a repo that never added it by hand tracks the file forever.

### Details

- One engine helper in `spec_common.py` computes the two local-state ignore rules (`<content-dir>/state.json`, `<content-dir>/autopilot/`), appends the absent ones to the root `.gitignore`, and untracks either path from the git index when it is tracked, keeping the file on disk.
- `use` calls the helper before it records the selection, so the next build in any repo self-heals and the fix travels in that member's pull request.
- `init` calls the helper and reports one `ignored`/`exists` line per rule and one `untracked` line per path, so a fresh repo never tracks the files.
- `shipd doctor` gains a report-only `local-state` check after `store-sync` that warns when either path is tracked or either rule is missing, naming `shipd init`.

Affected capabilities: `statusline` (modified), `spec-status` (modified), `shipd-cli` (modified). Impact: `plugins/s/skills/build/scripts/spec_common.py`, `plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_spec_common.py`, `plugins/s/skills/build/tests/test_spec_status.py`, `plugins/s/skills/build/tests/test_shipd_cli.py`, `docs/getting-started.md`, `docs/cheatsheet.md`, `plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to the shape of `state.json`: it keeps the single `current_spec` key. A keyed object with timestamps still conflicts on adjacent insertions and has no meaning on `main`.
- No relocation of the selection to the workspace root: the selection is per checkout, and the workspace root is itself a git repository that tracks its `.shipd/`.
- No change to `statusline.sh`, which keeps reading `<checkout>/.shipd/state.json`.
- No automated remedy under `doctor --fix`: the doctor-verb requirement limits automated remedies to local tooling, so `local-state` stays report-only.
- No change to the master merge engine or to the heartbeat writers.
- No repair of pull requests already open before the fix lands: their branches still modify the file and meet one modify/delete conflict against a `main` that untracked it.

## Implementation

- **The helper lives beside `ensure_gitignore_line`.** Add to `plugins/s/skills/build/scripts/spec_common.py`, directly after `ensure_gitignore_line` (line 1583): `local_state_rules(root)` returning `[<rel>/state.json, <rel>/autopilot/]` where `<rel>` is `os.path.relpath(specs_dir(root), root)` with forward slashes, or `[]` when `specs_dir(root)` is not inside `root` (an external store); `tracked_local_state(root)` returning the paths `git -C <root> ls-files -z -- <rel>/state.json <rel>/autopilot` prints, or `[]` when the root has no `.git` entry, `git` is missing, or the command fails; and `ensure_local_state_untracked(root)` returning `(appended, untracked)`, where `appended` is the list of `(rule, bool)` results of `ensure_gitignore_line` per rule and `untracked` is the list of paths it removed with `git -C <root> rm --cached -r -q --ignore-unmatch -- <paths>`. The helper never raises on git failure: it swallows `OSError` and a non-zero exit and reports only what happened. Rejected: a `.gitattributes` union merge driver, because the file must not be committed at all, and rejected: relocating the file to `~/.shipd`, because `statusline.sh` reads it from the checkout and must stay POSIX shell with no Python.
- **A checkout is a `.git` directory or a `.git` file.** The untrack step runs only when `os.path.exists(os.path.join(root, ".git"))`, which covers a main checkout and a linked worktree alike; `_is_main_checkout` in `spec_status.py` stays untouched.
- **`use` heals silently on stdout.** In `spec_status.cmd_use`, call `sc.ensure_local_state_untracked(root)` before `write_current`, print `untracked <path>` for each untracked path to stderr, and keep stdout as the change name alone. The ignore append prints nothing.
- **`init` reports every step.** In `spec_status.cmd_init`, after `_install_config_sample` and before `stamp_schema_marker`, call the helper and print `ignored <rule>` or `exists <rule>` per rule, then `untracked <path>` per path. The existing `exists`/`created` lines and the summary line are unchanged, so `TestInitVerb.test_fresh_root_gets_the_full_layout` keeps asserting the first four lines and the last line.
- **The doctor check is read-only and injectable.** In `plugins/s/bin/shipd`, add `check_local_state(root)` after `check_store_sync`: load the engine; when `sc.local_state_rules(root)` is empty return `("ok", "local-state", "content directory lives outside the repository — skipped")`; when the root has no `.git` entry return `("ok", "local-state", "not a git checkout — skipped")`; when `sc.tracked_local_state(root)` is non-empty return `warn` naming the tracked paths and `run \`shipd init\` to ignore and untrack local state`; when any rule is absent from `.gitignore` (probed through a new `sc.gitignore_carries(root, line)` predicate that `ensure_gitignore_line` also uses for its presence test) return `warn` naming the missing rules and the same remedy; otherwise `ok` naming both rules. Insert `check_local_state(root)` into `default_checks` directly after `check_store_sync(root)` and before `check_gh()`, the one slot in the roster no requirement claims with a "directly after" sentence (`wiki` claims the slot after `schema`, `store` the slot after `wiki`, `difft` the slot after `gh`, and the three GitHub checks the slots after `statusline`). Add `"local-state"` to `REMEDY_SURFACES` with the text `the git-ignore of the local selection state — run \`shipd init\` to ignore and untrack it`; `AUTOMATED_REMEDIES` is unchanged.
- **Tests use real temporary git repositories.** `git` is required by the preflight and present in CI, so the new tests run `git init`, `git add`, and `git commit` in temp roots with `user.name`/`user.email` set on the command line, and assert tracking through `git ls-files`.
- **Docs and version.** `docs/getting-started.md` lists `local-state` after `wiki` in the check roster (the roster there omits `store` and `store-sync`); `docs/cheatsheet.md` extends the `init` row to say it also ignores and untracks the local state files. Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.234` to `0.6.235`.

Risk: `git rm --cached` on a path the user deliberately committed. Guard: the spec has always required the file to be git-ignored, the file stays on disk, and every untrack is reported on the verb's output.

## Readiness attestation

### Problem and motivation

Sibling epic members each commit a rewritten `.shipd/state.json`, so autopilot pull requests like talky 91 stop at a conflict a human must resolve, although the spec already requires the file to be git-ignored.

Evidence:

- Three-way `git merge-file` of talky base 9e680fb, main 7b5cf8c, and PR head f9f0b2a: `.shipd/state.json` exits 1 with a conflict on `current_spec` (`builder-ui` versus `form-detail-page`); `.shipd/verified/web-app/spec.md` exits 0.
- Capability `statusline`, requirement `current-spec-selection`: the state file "SHALL be git-ignored".
- `plugins/s/skills/build/scripts/spec_status.py:9` and `:228-229` document the file as git-ignored; `cmd_init` at `:546` writes no ignore rule.
- Talky tracks the file in 45 commits since 2026-09-17 and tracks ten `.shipd/autopilot/*-build-heartbeat.json` files; its `.gitignore` names neither.

### Scope and non-goals

In scope are one engine helper, the `use` and `init` verbs, one doctor check, their tests, and two docs pages; the file shape, the statusline reader, `--fix`, and the merge engine stay untouched.

Evidence:

- In scope: `spec_common.py:1583` (`ensure_gitignore_line`, the helper's neighbor), `spec_status.py:584` (`cmd_use`), `spec_status.py:546` (`cmd_init`), `plugins/s/bin/shipd:1108` (`default_checks`).
- Out of scope: `plugins/s/integrations/statusline.sh:229-231` reads `$workspace/.shipd/state.json` unchanged; `spec_merge.py:205-235` rewrites masters in stable order and is not edited; `AUTOMATED_REMEDIES` at `plugins/s/bin/shipd:1156` is unchanged per capability `shipd-cli` requirement `doctor-verb`.

### Affected capabilities and files

Three capabilities and nine files are affected, because the ignore is enforced at the writer, the scaffolder, and the preflight, each with tests and docs.

Evidence:

- Capability `statusline`: requirement `current-spec-selection` (base e9dbeb8565ec, from `spec_status.py base-hash`).
- Capability `spec-status`: requirement `layout-init-verb` (base 11578bc7ec66, from `spec_status.py base-hash`).
- Capability `shipd-cli`: added requirement `doctor-local-state-check`, following `doctor-schema-check` and `doctor-wiki-check` as additive check requirements.
- Files: `plugins/s/skills/build/scripts/spec_common.py`, `plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_spec_common.py`, `plugins/s/skills/build/tests/test_spec_status.py`, `plugins/s/skills/build/tests/test_shipd_cli.py`, `docs/getting-started.md:52-54`, `docs/cheatsheet.md:86`, `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `spec_status.py init --root <fresh git repo>` exited 0, printed the four `created` directory lines, the sample line, and the summary, and left no `.gitignore`.
- Runnable premise: `spec_status.py --root <repo> use demo` exited 0 printing `demo`, and `git add -A && git status --short` then showed `A  .shipd/state.json`.

### No open task-shaping decision

Every task-shaping decision is settled by investigation; none remain.

Evidence:

- Location of the selection (repo-local, not the workspace root): settled by `current-spec-selection` and by the workspace root at `/Users/mikkelbergmann/projects/workspaces` being a git repository whose `git ls-files .shipd` tracks the wiki.
- Mechanism (ignore plus untrack, not a keyed object with timestamps): settled by the merge reproduction, since the file conflicts on adjacent insertions regardless of shape.
- Remedy scope (report-only under `--fix`): settled by `doctor-verb`, which limits automated remedies to `textual`, `difft`, and `statusline`.
- Check position (after `store-sync`, before `gh`): settled by the master's ordering claims, which leave that slot as the only unclaimed one among the repo-local checks.
