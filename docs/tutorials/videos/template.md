<!-- doc-type: how-to -->

# Write a video episode script

Every episode of the shipd video series follows one structure. This guide
walks you through filling it in. Copy the skeleton at the end, then complete
one numbered step per section.

Each episode runs five minutes and holds four to six beats. The
[series overview](index.md) lists the episodes and their roadmap groups.

## Steps

1. Create the file as `<NN>-<slug>.md` in `docs/tutorials/videos/`. Put
   `<!-- doc-type: how-to -->` on line 1. Add the heading
   `# Episode <N>: <title>`.
2. Write `## Introduction` in three to five sentences. State the problem the
   viewer has, what the episode shows, and who it is for.
3. Write `## At a glance` as a two-column table. Use exactly four rows:
   `Roadmap group`, `Runtime`, `Prerequisites`, and `Commands shown`.
4. Write `## Script` with one `### <start>–<end> <beat name>` subsection per
   beat. Start the first beat at `0:00`. Start each later beat where the
   previous beat ends. End the last beat at the runtime.
5. Give each beat two paragraphs. Open the first with `**On screen:**` and
   describe what the viewer sees. Open the second with `**Narration:**` and
   write the words the presenter speaks.
6. Write `## Takeaways` as three dot-points. Each point states one fact the
   viewer keeps.
7. Write `## Next` as one sentence that links the next episode file. In
   episode 10, link `index.md`.
8. Write `## Sources` as a list of links to the docs and specs that ground
   every claim. Read each source before you write the beat that relies on it.
9. Check the file. Run `python3 plugins/s/skills/document/scripts/docs_lint.py`
   on it until the command exits 0.

## Rules for the content

- Use each term of the shipd glossary in its one defined meaning.
- Show only commands that the linked sources document.
- Keep the file at 150 lines or fewer.
- Add no section beyond the six that the skeleton lists.

## Skeleton

```markdown
<!-- doc-type: how-to -->

# Episode <N>: <title>

## Introduction

<Three to five sentences: the viewer's problem, what the episode shows, and
who it is for.>

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | <group name> |
| Runtime | 5 minutes |
| Prerequisites | <what the viewer needs first> |
| Commands shown | <commands in the episode> |

## Script

### 0:00–<end> <beat name>

**On screen:** <what the viewer sees>

**Narration:** <what the presenter says>

### <start>–5:00 <beat name>

**On screen:** <what the viewer sees>

**Narration:** <what the presenter says>

## Takeaways

- <Fact one.>
- <Fact two.>
- <Fact three.>

## Next

<One sentence that links the [next episode](<NN>-<slug>.md).>

## Sources

- [<doc title>](<relative path to the doc>)
```
