## 1. Constant and helper

- [x] 1.1 [req: brand-subject-helper] In `plugins/s/skills/build/tests/test_spec_common.py`, add a `BrandSubjectTest` class covering every `brand-subject-helper` scenario (prefix once, idempotent with and without the trailing space, `fixup!`/`squash!`/`amend!` untouched, empty and whitespace subjects untouched) and asserting `BRAND_PREFIX == "☕ Shipd: "`. Run it and observe it fail.
- [x] 1.2 [req: brand-subject-helper] In `plugins/s/skills/build/scripts/spec_common.py`, add `BRAND_PREFIX = "☕ Shipd: "` and `brand_subject(subject)` exactly as the plan's Implementation states, beside `resolve_pr`. Add no config key. Confirm task 1.1 passes.

## 2. Brand script and hook

- [x] 2.1 [req: brand-script-verbs, commit-brand-hook-install] Add `plugins/s/skills/build/tests/test_brand.py` (private `HOME`, temp git repo with identity, as `test_worktree_engine.py` sets up) covering the `subject` verb, `commit-msg` in a linked worktree under the repo's .worktrees directory vs the root checkout, a `#` comment line kept, `install-hook` writing a marked 0755 hook, refreshing a marked hook, skipping a foreign hook and a `core.hooksPath` with the `note: commit branding skipped — ` line, a real `git commit` in a worktree getting branded, and a hook whose `brand.py` path is missing letting the commit through unbranded. Run it and observe it fail.
- [x] 2.2 [req: brand-script-verbs, commit-brand-hook-install] Create `plugins/s/skills/build/scripts/brand.py` (stdlib only, imports `spec_common` from its own directory, argparse verbs `subject`, `commit-msg`, `install-hook`) implementing the plan's verbs, hook file, and install rules, using `spec_common.brand_subject` and never spelling the prefix itself. Confirm task 2.1 passes.

## 3. Wire the call sites

- [x] 3.1 [req: commit-brand-hook-install] In `plugins/s/skills/build/tests/test_worktree_engine.py`, add to `CreatePathTest` the scenarios "Create installs the hook and a worktree commit is branded" and "A foreign hook is never clobbered". Run them and observe them fail.
- [x] 3.2 [req: commit-brand-hook-install] In `plugins/s/skills/build/scripts/worktree.py` `cmd_create`, after `worktree.sh` returns 0 and before the post-worktree scripts, import `brand` and call its install function for `root`, printing its line; ignore its outcome for the exit code. Confirm task 3.1 passes.
- [x] 3.3 [req: brand-engine-commits] In `plugins/s/skills/build/tests/test_spec_common.py`, add the "store auto-commit is branded" scenario against `wiki_autocommit`; then update the exact-subject expectations in `test_spec_common.py` (the `subject` compared near line 4759), `test_spec_status.py` (lines 4644, 4652, 4657, 4790, 5138), `test_spec_emit.py` (line 798), and `test_wiki_remove.py` (line 173) to the `☕ Shipd: ` branded form. Run them and observe them fail.
- [x] 3.4 [req: brand-engine-commits] In `plugins/s/skills/build/scripts/spec_common.py` `wiki_autocommit`, commit with `brand_subject(subject)`. Confirm task 3.3 passes.
- [x] 3.5 [req: pr-title-render] In `plugins/s/skills/pr/tests/test_pr_title.py`, add the "printed title carries the brand once" scenario to `CliTest` and update the existing CLI expectations (lines 80 to 100) to the branded form. Run them and observe them fail.
- [x] 3.6 [req: pr-title-render] In `plugins/s/skills/pr/scripts/pr_title.py` `main`, apply `spec_common.brand_subject` to the rendered title before printing it, and mention the brand in the module docstring. Confirm task 3.5 passes.
- [x] 3.7 [req: brand-engine-commits] In `plugins/s/skills/build/tests/test_brand.py`, add the "Skill commit lines use the helper" scenario. Then in `plugins/s/skills/gate/SKILL.md` (both `git commit -m` lines) and `plugins/s/skills/epic/SKILL.md` (the store amend line), wrap each subject as `"$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/brand.py" subject "<subject>")"`, keeping each file's line count. Confirm the scenario passes.

## 4. Docs and version

- [x] 4.1 [req: brand-engine-commits, pr-title-render] In `.shipd/README.md`'s `### PR title — the \`pr\` key` section, add one paragraph saying every title `/s:pr` renders, and every commit shipd writes in a shipd worktree or through the engine, starts with `☕ Shipd: `, which is not configurable; a repository with its own `commit-msg` hook or a `core.hooksPath` gets a note and unbranded commits. In `AGENTS.md`, change the store amend sentence's subject to say it carries the `☕ Shipd: ` brand.
- [x] 4.2 [req: *] Set `version` in `plugins/s/.claude-plugin/plugin.json` to one patch above the version on `main` at build time.
- [x] 4.3 [req: *] Run the full suite with `python3 -B -m unittest discover` over `plugins/s/skills` (grep the output for `OK` or `FAILED`) and confirm it is green.
