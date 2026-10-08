# review-related-fair-share
Status: verified
Theme: reliability

## Idea

### Motivation

v0.6.265's `semdiff related` allocates its per-review budget **first-come**, and
benchy-cf measured the consequence by running the subcommand directly on the
benchmark PRs, at no token cost.

On apilix — 22 changed files, 40-file budget, 72 candidates truncated — the
components and two hub modules consume the entire budget, and then
`snapshotEngine`, `storageDriver`, `syncEngine`, all four sync adapters and
`server/index.js` receive **zero related files**, each with a non-zero
truncation count proving candidates existed and were discarded.

Those starved files are where the cross-file defects live. Of the 17
never-matched golden findings that require diff plus related files, **9 are in
apilix**, on exactly that sync layer. So the feature spends its budget on hub
importers and UI components and gives nothing to the files it was built to
serve.

A cap meant to prevent context blowup became a lottery. The per-file truncation
counts were the only visible symptom, and reading them required going through
22 entries — the output was honest about withholding context and gave no clue
the withholding was concentrated where it mattered.

### Details

Three changes, all inside `cmd_related`:

1. **Fair-share allocation.** Round-robin passes rather than a running
   budget: every changed file receives its top-ranked candidate before any file
   receives a second.
2. **Scarce-first ordering within each pass**, which subsumes hub
   down-ranking without a threshold constant.
3. **A starvation count in the summary**, distinguishing a file with no
   candidates from a file denied by the budget.

### Non-goals

- **The caps do not change.** 8 per changed file and 40 per review in
  `balanced`, 20 and 120 in `max`. A larger budget would not fix first-come
  allocation; it would concentrate a larger budget. Fairness is the fix.
- **No bridge-edge detection.** benchy-cf identified that
  `window.electronAPI.X` against `contextBridge.exposeInMainWorld` and
  `ipcMain.handle('x')` is a string-keyed edge an import resolver cannot see,
  and that the s3Adapter golden finding sits on it. That is a different
  detector and belongs in its own change. Bolting string-key matching onto an
  import resolver would reintroduce the prose-mention problem in a new form —
  the defect v0.6.265 already had to fix once.
- No change to importer or importee **detection**, only to which of the
  detected candidates survive the budget.
- No prompt-surface change. Both reference-free surfaces already describe the
  subcommand and its caps correctly; nothing they say becomes false.

## Implementation

### Fair-share allocation

The current loop walks the changed files once, taking up to `per_file_cap`
candidates each and decrementing a shared `remaining` counter, so a file
reached late finds the budget spent.

Replace it with two phases. First collect every changed file's ranked candidate
list, with no budget applied. Then allocate in passes: on pass `i`, each file
that has an `i`-th candidate takes it, while budget remains. The loop ends when
the budget is exhausted or no file has an unallocated candidate.

On apilix that gives all 15 candidate-bearing files one each, then second and
third picks, rather than five files taking everything.

### Scarce-first ordering, instead of a hub threshold

Within each pass, visit files in ascending order of total candidate count. A
file with two candidates is served before a hub with twenty-seven.

