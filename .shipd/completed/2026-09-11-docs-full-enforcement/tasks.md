## 1. Flip the tests to the full-scope contract

- [x] 1.1 [req: docs-ci-marker-gate] In
      `plugins/s/skills/document/tests/test_docs_ci_gate.py`: set
      `STEP_NAME = "Lint docs"`, set `SKIP_NOTICE = "no docs to lint;
      skipping"`, and update the module docstring's "marker-gated" wording to
      the full-scope contract. Keep `PRIOR_STEP_NAME` and the structural
      assertions (step position, `docs_lint.py`, `docs/retros/`) unchanged.
- [x] 1.2 [req: docs-ci-marker-gate] In the same file, replace
      `test_no_marker_docs_skips_and_passes` with
      `test_unmarked_doc_fails`: the `NO_MARKER_DOC` fixture now makes the
      step exit non-zero with output containing `missing first-line doc-type
      marker`. Update `test_retros_are_exempt` to assert exit 0 and the new
      `SKIP_NOTICE` (retros excluded leaves an empty selection), and add
      `test_empty_docs_tree_skips_and_passes` (a tree with no `docs/*.md` at
      all: exit 0, notice printed). Run the suite and observe the new/updated
      tests fail — `ci.yml` still carries the marker-scoped step.

## 2. Flip the CI step

- [x] 2.1 [req: docs-ci-marker-gate] In `.github/workflows/ci.yml`, rewrite
      the `Lint marker-carrying docs` step as `Lint docs`, in the same
      position: collect `find docs -name '*.md' -not -path 'docs/retros/*'`
      into a variable with no first-line grep filter; when non-empty run
      `python3 plugins/s/skills/document/scripts/docs_lint.py` over the
      collected paths, otherwise print `no docs to lint; skipping`. Confirm
      `python3 -m unittest discover -s plugins/s/skills/document/tests -v`
      now passes.

## 3. Sweep and version bump

- [x] 3.1 [req: docs-ci-marker-gate] Sweep: run
      `python3 plugins/s/skills/document/scripts/docs_lint.py $(find docs
      -name '*.md' -not -path 'docs/retros/*')` from the repo root and
      confirm exit 0. If any file fails, fix it through `/s:document` until
      the run exits 0.
- [x] 3.2 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.203` to `0.6.204`.
- [x] 3.3 [req: *] Verification barrier: run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      the document suite
      (`python3 -m unittest discover -s plugins/s/skills/document/tests`)
      and confirm both pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 28 | 7.7k |
| Edit | 8 | 2.8k |
| SendMessage | 3 | 1.1k |
| Read | 8 | 619 |
| Agent | 1 | 408 |
| ToolSearch | 3 | 368 |
| Monitor | 1 | 332 |
| (no tool) | 0 | 124 |
| TaskStop | 1 | 57 |
| **Total** | 53 | 13.5k |
