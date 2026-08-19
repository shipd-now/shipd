# shipd-wordmark
Status: verified
Epic: harness-install

## Idea

Add a stdlib ANSI wordmark module to the engine scripts that renders the
block-character "shipd now" banner statically or as a finite color-sweep
animation, TTY/`NO_COLOR`-gated, for the upcoming `shipd install` TUI.

### Motivation

The harness-install epic requires the interactive `shipd install` step to open
with the animated shipd wordmark, but no engine module can render the banner —
the art exists only as static text at the top of `README.md` (the banner the
user shipped in PR #78). This member ships the rendering module first so the
install-tui member can compose it.

### Details

- New engine module `plugins/s/skills/build/scripts/wordmark.py`: the banner
  art as a constant byte-identical to `README.md` lines 2–5, a static
  `render(stream)` (plain, or truecolor gradient `#8888a0 → #c6ff4e` across
  the letters), a finite two-phase `animate(stream)` — white letter-by-letter
  reveal, then a faster color pass — and a script-level preview CLI
  (`python3 wordmark.py [--animate]`).
- Color and TTY gating delegated to the existing `cli_common.color_enabled`.
- Tests at `plugins/s/skills/build/tests/test_wordmark.py`; plugin version
  bump.

Affected capabilities: `shipd-wordmark` (added). Impact:
`plugins/s/skills/build/scripts/wordmark.py` (new),
`plugins/s/skills/build/tests/test_wordmark.py` (new),
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No new `shipd` binary verb — the `shipd-cli` capability pins exactly the
  curated verbs, and the epic confines the animation's user surface to
  `shipd install` (the install-tui member); the preview here is script-level
  only.
- No `README.md` or `icon.svg` changes, and no rebrand — ☕ stays the inline
  brand mark.
- No terminal-capability sniffing — no `COLORTERM` detection or 256-color
  fallback path; `NO_COLOR` and non-TTY are the only gates.
- No `install.sh` wiring or interactive selection — that is the install-tui
  member.

## Implementation

- **Module placement:** `wordmark.py` beside `cli_common.py` under
  `plugins/s/skills/build/scripts/`, importing `cli_common` for
  `color_enabled` — the engine's single color gate (observed:
  `color_enabled(io.StringIO())` → `False`; with `NO_COLOR=1` on a TTY →
  `False`). Rejected: a shell script under `plugins/s/integrations/` — the
  consumer (the install TUI) is Python, and the constitution's test rule
  covers Python engine scripts directly.
- **Art source of truth:** `ART`, a tuple of the four banner lines copied
  byte-for-byte (trailing spaces included) from the fenced block at
  `README.md:2-5`. A test compares `ART` against the README fence so the two
  can never drift silently. Rejected: reading the README at runtime — the
  module ships in the plugin snapshot where no README exists.
- **`render(stream)`:** when `cli_common.color_enabled(stream)` is false,
  write the plain art lines exactly (escape-free, byte-identical to `ART`);
  when true, decorate each glyph with a horizontal truecolor gradient — per
  column `t = x / (width - 1)`, linear RGB interpolation from `#8888a0`
  (`\x1b[38;2;136;136;160m`, leftmost) to `#c6ff4e`
  (`\x1b[38;2;198;255;78m`, rightmost) — and reset each line with `\x1b[0m`.
  Rejected: 256-color approximation — the user pinned exact hex endpoints,
  and `NO_COLOR`/piped paths already cover terminals without truecolor.
- **`animate(stream, *, reveal_delay=0.035, color_delay=0.012,
  sleep=time.sleep)` — two phases, both finite:** when color is disabled,
  exactly one plain `render` — no escapes, no sleeps. When enabled: hide the
  cursor (`\x1b[?25l`); **phase 1 (reveal)** — the banner's glyph columns
  appear left to right, letter by letter, rendered white
  (`\x1b[38;2;255;255;255m`), one reveal step per column group at
  `reveal_delay`; **phase 2 (color)** — a faster left-to-right wipe at
  `color_delay` converts the white glyphs to their gradient colors, ending
  settled on the static gradient render (identical to `render`'s colored
  output). Frames redraw in place via `\x1b[<n>A` repositioning, and the
  cursor is restored (`\x1b[?25h`) in a `finally` so an interruption never
  leaves it hidden. Delays and `sleep` are injectable so tests run
  deterministically with a spy sleep. Rejected: an unbounded
  loop-until-keypress — install must proceed on its own.
- **Preview CLI:** `argparse` main; bare run prints the static render to
  stdout and exits 0, `--animate` runs the animation. This is a developer
  preview, not a `shipd` verb: the binary's curated verb set is untouched
  (observed today: `shipd wordmark` prints the usage banner and exits 2, and
  must keep doing so).
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` 0.6.137 → 0.6.138
  in the same change — the cache snapshot is keyed by version.

Risk: terminals without truecolor support may render approximate colors from
the `38;2;r;g;b` sequences; that is cosmetic only, and every non-TTY, piped,
or `NO_COLOR` path stays byte-identical plain text, so scripted consumers are
unaffected. Risk: a future README banner edit desyncing `ART` — caught by the
fidelity test comparing the two.
