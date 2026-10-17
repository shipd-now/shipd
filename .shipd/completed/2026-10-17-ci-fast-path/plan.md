# ci-fast-path
Status: verified
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: 4ab8616826cf

## Idea

Let the required `ci` job skip its expensive test suites when a pull request touches only non-code planning content, while keeping the check name `ci` unchanged.

### Motivation

Authors of epic, research, and content-dir doc pull requests wait for the full engine, eval, review, and drive test suites although no test reads those files. A GitHub ruleset cannot vary required checks by path, so the saving has to live inside the single required `ci` job.

### Details

- Add `tools/ci_scope.py`, a stdlib-only classifier that reads the PR's changed paths and prints `fast=true` only when every path lies under `.shipd/epics/`, `.shipd/research/`, or `.shipd/docs/`.
- Make `spec_lint.py`'s library lint also validate every `.shipd/research/<slug>/report.md` and `.shipd/docs/<slug>/doc.md`, so the fast path is gated by shipd validation (Q4); amend `shipd-spec-lint` accordingly and bump the plugin version.
- Add `tools/tests/test_ci_scope.py` covering the classifier, the CLI, and a structural check of `ci.yml`.
- In `.github/workflows/ci.yml`, add a `Classify changed paths` step (id `scope`) and guard every test-suite step, the pip install, and the difftastic install with `if: steps.scope.outputs.fast != 'true'`.
- The version guard, spec library lint, in-flight lint, docs lint, and shell syntax checks keep running on every run, so an epic PR is still linted.

Affected capabilities: `ci-fast-path` (added); `shipd-spec-lint` (modified: `research-report-validation`, `docs-document-validation`). Impact: `tools/ci_scope.py`, `tools/tests/test_ci_scope.py`, `.github/workflows/ci.yml`, plus `plugins/s/skills/build/scripts/spec_lint.py`, `plugins/s/skills/build/tests/test_spec_lint.py`, `plugins/s/.claude-plugin/plugin.json`. `plugins/s/skills/build/scripts/spec_lint.py` and its tests also change (see Implementation), so the plugin version is bumped in the same PR.

### Non-goals

- No change to the job name `ci`, branch protection, or the `semantic-review` check.
- No fast path on push to `main`; that run always executes the full suite.
- No allowlisting of `.shipd/verified/`, `.shipd/planned/`, `.shipd/completed/`, top-level `docs/`, or any code, plugin, test, or workflow path.

## Implementation

- Allowlist is three content-dir prefixes: `.shipd/epics/`, `.shipd/research/`, `.shipd/docs/`. Rejected: also allowing `verified/` (tests read `.shipd/verified/*/spec.md` from the real tree) and top-level `docs/` (tests read `docs/customise.md`, `docs/pr-room.md`, and the review docs).
- The classifier fails closed: an empty path list, a path outside the allowlist, a path with a `..` segment or backslash, a non-PR event, or any git failure yields `fast=false` and exit 0, so a broken classifier costs time, never coverage.
- Interface: `classify(paths) -> bool`; `changed_paths(base, head) -> list` runs `git diff --name-only --no-renames -z base...head` (renames list both old and new paths); CLI `ci_scope.py --event E --base B --head H [--github-output FILE]` prints `fast=true|false` plus a one-line reason and appends the same `fast=` line to the output file. This mirrors `version_guard.py`'s three-dot diff.
- Script lives in `tools/` with tests in `tools/tests/`, which `ci.yml` already runs; a change to the script itself is not on the allowlist, so it runs the full suite.
- Lint steps stay unguarded, so `spec_lint.py` (which lints every epic) validates epic PRs on the fast path. The `Lint docs` step must stay directly after `Lint in-flight changes` (`test_docs_ci_gate.py`).
- `lint_library(root)` additionally calls `lint_research` for each `.shipd/research/<slug>/` holding `report.md` and `lint_docs` for each `.shipd/docs/<slug>/` holding `doc.md`; a missing directory or a slug dir without the file is skipped, so repos without them lint as before. Both existing requirements said library lint never walks those folders; they are MODIFIED and their two "Library lint ignores" scenarios are dropped. Every current report and doc passes these checks.
- Plugin version: `plugins/s/.claude-plugin/plugin.json` goes one patch above main (0.6.315 to 0.6.316) because `plugins/s/` changes.
- Risk: a future test starts reading an allowlisted directory. Guard: the allowlist is one constant, and the structural test in `test_ci_scope.py` pins that every test step is guarded.

