## 1. Tests first

- [x] 1.1 [req: wordmark-static] In `plugins/s/skills/build/tests/test_wordmark.py`,
      add a module-level `EXPECTED_ART` tuple that is a byte-identical literal
      copy of `wordmark.ART` (generate it from `ART` with `repr` so trailing
      spaces survive). Replace every `readme_banner()` call with
      `EXPECTED_ART`, rename `test_art_equals_the_readme_fence` to
      `test_art_equals_the_pinned_banner`, then delete the `README` constant,
      the `readme_banner()` function, and the README wording in the module
      docstring. Confirm `grep -n README plugins/s/skills/build/tests/test_wordmark.py`
      prints nothing.
- [x] 1.2 [req: onboard-tour-skill] In `ArtFidelityTest` in
      `plugins/s/skills/build/tests/test_wordmark.py`, add
      `test_onboard_banner_equals_the_art`: read
      `plugins/s/skills/onboard/SKILL.md` (path built from `REPO_ROOT`), find
      the line starting `**Step 1 — banner`, take the lines between the next
      two lines equal to "```", and assert they equal `tuple(wordmark.ART)`.
      Run `python3 -m unittest plugins/s/skills/build/tests/test_wordmark.py`
      and observe this one test fail (the onboard banner has drifted).

## 2. Banner source of truth

- [x] 2.1 [req: onboard-tour-skill] In `plugins/s/skills/onboard/SKILL.md`
      step 1, replace the five art lines inside the fenced block with the seven
      `wordmark.ART` lines, verbatim with trailing spaces. Re-run the wordmark
      tests and confirm they all pass.
- [x] 2.2 [req: wordmark-static] In `plugins/s/skills/build/scripts/wordmark.py`,
      replace the two comment lines above `ART` with: "The banner art — the
      canonical shipd banner. `plugins/s/skills/onboard/SKILL.md` carries a
      verbatim copy (test_wordmark asserts both)." Leave the tuple unchanged.
- [x] 2.3 [req: readme-displays-the-shipd-banner, readme-brand-marks] Delete
      lines 1–10 of `README.md` (the opening fence, the art, the closing fence,
      and the blank line after it) so line 1 is the `<img src="icon.svg" …>`
      element.

## 3. Release

- [x] 3.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` by
      one patch over what `main` carries.
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it passes.
