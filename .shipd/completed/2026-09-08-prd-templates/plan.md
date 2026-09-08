# prd-templates
Status: verified
Epic: prd-discovery

## Idea

Ship the three PRD template skeletons (`basic`, `standard`, `comprehensive`)
as references under the prd skill, with a drift-guard test pinning their
section skeletons to the engine's tier registry.

### Motivation

The `prd-discovery` epic mandates plugin-owned templates whose skeletons match
the engine-side tier registry, and none exist yet; the `/s:prd` skill and its
interview cannot compose a PRD without them.

### Details

- Three template files under `plugins/s/skills/prd/references/`: `basic.md`,
  `standard.md`, `comprehensive.md` — each a fill-ready PRD skeleton.
- A drift-guard test asserting each template's level-2 headings equal its
  tier's `PRD_TIER_SECTIONS` tuple exactly, in order.

Affected capabilities: `shipd-prd` (added requirement). Impact: new
`plugins/s/skills/prd/references/` directory, new
`plugins/s/skills/build/tests/test_prd_templates.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No `SKILL.md` for the prd skill — the `prd-skill` member creates it; this
  change ships only `references/` (verified harmless to plugin validation).
- No engine behavior changes: the registry, `lint_prd`, and the emit path
  are untouched. The one engine-side edit is the harness bodies drift guard's
  skill enumeration (see Implementation), which this change's new directory
  forces.
- No workspace-customizable templates (an epic non-goal).

## Implementation

- **One file per tier**, named exactly `<tier>.md` under
  `plugins/s/skills/prd/references/`, so the `/s:prd` skill later resolves a
  tier to its template by filename alone. Rejected: one file with three
  sections — a mid-interview tier switch should swap whole skeletons, not
  parse a shared file.
- **Skeleton shape** (each template): line 1 `# <prd-slug>` as a literal
  placeholder the skill replaces, then `Status: draft`, then
  `Template: <tier>` naming the file's own tier, a blank line, then every
  section its tier requires from `PRD_TIER_SECTIONS`
  (`spec_common.py:1328`) as an exact `## <name>` heading in registry order,
  each followed by one italic guidance line (e.g. *State the problem and who
  feels it — why now.*) telling the interviewer what the section must
  establish. Guidance prose is unconstrained by lint (headings only), but
  every guidance line stays a single italic line so a filled PRD replaces it
  wholesale. No `Initiative:` line in the skeletons — it is optional
  metadata the skill adds only when the PRD names a parent initiative.
- **Drift-guard test** `plugins/s/skills/build/tests/test_prd_templates.py`:
  resolves the templates directory relative to its own file
  (`…/tests/../../prd/references`), and for each tier in
  `sc.PRD_TEMPLATE_TIERS` asserts: the file exists; its `## ` heading lines
  (in document order) equal `sc.PRD_TIER_SECTIONS[tier]` exactly — content
  and order, no extras in the skeleton; its `Template:` line names the tier;
  its first line is a `# ` title; its `Status:` line says `draft`. Also
  asserts the references directory contains no unexpected `.md` beyond the
  three tiers, so a renamed template cannot silently escape the guard.
  Equality (not subset) is deliberate: the registry is a floor for authored
  PRDs, but the shipped skeleton is the canonical starting point and must
  carry exactly the tier's floor.
- **A live-lint sanity check inside the same test**: fill a temp workspace
  PRD from the `basic` template (replace the title placeholder with the
  directory slug, replace guidance lines with text) and assert
  `spec_lint.lint_prd` reports no errors — proving the skeletons produce
  lint-clean PRDs, not just matching headings.
- **Drift-guard predicate refinement.** Creating `plugins/s/skills/prd/`
  without a `SKILL.md` trips `test_harness_bodies.ShippedTemplateTest`'s 1:1
  skills↔bodies match, which enumerates *every* directory under
  `plugins/s/skills/`. A directory without a `SKILL.md` is not a skill —
  Claude Code ignores it — so the guard's enumeration narrows to
  `SKILL.md`-bearing directories (test-side only; `harness_bodies.commands()`
  reads the bodies directory and is untouched), with a docstring note naming
  why. The `harness-command-bodies/body-templates` requirement is MODIFIED
  accordingly in this change's deltas. Rejected: shipping a
  `harness/bodies/prd.md` now — it would advertise a `/s:prd` command whose
  skill does not exist until the `prd-skill` member.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.190` →
  `0.6.191`.
- **Risk**: a future registry change breaks the drift-guard loudly — that is
  the point; the failing test names the drifted tier and section.

## Questions and answers

### Q1: Which per-tier required-section lists does the registry pin?
- **Question:** Recorded during the sibling `prd-store` planning session and
  binding here: which concrete section lists do the tiers pin? Options:
  additive house style; additive corporate names; independent lists.
  Recommendation: additive house style.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Additive house style — basic: Problem, Solution, Success
  criteria; standard adds Users, Requirements, Non-goals; comprehensive adds
  Risks, Rollout, Open questions. Shipped in `spec_common.PRD_TIER_SECTIONS`;
  these templates are skeletons of exactly those lists.
- **Queued:** q-prd-tier-section-registry
