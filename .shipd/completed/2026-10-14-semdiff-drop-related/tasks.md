# Tasks

- [x] 1.1 [P1] [req: related-context] Establish what is safe to remove with a
      **whole-file** reachability scan of
      `plugins/s/skills/review/scripts/semdiff.py`, not a scan of function
      bodies. A body-only scan reports `_is_manifest` as unused because its
      one caller sits in a module-level lambda inside `COHORT_RULES`, and
      acting on that would silently stop the `contracts` cohort recognising
      manifests. Confirm `_is_manifest`, `MANIFEST_BASENAMES`,
      `MANIFEST_SUFFIXES` and `_grep_matches` all have live callers and name
      them.
- [x] 1.2 [P1] [req: related-context] Capture the behaviour baseline the right
      way: run the **current** script and the **edited** script against
      identical inputs, not the same script before and after in a working tree
      whose contents the edit changes. Cover `files`, `diff`, `context`,
      `lint`, `doctor` and `change`, using two fixed refs rather than
      working-tree mode. Note the shell is zsh, which does not word-split an
      unquoted expansion — pass arguments explicitly or the invocation becomes
      one argument and every comparison silently compares two usage errors.
- [x] 2.1 [P2] [req: related-context] Remove from `semdiff.py`: `cmd_related`,
      `_find_importers`, `_find_importees`, `_resolve_importee`,
      `_importee_tokens`, `_module_terms`, `_exists_with_extension`,
      `_find_unique_source_file`, `_file_text_at`, `_proximity_key`,
      `RELATED_CAPS`, `IMPORT_EXTENSIONS`, the section banner, the `related`
      subparser and the usage-header line. Keep the four symbols task 1.1
      identified and assert their presence after the edit.
- [x] 2.2 [P2] [req: related-context] Remove from
      `plugins/s/skills/review/tests/test_semdiff_files_context.py` the eight
      related-exclusive classes and the single `GrepFailureTest` method that
      drives `cmd_related`. Keep `FilesCohortTest`, `ContextTest` and
      `GrepFailureTest`'s remaining methods — that file covers three live
      subcommands and deleting it whole would drop their coverage.
- [x] 2.3 [P2] [req: related-context] Reword the two docstrings in
      `semdiff.py` that describe `related`'s behaviour, rather than leaving
      them describing a subcommand that no longer exists.
- [x] 2.4 [P2] [req: related-context] Bump
      `plugins/s/.claude-plugin/plugin.json` to the next free number **above
      whatever the main branch carries at the time**. Read it; do not assume.
      Two changes are in flight ahead of this one, and shipping a version at
      or below main's moves the plugin version backwards — which has happened
      twice in this series.
- [x] 3.1 [P3] [req: related-context] Verify. `semdiff.py --help` must no
      longer list `related`; the module must import cleanly; all seven
      surviving subcommands must produce byte-identical output against the
      pre-change script on identical inputs. Run the review suite and the
      build suite, reading each verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it, and never concurrently with a mutating probe.
      Confirm the whole-library lint passes and `version_guard.py` exits 0
      against the main branch.
- [x] 3.2 [P3] [req: related-context] Confirm no `/s:review` prompt surface
      changed — not `SKILL.md`, nothing under
      `plugins/s/skills/review/references/`, and nothing under
      `plugins/s/harness/` or `plugins/s/integrations/`. A ReviewBench
      measurement is calibrated against that prompt, so a stray edit there
      invalidates it.
