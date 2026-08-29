# docs-mermaid-diagrams
Status: verified

## Idea

Replace the ASCII ladder diagram in `docs/oracle.md` with a mermaid flowchart
so every diagram in `docs/` renders natively on the website.

### Motivation

The `docs/` pages are published on the website, where `docs/oracle.md`'s
box-drawing ladder diagram renders as an overflowing monospace block behind a
horizontal scrollbar. `docs/what-is-shipd.md` already ships a mermaid flowchart
that renders natively there, so mermaid is the proven diagram form for these
docs.

### Details

- Replace the fenced ASCII ladder-and-capture-loop diagram in `docs/oracle.md`
  (the sole code fence in its "The ladder" section) with a `mermaid` fence whose
  body is the staged diagram `artefacts/oracle-ladder.mmd`, preserving the
  ladder's full semantics: three rungs, the two oracle verdict branches, the
  human answer path, and the capture loop back to the oracle rung.
- Pin the mermaid form in the `shipd-ask` capability's `oracle-user-docs`
  requirement so the diagram stays website-renderable through future edits.

Affected capabilities: `shipd-ask` (modified). Impact: `docs/oracle.md` plus
the delta spec; no code, no dependencies.

### Non-goals

- No conversion of the annotated directory trees (`docs/portable-workspaces.md`,
  `docs/getting-started.md`) or the rules-precedence stack
  (`docs/guardrails.md`) — those are narrow monospace listings, not diagrams,
  and mermaid has no better primitive for them.
- No change to any CLI command/output/JSON/markdown-example fence in `docs/`.
- No change to `docs/what-is-shipd.md`'s existing mermaid diagram.
- No README changes — its box-art wordmark banner is intentional ASCII art
  governed by its own capabilities and outside the requested `docs/` scope.

## Implementation

- **One true diagram exists.** A box-drawing-character sweep across all ten
  `docs/**/*.md` files found box-drawing characters only in `docs/oracle.md`
  (the ladder); every other fenced block in `docs/` is a command, command
  output, JSON, or a markdown example. The change is therefore one fence
  replacement plus its spec pin.
- **The replacement diagram is authored here, as a staged artefact.** The exact
  mermaid source lives at `artefacts/oracle-ladder.mmd` and is copied verbatim
  into the fence, so the executor makes no design decisions. Rejected:
  describing the diagram in prose for the executor to draw — that invites
  semantic drift from the original ladder.
- **Style matches the existing mermaid diagram** in `docs/what-is-shipd.md`:
  a `flowchart` with quoted labels, `<br/>` line breaks, labeled edges, and a
  dotted edge for the feedback loop, keeping the docs' diagrams uniform. Angle
  brackets inside labels are written as HTML entities (`q-&lt;slug&gt;`) so the
  mermaid parser never sees a raw `<slug>`.
- **The spec pin is a MODIFIED delta on `oracle-user-docs`** (capability
  `shipd-ask`), which already governs `docs/oracle.md`'s diagram; the delta adds
  that the ladder diagram is a `mermaid` code fence, not ASCII art. Rejected: a
  new docs-wide "mermaid diagrams" capability — only one other doc carries a
  diagram and it is already mermaid, so a capability would govern nothing.
- Risk: mermaid's auto-layout arranges nodes differently from the hand-drawn
  ladder. Guarded by `flowchart TD` (rungs stay top-to-bottom) and by scenarios
  that check semantic content — rungs, verdict branches, capture loop — never
  pixel layout.
