# vertical-overview-diagram
Status: verified

## Idea

Reorder `docs/what-is-shipd.md` so the "Today shipd builds itself" paragraph
follows the "How it fits together" diagram, and flip that mermaid diagram to a
vertical orientation.

### Motivation

On the published docs site the overview diagram's left-to-right `flowchart LR`
layout is wider than the content column, forcing a horizontal scrollbar that
hides most of the pipeline. The user also wants the present-and-future
paragraph ("Today shipd builds itself …") to read as a closing note after the
diagram rather than sitting between the concept prose and the picture.

### Details

- In `docs/what-is-shipd.md`, change the mermaid fence's direction from
  `flowchart LR` to `flowchart TD` so the five stage subgraphs stack
  vertically and fit the site's content column.
- Move the third body paragraph (beginning "Today shipd builds itself —" and
  ending "… without watching it type.") from before the
  `## How it fits together` heading to after the closing mermaid fence, as the
  document's closing prose, byte-identical.
- Pin this layout in the `project-readme` capability (which already governs
  this doc's branding) as a new requirement.

Affected capabilities: `project-readme` (modified — one added requirement).
Impact: `docs/what-is-shipd.md` plus the delta spec; no code, no dependencies.

### Non-goals

- No wording changes to any paragraph or to the diagram's nodes, labels, or
  edges — orientation and document order only.
- No changes to `docs/oracle.md`'s mermaid diagram or any other docs file.
- No README changes.

## Implementation

- **Orientation flips via the graph direction alone.** `flowchart TD` changes
  only the layout axis; every node, subgraph, and edge line in the fence stays
  untouched, so the diagram's semantics cannot drift. Rejected: restructuring
  the subgraphs or splitting the diagram — more churn for the same rendering
  fix, and the validator would have more surface to re-confirm.
- **The paragraph moves verbatim, as a block.** The document then reads:
  intro paragraph, core-loop paragraph, `## How it fits together` + diagram,
  then the "Today shipd builds itself" paragraph as closing prose. Rejected:
  a new heading over the moved paragraph — the user asked for a reorder, not
  new structure.
- **The pin is an ADDED requirement on `project-readme`**, the capability that
  already carries this doc's branding scenario (`readme-brand-marks`), so the
  doc's structural contract lives in one place. Rejected: a MODIFIED
  `readme-brand-marks` — that requirement is about brand marks, and mixing
  layout into it would blur both.
- Risk: `flowchart TD` renders the stage subgraphs taller than wide, so the
  page grows vertically; that is the accepted trade — vertical scroll is
  native to a docs page, horizontal scroll is the defect being fixed.
