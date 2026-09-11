# Tasks — docs-entry-merge

## 1. Merge the entry walk

- [x] 1.1 [req: getting-started-doc, pipeline-follower-docs, harness-mode-docs, install-mode-docs]
      Rewrite `docs/getting-started.md` as the merged six-step how-to per
      `plan.md` §"Merged getting-started shape": marker
      `<!-- doc-type: how-to -->` on line 1, title "Getting started", steps
      `## 1. Install` through `## 6. Watch` with the exact obligations the
      plan lists per step (auto-update + `shipd update` fallbacks, harness
      selection + `shipd harness add`, the observed doctor check list, the
      eco and pr-mode one-liners, artifact purposes with the
      `../.shipd/README.md` grammar link, the three build outcomes,
      `shipd statusline install` with the newest-snapshot note), closing
      with a where-to-next list linking `cheatsheet.md`,
      `what-is-shipd.md`, and `workspaces.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/getting-started.md`
      and fix findings until it exits 0 at 150 lines or fewer.
- [x] 1.2 [req: quickstart-doc] Delete `docs/quickstart.md` with
      `git rm docs/quickstart.md`.

## 2. Rewrite the flanking docs

- [x] 2.1 [req: entry-docs-standard] Rewrite `docs/what-is-shipd.md` prose
      to the standard's sentence caps: add `<!-- doc-type: concept -->` as
      line 1, keep the ☕-opening title, keep the `flowchart TD` mermaid
      fence verbatim, keep the "Today shipd builds itself" paragraph as the
      final prose, and add one relative link to `getting-started.md` in the
      prose before the diagram. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/what-is-shipd.md`
      and fix findings until it exits 0 at 100 lines or fewer.
- [x] 2.2 [req: cheatsheet-doc] Refresh `docs/cheatsheet.md`: add
      `<!-- doc-type: reference -->` as line 1; rebuild the `/s:` table with
      one row per directory in `ls plugins/s/skills/` (adding `document`,
      `explain`, `prd`, `worktree-hooks`); rebuild the `shipd` table with
      one row per verb in the `./plugins/s/bin/shipd --help` banner (adding
      `init`, `search`, `prd`, `wiki`, `config`, `render`, `worktree`,
      `update`); keep the conventions preamble and the `workspace` row's
      precondition note; keep the intro's `getting-started.md` link. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/cheatsheet.md`
      until it exits 0 at 250 lines or fewer, then run every read-only
      `shipd` example whose row names no precondition verbatim from the
      repo root and confirm each exits 0.

## 3. Fix inbound links

- [x] 3.1 [req: readme-retains-onboarding-content] In `README.md`, rename
      the `## Quickstart` section (line ~248) to `## Getting started`,
      retarget its link to `docs/getting-started.md`, and adjust the
      sentence to describe the merged walk (install → doctor → onboard →
      plan/build → watch). Leave the introduction's
      `docs/what-is-shipd.md` + `docs/workspaces.md` link order untouched.
- [x] 3.2 [req: entry-docs-standard] In `docs/copilot-review.md` line 25,
      retarget the `quickstart.md#1-install` link to
      `getting-started.md#1-install`; change nothing else in that file.

## 4. Verify

- [x] 4.1 [req: *] Run the CI marker-scoped lint loop locally (the
      `Lint marker-carrying docs` step from `.github/workflows/ci.yml`) and
      confirm exit 0; confirm `test ! -f docs/quickstart.md`; confirm
      `grep -rn quickstart docs/ README.md --include='*.md'` matches only
      `docs/retros/` paths; confirm `wc -l` for the three entry docs is
      within 100/150/250.
