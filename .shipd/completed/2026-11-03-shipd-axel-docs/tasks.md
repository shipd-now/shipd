# shipd-axel-docs tasks

Author with `/s:document`: lint with `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-axel.md` until it exits 0. The facts and the diagram shape are fixed in `plan.md`'s `## Implementation`; add no other claims.

## 1. Write the page

- [x] 1.1 [req: shipd-axel-page] Create `docs/shipd-axel.md` with `<!-- doc-type: concept -->` on line 1 and the title `# The shipd-axel GitHub App`, covering every fact listed in `plan.md`.
- [x] 1.2 [req: shipd-axel-page] Add the one `flowchart TD` swimlane diagram to `docs/shipd-axel.md` per `plan.md`, with no `(planned)` labels.

## 2. Verify

- [x] 2.1 [req: *] Run the docs lint on `docs/shipd-axel.md` and confirm exit 0, confirm the file is at most 100 lines, and confirm no link points at the App's private source repository.
