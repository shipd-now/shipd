<!-- doc-type: how-to -->

# Write docs

`/s:document` writes or revises documentation against the shipd
documentation standard. It covers the files under `docs/`, and any other
documentation you point it at.

The standard lives in one rules file inside the plugin. The skill reads that
file before it writes a word, and never restates its rules. A docs lint
checks the mechanical half of the standard; the skill checks the rest.

The skill edits documentation only. It never commits, pushes, or opens a pull
request. The workflow that invoked it ships the edit in its own change.

## When to use it

- **Write a new doc.** Add a page under `docs/` for a feature.
- **Rewrite an existing doc.** Bring an old page up to the standard.
- **Fix a lint failure.** Clear the errors CI reports on a doc.

CI lints every file under `docs/` except `docs/retros/`.

## How to run it

1. Run `/s:document` and name the docs to write or revise.
2. The skill classifies each doc as concept, how-to, or reference, from the
   job the doc does.
3. The skill writes or rewrites each doc against the standard.
4. The skill runs the docs lint over every file it touched.
5. The skill fixes every error and re-runs the lint, until the lint exits
   clean.
6. The skill self-reviews the judgement rules the lint cannot check.
7. The skill reports each file, its doc type, its lint result, and the
   self-review result.

### Rewrites and caps

A rewrite keeps every fact the doc carries. The skill cuts repetition, but
never a fact the reader needs.

A doc over its cap gets split or cut. The skill never changes a doc's type
marker to buy a larger cap. A doc that does two jobs becomes two docs.

### Lint errors and warnings

A lint error blocks: the lint exits non-zero, and the doc cannot ship. A lint
warning is advice. The skill reads it, then fixes the sentence or leaves it
deliberately.

## Reference

### Doc types

Every doc opens with a doc-type marker on its first line, such as
`<!-- doc-type: how-to -->`.

| Doc type | Job | Line cap |
| --- | --- | --- |
| concept | Explains what something is and why it exists. | 100 lines |
| how-to | Walks the reader through one task. | 150 lines |
| reference | Lists verbs, flags, keys, or fields for lookup. | 250 lines |

The cap counts every line in the file, including headings, code fences, and
blank lines.

### The diagram rule

A doc carries at most one mermaid diagram. A diagram earns its place only
where it carries structure that prose cannot:

- three or more components that interact;
- a lifecycle with branches;
- a topology.

A diagram never restates an adjacent list or table.
