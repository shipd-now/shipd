# /s:research reference — the report grammar

The engine's checks mandate only the **citation skeleton** — the title line, a
numbered `## Sources` section, and `[n]` markers that resolve into it. The
Summary / Findings / Gaps sections are composition guidance you follow.

```
# <report title>

## Summary

Two or three paragraphs stating what the research found, with `[n]` markers on
the load-bearing claims.

## <Theme A — from a sub-question>

Findings for this theme, each load-bearing claim carrying an `[n]` marker that
maps to a listed source [1]. Record source disagreement here rather than
hiding it [2].

## <Theme B — from a sub-question>

...

## Gaps & caveats

- Questions the search did not settle, and any claim that survived extraction
  with no fetched source anchoring it — downgraded here rather than asserted.

## Sources

1. <source title> — <url>
2. <source title> — <url>
```

## Rules

- **Title.** Line 1 is a non-empty `# <title>`.
- **Citations.** Every load-bearing claim carries an inline `[n]` marker whose
  number appears in `## Sources`; at least one marker is required. A markdown
  link `[n](url)` is not a marker, and index expressions inside fenced code
  blocks are skipped, so code samples never trip the check.
- **Sources.** At least one numbered entry (`N. …`), one per source you
  actually fetched. Never list a source you did not read.

## Slug

Choose a kebab-case slug derived from the question — `payment-apis` for "which
payment APIs should we integrate?". You name the slug; the engine owns the path
it installs to.
