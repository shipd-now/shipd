# readme-drop-banner
Status: verified
Theme: developer-experience

## Idea

Remove the boxed ASCII-art banner from the top of `README.md` and make the
wordmark module's own art the single source of truth for the shipd banner.

### Motivation

The maintainer wants the README to open with the icon and introduction, but
three verified specs and seven wordmark tests bind the banner to the README, so
a README-only edit fails CI (PR #255). Moving the banner's source of truth into
`wordmark.ART` lets the README drop it without losing the banner anywhere else.

### Details

- Delete the fenced banner from `README.md`; it opens with the `icon.svg` image
  and then the ☕ introduction.
- `wordmark.ART` becomes the canonical banner; its comment stops pointing at
  the README.
- `test_wordmark.py` stops reading the README and compares against a pinned
  literal copy of the art.
- The `/s:onboard` step-1 banner is replaced with `wordmark.ART` verbatim (it
  had drifted to an unrelated banner), and a new test keeps the two in sync.
- Bump the plugin version.

Affected capabilities: `project-readme`, `shipd-wordmark`, `shipd-onboard`
(all modified). Impact: `README.md`, `plugins/s/skills/build/scripts/wordmark.py`
(comment only), `plugins/s/skills/build/tests/test_wordmark.py`,
`plugins/s/skills/onboard/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to the banner art, its gradient colors, or its animation.
- No change to `install_tui.py` or any other `wordmark` consumer.
- Closing the superseded PR #255 is a manual step outside this change's tasks.

## Implementation

- **Source of truth.** `ART` in `plugins/s/skills/build/scripts/wordmark.py`
  is the canonical banner. Its leading comment changes to say so and to name
  the onboard skill as the one verbatim copy. The tuple itself is unchanged.
- **Tests pin a literal.** `test_wordmark.py` drops `README`, `readme_banner()`,
  and the README wording in its module docstring, and adds a module-level
  `EXPECTED_ART` tuple: a byte-identical literal copy of today's `ART` (trailing
  spaces included). Every former `readme_banner()` call uses `EXPECTED_ART`.
  `test_art_equals_the_readme_fence` becomes `test_art_equals_the_pinned_banner`.
  Rejected: comparing `ART` to itself — that guards nothing, while a pinned
  copy catches an accidental edit to the art.
- **Onboard sync test.** Add `test_onboard_banner_equals_the_art` to
  `ArtFidelityTest`. It reads `plugins/s/skills/onboard/SKILL.md`, finds the
  line starting `**Step 1 — banner`, takes the lines between the next two
  lines that equal "```", and asserts they equal `tuple(wordmark.ART)`.
  Rejected: a separate onboard test file — the art lives in `wordmark`, so its
  fidelity tests live together.
- **Onboard banner.** In `plugins/s/skills/onboard/SKILL.md` step 1, replace
  the five lines inside the fence with the seven `ART` lines, verbatim.
- **README.** Delete `README.md` lines 1–10 (the opening fence, the art, the
  closing fence, and the blank line after it), so line 1 is the
  `<img src="icon.svg" …>` element.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` `version` by one
  patch from whatever `main` carries at build time (0.6.247 → 0.6.248 today).

Risk: a stray trailing-space difference between `EXPECTED_ART` and `ART`
fails the pinned tests; copying the tuple programmatically from `ART` and then
running the suite guards it.

## Readiness attestation

### Problem and motivation

The README banner is bound by specs and tests, so it cannot be removed with a
README-only edit; PR #255 failed CI on exactly that binding.

Evidence:

- `.shipd/verified/project-readme/spec.md:3` requirement
  `readme-displays-the-shipd-banner` requires the README to open with the banner.
- `plugins/s/skills/build/tests/test_wordmark.py:36` `readme_banner()` reads the
  README fence; CI run 37420079513 failed the seven tests that call it.

### Scope and non-goals

The change covers the README, the wordmark art's source of truth, its tests, and
the onboard banner; the art, colors, animation, and install TUI stay unchanged.

Evidence:

- In scope: `README.md:1-10`, `wordmark.py:31-32`, `test_wordmark.py`,
  `plugins/s/skills/onboard/SKILL.md:126-132`.
- Out of scope: `plugins/s/skills/build/scripts/install_tui.py:45` imports
  `wordmark` but never reads the README.

### Affected capabilities and files

Three capabilities and five files are affected, because the banner contract
spans the README, the wordmark module, and the onboard skill.

Evidence:

- `project-readme`: `readme-displays-the-shipd-banner` (base 563c1698c0cc),
  `readme-brand-marks` (base dfdf2dbd9321).
- `shipd-wordmark`: `wordmark-static` (base d11f49263a77).
- `shipd-onboard`: `onboard-tour-skill` (base 3f9a9a7bc540).
- Files: `README.md:1-10`, `plugins/s/skills/build/scripts/wordmark.py:31`,
  `plugins/s/skills/build/tests/test_wordmark.py:7,19,36-42,64-65`,
  `plugins/s/skills/onboard/SKILL.md:122-132`,
  `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `python3 -m unittest plugins/s/skills/build/tests/test_wordmark.py`
  on unchanged `main` → `OK`.
- Runnable premise: `git grep -l "█▀▀▀ █  █"` → only `README.md` and
  `wordmark.py`, so the onboard skill carries no copy of the current art.

### No open task-shaping decision

Every task-shaping decision is settled by investigation; none remain.

Evidence:

- Test oracle (pinned literal over self-comparison): investigation.
- Onboard banner fixed to `ART` and guarded by a sync test: investigation, per
  `.shipd/verified/shipd-onboard/spec.md:17` and the request.
- Version bump required: `AGENTS.md:18`.
