---
name: forget
description: >-
  Remove a captured preference from the personal memory store: take a free-text
  description of the memory to forget, locate the matching `memory-*` page,
  confirm the removal with a single dialog, and delete it through
  `wiki-remove --personal` — the remove counterpart to `/s:remember`. Use
  when asked to "forget that I prefer …", "remove a memory", "delete what you
  remember about …", "drop that preference", or "/s:forget". Trigger phrases:
  "forget that", "remove a memory", "delete a memory", "forget my preference",
  "/s:forget".
---

# /s:forget — remove a memory from the personal store

You are the **remove path over the personal memory store**. Your job is to take
a free-text description of a captured preference, find the `memory-<subject>`
page it names, confirm with the user, and delete that page through the engine's
`wiki-remove --personal` verb. You are the destructive counterpart to
`/s:remember`: remember *captures* a memory, and you *remove* one.

**You only decide *which* slug and *whether* the user confirmed.** The safe
deletion itself is the engine's: `wiki-remove --personal` removes the page,
drops its index entry, appends a dated `remove` log line, runs the whole-store
wiki lint, and restores byte-for-byte on any finding — so you inherit the
stranded-`[[link]]` refusal and reserved-slug guard without reimplementing them.
You never edit store files in place.

**The personal store is a single durable store — there is no base/job split and
no promotion step.** Every store verb here carries `--personal`, which resolves
the personal memory store at `<memory_dir>/wiki` (default `~/.shipd-memory/wiki`)
by fixed path, bypassing workspace discovery.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `am:forget
v<version>` in your first user-visible status sentence (e.g. "am:forget v0.6.24
— locating the memory to remove"), so the user can always see which plugin
snapshot the session is running.

The engine script is:

- **STATUS_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (the reads and the one remove verb).

Run every engine verb with `python3 STATUS_CLI --root <repo-root> <verb …>
--personal`, where `<repo-root>` is the invoking repo.

An **invocation argument** carries the free-text description of the memory to
remove (e.g. "my editor preference", "the ASCII diagram thing"). When it is
absent, ask the user what to forget and wait for a description before doing
anything.

## 1. Resolve the personal store

Resolve the personal memory store first:

```
python3 STATUS_CLI --root <repo-root> wiki-show --personal
```

`wiki-show --personal` resolves the personal store at `<memory_dir>/wiki` by
fixed path and prints its root, page count, coverage, and last log entry. Branch
on the outcome:

- **No store** — `wiki-show --personal` fails naming the missing store. Report
  that there is nothing to forget (no personal store exists) and stop. **Do
  not** scaffold anything.
- **Store present** — note the store root it printed and proceed to locate.

## 2. Locate the matching `memory-*` page

Find the page the description names. Read the index and grep the store's page
bodies — **read only, never edit**:

```
python3 STATUS_CLI --root <repo-root> cat wiki index --personal
```

Keep only the `- [[memory-<subject>]] — <summary>` entries (slug prefix
`memory-`). Then read-only `grep` the personal store's `wiki/` directory (the
store root `wiki-show --personal` printed, under its `wiki/` subdir) for the
description's subject terms, and read candidate pages with `python3 STATUS_CLI
--root <repo-root> cat wiki <slug> --personal` to judge the match. Retrieval is
index- and grep-based over markdown — no embeddings, no vector store, no search
service.

Resolve to one of three outcomes:

- **Exactly one match** — go to the confirm-then-remove flow (step 3).
- **No match** — report that no stored memory matches the description and remove
  nothing. Stop.
- **More than one match** — present the candidate `memory-*` pages (each with its
  slug and summary) and ask the user which one to forget. Once the user picks a
  single page, continue to the confirm-then-remove flow for that page.

## 3. Confirm, then remove

Removal is destructive, so it always goes through a **single AskUserQuestion**
before any `wiki-remove` runs.

- Issue the AskUserQuestion in a **prose-free turn** — the matched page's slug
  and summary ride inside the dialog's fields (the question/header and options),
  not in surrounding chat prose (the dialog-and-prose-separation rule). Offer two
  options: an affirmative "Remove it" and a negative "Keep it" (the default).
- **On the affirmative selection** — and only then — remove the page:

  ```
  python3 STATUS_CLI --root <repo-root> wiki-remove <slug> --personal
  ```

  `wiki-remove` deletes the page, drops its index entry, appends a dated
  `remove` log line, and runs the whole-store wiki lint, restoring byte-for-byte
  on any finding. If it exits non-zero, surface the finding and report that
  nothing was removed. On success, report the removal.
- **On the negative selection** — run no `wiki-remove`; the page remains. Report
  that the memory was kept and stop.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want
to proceed with this tool use") even when the user tried to answer.
Never treat a rejected or interrupted AskUserQuestion as a decline, a
stop, or an answer. When the user's next message arrives: if it answers
the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply.
Only an explicitly selected or typed stop/decline ends the flow.

## End

Report the outcome in one or two lines: the description you resolved, the page
you removed (or that the memory was kept, or that nothing matched), and the
personal store the run acted on. Then stop.