## Questions and answers

### Q1: How broad is the fast-path allowlist?
- **Question:** Which paths may skip the test suites? Options: (1) only `.shipd/epics/`, `.shipd/research/`, `.shipd/docs/`; (2) option 1 plus `.shipd/planned/` and `.shipd/completed/`; (3) option 1 plus top-level `docs/`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Tests read `.shipd/verified/` and top-level `docs/` in the real tree, and the minimal list is the safest start; widening is one constant.
- **Queued:** q-ci-fast-path-allowlist

### Q2: Do lint steps run on the fast path?
- **Question:** On the fast path, keep the cheap lint steps and skip only test suites and installs, or skip everything but checkout? Options: (1) keep lints; (2) skip all. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. `spec_lint.py` with no arguments lints every epic, so an epic PR is still validated in seconds.
- **Queued:** q-ci-fast-path-keeps-lints

### Q3: Where does the classifier live?
- **Question:** Where should the classification script live? Options: (1) `tools/ci_scope.py` with tests in `tools/tests/`; (2) `plugins/s/skills/build/scripts/ci_scope.py` beside `version_guard.py`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It is repo-level CI tooling, its tests already run in `ci.yml`, and it is not engine code. (The plugin is still bumped, for the lint change in Q4.)
- **Queued:** q-ci-scope-script-location

### Q4: Should CI validate research and docs files?
- **Question:** Should the library lint also validate research reports and content-dir docs so the fast path is gated by shipd validation? Options: (1) yes, extend `lint_library`; (2) leave them unlinted.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Yes. We can use the shipd validation to check specs and such, so CI does that: `lint_library` runs `lint_research` and `lint_docs` over the installed files.
- **Queued:** none

## Readiness attestation

### Problem and motivation

Epic and research PRs run the full test matrix though no test reads them, and a ruleset cannot vary required checks by path.

Evidence:

- `.github/workflows/ci.yml` runs every suite unconditionally on `pull_request` and `push`.
- `plugins/s/skills/build/scripts/version_guard.py` shows the repo's pattern for a small tested CI script.

### Scope and non-goals

The change adds one classifier, its tests, and `if:` guards in `ci.yml`; branch protection, push runs, and plugin files stay out.

Evidence:

- `.github/workflows/ci.yml:1-8` fixes the triggers and the single job `ci`.
- Out of scope: `plugins/s/` (no file edited).

### Affected capabilities and files

One new capability, `ci-fast-path`, and three files are affected.

Evidence:

- Files: `tools/ci_scope.py` (new), `tools/tests/test_ci_scope.py` (new), `.github/workflows/ci.yml`.
- Runnable premise: `python3 plugins/s/skills/build/scripts/spec_lint.py` with no arguments lints `.shipd/epics/*/epic.md` (`spec_lint.py:1778-1795`, `lint_library`), which is why lints stay on the fast path.
- Runnable premise: grep of `plugins/s/skills/*/tests`, `evals/tests`, `tools/tests` found real-tree reads of `.shipd/verified/`, `docs/`, `README`, `AGENTS.md`, `action.yml`, `install.sh`, `ci.yml`, and none of `.shipd/epics`, `research`, `docs`.
- `plugins/s/skills/document/tests/test_docs_ci_gate.py:159` pins step order for `Lint docs`.

### No open task-shaping decision

Four decisions were settled: three defaults the user confirmed and one the user added.

Evidence:

- Allowlist breadth: Q1, user-confirmed default.
- Lints on the fast path: Q2, user-confirmed default.
- Script location: Q3, user-confirmed default.
- Validate research and docs in library lint: Q4, user decision.
