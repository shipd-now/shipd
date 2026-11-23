# Wiki schema

The workspace knowledge store. Conventions (enforced by `spec_lint.py --wiki`):

- **Pages** live at `wiki/<slug>.md` with kebab-case slugs. The slugs `index`,
  `log`, `queue`, `schema`, and `sources` are reserved.
- **Wikilinks** `[[slug]]` in a page or in `index.md` (outside fenced code
  blocks) must resolve to an existing page.
- **Index** — `index.md` catalogs every page as `- [[slug]] — <summary>`; the
  entry set and the page set must match exactly.
- **Log** — `log.md` records append-only entries as level-2 headers
  `## [YYYY-MM-DD] <op> | <subject>`.
- **Queue** — `queue.md` holds pending questions as `## q-<slug>` blocks, each
  with non-empty `- Asked:`, `- Question:`, `- Options:`, `- Recommendation:`,
  and `- Answer:` lines (`Answer: pending` until answered).
- **Sources** under `sources/` are immutable: add-only, never overwritten.
