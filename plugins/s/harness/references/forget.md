# /s:forget — reference

The fuller protocol behind the forget command's workflow: matching, and the
guards the engine enforces on removal.

## Matching a description to a slug

Retrieval is index- and grep-based over markdown — no embeddings, no vector
store, no search service. In order:

1. `cat wiki index --personal` — keep the `- [[memory-<subject>]] —
   <summary>` entries; the `memory-` prefix is the only page set in scope.
2. Read-only `grep` the store root's `wiki/` subdir for the description's
   subject terms. The store root is the one `wiki-show --personal` printed.
3. `cat wiki <slug> --personal` on each candidate, to judge the match on
   the page's actual statement rather than on its slug alone.

Three outcomes, and only three:

- **Exactly one match** — confirm, then remove.
- **No match** — report it and remove nothing. Do not guess at the nearest
  page; a wrong removal is worse than a missed one.
- **Several matches** — present each candidate's slug and summary, ask
  which to forget, and proceed for the single page the user picks. Never
  remove more than one page in a run.

## Confirmation

Removal is destructive, so exactly one confirmation always precedes it, and
the affirmative choice is never the default. Two options only — remove or
keep — with the matched slug and summary visible in the question itself.

An interaction that comes back rejected or interrupted is **not** a
decline: re-offer the same two choices as a plain-text numbered list and
wait for a typed reply. Only an explicit keep ends the run as a decline.

## What the engine guarantees

```
python3 "$S/spec_status.py" --root <repo-root> wiki-remove <slug> --personal
```

The verb, not the command body, performs the deletion. It removes the page,
drops its index entry, appends a dated `remove` log line, runs the
whole-store wiki lint, and restores every affected file byte-for-byte on
any finding. So the removal inherits the store's guards for free:

- a **stranded `[[link]]`** — another page still links the removed slug —
  fails the lint and the removal is rolled back;
- a **reserved slug** (`index`, `queue`, `log`, `schema`) is refused.

On a non-zero exit, surface the finding verbatim and report that nothing
was removed. Never edit store files in place to force a removal the lint
refused; fix the linking page through `/s:remember` (a re-emit) first, then
retry.
