# coffee-statusline
Status: verified

## Why

The statusline currently leads with ☢️ (radioactive sign) — a placeholder glyph
with no connection to the project. The plugin's identity is "am": the `/s:`
namespace, mornings, coffee. Leading the statusline with ☕ leans into that
identity and reads instantly as "the shipd line" in a crowded terminal.

## What Changes

- The statusline prefix glyph changes from `☢️` to `☕` everywhere it renders:
  the selected-spec line, `no active specs`, and `<n> specs · none selected`.
- The glyph's encoding simplifies: ☕ is U+2615 with default emoji
  presentation, so the VS16 variation selector that ☢️ required is dropped
  (3 UTF-8 bytes instead of 6, no width quirk to document).
- The statusline tests and the README (line-format examples and annotations)
  follow the new glyph.
- Frozen history is untouched: archived changes under `am/spec/changes/archive/`
  and the `openspec/` bootstrap archive keep ☢️ as a record of their era.

## Capabilities

### Modified Capabilities

- `statusline`: the rendering requirement's line format changes its prefix
  glyph from ☢️ to ☕.
- `project-readme`: the spec-engine documentation requirement now shows the ☕
  statusline format.

## Impact

- `plugins/s/integrations/statusline.sh` — glyph bytes, variable name, header
  comments.
- `plugins/s/skills/build/tests/test_statusline.py` — expected-glyph constant
  and docstring.
- `README.md` — three ☢️ occurrences (statusline section format block, repo
  tree annotations).
- After merging, the plugin cache snapshot must be refreshed
  (`claude plugin update s@shipd`) for the live statusline to change.