This is deliberately not the threshold benchy-cf proposed ("down-rank anything
imported by more than N files"). It reaches the same goal without inventing a
constant that would be wrong in some repository, and it has the property that
actually matters: a tightly coupled file gets both of its candidates before a
hub gets a third. If real data shows a threshold behaves better, the output
will show it and the threshold is still available.

Within a single file, importees rank above importers. What a changed file calls
is more directly relevant to judging the change than an arbitrary sample of its
callers — and an arbitrary sample is exactly what a hub's importer list is,
which is why `types.ts` returning 7 of 34 importers was weak context.

### The review cap counts distinct files, not edges

A related file shared by several changed files costs the review cap **once**,
and is still listed under every changed file that relates to it.

The reasoning generalises beyond the apilix case that prompted it. The per-review
cap exists to bound what the reviewer has to read, and a reviewer reads a shared
module once however many changed files point at it. Counting per edge would make
the cap measure edges while claiming to measure reading cost — the same class of
error as the original defect, where the cap measured arrival order while
claiming to measure budget.

Concretely: `store.tsx` and `types.ts` are importees of most of apilix's changed
components. Under per-edge counting a handful of shared modules absorb much of
the 40 while adding one file's worth of actual reading. Under distinct counting
they cost two slots total.

This has a useful consequence. Once the budget is spent, an already-selected
file may still be listed under a further changed file, because listing it adds
no reading. So a cohesive cluster of files sharing dependencies is cheap, and
the budget is spent on genuinely new context.

The output reports both numbers so the distinction is visible: `related_files`
is the distinct count charged against the cap, and `related_edges` is the total
number of file-to-related pairs listed.

### The starvation count

`summary` gains two counts in place of a single ambiguous one:

- `files_without_candidates` — the search found nothing to relate. Correct
  behaviour; on apilix this is 7, being two markdown files, a stylesheet, two
  manifests, and the two electron entry points.
- `files_starved` — candidates existed and the budget denied them all. **This
  is 0 on a correct run**, and any non-zero value means allocation has
  regressed.

Separating them is load-bearing rather than cosmetic. A single
"files with zero related" count reads 7 on a healthy apilix run, so it would
look like a failure and be ignored, which is worse than not reporting it.
benchy-cf caught that before it was written into a test.

### Budget

No pressure anywhere. `semdiff.py` has no line ceiling. No prompt surface
changes, so `SKILL.md` stays at 357 of 370 and the rendered harness body stays
at 159 of 160 — the latter being why this change touches neither.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.265 → 0.6.266.

## Readiness attestation

### Problem and motivation

First-come budget allocation starves the changed files that hold the
cross-file findings this feature exists to reach.

Evidence: benchy-cf ran `semdiff related` from the marketplace 0.6.265 build, in
balanced mode, against three benchmark PRs. On apilix the summary read
`related_files 40` with `truncated 72`; `store.tsx` took 7 with 15 truncated and
`types.ts` took 2 with 27 truncated, while `snapshotEngine`, `storageDriver`,
`syncEngine`, the four sync adapters and `server/index.js` each received 0 with
truncation counts of 1 to 6. Nine of the 17 never-matched cross-file golden
findings sit in apilix on that sync layer.

### Scope and non-goals

In scope: the allocation loop in `cmd_related`, the within-pass ordering, the
within-file ordering, distinct-file charging against the review cap, the
summary's four counts, tests for each, the version bump, and the
`related-context` requirement.

Out of scope: the cap values, importer and importee detection, bridge-edge
detection, and both prompt surfaces.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review` requirement `related-context`, base `b0346df77d43`,
computed with `spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/tests/test_semdiff_files_context.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `cmd_related` holds a single
`remaining = per_review_cap` counter decremented inside the per-file loop,
which is the first-come allocation; `RELATED_CAPS` declares
`balanced {per_file 8, per_review 40}` and `max {per_file 20, per_review 120}`;
the per-file entry already reports `truncated`, and the summary already reports
`changed_files`, `related_files` and `truncated` but no starvation count;
candidates are ranked by `_proximity_key` alone, with no distinction between
importer and importee and no notion of candidate-count order across files.

### No open task-shaping decision

- Whether to raise the budget or fix allocation: fix allocation, because a
  larger budget concentrates the same way — settled above.
- Hub down-ranking by threshold or by scarce-first ordering: scarce-first, so
  no constant is invented, with the threshold still available if data favours
  it — settled above, and the divergence from benchy-cf's suggestion was put to
  them with the reasoning.
- Whether one zero count suffices: no, two counts, because a single one reads 7
  on a healthy run and would be dismissed — settled above.
- Whether bridge edges are in scope: no, separate detector — settled in the
  non-goals.
- Whether a shared related file costs the review cap once or once per edge:
  once, because the cap bounds what the reviewer reads and a shared file is
  read once — settled above, and raised by benchy-cf before implementation.
