# copilot-marker-deferral
Status: active
Theme: reliability

## Idea

### Motivation

`copilot-review-skill`'s `skill-template` requirement demands the copilot
template state that the verdict marker "is read from the last non-empty line by
exact equality". That is not how the gate reads it, and the same file records
why: `gate-workflow-template` says the workflow reads the verdict "by scanning
the review text backwards for the last line equal to a verdict marker", because
"the Copilot CLI streamed its session narration after the report" and the
last-non-empty-line rule then fell open. The template itself already says the
right thing — "the last line equal to a marker, found by scanning the body
backwards".

So one requirement describes an abandoned reader, two requirements below the one
that documents its abandonment. It is the same defect as the rubric copy
PR 287 just removed, in the same requirement: a second copy of wording another
requirement owns, left behind when the owner changed.

The semantic review on PR 287 found it, and also found the reason it survived:
nothing guards either copy. That review likewise found a clause of the rubric
left in a scenario PR 287 itself wrote, which is the same failure at the
smallest possible scale.

### Details

`skill-template` stops restating the reader's semantics and defers to
`gate-workflow-template`, which owns them. Two guards land so the next copy
fails CI instead of surviving two versions.

### Non-goals

- **The template does not change.** It already matches the gate. Both edits
  move requirements to the implementation, because the implementation is right.
- **The gate workflow does not change**, and neither does
  `gate-workflow-template`, which already owns the reader.
- No change to the review path's prose. v0.6.276 is under measurement and this
  must not perturb it.
- Not the distance change to the further-location rule. That is the next
  version and is registered separately.

## Implementation

### The deferral

Two edits to `copilot-review-skill` / `skill-template`:

- its prose drops "stating that the marker is read from the last non-empty line
  by exact equality" and instead requires the template state *how the gate
  reads it*, naming `gate-workflow-template` as the owner of those semantics
  and forbidding a restatement here;
- its scenario "The marker instruction states last-line equality" is dropped,
  with a `Dropped:` line, and replaced by one that compares the template's
  instruction against what `gate-workflow-template` states, asserting they
  agree and that this requirement restates neither.

A third edit removes the residual clause "with pure style excluded from
findings at any severity" from the rubric scenario PR 287 added — a fragment of
the `low` definition that requirement had just declared it would not restate,
and already covered by the same THEN's "the same `low` definition".

### The two guards, which are the point

Without a test, this drift class is caught only when a reviewer happens to read
two requirements side by side. Both guards go in
`plugins/s/skills/review/tests/test_skill_references.py`:

- **rubric parity** — the copilot template's `low` definition, floor and three
  instances match `plugins/s/skills/review/SKILL.md`, compared on
  whitespace-normalised text. This is the guard whose absence let the rubric
  copy go stale for two versions.
- **no restatement** — `skill-template`'s own text carries neither the rubric
  wording nor the reader semantics, matched against the phrases each owner
  states. This is the guard whose absence let the marker clause survive.

Each must be proven non-vacuous against the text it forbids, with the file
otherwise intact and its byte count checked, because a probe that truncates a
file produces a failure that proves nothing.

### Version

Adding tests touches `plugins/s/`, so
`plugins/s/.claude-plugin/plugin.json` bumps 0.6.276 → 0.6.277. The bump is
safe now: the v0.6.276 measurement finished, and no round is running.

## Readiness attestation

### Problem and motivation

A requirement describes a reader the workflow abandoned, and nothing guards
either of the two wording copies this capability has carried.

Evidence, read in this worktree: `skill-template` says "last non-empty line by
exact equality" at two places; `gate-workflow-template` says the gate scans
"backwards for the last line equal to a verdict marker" and records the
streamed-narration failure that caused the change;
`plugins/s/integrations/copilot/SKILL.md` says "the last line equal to a
marker, found by scanning the body backwards". No test in
`test_skill_references.py` compares the template's rubric to `SKILL.md` or
checks `skill-template` for restatement.

### Scope and non-goals

In scope: one MODIFIED requirement with one dropped scenario, two new tests,
the version bump.

Out of scope: the copilot template, the gate workflow,
`gate-workflow-template`, every review-path prose surface, and the distance
change.

### Affected capabilities and files

One capability, one requirement: `copilot-review-skill` / `skill-template`,
base `0e7438ba4ce5` from `spec_status.py base-hash` here.

Files: `.shipd/verified/copilot-review-skill/spec.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

- Which side changes: the requirement, because the template and the gate
  already agree with each other — settled above.
- Transcribe or defer: defer, since a second copy is the defect both times,
  and `gate-workflow-template` already owns the reader — settled above.
- Whether the guards ship here: yes. The measurement is finished, so the
  version bump they force is no longer a hazard, and their absence is the
  documented reason this clause survived — settled above.
