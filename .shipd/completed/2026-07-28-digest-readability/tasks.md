# Tasks — digest-readability

## 1. Skill and reference docs

- [x] 1.1 [req: investigation-findings-digest] In `plugins/s/skills/plan/SKILL.md` flow step 2, rewrite the digest instruction to the new form contract: short headed groups of concise dot-points (about two lines each, succinct over exhaustive), the situational-awareness framing ("the user can ask to dive deeper"), the lean-toward-diagram rule (include a compact proposed-shape diagram whenever the findings carry a shape or flow; always when the user asked for one), and keep the two mutually exclusive endings exactly as they are.
- [x] 1.2 [req: visualization-on-demand] In `plugins/s/skills/plan/references/visualization.md`, scope the decorative-visual prohibition to question-round visuals, add the digest lean-toward rule (a shape or flow in the findings satisfies the bar by itself), and add a short "digest shape sketch" idiom beside the existing three.
- [x] 1.3 [req: investigation-findings-digest] Bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 2. Verification

- [x] 2.1 [req: *] Run the live eval suite (`python3 evals/run.py`) and require both `/s:plan` cases to pass; inspect one passing transcript's digest and confirm it renders as headed dot-point groups (with a diagram when the case's findings carry a shape). Run the library lint and the full unittest suite as regression guards.
