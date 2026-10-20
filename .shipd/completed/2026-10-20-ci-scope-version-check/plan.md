# ci-scope-version-check
Status: verified
Planned-at: 73156d3ce5cd7c38ac953d31cd0771c4a89ffd93
Gated-hash: 43710be3917c

## Idea

Rename the CI fast path to "CI scope", and add a check on every push to `main` that fails when the pushed commit edits `plugins/s/` without a plugin version above its parent's.

### Motivation

Maintainers reading `ci.yml` confuse its "fast" output with the review gate's unrelated fast-pass auto-merge arming. Two pull requests each passed the version guard against an older `main` and both shipped plugin version 0.6.319, and nothing flagged it once they landed.

### Details

- `tools/ci_scope.py` prints and writes `scope=content` or `scope=full` instead of `fast=true` or `fast=false`; `classify(paths)` returns that scope string.
- `.github/workflows/ci.yml` guards every test-suite and install step with `if: steps.scope.outputs.scope != 'content'`.
- `.github/workflows/ci.yml` gains a step "Check the plugin version on main", run only on push events and never scope-guarded, which runs `version_guard.py` with the first parent as base and the pushed commit as head and fails with an error annotation asking for a follow-up bump.
- `tools/tests/test_ci_scope.py` follows the rename; a new `tools/tests/test_ci_main_version_check.py` runs the new step's script against throwaway git repos.

Affected capabilities: `ci-fast-path` (modified: `ci-scope-classifier`, `ci-fast-path-workflow`, renamed to `ci-scope-workflow`); `shipd-install` (modified: `plugin-version-advance`; added: `plugin-version-main-check`). Impact: `tools/ci_scope.py`, `tools/tests/test_ci_scope.py`, `tools/tests/test_ci_main_version_check.py` (new), `.github/workflows/ci.yml`. Nothing under `plugins/s/` changes, so the plugin version stays as it is.

### Non-goals

- No change to `version_guard.py` or its tests, and no new version comparison logic.
- No `strict` branch protection; the user keeps it off and catches duplicates at merge time.
- No rename of the capability folder `ci-fast-path` (the engine has no capability rename), and no change to shipd-plan's planning "fast path" or the review gate's fast-pass.
- No change to the pull request version guard step or the allowlist.

## Implementation

- Scope names are `content` and `full`. `content` names what the change holds (planning content only); `full` names what CI runs (the full suite). Rejected: `docs` (the allowlist excludes top-level `docs/`), `lite`/`light` (clash with `Profile: lite`), `skip` (inverts the meaning of the guard).
- The step id stays "scope" and the output key is "scope", so the guard reads "steps.scope.outputs.scope != 'content'". Comparing against `content` keeps the fail-closed rule: a missing output is an empty string, which is not `content`, so the full suite runs.
- `ci_scope.py` interface: constants `CONTENT = "content"` and `FULL = "full"`; `classify(paths) -> str`; the CLI prints "scope=<value> (<reason>)" and appends "scope=<value>" to the output file. `changed_paths` and every fail-closed rule are unchanged.
- Main check step, placed directly after "Guard the plugin version", with `if: github.event_name == 'push'` (the push trigger already lists only `main`, so `ci.yml` keeps its triggers). Its run block is exactly:

  ```
  status=0
  finding="$(python3 plugins/s/skills/build/scripts/version_guard.py --base HEAD^1 --head HEAD 2>&1)" || status=$?
  if [ "$status" -ne 0 ]; then
    echo "::error title=Plugin version not advanced on main::${finding}"
    echo "This commit reached main without a plugin version above its parent's, so two merges may share one version. Land a follow-up pull request that bumps plugins/s/.claude-plugin/plugin.json above the version now on main." >&2
    exit "$status"
  fi
  echo "plugin version check passed against the parent commit"
  ```

  The guard's finding already names both versions (base is the parent, head is the pushed commit). Capturing with `|| status=$?` keeps the default `bash -e` shell from exiting before the message prints. Exit 2 (unreadable manifest) also fails loudly. Rejected: adding a flag to `version_guard.py` (touches `plugins/s/` and needs a bump for a message only); comparing against `github.event.before` (a force push or new branch gives a useless base; the first parent is what the squash merge built on).
- "HEAD^1" resolves because checkout already sets `fetch-depth: 0`. A three-dot diff from a parent to its child equals the plain diff, so the guard's diff is exactly the pushed commit's change.
- Tests for the step read its run block out of `ci.yml` (the text between "run: |" and the next step, dedented) and run it with `bash -e` inside a temp git repo that holds a copy of `version_guard.py` at its real path and a manifest. So the test exercises the shipped text, not a copy.
- Docs: no file under `docs/` describes `ci.yml`, the classifier, or the version guard (grep for "ci_scope", "ci.yml", "version guard", "fast" over `docs/` and `README.md`), so no doc changes. The docs lint still runs as a check.
- Risk: the main check fails after merge and cannot block it. That is the intent; the red `main` run plus the annotation is the signal, and the fix is a follow-up bump.

## Readiness attestation

### Problem and motivation

"fast" in `ci.yml` reads like fast-pass, and duplicate plugin versions reach `main` unflagged.

Evidence:

- `.github/workflows/ci.yml` guards twelve steps with the "fast" output.
- Fast-pass is a review gate feature (grep "fast-pass" in `plugins/s/skills/review/`).
- Runnable premise: running `version_guard.py --base <c>^ --head <c>` for each of the last 80 first-parent commits exits 1 for 4723b1c, printing "base version '0.6.319', head version '0.6.319' does not exceed it".

### Scope and non-goals

Four repo files change; `plugins/s/` and branch protection stay out.

Evidence:

- In scope: `tools/ci_scope.py`, `tools/tests/test_ci_scope.py`, `tools/tests/test_ci_main_version_check.py`, `.github/workflows/ci.yml`.
- Out of scope: `plugins/s/skills/build/scripts/version_guard.py` is reused unchanged.

### Affected capabilities and files

Two capabilities change: `ci-fast-path` and `shipd-install`.

Evidence:

- `ci-fast-path`: `ci-scope-classifier` (base e8b65186bf3e), `ci-fast-path-workflow` (base 27464ecfcd85); `shipd-install`: `plugin-version-advance` (base d58075580004); hashes from `spec_status.py base-hash`.
- Runnable premise: `version_guard.py --base HEAD^ --head HEAD` on main head 73156d3 exits 0 with no output.
- `ci.yml` already has `push: branches: [main]` and `fetch-depth: 0`.
- No test outside `tools/tests/` reads the "fast" output or the version guard step (grep of `plugins/s/skills/*/tests`).

### No open task-shaping decision

Every decision is settled: scope names, step shape, and docs scope, under the user's pre-approved defaults.

Evidence:

- Scope names `content`/`full`: Implementation, first bullet.
- Main check uses the first parent and the unchanged guard: user direction, Implementation.
- Keep `strict` off: user decision.
