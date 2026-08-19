# shipd-wordmark

### Requirement: Banner art and static render
id: wordmark-static

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/wordmark.py` whose banner art constant is
byte-identical (trailing spaces included) to the fenced block-character
banner at the top of the repository `README.md`, and whose `render(stream)`
writes that banner to `stream`. If color is disabled for the stream (per
`cli_common.color_enabled`: non-TTY, or `NO_COLOR` set non-empty), then the
output SHALL be the plain art lines with no ANSI escape sequences. Where
color is enabled, the module SHALL decorate the glyphs with a horizontal
truecolor gradient interpolated linearly per column from `#8888a0`
(leftmost) to `#c6ff4e` (rightmost), resetting attributes at each line end.

#### Scenario: Piped render is plain and byte-identical
- **WHEN** `render` targets a non-TTY stream
- **THEN** the output is exactly the banner art lines each followed by a
  newline, containing no `\x1b` byte

#### Scenario: NO_COLOR suppresses color on a terminal
- **WHEN** `render` targets a TTY-like stream with `NO_COLOR=1`
- **THEN** the output contains no `\x1b` byte

#### Scenario: Colored render carries the gradient endpoints
- **WHEN** `render` targets a TTY-like stream with `NO_COLOR` unset
- **THEN** the output colors the leftmost glyph column with
  `\x1b[38;2;136;136;160m`, the rightmost with `\x1b[38;2;198;255;78m`, and
  each line ends with `\x1b[0m`

#### Scenario: Art stays in sync with the README banner
- **WHEN** the module's art constant is compared to the lines inside the
  README's opening fenced banner block
- **THEN** they are byte-identical

### Requirement: Two-phase finite animation
id: wordmark-animation

Where color is enabled for the target stream, `animate(stream)` SHALL run a
finite two-phase animation redrawn in place with cursor-repositioning
escapes: first a reveal phase in which the banner's glyphs appear left to
right, letter by letter, rendered white; then a strictly faster color phase
in which a left-to-right wipe converts the white glyphs to their gradient
colors, ending settled on output identical to the static colored render. The
cursor SHALL be hidden during the animation and restored afterwards,
including when the animation is interrupted. If color is disabled for the
stream, then `animate` SHALL write exactly one plain render with no ANSI
escape sequences and no frame delays.

#### Scenario: Disabled color degrades to one plain render
- **WHEN** `animate` targets a non-TTY stream with an injected spy sleep
- **THEN** the output equals the plain render exactly and the spy sleep was
  never called

#### Scenario: Enabled animation is finite and settles on the static render
- **WHEN** `animate` targets a TTY-like stream with an injected spy sleep
- **THEN** the sleep call count is finite and bounded, the output's final
  frame equals the static colored render's glyph output, and the output
  hides (`\x1b[?25l`) and later restores (`\x1b[?25h`) the cursor

#### Scenario: Color phase is faster than reveal phase
- **WHEN** `animate` runs with its default delays against a TTY-like stream
  and a spy sleep records each delay value
- **THEN** every color-phase delay is strictly smaller than every
  reveal-phase delay

### Requirement: Script preview CLI
id: wordmark-cli

When executed directly, `wordmark.py` SHALL print the static render to
stdout and exit `0`, and with `--animate` SHALL run the animation against
stdout instead. This preview is script-level only: the `shipd` binary's
curated verb set is unchanged, and `shipd wordmark` SHALL remain a usage
error.

#### Scenario: Bare run prints the plain banner when piped
- **WHEN** `python3 wordmark.py` runs with stdout piped
- **THEN** stdout is exactly the plain banner and the exit code is 0

#### Scenario: Animate flag degrades when piped
- **WHEN** `python3 wordmark.py --animate` runs with stdout piped
- **THEN** stdout is exactly one plain banner and the exit code is 0

#### Scenario: No shipd verb is added
- **WHEN** `shipd wordmark` runs
- **THEN** the usage banner is printed to stderr and the exit code is 2
