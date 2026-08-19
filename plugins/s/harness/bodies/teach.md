<!-- description: Distill this repo's spec artifacts and answered queue entries into the workspace wiki through one staged, lint-gated write. -->
# /s:teach — spec artifacts → workspace wiki pages

Fill the workspace wiki that `/s:ask` reads from: scan this repo's durable spec
surfaces, distill them into pages, interview the user only on what the scan
cannot settle, and install everything through one staged emit. Never edit a
store file in place — every mutation goes through the emit, which backs up,
installs, lints the whole store, and restores byte-for-byte on any finding.

<!-- include:preamble -->

Store reads and the queue write run as `python3 "$S/spec_status.py" --root
<repo-root> <verb …>`; the one store write is `python3 "$S/spec_emit.py"`. An
optional argument narrows the run to one topic or surface.

1. **Resolve the store.** `wiki-show` prints the store root, page count,
   coverage, last log entry, and a `base:` line reporting any layered base
   store. Branch on it:
   - **no workspace** — stop, name the missing workspace, and point the user at
     `workspace-init <path>`. Invent no store location and write nothing;
   - **workspace, no store** — scaffold once with `wiki-init` (it refuses an
     existing store), then continue;
   - **store present** — continue.

   An argument of the form `<change> Q<n>` (e.g. `dark-mode-toggle Q1`) is a
   different flow: skip steps 2–5, read `cat change <change>`, print that
   `### Q<n>` ledger entry in full, run one typed round for the corrected
   standing position, and install it through step 6 — updating the page the
   entry **Cited** instead of adding a near-duplicate slug, staging the
   correction verbatim as a dated `sources/` file, and dropping the entry's
   `Queued: q-<slug>` block. A missing change, or a ledger with no `Q<n>` of
   that number, stops the run without writing anything.
2. **Scan the surfaces through engine reads only** — never a raw read of
   `.shipd/` internals. Decision-dense first: `cat epic <slug>` (its Decisions
   and Design), `cat verified <capability>`, `cat research <slug>`,
   `project-show <slug>`, then completed changes' `cat change <slug>`
   implementation decisions. When `workspace-show` prints a `focus:` line, scan
   that project first. Then read the existing wiki — `cat wiki index`, then
   `cat wiki <slug>` for every page your surfaces bear on — plus, on `base:
   <path> (present)`, the base store's index and pages through the same reads
   rooted at that path. Widen with read-only `grep` under the store dir; never
   write through grep.
3. **Distill into pages.** Author kebab-case `wiki/<slug>.md` pages in the
   store's `schema.md` grammar (`cat wiki schema`), each naming the repo
   artifact behind its position and each carrying a matching index entry.
   **Update, don't duplicate** an existing page, and treat a subject the base
   store already covers as covered. Bound the run to 5–15 page touch-ups. With
   a base present, classify each page and each drained answer as job-scoped
   (the default) or job-independent — the promotion candidates for step 4.
4. **Interview only on gaps, contradictions, and promotion offers** — a
   decision the surfaces reference but leave unstated, two surfaces asserting
   incompatible positions, or a job-independent page better held in the base
   store. None of those, no interview. Otherwise run one batched typed round: a
   visible context brief, then plain-text numbered options-first questions with
   the recommendation first, answered by typed reply. Queue whatever the user
   defers, so it compounds instead of vanishing:
   ```sh
   python3 "$S/spec_status.py" --root <repo-root> wiki-queue-add <slug> \
     --question "<decision>" --options "<options>" \
     --recommendation "<lean>" --origin "teach"
   ```
5. **Drain the answered queue.** Read `cat wiki queue`; for every `## q-<slug>`
   block whose `Answer:` is not `pending`, distill it into page content and
   remove that block from the staged `queue.md`. Pending blocks stay untouched.
6. **Install through one staged write.** Stage into `staging=$(mktemp -d)`,
   mirroring the store layout: each touched `wiki/<slug>.md`; the **full**
   `index.md` (existing entries plus one per touched page); the **full**
   `queue.md` when anything drained; the **full** `log.md` with a fresh
   `## [YYYY-MM-DD] teach | <subject>` entry naming the surfaces covered and
   every drained `q-<slug>`; and interview or drained answers preserved
   verbatim as a fresh dated `sources/<file>` — add-only, so never restage an
   existing source path and never copy repo artifacts there. Then:
   ```sh
   python3 "$S/spec_emit.py" --root <repo-root> wiki --from "$staging"
   ```
   A lint finding means nothing was installed: fix the staged files and re-run.
   Keep every `[[link]]` store-local — a page may only link pages living in the
   store it installs into. Accepted promotions install **separately**, through
   a second staging dir emitted with `--root <base-store-path>` and carrying
   that store's own full `index.md` and `log.md`; promoted pages land in the
   base store only.
7. **Report and stop** — the pages touched, anything promoted, every `q-<slug>`
   drained or queued, and the store(s) written to. `/s:ask` is what reads this
   wiki back; `/s:remember` captures personal preferences instead.
<!-- if:file-references -->
   The ledger-correction mode (`/s:teach <change> Q<n>`), the page grammar, and
   the promotion rules are written out in {refs}/teach.md.
<!-- else -->
   The ledger-correction mode, the page grammar, and the promotion rules are
   not available as a separate file here. Say so if the user asks for them,
   state that you would have read the teach reference for that detail, and
   answer from the store's own `cat wiki schema` grammar and the `base:` line
   `wiki-show` printed.
<!-- end -->
