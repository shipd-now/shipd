## 1. Swap the glyph

- [x] 1.1 [P1] In `plugins/s/integrations/statusline.sh`: rename the `RADIO`
      variable to `COFFEE` (all uses), change its bytes to
      `$(printf '\xe2\x98\x95')` (bare U+2615, no VS16), and update the header
      comment block — the output-format example on line 6 becomes
      `☕ <name> · <status> · <done>/<total>`, and the U+2622/VS16 explanation
      comment becomes one line noting ☕ = U+2615 HOT BEVERAGE, emoji
      presentation by default, no variation selector needed.
- [x] 1.2 [P1] In `plugins/s/skills/build/tests/test_statusline.py`: rename the
      `RADIO` constant to `COFFEE` (all references), set it to `"☕"`, and
      update the constant's comment and any docstring mention of the old glyph
      accordingly.
- [x] 1.3 [P1] In `README.md`: replace all three `☢️` occurrences with `☕` —
      the statusline format block (`☕ <name> · <status> · <done>/<total>`),
      the `.claude/settings.json` tree annotation, and the `statusline.sh` tree
      annotation. Leave archived spec artifacts untouched.

## 2. Verify

- [x] 2.1 Run the full plugin test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it passes; then pipe a session JSON with this repo's root as
      `workspace.current_dir` into `plugins/s/integrations/statusline.sh` and
      confirm the rendered line starts with `☕` and contains no `☢`.
