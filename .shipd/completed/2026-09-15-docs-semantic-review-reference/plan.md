# docs-semantic-review-reference
Status: verified

## Idea

Add the reference companion to the semantic review guide, covering the `--json`
finding object, the `lint` configuration key, and the `prior` verb's evidence
classes.

### Motivation

`docs/semantic-review.md` explains what the review reads and how it rates
findings, and its requirement forbids it listing a flag or a JSON field. So the
machine payload, the one configuration key the review reads, and the four
classes `prior` reports have no documented home at all —
`docs/copilot-review-reference.md` sits at its 250-line cap and describes the
gate's managed files rather than the review.

### Details

- Add `docs/semantic-review-reference.md`: the `--json` object field by field,
  the ten `category` values, the `verdict` rule, the `suggestion` whitelist, the
  `lint` key's two members, and `prior`'s output fields and four dispositions.
- State that a thread posted before the identity marker reports `hash` as null,
  and that a null hash never matches.
- Link the new page from `docs/semantic-review.md`'s See also.

Affected capabilities: `project-readme` (one added requirement). Impact:
`docs/semantic-review-reference.md` and `docs/semantic-review.md`. No code
changes, and no plugin version bump.

### Non-goals

- No coverage of the workflow passes, the severity rubric, or the risk lenses.
  Those belong to the concept guide, which already carries them.
- No coverage of `semdiff diff`, `files`, or `context` output. Only the three
  subjects this change names.
- No edit to `docs/copilot-review-reference.md`, which is at its cap and scoped
  to the gate's managed files.
- No change to any script. Every fact is read from the running code, never
  changed to match the prose.

## Implementation

- **Reference, and the cap is a limit rather than a target.** The doc opens
  `<!-- doc-type: reference -->` and stays under 250 lines. Its job is lookup:
  fields, values, and rules, with no workflow narrative.
  `docs/copilot-review-reference.md` sits exactly at the cap, which is a
  caution — a reference that fills its cap is one edit from splitting.

- **Open by naming the concept guide, as the house does.**
  `docs/prd-reference.md` opens by pointing at `prd.md` and saying "this page
  lists the formats, the rules, and the command surfaces". This page opens the
  same way against `semantic-review.md`, so a reader who wants the why is sent
  one hop rather than served a second explanation.

- **Three sections, one per subject.** The `--json` object first, because the
  other two are read in its service; then the `lint` key; then `prior`. Each
  states its fields as a table or list, and each names the file the running
  behaviour lives in, so a reader can check the doc against the code.

- **Document the null hash, because a reader will meet it.** Running
  `review_gate.py prior 208` returns three entries, every one carrying
  `"hash": null` — those threads were posted before the identity marker shipped.
  A null hash matches nothing, so such a finding is always reported again. Left
  undocumented, that reads as a bug rather than as the marker's start date.

- **Document that a re-post creates a new thread.** That same command returns
  three entries for two findings: one finding holds two `thread_id`s because
  the gate was re-posted on a new head. A reader comparing entry count against
  finding count needs to know why they differ.

- **Every value is read from the running code, not from memory.** The ten
  `category` values and the `verdict` rule come from
  `plugins/s/skills/review/references/json-output.md`; the `suggestion`
  whitelist from its second section; the `lint` members from the `// lint`
  entry in `plugins/s/skills/build/references/shipd.config.example.json`; and
  the four dispositions from `prior`'s docstring in
  `plugins/s/skills/review/scripts/review_gate.py`, confirmed against its live
  output.

- **Risk: a reference doc drifts faster than a concept doc**, because it names
  values rather than ideas. The new requirement names the specific lists — the
  ten categories, the two `lint` members, the four dispositions — so a change to
  any of them fails a scenario rather than passing unnoticed.
