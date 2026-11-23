<!-- doc-type: how-to -->

# Research

A **research report** answers one question, with a citation for each fact.
Every load-bearing claim in it carries an inline `[n]` marker. Each marker
points at a source that `/s:research` actually fetched from the web.

The report is a standalone artifact. The engine installs it under the content
directory's `research/` folder, at `research/<slug>/report.md`. An epic links
the report from its `## Research` section, and [`/s:epic`](epics.md) reads it as context
it need not derive again.

`/s:research` searches, composes, installs, and stops. It never plans or
builds anything from what it finds.

## When to use it

Run `/s:research` when a decision depends on facts outside the repository:
vendor options, standards, prior art, or current practice. Run it before
`/s:epic`, so the epic starts from cited findings instead of model memory.

Skip it when the answer lives in the code or the spec library. A human
requests a report; no autopilot stage runs this skill.

## How to run it

Pass the question as the argument:

```sh
/s:research which payment APIs should we integrate?
```

The skill authors the report in its own worktree, `.worktrees/research-<slug>`,
on branch `change/research-<slug>`. The report ships in one pull request, like
any change.

### The clarification round

The skill researches a specific question without asking anything. It asks
only when the question is too vague to research: no scope, audience,
or success criterion it can infer. Then it asks one batched round of two or
three questions, each with a recommended default first.

### Web tools are required

The skill searches with the session's built-in WebSearch and WebFetch tools,
and nothing else. When either tool is unavailable, the skill stops and names
the missing tool. It never writes findings from model memory, because an
uncited report defeats its purpose.

### The five stages

The skill runs the question through five stages, in order:

1. **Decompose** — it breaks the question into three to six sub-questions.
2. **Search** — it runs a web search for each sub-question.
3. **Select** — it keeps the strongest sources: primary, authoritative, and
   recent where the topic moves.
4. **Extract** — it fetches each source and records each finding with the
   source behind it.
5. **Compose** — it writes the report, with a `[n]` marker on every
   load-bearing claim.

A claim that no fetched source anchors never appears as a finding. The skill
moves it to the gaps and caveats instead. Where sources disagree, the report
records the disagreement.

### The ending

The engine validates the report on install and refuses an invalid one. Once
the install passes, the skill commits the report on its branch and opens the
pull request. It then summarizes the findings and points at `/s:epic`.

## Reference

### The report's sections

| section | content |
| --- | --- |
| `# <title>` | the report title, on line 1 |
| provenance note | `> Prepared by the shipd research skill (/s:research).`, under the title |
| `## Summary` | two or three paragraphs on what the research found |
| one `## <theme>` per sub-question | the themed findings, each claim cited |
| `## Gaps & caveats` | open questions and any claim no source anchors |
| `## Sources` | a numbered list, one entry per fetched source |

Each inline `[n]` marker must match a numbered entry in `## Sources`. The
provenance note marks a report the skill composed, as distinct from a document
someone supplied.

### Listing reports

List the installed reports, across the root and its worktrees:

```sh
shipd list research
```

An epic links a report as
`- [<title>](../../research/<slug>/report.md)` under its `## Research` heading.
