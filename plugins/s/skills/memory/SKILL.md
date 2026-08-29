---
name: memory
description: >-
  List the durable preferences captured in the personal memory store:
  resolve the personal store, read its index, and print the stored `memory-*`
  pages — the read-only browse counterpart to `/s:remember`. Use when
  asked to "show my memories", "list what you remember", "what preferences
  are stored", "browse the memory store", or "/s:memory". Trigger phrases:
  "show my memories", "list my memories", "what do you remember", "browse
  memory", "/s:memory".
---

# /s:memory — browse the personal memory store

You are the **read path over the personal memory store**. Your job is to show
the user the `memory-<subject>` pages `/s:remember` has captured — the
durable preferences the oracle already consults first. You are the
read-only counterpart to `/s:remember`: remember *writes* the personal
store, and you *list* it.

**You are read-only.** You never mutate any store file and you require no new
engine verb: you resolve the store and read its index, nothing more. There is
no confirmation dialog and no write path in this skill.

**The personal store is a single durable store — there is no base/job split and
no promotion step.** Every store verb here carries `--personal`, which resolves
the personal memory store at `<memory_dir>/wiki` (default `~/.shipd-memory/wiki`)
by fixed path, bypassing workspace discovery.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:memory
v<version>` in your first user-visible status sentence (e.g. "shipd:memory v0.6.24
— listing your captured memories"), so the user can always see which plugin
snapshot the session is running.

The engine script is:

- **STATUS_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (all reads).

Run every engine verb with `python3 STATUS_CLI --root <repo-root> <verb …>
--personal`, where `<repo-root>` is the invoking repo.

## 1. Resolve the personal store

Resolve the personal memory store first:

```
python3 STATUS_CLI --root <repo-root> wiki-show --personal
```

`wiki-show --personal` resolves the personal store at `<memory_dir>/wiki` by
fixed path and prints its root, page count, coverage, and last log entry. Branch
on the outcome:

- **No store** — `wiki-show --personal` fails naming the missing store. Report
  that no memories are stored (the store has not been created yet) and stop.
  **Do not** scaffold anything — this skill is read-only.
- **Store present** — proceed to the listing.

## 2. List the stored memories

Read the store's catalogue:

```
python3 STATUS_CLI --root <repo-root> cat wiki index --personal
```

The index holds one `- [[<slug>]] — <summary>` entry per page. Keep only the
entries whose slug begins with `memory-` — those are the captured memory pages
(`/s:remember` writes exactly this `memory-<subject>` grammar). Print the
filtered entries to the user, each as its slug and summary, so they can see what
has been captured.

- When the store holds **at least one** `memory-*` page, print those entries.
- When the store holds **no** `memory-*` page (an empty store, or a store with
  only non-memory pages), report that no memories are stored.

## 3. End

Report the listing in a compact form: the personal store the run read, and the
`memory-*` pages it holds (or that none are stored). This skill mutates nothing
and asks nothing — it reads the index and prints it, then stops.
