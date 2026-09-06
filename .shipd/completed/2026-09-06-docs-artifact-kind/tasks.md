## 1. Docs lint checks

- [x] 1.1 [req: docs-document-validation, docs-document-format] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add tests for
      `lint_docs(root, slug, errors)`: a titled free-form document (body
      containing `[1]` markers and no `## Sources`) produces no findings; an
      untitled document produces a finding naming
      `<content-dir>/docs/<slug>/doc.md`; a missing document file produces a
      not-found finding naming the expected path; library lint
      (`lint_library`) produces no docs finding while an untitled file sits
      under `docs/`; and `spec_lint.py` exposes no command-line mode for the
      docs checks (mirror `test_no_command_line_mode_for_video_checks`). Run
      them and observe them fail — `lint_docs` does not exist yet.
- [x] 1.2 [req: docs-document-validation, docs-document-format] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add `lint_docs(root,
      slug, errors)` next to `lint_research`: resolve
      `<content-dir>/docs/<slug>/doc.md` via `sc.specs_dir`, report a
      not-found finding when the file is missing, otherwise enforce only a
      non-empty `# <title>` on line 1 (reuse the research title check's
      wording pattern), with a docstring citing shipd-spec-lint
      docs-document-validation and shipd-spec-format docs-document-format.
      Confirm the 1.1 tests pass.

## 2. Staged emission

- [x] 2.1 [req: staged-emission] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add docs-mode tests
      mirroring the research ones: a titled staged file installs at
      `<content-dir>/docs/<slug>/doc.md` printing `installed docs <slug> at
      <path>` with exit 0; an untitled staged file exits non-zero and leaves
      `<content-dir>/docs/<slug>/` absent; an existing destination refuses
      without `--replace` leaving the original untouched; `--replace`
      installs the new content. Run them and observe them fail.
- [x] 2.2 [req: staged-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py`, add `emit_docs(root,
      slug, src, replace)` mirroring `emit_research` (install to
      `docs/<slug>/doc.md`, validate with `sl.lint_docs`,
      `sc.stamp_schema_marker(root)`, print `installed docs %s at %s`), add
      the `docs` subparser (`slug`, `--from`, `--replace`) and its dispatch
      branch in `main`, and add the `docs` mode line to the module
      docstring. Confirm the 2.1 tests pass.

## 3. Mediated read (cat)

- [x] 3.1 [req: mediated-read-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add cat tests
      mirroring `test_cat_research`/`test_cat_unknown_research_errors`/
      `test_cat_research_reads_a_worktree_hosted_report`: `cat docs <slug>`
      prints one `--- <relpath>` separator plus the document; an unknown
      slug exits non-zero naming the probed candidate roots; a
      worktree-hosted document resolves from the main checkout. Run them and
      observe them fail.
- [x] 3.2 [req: mediated-read-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add a `"docs"` entry
      to `_CAT_PROBES` probing `docs/<slug>/doc.md` (noun `docs`), extend
      `cmd_cat`'s single-file kind tuple and its unknown-kind error text to
      include `docs`, add `"docs"` to the `cat` subparser's `choices`, and
      update the `cmd_cat`/`_CAT_PROBES` docstrings. Confirm the 3.1 tests
      pass.

## 4. Related search surface

- [x] 4.1 [req: related-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, extend the related
      tests (near `test_research_and_epic_surfaces_are_searched`): an
      installed `docs/<slug>/doc.md` containing a term prints a block with
      `kind: docs` and the slug. Run it and observe it fail.
- [x] 4.2 [req: related-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add a `docs` walk to
      `_related_candidate_artifacts` appending `("docs", slug, path, [path])`
      records for `docs/<slug>/doc.md`, alongside the research walk, and
      update the function and `cmd_related` docstrings to name the docs
      surface. Confirm the 4.1 test passes.

## 5. Listing

- [x] 5.1 [req: cli-list] Add failing tests: in
      `plugins/s/skills/build/tests/test_spec_status.py`, `list_rows(root,
      "docs", ...)` returns root-first deduped status-less rows for
      `docs/<slug>/` directories; in
      `plugins/s/skills/build/tests/test_shipd_cli.py`, `shipd list docs
      --root <repo>` prints one line per document with status `-`, prints
      `no docs` on an empty repo with exit 0, and the usage banner names
      `docs` among the list kinds. Run them and observe them fail.
- [x] 5.2 [req: cli-list] In
      `plugins/s/skills/build/scripts/spec_status.py`, append `"docs"` to
      `LIST_KINDS` and `"docs": "docs"` to `_LIST_KIND_DIRS`, updating the
      `list_rows` docstring; in `plugins/s/bin/shipd`, add `"docs": "no
      docs"` to `LIST_EMPTY_TEXT` and add `docs` to the `USAGE` banner's
      kind roster line. Confirm the 5.1 tests pass.

## 6. Version bump and verification

- [x] 6.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.179` to `0.6.180`
      (plugins/s/ changed; AGENTS.md rule).
- [x] 6.2 [req: *] Run the full engine suite — `python3 -m unittest
      discover -s plugins/s/skills/build/tests` — and confirm it passes
      with no `textual` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 91 | 23.7k |
| Edit | 31 | 3.3k |
| Read | 24 | 2.2k |
| (no tool) | 0 | 54 |
| Agent | 2 | 17 |
| **Total** | 148 | 29.3k |
