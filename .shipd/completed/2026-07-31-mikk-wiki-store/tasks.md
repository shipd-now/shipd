# Tasks

## 1. Paths and grammar helpers (spec_common.py)

- [x] 1.1 [req: wiki-store-layout] In
      `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests
      for `wiki_dir(ws_root)` returning `<content-dir>/wiki` under the
      workspace root, and for the reserved-slug constant covering `index`,
      `log`, `queue`, `schema`, `sources`.
- [x] 1.2 [req: wiki-page-grammar, wiki-index-and-log, wiki-question-queue] In
      `test_spec_common.py`, add failing tests for the grammar parse helpers:
      wikilink extraction that skips fenced code blocks, index-entry parsing of
      `- [[slug]] — summary` lines (non-matching lines ignored), log-header
      matching of `## [YYYY-MM-DD] <op> | <subject>`, and queue-block parsing
      of `## q-<slug>` blocks into their five `- Field:` values.
- [x] 1.3 [req: wiki-store-layout, wiki-page-grammar, wiki-index-and-log, wiki-question-queue]
      In `plugins/s/skills/build/scripts/spec_common.py`, implement `wiki_dir`
      beside `initiatives_dir`/`projects_dir`, the reserved-slug constant, and
      the parse helpers from 1.2; confirm the 1.1–1.2 tests pass.

## 2. Wiki lint mode (spec_lint.py)

- [x] 2.1 [req: wiki-lint-mode] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add failing tests for
      `lint_wiki(ws_root, errors)` over tmp-dir stores: a clean seeded store
      (no errors); and one error each for a missing layout file, a reserved
      page slug, a dead `[[wikilink]]` (with a fenced-code link ignored), an
      unindexed page, an index entry with no page, a malformed `log.md`
      header, and a queue block missing a field.
- [x] 2.2 [req: wiki-lint-mode] In
      `plugins/s/skills/build/scripts/spec_lint.py`, implement `lint_wiki`
      using the spec_common helpers, and wire a `--wiki` flag in `main` that
      requires a discoverable workspace (mirror the `--workspace` no-workspace
      error) and follows the existing findings/exit-code contract; confirm the
      2.1 tests pass.

## 3. Scaffold and read verbs (spec_status.py)

- [x] 3.1 [req: wiki-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests
      for `wiki-init` (creates `schema.md`, `index.md`, `log.md` with one
      dated entry, `queue.md`, `sources/`, `wiki/`; second run exits non-zero
      naming the existing store), `wiki-show` (prints root, page count,
      coverage health, pending count, last log entry), and `cat wiki <slug>`
      (page content; reserved slugs `index`/`log`/`queue`/`schema` print the
      top-level files; unknown slug exits non-zero).
- [x] 3.2 [req: wiki-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, implement `wiki-init`
      and `wiki-show` as subcommands beside `workspace-init`/`workspace-show`,
      and extend `cmd_cat` with the `wiki` kind; confirm the 3.1 tests pass.

## 4. Queue-add verb (spec_status.py)

- [x] 4.1 [req: wiki-status-verbs, wiki-question-queue] In
      `test_spec_status.py`, add failing tests for `wiki-queue-add`: a first
      add appends a `## q-<slug>` block carrying the `--question`,
      `--options`, `--recommendation`, optional `--origin` values, a
      current-date `Asked:` line, and `Answer: pending`; a duplicate slug
      exits non-zero with `queue.md` byte-identical to before.
- [x] 4.2 [req: wiki-status-verbs, wiki-question-queue] In `spec_status.py`,
      implement `wiki-queue-add` per the plan (build block, append,
      re-validate the queue with the spec_common parser, restore prior content
      and exit non-zero on duplicate or invalid result); confirm the 4.1 tests
      pass.

## 5. Staged wiki emission (spec_emit.py)

- [x] 5.1 [req: wiki-emission] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add failing tests for
      the `wiki` subcommand: staging a page plus updated `index.md` installs
      both and exits zero; a staged set producing a dead wikilink or unindexed
      page restores the prior store byte-for-byte and exits non-zero; staging
      a `sources/` file that already exists in the store refuses before any
      install.
- [x] 5.2 [req: wiki-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py`, implement the `wiki`
      subcommand per the plan: back up affected files, install the staged
      subset, run `lint_wiki` on the resulting store, restore and exit
      non-zero on findings; confirm the 5.1 tests pass.

## 6. Docs, version, verification

- [x] 6.1 [req: wiki-store-layout, wiki-page-grammar, wiki-index-and-log, wiki-question-queue]
      In `.shipd/README.md`, add a `### Wiki` subsection
      beside the Workspace/Initiative sections documenting the store layout
      and the index/log/queue/page grammars exactly as the shipd-wiki delta
      states them.
- [x] 6.2 [req: *] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 6.3 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and observe an
      all-green run.
