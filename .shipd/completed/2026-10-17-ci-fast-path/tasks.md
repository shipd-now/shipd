## 1. Classifier

- [x] 1.1 [req: ci-scope-classifier] Create `tools/tests/test_ci_scope.py` (stdlib unittest, load `tools/ci_scope.py` by path like `test_port.py`) with cases from the delta scenarios: fast epic/research/docs paths, mixed, verified, top-level docs, empty list, `..` path, push event, git failure (bad base ref). Run it and observe it fail.
- [x] 1.2 [req: ci-scope-classifier] Create `tools/ci_scope.py` with constant `ALLOWED_PREFIXES = (".shipd/epics/", ".shipd/research/", ".shipd/docs/")` and `classify(paths)` returning a bool, failing closed per the plan.
- [x] 1.3 [req: ci-scope-classifier] In `tools/ci_scope.py` add `changed_paths(base, head)` running `git diff --name-only --no-renames -z base...head` and a `main` taking `--event`, `--base`, `--head`, `--github-output`; print `fast=true|false` with a reason, append the `fast=` line to the output file, always exit 0. Confirm 1.1 passes.

## 2. Workflow

- [x] 2.1 [req: ci-fast-path-workflow] Add to `tools/tests/test_ci_scope.py` a structural test reading `.github/workflows/ci.yml` as text: a step with `id: scope` exists, the job name is `ci`, every step whose body has `unittest discover`, `pip install`, or `difft` carries `if: steps.scope.outputs.fast != 'true'`, and the steps named `Lint master spec library`, `Lint in-flight changes`, `Lint docs`, `Shell syntax checks`, `Guard the plugin version` carry no `scope` guard. Run it and observe it fail.
- [x] 2.2 [req: ci-fast-path-workflow] In `.github/workflows/ci.yml` insert, after `Set up Python`, a step `Classify changed paths` with `id: scope` running `python3 tools/ci_scope.py --event "${{ github.event_name }}" --base "origin/${{ github.base_ref }}" --head HEAD --github-output "$GITHUB_OUTPUT"`.
- [x] 2.3 [req: ci-fast-path-workflow] In `.github/workflows/ci.yml` add `if: steps.scope.outputs.fast != 'true'` to every `unittest discover` step, `Install third-party deps (board tui)`, and `Install difftastic for the review engine`. Leave `Lint docs` directly after `Lint in-flight changes`.

## 3. Library lint covers research and docs

- [x] 3.1 [req: research-report-validation, docs-document-validation] In `plugins/s/skills/build/tests/test_spec_lint.py`, rewrite `test_library_lint_ignores_research_files` and `test_library_lint_ignores_docs_files` into `test_library_lint_checks_research_files` and `test_library_lint_checks_docs_files` (an untitled file now yields a finding naming the file), and add a test that a library with titled reports and docs, or with neither folder, lints clean. Update the nearby comments and the class docstrings that say library linting never walks these folders. Run them and observe them fail.
- [x] 3.2 [req: research-report-validation, docs-document-validation] In `plugins/s/skills/build/scripts/spec_lint.py` `lint_library`, after the epics loop, call `lint_research(root, slug, errors)` for each `research/<slug>/` holding `report.md` and `lint_docs(root, slug, errors)` for each `docs/<slug>/` holding `doc.md`; skip absent folders and slug dirs without the file. Update `lint_library`'s docstring and the module header lines that say these folders are not walked.
- [x] 3.3 [req: research-report-validation, docs-document-validation] Run `python3 plugins/s/skills/build/scripts/spec_lint.py` from the repo root and confirm exit 0 on the real tree; run `python3 -m unittest discover -s plugins/s/skills/build/tests -v` and confirm it passes.

## 4. Plugin version

- [x] 4.1 [req: *] Set `version` in `plugins/s/.claude-plugin/plugin.json` to `0.6.316` (one patch above main, which carries `0.6.315`); confirm with `python3 plugins/s/skills/build/scripts/version_guard.py --base main --head HEAD`.

## 5. Verify

- [x] 5.1 [req: *] Run `python3 -m unittest discover -s tools/tests -v` and `python3 -m unittest discover -s plugins/s/skills/document/tests -v`; both must pass. Run the guard from 4.1 once more.
