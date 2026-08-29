<!-- description: Capture the user's durable preferences into the personal memory store as `memory-*` pages, through one confirmed, staged write. -->
# /s:remember — a stated preference → a personal memory page

Turn a preference the user states (or clearly expressed this session) into
`memory-<subject>` pages in the personal memory store the oracle
consults first. You are the personal-store counterpart to `/s:teach`: teach
fills the *workspace* wiki, you fill the *personal* store.

<!-- include:preamble -->

Reads run as `python3 "$S/spec_status.py" --root <repo-root> <verb …>
--personal`; the one write is `python3 "$S/spec_emit.py" … --personal`.
`--personal` resolves the store at `<memory_dir>/wiki` (default
`~/.shipd-memory/wiki`) by fixed path — one durable store, no base layering, no
promotion. Never edit a store file in place: the emit backs up, installs, lints
the whole store, and restores byte-for-byte on any finding. An optional
argument carries the preference to capture; without one, take candidates from
the session.

1. **Resolve the personal store.** `wiki-show --personal` fails naming a
   missing store — scaffold once with `wiki-init --personal` (it refuses an
   existing store), then continue.
2. **Extract candidates** — from the argument when given, otherwise from the
   session. Discrete standing preferences only: a tool choice, a tone, a
   formatting convention. One-off task details and ambient noise are not
   memories. Give each candidate a kebab-case `<subject>`.
3. **Reconcile against what is stored.** Read `cat wiki index --personal`,
   read-only `grep` the store's `wiki/` subdir for each candidate's terms, and
   read the likely pages with `cat wiki <slug> --personal`. Retrieval is index-
   and grep-based over markdown — no embeddings, no search service. Classify:
   - **add** — the store records nothing like it → a new page;
   - **update** — an existing `memory-<subject>` page covers it but the new
     information changes it → re-emit that whole page, never an in-place edit;
   - **skip** — an unchanged duplicate → stage nothing for it.

   Each page has exactly this shape, with a kebab-case `<subject>`:
   ```
   # memory-<subject>

   <one-line preference statement>

   - Origin: <invoking-repo>
   - Captured: <YYYY-MM-DD>
   ```
4. **Confirm before writing anything.** This writes durable personal memory the
   user may not have stated verbatim, so present the proposed set first — each
   candidate's classification, target slug, and the one line that would be
   written — as a **plain-text typed round**, never a dialog. Wait for a typed
   go-ahead; revise and reflect back anything the user prunes or amends.
5. **Install through one staged write.** Stage into `staging=$(mktemp -d)`,
   mirroring the store layout: each added or updated
   `wiki/memory-<subject>.md`; the **full** `index.md` (existing entries plus
   one `- [[memory-<subject>]] — <summary>` per touched page); and the **full**
   `log.md` with a fresh `## [YYYY-MM-DD] remember | <subject>` entry. Then:
   ```sh
   python3 "$S/spec_emit.py" --root <repo-root> wiki --from "$staging" --personal
   ```
   A lint finding means nothing was installed: fix the staged files and re-run.
6. **Offer git backing — typed rounds, never automatic.** `git -C <memory_dir>
   rev-parse --is-inside-work-tree` tells you whether the store's parent is a
   repo. When it is not, offer `git init <memory_dir>` **before** step 5, so
   the first captured page rides in the initial commit; a decline skips this
   step entirely and the capture still installs, just uncommitted. Once
   committed, and only where `gh` is authenticated, offer as separate rounds
   `gh repo create shipd-memory --private`, `git -C <memory_dir> remote add
   origin <url>`, and `git -C <memory_dir> push -u origin <branch>`. Print
   those exact commands for later when `gh` is absent or the user declines. A
   failed create or push is non-fatal — the local commit is the durable
   outcome.
7. **Report and stop** — the pages added, updated, and skipped, and the store
   written to. `/s:memory` lists what is stored; `/s:forget` removes one.
<!-- if:file-references -->
   The page grammar, the reconciliation edge cases, and the whole git-backing
   flow are written out in {refs}/remember.md.
<!-- else -->
   The page grammar, the reconciliation edge cases, and the whole git-backing
   flow are not available as a separate file here. Say so if the user asks for
   them, state that you would have read the remember reference for that detail,
   and answer from the page shape in step 3 and the store's own
   `cat wiki schema --personal` grammar.
<!-- end -->
