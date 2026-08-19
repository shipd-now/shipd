<!-- description: List the durable preferences captured in the personal memory store — the read-only browse counterpart to `/s:remember`. -->
# /s:memory — browse the personal memory store

Show the user the `memory-<subject>` pages `/s:remember` has captured. You are
**read-only**: you resolve the store, read its index, and print it. You mutate
nothing, scaffold nothing, and ask nothing.

<!-- include:preamble -->

Both verbs below run as `python3 "$S/spec_status.py" --root <repo-root>
<verb …> --personal`, where `<repo-root>` is the invoking repo. `--personal`
resolves the store at `<memory_dir>/wiki` (default `~/.shipd-memory/wiki`) by
fixed path, bypassing workspace discovery — one durable store, no base/job
split.

1. **Resolve the personal store.** `wiki-show --personal` prints its root, page
   count, coverage, and last log entry. A failure naming a missing store is a
   normal outcome, not an error to repair: report that no memories are stored
   yet and stop. Do **not** scaffold one — `/s:remember` creates the store.
2. **List the captured memories.** `cat wiki index --personal` holds one
   `- [[<slug>]] — <summary>` entry per page. Keep only the entries whose slug
   begins with `memory-` — the grammar `/s:remember` writes, and the only page
   set in scope — and print each kept entry as its slug and summary. Where the
   store holds no `memory-*` page (an empty store, or one holding only other
   wiki pages), report that no memories are stored.
3. **Report and stop** — the store the run read and the pages it holds, in a
   compact form. Distinguish the two empty outcomes: no store at all, versus a
   store holding no memories. Neither is a failure. `/s:remember` captures a
   new memory; `/s:forget` removes one.
<!-- if:file-references -->
   The store layout and the `memory-*` page grammar are written out in
   {refs}/memory.md.
<!-- else -->
   The store layout and the `memory-*` page grammar are not available as a
   separate file here. Say so if the user asks for them, state that you would
   have read the memory reference for that detail, and answer from the store's
   own `cat wiki schema --personal` grammar.
<!-- end -->
