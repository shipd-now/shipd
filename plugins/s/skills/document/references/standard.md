<!-- doc-type: reference -->

# The shipd documentation standard

This file is the one source of the shipd writing rules. `SKILL.md`, other
skills, and `AGENTS.md` point here by path; none of them restates a rule.

The rules adapt ASD-STE100 — the simplified technical English of aerospace
maintenance manuals — to software prose. One part of STE does not survive the
move. Its controlled dictionary forbids ordinary software vocabulary, so the
shipd glossary below replaces it.

`scripts/docs_lint.py` checks the mechanical rules. The author checks the
rest, because they need judgement.

## Core rules

These seven rules govern every piece of shipd prose: documentation, plan and
spec artifacts, commit messages, pull request bodies, and conversational
replies.

1. **Write in the active voice.** Name the actor, then the action. Write "the
   engine writes the spec", never "the spec is written".
2. **Keep a descriptive sentence to 25 words or fewer.** A descriptive
   sentence states what something is, or how it behaves.
3. **Keep a procedural sentence to 20 words or fewer.** A procedural sentence
   tells the reader to act. Steps live in numbered lists.
4. **Give each sentence one text category.** A sentence either describes or
   instructs, never both. Split the sentence that does both.
5. **Keep a paragraph to six sentences or fewer.** A longer block of prose
   becomes two paragraphs, or a list.
6. **Choose the specific verb.** Replace "make", "do", and "take" with the
   verb that names the action: build, run, claim, resolve.
7. **Keep a noun cluster to three words or fewer.** Break a longer cluster
   with a preposition.

Rule seven in practice: "the review gate status check" becomes "the status
check for the review gate".

One more rule binds the seven together: **one word carries one meaning**.
Never vary a term for style. A reader who meets two words for one thing looks
for a distinction that does not exist.

## Documentation rules

These rules apply to files under `docs/`, on top of the core rules.

### The doc-type marker

Every doc opens with an HTML comment on its first line:

```
<!-- doc-type: concept -->
```

The marker takes one of three values:

- **concept** — explains what something is and why it exists.
- **how-to** — walks the reader through one task.
- **reference** — lists verbs, flags, keys, or fields for lookup.

GitHub renders the comment as nothing, which is why the marker is a comment
and not YAML frontmatter. Frontmatter would render as a table above the doc.

### Line caps

| doc type | cap |
|---|---|
| concept | 100 lines |
| how-to | 150 lines |
| reference | 250 lines |

The cap counts every line in the file, including headings, code fences, and
blank lines. A doc over its cap gets split or cut. The cap has no exceptions:
a doc that cannot fit is really two docs.

Write one doc for one job. A concept doc that starts listing flags has become
a reference doc; move the flags.

### Diagrams — the structural test

A mermaid diagram earns its place only when it carries structure that prose
cannot. Exactly one of these three conditions justifies a diagram:

- three or more components that interact,
- a lifecycle with branches, or
- a topology.

Two further limits apply. A doc carries at most one diagram. A diagram never
restates an adjacent list or table — a picture of a list is noise, and it goes
stale on the next edit.

Keep a mermaid fence as mermaid source. GitHub renders it natively, so the doc
needs no rendering step.

### The shipd glossary

Each term below carries exactly one meaning across every shipd surface. Use
the term for that meaning, and use no synonym for it.

| term | meaning |
|---|---|
| change | One unit of planned work: one worktree, one branch, one pull request. |
| worktree | The git checkout a change is built in, at `.worktrees/<change>`. |
| epic | A feature decomposed into member changes over shared decisions. |
| member | One change that an epic's table lists. |
| workspace | The repository that holds the projects, initiatives, and wiki a team shares. |
| initiative | A workspace brief that states the outcomes an epic delivers against. |
| store | An external repository that holds shipd artifacts for other repositories. |
| wiki | The workspace's durable knowledge pages, which the oracle reads. |
| oracle | The non-interactive answerer that consults the wiki before a human. |
| gate | A required check that blocks a merge until it passes. |
| capability | One named area of behavior that the spec library documents. |
| spec | The requirements and scenarios file for one capability. |

Reserve each term for its row. A "change" is never a "task", an "item", or a
"ticket". An epic's "member" is never a "child" or a "sub-change".

## Voice digest

shipd voice — apply these to every reply, not only to docs:

- Write in the active voice: name the actor, then the action.
- Keep descriptive sentences to 25 words, instructions to 20.
- Give each sentence one job — describe, or instruct, never both.
- Keep paragraphs to six sentences or fewer.
- Choose the exact verb over "make", "do", or "take".
- Keep noun clusters to three words or fewer.
- Use one word for one meaning; never vary a term for style.
- Cut any sentence that carries no information.
