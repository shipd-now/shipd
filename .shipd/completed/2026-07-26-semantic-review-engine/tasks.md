## 1. semdiff diff engine

- [x] 1.1 [req: structural-diff, text-fallback] Add
      `plugins/s/skills/review/tests/test_semdiff_diff.py`: build a fixture
      git repo in a tempdir (initial commit, then a content edit, a
      whitespace-only edit, an untracked file, and a `feature` branch);
      assert working-tree mode lists the modified + untracked paths with
      kinds, filters the whitespace-only file, `main feature` resolves
      merge-base mode with after-content from the ref, `--linear` yields
      two-dot mode, and with difft absent (force via PATH) the output is
      `engine: "text"` with exit 0. Guard difft-dependent asserts with a
      skip when `difft` is missing. Run it and observe failure — semdiff
      does not exist yet.
- [x] 1.2 [req: structural-diff] Create
      `plugins/s/skills/review/scripts/semdiff.py` (stdlib-only, argparse
      subcommands) with the shared helpers (`run`, `have`, `die`,
      `in_git_repo`, `repo_root`), `resolve_endpoints`, `changed_paths`,
      `blob_at`, and the difft engine path of `cmd_diff` — difft JSON via
      tempfile pairs, whitespace-only filtering, hunk summarization,
      declaration-marker `signature_changes`, per-file/summary
      `engine: "difft"` stamps — porting the pasted automedifftool logic.
- [x] 1.3 [req: text-fallback] In the same `cmd_diff`, add the text engine:
      when `difft` is missing (or its JSON fails to parse for a file),
      parse `git diff` unified hunks for that file into the same entry
      shape with `engine: "text"`, matching declaration markers against
      added lines for `signature_changes`; never exit non-zero for a
      missing difft. Confirm `test_semdiff_diff.py` passes.

## 2. files, context, change bridge

- [x] 2.1 [req: cohort-grouping, reference-context] Add
      `plugins/s/skills/review/tests/test_semdiff_files_context.py`:
      cohort grouping over sample paths (api/tests/frontend rules, the
      shipd `skills` cohort for `plugins/*/skills/` paths, the `specs`
      cohort for content-dir artifact paths, top-level fallback) and
      `context` returning `git grep` matches plus the best-effort note in
      a fixture repo with `rg` masked from PATH. Observe failure first.
- [x] 2.2 [req: cohort-grouping] Implement `cmd_files` in `semdiff.py`:
      port the segment-aware COHORT_RULES and add the shipd rules —
      first path segment `plugins` with a `skills` segment → `skills`
      cohort; a leading content-dir segment (resolved via the engine
      config, default `.am`) → `specs` cohort.
- [x] 2.3 [req: reference-context] Implement `cmd_context` in
      `semdiff.py`: rg `--json` word-match with `--lang` glob mapping and
      `--path` scope, `git grep -n -w` fallback, and the fixed best-effort
      note in the JSON. Confirm `test_semdiff_files_context.py` passes.
- [x] 2.4 [req: change-bridge] Add
      `plugins/s/skills/review/tests/test_semdiff_change.py`: copy the
      build suite's sample fixture (`.shipd/` layout with a planned change)
      into a tempdir git repo; assert `semdiff change sample-change`
      reports deltas with scenario texts, task progress from checkbox
      states, empty lint findings, and plan.md impact files; assert an
      unknown change exits non-zero naming it. Observe failure first.
- [x] 2.5 [req: change-bridge] Implement `cmd_change` in `semdiff.py`:
      `sys.path`-insert `../../build/scripts` relative to `__file__`,
      import `spec_common` and `spec_lint`, resolve the content dir from
      the layered config, parse the change's delta specs (operation,
      capability, requirement id/text, scenarios) and `tasks.md`
      checkboxes, run the change lint in-process for findings, and extract
      backtick path-like tokens from `plan.md` as `impact_files`. Confirm
      `test_semdiff_change.py` passes.

## 3. doctor

- [x] 3.1 [req: doctor-provisioning] Add
      `plugins/s/skills/review/tests/test_semdiff_doctor.py`: doctor
      without `--fix` exits zero with git present and difft missing
      (recommended, not required) and non-zero with git masked from PATH;
      `_difft_target()` maps darwin/linux × arm64/x86_64 and returns None
      otherwise; install-dir selection prefers `$CLAUDE_PLUGIN_ROOT/bin`
      else `~/.local/bin`. No network in any test. Observe failure first.
- [x] 3.2 [req: doctor-provisioning] Implement `cmd_doctor` in
      `semdiff.py`: the DEPS table (git required; difft recommended with
      degrade-not-block wording; rg, gh optional) and the tiered `--fix`
      installer ported from the paste (brew → cargo → prebuilt release
      download into the install dir, chmod +x, PATH note). Confirm
      `test_semdiff_doctor.py` passes.

## 4. /s:review skill

- [x] 4.1 [req: review-skill, spec-aware-review] Author
      `plugins/s/skills/review/SKILL.md` (frontmatter name `review`,
      description with trigger phrases like "review my changes",
      "semantic review", "/s:review"): workflow of map-cohorts →
      structural diff → downstream impact via `context` → call-site value
      tracing (dead guards, comment drift) → findings by cohort with the
      high/medium/low rubric; semdiff invoked as `python3
      <plugin-root>/skills/review/scripts/semdiff.py`; spec-aware mode via
      `semdiff change` (named change, else auto-detect a sole planned
      change) with Met/Unmet/Can't-tell classification, unmet-as-high,
      task honesty, uncovered-code observations; the rendered report
      (effort score, `## Findings: ✅ Ship it` / `❌ Fix required` header,
      summary table with 🔴/🟠/🟡 dots, collapsible walkthrough, optional
      dark-mode-safe mermaid, numbered cohort findings, could-not-verify)
      and the `--json` machine mode; guardrails: two sanctioned emoji
      sites only, shipd-only naming, read-only, degrade via doctor
      (offer `--fix`, run only on user agreement), and the question
      rejection recovery rule carried by interactive am skills.

## 5. Wiring and verification

- [x] 5.1 [req: review-test-coverage] Add a `Run review test suite` step to
      `.github/workflows/ci.yml`: `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`.
- [x] 5.2 [req: review-skill] Bump `plugins/s/.claude-plugin/plugin.json`
      version 0.3.3 → 0.4.0 (new skill), and mention `/s:review` in
      `AGENTS.md`'s skill roster sentence alongside `/s:plan` and
      `/s:build`.
- [x] 5.3 [req: *] Verification barrier: run both unittest suites
      (`plugins/s/skills/build/tests`, `plugins/s/skills/review/tests`),
      `spec_lint.py` on the master library and this change, and exercise
      `semdiff diff main`, `files`, `context`, `change
      semantic-review-engine`, and `doctor` live in this worktree,
      confirming text-engine degradation on a difft-less machine.
