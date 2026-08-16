# ci-lint-action
Status: verified
Epic: shipd-dx

## Idea

A repo-root composite GitHub Action so consumer repositories run shipd's
structural spec lint as a check with a few lines of workflow YAML
(`uses: shipd-now/shipd@<ref>`).

### Motivation

A repository adopting shipd has no way to enforce spec-library and
change-delta validity in CI without copying engine invocations by hand; the
`shipd-dx` epic makes a few-lines CI check one of its success criteria.

### Details

- New `action.yml` at the repository root: a composite action with a `path`
  input (default `.`) whose steps run, using the runner's `python3`,
  `spec_lint.py --root <path>` from `${{ github.action_path }}` and then
  lint every change under the consumer's resolved `planned/` directory —
  the same two invocations this repo's own CI performs.
- README gains a CI section with the consumer workflow snippet (checkout +
  the `uses:` step).
- Structural tests assert the manifest's load-bearing lines and execute the
  substituted step command against a fixture repo.

Affected capabilities: `ci-action` (added). Impact: `action.yml` (new, repo
root), `README.md`,
`plugins/s/skills/build/tests/test_ci_action.py` (new), plugin version bump
(tests live under `plugins/s/`). No new dependencies.

### Non-goals

- No semantic review in the action — the review gate needs an LLM and is
  explicitly out of scope per the epic decision.
- No dependency caching and no `actions/cache`/tool-cache steps: the
  stdlib-only engine scripts travel inside the action's own checkout, so
  there is nothing to download or cache (a deliberate, recorded deviation
  from the epic's caching decision — see Implementation).
- No third-party action steps (`actions/setup-python` included) — nothing to
  pin, no cache-poisoning surface.
- No marketplace publication metadata (branding/icons) beyond a name and
  description.

## Implementation

- **Composite, not Docker or JS** — the engine is plain python3 scripts that
  need no build step; composite keeps the consumer YAML to `uses:` + input.
- **The epic's caching decision is deliberately not implemented.** The
  decision guarded against re-downloading tools; a composite action's
  scripts arrive with its checkout and the engine imports nothing beyond the
  stdlib, so a cache step would cache nothing and only add the poisoning
  surface the epic warns about. The action therefore has zero cache and
  zero third-party steps; GitHub-hosted runners ship `python3` (documented
  as the action's one runner requirement).
- **Steps:** (1) `python3 "$GITHUB_ACTION_PATH/plugins/s/skills/build/scripts/spec_lint.py" --root "<path>"`
  for the master library; (2) a sh loop with the same shape as this repo's
  `.github/workflows/ci.yml` in-flight loop (iterate change dirs, lint each
  basename via `spec_lint.py <change> --root "<path>"`), except the content
  dir is resolved config-aware — a `python3 -c` one-liner importing the
  engine's own `spec_common` (`resolve_config` + `specs_dirname`) from
  `$GITHUB_ACTION_PATH/plugins/s/skills/build/scripts` — so a consumer with
  a custom `.shipd-config.json` `dir` key gets its in-flight changes linted
  from the same directory the master-library lint already resolves
  internally. Both steps use `shell: bash` as composite steps require.
- **Interface:** input `path` (default `.`) — the consumer repository
  directory to lint (they check out their own repo first; the action's
  checkout is implicit in `github.action_path`).
- **Tests** (`test_ci_action.py`, stdlib — no YAML parser): assert
  `action.yml` declares `using: "composite"`, the `path` input with its
  default, and steps referencing `spec_lint.py` via the action-path
  variable; then execute the step's command with the variables substituted
  against a fixture repo (valid library passes; an invalid change fails
  nonzero) — proving the encoded command line actually runs.
- **README snippet** shows the minimal consumer workflow: checkout, then
  `uses: shipd-now/shipd@main` (with a note to prefer a pinned ref).
- Risk: composite `shell:` quoting differences across runners; guard: the
  command is a single `python3` invocation plus a POSIX loop, both already
  proven in this repo's `ci.yml`.
