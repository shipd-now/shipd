# skills-venn-diagram
Status: verified

## Idea

Add a mermaid Venn diagram of how the shipd skills overlap to
`docs/cheatsheet.md`, so it renders on the documentation index page, and bring
the README's skill roster back in line with it.

### Motivation

`README.md` already sorts every skill into three groups — the core loop,
bigger than one change, and knowledge — but nothing draws how skills span
those groups, and three shipped skills are missing from the roster entirely.
The documentation index has no picture of how twenty-five commands relate.

### Details

- Add one `venn-beta` mermaid fence to `docs/cheatsheet.md`, above the `/s:`
  table, placing every `/s:` command as `s:NAME` in a region.
- Add `/s:prd`, `/s:explain`, and `/s:worktree-hooks` to `README.md`'s
  **Skills** section, which omits all three.

The website renders this file's body inline on `/docs` under "Command
overview" (`shipd-now-website/app/docs/page.tsx`, `lib/docs.ts`
`cheatsheetBody()`), so the fence reaches the index page, `/docs/cheatsheet`,
and GitHub from one source.

Affected capabilities: `project-readme` (modified). Impact: `docs/cheatsheet.md`,
`README.md`; no new dependencies.

### Non-goals

- No change to the shipd-now-website repository. Mermaid's venn renderer
  places each set label on top of its own region's text and ignores the site
  palette; repositioning and recolouring the inlined SVG is a separate change
  in that repository, which must merge before this one.
- No `title` line in the fence — mermaid hardcodes the venn title's fill to a
  dark grey it does not expose, so the markdown heading carries the title.
- No `style` lines in the fence — the corpus stays presentation-free.
- No second diagram anywhere in the corpus, and no change to either table's
  rows.

## Implementation

- **The diagram is `venn-beta`, not hand-drawn SVG.** Mermaid added the type
  in v11.13.0; `shipd-now-website` pins `mermaid@11.17.2` through
  `mermaid-isomorphic@3.1.0`, which renders it at sync time to a committed
  SVG. Verified: rendering this taxonomy through that exact pair returned a
  fulfilled result with an `aria-roledescription="venn"` SVG. Rejected: an
  inline SVG authored in the website, which would put documentation content
  in the presentation repository.
- **The fence goes above the `/s:` table, under its own `##` heading.** The
  heading supplies the title the fence cannot style.
- **Region membership follows `README.md`'s three groups.** A skill that
  operates across groups sits in the matching intersection: `s:build` and
  `s:autopilot` across the core loop and bigger than one change; `s:ask`
  across the core loop and knowledge; `s:research` and `s:video-ingest`
  across bigger than one change and knowledge; `s:teach` across all three.
  Every other skill sits in its README group alone.
- **One `text` node per region, names separated by two spaces.** Mermaid
  divides a region's width between its `text` nodes and lets each overflow
  its box, so two nodes in one region collide into an unreadable run; a
  single node wraps into a clean column. Verified by rendering both shapes.
- **The README stays a partition; only the diagram carries overlap.** The
  README catalogues each skill once under its primary group. The diagram is
  the only surface that shows a skill spanning groups, so the two never
  contradict each other.
- **The documentation standard permits this diagram.** It bars a diagram that
  restates an adjacent list or table. The tables carry no grouping at all, so
  the Venn adds structure rather than repeating one; the standard's
  one-diagram-per-doc cap is met, since `docs/cheatsheet.md` carries none today.
- Risk: `venn-beta` is a beta renderer whose markup may change on a mermaid
  upgrade. The corpus carries plain content with no styling, so an upgrade
  changes how the diagram looks, never whether this file is valid.
- Risk: merging this before the website's label pass publishes a diagram whose
  set labels overlap their region text within the hour the sync next runs.
  Guard: ship the website change first.

## Questions and answers

### Q1: Where should the diagram live?
- **Question:** Should the Venn live in the docs corpus as a `venn-beta`
  fence in `docs/cheatsheet.md`, which the website renders onto `/docs`,
  `/docs/cheatsheet` and GitHub; or be hand-authored as inline SVG in the
  website's `app/docs/page.tsx`? Recommendation: the corpus.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** The corpus. Documentation content, diagrams included, belongs in
  this repository; the website renders the corpus and never becomes a second
  source of content. Where corpus markdown cannot express a presentation
  concern, the website carries that as a presentation-only pass over the
  rendered SVG. The user accepted that this splits the work across two
  repositories.
- **Queued:** q-docs-diagram-placement

### Q2: What three sets should the diagram use?
- **Question:** Which three sets should the Venn use, with every skill placed
  as `s:NAME`? Options: (1) Specify / Deliver / Know; (2) Discover / Build /
  Verify; (3) a grouping the repository already documents. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 3 — the README's own groups: **The core loop**, **Bigger
  than one change**, and **Knowledge**. It is a maintained taxonomy that
  already places every skill, so the diagram matches how shipd describes
  itself rather than inventing an axis. The README states a strict partition,
  so the intersections are derived here, not asserted there. The README's
  roster is also stale: `s:prd`, `s:explain`, and `s:worktree-hooks` appear in
  the cheatsheet but in none of its three groups.
- **Cited:** README.md `## Skills`, docs/cheatsheet.md

### Q3: Where does the layout fix for mermaid's venn output live?
- **Question:** Mermaid's venn auto-layout overlaps each set label with its
  region's text and ships an off-brand palette. Should the website's
  `lib/rehype-inline-diagrams.ts` gain a venn post-render pass, matching the
  surgery it already does for flowchart labels? Recommendation: yes.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Yes, and in the website repository only — post-render surgery on
  the inlined SVG is the documented house pattern there, and constraining the
  corpus instead would edit content the hourly sync owns. That keeps this
  change free of styling and makes the layout fix a separate change.
- **Cited:** shipd-now-website verified/docs-shell, verified/docs-corpus,
  change/diagram-edge-labels, change/diagram-fit-boxes, change/docs-mermaid
