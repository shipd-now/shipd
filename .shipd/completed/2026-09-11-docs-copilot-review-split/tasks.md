# Tasks — docs-copilot-review-split

## 1. Split the guide

- [x] 1.1 [req: copilot-review-guide] Create `docs/copilot-review-reference.md`
      with `<!-- doc-type: reference -->` as line 1 and an opening link back
      to `copilot-review.md`, moving from today's `docs/copilot-review.md`
      the content `plan.md` §"Content moves, it is not re-derived" routes to
      the reference: the managed-file table, the two-mode comparison table
      with the pending-first rule, the CLI reviewer run sequence, the poll
      fallback with its fail-open guarantee and 20-second/15-minute bounds,
      the verdict table with the last-line-only rule, `SHIPD_GATE_FAIL_OPEN`
      with `gh variable set` and the pair-with-token guidance, the trust
      boundary, tokens and permissions with the fork-PR limit, the
      poll-scoped private-repo note with the fail-soft setup checkout, the
      report states table with foreign/`--force`, and scope and limits.
      Compress the retracted-bootstrap history to one line. Add no diagram.
      Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review-reference.md`
      and fix findings until it exits 0 at 250 lines or fewer.
- [x] 1.2 [req: copilot-review-guide] Rewrite `docs/copilot-review.md` as the
      how-to: `<!-- doc-type: how-to -->` as line 1, an opening link to
      `copilot-review-reference.md`, then in task order: prerequisites, the
      `/s:gate` shortcut note, `shipd copilot add` with its output, the four
      managed file paths and `--root`, commit-and-push with the head-branch
      rule (changed-skill consequence scoped to the CCR/poll surface),
      enabling reviews per-PR and via a branch ruleset (neither needed in
      CLI reviewer mode), the full minimal-PAT reviewer-token recipe with
      `gh secret set COPILOT_GITHUB_TOKEN`, expiry fail-safe semantics, and
      removal restoring the poll fallback, verification via `shipd doctor`'s
      `protection`/`automerge`/`copilot-secret` lines and bare
      `shipd copilot`, and maintenance (re-`add`, `remove`,
      edit-templates-not-copies). Keep the See-also links to `/s:review` and
      to the research report at `.shipd/research/copilot-code-review/report.md`
      (linked doc-relative, with a `../` prefix). Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review.md`
      and fix findings until it exits 0 at 150 lines or fewer.

## 2. Fix inbound links

- [x] 2.1 [req: copilot-review-guide] In `docs/guardrails.md`, update the
      See-also entry at line 217 so its link text matches the how-to's new
      title while still pointing at `copilot-review.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/guardrails.md`
      and confirm it still exits 0.

## 3. Verify

- [x] 3.1 [req: *] Run the CI marker-scoped lint loop locally (the
      `Lint marker-carrying docs` step body from `.github/workflows/ci.yml`)
      and confirm exit 0; confirm `wc -l` reports `docs/copilot-review.md`
      at 150 or fewer and `docs/copilot-review-reference.md` at 250 or
      fewer; confirm every relative link and anchor in both docs resolves,
      including the pair's cross-links and `docs/guardrails.md`'s entry;
      confirm `grep -rn "copilot-review" plugins/s/ .github/` shows no
      plugin or CI file was edited; run `shipd lint
      docs-copilot-review-split` and confirm it reports the change clean.
