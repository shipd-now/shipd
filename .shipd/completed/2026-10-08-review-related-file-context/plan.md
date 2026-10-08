# review-related-file-context
Status: verified
Theme: reliability

## Idea

### Motivation

`/s:review`'s recall has sat near 40% across fifteen versions of prompt work,
and benchy-cf's union analysis now shows why: the ceiling is a **context**
limit, not a prompting one.

Across all 25 benchmark rounds scored — every version, both PR sets — 56 of the
80 golden findings have been matched at least once. **24 have never been matched
by any configuration.** Of those 24:

- **17 require "diff plus related files"** to detect. Only 6 are diff-only.
- **12 are rated "easy"**, so they are not subtle findings the reviewer lacks
  the skill to see. They need context it never fetches.
- 16 are `low` and 8 `medium`; none is `high`.

The skill states the opposing principle in its own opening, at
`plugins/s/skills/review/SKILL.md:24`: "Never read whole files into context when
the structural diff and targeted lookups will do — that is the entire point."
That principle is doing exactly what it says, and it is what caps recall.

The published literature agrees on the direction. A practitioner writeup of 20
recall experiments found that most prompt changes produced no effect beyond
run-to-run variation, while the fixes that worked were mechanical — a
verification policy that keeps uncertain findings, and anchoring repairs that
recovered 11 true positives the pipeline had failed to map. Our own history says
the same thing: the changes that moved the number were the `locations` array,
the concrete severity instances, and the manifest lens with its `semdiff` code
change, while abstract wording changes stayed inside noise.

### Details

`semdiff` gains a `related` subcommand that emits, per changed file, a **bounded
set of related files** — the files that import it and the files it imports — and
the review reads what the engine names. The reviewer's discretion is not
widened; the engine's output is.

### Non-goals

- **No unbounded file reading.** The context-economy principle survives against
  whole-file reads and model-chosen exploration. What changes is that an
  engine-selected, capped, named set becomes readable. A reviewer may not decide
  for itself to open a file the engine did not name.
- **No call graph.** `related` is grep-backed and best-effort, like `context`
  before it, and says so in its own output.
- **No multi-round aggregation in this change.** The user settled that it ships
  later as an opt-in setting for high-stakes reviews rather than a default,
  since three-round union buys about 12 golden findings but published precision
  cost runs false positives 170 to 328, and part of our own measured variance is
  matcher noise and anchoring rather than detection. Recorded here so the
  decision is not relitigated; built separately so benchy-cf can attribute each.
  It will be a setting of the `max` mode this change introduces.
- **No deterministic criterion dispatch, and no ephemeral coverage ledger, in
  this change.** Both are promising — the determinism paper reports 2.17× F1 at
  5 to 15× fewer tokens — and both are separate changes for the same attribution
  reason.
- Not the teach feature. It is the wrong tool twice over: the wiki resolves per
  invocation root, so a page written in this workspace is invisible to a review
  of an unrelated checkout, and distilling measured benchmark misses into
  permanent detection guidance would be training on the test set.

## Implementation

### The `related` subcommand

`semdiff related <base> [<head>]` emits JSON keyed by changed file, each entry
carrying `importers` and `importees`, plus the same best-effort note
`context` already carries. It reuses `cmd_context`'s tool ladder — ripgrep when
present, `git grep` otherwise — so it adds no dependency and stays inside the
constitution's stdlib-only rule.

Two directions, both grep-backed:

- **Importers** — the files that reference the changed file. Search for the
  file's module name (its basename without extension, and its
  extensionless repo path for languages that import by path), which is what an
  import statement names.
- **Importees** — the files the changed file references. Scan the changed
  file's own import, require, use, and include lines, and resolve each against
  paths that exist in the repository.

### The bound is the whole design

An unbounded related set would reintroduce the context cost the principle
exists to prevent, so the cap is part of the contract rather than a tuning
knob:

- at most **8 related files per changed file**, and at most **40** across the
  whole review;
- ranked **same directory first**, then nearest common ancestor, so the files
  most likely to matter survive the cap;
- every truncation reported in the output as a count, never silently, so a
  reviewer knows context was withheld and can say so in what it could not
  verify.

Those numbers are deliberate and will be wrong in some repository. They are
stated in the spec so a later change can move them against evidence rather than
by feel.

### Two named modes, because the cap is the thing worth varying

`related` takes `--mode balanced|max`, defaulting to **`balanced`**. The caps
above are the balanced defaults. **`max`** raises them — 20 per changed file and
120 per review — for a review where recall matters more than cost.

The vocabulary lands here rather than with the aggregation change because this
is where the first real knob appears, and naming it twice would mean renaming it
once. Aggregation becomes a second thing `max` turns on, so a caller asks for
maximum recall once rather than learning a flag per technique.

Mode is a `related` argument, not review-wide state: the subcommand reports the
mode it ran in, so a review's own output records which one produced its context.

### The principle, amended rather than deleted

`SKILL.md:24` currently reads "Never read whole files into context when the
structural diff and targeted lookups will do — that is the entire point." It
becomes a narrower rule: the structural diff and targeted lookups come first,
and the files `related` names are read when a check needs cross-file context —
with whole-file reads of anything the engine did not name still ruled out.

