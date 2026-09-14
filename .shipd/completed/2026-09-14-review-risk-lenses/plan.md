# review-risk-lenses
Status: verified
Epic: review-rubric

## Idea

Add four risk lenses — security, performance, stability, and data integrity —
to the review rubric, with every trigger always visible and the depth loaded on
demand.

### Motivation

The `/s:review` rubric judges correctness and maintainability and names no
security, performance, stability, or data-integrity concern, so a leaked
credential or an irreversible migration passes a green review. The
`review-skill` requirement at `.shipd/verified/semantic-review/spec.md:158`
lists every judgement pass the skill carries, and none of them guards those
four risks.

### Details

- Add an always-inline `### 5b. Risk lenses` step to the plugin skill: one line
  per lens naming what it looks for, and a pointer to the reference for depth.
- Add `plugins/s/skills/review/references/risk-lenses.md` carrying the full
  guidance and worked examples, read when a lens fires.
- Floor an exposure finding at `high`: a leaked credential and an unguarded
  authorization boundary are always high, whatever the reviewer's confidence.
- Extend the `--json` finding taxonomy with `security`, `performance`,
  `stability`, and `data-integrity`.
- Carry the lenses inline into `plugins/s/harness/bodies/review.md` and
  `plugins/s/integrations/copilot/SKILL.md`, neither of which can read a
  reference file.
- Extend the agreement test so the new reference is pinned like the other three.

Affected capabilities: `semantic-review` (one added requirement). Impact:
`plugins/s/skills/review/SKILL.md`, a new
`plugins/s/skills/review/references/risk-lenses.md`,
`plugins/s/skills/review/references/json-output.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/integrations/copilot/SKILL.md`,
`plugins/s/skills/build/tests/test_copilot_verb.py` (four tests locate a
section by the heading number task 3.4 renumbers), and
`plugins/s/.claude-plugin/plugin.json`. No new dependencies, and no engine
script changes.

### Non-goals

- No cohort-gating of the lens triggers. `COHORT_RULES` in `semdiff.py:575`
  classifies by path shape and defines no security cohort, so a gated trigger
  would miss a secret in `frontend/` or a root config.
- No closing of the copilot template's pre-existing judgement-pass gap. It
  carries none of the four existing passes; adding the ones this member
  introduces is in scope, adding the ones it does not is a separate change.
- No engine change. `semdiff.py` and `review_gate.py` are untouched, so no gate
  install goes stale beyond the ordinary version bump.
- No severity floor beyond exposure. Performance, stability, and
  data-integrity findings rate on the existing scale.
- No `cohort` to `category` rename. That stays the sibling member
  `review-finding-category`, and this member adds values to the field under its
  current name.

## Implementation

- **The trigger is inline; the depth is a reference.** The epic's Decision *"A
  reference states its whole trigger"* makes a hidden trigger a named hazard, so
  the five trigger lines live in `SKILL.md` where every review reads them, and
  only the worked guidance sits behind the load condition. Rejected: the epic's
  original cohort-gated design. The cohort vocabulary is a path heuristic with
  no security member, so the security lens would never fire reliably — verified
  by reading `COHORT_RULES` at `plugins/s/skills/review/scripts/semdiff.py:575`.
  Also rejected: all four lenses inline with no reference, which pushes
  `SKILL.md` to roughly 293 of its 300-line ceiling and leaves later members no
  headroom.

- **The five triggers, in this order**, each one line under `### 5b`:
  secret or credential exposure; authorization boundary; unbounded work;
  resource release; migration reversibility. The first two are the security
  lens, the third is performance, the fourth is stability, the fifth is data
  integrity — four lenses, five triggers, because security splits cleanly into
  exposure and authorization and the two are looked for differently.

- **Exposure floors at `high`.** The existing rubric defines `high` as a
  correctness bug, a contract break with an un-updated consumer, or an unmet
  spec criterion; a leaked credential fits none of them and would otherwise
  land at `medium` on a reviewer's uncertainty. The floor is stated as a rule
  on the severity rubric in each of the three surfaces, not as a new severity
  tier. Rejected: a floor covering irreversible migrations too — it widens the
  blocking set on a judgement ("is this really irreversible") far less crisp
  than "is this a credential".

- **Taxonomy values land on one surface.** The `--json` finding taxonomy lives
  only at `plugins/s/skills/review/references/json-output.md:17`; the harness
  body carries no JSON shape, and the copilot template's array holds
  `severity`, `path`, `start_line`, `end_line`, `detail` and `replacement` with
  no taxonomy field at all. Verified by grep across all three surfaces. So the
  four new values are a one-file edit, and this member cannot collide with
  `review-finding-category` beyond that same line.

- **Three surfaces, by what each can do.** The plugin skill gets the inline
  triggers plus the reference. The harness body and the copilot template get
  the lens guidance inline, condensed to their own house style — the harness
  body as a new numbered step after its step 6, the copilot template as a new
  step after its step 4 — because a GitHub Actions runner has no
  `${CLAUDE_PLUGIN_ROOT}` and no reference files.

- **The agreement test extends rather than bends.** `risk-lenses.md` joins the
  three references already pinned by
  `test_table_cell_agrees_with_reference_condition`, which requires its `Load
  when` cell and its condition sentence to share at least three content words.
  Measured on the current head, the existing rows share 6, 3 and 3, so the
  threshold has no slack: the new row's wording must be checked against the
  test rather than assumed to pass.

- **Risk: a lens that fires on everything is a lens nobody runs.** Each trigger
  is written as a concrete thing to look for in the diff, not as a topic to
  consider. The reference carries the worked examples that keep the line
  between a real finding and a reflex one.

- **Version bump.** `plugins/s/.claude-plugin/plugin.json` moves to `0.6.216`,
  per the cache-snapshot rule in AGENTS.md.
