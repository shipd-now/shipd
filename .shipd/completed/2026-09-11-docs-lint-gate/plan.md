# docs-lint-gate
Status: verified
Epic: docs-rewrite
Theme: developer-experience

## Idea

Add a marker-gated docs-lint step to the repository's CI so every doc that
carries a `<!-- doc-type: ... -->` marker is checked by `docs_lint.py` on every
PR, with `docs/retros/` exempt.

### Motivation

The shipd documentation standard and its lint exist, but nothing enforces them
in CI, so a doc rewritten to the standard can silently regress. The epic's
first member lands a marker-scoped gate so each rewrite cluster opts in as it
ships and stays guarded for the epic's whole duration.

### Details

- Add a `Lint marker-carrying docs` step to `.github/workflows/ci.yml`,
  following the inline shell-loop shape of the existing `Lint in-flight
  changes` step: select markdown files under `docs/` (recursive) whose first
  line carries a doc-type marker comment, excluding `docs/retros/`, and run
  `plugins/s/skills/document/scripts/docs_lint.py` on them.
- With no marker-carrying docs — the tree's current state — the step prints a
  skip notice and passes without invoking the lint.
- Add `plugins/s/skills/document/tests/test_docs_ci_gate.py`, which extracts
  the step's `run:` body from `ci.yml` and executes it against fixture trees,
  per the `test_ci_action.py` executable pattern. CI already discovers this
  suite.
- Bump the plugin version (the change touches `plugins/s/`).

Affected capabilities: `shipd-document` (modified — one ADDED requirement).
Impact: `.github/workflows/ci.yml`, new
`plugins/s/skills/document/tests/test_docs_ci_gate.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies; the lint and the
test stay stdlib-only.

### Non-goals

- No full-scope enforcement — every unmarked doc stays unlinted; the epic's
  final member (`docs-full-enforcement`) flips the scope.
- No change to `docs_lint.py`, the standard, or the `/s:document` skill flow —
  they are the epic's fixed inputs.
- No doc rewrites and no markers added to any doc — the rewrite members do
  that, cluster by cluster.
- No change to the consumer-facing composite action (`action.yml`); this gate
  is this repository's own CI only.

## Implementation

- **Selection filter: first line contains `<!-- doc-type:` (optional spaces
  after `<!--`), matched leniently.** The step selects with
  `find docs -name '*.md' -not -path 'docs/retros/*'` plus a first-line
  `grep -q '<!-- *doc-type:'`, unanchored. `docs_lint.py`'s marker regex
  (`MARKER_RE`, `docs_lint.py:50`) strips the line and allows any spacing, so
  a lenient filter guarantees a malformed or unknown marker is selected and
  *fails* the lint (observed: unknown `doc-type: bogus` exits 1) instead of
  being silently skipped. Rejected: anchoring on `^<!--` — it would skip a
  marker the lint itself accepts (leading whitespace), creating a gap between
  the filter and the checker.
- **Inline `run:` block in `ci.yml`, not a helper script.** The step mirrors
  the existing `Lint in-flight changes` shell loop: collect the selected paths
  into a variable, run the lint once over all of them when non-empty,
  otherwise print `no marker-carrying docs; skipping` and pass. `find`'s exit
  is unaffected by non-matching `-exec` filters, so the block is safe under
  the runner's `bash -e`. Rejected: a new script under `plugins/s/` — the
  repo's other repo-scoped lint steps are inline, and a script would expand
  the plugin surface for six lines of shell.
- **Step placement and failure mode.** The step sits with the lint steps,
  directly after `Lint in-flight changes`. Any lint error exits 1 and fails
  the required `ci` check; warnings (passive voice) never affect the exit
  code — that contract is `docs_lint.py`'s own and is not restated in CI.
- **Test follows the `test_ci_action.py` executable pattern.**
  `test_docs_ci_gate.py` reads `.github/workflows/ci.yml` as text, extracts
  the named step's dedented `run:` body with a small helper (no YAML parser —
  tests stay stdlib-only), and executes it with `bash -e` in fixture
  directories that carry a fabricated `docs/` tree plus a copy of the real
  `docs_lint.py` at its repo-relative path. This proves the encoded command
  actually gates, not merely that `ci.yml` mentions the script. It lives in
  `plugins/s/skills/document/tests/` because CI already discovers that suite
  (`ci.yml:37`) and the gate is document-skill territory.
- **Scope flip is a one-line seam.** The selection filter is the only
  marker-scoped part of the step; `docs-full-enforcement` later drops the
  first-line grep and adds the marker requirement for all non-retro docs,
  updating the same test.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` goes `0.6.202` →
  `0.6.203` in the same change, per the repo's cache-snapshot rule.

Risk: shell quoting over the collected path list — mitigated by the fixture
test executing the verbatim step body, and by repo doc paths containing no
whitespace.
