# build-pointer-newline
Status: verified

## Idea

Format the plan hand-off's closing build pointer on its own line: the summary's
last sentence ends with a colon, then a blank line, then `/s:build` alone.

### Motivation

The hand-off summary currently buries the next command mid-sentence
("…ready to implement with `/s:build`."), so the one actionable string is hard
to spot and copy; the user asked for the summary to end with a colon and place
`/s:build` on its own line.

### Details

- Amend `shipd-plan`'s `standalone-invocation` requirement so the hand-off
  summary's closing sentence ends with a colon and the `/s:build` pointer sits
  alone on its own line, separated by a blank line.
- Update both hand-off passages in `plugins/s/skills/plan/SKILL.md` — the
  Ending's "Point at build" step and the enrichment re-gate exit — to state
  that format.
- Bump the plugin version in `plugins/s/.claude-plugin/plugin.json`.

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`;
no new dependencies.

### Non-goals

- No change to other skills' endings (e.g. `/s:epic`'s pointer at `/s:plan`).
- No change to the rest of the hand-off summary's structure — the
  motivation-led ordering and the no-file-inventory rule stay as they are.

## Implementation

- Encode the format in the `standalone-invocation` requirement, not only in
  SKILL.md prose, so the convention merges into the master library on archive
  and survives future skill rewrites. Rejected: a SKILL.md-only edit — the
  master spec would keep permitting the inline pointer.
- The exact format: the summary's final sentence ends with a colon (e.g.
  "The change is ready to implement with:"), followed by a blank line, then
  `/s:build` alone on its own line. Both hand-off sites reference the same
  format: Ending step 3 ("Point at build") at
  `plugins/s/skills/plan/SKILL.md:688` and the enrichment re-gate exit bullet
  at `plugins/s/skills/plan/SKILL.md:184`.
- Version bump: `plugins/s/.claude-plugin/plugin.json` moves one patch above
  the value on the branch (0.6.126 → 0.6.127 as of planning). The in-flight
  `copilot-review-gate` change also claims 0.6.127; whichever merges second
  resolves the conflict by taking one patch above the then-current value, per
  the AGENTS.md cache-snapshot rule.

Risk: skill prose has no runtime test surface, so the format is enforced by
the spec scenario and review rather than an automated check — acceptable for a
documentation-format convention.
