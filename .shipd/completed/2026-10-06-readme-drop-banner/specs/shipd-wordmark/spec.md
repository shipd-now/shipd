## MODIFIED Requirements

### Requirement: Banner art and static render
id: wordmark-static
base: d11f49263a77
Dropped: Art stays in sync with the README banner

The engine SHALL provide a stdlib-only module
`plugins/s/skills/build/scripts/wordmark.py` whose banner art constant `ART`
is the canonical shipd banner — the single source of truth every other copy
of the banner matches byte for byte — and whose `render(stream)` writes that
banner to `stream`. If color is disabled for the stream (per
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

#### Scenario: Art matches the pinned banner
- **WHEN** the module's art constant is compared to the test suite's pinned
  literal copy of the banner
- **THEN** they are byte-identical, trailing spaces included

#### Scenario: Art does not depend on the README
- **WHEN** the wordmark tests run
- **THEN** none of them reads `README.md`