This is a real relaxation of a stated design principle, so it is recorded in the
spec and in the oracle queue rather than changed quietly. The oracle returned
`INSUFFICIENT` on it and filed `q-review-related-file-context`; the user settled
it, and that answer is now captured in the workspace store.

### Where the review runs it

A new step runs `related` after the structural diff and before the judgement
passes, so the cross-file context is in hand when the checks that need it fire.
The step names which checks it serves — the downstream-impact and call-site
checks, the sibling-consistency and stdlib-semantics lenses — because a reviewer
told only "read these files" will read them and draw nothing from them.

### Budget

`SKILL.md` is at 340 of 350 once v0.6.263 merges, so the new step's roughly
eight lines leave almost nothing. If it does not fit, raise the ceiling in its
one owner requirement, `review-skill-references`, exactly as v0.6.262 did for
this file and for the harness bodies. Do not compress to fit: two content
regressions have already shipped that way, and a third would be the same
mistake with the same cause.

### Sequencing

This change edits `SKILL.md` in the same region as v0.6.263
(`review-runtime-location`), which is verified and merging. Bring the branch
current with `origin/main` before implementing, and expect to reconcile.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps to 0.6.264, after v0.6.263.

## Readiness attestation

### Problem and motivation

17 of the 24 golden findings that no version has ever matched require context
beyond the diff, and the skill's stated principle forbids fetching it.

Evidence: benchy-cf's union analysis over 25 scored rounds — 56 of 80 golden
findings matched at least once, 24 never, of which 17 need "diff plus related
files", 6 are diff-only, 12 are rated easy, 16 `low` and 8 `medium`. Per-round
means against unions: v0.6.260 on five PRs scored 32.0 mean against a 44 union,
with 36 of 80 missed in all three rounds. The principle is quoted at
`plugins/s/skills/review/SKILL.md:24`.

### Scope and non-goals

In scope: the `related` subcommand with its caps and reporting, the amended
principle, the new workflow step, both reference-free surfaces, the spec
requirements, tests, the version bump.

Out of scope: aggregation (settled as a later opt-in change), deterministic
dispatch, the ephemeral coverage ledger, any teach or wiki integration, and any
unbounded or model-chosen file reading.

### Affected capabilities and files

One capability, three requirements, one of them new.

Evidence, hashes computed with `spec_status.py base-hash` in this worktree:
`semantic-review` requirements `review-skill` (base `993a5177bca6`),
`review-skill-references` (base `4e3f894627a6`) and `reference-context` (base
`55d3088a874c`), the last being the existing targeted-lookup requirement the new
`related-context` requirement sits beside. Files:
`plugins/s/skills/review/scripts/semdiff.py`,
`plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_semdiff_files_context.py`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `semdiff files` emits cohorts mapping to file
lists and assigns no criteria; `cmd_context` at
`plugins/s/skills/review/scripts/semdiff.py:1124` implements the rg-then-git-grep
ladder this subcommand reuses, and dies with code 127 when neither is present;
the `reference-context` requirement already states the best-effort,
never-a-call-graph contract that `related` inherits; `SKILL.md` is 338 lines in
this worktree and 340 on the v0.6.263 branch, against a 350 ceiling owned by
`review-skill-references`.

### No open task-shaping decision

- Whether to relax the context principle: yes, bounded and engine-selected —
  settled by the user after the oracle returned `INSUFFICIENT`, and captured in
  the workspace store as `q-review-related-file-context`.
- Whether the reviewer may widen the set itself: no, only the engine's named set
  is readable — settled above.
- How the set is bounded: 8 per changed file, 40 per review, same-directory
  first, truncation reported — settled above, with the numbers in the spec so
  evidence can move them.
- What the modes are called: `balanced` is the default and `max` the
  recall-first setting, named by the user — settled above, with `max` raising
  the caps here and gaining aggregation in the later change.
- Whether this change also builds aggregation, dispatch, or the ledger: no, each
  ships separately for attribution — settled in the non-goals.
- What happens if the line ceiling binds: raise it in its single owner, never
  compress — settled above.

## Questions and answers

### Q1: Whether review may read related unchanged files beyond the diff

- **Question:** Should `/s:review` read related (unchanged) files beyond the
  structural diff in order to find defects that require cross-file context?
  Options: (A) keep the stated context-economy principle, with bounded lookups
  only through `semdiff context`, accepting the recall ceiling; (B) relax it
  deliberately, with `semdiff` emitting a bounded set of related files
  (importers and importees) per changed file that the review is expected to
  read; (C) keep the principle and treat the 24 unreachable golden findings as
  out of scope. Recommendation: B, bounded and emitted by the engine rather
  than left to the model's discretion.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** B. `/s:review` may read related unchanged files, but only a
  bounded set the engine selects, never at the reviewer's discretion — `semdiff`
  emits the importers and importees per changed file and the review reads what
  it names. The principle still holds against unbounded whole-file reads and
  model-chosen exploration; it is the engine-bounded set that is now permitted.
  The oracle checked the personal store, the workspace wiki and queue, the base
  store and the repository's own spec surfaces, and found no recorded position
  either way, so this was a genuine gap rather than something already settled.
- **Queued:** q-review-related-file-context
