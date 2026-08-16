## 1. Action manifest

- [x] 1.1 [req: composite-lint-action] Add failing tests in
      `plugins/s/skills/build/tests/test_ci_action.py`: `action.yml`
      exists at the repo root and declares `using: composite`, the `path`
      input with default `.`, steps referencing `spec_lint.py` through the
      action-path variable, and no `uses:` or cache steps; plus execution
      tests running the substituted step commands against fixture repos
      (valid library + valid change passes; a change with a structural
      error exits nonzero).
- [x] 1.2 [req: composite-lint-action] Author `action.yml` at the repo
      root: name/description, the `path` input, two `shell: bash` steps —
      master-library lint and the per-planned-change loop — both invoking
      `spec_lint.py` from `$GITHUB_ACTION_PATH`. Run the 1.1 tests green.

## 2. Docs

- [x] 2.1 [req: ci-usage-docs] Add the README CI section: the consumer
      workflow snippet (checkout + `uses: shipd-now/shipd@<ref>`), the
      pinned-ref note, the `path` input default, and the python3 runner
      requirement.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Run `plugins/s/skills/build/tests/` with no `textual`
      installed; green.
