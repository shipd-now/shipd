# plan-attestation-table
Status: complete

## Idea

Render the `/s:plan` readiness attestation as a markdown table instead of
prose lines, so it is easier to scan and read.

### Motivation

The readiness attestation prints as four dense prose bullets with citations
buried mid-sentence, which the user reports is hard to scan; the current
contract mandates "one cited line per checklist item".

### Details

- Modify requirement `readiness-attestation` in capability `shipd-plan`: the
  attestation is printed as a markdown table with one cited row per checklist
  item instead of one prose line per item.
- Update the Attestation section of
  `plugins/s/skills/plan/references/readiness.md` and step 5 of
  `plugins/s/skills/plan/SKILL.md` to the table contract.
- Bump the plugin version in `plugins/s/.claude-plugin/plugin.json`.

Affected capabilities: `shipd-plan` (modified). Impact: docs/spec-only —
`plugins/s/skills/plan/references/readiness.md`,
`plugins/s/skills/plan/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`; no
code changes, no new dependencies.

### Non-goals

- No change to the four checklist items, their evidence standards, or the
  runnable-premise rule — this is presentation only.
- No edits to archived changes under `.shipd/completed/`, which also carry the
  old phrasing.
- No engine or lint enforcement of the table — the attestation remains
  user-visible response text, never a parsed artifact.

## Implementation

- **Table shape: three columns — `#`, `Item`, `Evidence` — one row per
  checklist item.** The item column names the checklist item; the evidence
  column carries the citation(s). Rejected: a Verdict/checkmark column — every
  printed row is by definition met (an unmet item blocks emission), so the
  column would carry no information.
- **Item 4's row carries its decisions in the evidence cell** — each
  task-shaping decision with the rung that settled it (investigation, personal
  memory, the oracle, or the user), or an explicit "none remained". Verified
  runnable premises stay in item 3's evidence cell, preserving requirement
  `premise-evidence-in-attestation` unchanged.
- **Minimal normative rewording.** The only phrase change in prose surfaces is
  "one cited line per checklist item" → the table contract ("a markdown table
  with one cited row per checklist item"); the evidence standards per item are
  untouched. This keeps the delta reviewable and the blast radius to two
  documentation files.
- **Version bump `0.6.96` → `0.6.97`** in
  `plugins/s/.claude-plugin/plugin.json`, per the repo rule that every
  `plugins/s/` change bumps the version in the same PR (the plugin cache
  snapshot is keyed by version).

Risk: the delta's `base:` hash goes stale if `shipd-plan` merges another
change first; guarded by the emit/merge engines validating the hash against
the current master.
