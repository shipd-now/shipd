# docs-full-enforcement
Status: verified
Epic: docs-rewrite
Theme: developer-experience

## Idea

Flip the CI docs-lint gate from marker-scoped to full scope: every markdown
file under `docs/` except `docs/retros/` must carry a doc-type marker and pass
`docs_lint.py` on every PR.

### Motivation

The epic's rewrite members have all shipped — every non-retro doc now carries
a marker and the full-scope lint exits 0 — but the CI step still selects only
marker-carrying files, so a newly added unmarked doc would silently bypass the
standard. The epic's final member closes that gap by making the gate
unconditional.

### Details

- Rewrite the `Lint marker-carrying docs` step in `.github/workflows/ci.yml`
  as a full-scope `Lint docs` step: drop the first-line marker grep and run
  `plugins/s/skills/document/scripts/docs_lint.py` over every
  `docs/**/*.md` outside `docs/retros/`. The lint itself errors on a missing
  first-line marker, so full scope enforces the marker requirement with no
  extra CI logic.
- Update `plugins/s/skills/document/tests/test_docs_ci_gate.py` to the
  full-scope contract: an unmarked doc now fails, retros stay exempt, and an
  empty `docs/` tree still passes via the retained empty-selection guard.
- Sweep: run the full-scope lint over the real tree and confirm exit 0 —
  observed clean at planning time (17 docs, all marked, two warnings only).
- Bump the plugin version (the test edit touches `plugins/s/`).

Affected capabilities: `shipd-document` (modified — the `docs-ci-marker-gate`
requirement flips to full scope). Impact: `.github/workflows/ci.yml`,
`plugins/s/skills/document/tests/test_docs_ci_gate.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `docs_lint.py`, the standard, or the `/s:document` skill — the
  epic's fixed inputs.
- No doc rewrites: the sweep verified zero stragglers, so no straggler-fix
  work is expected; a straggler surfacing mid-build is fixed through
  `/s:document`, never by relaxing the gate.
- No `docs/retros/` enforcement — retros stay exempt, per the epic.
- No epic close-out: `epic-sync` on the merged epic runs later in its own
  `epic-close-docs-rewrite` worktree, per AGENTS.md.
- No change to the consumer-facing composite action (`action.yml`).

## Implementation

- **Full scope is "lint everything"; the lint carries the marker rule.** The
  step keeps `find docs -name '*.md' -not -path 'docs/retros/*'` and passes
  every hit to `docs_lint.py` — the first-line grep filter is deleted.
  Observed: `docs_lint.py` on a file with no first-line marker prints
  `error: missing first-line doc-type marker` and exits 1, so unmarked docs
  fail CI with no separate marker check. Rejected: a shell-side marker test
  before the lint — it would duplicate a rule the lint already enforces and
  could drift from `MARKER_RE`.
- **The empty-selection guard stays.** Observed: `docs_lint.py` with no
  arguments exits 2 (usage), so the step keeps the collect-then-run shape —
  when `find` selects nothing it prints `no docs to lint; skipping` and
  passes. Rejected: dropping the guard — an emptied `docs/` tree would turn
  the step into a usage error instead of a pass.
- **The step renames to `Lint docs`.** Its old name described the
  marker-scoped selection this change deletes. The step keeps its place
  directly after `Lint in-flight changes`; `test_docs_ci_gate.py` asserts
  both the name (`STEP_NAME`) and the position, so the test updates in the
  same change. Rejected: keeping the old name — it would misdescribe the
  step's scope permanently.
- **The requirement keeps its id.** The delta modifies `docs-ci-marker-gate`
  in place (base `aa4579b9f9c5`) rather than renaming it: the gate now
  *requires* markers on every non-retro doc, so the id still describes the
  behavior, and a rename would churn the ledger for no contract gain.
- **Test updates follow the existing executable pattern.** The fixture tests
  keep executing the extracted `run:` body under `bash -e`: the unmarked-doc
  fixture flips from skip-and-pass to fail-with-marker-error, the retros
  fixture keeps passing (its output no longer carries a marker-scoped skip
  notice — with retros excluded the selection is empty, so the new notice
  appears), and a no-docs tree passes with the notice. The structural
  assertions (`docs_lint.py` named, `docs/retros/` exempt) are unchanged.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` goes `0.6.203` →
  `0.6.204`, per the repo's cache-snapshot rule.

Risk: a doc merged to `main` between planning and this change's merge could
arrive unmarked and fail the flipped gate on this PR; the sweep task re-runs
the full-scope lint at build time so any such straggler is caught and fixed
through `/s:document` before the PR ships.
