<!-- doc-type: how-to -->

# The wiki

The **wiki** is the store of durable knowledge that the [oracle](oracle.md)
answers from. Its pages hold the standing positions a team has settled, so an
agent reads a decision instead of asking a person again.

A repository in a workspace uses the workspace store. A repository with no
workspace uses its own repo-local fallback store, at `wiki/` under its content
directory. Both stores share one layout and one page grammar.

`/s:teach` writes to the store, and the oracle answers from it.

## When to use it

Run `/s:teach` for any of three jobs:

- **Distil decisions.** Turn the repository's epics, specs, and plans into
  wiki pages the oracle can cite.
- **Drain the queue.** Turn answered queue entries into proper pages.
- **Correct a standing answer.** Replace a recorded position that no longer
  holds.

You rarely need a sweep after every build. Right after `/s:build` marks a
change `verified`, the teacher agent distils that one change into the workspace
store. The teacher runs no interview and touches at most five pages. It skips
a repo-local fallback store. `/s:teach` stays the full sweep.

A preference about you, not about the workspace, belongs in
[personal memory](memory.md).

## How to run it

### Teach the wiki

Run the skill bare for the full sweep, or pass a topic to narrow it:

```sh
/s:teach
/s:teach shipd-wiki
```

The topic can name a capability, an epic slug, or a subject keyword. The skill
runs these steps:

1. **Resolve the store.** It finds the workspace store, or the fallback store.
   It scaffolds an absent store once.
2. **Scan the spec surfaces.** It reads epic decisions, verified capabilities,
   research reports, and the decisions of completed plans. A declared focus
   project's surfaces come first.
3. **Distil into pages.** Each page cites its backing artifact by name, such as
   `epic/<slug>` or `verified/<capability>`. The skill updates an existing page
   before it adds a new one.
4. **Stay bounded.** One run touches at most 15 pages. The log records what the
   run covered, so the next run continues from there.
5. **Interview once, only if needed.** One question round opens for gaps,
   contradictions, and promotion offers. With none of those, no round opens.
6. **Queue what you defer.** A question you defer joins the queue with
   `Answer: pending`, so a later run picks it up.
7. **Drain the queue.** Each answered queue entry becomes page content, and its
   block leaves the queue. An advisory answer keeps its `Authority: advisory`
   line on the page.
8. **Write once.** The skill stages every touched file and installs them in one
   write. The write runs the wiki lint and restores the store on any finding.

When the repository has neither a workspace nor a content directory, the skill
stops and names both. `/s:init wiki` scaffolds a store for that repository.

### Correct an answer

Point the skill at one recorded consultation in a change's plan:

```sh
/s:teach dark-mode-toggle Q1
```

The skill skips the sweep and runs these steps:

1. It prints the entry from the plan's `## Questions and answers` section.
2. It asks one question: the corrected position, and what it rests on.
3. It updates the wiki page the entry cites, rather than adding a duplicate.
4. It keeps your typed correction verbatim in `sources/`.
5. It drains the entry's queue block in the same write.

The skill reads a merged change's plan too. When the change or the `Q<n>` entry
does not exist, the skill reports that and writes nothing.

During planning, `/s:plan` names this form for each oracle consultation it
records.

### Promote to a base store

A base store holds knowledge that serves every workspace. When a base store
sits beneath your store, `/s:teach` sorts each page into one of two kinds:

- **job-scoped** — knowledge specific to this workspace. It lands in your
  store, as by default.
- **job-independent** — a convention or position that would serve every
  workspace. It becomes a promotion offer in the question round.

An accepted offer installs into the base store only, through a second staged
write. Promotion never removes a page from your store. Without a base store,
the skill sorts nothing and offers no promotion.

## Reference

### The store's files

| entry | what it holds |
| --- | --- |
| `index.md` | The page catalogue: one `- [[slug]] — <summary>` line per page. |
| `queue.md` | The oracle's pending questions, one `## q-<slug>` block each. |
| `log.md` | One dated entry per store event, appended and never rewritten. |
| `schema.md` | The page grammar: slugs, `[[slug]]` links, and index entries. |
| `wiki/` | The pages, one `wiki/<slug>.md` file each. |
| `sources/` | Answers preserved verbatim, as dated, add-only files. |

### The verbs

| verb | what it does |
| --- | --- |
| `shipd wiki` | Report the store: root, chain, base, pages, coverage, pending questions, last log. |
| `shipd wiki init` | Scaffold the store. It refuses a store that already exists. |
| `shipd lint --wiki` | Validate the whole store, and print `OK: wiki is valid.` when it passes. |

[Personal memory](memory.md) covers your own preferences.
[Workspaces](workspaces.md) covers where a store lives and how stores chain.
