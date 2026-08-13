## 1. Config key + personal-store resolution

- [x] 1.1 [req: memory-store-key] Add `plugins/s/skills/build/tests/test_memory_store.py`
      with a `memory_store_dir` resolution case: a config layer declaring
      `memory_dir: "~/personal/shipd-memory"` resolves to
      `<home>/personal/shipd-memory/wiki`; an undeclared key defaults to the
      expanded `~/.shipd-memory/wiki`; a relative, empty, or non-string value
      raises `ConfigError` naming `memory_dir`. Run it and observe it fail — the
      helper does not exist yet.
- [x] 1.2 [req: memory-store-key] Add `memory_store_dir(root)` to
      `plugins/s/skills/build/scripts/spec_common.py` next to `wiki_base_dir`:
      resolve the layered config, read `memory_dir` (defaulting to
      `~/.shipd-memory` when undeclared), `~`-expand it, validate it is a non-empty
      string expanding to an absolute path (raise `ConfigError` naming
      `memory_dir` otherwise), and return `os.path.join(<expanded>, "wiki")`.
      Confirm the section-1 resolution case in `test_memory_store.py` passes.

## 2. Personal-store targeting on the wiki verbs

- [x] 2.1 [req: wiki-status-verbs, wiki-store-layout] In `test_memory_store.py`,
      add a targeting case: `wiki-init --personal` scaffolds the store at
      `<memory_dir>/wiki` (pointing `memory_dir` at a temp dir via a config
      layer) without any workspace; `wiki-show --personal` reports that store's
      health with a `base: none` line; `cat wiki <slug> --personal` reads a page
      from it. Run it and observe it fail — `--personal` does not exist yet.
- [x] 2.2 [req: wiki-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, add a
      `_wiki_store(root, personal)` helper returning
      `sc.memory_store_dir(root)` when `personal` else
      `sc.wiki_dir(_resolve_workspace(root))`, and route `cmd_wiki_init`,
      `cmd_wiki_show`, and the `wiki` kind of `cmd_cat` through it via a new
      `personal` parameter. Under `--personal`, `cmd_wiki_show` prints
      `base: none` (skip the `wiki_base` resolution).
- [x] 2.3 [req: wiki-status-verbs] In `spec_status.py`'s argument parser, add a
      `--personal` flag to the `wiki-init`, `wiki-show`, and `cat` subparsers and
      thread it into the `cmd_wiki_init`/`cmd_wiki_show`/`cmd_cat` dispatch.
      Confirm the section-2 targeting case in `test_memory_store.py` passes.

## 3. wiki-remove verb

- [x] 3.1 [req: wiki-remove-verb] Add
      `plugins/s/skills/build/tests/test_wiki_remove.py` covering: a successful
      removal drops `wiki/<slug>.md`, its `index.md` entry, and appends a dated
      `remove | <slug>` line to `log.md`; an inbound `[[slug]]` link in another
      page blocks removal and restores the store byte-for-byte with a non-zero
      exit naming the linking page; a missing page and a reserved slug each exit
      non-zero writing nothing; a removal in a git store commits only the touched
      files with subject `shipd-wiki: remove <slug>`; a removal in a non-git store
      exits zero with no commit; and `wiki-remove <slug> --personal` removes from
      the personal store leaving the workspace store untouched. Run it and
      observe it fail — the verb does not exist yet.
- [x] 3.2 [req: wiki-remove-verb] Add `cmd_wiki_remove(root, slug, personal)` to
      `spec_status.py`: resolve the store via `_wiki_store(root, personal)`,
      refuse a reserved slug (`index`/`log`/`queue`/`schema`/`sources`) and a
      missing `wiki/<slug>.md` up front (writing nothing), then back up
      `wiki/<slug>.md`, `index.md`, and `log.md`; delete the page; remove its
      `index.md` catalog entry; and append `## [YYYY-MM-DD] remove | <slug>` to
      `log.md`.
- [x] 3.3 [req: wiki-remove-verb] In `cmd_wiki_remove`, after mutating, run the
      whole-store wiki lint (`spec_lint.lint_wiki`, the entry point `emit_wiki`
      uses); on any finding, restore the backed-up files byte-for-byte, exit
      non-zero, and name the reason (including the linking page for a stranded
      wikilink).
- [x] 3.4 [req: wiki-remove-verb] In `cmd_wiki_remove`, on a clean lint call
      `sc.wiki_autocommit(store, [page, index, log], "shipd-wiki: remove %s" % slug)`
      so the touched files commit inside a git work tree and nothing is attempted
      outside one.
- [x] 3.5 [req: wiki-remove-verb] Register the `wiki-remove <slug>` subcommand in
      `spec_status.py`'s argument parser with a `--personal` flag, dispatch it to
      `cmd_wiki_remove`, and confirm `test_wiki_remove.py` passes.

## 4. Personal-store targeting on emit

- [x] 4.1 [req: wiki-emission] In `test_memory_store.py`, add an emit case:
      `spec_emit.py wiki --from <staging> --personal` installs the staged set
      into `<memory_dir>/wiki` with the same lint/rollback guarantees and leaves
      the workspace store untouched. Run it and observe it fail — `--personal`
      does not exist yet.
- [x] 4.2 [req: wiki-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py`, add a `personal` parameter
      to `emit_wiki` resolving the destination via `sc.memory_store_dir(root)`
      when set (bypassing the workspace resolution) with identical backup, lint,
      and restore semantics, and add a `--personal` flag to the `wiki` subparser
      threaded into the `emit_wiki` call. Confirm the section-4 emit case passes.

## 5. Packaging

- [x] 5.1 [req: memory-store-key] Bump the plugin version to `0.6.21` in
      `plugins/s/.claude-plugin/plugin.json` (this change touches
      `plugins/s/`), then run the engine unit suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it passes.
