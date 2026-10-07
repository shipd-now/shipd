# review-low-severity-sweep
Status: verified
Theme: reliability

## Idea

### Motivation

Item 1 of the benchy-cf ReviewBench handoff (multi-site findings + fix-site
anchoring) shipped as v0.6.249 and measured grounded recall rising from 33.2%
to 44.6% macro on the same 5 benchmark PRs. Against the remaining misses,
benchy-cf reports that most of what `/s:review` still misses on v0.6.249 are
real low-severity defects: a swallowed delete error, workspace history/
snapshot files left behind on delete, synchronous `fs` calls in an Electron
IPC handler, a React row key built from the list index, a `has_more` field
declared but never read, duplicated tracing blocks in `connect()`. The
reviewer *can* find these — it caught a few by chance on the v0.6.249 run
(CrabTrap's `has_more`-never-read field, `Count`/`Query` not sharing one
transaction) — but nothing in the skill asks it to look, because the current
severity rubric defines low as "style, naming, minor redundancy, defensive
nits" and states low findings never block. Together those two facts tell the
model lows don't matter.

### Details

Redefine "low" severity as a real but minor defect, not style, and add a
breadth-sweep step that revisits each changed file once more, end to end,
for a remaining defect of that kind — a pass the targeted structural and
signature-chasing steps don't exist to catch, since a minor defect can sit
beside a hunk without being part of it structurally. Mirror both changes
into `plugins/s/harness/bodies/review.md`, since the semantic-review
capability's `review-skill` requirement binds the skill and the harness body
to the same judgement passes, and correct that requirement's "three
judgement passes" count to four.

Affected capability: `semantic-review` (requirement `review-skill`,
modified). Impact: `plugins/s/skills/review/SKILL.md` (severity rubric, a new
workflow step, a line-budget extraction to a new reference file),
`plugins/s/skills/review/references/new-code-checks.md` (new),
`plugins/s/harness/bodies/review.md` (mirrored rubric + step, fully inline —
it ships into other repos with no `${CLAUDE_PLUGIN_ROOT}`),
`.shipd/verified/semantic-review/spec.md`, and the plugin version bump. No
new dependency, no test changes required beyond what the suite already
covers generically (confirmed below).

### Non-goals

- No PR-comment volume cap or fold-minor-findings-together mechanism for the
  posted gate comment. The original handoff flagged this as worth
  "considering" and benchy-cf repeated it "may be worth it," but it is
  explicitly a maybe pending real PR volume data ReviewBench cannot produce
  (it only ever reads the `--json` output, never a posted PR), and bundling a
  UX/volume policy change into a recall-focused change would break the
  change-one-variable-at-a-time discipline this collaboration has followed
  since item 1. Every finding, low included, keeps rendering in `--json`,
  the summary table, and (if anchored) its own inline comment, unchanged.
- `plugins/s/integrations/copilot/SKILL.md` carries its own copy of the same
  "style, naming, minor redundancy, defensive nits" rubric line (a third
  surface, for GitHub Copilot's own built-in review — a different reviewer
  context ReviewBench never exercises) and is deliberately left untouched
  here. It now disagrees with the redefined rubric on the other two
  surfaces. Left as a known, tracked inconsistency rather than silently
  patched in a change whose evidence base is entirely about `/s:review`;
  reconciling it is a separate change if Copilot's own flow is ever
  benchmarked.
- Items 3 (PR description vs. implementation), 4 (new risk lenses), and 5
  (missing-test precision — on hold; benchy-cf found its original
  justification was judge noise, not a real finding) are separate, later
  changes. This change does not touch step 7 (test coverage per finding),
  `references/risk-lenses.md`, or anything about PR descriptions.
- No change to the high/medium rubric, the exposure floor, or the
  blocks/never-blocks verdict rule — low still never blocks.

## Implementation

### The rubric redefinition

Replace the `low` bullet in both `SKILL.md`'s and `harness/bodies/review.md`'s
severity rubric. "Low" becomes a real but minor defect, naming the concrete
categories the benchmark's actual misses fall into: a swallowed or
silently-dropped error; a resource or file leak on a rare or cleanup path;
dead or duplicated code; a field or variable declared but never read; an
unstable or incorrect identity (e.g. a list/row key derived from array index
instead of a stable id); a blocking or synchronous call where the
surrounding context is async or event-driven. State explicitly, in the same
place, that pure style, naming preference, and formatting are never findings
at any severity — that is the other half of the redefinition, not an
afterthought.

### The breadth-sweep step

New step, titled "Breadth sweep for minor defects," positioned after the
existing risk-lenses step (SKILL.md's `5b`, harness body's step 7) and
before the report step — so the reviewer has already judged new code and
applied the fixed risk triggers before doing one more end-to-end pass over
every changed file for a remaining defect of the categories above. In
SKILL.md this is step `5c`. In `harness/bodies/review.md`, which has no
sub-lettered steps, insert it as a new sequential numbered step and
renumber every step after it by one — no external surface pins those harness
step numbers (confirmed: no test references `bodies/review.md` by step
number, only by phrase).

### The SKILL.md line-budget extraction

