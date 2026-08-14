## Context

The statusline (`plugins/s/integrations/statusline.sh`, specced in the
`statusline` capability) prefixes every rendered line with a glyph, currently
☢️. The request: swap it for ☕ to match the "am" (morning/coffee) identity.
The glyph appears in four living places: the script (raw UTF-8 bytes via
`printf`, plus comments), the test suite's expected constant, the master specs
(`statusline`, `project-readme`), and the README. Archived change artifacts
also contain ☢️ but are immutable history.

## Goals / Non-Goals

**Goals:**
- ☕ replaces ☢️ in every living artifact: script, tests, master specs (via
  this change's deltas), README.
- Correct, minimal encoding of the new glyph.

**Non-Goals:**
- Touching archived changes (`am/spec/changes/archive/`, `openspec/`) — frozen.
- Any other statusline behavior, color, or format change.

## Decisions

### D1 — Bare U+2615, no variation selector
☕ is U+2615 HOT BEVERAGE, `Emoji_Presentation=Yes` — it renders as emoji by
default, so no U+FE0F (VS16) is appended. UTF-8 bytes: `\xe2\x98\x95`. This
differs from ☢️ (U+2622, a narrow text-presentation symbol that required VS16
to render as emoji), so the script's VS16 explanation comment is replaced, not
imitated.
- *Rejected alternative:* U+2615 + VS16 — legal but redundant, and doubles the
  glyph's byte length for nothing.

### D2 — Rename the script/test identifier RADIO → COFFEE
The script's `RADIO` variable and the test module's `RADIO` constant are named
after the old glyph; keeping the name would be misleading. Rename both to
`COFFEE` in the same tasks that change the bytes.

### D3 — Master specs change via MODIFIED deltas, archives stay frozen
The `statusline-rendering` and `readme-documents-spec-engine` requirements
embed the glyph in their normative line format, so this change carries MODIFIED
deltas with fresh `base:` hashes; `spec_merge.py` updates the master library at
merge time. Archived artifacts keep ☢️ — history is not rewritten.

## Risks / Trade-offs

- **Terminal rendering variance** → U+2615 is one of the oldest, most widely
  supported emoji (Unicode 4.0); its default emoji presentation makes it
  *more* portable than the old glyph, not less.
- **Stale cache snapshot after merge** → the user-scope plugin cache serves the
  statusline registration docs, but the statusline itself runs live from the
  repo per `.claude/settings.json`, so the visible line updates on merge; the
  cached copy catches up at the next `claude plugin update s@shipd`.
