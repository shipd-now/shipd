## 1. Search verb in the status CLI

- [x] 1.1 [req: search-verb] Add a `SearchTest` class to
      `plugins/s/skills/build/tests/test_spec_status.py`, modeled on
      `RelatedTest` (same base class and `self.cli` harness), covering: a
      tracked code file match (`git init` + commit in the temp repo, block
      `kind: code`, slug the root-relative path, score counting hits); a
      term hit only under the content directory printing `kind: verified`
      with no `kind: code` block; a NUL-carrying tracked file yielding no
      match; an initiative brief under the workspace anchor's
      `initiatives/<slug>/brief.md` printing `kind: initiative`; a verified
      spec and a code file ranking together by descending score; a non-git
      root still matching a verified spec and exiting `0`; `--json` emitting
      one array with `kind`/`slug`/`score`/`path`; a twelve-match corpus
      capping at ten blocks plus a remainder line; and a no-match run exiting
      non-zero with a single `Error:` line. Run the class and observe every
      test fail — the verb does not exist yet.
- [x] 1.2 [req: search-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, extract the shared
      rank-and-render tail of `cmd_related` (score rows, sort, cap at
      `RELATED_MAX_BLOCKS`, keyed-block/JSON printing, no-match
      `StatusError`) into a module-level helper, and re-express
      `cmd_related` over it with behavior byte-for-byte unchanged.
- [x] 1.3 [req: search-verb] In the same file add
      `_search_initiative_artifacts(root)`: resolve the workspace anchor via
      `sc.resolve_wiki_root(root)`, yield
      `("initiative", slug, brief_path, [brief_path])` for each
      `initiatives/<slug>/brief.md` under `sc.initiatives_dir(anchor)`,
      returning `[]` on any `sc.ConfigError`/`OSError`/`None` resolution.
- [x] 1.4 [req: search-verb] In the same file add
      `_search_code_artifacts(root)`: run
      `git ls-files -z` with `cwd=root` via `subprocess`, return `[]` on any
      failure; skip paths under `sc.specs_dir(root)`, files over 1 MiB,
      files whose first 8192 bytes contain a NUL, and unreadable files;
      yield `("code", relpath, abspath, [abspath])` per surviving file.
- [x] 1.5 [req: search-verb] In the same file add `cmd_search(root, terms,
      as_json=False)` composing `_related_corpus(root)` +
      `_search_initiative_artifacts(root)` + `_search_code_artifacts(root)`
      through the shared rank-and-render helper; wire argparse (`p_search`
      with `terms` nargs="+" and `_add_json_flag`, mirroring `p_related`)
      and the `args.verb == "search"` dispatch. Run the `SearchTest` class
      and the existing `RelatedTest` class; confirm both pass.

## 2. Binary exposure

- [x] 2.1 [req: cli-dispatch] Add a delegation test to
      `plugins/s/skills/build/tests/test_shipd_cli.py` mirroring the
      existing `related` delegation test: `shipd search zzz-no-such-term`
      exits non-zero with `spec_status.py search`'s `Error:` line, and the
      `--help` banner lists `search`. Run it and observe it fail.
- [x] 2.2 [req: cli-dispatch] In `plugins/s/bin/shipd` add
      `"search": ("spec_status.py", ["search"])` to `VERB_TABLE`, a banner
      line `search <term> [term...]` (describing the superset ranked search)
      directly under the `related` line, and add `search` to the trailing
      "read verbs … accept --json" sentence. Confirm the test from 2.1
      passes.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version`
      from `0.6.188` to `0.6.189`.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes with no `textual` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 93 | 18.3k |
| Edit | 16 | 4.7k |
| Read | 13 | 4.6k |
| (no tool) | 0 | 4.1k |
| Agent | 2 | 1.3k |
| **Total** | 124 | 33.1k |
