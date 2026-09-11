# Tasks — docs-feature-guides

## 1. Rewrite the in-place reference docs

- [x] 1.1 [req: oracle-user-docs] Rewrite `docs/oracle.md` to the standard
      per `plan.md` §"oracle.md keeps every pinned obligation": add
      `<!-- doc-type: reference -->` as line 1, keep the mermaid ladder
      fence, the `ANSWER` example with `Cited:`/`Evidence:` lines, the
      advisory example with its `Authority: advisory` line, the
      `INSUFFICIENT` example, the definitive-evidence bar, the three capture
      tiers with `wiki-queue-answer`/`wiki-queue-discard`, and `/s:teach` as
      the correction path; keep the See-also links to `what-is-shipd.md` and
      `workspaces.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/oracle.md`
      and fix findings until it exits 0 at 250 lines or fewer.
- [x] 1.2 [req: guardrails-key-docs] Rewrite `docs/guardrails.md` to the
      standard per `plan.md` §"guardrails.md keeps every pinned obligation":
      add `<!-- doc-type: reference -->` as line 1; keep both hook events
      over added lines, the rule format with the worked example, the three
      sources and precedence with the built-ins table, add/edit/override
      including the same-named built-in override, cooldown behavior, both
      config kill-switches with the superseded `rules` note and
      `SHIPD_GUARDRAILS=off`, and the token-cost section with the
      deny-for-certain / remind-for-fuzzy guidance; keep the See-also links.
      Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/guardrails.md`
      and fix findings until it exits 0 at 250 lines or fewer.

## 2. Split the PRD guide

- [x] 2.1 [req: prd-user-docs] Create `docs/prd-reference.md` with
      `<!-- doc-type: reference -->` as line 1 and an opening link back to
      `prd.md`, moving from today's `docs/prd.md` the content `plan.md`
      §"Content moves, it is not re-derived" lists: header format and
      recognized keys, the three-status vocabulary with staged re-install
      approval and `shipd lint --prd`, the tier section lists with additive
      nesting and the floor-not-ceiling rule, the `shipd search` example
      block, the `shipd prd` report and roster examples with `cited-by`
      semantics, `shipd render` composition, and the epic `PRD:` header link
      with its lint rule; dissolve the FAQ into the owning sections or drop
      duplicates. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/prd-reference.md`
      and fix findings until it exits 0 at 250 lines or fewer.
- [x] 2.2 [req: prd-user-docs] Rewrite `docs/prd.md` as the concept hub:
      `<!-- doc-type: concept -->` as line 1, covering the discover phase,
      the Initiative → PRD → Epic → Change hierarchy with its mermaid fence
      and the upward-reference direction, workspace storage with chain
      resolution and the no-workspace refusal, the standalone nature, the
      lifecycle and tier overviews, `/s:prd` as the authoring path, and
      relative links to `prd-reference.md` and `workspaces.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/prd.md`
      and fix findings until it exits 0 at 100 lines or fewer.

## 3. Rewrite the supersession-gate concept

- [x] 3.1 [req: supersession-gate-doc] Rewrite `docs/supersession-gate.md`
      to the standard: `<!-- doc-type: concept -->` as line 1, covering why
      a plan goes stale, build's Phase-0 sequence with the
      clean/drift/superseded outcomes, the three finding kinds with their
      meanings, the exit codes, and the self-run
      `python3 plugins/s/skills/build/scripts/spec_status.py check-base`
      invocation (no binary verb exists for it). Add no diagram. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/supersession-gate.md`
      and fix findings until it exits 0 at 100 lines or fewer.

## 4. Verify

- [x] 4.1 [req: *] Run the CI marker-scoped lint loop locally (the
      `Lint marker-carrying docs` step body from `.github/workflows/ci.yml`)
      and confirm exit 0; confirm `wc -l` reports `docs/prd.md` and
      `docs/supersession-gate.md` at 100 or fewer and `docs/oracle.md`,
      `docs/guardrails.md`, and `docs/prd-reference.md` at 250 or fewer;
      confirm every relative link and anchor in the five docs resolves;
      confirm `grep -n 'spec_status\|spec_emit' docs/prd.md docs/prd-reference.md`
      matches nothing; run `shipd lint docs-feature-guides` and confirm it
      reports the change clean.
