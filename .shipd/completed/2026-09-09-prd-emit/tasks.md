## 1. Emit verb

- [x] 1.1 [req: staged-emission] Add PRD emit tests to
      `plugins/s/skills/build/tests/test_spec_emit.py` using the suite's
      temp-workspace fixtures: a lint-clean `basic` PRD installs at the
      workspace's `prds/<slug>/prd.md` with exit 0; a PRD missing a tier
      section prints the findings, leaves nothing installed, and exits
      non-zero; an existing destination refuses without `--replace` and
      succeeds with it; a root with no discoverable workspace exits non-zero
      naming the missing workspace. Run them and observe them fail.
- [x] 1.2 [req: staged-emission] In
      `plugins/s/skills/build/scripts/spec_emit.py`, add
      `emit_prd(root, slug, src, replace)` mirroring `emit_initiative`
      (destination `sc.prd_path`, validation `sl.lint_prd`, install through
      `_install_dir`), the `prd` argparse subparser and dispatch branch, and
      the module docstring's mode entry. Confirm the tests from 1.1 pass.

## 2. Read verb and search surface

- [x] 2.1 [req: mediated-read-verb, search-verb] Add tests to
      `plugins/s/skills/build/tests/test_spec_status.py`: `cat prd <slug>`
      prints the PRD's content with its `--- <path>` separator when a
      workspace-chain member hosts it (nearest member winning); an unknown
      slug exits non-zero naming the expected `prd.md` path; and in the
      `SearchTest` fixtures a `prds/<slug>/prd.md` under the workspace
      anchor produces a `kind: prd` block, while a workspace-less root still
      searches every other surface. Run them and observe them fail.
- [x] 2.2 [req: mediated-read-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add the `prd` branch
      to `cmd_cat` mirroring the `initiative` branch (`sc.resolve_prd`,
      expected-path error via `sc.prd_path`), and add `prd` to the `cat`
      argparse kind choices and the verb docstring. Confirm the `cat` tests
      from 2.1 pass.
- [x] 2.3 [req: search-verb] In the same file add
      `_search_prd_artifacts(root)` beside `_search_initiative_artifacts`
      (anchor via `sc.resolve_wiki_root`, records
      `("prd", slug, path, [path])` from `sc.prds_dir(anchor)`, `[]` on any
      resolution failure) and append it to `cmd_search`'s corpus after the
      initiative surface. Confirm the search tests from 2.1 pass.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version`
      to the next free patch (0.6.195 at build time; main had consumed
      .192-.194 in flight).
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 91 | 26.2k |
| (no tool) | 0 | 5.6k |
| Edit | 16 | 3.4k |
| Agent | 2 | 775 |
| Read | 5 | 252 |
| **Total** | 114 | 36.3k |
