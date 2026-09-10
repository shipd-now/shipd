## 1. Failing test first

- [x] 1.1 [req: docs-ci-marker-gate] Add
      `plugins/s/skills/document/tests/test_docs_ci_gate.py`: a helper reads
      `.github/workflows/ci.yml` as text and extracts the dedented `run:` body
      of the step named `Lint marker-carrying docs` (no YAML parser, per the
      `test_ci_action.py` pattern); tests execute that body with
      `["bash", "-e"]` in a temp directory holding a fabricated `docs/` tree
      and a copy of the real `docs_lint.py` at
      `plugins/s/skills/document/scripts/docs_lint.py`. Cover four cases:
      failing marker doc → non-zero; clean marker doc → 0; no marker docs →
      0 with a skip notice on stdout; failing marker doc only under
      `docs/retros/` → 0. Run the suite and observe it fail — the step does
      not exist yet.

## 2. The CI step

- [x] 2.1 [req: docs-ci-marker-gate] In `.github/workflows/ci.yml`, directly
      after the `Lint in-flight changes` step, add a `Lint marker-carrying
      docs` step whose `run:` block selects files with
      `find docs -name '*.md' -not -path 'docs/retros/*'` filtered by
      first-line `grep -q '<!-- *doc-type:'`, then runs
      `python3 plugins/s/skills/document/scripts/docs_lint.py` over the
      selected files when any exist, else prints
      `no marker-carrying docs; skipping`. Confirm
      `python3 -m unittest discover -s plugins/s/skills/document/tests -v`
      now passes.

## 3. Version bump and verification

- [x] 3.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.202` to `0.6.203`.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests -v`) and
      the document suite to confirm nothing regressed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 45 | 10.3k |
| Write | 1 | 6.5k |
| Read | 23 | 1.3k |
| Monitor | 2 | 399 |
| Agent | 2 | 313 |
| (no tool) | 0 | 105 |
| ToolSearch | 2 | 30 |
| Edit | 2 | 20 |
| TaskStop | 1 | 17 |
| **Total** | 78 | 19.1k |
