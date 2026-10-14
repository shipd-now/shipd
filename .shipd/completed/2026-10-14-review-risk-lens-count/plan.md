# review-risk-lens-count
Status: verified
Theme: reliability

## Idea

### Motivation

`plugins/s/skills/review/references/risk-lenses.md` opens "Five triggers, four
lenses". Both figures are wrong and they are transposed: `review-risk-lenses`
fixes **five lenses expressed as six triggers**, and the file itself documents
**six** sections. `SKILL.md` step 5b names six. So the one surface that
contradicts the other three is the reference a reviewer opens when a trigger
fires.

It has been wrong in every version this benchmark series measured — v0.6.260
through v0.6.286 — so it cannot have skewed a comparison between any two of
them. What it may have cost is absolute recall, in one specific place: a
reviewer told to expect four lenses and five triggers, then reading six
sections, has every reason to treat the last one as surplus. The last one is
**packaging and dependency manifests**, the sixth trigger, added later than the
rest.

That is not proven and this change does not claim it. What is certain is that
the file misstates its own contents on the prompt path.

### Details

The header states six triggers and five lenses, and a test pins the counts
against the sections.

### Non-goals

- **No claim that this recovers recall.** The packaging-trigger hypothesis is
  stated as a hypothesis. Whether it moves anything is for a round set, and
  this change ships so that set has something to measure.
- **No change to the requirement's own counts.** `review-risk-lenses` already
  says five lenses and six triggers, and has throughout. The file was wrong,
  not the spec.
- **No change to the lens content**, to `SKILL.md`, to the harness body, or to
  any other reference. One sentence in one file, plus its guard.

## Implementation

The header becomes "Six triggers, five lenses", matching the requirement and
the file's own six sections. One line, one word changed in each count.

`RiskLensCountsAgreeTest` pins three things, because the drift needed all
three to go unchecked: that the header states the right counts and not the
transposed pair, that the file carries exactly six `##` sections, and that
every trigger phrase `SKILL.md` names has a section of its own. The third is
the one that catches a seventh trigger being added to the skill and not here.

The requirement gains the acceptance criterion whose absence let this survive:
the reference file SHALL state the same counts and carry one section per
trigger. Nothing compared the header to the sections before, which is the whole
reason a wrong number sat on the prompt path for twenty-six versions.

### This moves a measured prompt surface

`risk-lenses.md` is read on every review where a trigger fires, so this is not
a measurement-neutral change. It ships deliberately as its own version with
nothing else in it, so a round set can attribute whatever it finds to this one
sentence. The measuring session's own instruction was to land it after their
run rather than before, because moving two prompt surfaces in one round set
would make the result unattributable.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps to the next free number above
whatever `main` carries when this ships. Read it rather than assuming: main
moved four times during this series' final changes, and a version at or below
main's moves the plugin version backwards.

## Readiness attestation

### Problem and motivation

A file on the `/s:review` prompt path misstates its own contents, and nothing
checks it.

Evidence, measured in this worktree: the header reads "Five triggers, four
lenses"; `grep -cE '^## '` over the file returns **6**; `SKILL.md` step 5b
carries **6** trigger bullets; `review-risk-lenses` states "five risk lenses
… expressed as six triggers". No test in
`plugins/s/skills/review/tests/` referenced the file's header before this
change.

### Scope and non-goals

In scope: one header sentence, one new test class, one MODIFIED requirement
with one added scenario, the version bump.

Out of scope: the lens content, every other prompt surface, the requirement's
own counts, and any claim about recall.

### Affected capabilities and files

One capability, one requirement: `semantic-review`/`review-risk-lenses`, base
`0db75923ac49` from `spec_status.py base-hash` here.

Files: `plugins/s/skills/review/references/risk-lenses.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: the file has six `##` sections; `SKILL.md`
step 5b has six trigger bullets; the guard fails against `main`'s header with
the file otherwise intact — 6919 bytes against the fixed 6918, a one-byte
delta consistent with "Five"→"Six" and "four"→"five" — and passes once
restored.

### No open task-shaping decision

- Which side is wrong: the file, because the requirement, `SKILL.md` and the
  file's own section count all say six triggers — settled above with all four
  figures measured.
- Whether to claim a recall effect: no, it is a hypothesis and is labelled one;
  the change ships so a round set can test it — settled above.
- Whether this is measurement-neutral: no, and it ships alone for that reason
  — settled above.
- What the version becomes: read from `main` at ship time — settled above.
