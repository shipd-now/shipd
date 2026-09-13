# skills-venn-reframe
Status: verified

## Idea

Rename the three skill groups to Pipeline, Orchestration and Memory, and give
each Venn region a name that says what shipd does there.

### Motivation

The diagram currently splits the skills by how many changes they touch — "One
change" against "Many changes" — which describes the partition without saying
what the system does, so a reader learns the shape and not the product.

### Details

- Rename the `README.md` Skills section's three group headings to
  **Pipeline**, **Orchestration** and **Memory**, keeping every row where it
  is.
- Rename the fence's three sets to match, and give its seven regions names
  that describe the work: spec, build, ship; epics, driven; decisions that
  stick; unattended; asks first; evidence; compounds.
- Rewrite the list beneath the fence to those region names.

Affected capabilities: `project-readme` (modified `cheatsheet-doc` and
`readme-catalogs-the-plugin-s-skills`). Impact: `README.md`,
`docs/cheatsheet.md`; no new dependencies.

### Non-goals

- No change to which skill sits in which group or region. This change renames
  the groups; it does not re-sort the twenty-five skills.
- No change to the diagram's geometry, palette, or the website that renders
  it. The canvas measured 475 units before this change and after it.
- No `title` line and no `style` line in the fence.

## Implementation

- **The two surfaces are renamed in one change because a requirement binds
  them.** `cheatsheet-doc` ties the fence's three sets to the README's Skills
  groups, so renaming one without the other would break that tie the moment it
  merged.
- **The requirement stops naming the groups.** Both requirements currently
  enumerate "the core loop, bigger than one change, and knowledge" in their
  own prose, which is what made this rename a spec edit rather than a content
  edit. They now say "the three group headings the section declares", so the
  next rename is a content change alone.
- **Intersection names are one or two words.** The three pairwise regions and
  the centre are a fraction of a circle's area. Verified by rendering this
  fence through the site's own pipeline: at three words the middle regions
  overlapped each other; at one or two they do not, and the fitted canvas
  stays 475 units with zero horizontal overflow at a 360px viewport.
- **The list repeats the region names verbatim**, so a reader moving from a
  circle to the list finds the same word — the same rule the list already
  follows.