`plugins/s/skills/review/SKILL.md` is 329 lines against
`test_under_line_ceiling`'s hard `< 330` assertion — there is no headroom for
a new rubric sentence plus a new step. Free it by extracting step 5's five
sub-bullets ("Wrong quantity measured," "Escape hatch lapsing the
guarantee," "Termination on hostile input," "Boundary agreement," "Doc
comment versus code" — currently ~14 lines of bullets and explanatory prose)
into a new reference file, `plugins/s/skills/review/references/new-code-checks.md`,
following the exact pattern `risk-lenses.md`/`linters.md`/`posting.md`
already establish: a short paragraph stays inline under step 5 ("judge it
against its own stated purpose — do not wave it through because it is new
rather than modified") plus a pointer to the new reference for the five
checks and worked examples, and the reference is added as a new row to
SKILL.md's `## References` table (condition: "a function, class, guard, or
helper is new in the diff"). No test pins step 5's bullet text verbatim
(confirmed), so this extraction is safe. `harness/bodies/review.md`'s mirror
of this step is already a single compact paragraph with no bullets — it
needs no matching extraction, since it never had the detail to begin with
and can never gain a references table (it ships into other repos with no
`${CLAUDE_PLUGIN_ROOT}`).

The exact line counts the extraction frees, and the exact final wording of
the new rubric bullet and the new step, are a task-level concern: the
implementer edits, then runs
`python3 -m unittest discover -s plugins/s/skills/review/tests -v`
(which includes `test_under_line_ceiling`) and iterates on wording/trimming
until it is green, rather than this plan asserting a line count that could
be stale by the time it is checked.

### Spec

`.shipd/verified/semantic-review/spec.md`'s `review-skill` requirement is
MODIFIED: the rubric's `low` description, the new breadth-sweep pass, and
the judgement-pass count correction (three → four) are stated, with new
scenarios for the redefinition and the sweep. The existing "Scenario: The
harness body carries the same passes" scenario is widened to also assert the
harness body instructs the sweep.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.249 → 0.6.250 per
`AGENTS.md`.

## Readiness attestation

### Problem and motivation

Most of what `/s:review` still misses on v0.6.249, per benchy-cf's
benchmark, are real low-severity defects the current rubric actively
discourages looking for (`low` = "style... defensive nits," low never
blocks).

Evidence: benchy-cf's handoff message (this session, this conversation),
citing CrabTrap's `has_more`-never-read field and the `Count`/`Query`
transaction split as defects the v0.6.249 run caught only by chance, plus the
original 5-item handoff's six named examples (swallowed delete error,
leftover history/snapshot files, synchronous `fs` in an IPC handler, an
index-derived React key, the unread `has_more` field, duplicated tracing
blocks).

### Scope and non-goals

In scope: the rubric redefinition and the breadth-sweep step on SKILL.md and
harness/bodies/review.md, the spec delta, and the version bump. Out of
scope: any PR-comment volume policy, the copilot integration's own rubric
copy, and items 3/4/5.

Evidence: `plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`.shipd/verified/semantic-review/spec.md` (`review-skill`),
`plugins/s/.claude-plugin/plugin.json`. Confirmed out of scope:
`grep -rln "style, naming, minor redundancy" plugins/s/` also matches
`plugins/s/integrations/copilot/SKILL.md`, left untouched per the non-goal
above.

### Affected capabilities and files

One capability, one requirement.

Evidence: capability `semantic-review`, requirement `review-skill` (base
hash `ed722decb821`, from `spec_status.py base-hash semantic-review
review-skill`, run against this worktree's current `main`). Runnable
premise: `wc -l plugins/s/skills/review/SKILL.md` reports 329, and
`python3 -m unittest plugins.s.skills.review.tests.test_skill_references.SkillMdStructureTest.test_under_line_ceiling`
(run via the discover command above) is the exact gate the extraction must
clear. Runnable premise: `grep -rn "style, naming, minor redundancy|defensive nits" plugins/s/`
confirms the wording appears in exactly three files
(`skills/review/SKILL.md`, `harness/bodies/review.md`,
`integrations/copilot/SKILL.md`); no test in
`plugins/s/skills/review/tests/*.py` or
`plugins/s/skills/build/tests/test_copilot_verb.py` hard-codes that phrase
or any other exact rubric wording (both suites check only generic
substrings — `"Severity rubric."`, `"**low**"`, bare `"low"`), so no test
needs editing to accommodate the new wording.

### No open task-shaping decision

- Whether to add a comment-volume cap/fold mechanism: no — explicitly
  deferred, no volume data exists yet and it would conflate two variables.
- Whether to update the copilot integration's own rubric copy: no — left as
  a tracked inconsistency, out of this benchmark-evidenced change's scope.
- Where the breadth-sweep step sits in the sequence: after the risk-lenses
  step (5b / harness step 7), before the report step — settled above.
- How to free SKILL.md's line budget: extract step 5's bullets to a new
  reference file, settled above and confirmed safe against the test suite.
- Exact final wording/line trim: a task-level, test-gated iteration, not a
  plan-time decision — settled above.
