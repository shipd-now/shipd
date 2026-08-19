# /s:memory — reference

The fuller protocol behind the memory command's read-only listing.

## The personal store

`--personal` resolves the store at `<memory_dir>/wiki` (default
`~/.shipd-memory/wiki`) by fixed path, bypassing workspace discovery. It is
a single durable store — no job/base split, no layering, no promotion. Its
layout:

```
<memory_dir>/wiki/
  index.md      one `- [[<slug>]] — <summary>` entry per page
  queue.md      pending questions
  log.md        dated entries, one per run that wrote
  schema.md     the store's page conventions
  wiki/         the pages themselves, `<slug>.md`
  sources/      add-only verbatim answers
```

## What counts as a memory page

Only a page whose slug begins with `memory-`. That prefix is the grammar
`/s:remember` writes and the only filter this command applies; other pages
in the store are not memories and are not listed. A page's shape:

```
# memory-<subject>

<one-line preference statement>

- Origin: <invoking-repo>
- Captured: <YYYY-MM-DD>
```

## Read-only means read-only

This command runs exactly two verbs — `wiki-show --personal` and
`cat wiki index --personal` — and requires no engine verb of its own. It
never scaffolds a missing store (that is `/s:remember`'s first step), never
edits a page, and asks no confirmation, because it changes nothing.

A `wiki-show --personal` failure naming a missing store is a normal
outcome, not an error to repair: report that no memories are stored yet and
stop.

## Empty outcomes

Distinguish them in the report:

- **No store** — nothing has ever been captured.
- **Store present, no `memory-*` page** — the store exists but holds no
  memories (it may still hold other wiki pages).

Both end the run; neither is a failure.
