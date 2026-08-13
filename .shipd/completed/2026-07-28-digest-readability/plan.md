# digest-readability
Status: verified

## Idea

The `/s:plan` findings digest reads as a wall of text: the spec mandates
its *content* (files, patterns, surprises, the ending block) but nothing
about its *form*, so digests legally render as dense multi-line bullet
prose. Worse, the visualization rules effectively ban diagrams from digests
— a visual must "carry a decision" or be explicitly requested — even though
the go-ahead prompt is a decision the user makes by judging the proposed
shape. Users expected a diagram and scannable points; they got paragraphs.

This change makes the digest a situational-awareness surface:

- Digest content is organized as short headed groups of concise dot-points
  (about two lines each, succinct over exhaustive) — depth stays available
  on request, because the user can always ask to dive deeper.
- Diagrams are leaned toward: whenever the findings carry a shape or flow
  that a compact diagram conveys faster than prose, the digest includes
  one; an explicit user request is always honored as today.
- The two mutually exclusive endings (OPEN QUESTIONS ⊕ typed go-ahead) are
  untouched.

### Non-goals

- No change to the depth-path context briefs or the shared-understanding
  summary — same density disease, separate change if wanted.
- No change to the digest's required content, the two-ending machinery, or
  any question-round protocol.
- The decorative-visual prohibition stays in force for question rounds —
  only the digest gets the lean-toward-diagram stance.

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/SKILL.md` (flow step 2),
`plugins/s/skills/plan/references/visualization.md`, plugin version bump.
Doc/spec only — no engine code, no unit-test surface.

## Implementation

- **Form joins the digest contract.** `investigation-findings-digest` gains
  form mandates: headed groups of dot-points (≤ ~2 lines each), succinct
  framing whose job is telling the user where the flow stands, and a
  compact proposed-shape diagram when the findings carry a shape or flow.
  Rejected: a rigid fixed template — section names vary legitimately with
  the change; the mandate is form discipline, not a boilerplate.
- **The diagram bar gets a digest carve-out.** `visualization-on-demand`
  keeps the decorative ban for question rounds but adopts lean-toward for
  the digest: a shape or flow in the findings satisfies the bar by itself.
  Rejected: diagram-always-mandatory — a one-file doc tweak has no shape
  worth drawing, and a forced diagram is the new wall of text.
- **`visualization.md` documents the digest idiom** beside the existing
  three (current-vs-proposed, flow sketch, options table) and scopes its
  prohibition paragraph to question-round visuals.
- **SKILL.md flow step 2** gets the digest layout guidance: headed groups,
  dot-points, the lean-toward-diagram instruction, and the
  "user can ask to dive deeper" framing. Plugin version bumps one patch.

Risk: skill-doc changes only take effect via the snapshot and live eval
behavior can drift from intent; guarded by the verification task running
the live `/s:plan` eval cases (the resume-driver harness passes today) and
by the spec scenarios pinning the form rules for future audits.
