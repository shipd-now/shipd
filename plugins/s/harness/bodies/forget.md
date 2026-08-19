<!-- description: Remove one captured preference from the personal memory store, confirmed first — the remove counterpart to `/s:remember`. -->
# /s:forget — remove a memory from the personal store

Take a free-text description of a captured preference, find the
`memory-<subject>` page it names, confirm with the user, and delete that page
through the engine. You decide only **which** slug and **whether** the user
confirmed; the engine performs the safe deletion. Never edit a store file in
place.

<!-- include:preamble -->

Every verb below runs as `python3 "$S/spec_status.py" --root <repo-root>
<verb …> --personal`, where `<repo-root>` is the invoking repo. `--personal`
resolves the store at `<memory_dir>/wiki` (default `~/.shipd-memory/wiki`) by
fixed path — one durable store, no base/job split. An argument carries the
description of the memory to remove (e.g. "my editor preference"); without one,
ask what to forget and wait for a description before doing anything.

1. **Resolve the personal store.** `wiki-show --personal` failing names a
   missing store: report that there is nothing to forget and stop, scaffolding
   nothing. Otherwise note the store root it printed and continue.
2. **Locate the matching page.** Read `cat wiki index --personal` and keep the
   `- [[memory-<subject>]] — <summary>` entries; read-only `grep` the store
   root's `wiki/` subdir for the description's subject terms; read candidates
   with `cat wiki <slug> --personal` and judge the match on the page's
   statement, not on its slug alone. Retrieval is index- and grep-based over
   markdown — no embeddings, no search service. Three outcomes, and only three:
   - **exactly one match** — go to step 3;
   - **no match** — report that nothing stored matches, remove nothing, and
     stop. Never guess at the nearest page: a wrong removal is worse than a
     missed one;
   - **several matches** — present each candidate's slug and summary, ask which
     to forget, and continue for the single page the user picks. Never remove
     more than one page in a run.
3. **Confirm, then remove.** Removal is destructive, so exactly one
   confirmation always precedes it, offering two options — "Remove it" and
   "Keep it" (the default, so the affirmative is never the default).
<!-- if:question-dialogs -->
   Ask it as a single AskUserQuestion dialog in a prose-free turn: the matched
   slug and summary ride inside the dialog's own fields, not in surrounding
   chat. Never treat a rejected or interrupted dialog as a decline — re-offer
   the same two options as a numbered list and wait for a typed reply.
<!-- else -->
   Ask it as a plain-text numbered list of the two options, naming the matched
   slug and its summary, and read the answer from the user's typed reply.
<!-- end -->
   On the affirmative choice **only**, remove the page:
   ```sh
   python3 "$S/spec_status.py" --root <repo-root> wiki-remove <slug> --personal
   ```
   The verb deletes the page, drops its index entry, appends a dated `remove`
   log line, and lints the whole store, restoring byte-for-byte on any finding
   — so a stranded `[[link]]` from another page rolls the removal back. On a
   non-zero exit, surface the finding verbatim and report that nothing was
   removed; never edit store files in place to force a removal the lint
   refused. On the negative choice, run nothing and report the memory kept.
4. **Report and stop** — in a line or two: the description you resolved, the
   page removed (or kept, or that nothing matched), and the store the run acted
   on. `/s:memory` lists what remains; `/s:remember` captures a new memory.
<!-- if:file-references -->
   The matching heuristics and the removal guards the engine enforces are
   written out in {refs}/forget.md.
<!-- else -->
   The matching heuristics and the removal guards the engine enforces are not
   available as a separate file here. Say so if the user asks for them, state
   that you would have read the forget reference for that detail, and answer
   from the lint finding the verb printed — it names the guard that fired.
<!-- end -->
